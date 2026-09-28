---
name: solve-nonsmooth-problem
description: Formulate and solve non-smooth, constrained or non-convex inverse problems with PyProximal on top of PyLops operators - total variation, L1/sparsity in a transform, group sparsity, box/positivity/ball/affine constraints, low rank, plug-and-play denoisers - by writing the objective as f(x) + g(Kx), picking proximal operators and a solver (ProximalGradient, ADMM, LinearizedADMM, PrimalDual, ...), setting step sizes from operator norms, and verifying convergence. Use when the user asks "add TV regularisation", "positivity / bound constraints in my PyLops inversion", "L1 with a non-orthogonal transform", "use PyProximal", "ADMM / primal-dual for my problem".
---

Goal: a runnable script that solves the user's non-smooth problem with a
formulation written down explicitly, provably valid step sizes, and a convergence
check. Do not modify the installed `pyproximal` / `pylops` packages.

If the problem is a plain (Tikhonov-)regularised least squares, or L1 with an
orthogonal transform, PyLops alone is simpler: use the `pylops` plugin skill
`solve-inverse-problem` instead.

## 0. Check the environment

- Use the project's Python runner; check
  `python -c "import pyproximal, pylops; print(pyproximal.__version__, pylops.__version__)"`.
  PyProximal requires a recent PyLops (≥ 2.4 for 0.12); ask before installing or
  upgrading.
- Signatures and return values of solvers changed across versions (e.g.
  `AcceleratedProximalGradient` → `ProximalGradient(acceleration=...)`,
  `DouglasRachfordSplitting` roles of x/y): inspect the installed ones.
  `reference/solver_guide.md` summarises PyProximal 0.12.

## 1. Write the objective

Write the problem in the form **`min_x f(x) + g(K x)`** (or `f(x) + ε g(x)`)
before coding, and show it to the user:

- data term: usually `f = ½‖Op x − y‖²` → `pyproximal.L2(Op=Op, b=y)` (smooth, has
  `.grad`), or `L2(b=y)` applied to `K = Op` inside a stack;
- regulariser/constraint: `L1`, `L21` (+ `pylops.Gradient` = isotropic TV),
  `Box`, `EuclideanBall`, `L1Ball`, `AffineSet`, `Nuclear`, … (table in the guide);
- `K`: a PyLops operator (`Gradient`, a transform, `Op`, or
  `pylops.VStack([...])` with `pyproximal.VStack([...], nn=[...])` for several
  terms at once);
- weights: scale proxes with floats (`lam * pyproximal.L21(ndim=2)` with
  `lam = float(...)`): an integer (`2 * f`) silently yields `None` instead of a
  scaled operator.

## 2. Pick the solver

| Structure | Solver |
|---|---|
| `f` smooth (e.g. L2 data) + simple `g` on `x` (L1, Box) | `ProximalGradient(proxf, proxg, x0, epsg, tau, acceleration="fista")` |
| `f` + `g(Kx)` with `K` non-trivial (TV, analysis L1 with non-orthogonal transform) | `PrimalDual(proxf, proxg, K, x0, tau, mu)` or `LinearizedADMM(proxf, proxg, K, x0, tau, mu)` |
| `½‖Op x − b‖² + g(Ax)` with a good inner least-squares solver | `ADMML2(proxg, Op, b, A, x0, tau)` |
| `f(x) + g(x)` both non-smooth with cheap proxes | `ADMM` or `DouglasRachfordSplitting` |
| constraints + data + regulariser | `PrimalDual` with `f = Box(...)`, `g = VStack([L2(b=y), lam*L21])`, `K = VStack([Op, Gradient])` |
| many terms | `GeneralizedProximalGradient`, `PPXA`, `ConsensusADMM` |
| learned/denoiser prior | `pnp.PlugAndPlay` |

State the choice and why.

## 3. Step sizes and parameters

- Compute operator norms, do not guess: `L = ‖K‖²` with
  `pylops.optimization.eigs.power_iteration(K.H @ K, niter=100)[0]` (inflate ~5 %)
  or `(K.H @ K).eigs(neigs=1)` (ARPACK may raise `ArpackNoConvergence` – raise
  `niter` or use power iteration).
- ProximalGradient: `tau ≤ 1/L` with `L = ‖Op‖²` for `½‖Op x − b‖²` (or
  `tau=None` for backtracking); PrimalDual: `tau * mu * ‖K‖² < 1` (e.g.
  `tau = mu = 0.95/sqrt(L)`); LinearizedADMM: `mu ≤ tau / ‖K‖²`.
- Inner solves: `L2(Op=..., niter=...)` needs an inner iterative solve at every
  prox; keep `niter` small (10–30) with `warm=True`, or move `Op` into `K` and use
  `L2(b=y)` instead.
- Choose every free parameter (regularisation weight, threshold, `tau`/`mu` for ADMM/PnP, rank, `niter`, denoiser strength) with a criterion that does not use the true model: discrepancy principle (residual ≈ noise level), held-out observed data, L-curve, or a stated scale argument. Never pick a value because it gives the best SNR against the true model; that is an oracle, and it will not transfer to real data. The same applies to information that is only known from how the synthetic was built (the true support, number of components or rank).

## 4. Write, run, verify

Adapt `reference/tv_template.py` (TV deblurring with and without box
constraints via `PrimalDual`):

- a `callback` storing the objective value per iteration; plot it (log scale);
- stop criterion: relative change of the objective / model below a tolerance, or
  a fixed `niter` shown to be enough by the cost curve;
- check constraints are satisfied (e.g. bounds), and compare with the
  unconstrained / L2 solution to show what the non-smooth term changes;
-  use a synthetic with known model first when possible, but only to *evaluate* the result (`pylops.utils.metrics.snr` of the final model); the true model must not feed into the solve or into choosing its parameters. A table of SNR vs parameter can be shown as a diagnostic, next to the parameter picked by the truth-free criterion.

If the cost oscillates or diverges, the step sizes violate the conditions above
(recompute `‖K‖²`), or `K` fails the dot-test
(`pylops.utils.dottest`).

## 5. Hand off

Report: the objective as written, the proxes/solver chosen and why, the step
sizes and how they were derived, how each free parameter was chosen (the truth-free criterion used), convergence evidence, the result compared with a baseline, and parameters left to tune.
