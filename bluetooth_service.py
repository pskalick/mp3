#!/usr/bin/env python3
import argparse
import subprocess
import sys
import time
from typing import List

from shared_state import write_state


def run_command(command: List[str]) -> subprocess.CompletedProcess:
    return subprocess.run(command, check=False, text=True, capture_output=True)


def ensure_command_exists(name: str) -> None:
    result = subprocess.run(["which", name], text=True, capture_output=True)
    if result.returncode != 0:
        write_state({"status": "error", "last_error": f"Missing command: {name}"})
        print(f"Missing required command: {name}", file=sys.stderr)
        sys.exit(1)


def list_paired_devices() -> List[str]:
    result = run_command(["bluetoothctl", "devices", "Paired"])
    devices: List[str] = []
    for line in result.stdout.splitlines():
        parts = line.strip().split()
        if len(parts) >= 2 and parts[0] == "Device":
            devices.append(parts[1])
    return devices


def connect_device(mac_address: str, retries: int, retry_delay_sec: int) -> bool:
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
        result = run_command(command)
        output = f"{result.stdout}\n{result.stderr}".lower()
        if "successful" in output or "connection successful" in output:
            return True
        time.sleep(retry_delay_sec)
    return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Bluetooth auto-connect service")
    parser.add_argument("--bt-mac", default=None, help="Optional MAC to connect")
    parser.add_argument("--retries", type=int, default=5)
    parser.add_argument("--retry-delay", type=int, default=5)
    parser.add_argument("--interval", type=int, default=30, help="Reconnect loop interval seconds")
    args = parser.parse_args()

    ensure_command_exists("bluetoothctl")
    write_state({"status": "bluetooth-starting"})

    while True:
        if args.bt_mac:
            devices = [args.bt_mac]
        else:
            devices = list_paired_devices()

        if not devices:
            write_state(
                {
                    "status": "bluetooth-no-devices",
                    "bluetooth_connected": False,
                    "bluetooth_devices": [],
                    "last_error": "No paired Bluetooth devices found.",
                }
            )
            time.sleep(args.interval)
            continue

        connected_devices = []
        for device in devices:
            if connect_device(device, args.retries, args.retry_delay):
                connected_devices.append(device)

        write_state(
            {
                "status": "bluetooth-connected" if connected_devices else "bluetooth-failed",
                "bluetooth_connected": bool(connected_devices),
                "bluetooth_devices": connected_devices,
                "last_error": "" if connected_devices else "Bluetooth connection failed.",
            }
        )
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
