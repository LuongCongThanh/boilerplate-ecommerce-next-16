"""Gọi git cho mọi script của ship-ticket-fashion.

Tách khỏi common.py vì common.py import progress.py; progress.py import file này thì không vòng.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


def git(*args: str, strip: bool = True) -> str:
    """stdout của git, rỗng khi lỗi. Porcelain cần `strip=False`: dấu cách đầu là mã trạng thái."""
    out = subprocess.run(["git", *args], capture_output=True, text=True, encoding="utf-8")
    if out.returncode != 0:
        return ""
    return out.stdout.strip() if strip else out.stdout


def repo_root() -> Path:
    root = git("rev-parse", "--show-toplevel")
    if not root:
        raise SystemExit("Không ở trong git repo")
    return Path(root)
