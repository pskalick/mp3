#!/usr/bin/env bash
set -euo pipefail

# Usage:
# ./run.sh                 # auto-connect all paired Bluetooth devices
# ./run.sh AA:BB:CC:DD:EE:FF

cleanup() {
  pkill -f "python3 bluetooth_service.py" || true
  pkill -f "python3 playback_service.py" || true
  pkill -f "python3 display_service.py" || true
}

trap cleanup EXIT INT TERM

if [ $# -ge 1 ]; then
  BT_MAC="$1"
  python3 bluetooth_service.py --bt-mac "$BT_MAC" &
else
  python3 bluetooth_service.py &
fi

python3 playback_service.py --music-dir /media/music --shuffle --loop &
python3 display_service.py
