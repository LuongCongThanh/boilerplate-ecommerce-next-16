"""PreToolUse hook: agent chỉ được merge PR vào `dev`; `uat` và `main` do người làm.

Chặn (exit 2) lệnh shell có:
- `gh pr merge` cho PR có base khác `dev` (tra base bằng `gh pr view`; không tra được thì chặn);
- `gh api` gọi endpoint merge (REST `pulls/<n>/merge`, `merges`) hoặc mutation merge của GraphQL;
- `git push` có đích là `uat` / `main`: ghi rõ, qua `HEAD`, hoặc không ghi đích khi nhánh hiện tại,
  upstream, hay nhánh vừa `checkout` / `switch` trong cùng lệnh là `uat` / `main`;
  cả `--all` / `--mirror`.
Lỗi bất kỳ trong hook cũng chặn. Promote `dev` → `uat` và release `uat` → `main` theo
docs/architecture/11-git-workflow.md mục 4.3.
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
MERGE_VALUE_FLAGS = {"-t", "--subject", "-b", "--body", "-F", "--body-file", "-A",
                     "--author-email", "--match-head-commit", "-R", "--repo"}
PUSH_VALUE_FLAGS = {"-o", "--push-option", "--repo", "--receive-pack", "--exec"}

QUOTED = r"(?:\"[^\"]*\"|'[^']*'|\S+)"
ENV = rf"(?:\w+={QUOTED}\s+)*"
WRAPPERS = r"(?:(?:env|command|exec|nohup|time|sudo|xargs)(?:\s+-\S+)*\s+)*"
# vị trí lệnh: đầu dòng, sau ; & | ( ` $( hoặc trong `bash -c "…"`; có thể có gán biến, wrapper
AT_COMMAND = rf"(?:^|[;&|(`]|\$\(|-c\s+[\"'])\s*{ENV}{WRAPPERS}{ENV}"
GH = r"gh(?:\.exe)?"
# option chung của git đứng trước subcommand: -C <dir>, -c <k=v>, --git-dir=…, --no-pager…
GIT = rf"git(?:\.exe)?((?:\s+(?:-[Cc]\s+{QUOTED}|--[\w-]+(?:={QUOTED})?|-[pP]))*)"
SEGMENT = r"([^;&|\n]*)"
HEREDOC = re.compile(r"<<-?\s*(['\"]?)(\w+)\1[^\n]*\n.*?^\s*\2\s*$", re.S | re.M)
SHELL = re.compile(r"\b(?:ba|z|da|k)?sh(?:\.exe)?\b|\bpwsh\b|\bpowershell\b")
GRAPHQL_MERGE = re.compile(r"mergePullRequest|enablePullRequestAutoMerge|mergeBranch|query=@")


def strip_heredocs(command: str) -> str:
    """Thân heredoc là dữ liệu (thân PR, message), trừ khi heredoc được đưa cho shell chạy."""

    def replace(match: re.Match) -> str:
        line_start = command.rfind("\n", 0, match.start()) + 1
        first_line = command[line_start : command.find("\n", match.start())]
        return match.group(0) if SHELL.search(first_line) else "<<HEREDOC"

    return HEREDOC.sub(replace, command)


def tokens(raw: str) -> list[str]:
    try:
        return shlex.split(raw)
    except ValueError:
        return raw.split()


def git_out(*args: str, cwd: str | None = None) -> str:
    proc = subprocess.run(["git", *args], capture_output=True, text=True, encoding="utf-8",
                          cwd=cwd or os.environ.get("CLAUDE_PROJECT_DIR") or None)
    return proc.stdout.strip() if proc.returncode == 0 else ""


def pr_base(selector: str | None, repo: str | None) -> str:
    view = ["gh", "pr", "view", *([selector] if selector else []), "--json", "baseRefName",
            "-q", ".baseRefName", *(["-R", repo] if repo else [])]
    proc = subprocess.run(view, capture_output=True, text=True, encoding="utf-8",
                          cwd=os.environ.get("CLAUDE_PROJECT_DIR") or None)
    return proc.stdout.strip() if proc.returncode == 0 else ""


def current_branch(cwd: str | None) -> str:
    return git_out("branch", "--show-current", cwd=cwd)


def upstream_branch(cwd: str | None) -> str:
    """`origin/main` → `main`; không có upstream → ""."""
    upstream = git_out("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}", cwd=cwd)
    return upstream.split("/", 1)[1] if "/" in upstream else ""


def merge_problem(args: list[str]) -> str | None:
    selector, repo, skip = None, None, False
    for i, arg in enumerate(args):
        if skip:
            skip = False
            continue
        if arg.startswith("--repo="):
            repo = arg.split("=", 1)[1]
        elif arg.startswith("-R") and len(arg) > 2:
            repo = arg[2:]
        elif arg in MERGE_VALUE_FLAGS:
            if arg in ("-R", "--repo") and i + 1 < len(args):
                repo = args[i + 1]
            skip = True
        elif not arg.startswith("-") and selector is None:
            selector = arg
    base = pr_base(selector, repo)
    if not base:
        return f"không tra được base của PR {selector or '(nhánh hiện tại)'}; ghi rõ số PR"
    if base != ALLOWED_BASE:
        return f"PR {selector or ''} có base `{base}`: agent chỉ merge PR vào `{ALLOWED_BASE}`"
    return None


def git_cwd(global_opts: str) -> str | None:
    opts = tokens(global_opts)
    for i, opt in enumerate(opts):
        if opt == "-C" and i + 1 < len(opts):
            return opts[i + 1]
    return None


def push_destinations(args: list[str], cwd: str | None, switched: set[str]) -> set[str]:
    positional, skip = [], False
    for arg in args:
        if skip:
            skip = False
        elif arg in PUSH_VALUE_FLAGS:
            skip = True
        elif not arg.startswith("-"):
            positional.append(arg)
    refspecs = positional[1:]
    if not refspecs:  # `git push` / `git push origin`: đẩy nhánh hiện tại lên upstream
        return {current_branch(cwd), upstream_branch(cwd), *switched}
    dests = set()
    for refspec in refspecs:
        dest = refspec.rsplit(":", 1)[-1].removeprefix("+").removeprefix("refs/heads/")
        dests |= {current_branch(cwd), *switched} if dest == "HEAD" else {dest}
    return dests


def push_problem(args: list[str], cwd: str | None, switched: set[str]) -> str | None:
    if any(a in ("--all", "--mirror") for a in args):
        return "`git push --all/--mirror` có thể đẩy lên uat/main"
    hit = push_destinations(args, cwd, switched) & PROTECTED
    if hit:
        return f"push lên `{', '.join(sorted(hit))}`: chỉ đi qua PR, và PR vào uat/main do người merge"
    return None


def check(command: str) -> str | None:
    command = strip_heredocs(command)
    flags = re.M
    for raw in re.findall(AT_COMMAND + GH + r"\s+pr\s+merge\b" + SEGMENT, command, flags):
        if problem := merge_problem(tokens(raw)):
            return problem
    api = AT_COMMAND + GH + r"\s+api\b"
    if re.search(api + r"[^;&|\n]*(?:pulls/\d+/merge|/merges)\b", command, flags):
        return "merge qua REST `gh api`: dùng `gh pr merge` để hook kiểm base"
    if re.search(api + r"\s+graphql\b", command, flags) and GRAPHQL_MERGE.search(command):
        return "merge qua GraphQL `gh api graphql`: dùng `gh pr merge` để hook kiểm base"
    switched = set(re.findall(AT_COMMAND + GIT + r"\s+(?:checkout|switch)\s+(?:-\S+\s+)*(\w+)\b",
                              command, flags))
    switched = {branch for _, branch in switched} & PROTECTED
    for global_opts, raw in re.findall(AT_COMMAND + GIT + r"\s+push\b" + SEGMENT, command, flags):
        if problem := push_problem(tokens(raw), git_cwd(global_opts), switched):
            return problem
    return None


def main() -> int:
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")
    try:
        payload = json.load(sys.stdin)
        problem = check(payload.get("tool_input", {}).get("command", ""))
    except Exception as exc:  # noqa: BLE001 — hook lỗi thì chặn, không để lệnh lọt
        problem = f"hook lỗi ({type(exc).__name__}: {exc}), chặn cho an toàn"
    if problem:
        print(f"Chặn bởi .claude/hooks/guard_merge_target.py: {problem}. "
              "Promote dev → uat và release uat → main do người dùng merge trên GitHub.",
              file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
