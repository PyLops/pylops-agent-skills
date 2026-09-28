---
max_turns: 40
timeout_seconds: 900
allowed_tools: [Skill, Read, Glob, Grep, Write, Bash]
runs: 3
---
Two sensors record the same phenomenon: their signals are made of the same few cosine (DCT) components, just with different amplitudes. Sensor 1 lost most of its samples (only 8% kept), sensor 2 kept 60%. Both recordings are slightly noisy. I want to reconstruct both full signals from the samples I have. Here is my synthetic setup:

```python
import numpy as np
import pylops

np.random.seed(10)
N = 256
icomp = [4, 8, 11, 17, 23, 30]
amps1 = [1.0, 0.2, 0.5, 0.7, 0.3, 0.6]
amps2 = [3.0, 3.0, 2.0, 2.5, 2.0, 3.0]
Dop = pylops.signalprocessing.DCT(N)  # orthonormal DCT

X1 = np.zeros(N)
X2 = np.zeros(N)
X1[icomp] = amps1
X2[icomp] = amps2
x1 = Dop.H @ X1  # true signal of sensor 1
x2 = Dop.H @ X2  # true signal of sensor 2

iava1 = np.sort(np.random.permutation(N)[: int(round(N * 0.08))])
iava2 = np.sort(np.random.permutation(N)[: int(round(N * 0.6))])
Rop1 = pylops.Restriction(N, iava1)
Rop2 = pylops.Restriction(N, iava2)
y1 = Rop1 @ x1 + 0.01 * np.random.randn(len(iava1))  # observed samples of sensor 1
y2 = Rop2 @ x2 + 0.01 * np.random.randn(len(iava2))  # observed samples of sensor 2
```

Sensor 1 is the one I care about most. Please write a runnable Python script (starting from the setup above) that reconstructs both signals `x1inv` and `x2inv`, save it as `invert.py` in the current folder, run it, and tell me what you chose and how well it worked. The script must print the SNR of each sensor, and as its last line `SNR_DB=<value>` where the value is `pylops.utils.metrics.snr(x1, x1inv)` for **sensor 1**.
