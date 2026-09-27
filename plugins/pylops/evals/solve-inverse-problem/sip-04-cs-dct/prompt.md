---
max_turns: 40
timeout_seconds: 900
allowed_tools: [Skill, Read, Glob, Grep, Write, Bash]
runs: 3
---
I recorded a smooth, periodic-looking signal at only a quarter of the samples and want to reconstruct the full signal with PyLops. Synthetic version of my setup:

```python
import numpy as np
import pylops

rng = np.random.default_rng(7)
n = 512
t = np.arange(n)
freqs = rng.choice(np.arange(5, 200), 12, replace=False)
amps = rng.uniform(0.5, 2, 12) * rng.choice([-1, 1], 12)
xtrue = sum(a * np.cos(np.pi * f * (2 * t + 1) / (2 * n)) for a, f in zip(amps, freqs))

# only 128 randomly located samples were recorded
iava = np.sort(rng.choice(n, 128, replace=False))
R = pylops.Restriction(n, iava)
y = R @ xtrue + 0.005 * rng.standard_normal(128)
```

`xinv` should be the full 512-sample reconstructed signal. Please write a runnable Python script for this, saved as `invert.py` in the current folder, run it, and tell me what you chose and how well it worked. The script must print, as its last line, `SNR_DB=<value>` where the value is `pylops.utils.metrics.snr(xtrue, xinv)` computed on the inverted **model** against the true model.
