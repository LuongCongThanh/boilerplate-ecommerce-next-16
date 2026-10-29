"""Đóng ticket trong PR của nó: Status resolved, dòng **PR:**, tick acceptance criteria.

Theo docs/agents/issue-tracker.md mục "Đóng ticket".
python .claude/skills/ship-ticket-fashion/scripts/close_ticket.py <ticket.md> --pr 23
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def close(text: str, pr: int) -> tuple[str, list[str]]:
    if not re.search(r"^Status:", text, re.M):
        raise SystemExit("Ticket không có dòng Status:")
    status_line = "Status: resolved"
    if not re.search(r"\*\*PR:\*\*", text):
        status_line += f"\n\n**PR:** #{pr}"
    text = re.sub(r"^Status:.*$", status_line, text, count=1, flags=re.M)

    match = re.search(r"^## Acceptance criteria\s*$(.*?)(?=^## |\Z)", text, re.M | re.S)
    if not match:
        return text, []
    body = match.group(1)
    ticked = re.findall(r"^\s*- \[ \] (.+)$", body, re.M)
    body = re.sub(r"^(\s*)- \[ \]", r"\1- [x]", body, flags=re.M)
    return text[: match.start(1)] + body + text[match.end(1) :], ticked


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("ticket", type=Path)
    parser.add_argument("--pr", type=int, required=True, help="số PR đóng ticket")
    args = parser.parse_args()

    text = args.ticket.read_text(encoding="utf-8")
    new_text, ticked = close(text, args.pr)
    args.ticket.write_text(new_text, encoding="utf-8", newline="\n")

    print(f"{args.ticket}: Status resolved, PR #{args.pr}")
    if ticked:
        print("Đã tick (đối chiếu từng mục với báo cáo):")
        for item in ticked:
            print(f"  - {item}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
