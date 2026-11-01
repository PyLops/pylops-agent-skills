---
max_turns: 30
timeout_seconds: 600
allowed_tools: [Skill, Read, Glob, Grep, Write, Bash]
runs: 3
---
I have a 1-D blurring operator and noisy data, and I want to recover the underlying signal, but I have not written any inversion yet. Can you build the inversion for me? Here is how I generate the operator and the data:

```python
import numpy as np
import pylops

rng = np.random.default_rng(5)
n = 200
z = np.arange(n)
xtrue = np.zeros(n); xtrue[40:80] = 1.0; xtrue[120:150] = -0.7
t = np.arange(-15, 16)
h = np.exp(-0.5 * (t / 4) ** 2); h /= h.sum()
Op = pylops.signalprocessing.Convolve1D(n, h=h, offset=15)
y = Op @ xtrue + 0.02 * rng.standard_normal(n)
```

Please write a runnable script, run it, and tell me what you did and how well it recovered the signal.
