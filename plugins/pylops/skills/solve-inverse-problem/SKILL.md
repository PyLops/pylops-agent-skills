---
name: solve-inverse-problem
description: Use this skill whenever the user has (or can build) a PyLops operator and data and wants to invert it - load it before choosing a solver or writing any inversion code, even when the right solver or regularisation seems obvious. It sets up and runs the inversion in the user's project - choose the solver (lsqr, cgls, cg, regularized_inversion, preconditioned_inversion, fista, spgl1, omp, irls, splitbregman), the regularisation and the stopping parameters, and write a runnable script that reports convergence. E.g. "invert my data with this operator", "which PyLops solver should I use", "add Tikhonov / smoothness / sparsity regularisation to my inversion", "solve y = Op x". Not for an inversion that already misbehaves (use debug-inversion) or for choosing regularisation weights with an L-curve or sweep (use tune-regularization).
---

Goal: a **runnable, reproducible inversion script** in the user's project that
solves their problem with a solver and regularisation chosen for a stated reason,
and shows whether it converged. Do not modify the installed `pylops` package.

If the user has no operator yet, use the `wrap-operator` skill first. If they
already have an inversion that misbehaves, use `debug-inversion` instead. To
choose regularisation weights, hand over to `tune-regularization` once the setup
below works.

## 0. Check the environment

- Find how the project runs Python (`uv.lock`, `pyproject.toml`,
  `environment.yml`, `requirements*.txt`, active venv) and use that runner.
- Check PyLops and its version: `python -c "import pylops; print(pylops.__version__)"`.
  Solver signatures and return tuples changed across versions: inspect the
  installed ones (`help(pylops.optimization.basic.cgls)`) rather than trusting
  memory. `reference/solver_guide.md` describes PyLops 2.x.
- Optional packages: `spgl1` is needed by `pylops.optimization.sparsity.spgl1`;
  PyProximal is needed for non-smooth problems beyond what PyLops offers. Ask
  before installing anything.

## 1. Characterise the problem

Before picking a solver, write down (and confirm with the user if unclear):

- `Op.shape = (N, M)`, `Op.dims`, `Op.dimsd`, dtype (real/complex);
- whether the problem is **square/symmetric positive definite** (e.g. already
  normal equations), **overdetermined** (`N > M`), or **underdetermined**
  (`N < M`, e.g. interpolation, compressive sensing);
- the **noise** level (known sigma? SNR?) and whether data are available on a
  subset only (then the operator should include a `Restriction`);
- the **prior** the user expects on the model: smooth, blocky/piecewise
  constant, sparse in some transform, bounded, positive, low-rank;
- the size: can `Op.todense()` be afforded for a sanity check (M, N up to a few
  thousand)?

Run `pylops.utils.dottest(Op, *Op.shape, complexflag=...)` once. If it fails,
stop and switch to `debug-inversion` / `wrap-operator`: no solver will fix a wrong
adjoint.

## 2. Pick the solver

Use `reference/solver_guide.md` for the full decision table and return values.
In short:

| Prior / structure | Start with |
|---|---|
| well-posed, overdetermined, no prior | `lsqr` or `cgls` (`damp` for zero-order Tikhonov) |
| symmetric positive (semi)definite `Op` | `cg` |
| smooth model | `regularized_inversion` with `Regs=[SecondDerivative/Laplacian]`, `epsRs=[...]` |
| model best expressed in another basis | `preconditioned_inversion` with `P` (e.g. smoothing or a synthesis transform) |
| sparse in the model or in a transform `T` (signal → coefficients) | `fista` (`SOp=T.H`) or `spgl1` (`SOp=T`, note the opposite convention) if a residual target `sigma` is known – see `pick-sparsifying-transform` |
| few non-zeros, explicit dictionary | `omp` |
| robust to outliers (L1 data misfit) | `irls` with `kind="data"` |
| blocky / TV-like, mixed L1 + L2 terms | `splitbregman` with `RegsL1=[FirstDerivative/Gradient]` |
| constraints (bounds, positivity), TV with better control, other non-smooth terms | PyProximal: use the `pyproximal` plugin skill `solve-nonsmooth-problem` |

Avoid `Op / y` in production code: it is a convenience wrapper with a fixed
100 iterations and no control over stopping or regularisation.

State which solver was picked and why (one or two sentences) before writing code.

## 3. Write the script

Start from `reference/inversion_template.py` and adapt it:

- build (or import) the operator, load the data, reshape to `Op.dimsd`;
- **scale** data and model sensibly: if `|y|` is ~1e-8 or ~1e8 normalise it and
  undo the scaling on the result; badly scaled problems stall Krylov solvers;
- set `x0` (zero, or a smooth background model when the user has one);
- choose `niter` from the problem size and condition, not "1000 to be safe":
  start with 20–100 for Krylov solvers and 100–500 for (F)ISTA, then look at the
  cost curve. Use `tol` / `rtol` to stop early;
- for regularised solvers, set initial weights from a scale argument
  (e.g. `eps ≈ ||Op.H y|| / ||Reg.H Reg x||` order-of-magnitude) and mark them as
  "to be tuned" – do not claim they are optimal;
- for `fista`/`ista`, let `alpha=None` so PyLops estimates the step from the
  largest eigenvalue, or pass `eigsdict={"niter": ..., "tol": ...}` for big
  operators; `eps` is the threshold weight;
- keep the whole solver return tuple and name its entries (they differ between
  solvers – see `reference/solver_guide.md`);
- save outputs (`np.save` / the project's I/O) rather than only plotting.

Put the script where the user keeps analysis code (ask if ambiguous) and use
the project's plotting conventions if any.

## 4. Check the result

Run the script and report, with numbers:

- solver exit status (`istop` where available) and iterations used;
- the **cost curve** (log scale) – flat from iteration 1 means a wrong setup,
  still decreasing at `niter` means increase it;
- data residual `||y - Op x|| / ||y||` compared with the expected noise level
  (much lower than the noise ⇒ overfitting; much higher ⇒ under-fitting or
  a modelling error);
- if the user has a true model (synthetic), `pylops.utils.metrics.snr(xtrue, xinv)`;
- a plot of the model (and data, modelled data, residual).

If something looks wrong, switch to `debug-inversion` rather than randomly
changing parameters.

## 5. Hand off

Report: the solver and regularisation chosen and why, the file path, the
convergence summary above, and the parameters that should be tuned next
(pointing to `tune-regularization`).
