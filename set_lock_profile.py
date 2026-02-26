#!/usr/bin/env python3
import json
import sys
from pathlib import Path

USAGE = "Usage: set_lock_profile.py <config.json> <profile_name> [anneau2_scan_brightness]"

def main():
    if len(sys.argv) < 3:
        print(USAGE)
        sys.exit(2)

    cfg_path = Path(sys.argv[1])
    profile = sys.argv[2]
    brightness = float(sys.argv[3]) if len(sys.argv) >= 4 else None

    data = json.loads(cfg_path.read_text(encoding="utf-8"))

    # Vérifie que le profil existe
    profiles = data.get("camera", {}).get("lock_profiles", {})
    if profile not in profiles:
        available = ", ".join(sorted(profiles.keys()))
        raise SystemExit(f"Profil '{profile}' introuvable. Disponibles: {available}")

    # Set profil actif
    data["camera"]["lock_profile_active"] = profile

    # Optionnel : ajuster brightness du scan pour anneau2 dans le profil choisi
    if brightness is not None:
        lp = data["camera"]["lock_profiles"][profile]
        lp.setdefault("led_scan", {}).setdefault("anneau2", {})
        lp["led_scan"]["anneau2"]["enabled"] = True
        lp["led_scan"]["anneau2"]["brightness"] = brightness

    # Sauvegarde (joli + stable)
    cfg_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"OK: lock_profile_active = {profile}" + (f" ; anneau2_scan_brightness = {brightness}" if brightness is not None else ""))

if __name__ == "__main__":
    main()