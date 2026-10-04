from __future__ import annotations

import json
from pathlib import Path

import pytest

from csx.model import Trace, load_trace
from csx.replay import compare, replay
from csx.validate import ValidationError, validate_trace


ROOT = Path(__file__).parents[1]
FIXTURES = ROOT / "fixtures"


def test_both_educational_fixtures_validate() -> None:
    for path in FIXTURES.glob("*.json"):
        trace = load_trace(path)
        validate_trace(trace)


def test_replay_is_deterministic_and_preserves_source_to_state_path() -> None:
    trace = load_trace(FIXTURES / "agent-loop-context.correct.json")
    validate_trace(trace)
    first = replay(trace)
    second = replay(trace)
    assert first == second
    assert first[-1]["state"]["observation"] == "green"
    assert first[1]["assertions"] == ["a0"]


def test_compare_exposes_learner_visible_difference() -> None:
    correct = load_trace(FIXTURES / "agent-loop-context.correct.json")
    incorrect = load_trace(FIXTURES / "agent-loop-context.incorrect.json")
    validate_trace(correct)
    validate_trace(incorrect)
    result = compare(correct, incorrect)
    assert result["differences"][0]["event_id"] == "e1"
    assert result["assertions"] == {"left_failed": [], "right_failed": ["a0", "a1"]}


@pytest.mark.parametrize(
    "mutator, message",
    [
        (lambda data: data["events"].__setitem__(1, {**data["events"][1], "id": data["events"][0]["id"]}), "duplicate event id"),
        (lambda data: data["events"][1].__setitem__("causal_parents", ["future"]), "unknown or future causal parent"),
        (lambda data: data.__setitem__("timestamp", "2026-10-04T00:00:00Z"), "non-deterministic metadata"),
        (lambda data: data["events"][1].__setitem__("logical_time", -1), "non-decreasing logical_time"),
    ],
)
def test_invalid_contract_is_rejected(mutator, message: str) -> None:
    data = json.loads((FIXTURES / "agent-loop-context.correct.json").read_text())
    mutator(data)
    with pytest.raises(ValidationError, match=message):
        validate_trace(Trace(data))


def test_assertion_must_be_linked_from_event() -> None:
    data = json.loads((FIXTURES / "agent-loop-context.correct.json").read_text())
    data["events"][1]["assertions"] = []
    with pytest.raises(ValidationError, match="not linked from its event"):
        validate_trace(Trace(data))
