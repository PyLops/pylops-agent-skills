---
max_turns: 15
timeout_seconds: 300
allowed_tools: [Skill, Read, Glob, Grep, Write, Bash]
runs: 3
---
I wrote a forward-difference operator as a custom PyLops LinearOperator, but `dottest` fails. What's wrong?

```python
import numpy as np
import pylops
from pylops.utils import dottest

class ForwardDiff(pylops.LinearOperator):
    """y[i] = x[i+1] - x[i], i = 0..n-2"""
    def __init__(self, n, dtype="float64"):
        super().__init__(dtype=np.dtype(dtype), shape=(n - 1, n))
        self.n = n

    def _matvec(self, x):
        return x[1:] - x[:-1]

    def _rmatvec(self, y):
        x = np.zeros(self.n, dtype=self.dtype)
        x[1:] -= y
        x[:-1] += y
        return x

Op = ForwardDiff(100)
dottest(Op, 99, 100, verb=True, raiseerror=False)
```
