"""
run.py  —  single entry point for the whole project
Usage:  python run.py

This file lives at the project root so Python's working directory is
automatically the repo root, which means all  `from GUI.xxx import ...`
and  `from backend.xxx import ...`  package imports resolve correctly
without needing to set PYTHONPATH manually.
"""
import sys
import os
from pathlib import Path

# ── guarantee the project root is on sys.path ────────────────────────────
# This is the one job this file has — after this line every sub-package
# (GUI, backend) is importable regardless of how the user invoked the script.
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# ── also set PYTHONPATH in the environment so child processes inherit it ──
os.environ.setdefault("PYTHONPATH", str(ROOT))

# ── hand off to the real entry point ─────────────────────────────────────
from GUI.app import main

if __name__ == "__main__":
    main()
