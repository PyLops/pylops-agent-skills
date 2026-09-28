---
max_turns: 30
timeout_seconds: 600
allowed_tools: [Skill, Read, Glob, Grep, Write, Bash]
runs: 3
---
I'm doing a joint inversion of a ray-tomography dataset and a gravity dataset with PyLops. Dataset 2 is fitted almost exactly (misfit ~3e-9), but dataset 1 is only fitted to ~6% even though its noise is tiny, and the model error stays at ~0.22 no matter what I do. Adding dataset 1 seems to make no difference. What's going on? Script:

```python
import numpy as np
import pylops

nx = 100
rng = np.random.default_rng(1)
x = np.linspace(0, 1000, nx)          # cell centres
dx = x[1] - x[0]

# dataset 1: straight-ray tomography, kernel = path length in each cell
nray = 150
K1 = (rng.random((nray, nx)) < 0.3) * dx * 1e-3

# dataset 2: gravity of 2-D cells at depth z, observed at 30 stations
z = 50.0
xs = np.linspace(0, 1000, 30)
K2 = 2 * 6.674e-11 * 1e8 * 1000.0 * dx * z / ((xs[:, None] - x[None]) ** 2 + z ** 2) * 1e2

Op1 = pylops.MatrixMult(K1)
Op2 = pylops.MatrixMult(K2)
Op = pylops.VStack([Op1, Op2])

mtrue = np.zeros(nx)
mtrue[20:30] = 1.0
mtrue[60:80] = 0.5
d1 = Op1 @ mtrue + 1e-5 * rng.standard_normal(nray)
d2 = Op2 @ mtrue + 1e-1 * rng.standard_normal(30)
y = np.concatenate([d1, d2])

minv = pylops.optimization.basic.cgls(Op, y, niter=100, damp=1e-2)[0]
print("dataset 1 misfit:", np.linalg.norm(Op1 @ minv - d1) / np.linalg.norm(d1))
print("dataset 2 misfit:", np.linalg.norm(Op2 @ minv - d2) / np.linalg.norm(d2))
print("model error:     ", np.linalg.norm(minv - mtrue) / np.linalg.norm(mtrue))
```
