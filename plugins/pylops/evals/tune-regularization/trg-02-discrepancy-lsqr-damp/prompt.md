---
max_turns: 30
timeout_seconds: 600
allowed_tools: [Skill, Read, Glob, Grep, Write, Bash]
runs: 3
---
I am inverting a smoothing integral operator with `lsqr` and a damping term. I know the noise standard deviation is exactly 0.1, and I picked `damp=0.01` by trial and error, but the model looks noisy. How should I choose `damp` in a principled way? The synthetic test is:

```python
import numpy as np
import pylops

rng = np.random.default_rng(7)
n = 120
s = np.linspace(0, 1, n)
K = np.exp(-((s[:, None] - s[None, :]) ** 2) / (2 * 0.04 ** 2)) / n * 10
Op = pylops.MatrixMult(K)
xtrue = np.sin(2 * np.pi * 2 * s) + 0.5 * (s > 0.6)
y = Op @ xtrue + 0.1 * rng.standard_normal(n)

xinv = pylops.optimization.basic.lsqr(Op, y, damp=0.01, niter=2000)[0]
```

Please write a runnable Python script saved as `sweep.py` in the current folder, run it, and tell me what you chose and why. The script must print, as its last line, `DAMP_CHOSEN=<value>` with the value you recommend.
