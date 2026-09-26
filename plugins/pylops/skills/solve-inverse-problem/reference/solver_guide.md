# PyLops solver guide (PyLops 2.x)

All solvers below are importable from `pylops.optimization.{basic,leastsquares,sparsity}`
and also as `pylops.<name>`. Function wrappers accept n-D `y`/`x0` and return
`x` reshaped to `Op.dims`. Check the installed signatures with `help(...)`
before relying on this table.

## Which problem does each solver solve?

| Solver | Objective | Use when |
|---|---|---|
| `cg(Op, y, x0, niter, damp, tol)` | `Op x = y`, `Op` square Hermitian positive (semi)definite | you already built normal equations or a SPD operator |
| `cgls(Op, y, x0, niter, damp, tol)` | `min ‖y − Op x‖² + damp² ‖x‖²` | any rectangular least-squares problem |
| `lsqr(Op, y, x0, damp, atol, btol, conlim, niter)` | same as `cgls`, numerically more stable | ill-conditioned least squares; gives `acond`, `anorm` estimates |
| `regularized_inversion(Op, y, Regs, x0, Weight, dataregs, epsRs, engine, **kwargs_solver)` | `min ‖W(y − Op x)‖² + Σ εᵢ² ‖dᵢ − Rᵢ x‖²` | smoothness/closeness priors; data weighting |
| `normal_equations_inversion(Op, y, Regs, x0, Weight, dataregs, epsI, epsRs, NRegs, epsNRs, engine, **kwargs_solver)` | same, via normal equations and `cg` | small/cheap problems, or when `NRegs` (already-squared regularisers) are handy |
| `preconditioned_inversion(Op, y, P, x0, engine, **kwargs_solver)` | `min ‖y − Op P p‖²`, returns `x = P p` | model described in another basis (smooth, band-limited, synthesis dictionary) |
| `ista` / `fista(Op, y, x0, niter, SOp, eps, alpha, eigsdict, threshkind, perc, decay, tol)` | `min ½‖y − Op x‖² + eps ‖SOpᴴ x‖₁` (or L0/L½ with `threshkind`) | sparse model (`SOp=None`) or sparse in an orthogonal/tight-frame transform (analysis form) |
| `spgl1(Op, y, x0, SOp, tau, sigma, **kwargs_spgl1)` | BPDN `min ‖p‖₁ s.t. ‖y − Op SOpᴴ p‖ ≤ sigma` (or LASSO with `tau`), `x = SOpᴴ p` | sparse in a transform (`SOp` = analysis transform, e.g. `FFT2D`, `DWT2D`) and a residual target (noise level) is known |
| `omp(Op, y, niter_outer, niter_inner, sigma, normalizecols)` | greedy sparse recovery, stops when `‖r‖ < sigma` | very sparse model, explicit dictionary |
| `irls(Op, y, x0, nouter, threshR, epsR, epsI, kind, **kwargs_solver)` | L1 data misfit (`kind="data"`), L1 model (`"model"`), or both (`"datamodel"`) | outliers / spiky noise in data |
| `splitbregman(Op, y, RegsL1, x0, niter_outer, niter_inner, RegsL2, dataregsL2, mu, epsRL1s, epsRL2s, tau)` | `min μ/2‖y − Op x‖² + Σ ε‖Rᵢ x‖₁ + Σ ε‖Lⱼ x‖²` | blocky / piecewise-constant models (anisotropic TV with `FirstDerivative`s) |

Synthesis vs analysis for sparsity:

With `T` an analysis transform (signal → coefficients) and `S = T.H` its synthesis:

- **Synthesis** (`x = S p`, `p` sparse): invert `Op @ S` for `p` with `fista`/`omp`, then
  `x = S @ p`; `spgl1(Op, y, SOp=T)` does this for you (it inverts `Op @ T.H`) and returns
  `(x, p, info)`.
- **Analysis** (`‖T x‖₁` small): `fista(Op, y, SOp=S)` – note `fista`'s `SOp` is the
  synthesis side (penalty `‖SOpᴴ x‖₁`), the opposite convention to `spgl1`. The update is
  exact only if `S` is orthogonal or a tight frame (FFT with `norm="ortho"`, orthogonal
  wavelets). Otherwise use PyProximal.

## Return values

| Solver | Returns |
|---|---|
| `cg` | `(x, iiter, cost)` |
| `cgls` | `(x, istop, iiter, r1norm, r2norm, cost)` (`cost` = history of `r1norm`) |
| `lsqr` | `(x, istop, iiter, r1norm, r2norm, anorm, acond, arnorm, xnorm, var, cost)` |
| `regularized_inversion` | `(xinv, istop, itn, r1norm, r2norm)` (no cost history) |
| `preconditioned_inversion` | `(xinv, istop, itn, r1norm, r2norm)` |
| `normal_equations_inversion` | `(xinv, istop)` |
| `ista` / `fista` | `(x, niter, cost)` (`cost` includes the regularisation term) |
| `omp` | `(x, niter_outer, cost)` |
| `irls` | `(x, nouter)` |
| `spgl1` | `(xinv, pinv, info)` (`info["rnorm2"]` = residual history, `info["stat"]` = exit status) |
| `splitbregman` | `(xinv, itn_out, cost)` |

To get a cost history from `regularized_inversion` / `preconditioned_inversion`, pass
`engine="pylops"` (inner solver is PyLops `cgls`) and a `callback`, or run the augmented
system yourself: `Opaug = VStack([Op, eps * Reg])`, `yaug = np.hstack([y, 0])` and call
`cgls`/`lsqr`.

## `kwargs_solver` routing

- `engine="scipy"` (default) → `scipy.sparse.linalg.lsqr` (or `cg` for the normal-equations
  variant): iterations are `iter_lim=...` (lsqr) / `maxiter=...` (cg), tolerances `atol`, `btol`.
- `engine="pylops"` → PyLops `cgls` (or `cg`): iterations are `niter=...`, plus `tol`,
  `callback`. Required for CuPy arrays.

## Stopping and monitoring

- `niter`: upper bound. `tol` (absolute on residual), `rtol` (relative to initial cost),
  `rtol1` (relative to data norm) stop earlier.
- `callback(x)` is called each iteration on the current model.
- Class API (`pylops.optimization.cls_basic.CGLS`, `cls_sparsity.FISTA`, …) accepts
  `callbacks=[...]` objects from `pylops.optimization.callback`:
  `MetricsCallback(xtrue, Op=None, which=("mae","mse","snr","psnr"))` stores metrics per
  iteration in `.metrics`; subclass `Callbacks` and implement `on_step_end(self, solver, x)`
  for custom logging; set `self.stop = True` to stop early.
- `show=True` prints the iteration log.

## Regularisation operators commonly used

- `pylops.Identity` (zero-order Tikhonov, same as `damp`).
- `pylops.FirstDerivative(dims, axis=...)`, `pylops.SecondDerivative(dims, axis=...)`,
  `pylops.Laplacian(dims, axes=..., weights=...)`, `pylops.Gradient(dims)` (stacked output).
- `pylops.Smoothing1D/2D` as preconditioner `P` for `preconditioned_inversion`.
- Transforms (`FFT`, `DWT`, `DCT`, `Radon2D`, `Seislet`, `UDCT`, `Sliding2D`/`Patch2D`) as `SOp`.
  See the `pick-sparsifying-transform` skill.

## Tutorials

- Solvers: https://pylops.readthedocs.io/en/stable/tutorials/solvers.html
- Class-based solvers and callbacks: https://pylops.readthedocs.io/en/stable/tutorials/classsolvers.html
- Image deblurring (Tikhonov, sparsity, TV): https://pylops.readthedocs.io/en/stable/tutorials/deblurring.html
- Real/complex inversion: https://pylops.readthedocs.io/en/stable/tutorials/realcomplex.html
