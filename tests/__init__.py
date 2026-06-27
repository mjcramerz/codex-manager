from __future__ import annotations

from pathlib import Path
import sys


PYTHON_SRC = Path(__file__).resolve().parents[1] / "src" / "python"
if str(PYTHON_SRC) not in sys.path:
    sys.path.insert(0, str(PYTHON_SRC))

from lib.pycache_bootstrap import bootstrap_pycache_prefix

bootstrap_pycache_prefix()
