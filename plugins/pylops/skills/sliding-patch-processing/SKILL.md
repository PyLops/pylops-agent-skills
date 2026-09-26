---
name: sliding-patch-processing
description: Set up PyLops windowed operators - Sliding1D, Sliding2D, Sliding3D, Patch2D, Patch3D - to apply a local transform or operator over overlapping windows of 1-D/2-D/3-D data, choosing window size, overlap, taper and model size with the *_design and *_pad_to_next helpers, checking coverage and the dot-test, and using them for local denoising, interpolation or inversion. Use when the user asks "apply FFT/Radon/any operator in overlapping windows", "local transform / patching with PyLops", "Patch2D gives artefacts at the edges", "how do I pick nwin, nover, nop".
---

Goal: a correctly tiled windowed operator for the user's data and local
transform, proven by a coverage check and a dot-test, used in the processing
they need (usually a sparsity-promoting inversion). Do not modify the installed
`pylops` package.

## 0. Check the environment

Use the project's Python runner; check `pylops.__version__` and inspect the
installed signatures (`help(pylops.signalprocessing.Patch2D)`,
`help(pylops.signalprocessing.patch2d_design)`) – the design helpers and
`*_pad_to_next` are recent additions (PyLops ≥ 2.x).

## 1. Choose the operator

| Data | Windows along | Operator | Local operator acts on |
|---|---|---|---|
| 1-D signal | axis 0 | `Sliding1D(Op, dim, dimd, nwin, nover)` | `nwin` samples |
| 2-D, window one axis only (e.g. space, full time) | axis 0 | `Sliding2D(Op, dims, dimsd, nwin, nover)` | `(nwin, dimsd[1])` |
| 3-D, window two axes, full third | axes 0, 1 | `Sliding3D(Op, dims, dimsd, nwin, nover, nop)` | `(nwin[0], nwin[1], dimsd[2])` |
| 2-D, window both axes | axes 0, 1 | `Patch2D(Op, dims, dimsd, nwin, nover, nop)` | `nwin` (2-tuple) |
| 3-D, window all axes | axes 0, 1, 2 | `Patch3D(...)` | `nwin` (3-tuple) |

All live in `pylops.signalprocessing`. Common arguments: `tapertype`
(`"hanning"` default, `"cosine"`, `"cosinesquare"`, `None`), `savetaper`
(`True` = faster, `False` = less memory), `Patch*` also `scalings` (one factor per
window).

## 2. Define the local operator

The key convention: **`Op` maps one window of model coefficients to one window
of data**, i.e. `Op.shape == (prod(window data shape), prod(nop))`. For a
transform `T` that maps data → coefficients (FFT, Radon adjoint, wavelets), pass
its synthesis side, typically `T.H` (e.g. `FFT2D(nwin, nffts=nop).H`,
or `Radon2D(t, hwin, px)` which already maps (px, t) → (h, t)). For local
coordinates (e.g. Radon offsets), centre the window axis
(`np.linspace(-dx*nwin//2, dx*nwin//2, nwin)` with `centeredh=True`).

## 3. Design the windows

- `nwin`: long enough to contain the local structure (a few wavelengths/events),
  short enough that events are locally linear/sparse.
- `nover`: typically 20–50 % of `nwin`; needed for smooth tapering.
- `nop`: the model size per window in the transform domain (e.g. number of
  slopes, FFT sizes ≥ `nwin`).
- Call `nwins, dims, mwins_inends, dwins_inends = patch2d_design(dimsd, nwin, nover, nop)`
  (`sliding1d_design`, `sliding2d_design`, `sliding3d_design`, `patch3d_design`
  similarly) and use the returned `dims` for the operator.
- Windows may not reach the end of the data. Check `dwins_inends` (last end must
  equal `dimsd` along each windowed axis), or pad with
  `inpt_pad, nwins, dims, mwins_inends, dwins_inends = patch2d_pad_to_next(inpt, nwin, nover, nop)`
  (`sliding2d_pad_to_next`, `sliding3d_pad_to_next`, `patch3d_pad_to_next`
  likewise; for `Sliding1D` pad manually) and crop at the end.

## 4. Verify

Adapt `reference/sliding_template.py`:

1. **Tiling check** (`check_tiling`): with an identity local operator,
   `Ptaper @ Pnotaper.H @ ones == ones` everywhere. Any deviation means
   uncovered samples or tapers that do not sum to one.
2. **Dot-test** of the full windowed operator (`complexflag=2` when the local
   operator is complex in model and real in data, e.g. FFT synthesis).
3. For transforms, apply `P.H` to data and `P` back with an untapered adjoint and
   a tapered forward to see the reconstruction quality before inverting.

## 5. Use it

- **Denoising / sparse representation**: `pylops.fista(P, y, eps=..., niter=...)`
  or `pylops.spgl1(P, y, sigma=...)` for the window coefficients, then `P @ coeffs`.
- **Interpolation**: `Op = Restriction @ P` (or `R @ P`), invert for coefficients,
  apply `P` for the full data.
- **Adaptive subtraction / local filtering**: local `MatrixMult`/`Convolve1D`
  per window via `Sliding*`.
- Tune `eps` / `niter` with `tune-regularization`; pick the transform with
  `pick-sparsifying-transform`.
- CPU/CuPy only (not JAX); cost grows with the number of windows and overlap.

## 6. Hand off

Report: chosen operator and window parameters (with `nwins`), the tiling-check
and dot-test results, padding applied (if any), and the processing result (plots,
SNR if a reference is available).
