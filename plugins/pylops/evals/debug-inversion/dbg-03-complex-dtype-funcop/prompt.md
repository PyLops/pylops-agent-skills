---
max_turns: 30
timeout_seconds: 600
allowed_tools: [Skill, Read, Glob, Grep, Write, Bash]
runs: 3
---
My frequency-domain inversion crashes inside regularized_inversion and I don't understand why — the data and the model are complex, and the Green's function matrix is complex too. Script (`invert_green.py`):

```python
import numpy as np
import pylops
from pylops.optimization.leastsquares import regularized_inversion

nf, nx = 100, 60
rng = np.random.default_rng(0)
f = np.linspace(5, 40, nf)
xs = np.linspace(0, 500, nx)
# frequency-domain Green's functions
G = np.exp(-2j * np.pi * np.outer(f, xs) / 1500.0) / nx

Op = pylops.FunctionOperator(
    lambda m: G @ m,
    lambda d: G.conj().T @ d,
    nf, nx,
)
D1 = pylops.FirstDerivative(nx, dtype="complex128")

mtrue = np.sin(2 * np.pi * xs / 250) * np.exp(1j * xs / 200)
d = Op @ mtrue + 1e-3 * (rng.standard_normal(nf) + 1j * rng.standard_normal(nf))

minv = regularized_inversion(Op, d, [D1], epsRs=[1e-2], iter_lim=200)[0]
print(np.linalg.norm(minv - mtrue) / np.linalg.norm(mtrue))
```
