---
type: llm
focus: last_message
weight: 1
---
Ground truth: the forward operator is a causal convolution (`np.convolve(x, h, "full")[:nt]`), but the adjoint repeats the same convolution instead of correlating: the adjoint must use the time-reversed filter, e.g. `np.convolve(y, h[::-1], "full")[len(h) - 1 : len(h) - 1 + nt]` (or `np.correlate(y, h, "full")` with the matching slice), or the user can use `pylops.signalprocessing.Convolve1D` directly. With a correct adjoint cgls converges.

PASS only if ALL of these hold:
- It says the adjoint is wrong (not the transpose of the forward) and that this is why the dot-test fails and cgls stalls.
- It identifies the missing time reversal / correlation (and the corresponding slice) and gives a corrected adjoint equivalent to the ground truth, or recommends Convolve1D.
- It does not name the solver choice, damp, niter or noise as the main cause.

Otherwise FAIL.
