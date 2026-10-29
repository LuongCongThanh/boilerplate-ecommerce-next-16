"""Gọi git cho mọi script của ship-ticket-fashion.

Tách khỏi common.py vì common.py import progress.py; progress.py import file này thì không vòng.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


def git(*args: str) -> str:
    out = subprocess.run(["git", *args], capture_output=True, text=True, encoding="utf-8")
    return out.stdout.strip() if out.returncode == 0 else ""


def repo_root() -> Path:
    root = git("rev-parse", "--show-toplevel")
    if not root:
        raise SystemExit("Không ở trong git repo")
    return Path(root)
