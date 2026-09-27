---
max_turns: 40
timeout_seconds: 900
allowed_tools: [Skill, Read, Glob, Grep, Write, Bash]
runs: 3
---
I need to invert some sensor data with PyLops to recover `x`. This is how my (synthetic) data are made:

```python
import numpy as np
import pylops

rng = np.random.default_rng(42)
nobs, m = 300, 50
A = rng.standard_normal((nobs, m))
xtrue = rng.standard_normal(m)
Op = pylops.MatrixMult(A)

y = Op @ xtrue + 0.01 * rng.standard_normal(nobs)
bad = rng.choice(nobs, 30, replace=False)
y[bad] += rng.choice([-1, 1], 30) * rng.uniform(20, 50, 30)
```

Some of the readings look a bit odd. In the real survey I only get `y` and `A`, nothing else from this script. Can you set up the inversion? Please write a runnable Python script for this, saved as `invert.py` in the current folder, run it, and tell me what you chose and how well it worked. The script must print, as its last line, `SNR_DB=<value>` where the value is `pylops.utils.metrics.snr(xtrue, xinv)` computed on the inverted **model** against the true model.
