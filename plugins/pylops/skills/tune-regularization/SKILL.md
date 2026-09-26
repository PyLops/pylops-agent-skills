---
name: tune-regularization
description: Choose regularisation weights and thresholds for a PyLops inversion (epsRs in regularized_inversion, damp in cgls/lsqr, eps in ista/fista, epsRL1s in splitbregman, sigma/tau in spgl1, niter as implicit regularisation) with a principled, reproducible sweep - L-curve, discrepancy principle, GCV for small problems, or a synthetic test with a known model. Use when the user asks "how do I choose epsilon / lambda / damping", "my inversion is too smooth / too noisy", "make an L-curve", or after solve-inverse-problem produced a working but untuned inversion.
---

Goal: a **sweep script** in the user's project that evaluates a regularisation
parameter over a range, applies one or more selection criteria, and reports the
chosen value with a plot that justifies it. PyLops has no built-in L-curve / GCV /
discrepancy helper, so the skill provides `reference/lcurve_template.py`.

Requires a working inversion (operator passes the dot-test, solver runs). If there
is none, use `solve-inverse-problem` first.

## 0. Check the environment

Same as the other PyLops skills: use the project's Python runner, check
`pylops.__version__`, inspect solver signatures in the installed version.

## 1. Identify the parameter(s)

Map the user's solver to the knob being tuned and its meaning:

| Solver | Parameter | Objective term |
|---|---|---|
| `cgls` / `lsqr` | `damp` | `damp² ‖x‖²` |
| `regularized_inversion` | `epsRs=[ε₁, ε₂, …]` | `Σ εᵢ² ‖Rᵢ x‖²` |
| `normal_equations_inversion` | `epsI`, `epsRs` (and `epsNRs`) | `epsI² ‖x‖²`, `Σ εᵢ² ‖Rᵢ x‖²` (same scaling as `regularized_inversion`) |
| `ista` / `fista` | `eps` | `eps ‖SOpᴴ x‖₁` (effective threshold is `eps·alpha/2`) |
| `splitbregman` | `epsRL1s`, `epsRL2s`, `mu` | L1 and L2 weights, data weight |
| `spgl1` | `sigma` (BPDN) or `tau` (LASSO) | residual bound or L1-ball radius |
| any Krylov solver without explicit regularisation | `niter` | early stopping (semi-convergence) |

With more than one weight, tune one at a time (fix the others at a
scale-based guess), or fix their ratio and sweep an overall factor. Do not
launch a full grid over several parameters unless the problem is small.

## 2. Pick the criterion

Choose based on what the user knows:

1. **Known noise level** (sigma per sample, or an estimate from a noise-only
   window): **discrepancy principle** - choose the largest regularisation whose
   data residual `‖y − Op x‖` is ≤ `τ · σ · sqrt(N)`, `τ ≈ 1.0–1.1`. For
   `spgl1`, this is exactly `sigma = τ σ sqrt(N)`.
2. **Synthetic with a true model**: maximise `pylops.utils.metrics.snr(xtrue, x)`
   (report it, but warn it does not transfer 1:1 to field data).
3. **Nothing known**: **L-curve** - plot `log ‖Rx‖` vs `log ‖y − Op x‖` and pick the
   point of maximum curvature. Needs a wide enough range to show both branches.
4. **Small problem** (`Op.todense()` affordable, N, M ≲ 3000) and quadratic
   regularisation: **GCV** computed exactly on the dense matrices (implemented in
   the template).

Report more than one criterion when they are cheap; disagreement between them is
information for the user.

## 3. Write and run the sweep

Adapt `reference/lcurve_template.py`:

- replace `build_problem` with the user's operator, data and regularisation;
- replace `solve(eps, x0)` with the user's solver call **with everything else
  fixed** (same `niter`, tolerance, `x0` policy);
- use a **log-spaced grid** spanning at least 4 orders of magnitude around a
  scale-based guess (e.g. `ε₀ ≈ ‖Opᴴ y‖ / ‖Rᴴ R Opᴴ y‖` for quadratic terms, or
  `eps₀ ≈ max|Opᴴ y|` scale for L1 thresholds, where larger values give all-zero
  models);
- solve from large to small ε and **warm start** from the previous solution
  (`x0=...`) to save iterations - unless the solver ignores `x0`;
- keep `niter` large enough that each solve has converged, otherwise the curve
  measures iteration count, not regularisation (check a couple of cost curves);
- for early stopping as regulariser, run once with a callback that stores
  `x` every k iterations and compute the same criteria on iteration number.

Run it, then look at the plot before trusting the automatic pick: an L-curve with
no clear corner (common with L1 terms or very noisy data) should be reported as
such, not forced. With derivative regularisers a second knee often appears at
very large ε (the model collapses into the null space of `R`, e.g. a linear
trend for `SecondDerivative`); it bends the other way and is not the L-curve
corner – the template's curvature orientation already excludes it.

## 4. Hand off

Report:

- the parameter swept, the range and the number of solves;
- the value picked by each criterion and the one recommended, with the reason;
- the plot file(s) (L-curve, residual vs ε, SNR vs ε if available) and the
  model at the chosen value next to one over- and one under-regularised model;
- the exact line to change in the user's inversion script.
