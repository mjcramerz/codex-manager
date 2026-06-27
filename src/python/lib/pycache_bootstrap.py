from __future__ import annotations

import os
from pathlib import Path
import sys


DEFAULT_PYCACHE_PREFIX = "/tmp/codex-pycache"


def bootstrap_pycache_prefix(default: str = DEFAULT_PYCACHE_PREFIX) -> str:
    raw = os.environ.get("PYTHONPYCACHEPREFIX", "").strip()
    if not raw or any(ch in raw for ch in ("\x00", "\n", "\r")):
        raw = default

    target = Path(raw)
    if not target.is_absolute():
        target = Path(default)

    try:
        target.mkdir(parents=True, exist_ok=True)
    except OSError:
        return str(target)

    rendered = str(target)
    os.environ["PYTHONPYCACHEPREFIX"] = rendered
    sys.pycache_prefix = rendered
    return rendered
