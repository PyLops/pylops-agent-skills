---
max_turns: 30
timeout_seconds: 600
allowed_tools: [Skill, Read, Glob, Grep, Write, Bash]
runs: 3
---
I have a small dense problem (150 unknowns) that I solve with Tikhonov damping through `lsqr`. I do not know the noise level, so I cannot use the discrepancy principle, and I used `damp=0.001` which gives a very noisy model. How can I choose `damp` without knowing the noise? My script:

```python
import numpy as np
import pylops

rng = np.random.default_rng(11)
n = 150
s = np.linspace(0, 1, n)
K = np.exp(-((s[:, None] - s[None, :]) ** 2) / (2 * 0.03 ** 2)) / n * 10
Op = pylops.MatrixMult(K)
xtrue = np.exp(-0.5 * ((s - 0.3) / 0.08) ** 2) - 0.6 * np.exp(-0.5 * ((s - 0.7) / 0.05) ** 2)
y = Op @ xtrue + 0.08 * rng.standard_normal(n)

xinv = pylops.optimization.basic.lsqr(Op, y, damp=0.001, niter=2000)[0]
```

Please write a runnable Python script saved as `sweep.py` in the current folder, run it, and tell me what you chose and why. The script must print, as its last line, `DAMP_CHOSEN=<value>` with the value you recommend.
