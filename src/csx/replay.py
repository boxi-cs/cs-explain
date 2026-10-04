"""Pure replay and comparison helpers; no source code is executed."""

from __future__ import annotations

from typing import Any

from .model import Trace


def replay(trace: Trace) -> list[dict[str, Any]]:
    """Apply state deltas in event order and return a learner-readable timeline."""
    state: dict[str, Any] = {}
    timeline: list[dict[str, Any]] = []
    for event in trace.events:
        state.update(event["state_delta"])
        timeline.append(
            {
                "event_id": event["id"],
                "logical_time": event["logical_time"],
                "operation": event["operation"],
                "observation": event["observation"],
                "state": dict(state),
                "assertions": list(event["assertions"]),
            }
        )
    return timeline


def compare(left: Trace, right: Trace) -> dict[str, Any]:
    """Compare event outcomes while retaining a stable, text-friendly shape."""
    left_events = {event["id"]: event for event in left.events}
    right_events = {event["id"]: event for event in right.events}
    ids = list(dict.fromkeys([event["id"] for event in left.events] + [event["id"] for event in right.events]))
    differences: list[dict[str, Any]] = []
    left_timeline = {item["event_id"]: item for item in replay(left)}
    right_timeline = {item["event_id"]: item for item in replay(right)}
    for event_id in ids:
        l = left_timeline.get(event_id)
        r = right_timeline.get(event_id)
        if l != r:
            differences.append({"event_id": event_id, "left": l, "right": r})
    return {
        "left": left.trace_id,
        "right": right.trace_id,
        "same_event_ids": [event_id for event_id in ids if event_id in left_events and event_id in right_events],
        "differences": differences,
        "assertions": {
            "left_failed": [a["id"] for a in left.assertions if a["status"] == "fail"],
            "right_failed": [a["id"] for a in right.assertions if a["status"] == "fail"],
        },
    }
