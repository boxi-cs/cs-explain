# cs-explain

Executable explanations for computer science: connect source code, state, events, failures, and verification in one replayable trace.

> **Status:** scaffold. The public contract and first MVP are being designed.

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

## Repository boundaries

This repository owns reusable engine code, schemas, adapters, and renderer interfaces. Lesson content lives in `boxi-cs/cs-scenes`; the course repository consumes fixed, reviewed artifacts rather than importing this repository at build time.

## Development principles

- deterministic fixtures and explicit seeds;
- offline-first builds;
- trace, assertions, and transcripts alongside rendered output;
- accessible text fallback for every visual explanation;
- no untrusted code execution in the core viewer.

See [ARCHITECTURE.md](ARCHITECTURE.md) for the initial design contract.
