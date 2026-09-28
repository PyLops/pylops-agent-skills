---
max_turns: 25
timeout_seconds: 600
allowed_tools: [Skill, Read, Glob, Grep, Write, Bash]
runs: 3
---
My deconvolution with lsqr gives a very noisy model. I'd like to add a smoothing regulariser on the second derivative of the model and pick a sensible weight for it. How should I change this?

```python
import numpy as np
import pylops

n = 300
t = np.arange(-25, 26)
h = np.exp(-0.5 * (t / 6.0) ** 2)
h /= h.sum()
Op = pylops.signalprocessing.Convolve1D(n, h=h, offset=25)

xx = np.linspace(0, 1, n)
xtrue = np.sin(2 * np.pi * 2 * xx) + 0.5 * np.sin(2 * np.pi * 5 * xx)
rng = np.random.default_rng(1)
y = Op @ xtrue + 0.05 * rng.standard_normal(n)

xinv = pylops.optimization.basic.lsqr(Op, y, niter=300)[0]
```
