#!/bin/bash
set -e
systemctl stop rbx-app.service || true
/home/rubik/rubik-env/bin/python3 /home/rubik/rubiks-robot/tools/rbx_safe_shutdown.py || true
/sbin/poweroff
