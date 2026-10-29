"""Kiểm tra trước G2 và trước push theo docs/architecture/11-git-workflow.md.

python .claude/skills/ship-ticket-fashion/scripts/check_ship.py <T>
In OK / WARN / FAIL từng mục rồi SHIP OK hoặc SHIP FAIL. Mỗi WARN / FAIL là một điểm của G2.
"""

from __future__ import annotations

import argparse
import re
import sys

from common import git, load_state, resolve

BRANCH = re.compile(r"^(feat|fix|refactor|docs|chore|test|hotfix)/[a-z0-9]+(-[a-z0-9]+)*$")
TYPES = "feat|fix|perf|refactor|test|docs|build|ci|chore|revert"
SUBJECT = re.compile(rf"^({TYPES})(\([a-z0-9-]+\))?!?: [a-z0-9`].*[^.]$")
GENERATED = ("/migrations/", "uv.lock", "openapi.yaml")
MAX_LINES = 400


def check_subjects(subjects: list[str]) -> list[str]:
    return [s for s in subjects if not SUBJECT.match(s)]


def diff_size(numstat: str) -> int:
    total = 0
    for line in numstat.splitlines():
        added, deleted, path = line.split("\t", 2)
        if added == "-" or any(g in path for g in GENERATED):
            continue
        total += int(added) + int(deleted)
    return total


def compare_with_dev() -> list[tuple[str, str]]:
    results = []
    behind = int(git("rev-list", "--count", "HEAD..origin/dev") or 0)
    results.append(
        (
            "WARN" if behind else "OK",
            f"sau origin/dev {behind} commit (git fetch trước để chính xác)",
        )
    )

    # commit merge (kéo dev về nhánh) mất khi squash nên không kiểm tên
    subjects = git("log", "--no-merges", "--format=%s", "origin/dev..HEAD").splitlines()
    bad = check_subjects(subjects)
    results.append(
        ("FAIL" if bad else "OK", f"{len(subjects)} commit, {len(bad)} sai Conventional Commits")
    )
    results.extend(("FAIL", f"  commit: {s}") for s in bad)

    size = diff_size(git("diff", "--numstat", "origin/dev...HEAD"))
    results.append(
        ("WARN" if size > MAX_LINES else "OK", f"{size} dòng đổi (không tính migration, file sinh)")
    )
    return results


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("ticket")
    args = parser.parse_args()

    feature, ticket = resolve(args.ticket)
    state = load_state(feature.slug, ticket.num) or {}
    results: list[tuple[str, str]] = []

    branch = git("branch", "--show-current")
    if state and branch != state.get("branch"):
        results.append(("FAIL", f"nhánh {branch} khác nhánh của state {state.get('branch')}"))
    results.append(("OK" if BRANCH.match(branch) else "WARN", f"tên nhánh {branch}"))

    dirty = git("status", "--porcelain").splitlines()
    results.append(("FAIL" if dirty else "OK", f"{len(dirty)} file chưa commit"))

    # git() trả "" khi lỗi: thiếu origin/dev thì mọi phép so sánh bên dưới thành 0 và báo OK sai.
    if not git("rev-parse", "--verify", "--quiet", "origin/dev"):
        results.append(("FAIL", "không thấy origin/dev (chạy git fetch origin dev)"))
    else:
        results.extend(compare_with_dev())

    for level, message in results:
        print(f"{level} {message}")
    failed = any(level == "FAIL" for level, _ in results)
    print("SHIP FAIL" if failed else "SHIP OK")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
