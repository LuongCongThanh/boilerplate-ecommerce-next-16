"""PreToolUse hook: agent chỉ được merge PR vào `dev`; `uat` và `main` do người làm.

Chặn (exit 2) lệnh shell có:
- `gh pr merge` cho PR có base khác `dev` (tra base bằng `gh pr view`; không tra được thì chặn);
- `gh api` gọi endpoint merge của PR;
- `git push` lên `uat` / `main`, hoặc `--all` / `--mirror`.
Promote `dev` → `uat` và release `uat` → `main` theo docs/architecture/11-git-workflow.md mục 4.3.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import sys

ALLOWED_BASE = "dev"
PROTECTED = {"uat", "main"}
# flag của `gh pr merge` có nhận giá trị: bỏ qua giá trị khi tìm số PR
VALUE_FLAGS = {"-t", "--subject", "-b", "--body", "-F", "--body-file", "-A", "--author-email",
               "--match-head-commit", "-R", "--repo"}
SEGMENT = r"([^;&|\n]*)"


def tokens(raw: str) -> list[str]:
    try:
        return shlex.split(raw)
    except ValueError:
        return raw.split()


def merge_problem(args: list[str]) -> str | None:
    selector, repo, skip = None, None, False
    for i, arg in enumerate(args):
        if skip:
            skip = False
            continue
        if arg in ("-R", "--repo"):
            repo = args[i + 1] if i + 1 < len(args) else None
        if arg in VALUE_FLAGS:
            skip = True
        elif not arg.startswith("-") and selector is None:
            selector = arg
    view = ["gh", "pr", "view", *([selector] if selector else []), "--json", "baseRefName",
            "-q", ".baseRefName", *(["-R", repo] if repo else [])]
    proc = subprocess.run(view, capture_output=True, text=True, encoding="utf-8",
                          cwd=os.environ.get("CLAUDE_PROJECT_DIR") or None)
    base = proc.stdout.strip()
    if proc.returncode != 0 or not base:
        return f"không tra được base của PR {selector or '(nhánh hiện tại)'}; ghi rõ số PR"
    if base != ALLOWED_BASE:
        return f"PR {selector or ''} có base `{base}`: agent chỉ merge PR vào `{ALLOWED_BASE}`"
    return None


def push_problem(args: list[str]) -> str | None:
    if any(a in ("--all", "--mirror") for a in args):
        return "`git push --all/--mirror` có thể đẩy lên uat/main"
    for arg in args:
        if arg.startswith("-"):
            continue
        dest = arg.rsplit(":", 1)[-1].removeprefix("+").removeprefix("refs/heads/")
        if dest in PROTECTED:
            return f"push lên `{dest}`: chỉ đi qua PR, và PR vào uat/main do người merge"
    return None


def check(command: str) -> str | None:
    for raw in re.findall(r"\bgh\s+pr\s+merge\b" + SEGMENT, command):
        if problem := merge_problem(tokens(raw)):
            return problem
    if re.search(r"\bgh\s+api\b[^;&|\n]*pulls/\d+/merge\b", command):
        return "merge PR qua `gh api`: dùng `gh pr merge` để hook kiểm base"
    for raw in re.findall(r"\bgit\s+push\b" + SEGMENT, command):
        if problem := push_problem(tokens(raw)):
            return problem
    return None


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    payload = json.load(sys.stdin)
    problem = check(payload.get("tool_input", {}).get("command", ""))
    if problem:
        print(f"Chặn bởi .claude/hooks/guard_merge_target.py: {problem}. "
              "Promote dev → uat và release uat → main do người dùng merge trên GitHub.",
              file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
