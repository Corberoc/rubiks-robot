#!/usr/bin/env python3
from gpiozero import Button
from signal import pause
import subprocess
import time

GPIO_PIN = 3

APP_SERVICE = "rbx-app.service"
HOLD_SECONDS = 2.0
DEBOUNCE = 0.15

SAFE_SHUTDOWN_SCRIPT = "/usr/local/bin/rbx_safe_shutdown.sh"

btn = Button(GPIO_PIN, pull_up=True, bounce_time=DEBOUNCE, hold_time=HOLD_SECONDS)

_long_fired = False

def run(cmd):
    subprocess.run(cmd, check=False)

print("[GPIO3] ready (short=restart, long=shutdown)", flush=True)

def on_held():
    global _long_fired
    _long_fired = True
    print("[GPIO3] LONG -> safe shutdown", flush=True)
    run([SAFE_SHUTDOWN_SCRIPT])

def on_released():
    global _long_fired
    if _long_fired:
        _long_fired = False
        return
    time.sleep(0.02)
    print("[GPIO3] SHORT -> stop + wait + start app", flush=True)
    run(["/bin/systemctl", "stop", APP_SERVICE])
    time.sleep(3.0)
    run(["/bin/systemctl", "start", APP_SERVICE])

btn.when_held = on_held
btn.when_released = on_released
pause()
