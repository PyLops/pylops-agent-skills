---
max_turns: 30
timeout_seconds: 600
allowed_tools: [Skill, Read, Glob, Grep, Write, Bash]
runs: 3
---
I wrapped my convolution as a PyLops operator so I can deconvolve with lsqr. I already made sure the adjoint is a correlation (time-reversed wavelet), but lsqr still gives a poor result: relative error about 0.93, with ringing around the spikes, even though the noise is tiny (1e-4). Is my damping too small, or do I need more iterations? Here is the full script (`deconv.py`):

```python
import numpy as np
import pylops

nt = 301
dt = 0.004
rng = np.random.default_rng(3)

# asymmetric (minimum-phase-like) wavelet
tw = np.arange(41) * dt
h = np.exp(-tw / 0.02) * np.sin(2 * np.pi * 25 * tw)
nh = len(h)

def forward(x):
    # causal convolution, keep the first nt samples
    return np.convolve(x, h, mode="full")[:nt]

def adjoint(y):
    # adjoint of convolution = correlation with the wavelet
    # (convolve with the time-reversed wavelet and re-align)
    return np.convolve(y, h[::-1], mode="full")[nh - 2 : nh - 2 + nt]

Op = pylops.FunctionOperator(forward, adjoint, nt, nt)

x = np.zeros(nt)
x[[50, 120, 125, 200]] = [1.0, -0.6, 0.4, 0.8]
y = Op @ x + 1e-4 * rng.standard_normal(nt)

xinv = pylops.optimization.basic.lsqr(Op, y, niter=200, damp=1e-4)[0]
print("relative error:", np.linalg.norm(xinv - x) / np.linalg.norm(x))
```
