"""Chạy một lệnh, ghi toàn bộ output vào log, chỉ in tóm tắt (xanh) hoặc đoạn cuối (đỏ).

python .claude/skills/ship-ticket-fashion/scripts/run_logged.py --label test --cwd backend \
    -- make test
Log: .git/ship-ticket-fashion/logs/<label>.log
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from common import repo_root, state_dir


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--label", required=True)
    parser.add_argument("--cwd", default=".", help="thư mục chạy, tính từ gốc repo")
    parser.add_argument("--tail", type=int, default=40, help="số dòng cuối in ra khi lệnh đỏ")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        parser.error("thiếu lệnh sau --")

    logs = state_dir() / "logs"
    logs.mkdir(exist_ok=True)
    log = logs / f"{args.label}.log"
    proc = subprocess.run(
        command,
        cwd=repo_root() / Path(args.cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    output = proc.stdout + proc.stderr
    log.write_text(f"$ {' '.join(command)}\n{output}\nexit {proc.returncode}\n", encoding="utf-8")

    lines = [line for line in output.splitlines() if line.strip()]
    if proc.returncode == 0:
        print(f"OK {args.label} · {lines[-1] if lines else '(không có output)'} · log {log}")
    else:
        print(f"RED {args.label} (exit {proc.returncode}) · log {log}")
        print("\n".join(lines[-args.tail :]))
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
