"""Data loading and canonical serialization for trace documents."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


JSON = dict[str, Any]


@dataclass(frozen=True)
class Trace:
    """A loaded trace; validation is deliberately separate and explicit."""

    document: JSON

    @property
    def trace_id(self) -> str:
        return self.document["trace_id"]

    @property
    def events(self) -> list[JSON]:
        return self.document["events"]

    @property
    def assertions(self) -> list[JSON]:
        return self.document["assertions"]

    def canonical_json(self) -> str:
        """Return a stable representation suitable for golden fixtures."""
        return json.dumps(self.document, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def load_trace(path: str | Path) -> Trace:
    """Load JSON without executing or importing anything from the trace."""
    with Path(path).open(encoding="utf-8") as handle:
        document = json.load(handle)
    if not isinstance(document, dict):
        raise ValueError("trace root must be a JSON object")
    return Trace(document)
