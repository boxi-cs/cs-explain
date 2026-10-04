"""Deterministic validation for the learner-facing trace contract."""

from __future__ import annotations

from typing import Any

from .model import Trace


class ValidationError(ValueError):
    """A trace violates a contract rule."""


ROOT_KEYS = {
    "schema_version",
    "trace_id",
    "title",
    "seed",
    "source",
    "events",
    "assertions",
    "text_fallback",
}
EVENT_KEYS = {
    "id",
    "logical_time",
    "actor",
    "operation",
    "source_span",
    "state_delta",
    "observation",
    "causal_parents",
    "assertions",
}
ASSERTION_KEYS = {"id", "kind", "description", "event_id", "status", "evidence"}
FORBIDDEN_METADATA_KEYS = {"timestamp", "created_at", "updated_at", "random", "uuid"}


def _object(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValidationError(f"{path} must be an object")
    return value


def _string(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{path} must be a non-empty string")
    return value


def _list(value: Any, path: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValidationError(f"{path} must be an array")
    return value


def _keys(value: dict[str, Any], allowed: set[str], path: str) -> None:
    unknown = sorted(set(value) - allowed)
    if unknown:
        dynamic = sorted(set(unknown) & FORBIDDEN_METADATA_KEYS)
        if dynamic:
            raise ValidationError(f"{path} contains non-deterministic metadata: {', '.join(dynamic)}")
        raise ValidationError(f"{path} has unknown keys: {', '.join(unknown)}")


def validate_trace(trace: Trace) -> None:
    """Validate structure, ordering, links and deterministic metadata.

    This function never runs source code. It only inspects JSON values.
    """
    root = _object(trace.document, "trace")
    _keys(root, ROOT_KEYS, "trace")
    required = ROOT_KEYS
    missing = sorted(required - set(root))
    if missing:
        raise ValidationError(f"trace is missing required keys: {', '.join(missing)}")
    if root["schema_version"] != "trace/v0.1":
        raise ValidationError("trace.schema_version must be trace/v0.1")
    _string(root["trace_id"], "trace.trace_id")
    _string(root["title"], "trace.title")
    if isinstance(root["seed"], bool) or not isinstance(root["seed"], int):
        raise ValidationError("trace.seed must be an integer")
    _string(root["text_fallback"], "trace.text_fallback")

    source = _object(root["source"], "trace.source")
    if not source:
        raise ValidationError("trace.source must contain at least one source file")
    for filename, contents in source.items():
        _string(filename, "trace.source filename")
        if not isinstance(contents, str):
            raise ValidationError(f"trace.source[{filename!r}] must be a string")

    for key in root:
        if key in FORBIDDEN_METADATA_KEYS:
            raise ValidationError(f"trace contains non-deterministic metadata: {key}")

    events = _list(root["events"], "trace.events")
    if not events:
        raise ValidationError("trace.events must contain at least one event")
    assertions = _list(root["assertions"], "trace.assertions")
    event_ids: set[str] = set()
    last_time = -1
    for index, raw_event in enumerate(events):
        path = f"trace.events[{index}]"
        event = _object(raw_event, path)
        _keys(event, EVENT_KEYS, path)
        missing_event = sorted(EVENT_KEYS - set(event))
        if missing_event:
            raise ValidationError(f"{path} is missing required keys: {', '.join(missing_event)}")
        event_id = _string(event["id"], f"{path}.id")
        if event_id in event_ids:
            raise ValidationError(f"duplicate event id: {event_id}")
        event_ids.add(event_id)
        logical_time = event["logical_time"]
        if isinstance(logical_time, bool) or not isinstance(logical_time, int):
            raise ValidationError(f"{path}.logical_time must be an integer")
        if logical_time < 0 or logical_time < last_time:
            raise ValidationError("events must have non-decreasing logical_time")
        last_time = logical_time
        _string(event["actor"], f"{path}.actor")
        _string(event["operation"], f"{path}.operation")
        span = _object(event["source_span"], f"{path}.source_span")
        if set(span) != {"file", "line"}:
            raise ValidationError(f"{path}.source_span must contain file and line only")
        if span["file"] not in source:
            raise ValidationError(f"{path}.source_span.file is not in trace.source")
        if isinstance(span["line"], bool) or not isinstance(span["line"], int) or span["line"] < 1:
            raise ValidationError(f"{path}.source_span.line must be a positive integer")
        if not isinstance(event["state_delta"], dict):
            raise ValidationError(f"{path}.state_delta must be an object")
        _string(event["observation"], f"{path}.observation")
        parents = _list(event["causal_parents"], f"{path}.causal_parents")
        for parent in parents:
            _string(parent, f"{path}.causal_parents item")
            if parent not in event_ids:
                raise ValidationError(f"{path} refers to unknown or future causal parent: {parent}")
        refs = _list(event["assertions"], f"{path}.assertions")
        for ref in refs:
            _string(ref, f"{path}.assertions item")

    assertion_ids: set[str] = set()
    for index, raw_assertion in enumerate(assertions):
        path = f"trace.assertions[{index}]"
        assertion = _object(raw_assertion, path)
        _keys(assertion, ASSERTION_KEYS, path)
        missing_assertion = sorted(ASSERTION_KEYS - set(assertion))
        if missing_assertion:
            raise ValidationError(f"{path} is missing required keys: {', '.join(missing_assertion)}")
        assertion_id = _string(assertion["id"], f"{path}.id")
        if assertion_id in assertion_ids:
            raise ValidationError(f"duplicate assertion id: {assertion_id}")
        assertion_ids.add(assertion_id)
        _string(assertion["kind"], f"{path}.kind")
        _string(assertion["description"], f"{path}.description")
        event_id = _string(assertion["event_id"], f"{path}.event_id")
        if event_id not in event_ids:
            raise ValidationError(f"{path}.event_id refers to an unknown event")
        if assertion["status"] not in {"pass", "fail"}:
            raise ValidationError(f"{path}.status must be pass or fail")
        _string(assertion["evidence"], f"{path}.evidence")

    referenced_assertions = {
        ref
        for event in events
        for ref in event["assertions"]
    }
    unknown_refs = sorted(referenced_assertions - assertion_ids)
    if unknown_refs:
        raise ValidationError(f"events refer to unknown assertions: {', '.join(unknown_refs)}")
    for assertion in assertions:
        event = next(event for event in events if event["id"] == assertion["event_id"])
        if assertion["id"] not in event["assertions"]:
            raise ValidationError(f"assertion {assertion['id']} is not linked from its event")
