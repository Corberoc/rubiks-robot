#!/usr/bin/env python3
# =============================================================================
# touchv2.py - Driver tactile XPT2046 en SPI hardware (spidev0.1) + IRQ
# =============================================================================
# Câblage attendu (Raspberry Pi / BCM) :
#   - T_CLK  -> GPIO11 (SPI0 SCLK)
#   - T_DIN  -> GPIO10 (SPI0 MOSI)
#   - T_DO   -> GPIO9  (SPI0 MISO)
#   - T_CS   -> GPIO7  (SPI0 CE1)  => /dev/spidev0.1
#   - T_IRQ  -> GPIO17 (IRQ tactile)
#
# Dépendances :
#   - python3-spidev (apt) OU spidev (pip)
#   - RPi.GPIO
#
# API :
#   - TouchHandler(on_press, on_release, on_move, width, height, rotate)
#   - start(), stop(), cleanup()
#   - is_touched(), get_touch()
#
# Remarques :
#   - Les valeurs brutes (raw) dépendent de ton écran/montage.
#     Par défaut, on renvoie du "pixel" en 320x240 et on fournit
#     des options swap/invert/rotate.
# =============================================================================

import time
import threading

import spidev
import RPi.GPIO as GPIO
import traceback

class TouchHandler2:
    """
    Gestion tactile XPT2046 (SPI hardware).
    - Lecture via /dev/spidev0.1 (CE1)
    - IRQ GPIO17 (actif à l'état bas quand touch)
    """

    # Commandes XPT2046 (classiques)
    # 0x90 = read X, 0xD0 = read Y (selon orientation, peut sembler "inversé")
    CMD_X = 0x90
    CMD_Y = 0xD0
    CMD_Z1 = 0xB0
    CMD_Z2 = 0xC0

    def __init__(
        self,
        on_press=None,
        on_release=None,
        on_move=None,
        *,
        width: int = 320,
        height: int = 240,
        rotate: int = 0,
        irq_gpio: int = 17,
        spi_bus: int = 0,
        spi_dev: int = 1,
        spi_hz: int = 2_000_000,
        # Mapping options (souvent nécessaires)
        swap_xy: bool = False,
        invert_x: bool = False,
        invert_y: bool = False,
        # Filtrage / seuils
        min_raw: int = 100,
        max_raw: int = 4000,
        move_threshold_px: int = 2,
        poll_s: float = 0.01,
    ):
        self.on_press = on_press
        self.on_release = on_release
        self.on_move = on_move

        self.width = int(width)
        self.height = int(height)
        self.rotate = int(rotate) % 4

        self.irq_gpio = int(irq_gpio)
        self.spi_bus = int(spi_bus)
        self.spi_dev = int(spi_dev)
        self.spi_hz = int(spi_hz)

        self.swap_xy = bool(swap_xy)
        self.invert_x = bool(invert_x)
        self.invert_y = bool(invert_y)

        self.min_raw = int(min_raw)
        self.max_raw = int(max_raw)
        self.move_threshold_px = int(move_threshold_px)
        self.poll_s = float(poll_s)

        self._stop_event = threading.Event()
        self._thread = None
        self._lock = threading.Lock()
        self._last_xy = (None, None)
        self._touching = False

        # GPIO IRQ
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.irq_gpio, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        # SPI
        self._spi = spidev.SpiDev()
        self._spi.open(self.spi_bus, self.spi_dev)  # => /dev/spidev0.1
        self._spi.max_speed_hz = self.spi_hz
        self._spi.mode = 0b00
        self._spi_lock = threading.Lock()

    # --------------------- Low-level reads ---------------------
    def _safe_call(self, cb, *args):
        if not cb:
            return
        try:
            cb(*args)
        except Exception:
            print("[TOUCHV2] callback crashed:")
            traceback.print_exc()

    def _read12(self, cmd: int) -> int:
        """
        Lit une valeur 12-bit du XPT2046.
        Transaction standard : [cmd, 0x00, 0x00]
        """
        with self._spi_lock:
            r = self._spi.xfer2([cmd, 0x00, 0x00])
        # 12-bit : bits [14:3] de la réponse
        return ((r[1] << 8) | r[2]) >> 3

    def is_touched(self) -> bool:
        """IRQ actif bas quand on touche."""
        return GPIO.input(self.irq_gpio) == GPIO.LOW

    # --------------------- Public API ---------------------

    def get_touch(self):
        """Retourne (x, y) en pixels, ou (None, None) si pas de touch."""
        with self._lock:
            return self._last_xy

    def read_raw(self):
        """
        Lit raw x/y (12-bit). Retourne (x_raw, y_raw) ou (None, None).
        """
        if not self.is_touched():
            return None, None

        x_raw = self._read12(self.CMD_X)
        y_raw = self._read12(self.CMD_Y)

        if not (self.min_raw < x_raw < self.max_raw and self.min_raw < y_raw < self.max_raw):
            return None, None

        return x_raw, y_raw

    def raw_to_pixel(self, x_raw: int, y_raw: int):
        """
        Convertit du raw 12-bit vers un repère pixel "approx".
        Sans calibration fine, on mappe [min_raw..max_raw] vers [0..W/H].
        """
        # Map simple
        def map_range(v, in_min, in_max, out_min, out_max):
            return int((v - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)

        x = map_range(x_raw, self.min_raw, self.max_raw, 0, self.width - 1)
        y = map_range(y_raw, self.min_raw, self.max_raw, 0, self.height - 1)

        # Options swap/invert
        if self.swap_xy:
            x, y = y, x
        if self.invert_x:
            x = (self.width - 1) - x
        if self.invert_y:
            y = (self.height - 1) - y

        # Rotation (0..3) dans le repère width x height
        if self.rotate == 0:
            pass
        elif self.rotate == 1:
            x, y = y, (self.width - 1) - x
        elif self.rotate == 2:
            x, y = (self.width - 1) - x, (self.height - 1) - y
        elif self.rotate == 3:
            x, y = (self.height - 1) - y, x

        # Clamp
        x = max(0, min(self.width - 1, x))
        y = max(0, min(self.height - 1, y))
        return x, y

    def read_pixel(self):
        """Retourne (x, y) en pixels, ou (None, None)."""
        x_raw, y_raw = self.read_raw()
        if x_raw is None:
            return None, None
        return self.raw_to_pixel(x_raw, y_raw)

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=1.0)

    def cleanup(self):
        self.stop()
        try:
            self._spi.close()
        except Exception:
            pass

    # --------------------- Poll loop ---------------------

    def _loop(self):
        last_x, last_y = None, None
        pressed_sent = False

        while not self._stop_event.is_set():
            if self.is_touched():
                x, y = self.read_pixel()
                if x is not None:
                    with self._lock:
                        self._last_xy = (x, y)
                        self._touching = True

                    if not pressed_sent:
                        pressed_sent = True
                        last_x, last_y = x, y
                        if self.on_press:
                            self._safe_call(self.on_press, x, y)
                    else:
                        if (last_x is None or abs(x - last_x) > self.move_threshold_px
                                or abs(y - last_y) > self.move_threshold_px):
                            last_x, last_y = x, y
                            if self.on_move:
                                self._safe_call(self.on_move, last_x, last_y)

                time.sleep(self.poll_s)
            else:
                if pressed_sent:
                    pressed_sent = False
                    if self.on_release and last_x is not None:
                        self._safe_call(self.on_release, last_x, last_y)
                with self._lock:
                    self._last_xy = (None, None)
                    self._touching = False
                last_x, last_y = None, None
                time.sleep(self.poll_s)


# -------------------------------------------------------------------------
# Mode test direct : python3 touchv2.py
# -------------------------------------------------------------------------
if __name__ == "__main__":
    def press(x, y): print(f"PRESS  x={x} y={y}")
    def move(x, y):  print(f"MOVE   x={x} y={y}")
    def rel(x, y):   print(f"RELEASE x={x} y={y}")

    t = TouchHandler2(on_press=press, on_move=move, on_release=rel)
    t.start()
    print("Touchv2 OK. Touche l'écran (Ctrl+C pour quitter).")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        t.cleanup()
        GPIO.cleanup()
        print("Bye")