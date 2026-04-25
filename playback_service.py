#!/usr/bin/env python3
import argparse
import random
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import List

from shared_state import write_state

AUDIO_EXTENSIONS = {".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac"}
DEFAULT_MUSIC_DIR = "/media/music"


def ensure_command_exists(name: str) -> None:
    result = subprocess.run(["which", name], text=True, capture_output=True)
    if result.returncode != 0:
        write_state({"status": "error", "last_error": f"Missing command: {name}"})
        print(f"Missing required command: {name}", file=sys.stderr)
        sys.exit(1)


def scan_music(folder: str) -> List[Path]:
    root = Path(folder)
    if not root.exists():
        return []
    tracks: List[Path] = []
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in AUDIO_EXTENSIONS:
            tracks.append(path)
    return sorted(tracks)


def main() -> None:
    parser = argparse.ArgumentParser(description="Music playback service")
    parser.add_argument("--music-dir", default=DEFAULT_MUSIC_DIR)
    parser.add_argument("--shuffle", action="store_true")
    parser.add_argument("--loop", action="store_true", help="Repeat playlist forever")
    args = parser.parse_args()

    ensure_command_exists("cvlc")
    write_state({"status": "scanning", "last_error": ""})

    stop_flag = {"value": False}
    current_process = {"value": None}

    def handle_sigint(_sig, _frame):
        stop_flag["value"] = True
        proc = current_process["value"]
        if proc is not None and proc.poll() is None:
            proc.terminate()
        write_state({"status": "stopped"})
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_sigint)
    signal.signal(signal.SIGTERM, handle_sigint)

    while not stop_flag["value"]:
        tracks = scan_music(args.music_dir)
        if not tracks:
            write_state(
                {"status": "no-music", "track_index": 0, "track_total": 0, "track_name": "", "last_error": "No music files found."}
            )
            time.sleep(10)
            continue

        if args.shuffle:
            random.shuffle(tracks)

        write_state({"status": "playing", "track_total": len(tracks), "last_error": ""})
        for index, track in enumerate(tracks, start=1):
            if stop_flag["value"]:
                break
            write_state({"status": "playing", "track_index": index, "track_name": track.stem})
            cmd = ["cvlc", "--play-and-exit", "--no-video", str(track)]
            current_process["value"] = subprocess.Popen(cmd)
            current_process["value"].wait()

        if not args.loop:
            write_state({"status": "playlist-complete"})
            break


if __name__ == "__main__":
    main()
