"""Compare candidate sparsifying transforms on a representative signal.

For each candidate analysis transform ``T`` (data -> coefficients) it reports:
- whether ``T`` is a tight frame (``T.H @ T == I``), which decides whether
  ``fista(Op, y, SOp=T.H)`` analysis updates are exact and whether ``T.H``
  reconstructs;
- the best-k-term approximation curve: SNR of the signal rebuilt from the
  largest k coefficients, k given as % of the number of signal samples
  (higher is better at small k).

Runs as-is on a 2-D seismic-like gather. ADAPT ``make_signal`` and
``candidates``; candidates that miss optional dependencies are skipped.
"""

import matplotlib.pyplot as plt
import numpy as np

import pylops
from pylops.utils.metrics import snr


def make_signal():
    """ADAPT: return a representative (noise-free if possible) signal and samplings."""
    par = {"ox": 0, "dx": 10, "nx": 64, "ot": 0, "dt": 0.004, "nt": 128, "f0": 25}
    t, _, x, _ = pylops.utils.seismicevents.makeaxis(par)
    wav = pylops.utils.wavelets.ricker(t[:41], f0=par["f0"])[0]
    _, d = pylops.utils.seismicevents.linear2d(
        x, t, 1500, [0.1, 0.25, 0.35], [1500, 3000, -2500], [1.0, -0.8, 0.6], wav
    )
    return d, (par["dx"], par["dt"])


def candidates(d, sampling):
    """ADAPT: name -> callable returning an analysis operator on d.shape."""
    dims = d.shape
    c = {
        "FFT2D": lambda: pylops.signalprocessing.FFT2D(dims, norm="ortho"),
        "DCT": lambda: pylops.signalprocessing.DCT(dims),
        "DWT2D (db4, 3 levels)": lambda: pylops.signalprocessing.DWT2D(
            dims, wavelet="db4", level=3),
        "DWT2D (haar, 3 levels)": lambda: pylops.signalprocessing.DWT2D(
            dims, wavelet="haar", level=3),
    }

    def seislet():
        from pylops.utils.signalprocessing import slope_estimate

        slope = -slope_estimate(d.T, sampling[1], sampling[0], smooth=2.5)[0].T
        return pylops.signalprocessing.Seislet(slope, sampling=sampling)

    c["Seislet (estimated slopes)"] = seislet
    c["Curvelet UDCT"] = lambda: pylops.signalprocessing.UDCT(dims)
    return c


def tight_frame_error(T, nrep=3, seed=0):
    """max relative ||T^H T x - x|| over random x (0 => tight frame)."""
    rng = np.random.default_rng(seed)
    errs = []
    for _ in range(nrep):
        x = rng.standard_normal(T.shape[1])
        errs.append(np.linalg.norm(np.real(T.H @ (T @ x)).ravel() - x) / np.linalg.norm(x))
    return max(errs)


def reconstruct(T, c, tight):
    if tight:
        return np.real(T.H @ c).ravel()
    if hasattr(T, "inverse"):  # e.g. Seislet
        return np.real(T.inverse(c))
    return np.real(pylops.lsqr(T, c, niter=100, atol=1e-10, btol=1e-10)[0])


def best_k_curve(T, x, percents, tight):
    c = (T @ x.ravel()).ravel()
    order = np.argsort(np.abs(c))[::-1]
    out = []
    for p in percents:
        # k relative to the number of signal samples, so redundant frames are
        # not favoured by having more coefficients
        k = min(c.size, max(1, int(np.ceil(p / 100 * x.size))))
        ck = np.zeros_like(c)
        ck[order[:k]] = c[order[:k]]
        out.append(snr(x.ravel(), reconstruct(T, ck, tight)))
    return np.array(out)


def main(percents=(0.5, 1, 2, 5, 10, 20)):
    d, sampling = make_signal()
    results = {}
    for name, build in candidates(d, sampling).items():
        try:
            T = build()
        except (ModuleNotFoundError, ImportError) as e:
            print(f"skip {name}: {e}")
            continue
        tfe = tight_frame_error(T)
        tight = tfe < 1e-6
        redundancy = T.shape[0] / T.shape[1]
        curve = best_k_curve(T, d, percents, tight)
        results[name] = curve
        print(f"{name:28s} redundancy={redundancy:5.2f} tight-frame={'yes' if tight else f'no ({tfe:.1e})':>12s} "
              + " ".join(f"{p}%:{s:6.1f}dB" for p, s in zip(percents, curve)))

    fig, ax = plt.subplots(figsize=(7, 4))
    for name, curve in results.items():
        ax.semilogx(percents, curve, ".-", label=name)
    ax.set_xlabel("coefficients kept [% of signal samples]")
    ax.set_ylabel("SNR of reconstruction [dB]")
    ax.legend(fontsize=8)
    ax.grid(True, which="both", alpha=0.3)
    fig.tight_layout()
    fig.savefig("compressibility.png", dpi=120)
    return results


if __name__ == "__main__":
    main()
