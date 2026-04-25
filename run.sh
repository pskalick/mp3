#!/usr/bin/env bash
set -euo pipefail

# Usage:
# ./run.sh AA:BB:CC:DD:EE:FF

if [ $# -lt 1 ]; then
  echo "Usage: $0 <HEADPHONES_BT_MAC>"
  exit 1
fi

BT_MAC="$1"

python3 player.py --bt-mac "$BT_MAC" --music-dir /media/music --shuffle --epd
