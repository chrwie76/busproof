#!/bin/sh
# The broker's start: its password file is made from the generated password, inside the container.
set -eu
mosquitto_passwd -c -b /tmp/passwd busproof "$(cat /secrets/password)"
chown mosquitto /tmp/passwd
chmod 600 /tmp/passwd
exec mosquitto -c /mosquitto/config/mosquitto.conf
