---
type: llm
focus: trace
weight: 1
---
PASS only if ALL of these hold:
- A script that builds an inversion with a PyLops solver for the user's operator and data was actually run in the trace.
- The answer reports a result of the run (an error or SNR against the true model, or a residual compared to the noise level 0.02).
- The answer does not turn into a standalone regularisation-parameter study: it picks and justifies a solver and regulariser for the problem (a brief parameter choice is fine).

Otherwise FAIL.
