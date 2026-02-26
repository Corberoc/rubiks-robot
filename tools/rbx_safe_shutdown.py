#!/usr/bin/env python3
# =============================================================================
# rbx_safe_shutdown.py
# -----------------------------------------------------------------------------
# Met le robot en état SAFE (servos/leds/ecran/gpio) avant poweroff.
# Best-effort : aucune étape ne doit faire planter le script.
# =============================================================================

from __future__ import annotations
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional


# =============================================================================
# ✅ CONSTANTES A REMPLIR / AJUSTER ICI
# =============================================================================

# --- Servos (pigpio) ---
SERVO_PIN_1 = 16   # <-- GPIO du servo 1
SERVO_PIN_2 = 5   # <-- GPIO du servo 2
SERVOS_USE_PIGPIO = True  # True si tu utilises pigpio (recommandé)

# --- LEDs NeoPixel ---
LEDS_USE_CONFIG_JSON = True  # True = lire pins/count dans config.json
# (Chemin résolu dynamiquement via RBX_CONFIG injecté par le wrapper systemd)
RBX_CONFIG_PATH = ""  # non utilisé si RBX_CONFIG est défini

# (Optionnel) override manuel si tu veux forcer sans config.json :
# NEOPIXELS_OVERRIDE = [{"pin": 18, "count": 24, "brightness": 0.2},
#                       {"pin": 19, "count": 12, "brightness": 0.2}]
NEOPIXELS_OVERRIDE: List[Dict[str, Any]] = []

# --- Écran (facultatif) ---
SCREEN_SAFE_ENABLED = False  # mets True quand tu as branché le hook ci-dessous
# Exemple de hook : tu mets ton import + clear dans safe_screen_clear()
# =============================================================================


def log(msg: str) -> None:
    print(f"[SAFE_SHUTDOWN] {msg}", flush=True)


def safe_call(label: str, fn) -> None:
    try:
        fn()
        log(f"OK: {label}")
    except Exception as e:
        log(f"SKIP: {label} -> {e}")


# =============================================================================
# SERVOS SAFE
# =============================================================================

def servos_safe() -> None:
    """
    SAFE servos : coupe le signal servo (pulsewidth=0) sur les pins indiquées.
    - pigpio est robuste pour ça.
    """
    if not SERVOS_USE_PIGPIO:
        raise RuntimeError("SERVOS_USE_PIGPIO=False")

    import pigpio  # nécessite pigpiod actif

    pi = pigpio.pi()
    if not pi.connected:
        raise RuntimeError("pigpio non connecté (pigpiod pas lancé ?)")

    for pin in (SERVO_PIN_1, SERVO_PIN_2):
        pi.set_servo_pulsewidth(pin, 0)  # stop PWM servo
        time.sleep(0.02)

    pi.stop()
    log(f"Servos OFF (pulsewidth=0) on GPIO{SERVO_PIN_1}, GPIO{SERVO_PIN_2}")


# =============================================================================
# LEDS SAFE
# =============================================================================

def _load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _find_config_path() -> Path:
    # priorité à la variable d'env
    env = os.environ.get("RBX_CONFIG")
    if env:
        p = Path(env).expanduser()
        if p.exists():
            return p

    # sinon chemin constant (vide = ignoré)
    if RBX_CONFIG_PATH:
        p = Path(RBX_CONFIG_PATH).expanduser()
        if p.exists():
            return p

    # fallback : quelques candidats
    candidates = [
        Path.cwd() / "config.json",
        Path.home() / "rubiks-robot" / "config.json",
    ]
    for c in candidates:
        if c.exists():
            return c

    raise RuntimeError("config.json introuvable (RBX_CONFIG ou RBX_CONFIG_PATH)")


def _extract_rings_from_cfg(cfg: Dict[str, Any]) -> List[Dict[str, Any]]:
    rings: List[Dict[str, Any]] = []
    leds = cfg.get("leds") or {}
    if not isinstance(leds, dict):
        return rings

    if "anneau1" in leds or "anneau2" in leds:
        for key in ("anneau1", "anneau2"):
            r = leds.get(key)
            if not isinstance(r, dict):
                continue
            if r.get("enabled") is False:
                continue
            pin = r.get("pin")
            count = r.get("count")
            if isinstance(pin, int) and isinstance(count, int) and count > 0:
                rings.append({
                    "name": key,
                    "pin": pin,
                    "count": count,
                    "brightness": float(r.get("brightness", 0.2)),
                })
    else:
        pin = leds.get("pin")
        count = leds.get("count")
        if isinstance(pin, int) and isinstance(count, int) and count > 0:
            rings.append({
                "name": "leds",
                "pin": pin,
                "count": count,
                "brightness": float(leds.get("brightness", 0.2)),
            })
    return rings


def leds_off() -> None:
    try:
        import board
        import neopixel
    except Exception as e:
        raise RuntimeError(f"imports neopixel/board KO: {e}")

    if NEOPIXELS_OVERRIDE:
        rings = NEOPIXELS_OVERRIDE
        log("NeoPixels: utilisation override (NEOPIXELS_OVERRIDE)")
    else:
        if not LEDS_USE_CONFIG_JSON:
            raise RuntimeError("LEDS_USE_CONFIG_JSON=False et pas d'override")
        cfg_path = _find_config_path()
        cfg = _load_json(cfg_path)
        rings = _extract_rings_from_cfg(cfg)
        if not rings:
            raise RuntimeError(f"Aucun anneau trouvé dans {cfg_path}")
        log(f"NeoPixels: config.json = {cfg_path}")

    for r in rings:
        pin_num = int(r["pin"])
        count = int(r["count"])
        brightness = float(r.get("brightness", 0.2))

        attr = f"D{pin_num}"
        if not hasattr(board, attr):
            log(f"LED SKIP: GPIO{pin_num} introuvable côté board.{attr}")
            continue

        bpin = getattr(board, attr)
        px = neopixel.NeoPixel(bpin, count, brightness=brightness, auto_write=False)
        px.fill((0, 0, 0))
        px.show()
        time.sleep(0.02)
        log(f"LED OFF: GPIO{pin_num} n={count}")


# =============================================================================
# SCREEN SAFE (hook)
# =============================================================================

def safe_screen_clear() -> None:
    if not SCREEN_SAFE_ENABLED:
        raise RuntimeError("SCREEN_SAFE_ENABLED=False")
    from ecran_safe import safe_clear_screen
    safe_clear_screen()


# =============================================================================
# GPIO CLEANUP
# =============================================================================

def gpio_cleanup() -> None:
    try:
        import RPi.GPIO as GPIO
        GPIO.cleanup()
    except Exception:
        pass


# =============================================================================
# MAIN
# =============================================================================

def main() -> int:
    log("Début SAFE... (servos -> leds -> écran -> gpio)")

    safe_call("Servos OFF", servos_safe)
    safe_call("LEDs OFF", leds_off)
    safe_call("Écran clear", safe_screen_clear)
    safe_call("GPIO cleanup", gpio_cleanup)

    log("SAFE terminé.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        log(f"Erreur inattendue (ignorée): {e}")
        sys.exit(0)