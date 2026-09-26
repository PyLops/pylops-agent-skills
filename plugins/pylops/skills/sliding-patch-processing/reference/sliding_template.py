"""Template for windowed (Patch2D / Sliding2D) processing with PyLops.

Runs as-is: denoises a noisy 2-D gather by sparsity-promoting inversion of
local FFT2D patches. To adapt it, replace ``make_data`` and ``local_operator``
and keep the design -> tiling check -> dot-test -> invert structure.

Conventions (PyLops 2.x):
- the local operator maps ONE window of model coefficients (shape ``nop``)
  to ONE window of data (shape ``nwin``), i.e. ``Op.shape == (prod(nwin), prod(nop))``.
  For a transform T acting on data, pass ``T.H`` (synthesis);
- ``Patch2D`` windows both axes, ``Sliding2D`` only axis 0 (the local operator
  then acts on (nwin, full axis 1));
- forward: coefficients -> data; adjoint: data -> coefficients.
"""

import matplotlib.pyplot as plt
import numpy as np

import pylops
from pylops.signalprocessing import Patch2D, patch2d_design
from pylops.utils import dottest
from pylops.utils.metrics import snr


def make_data(rng):
    """ADAPT: return (clean or None, observed) 2-D arrays."""
    par = {"ox": 0, "dx": 2, "nx": 120, "ot": 0, "dt": 0.004, "nt": 180, "f0": 20}
    t, _, x, _ = pylops.utils.seismicevents.makeaxis(par)
    wav = pylops.utils.wavelets.ricker(t[:41], f0=par["f0"])[0]
    _, clean = pylops.utils.seismicevents.parabolic2d(
        x - x.mean(), t, [0.15, 0.35, 0.5], [0, 0, 0], [1e-5, 5e-6, -3e-6], [1.0, -1.5, 0.8], wav
    )
    noisy = clean + 0.3 * rng.standard_normal(clean.shape)
    return clean, noisy


def local_operator(nwin, nop):
    """ADAPT: operator from one window of coefficients (nop) to data (nwin)."""
    return pylops.signalprocessing.FFT2D(nwin, nffts=nop, real=False).H


def check_tiling(dimsd, nwin, nover, tapertype):
    """Windows must cover the data and tapers must sum to one.

    Uses an identity local operator: tapered forward of the untapered adjoint
    must give back an array of ones everywhere.
    """
    nwins, dims, _, _ = patch2d_design(dimsd, nwin, nover, nwin)
    Id = pylops.Identity(int(np.prod(nwin)))
    Pnotap = Patch2D(Id, dims, dimsd, nwin, nover, nwin, tapertype=None)
    Ptap = Patch2D(Id, dims, dimsd, nwin, nover, nwin, tapertype=tapertype)
    ones = (Ptap @ (Pnotap.H @ np.ones(dimsd).ravel())).reshape(dimsd)
    err = np.abs(ones - 1)
    print(f"nwins={nwins}, max tiling error={err.max():.2e}")
    if err.max() > 1e-6:
        bad = np.argwhere(err > 1e-6)
        print(f"!! tiling/taper problem, e.g. at samples {bad[:3].tolist()} "
              "(uncovered edge: use patch2d_pad_to_next or change nwin/nover)")
    return err.max()


def main(nwin=(24, 36), nover=(8, 12), nop=(32, 64), tapertype="hanning", eps=0.5, niter=60):
    rng = np.random.default_rng(0)
    clean, noisy = make_data(rng)
    dimsd = noisy.shape

    # 1. design and tiling check
    check_tiling(dimsd, nwin, nover, tapertype)
    nwins, dims, _, _ = patch2d_design(dimsd, nwin, nover, nop)

    # 2. operators
    Op = local_operator(nwin, nop)
    assert Op.shape == (np.prod(nwin), np.prod(nop)), Op.shape
    P = Patch2D(Op, dims, dimsd, nwin, nover, nop, tapertype=tapertype)
    dottest(P, *P.shape, complexflag=2, rtol=1e-6, raiseerror=True)

    # 3. sparsity-promoting inversion for the patch coefficients
    coeffs, niters, cost = pylops.fista(P, noisy.ravel(), niter=niter, eps=eps,
                                        eigsdict=dict(niter=10, tol=1e-3))
    denoised = np.real(P @ coeffs).reshape(dimsd)

    if clean is not None:
        print(f"SNR noisy={snr(clean, noisy):.2f} dB, denoised={snr(clean, denoised):.2f} dB")

    fig, axs = plt.subplots(1, 4, figsize=(16, 4), sharey=True)
    for ax, img, title in zip(axs, [clean, noisy, denoised, noisy - denoised],
                              ["clean", "noisy", "denoised", "removed"]):
        if img is not None:
            ax.imshow(img.T, cmap="gray", vmin=-1, vmax=1, aspect="auto")
        ax.set_title(title)
    fig.tight_layout()
    fig.savefig("patch_denoising.png", dpi=120)
    return denoised


if __name__ == "__main__":
    main()
