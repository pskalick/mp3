#!/usr/bin/env python3
import argparse
import time

from epaper_display import EpaperDisplay
from shared_state import read_state


def build_lines(state: dict) -> tuple[str, list[str]]:
    status = state.get("status", "starting")
    title = "MP3 Player"

    if status == "playing":
        line1 = f"{state.get('track_index', 0)}/{state.get('track_total', 0)}"
        line2 = state.get("track_name", "")
        bt = "BT: ok" if state.get("bluetooth_connected") else "BT: no"
        return "Now Playing", [line1, line2, bt]

    if status == "bluetooth-no-devices":
        return title, ["No BT devices", "Pair once in", "bluetoothctl"]
    if status == "bluetooth-failed":
        return title, ["Bluetooth failed"]
    if status == "no-music":
        return title, ["No music in", "/media/music"]
    if status == "playlist-complete":
        return title, ["Playlist complete"]
    if status == "stopped":
        return title, ["Stopped"]
    if status == "scanning":
        return title, ["Scanning music..."]

    message = state.get("last_error", "") or status
    return title, [message]


def main() -> None:
    parser = argparse.ArgumentParser(description="E-paper display service")
    parser.add_argument("--refresh", type=int, default=5, help="Refresh interval seconds")
    args = parser.parse_args()

    epaper = EpaperDisplay(enabled=True)
    if not epaper.ready:
        print("E-paper not available. Install waveshare_epd + Pillow and check wiring.")
        return

    last_rendered = None
    while True:
        state = read_state()
        title, lines = build_lines(state)
        rendered = (title, tuple(lines))
        if rendered != last_rendered:
            epaper.show(title, lines)
            last_rendered = rendered
        time.sleep(args.refresh)


if __name__ == "__main__":
    main()
