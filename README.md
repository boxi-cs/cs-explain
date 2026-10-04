# cs-explain

Executable explanations for computer science: connect source code, state, events, failures, and verification in one replayable trace.

> **Status:** trace contract MVP. The core is intentionally small and offline; it does not execute source code.

## Scope

`cs-explain` will provide a versioned trace schema, deterministic replay, source/state linking, interactive playback, and static SVG/HTML export. Animation is a renderer; the trace and its verification evidence are the primary artifacts.

Initial MVP scenes:

1. agent loop and context packets;
2. evaluator budget, trajectory, oracle, and score;
3. incident retry and idempotency.

## Planned commands

```text
csx run
csx replay
csx compare A B
csx verify
```

The commands accept JSON trace files and never import or execute anything from a
trace. They validate the learner-facing links before producing output:

```bash
python -m csx.cli run fixtures/agent-loop-context.correct.json
python -m csx.cli replay fixtures/agent-loop-context.correct.json
python -m csx.cli compare \
  fixtures/agent-loop-context.correct.json \
  fixtures/agent-loop-context.incorrect.json
python -m csx.cli verify fixtures/agent-loop-context.correct.json
python -m csx.cli verify fixtures/agent-loop-context.incorrect.json  # exits 1: failing evidence
```

Install the package in an environment with Python 3.12 or newer to use the
`csx` entry point directly (`pip install -e .`). The same commands work without
network access once the checkout is present.

## Trace contract v0.1

The JSON Schema is [schemas/trace-v0.1.schema.json](schemas/trace-v0.1.schema.json).
Each trace keeps the educational path explicit:

```text
source span → event → state delta → observation → assertion evidence
```

Events have stable IDs, non-decreasing logical time, causal parent IDs, and a
source span. Replay applies only the declared `state_delta` objects in order.
Assertions are linked from both the event and the top-level assertion list, and
have an explicit `pass` or `fail` status. A required `text_fallback` makes the
same explanation available without animation or a browser. `seed` is part of
the contract so generated fixtures can be reproduced; timestamps, UUIDs and
other dynamic metadata are rejected.

The two `agent-loop-context` fixtures are deliberately paired: the correct
trace keeps context bounded and passes its prediction, while the incorrect
trace exposes an over-broad context and a failing prediction. Both are valid
traces so a learner can compare a working path with an evidence-backed failure.

Run the deterministic checks with:

```bash
python -m pytest
```

Content authors should put episodes and narration in `boxi-cs/cs-scenes` and
pin this repository to a release tag plus commit. This repository provides the
replay and verification contract; it is not a hosted runner and it does not
execute learner or episode source code.

## Repository boundaries

This repository owns reusable engine code, schemas, adapters, and renderer interfaces. Lesson content lives in `boxi-cs/cs-scenes`; the course repository consumes fixed, reviewed artifacts rather than importing this repository at build time.

## Development principles

- deterministic fixtures and explicit seeds;
- offline-first builds;
- trace, assertions, and transcripts alongside rendered output;
- accessible text fallback for every visual explanation;
- no untrusted code execution in the core viewer.

See [ARCHITECTURE.md](ARCHITECTURE.md) for the initial design contract.
