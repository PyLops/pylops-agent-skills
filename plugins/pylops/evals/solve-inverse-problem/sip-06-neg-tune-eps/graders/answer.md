---
type: llm
focus: trace
weight: 1
---
PASS only if ALL of these hold:
- The answer (with a script that was actually run in the trace) sweeps epsRs over a logarithmic range of values (at least ~8 values spanning several orders of magnitude) with the user's `regularized_inversion` setup.
- For each value it computes the data residual norm and the regularisation norm (||D2 x||), and builds an L-curve (plot saved to a file and/or the values tabulated); it selects a value by a stated criterion (L-curve corner / maximum curvature, and/or the discrepancy principle with noise std 0.02).
- It reports the recommended epsRs and the numbers backing it, and they do not visibly contradict the tool output in the trace (parts of the trace may be elided; do not fail for numbers you cannot find).
- It keeps the user's solver and regulariser rather than re-designing the inversion (a brief side remark about alternatives is fine).

Otherwise FAIL.
