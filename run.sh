#!/usr/bin/env bash
set -euo pipefail

# Usage:
# ./run.sh                 # auto-connect all paired Bluetooth devices
# ./run.sh AA:BB:CC:DD:EE:FF

if [ $# -ge 1 ]; then
  BT_MAC="$1"
  python3 player.py --bt-mac "$BT_MAC" --music-dir /media/music --shuffle --epd
else
  python3 player.py --music-dir /media/music --shuffle --epd
fi
