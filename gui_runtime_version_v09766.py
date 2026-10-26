"""Runtime version label derived from Git branch, with safe fallback."""
from pathlib import Path
import subprocess

FALLBACK = "v0.9.7.66"

def runtime_version(root=None):
    root = Path(root) if root else Path(__file__).resolve().parent
    try:
        result = subprocess.run(["git", "-C", str(root), "branch", "--show-current"], capture_output=True, text=True, timeout=2, check=False)
        name = result.stdout.strip()
        if result.returncode == 0 and name and not any(c in name for c in "\r\n\t"):
            return name
    except (OSError, subprocess.TimeoutExpired):
        pass
    return FALLBACK
