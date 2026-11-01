---
max_turns: 30
timeout_seconds: 600
allowed_tools: [Skill, Read, Glob, Grep, Write, Bash]
runs: 3
---
I recover a sparse model with `fista` and I want to choose `eps` from the corner of the L-curve (data residual against the L1 norm of the model). With `eps=2.0` I only get 4 non-zeros, and I would like a single justified number. The noise standard deviation is 0.15. Please build the L-curve and tell me the corner. My test problem:

```python
import numpy as np
import pylops

rng = np.random.default_rng(2)
N, M = 200, 80
A = rng.standard_normal((M, N)) / np.sqrt(M)
Op = pylops.MatrixMult(A)
xtrue = np.zeros(N)
xtrue[rng.choice(N, 6, replace=False)] = rng.uniform(1, 3, 6) * rng.choice([-1, 1], 6)
y = Op @ xtrue + 0.15 * rng.standard_normal(M)

xinv = pylops.optimization.sparsity.fista(Op, y, eps=2.0, niter=500)[0]
```

Please write a runnable Python script saved as `sweep.py` in the current folder, run it, and tell me what you chose and why. The script must print, as its last line, `EPS_CHOSEN=<value>` with the value you recommend.
