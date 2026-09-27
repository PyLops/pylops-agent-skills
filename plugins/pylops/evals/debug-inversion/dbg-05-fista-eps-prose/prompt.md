---
max_turns: 30
timeout_seconds: 600
allowed_tools: [Skill, Read, Glob, Grep, Write, Bash]
runs: 3
---
My sparse deconvolution with pylops fista always returns a model that is exactly zero everywhere, no matter whether I use niter=50 or niter=2000. The operator is a Convolve1D with a small wavelet (I computed Op.eigs() and the largest eigenvalue is about 0.1), my data have peak amplitude around 1e-3, and I call `fista(Op, y, niter=500, eps=10)` with the default alpha. The dot-test passes. Why is everything zero and how do I fix it?
