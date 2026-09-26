---
name: accelerate-on-gpu
description: Move an existing PyLops workflow (operators, custom LinearOperators and solvers) from NumPy on CPU to GPU with CuPy, or to JAX, and benchmark it against the CPU version. Covers backend-agnostic custom operators, dtype choice, host/device transfers, operators without GPU support, mixed CPU/GPU setups with ToCupy, and correct GPU timing. Use when the user asks "run my PyLops inversion on GPU", "use cupy with pylops", "my PyLops code is too slow", "port this operator to JAX".
---

Goal: the user's workflow runs on the GPU (CuPy) or with JAX, gives the same
result as on CPU (within dtype precision), and a benchmark shows whether it is
actually faster. Do not modify the installed `pylops` package.

## 0. Check the environment

- Use the project's Python runner. Check `pylops.__version__`, and whether a GPU
  and backend are usable:
  - CuPy: `python -c "import cupy as cp; print(cp.__version__, cp.cuda.runtime.getDeviceCount())"`
  - JAX: `python -c "import jax; print(jax.__version__, jax.devices())"`
- PyLops detects CuPy/JAX **at import time**: they must be installed before (or
  alongside) PyLops, and `CUPY_PYLOPS=0` / `JAX_PYLOPS=0` in the environment
  disable them. If `import pylops` fails after installing CuPy/JAX, check versions
  against the PyLops installation docs. Ask before installing anything; the CuPy
  wheel must match the CUDA version (`cupy-cuda12x`, `cupy-cuda13x`, or PyLops
  extras `pylops[gpu-cu12]`/`pylops[gpu-cu13]`).
- If no GPU is available, still make the code backend-agnostic and test it on
  CPU with NumPy (and with JAX on CPU if installed); say clearly that GPU
  performance was not measured.

## 1. Inventory the workflow

List every operator in the chain and check GPU support in the PyLops GPU page
(https://pylops.readthedocs.io/en/stable/gpu.html) or the table below. Summary
for PyLops 2.x:

- **Work on CuPy and JAX**: basic operators (`MatrixMult`, `Diagonal`,
  `Identity`, `Restriction`, `VStack`/`HStack`/`BlockDiag`, `Kronecker`,
  `Transpose`, `Roll`, `Pad`, …), all derivatives, `FFT`/`FFT2D`/`FFTND`,
  `Shift`, `Convolve2D/ND`, `Fredholm1`, `Interp`, `ChirpRadon2D/3D`,
  `MDC`, `UpDownComposition2D/3D`, `Blending*`, `PoststackLinearModelling`,
  `AVOLinearModelling`.
- **CuPy only** (not JAX): `Sliding*`, `Patch*`, `Bilinear`,
  `NonStationaryConvolve2D`, `FourierRadon2D/3D` (`engine="cuda"`);
  `Convolve1D` and `PrestackLinearModelling` are partial on JAX.
- **CPU only**: `DWT*`, `DCT`, `Seislet`, `UDCT`, `Radon2D/3D`, `Spread`,
  `PWSprayer2D`, `PWSmoother2D`, `Kirchhoff` (its `engine="cuda"` is Numba-CUDA, not
  CuPy arrays), `AcousticWave2D`; `LinearOperator.eigs`, `.cond`, `.trace`,
  `.tosparse`.
- Solvers in `pylops.optimization` work with CuPy/JAX arrays. Wrappers that
  default to SciPy (`regularized_inversion`, `preconditioned_inversion`,
  `normal_equations_inversion`, `irls`, `omp`, `splitbregman`) switch to the
  PyLops inner solver for non-NumPy arrays, so their `kwargs_solver` must then use
  PyLops names (`niter`, not SciPy's `iter_lim`): pass `engine="pylops"` explicitly
  so CPU and GPU runs take the same arguments. `spgl1` is CPU only.

The installed version is authoritative: when unsure, try the operator on a small
CuPy array and compare with NumPy.

## 2. Port

- **One switch**: introduce a backend variable (`xp = cupy` or `numpy`, or a
  `backend="numpy"|"cupy"|"jax"` argument) and create every array the operators
  hold (matrices, filters, wavelets, masks, diagonals) and the data/`x0` with it.
  PyLops picks the backend from the arrays: an operator built with NumPy arrays
  applied to CuPy data fails or silently copies.
  `pylops.utils.backend.get_module(backend)` returns the module.
- **dtype**: prefer `float32`/`complex64` on GPU (consumer GPUs are much slower in
  double precision); pass `dtype=` to operators consistently. Check the accuracy
  impact against the `float64` CPU run.
- **Custom operators** (`LinearOperator` subclasses written by the user): replace
  `np.` calls on inputs with `ncp = get_array_module(x)` and `ncp.`; move stored
  parameters to the input's device with `to_cupy_conditional(x, self.param)`; avoid
  `np.asarray`, `.tolist()`, Python loops over elements and SciPy functions on
  CuPy arrays (use `cupyx.scipy` equivalents). Re-run the dot-test with
  `dottest(..., backend="cupy")`.
- **JAX**: wrap the final operator in `pylops.JaxOperator(Op)` (JIT-compiles
  `matvec`/`rmatvec`); `Op.rmatvecad(x, y)` gives an autodiff adjoint to test a
  hand-written one. JAX arrays are immutable: replace in-place assignments
  (`x[idx] = v`) in the user's setup code with NumPy construction followed by
  `jnp.asarray`, or with `x.at[idx].set(v)`. `ToCupy`/`inoutengine` mixed setups
  are not available with JAX.
- **Unsupported operators**: keep them on CPU and sandwich GPU parts with
  `pylops.ToCupy` (`Top1.H @ GpuOp @ Top`), or use `VStack`/`BlockDiag` with
  `inoutengine=("numpy", "cupy")` when the model fits on GPU but the data does
  not. This is also the pattern when the full data do not fit in GPU memory.
- **Transfers**: move data to the GPU once (`cp.asarray`) and results back once
  (`cp.asnumpy` or `pylops.utils.backend.to_numpy`) – not inside callbacks or
  loops. Plotting needs NumPy arrays.
- `LinearOperator.eigs` / `cond` are CPU only. `ista`/`fista` with `alpha=None`
  already switch to `pylops.optimization.eigs.power_iteration` for non-NumPy
  arrays, but `eigsdict` keys then go to `power_iteration` (`niter`, `tol`) instead
  of `eigs`; for your own estimates call
  `power_iteration(Op.H @ Op, niter=..., dtype=..., backend="cupy")`, or compute
  `alpha` once on CPU and pass it.

## 3. Verify and benchmark

Adapt `reference/benchmark_template.py`:

- compare forward, adjoint and final inversion result CPU vs GPU
  (`np.allclose` with a tolerance matching the dtype, e.g. `rtol=1e-4` for float32);
- time `matvec`, `rmatvec` and the full solve after a **warm-up** call
  (CuPy compiles kernels and JAX JIT-compiles on first use) and with
  **synchronisation** (`cp.cuda.Device().synchronize()`,
  `jax.block_until_ready`) – otherwise GPU timings are meaningless;
- repeat several times and report median; try at least two problem sizes
  (small problems are often faster on CPU).

## 4. Hand off

Report: what changed (backend switch, custom-operator edits, operators kept on
CPU), the accuracy check, the timing table (CPU vs GPU, per size), and remaining
bottlenecks (CPU-only operators, transfers).
