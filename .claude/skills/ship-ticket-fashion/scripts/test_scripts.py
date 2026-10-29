"""Test cho các script của skill (stdlib unittest, không cần môi trường backend).

python -m unittest discover -s .claude/skills/ship-ticket-fashion/scripts
"""

# ruff: noqa: PT009
from __future__ import annotations

import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from check_ac_trace import test_exists, trace
from check_ship import check_subjects, diff_size
from close_ticket import close
from progress import Feature, frontier, parse_ticket
from state import apply, check_transition, validate

TICKET = """# Lớp API

Status: ready-for-agent

Blocked by: 09

Spec: [spec.md](../spec.md)

## Việc cần làm

- [ ] không phải AC

## Acceptance criteria

- [ ] lỗi trả ErrorDTO
- [x] page_size tối đa 100

## Comments
"""


def make_state(**overrides) -> dict:
    state = {
        "ticket": "x.md",
        "feature": "f",
        "num": 1,
        "branch": "feat/x",
        "mode": "full",
        "phase": "grill",
        "gates": {"g1": None, "g2": None},
        "slices": [],
        "pr": None,
    }
    state.update(overrides)
    return state


class TicketParsing(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.path = self.dir / "16-shared-api.md"
        self.path.write_text(TICKET, encoding="utf-8")

    def test_counts_only_acceptance_criteria(self):
        ticket = parse_ticket(self.path)
        self.assertEqual(
            (ticket.num, ticket.status, ticket.blocked_by), (16, "ready-for-agent", [9])
        )
        self.assertEqual((ticket.ac_done, ticket.ac_total), (1, 2))

    def test_frontier_skips_open_blockers_and_follows_spec_order(self):
        def ticket(num, status, blocked=()):
            return replace(
                parse_ticket(self.path), num=num, status=status, blocked_by=list(blocked)
            )

        feature = Feature(slug="f", spec_order=[15, 12])
        for num, status, blocked in [
            (9, "resolved", ()),
            (12, "ready-for-agent", (9,)),
            (15, "ready-for-agent", ()),
            (16, "ready-for-agent", (15,)),
        ]:
            feature.tickets[num] = ticket(num, status, blocked)
        self.assertEqual([t.num for t in frontier(feature)], [15, 12])

    def test_close_sets_status_pr_and_ticks_only_acceptance_criteria(self):
        text, ticked = close(TICKET, 23)
        self.assertIn("Status: resolved\n\n**PR:** #23", text)
        self.assertIn("- [ ] không phải AC", text)
        self.assertIn("- [x] lỗi trả ErrorDTO", text)
        self.assertEqual(ticked, ["lỗi trả ErrorDTO"])


class StateMachine(unittest.TestCase):
    def test_code_needs_g1(self):
        self.assertIsNotNone(check_transition(make_state(), "code", None))
        self.assertIsNone(check_transition(make_state(), "code", "g1"))

    def test_rejects_skipping_phases(self):
        self.assertIn("không đi được", check_transition(make_state(), "review", None))

    def test_report_needs_every_slice_done(self):
        state = make_state(phase="code", slices=[{"id": "S1", "status": "code"}])
        self.assertIsNotNone(check_transition(state, "report", None))

    def test_ship_needs_g2_and_review_may_return_to_code(self):
        self.assertIsNotNone(check_transition(make_state(phase="sync"), "ship", None))
        self.assertIsNone(check_transition(make_state(phase="review"), "code", None))

    def test_validate_rejects_cycles_and_unknown_acs(self):
        slices = [
            {"id": "S1", "acs": [1], "dependsOn": ["S2"], "status": "todo"},
            {"id": "S2", "acs": [5], "dependsOn": ["S1"], "status": "todo"},
        ]
        errors = validate(make_state(slices=slices), ac_total=2)
        self.assertTrue(any("vòng lặp" in e for e in errors))
        self.assertTrue(any("AC 5" in e for e in errors))

    def test_apply_selects_slice_by_id_and_parses_json(self):
        state = make_state(slices=[{"id": "S1", "status": "todo"}])
        apply(state, ["slices.S1.status=done", "pr=23", "next=S2: viết test"], push=False)
        apply(state, ['slices=[{"id": "S2", "status": "todo"}]'], push=True)
        self.assertEqual(state["slices"][0]["status"], "done")
        self.assertEqual((state["pr"], state["next"]), (23, "S2: viết test"))
        self.assertEqual([s["id"] for s in state["slices"]], ["S1", "S2"])


class Checks(unittest.TestCase):
    def test_trace_reports_uncovered_ac_and_missing_test(self):
        backend = Path(tempfile.mkdtemp())
        (backend / "tests").mkdir()
        (backend / "tests" / "test_a.py").write_text(
            "class TestA:\n    def test_ok(self):\n", encoding="utf-8"
        )
        state = make_state(
            slices=[
                {
                    "id": "S1",
                    "acs": [1],
                    "tests": ["tests/test_a.py::TestA::test_ok", "tests/test_a.py::test_gone"],
                }
            ],
            untestable={},
        )
        problems = trace(state, ac_total=2, backend=backend, planned=False)
        self.assertTrue(any(p.startswith("AC 2") for p in problems))
        self.assertTrue(any("test_gone" in p for p in problems))
        self.assertTrue(test_exists(backend, "tests/test_a.py::TestA::test_ok"))

    def test_conventional_subjects(self):
        good = [
            "feat(shared): add ErrorDTO handler",
            "docs: close shared core ticket",
            "fix(ci)!: drop x",
        ]
        bad = ["Add stuff", "feat(shared): Add handler", "fix: trailing dot."]
        self.assertEqual(check_subjects(good + bad), bad)

    def test_diff_size_skips_generated_files(self):
        numstat = (
            "10\t2\tbackend/shared/api.py\n"
            "300\t0\tbackend/modules/x/migrations/0001.py\n"
            "5\t5\tuv.lock\n"
        )
        self.assertEqual(diff_size(numstat), 12)


if __name__ == "__main__":
    unittest.main()
