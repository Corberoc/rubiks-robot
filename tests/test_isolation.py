#!/usr/bin/env python3
import time
from rpi_ws281x import PixelStrip, Color

N1, PIN1, CH1 = 24, 18, 0   # anneau 1: GPIO18 = PWM0
N2, PIN2, CH2 = 12, 19, 1   # anneau 2: GPIO19 = PWM1

FREQ = 800000
DMA  = 10
BRI  = 80
INV  = False

s1 = PixelStrip(N1, PIN1, FREQ, DMA, INV, BRI, CH1)
s2 = PixelStrip(N2, PIN2, FREQ, DMA, INV, BRI, CH2)
s1.begin(); s2.begin()

def fill(s, r, g, b):
    c = Color(r, g, b)
    for i in range(s.numPixels()):
        s.setPixelColor(i, c)
    s.show()

def off():
    fill(s1, 0, 0, 0); fill(s2, 0, 0, 0)

off()
input("Tout doit être éteint. Entrée...\n")

off(); fill(s1, 255, 0, 0)
input("Seul anneau 1 (GPIO18) ROUGE. Entrée...\n")

off(); fill(s2, 0, 255, 0)
input("Seul anneau 2 (GPIO19) VERT. Entrée...\n")

off(); fill(s1, 0, 0, 255); fill(s2, 0, 0, 255)
input("Les deux BLEUS. Entrée...\n")

off()
print("OK")