---
name: debug-inversion
description: Use whenever a user shares PyLops code or results that misbehave and asks what is wrong - a crash or traceback (dtype/casting errors, shape mismatches), a solver (lsqr, cgls, cg, fista, ista, spgl1, regularized_inversion, splitbregman) that stalls, diverges, returns NaNs, zeros, ringing or a wrong model, one dataset or block being ignored in a stacked/joint inversion, or a custom FunctionOperator/LinearOperator that may have a wrong adjoint - even when the bug looks obvious from the code. Diagnoses with evidence (block-by-block dot-tests incl. complex, dtype and dims checks, operator/data scaling, solver and eps/damp choice), then proposes the smallest fix and verifies it. Not for choosing a solver for a new, working setup (use solve-inverse-problem) or picking regularisation weights (use tune-regularization).
---

Goal: find **why** the user's inversion misbehaves, with evidence for each claim,
and propose the smallest fix. Diagnose first; change the user's code only after
reporting the findings (or when asked to fix). Never make a failing dot-test pass
by loosening its tolerance.

Carry out these steps yourself, now, in this conversation: nothing runs in the
background and no one else will report back. Do not end your turn until you have
given the user the report of section 2.

## 0. Reproduce

- Use the project's Python runner; note `pylops.__version__`, NumPy/SciPy (and
  CuPy/JAX if used) versions.
- Run the user's script as is and capture: solver output (`show=True`), return
  tuple (`istop`, iterations, cost history), shapes and dtypes of `Op`, `y`, `x0`.
- If it is slow, reproduce on a smaller size (fewer samples, fewer sources) that
  still shows the problem. Keep that reduced case for the checks below.
- If the user described the problem in words and gave no script, do not stop to
  ask for one: build a minimal reproduction from the numbers they gave (operator
  type, sizes, amplitudes, solver call), or reason from those numbers directly
  (e.g. compare `eps`, `damp`, `tol` with `‖Op‖` and `‖Opᴴ y‖`). Ask for the code
  only if the description does not pin down the problem.
- If Python or PyLops cannot be run here, say so once and reason from the code
  and the numbers the user gave. Never present a value as measured (dot-test
  result, error, cost, norm) unless a command you ran printed it; label anything
  else as an estimate.

`reference/diagnostics.py` contains helpers for the checks below (import or copy
them next to the user's script; do not add them to the user's package unless
asked).

## 1. Run the checks in this order

When a check fails, note the finding and its fix, then continue with the
remaining checks: an inversion often has more than one problem (e.g. a wrong
adjoint **and** badly scaled blocks), and fixing only the first may not improve
the result. After fixing a problem, re-run the inversion; if the result is still
poor, the next check is where to look.

1. **Adjoint (dot-test)** – `pylops.utils.dottest(Op, *Op.shape, complexflag=...)`
   on the full operator **and on every block** (`dottest_blocks` walks
   `VStack`/`HStack`/`BlockDiag` and products). Use `complexflag=3` if any part is
   complex. A failure localises the wrong adjoint → fix it (see `wrap-operator`).
   Custom `FunctionOperator`s with an "adjoint" that is actually an inverse or a
   non-conjugated transpose are the usual culprits.
2. **Shapes and ordering** – `Op.dims`/`Op.dimsd` vs how `y` was built: `y.ravel()`
   in C order matching `dimsd`, no silent transpose (e.g. `(nx, nt)` vs `(nt, nx)`),
   no broadcasting `(n,)` vs `(n, 1)`. Compare `Op @ xtrue` (or `Op @ x` for a
   simple test model) with the observed data visually: they must look alike.
3. **dtypes** – mixing `float32` operators with `float64` data, complex operators on
   real data (and vice-versa), or integer arrays. `describe_problem` prints them.
   For a complex operator and a real model, see the PyLops "Real/complex inversion"
   tutorial (`Op.toreal()`, `Op.toimag()`).
4. **NaN / Inf** – in `y`, `x0`, operator internals (e.g. divisions by zero in a
   `Diagonal`, `log` of a velocity model). Check `np.isfinite` everywhere.
5. **Scaling and conditioning** – `Op.eigs(neigs=1)` (largest singular value) and,
   for small problems, `Op.cond()`; `‖y‖`, `‖Opᴴ y‖`. Signs: data at 1e-10 or 1e+10,
   columns of the operator with norms spanning many orders of magnitude (e.g.
   stacked blocks with different physical units), regularisation weights orders
   of magnitude too large or small relative to `‖Op‖`. Fix by normalising data,
   weighting blocks, or preconditioning.
6. **Solver vs problem** – `cg` on a non-symmetric / non-square operator;
   `lsqr`/`cgls` on a huge `niter` without regularisation on noisy data
   (semi-convergence: error goes down then up); `fista` with a user-set `alpha`
   larger than `1/‖Op‖²` (diverges) – leave `alpha=None` or compute it from
   `Op.eigs`; `fista` with an `SOp` that is not orthogonal/tight-frame;
   `regularized_inversion` / `preconditioned_inversion` with `engine="scipy"`
   (default) while passing `niter` – SciPy's `lsqr` takes `iter_lim` and raises
   `TypeError`; either use `iter_lim=...` or `engine="pylops", niter=...`.
7. **Stopping** – look at the cost curve (`plot_convergence`): flat from the start
   ⇒ wrong setup (x0 already optimal, zero data, zero operator block); stops
   early with `istop` meaning "tolerance reached" at a bad model ⇒ `tol`/`atol`
   too loose relative to data scale; still decreasing at `niter` ⇒ increase
   `niter` or precondition.
8. **Regularisation and noise** – residual far below the noise level ⇒ overfitting
   (increase regularisation / stop earlier); far above ⇒ over-regularised or
   modelling error. Use the `tune-regularization` skill to pick weights properly.
9. **Modelling error** – the operator is right, but does not explain the data
   (wrong wavelet, sampling, units, geometry). Evidence: residual has coherent
   structure, not noise. Compare data and `Op @ x` for a best-guess model.
10. **Backend** – CuPy/JAX runs: arrays on different devices, operators built
    with NumPy arrays but applied to CuPy data, `float64` on consumer GPUs being
    very slow. See `accelerate-on-gpu`.

## 2. Report

For each finding, give: the check, the evidence (numbers, plot path, the failing
block name), the likely cause, and the proposed fix. Rank by impact. Then either
apply fixes (if the user asked) and re-run to show the improvement, or list the
exact changes to make.

Keep what you ran apart from what you did not:

- Mark each check as **run** (quote the command's output it rests on) or **not
  run** (say why, and label any statement about it as an expectation). Do not
  report a check as passed for a part you did not test, e.g. "every block passes
  the dot-test" when only the full operator was tested.
- For each proposed fix, say whether you tested it and what it changed. If a fix
  you tested did not help, say so explicitly and check your implementation of it
  before concluding that the problem is elsewhere.

Say the result is limited by the physics / data (null space, noise, limited
aperture) only when the operator and the data weighting are correct and a
tested fix did not improve it - not as a fallback when a fix did not work.
In that case say so explicitly rather than tweaking parameters.
