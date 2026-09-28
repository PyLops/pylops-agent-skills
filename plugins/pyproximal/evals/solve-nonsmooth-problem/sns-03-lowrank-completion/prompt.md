---
max_turns: 40
timeout_seconds: 900
allowed_tools: [Skill, Read, Glob, Grep, Write, Bash]
runs: 3
---
I have a 60 × 60 table of measurements where only 30% of the entries were recorded, and those are slightly noisy. The underlying table should be well explained by a few underlying factors. To test an approach I built this synthetic:

```python
import numpy as np

rng = np.random.default_rng(0)
n = 60
Xtrue = rng.standard_normal((n, 3)) @ rng.standard_normal((3, n))
idx = np.sort(rng.choice(n * n, int(0.3 * n * n), replace=False))  # observed entries (flat indices)
y = Xtrue.ravel()[idx] + 0.05 * rng.standard_normal(idx.size)
```

Please fill in the missing entries using PyLops/PyProximal where it makes sense: write a runnable Python script starting from the setup above, save it as `invert.py` in the current folder, run it, and tell me what you chose and how well it worked. The script must print, as its last line, `SNR_DB=<value>` where the value is `pylops.utils.metrics.snr(Xtrue.ravel(), Xinv.ravel())` for the full reconstructed 60 × 60 matrix `Xinv`.
