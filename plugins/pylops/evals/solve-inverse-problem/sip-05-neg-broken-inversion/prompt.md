---
max_turns: 30
timeout_seconds: 600
allowed_tools: [Skill, Read, Glob, Grep, Write, Bash]
runs: 3
---
I wrapped my causal filter as a PyLops FunctionOperator to deconvolve with cgls, but cgls stalls: the cost barely decreases after the first few iterations and the model looks nothing like the truth. `pylops.utils.dottest(Op, 300, 300)` also fails. What's wrong with my code?

```python
import numpy as np
import pylops

nt = 300
h = np.exp(-np.arange(30) / 6.0)  # causal, decaying filter

def forward(x):
    return np.convolve(x, h, mode="full")[:nt]

def adjoint(y):
    return np.convolve(y, h, mode="full")[:nt]

Op = pylops.FunctionOperator(forward, adjoint, nt, nt)

rng = np.random.default_rng(3)
xtrue = np.zeros(nt)
xtrue[[40, 90, 150, 220]] = [1.0, -0.7, 0.5, 0.9]
y = Op @ xtrue + 1e-3 * rng.standard_normal(nt)

xinv = pylops.cgls(Op, y, x0=np.zeros(nt), niter=100, damp=1e-3)[0]
print(np.linalg.norm(xinv - xtrue) / np.linalg.norm(xtrue))
```
