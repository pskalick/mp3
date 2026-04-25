#!/usr/bin/env python3
import argparse
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Optional

from epaper_display import EpaperDisplay

AUDIO_EXTENSIONS = {".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac"}
DEFAULT_MUSIC_DIR = "/media/music"


def run_command(command: List[str], check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(command, check=check, text=True, capture_output=True)


def ensure_command_exists(name: str) -> None:
    result = subprocess.run(["which", name], text=True, capture_output=True)
    if result.returncode != 0:
        print(f"Missing required command: {name}", file=sys.stderr)
        sys.exit(1)


def scan_music(folder: str) -> List[Path]:
    root = Path(folder)
    if not root.exists():
        print(f"Music folder does not exist: {folder}", file=sys.stderr)
        return []

    tracks = []
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in AUDIO_EXTENSIONS:
            tracks.append(path)

    return sorted(tracks)


def connect_bluetooth(mac_address: str, retries: int, retry_delay_sec: int) -> bool:
    ensure_command_exists("bluetoothctl")
    print(f"Connecting Bluetooth headphones: {mac_address}")

    for attempt in range(1, retries + 1):
        command = [
            "bluetoothctl",
            "--timeout",
            "20",
            "power",
            "on",
            "agent",
            "on",
            "default-agent",
            "trust",
            mac_address,
            "pair",
            mac_address,
            "connect",
            mac_address,
        ]
        result = run_command(command, check=False)
        output = f"{result.stdout}\n{result.stderr}".lower()
        if "successful" in output or "connection successful" in output:
            print("Bluetooth connected.")
            return True

        print(f"Bluetooth attempt {attempt}/{retries} failed. Retrying...")
        time.sleep(retry_delay_sec)

    print("Could not connect Bluetooth headphones.", file=sys.stderr)
    return False


def list_paired_devices() -> List[str]:
    result = run_command(["bluetoothctl", "devices", "Paired"], check=False)
    devices: List[str] = []
    for line in result.stdout.splitlines():
        # Expected format: "Device AA:BB:CC:DD:EE:FF Device Name"
        parts = line.strip().split()
        if len(parts) >= 2 and parts[0] == "Device":
            devices.append(parts[1])
    return devices


def connect_all_paired_devices(retries: int, retry_delay_sec: int) -> bool:
    ensure_command_exists("bluetoothctl")
    devices = list_paired_devices()
    if not devices:
        print("No paired Bluetooth devices found.", file=sys.stderr)
        return False

    print(f"Trying auto-connect for {len(devices)} paired Bluetooth device(s).")
    at_least_one_connected = False
    for mac_address in devices:
        connected = connect_bluetooth(mac_address, retries, retry_delay_sec)
        at_least_one_connected = at_least_one_connected or connected

    return at_least_one_connected


def play_tracks_loop(
    tracks: List[Path], shuffle: bool, epaper: Optional[EpaperDisplay] = None
) -> None:
    ensure_command_exists("cvlc")
    ordered = list(tracks)
    if shuffle:
        import random

        random.shuffle(ordered)

    print(f"Starting playback ({len(ordered)} tracks). Press Ctrl+C to stop.")
    current_process: subprocess.Popen | None = None

    def handle_sigint(_sig, _frame):
        if current_process is not None and current_process.poll() is None:
            current_process.terminate()
        if epaper is not None:
            epaper.show("MP3 Player", ["Stopped"])
            epaper.sleep()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_sigint)

    for index, track in enumerate(ordered, start=1):
        now_playing = track.stem
        print(f"[{index}/{len(ordered)}] {now_playing}")
        if epaper is not None:
            epaper.show(
                "Now Playing",
                [
                    f"{index}/{len(ordered)}",
                    now_playing,
                ],
            )

        command = ["cvlc", "--play-and-exit", "--no-video", str(track)]
        current_process = subprocess.Popen(command)
        current_process.wait()

    if epaper is not None:
        epaper.show("MP3 Player", ["Playlist complete"])
        epaper.sleep()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Raspberry Pi music player for /media/music with Bluetooth headphones."
    )
    parser.add_argument(
        "--music-dir",
        default=DEFAULT_MUSIC_DIR,
        help="Directory that contains music files (default: /media/music)",
    )
    parser.add_argument(
        "--bt-mac",
        default=None,
        help="Bluetooth MAC address of headphones (optional). If omitted, all paired devices are auto-connected.",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=5,
        help="Bluetooth connection retries (default: 5)",
    )
    parser.add_argument(
        "--retry-delay",
        type=int,
        default=5,
        help="Seconds between Bluetooth retries (default: 5)",
    )
    parser.add_argument(
        "--shuffle",
        action="store_true",
        help="Shuffle songs before playback.",
    )
    parser.add_argument(
        "--epd",
        action="store_true",
        help='Enable Waveshare 2.13" V4 e-paper status display.',
    )
    args = parser.parse_args()

    epaper = EpaperDisplay(enabled=args.epd)
    if args.epd and not epaper.ready:
        print(
            "E-paper requested but not available. Install waveshare_epd + pillow and check wiring.",
            file=sys.stderr,
        )

    if epaper.ready:
        epaper.show("MP3 Player", ["Scanning music..."])

    tracks = scan_music(args.music_dir)
    if not tracks:
        if epaper.ready:
            epaper.show("MP3 Player", ["No music found"])
            epaper.sleep()
        print(f"No supported music files found in: {args.music_dir}", file=sys.stderr)
        sys.exit(1)

    if epaper.ready:
        epaper.show("MP3 Player", [f"Tracks: {len(tracks)}", "Bluetooth connect..."])

    if args.bt_mac:
        connected = connect_bluetooth(args.bt_mac, args.retries, args.retry_delay)
    else:
        connected = connect_all_paired_devices(args.retries, args.retry_delay)
    if not connected:
        if epaper.ready:
            epaper.show("MP3 Player", ["Bluetooth failed"])
            epaper.sleep()
        sys.exit(1)

    if epaper.ready:
        epaper.show("MP3 Player", ["Bluetooth connected"])
    play_tracks_loop(tracks, args.shuffle, epaper=epaper if epaper.ready else None)


if __name__ == "__main__":
    main()
