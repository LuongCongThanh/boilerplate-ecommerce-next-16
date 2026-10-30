"""Hàm dùng chung cho các script của ship-ticket-fashion: git, thư mục state, tìm ticket."""

from __future__ import annotations

import json
from pathlib import Path

from gitcmd import git, repo_root
from progress import Feature, Ticket, load_features


def state_dir() -> Path:
    path = Path(git("rev-parse", "--absolute-git-dir")) / "ship-ticket-fashion"
    path.mkdir(parents=True, exist_ok=True)
    return path


def state_path(feature: str, num: int) -> Path:
    return state_dir() / f"{feature}-{num:02d}.json"


def resolve(arg: str, features: dict[str, Feature] | None = None) -> tuple[Feature, Ticket]:
    """`<feature>/<NN>`, `<NN>` hoặc đường dẫn ticket → (feature, ticket)."""
    features = features if features is not None else load_features(repo_root())
    path = Path(arg)
    if path.suffix == ".md" and path.exists():
        feature, num = path.resolve().parent.parent.name, int(path.name.split("-", 1)[0])
    elif "/" in arg:
        feature, _, raw = arg.partition("/")
        num = int(raw)
    else:
        num = int(arg)
        matches = [f.slug for f in features.values() if num in f.tickets]
        open_matches = [s for s in matches if features[s].tickets[num].status != "resolved"]
        candidates = open_matches or matches
        if len(candidates) != 1:
            raise SystemExit(
                f"Ticket {num:02d} không rõ thuộc feature nào: {', '.join(matches) or 'không có'}. "
                "Dùng dạng <feature>/<NN>."
            )
        feature = candidates[0]
    if feature not in features or num not in features[feature].tickets:
        raise SystemExit(f"Không thấy ticket {feature}/{num:02d}")
    return features[feature], features[feature].tickets[num]


def ticket_ref(ticket: Ticket) -> str:
    """Đường dẫn ticket tính từ gốc repo, dạng dùng trong state và trailer `Refs:`."""
    return ticket.path.relative_to(ticket.path.parents[3]).as_posix()


def load_state(feature: str, num: int) -> dict | None:
    path = state_path(feature, num)
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def save_state(state: dict) -> Path:
    path = state_path(state["feature"], state["num"])
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)
    return path
