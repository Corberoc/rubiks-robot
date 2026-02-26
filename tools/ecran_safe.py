# /home/rubik/rubiks-robot/tools/ecran_safe.py
# rotate=0 : si  affichage est tourné, la rotation (0/1/2/3) a juster
from __future__ import annotations

def safe_clear_screen() -> None:
    """
    Efface l'écran ILI9341 (SPI0 CE0) en affichant une image noire.
    Pins confirmées :
      - CS  : GPIO8  (SPI0 CE0)  -> port=0, device=0
      - DC  : GPIO25
      - RST : GPIO24
    """
    try:
        from luma.core.interface.serial import spi
        from luma.lcd.device import ili9341
        from PIL import Image
    except Exception:
        return

    try:
        # SPI0 CE0 => port=0, device=0 (CS=GPIO8)
        serial = spi(port=0, device=0, gpio_DC=25, gpio_RST=24)
        device = ili9341(serial, width=320, height=240, rotate=0)

        black = Image.new("RGB", (device.width, device.height), "black")
        device.display(black)
    except Exception:
        return