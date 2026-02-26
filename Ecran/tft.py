#!/usr/bin/env python3
import time
from luma.core.interface.serial import spi
from luma.lcd.device import ili9341
from PIL import Image, ImageDraw, ImageFont
import RPi.GPIO as GPIO

GPIO.setwarnings(False)

serial = spi(port=0, device=0, gpio_DC=25, gpio_RST=24)

for rot in (0, 1, 2, 3):
    device = ili9341(serial, width=320, height=240, rotate=rot)

    img = Image.new("RGB", (device.width, device.height), "black")
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()

    draw.text((10, 10), f"ILI9341 OK - rotate={rot}", fill="white", font=font)
    draw.rectangle((10, 40, 110, 140), outline="white", fill="red")
    draw.rectangle((120, 40, 220, 140), outline="white", fill="green")
    draw.rectangle((230, 40, 310, 140), outline="white", fill="blue")

    device.display(img)
    time.sleep(2)

# noir à la fin
device.display(Image.new("RGB", (device.width, device.height), "black"))
print("Done")