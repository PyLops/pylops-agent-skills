---
max_turns: 30
timeout_seconds: 600
allowed_tools: [Skill, Read, Glob, Grep, Write, Bash]
runs: 3
---
I deblur a 1-D signal with plain `cgls` and no regulariser. The noise standard deviation is 0.03. The more iterations I run the noisier the result gets, and I set `niter=1000` because I thought more is better. How many iterations should I use? My script:

```python
import numpy as np
import pylops

rng = np.random.default_rng(4)
n = 250
z = np.arange(n)
xtrue = np.exp(-0.5 * ((z - 80) / 10) ** 2) + 0.6 * np.exp(-0.5 * ((z - 170) / 6) ** 2)
t = np.arange(-20, 21)
h = np.exp(-0.5 * (t / 4) ** 2); h /= h.sum()
Op = pylops.signalprocessing.Convolve1D(n, h=h, offset=20)
y = Op @ xtrue + 0.03 * rng.standard_normal(n)

xinv = pylops.cgls(Op, y, niter=1000)[0]
```

Please write a runnable Python script saved as `sweep.py` in the current folder, run it, and tell me what you chose and why. The script must print, as its last line, `NITER_CHOSEN=<value>` with the value you recommend.
