---
max_turns: 30
timeout_seconds: 600
allowed_tools: [Skill, Read, Glob, Grep, Write, Bash]
runs: 3
---
My regularised plane-wave inversion with cgls stalls: it runs all 100 iterations, the cost stays high (around 7) and the recovered model is wrong (relative error ~0.8). The data are only 1% noise so I expected a near-perfect fit. I already use the Hermitian adjoint in my custom operator, and the other blocks are standard PyLops operators. Can you find out why? Script:

```python
import numpy as np
import pylops


class SteeringOp(pylops.LinearOperator):
    """Plane-wave steering: model is complex amplitudes on nx receivers,
    data are nd slowness samples."""

    def __init__(self, xr, p, fc):
        self.A = np.exp(-2j * np.pi * fc * np.outer(p, xr)) / np.sqrt(len(xr))
        super().__init__(dtype=np.complex128, shape=self.A.shape)

    def _matvec(self, x):
        return self.A @ x

    def _rmatvec(self, y):
        # Hermitian adjoint
        return (y @ self.A).conj()


nx, nd = 80, 120
rng = np.random.default_rng(42)
xr = np.linspace(0, 1, nx)
p = np.linspace(-1, 1, nd)

Sop = SteeringOp(xr, p, fc=10.0)
D2 = pylops.SecondDerivative(nx, dtype="complex128")
Rop = pylops.Restriction(nx, np.arange(0, nx, 4), dtype="complex128")
Op = pylops.VStack([Sop, Rop, 0.5 * D2])

xtrue = np.exp(-((xr - 0.5) ** 2) / 0.02) * np.exp(1j * 3 * xr)
d = Sop @ xtrue + 0.01 * (rng.standard_normal(nd) + 1j * rng.standard_normal(nd))
dr = Rop @ xtrue + 0.01 * (rng.standard_normal(Rop.shape[0]) + 1j * rng.standard_normal(Rop.shape[0]))
y = np.concatenate([d, dr, np.zeros(nx, dtype=complex)])

xinv, istop, iit, r1, r2, cost = pylops.optimization.basic.cgls(
    Op, y, x0=np.zeros(nx, dtype=complex), niter=100, tol=1e-10
)
print("iterations:", iit, "final cost:", cost[-1])
print("relative error:", np.linalg.norm(xinv - xtrue) / np.linalg.norm(xtrue))
```
