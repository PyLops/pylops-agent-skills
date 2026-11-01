---
max_turns: 30
timeout_seconds: 600
allowed_tools: [Skill, Read, Glob, Grep, Write, Bash]
runs: 3
---
I am recovering a sparse model with `fista`, but with `eps=5.0` the output is all zeros, and I do not know how to pick `eps`. The noise standard deviation is 0.05. How should I choose `eps`? My test problem:

```python
import numpy as np
import pylops

rng = np.random.default_rng(2)
N, M = 200, 80
A = rng.standard_normal((M, N)) / np.sqrt(M)
Op = pylops.MatrixMult(A)
xtrue = np.zeros(N)
xtrue[rng.choice(N, 6, replace=False)] = rng.uniform(1, 3, 6) * rng.choice([-1, 1], 6)
y = Op @ xtrue + 0.05 * rng.standard_normal(M)

xinv = pylops.optimization.sparsity.fista(Op, y, eps=5.0, niter=500)[0]
```

Please write a runnable Python script saved as `sweep.py` in the current folder, run it, and tell me what you chose and why. The script must print, as its last line, `EPS_CHOSEN=<value>` with the value you recommend.
