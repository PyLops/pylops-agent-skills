---
name: pick-sparsifying-transform
description: Choose a sparsifying transform for a signal or image in a PyLops sparsity-promoting inversion (FFT/FFT2D/FFTND, DCT, DWT/DWT2D/DWTND, DTCWT, Seislet, curvelets via UDCT, Radon/FourierRadon/ChirpRadon, windowed versions with Sliding/Patch), check its optional dependencies and frame properties, compare candidates quantitatively with a best-k-term compressibility test, and wire the winner into fista/spgl1 in synthesis or analysis form. Use when the user asks "which transform should I use for sparsity", "wavelets or curvelets for my data", "make my model sparse for fista/spgl1", "compressive sensing / interpolation with PyLops".
---

Goal: a transform chosen by evidence (not habit) for the user's signal, and
correct code that uses it in a sparsity-promoting PyLops inversion. Do not modify
the installed `pylops` package.

## 0. Check the environment

- Use the project's Python runner; check `pylops.__version__`.
- Optional dependencies (ask before installing):
  - `DWT`, `DWT2D`, `DWTND` → `PyWavelets` (`pywt`);
  - `UDCT` (curvelets) → `curvelets>=1.2`;
  - `DTCWT` → `dtcwt` (may lag behind NumPy 2);
  - `spgl1` solver → `spgl1`;
  - fast `Radon2D/3D` → `numba` (`engine="numba"`);
  - the external Curvelops package (FDCT via CurveLab) is a separate install –
    only suggest it if `UDCT` is not suitable.
- Check what imports: `python -c "import pywt, curvelets, spgl1"` etc.

## 1. Understand the signal

Ask for (or load) a **representative example** of the model/data to be made
sparse – ideally noise-free (a synthetic, a well-sampled subset, or a previous
good result). Characterise it:

| Signal character | Natural candidates |
|---|---|
| sum of few sinusoids / band-limited, stationary | `FFT`, `FFT2D`, `FFTND` (`norm="ortho"`), `DCT` |
| smooth with localised discontinuities (1-D, images) | `DWT`/`DWT2D`/`DWTND` (e.g. `db4`, `sym8`, few levels) |
| piecewise constant / blocky | `DWT` with `haar`, or not a transform at all: TV (`splitbregman`, PyProximal) |
| images/seismic with oriented curved edges or events | curvelets `UDCT`, `DTCWT` |
| seismic events with smoothly varying slope | `Seislet` (needs slopes from `pylops.utils.signalprocessing.slope_estimate`) |
| linear/parabolic/hyperbolic seismic events | `Radon2D/3D`, `FourierRadon2D/3D`, `ChirpRadon2D/3D` |
| locally simple, globally complex | any of the above in windows with `Patch2D/3D` or `Sliding1D/2D/3D` (see `sliding-patch-processing`) |
| a learned or explicit dictionary | `MatrixMult(D)` with `omp` |

Shortlist 2–4 candidates.

## 2. Compare candidates

Adapt `reference/compressibility_test.py`: it reports, for each candidate
analysis transform `T` (data → coefficients):

- **tight frame or not** (`T.H @ T == I`): decides whether `T.H` reconstructs and
  whether analysis-form `fista` updates are exact (true for `FFT*` with
  `norm="ortho"`, orthogonal wavelets, `DCT`, `UDCT`; false for `Seislet`, Radon);
- **redundancy** (`T.shape[0] / T.shape[1]`): cost and memory grow with it;
- the **best-k-term curve**: SNR of the signal rebuilt from its largest *k*
  coefficients (*k* as a % of the number of signal samples, so redundant frames
  are not favoured). The best transform reaches high SNR with the fewest
  coefficients.

Radon-type operators map model (slowness, time) → data, so their "coefficients"
come from an inversion, not `T @ x`: compare them by running a short `fista` on
the representative signal instead of the best-k test.

Also weigh: speed of `matvec`/`rmatvec`, GPU support (see `accelerate-on-gpu`),
and parameters that need tuning (wavelet family/levels, curvelet scales/angles,
Radon slowness range and sampling).

## 3. Wire it into the inversion

Let `Op` be the physics/sampling operator (e.g. `Restriction` for interpolation)
and `S` the synthesis operator (coefficients → signal; for the transforms above
`S = T.H`, or the transform itself for Radon-type operators).

- **Synthesis** (`x = S p`, `p` sparse) – works for any `S`:
  - `pylops.spgl1(Op, y, SOp=T, sigma=...)` → `(x, p, info)`: note that `spgl1`
    takes the **analysis** transform `T` and internally inverts `Op @ T.H`,
    returning `x = T.H p`; set `sigma` from the noise level (`‖noise‖₂`);
  - or `p = pylops.fista(Op @ S, y, eps=..., niter=...)[0]`, then `x = S @ p`.
- **Analysis** (`‖T x‖₁` small) – `pylops.fista(Op, y, SOp=T.H, eps=...)`
  (here `SOp` is the **synthesis** side, penalty `‖SOpᴴ x‖₁`) is exact only for
  tight frames; otherwise use PyProximal (`solve-nonsmooth-problem` skill,
  e.g. `L1` composed with `T` in `PrimalDual`/`LinearizedADMM`).
- For complex transforms (`FFT*`, `UDCT`) of real signals, take `np.real` of the
  final `x`, and use `complexflag` in dot-tests.
- Dot-test `Op @ S` before inverting. Tune `eps`/`sigma` with
  `tune-regularization`.

## 4. Hand off

Report: the candidates tried, the compressibility table/plot and tight-frame
properties, the chosen transform with its parameters and why, dependency notes,
and the snippet (synthesis or analysis) used in the user's inversion.
