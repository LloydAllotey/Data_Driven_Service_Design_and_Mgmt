"""
database/storage.py — Session persistence.

Handles reading and writing group session JSON files stored in sessions/.
All other modules import from here — nothing else should touch the filesystem.
"""

from __future__ import annotations

import json
import random
import string
from pathlib import Path
from typing import Optional

# ROOT is the project root (Remote_Data_Driven/), one level above database/
ROOT = Path(__file__).parent.parent
SESSIONS_DIR = ROOT / "sessions"
SESSIONS_DIR.mkdir(exist_ok=True)


def _session_path(code: str) -> Path:
    return SESSIONS_DIR / f"{code.upper()}.json"


def _load_session(code: str) -> Optional[dict]:
    p = _session_path(code)
    if not p.exists():
        return None
    with open(p) as f:
        return json.load(f)


def _save_session(data: dict) -> None:
    code = data["group_code"]
    with open(_session_path(code), "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _new_group_code() -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
