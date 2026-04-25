#!/usr/bin/env python3
import json
import tempfile
from pathlib import Path
from typing import Any, Dict

STATE_FILE = Path("/tmp/mp3_state.json")


def default_state() -> Dict[str, Any]:
    return {
        "status": "starting",
        "track_index": 0,
        "track_total": 0,
        "track_name": "",
        "bluetooth_connected": False,
        "bluetooth_devices": [],
        "last_error": "",
    }


def read_state() -> Dict[str, Any]:
    if not STATE_FILE.exists():
        return default_state()
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return default_state()


def write_state(updates: Dict[str, Any]) -> Dict[str, Any]:
    data = default_state()
    data.update(read_state())
    data.update(updates)

    fd, temp_path = tempfile.mkstemp(prefix="mp3_state_", suffix=".json", dir=str(STATE_FILE.parent))
    try:
        with open(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=True)
        Path(temp_path).replace(STATE_FILE)
    except Exception:
        try:
            Path(temp_path).unlink(missing_ok=True)
        except Exception:
            pass
        raise
    return data
