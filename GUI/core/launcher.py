"""
GUI/core/launcher.py
Starts and health-checks the FastAPI backend subprocess.
Isolated here so app.py stays clean and this logic is easy to test/swap.
"""
import sys
import subprocess
import time
from pathlib import Path

from GUI.core.api_client import health_check


def start_backend() -> subprocess.Popen:
    """
    Spawn the uvicorn backend as a background subprocess.
    Returns the Popen handle so the caller can terminate it on exit.
    """
    backend_dir = Path(__file__).resolve().parent.parent.parent / "backend"
    cmd = [
        sys.executable, "-m", "uvicorn", "main:app",
        "--host", "127.0.0.1", "--port", "8000",
        "--log-level", "warning",
    ]
    return subprocess.Popen(
        cmd, cwd=str(backend_dir),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def wait_for_backend(timeout: float = 15.0, poll: float = 0.4) -> bool:
    """
    Poll /health until the backend responds or the timeout expires.
    Returns True if the backend came up, False otherwise.
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        if health_check():
            return True
        time.sleep(poll)
    return False
