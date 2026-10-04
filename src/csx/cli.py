"""The offline ``csx`` command line interface."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .model import load_trace
from .replay import compare, replay
from .validate import ValidationError, validate_trace


def _load_valid(path: str):
    trace = load_trace(path)
    validate_trace(trace)
    return trace


def _dump(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Replay and verify an offline CS explanation trace")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("run", "replay", "verify"):
        subparser = subparsers.add_parser(command)
        subparser.add_argument("trace", type=Path)
    compare_parser = subparsers.add_parser("compare")
    compare_parser.add_argument("left", type=Path)
    compare_parser.add_argument("right", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command in {"run", "replay"}:
            trace = _load_valid(args.trace)
            _dump({"trace_id": trace.trace_id, "timeline": replay(trace)})
            return 0
        if args.command == "verify":
            trace = _load_valid(args.trace)
            failed = [a["id"] for a in trace.assertions if a["status"] == "fail"]
            _dump({"trace_id": trace.trace_id, "valid": not failed, "failed_assertions": failed})
            return 1 if failed else 0
        left = _load_valid(args.left)
        right = _load_valid(args.right)
        _dump(compare(left, right))
        return 0
    except (OSError, ValueError, ValidationError, json.JSONDecodeError) as error:
        print(f"csx: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
