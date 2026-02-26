#!/usr/bin/env python3
import time
import spidev
import RPi.GPIO as GPIO

IRQ = 17          # T_IRQ
SPI_BUS = 0
SPI_DEV = 1       # CE1 => /dev/spidev0.1
SPI_HZ = 2_000_000

CMD_X = 0x90
CMD_Y = 0xD0

MIN_RAW = 100
MAX_RAW = 4000

W, H = 320, 240   # repère logique (même que ton affichage luma)

def read12(spi, cmd):
    r = spi.xfer2([cmd, 0x00, 0x00])
    return ((r[1] << 8) | r[2]) >> 3

def map_range(v, in_min, in_max, out_min, out_max):
    return int((v - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)

def raw_to_pixel(x_raw, y_raw):
    x = map_range(x_raw, MIN_RAW, MAX_RAW, 0, W - 1)
    y = map_range(y_raw, MIN_RAW, MAX_RAW, 0, H - 1)
    # clamp
    x = max(0, min(W - 1, x))
    y = max(0, min(H - 1, y))
    return x, y

def main():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(IRQ, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    spi = spidev.SpiDev()
    spi.open(SPI_BUS, SPI_DEV)
    spi.max_speed_hz = SPI_HZ
    spi.mode = 0

    print("✅ Touch test simple (Ctrl+C pour quitter)")
    print("Touche l'écran: on affiche x_raw/y_raw puis x/y (approx).")

    try:
        while True:
            if GPIO.input(IRQ) == GPIO.LOW:  # touched
                x_raw = read12(spi, CMD_X)
                y_raw = read12(spi, CMD_Y)

                if MIN_RAW < x_raw < MAX_RAW and MIN_RAW < y_raw < MAX_RAW:
                    x, y = raw_to_pixel(x_raw, y_raw)
                    print(f"raw: x={x_raw:4d} y={y_raw:4d}  ->  px: x={x:3d} y={y:3d}")
                time.sleep(0.05)
            else:
                time.sleep(0.01)
    except KeyboardInterrupt:
        pass
    finally:
        spi.close()
        GPIO.cleanup()
        print("Bye")

if __name__ == "__main__":
    main()