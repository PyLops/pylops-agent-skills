---
max_turns: 40
timeout_seconds: 900
allowed_tools: [Skill, Read, Glob, Grep, Write, Bash]
runs: 3
---
I'm deblurring small blocky images (flat regions with sharp edges). A 3×3 median filter is a very good denoiser for this kind of image, so I'd like to use it as the prior inside the inversion itself, not just to clean up the result afterwards. Here is my synthetic test:

```python
import numpy as np
import pylops

ny = nx = 64
xtrue = np.zeros((ny, nx))
xtrue[8:56, 8:56] = 0.3
xtrue[16:30, 14:40] = 1.0
xtrue[36:50, 20:32] = 0.7
xtrue[34:52, 40:50] = 0.5
yy, xx = np.mgrid[:ny, :nx]
xtrue[(yy - 24) ** 2 + (xx - 46) ** 2 < 36] = 0.8

t = np.arange(-10, 11)
g = np.exp(-0.5 * (t / 1.5) ** 2)
h = np.outer(g, g)
h /= h.sum()
Op = pylops.signalprocessing.Convolve2D(dims=(ny, nx), h=h, offset=(10, 10))

rng = np.random.default_rng(0)
y = Op @ xtrue.ravel() + 0.01 * rng.standard_normal(ny * nx)
```

Please write a runnable Python script starting from the setup above that recovers the image `xinv` (shape 64 × 64) using the median filter as the prior, save it as `invert.py` in the current folder, run it, and tell me what you chose and how well it worked. The script must print, as its last line, `SNR_DB=<value>` where the value is `pylops.utils.metrics.snr(xtrue, xinv)`.
