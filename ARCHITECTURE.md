# Initial architecture

The core model is `source -> event trace -> state/replay -> verification evidence -> renderers`.

A trace event should be able to identify its logical time, actor, operation, source span, state change, causal parents, and assertions. Renderers must not infer correctness from animation order; correctness comes from explicit evidence such as tests, invariants, or counterexamples.

The first implementation will prefer Python 3.12 and SVG/HTML output. Optional video or Manim adapters can be added after the trace contract is stable. Schema compatibility is versioned independently from renderer releases.

The course integration boundary is a release tag plus a recorded commit and artifact digest. No course build should fetch this repository from the network.
