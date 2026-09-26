"""Template for choosing a regularisation weight in a PyLops inversion.

Runs as-is on a toy 1-D deconvolution with second-derivative (smoothness)
regularisation. To adapt it, replace ``build_problem`` and ``solve`` and keep
the sweep, the selection criteria and the plots.

Criteria implemented:
- L-curve corner (maximum curvature in log-log);
- discrepancy principle (needs the noise standard deviation);
- best SNR against a known model (synthetic tests only);
- GCV, exact on dense matrices (small quadratic problems only).
"""

import matplotlib.pyplot as plt
import numpy as np

import pylops
from pylops.utils.metrics import snr


def build_problem(rng):
    """ADAPT: return (Op, Reg, y, xtrue or None, noise_std or None)."""
    nt = 201
    t = np.arange(nt) * 0.004
    h, _, hcenter = pylops.utils.wavelets.ricker(t[:41], f0=15)
    Op = pylops.signalprocessing.Convolve1D(nt, h=h, offset=hcenter)
    Reg = pylops.SecondDerivative(nt)

    xtrue = np.sin(2 * np.pi * 3 * t) * np.exp(-t)  # smooth model
    noise_std = 0.05
    y = Op @ xtrue + noise_std * rng.standard_normal(nt)
    return Op, Reg, y, xtrue, noise_std


def solve(Op, Reg, y, eps, x0):
    """ADAPT: the user's solver call with everything but ``eps`` fixed."""
    Opaug = pylops.VStack([Op, eps * Reg])
    yaug = np.concatenate([y, np.zeros(Reg.shape[0])])
    return pylops.cgls(Opaug, yaug, x0=x0, niter=200, tol=1e-10)[0]


def lcurve_corner(epsilons, rnorm, xnorm):
    """Index of the L-curve corner (maximum curvature in log-log).

    Points are ordered by increasing eps so that the corner between the
    "under-regularised" (vertical) and "over-regularised" (horizontal) branches
    has positive curvature. A second knee with opposite curvature can appear
    at very large eps (model pushed into the null space of the regulariser):
    it is not the L-curve corner.
    """
    order = np.argsort(epsilons)
    lr, lx = np.log(rnorm[order]), np.log(xnorm[order])
    # parametrise by arc length to make finite differences uniform
    s = np.concatenate([[0], np.cumsum(np.hypot(np.diff(lr), np.diff(lx)))])
    dr, dx = np.gradient(lr, s), np.gradient(lx, s)
    ddr, ddx = np.gradient(dr, s), np.gradient(dx, s)
    kappa = (dr * ddx - ddr * dx) / (dr**2 + dx**2) ** 1.5
    kappa[[0, -1]] = -np.inf  # ends are not valid corners
    kappa_orig = np.empty_like(kappa)
    kappa_orig[order] = kappa
    return int(np.argmax(kappa_orig)), kappa_orig


def discrepancy(epsilons, rnorm, noise_std, n, tau=1.02):
    """Largest eps whose residual is below tau * noise level (None if none)."""
    target = tau * noise_std * np.sqrt(n)
    ok = np.where(rnorm <= target)[0]
    return (int(ok[np.argmax(epsilons[ok])]) if ok.size else None), target


def gcv_dense(Op, Reg, y, epsilons):
    """Exact GCV for min ||y - A x||^2 + eps^2 ||R x||^2 (small problems)."""
    A, R = Op.todense(), Reg.todense()
    AtA, RtR, n = A.T.conj() @ A, R.T.conj() @ R, A.shape[0]
    g = []
    for eps in epsilons:
        H = A @ np.linalg.solve(AtA + eps**2 * RtR, A.T.conj())  # influence matrix
        r = y - H @ y
        g.append(n * np.real(r.conj() @ r) / np.real(n - np.trace(H)) ** 2)
    return int(np.argmin(g)), np.array(g)


def main(neps=25, seed=0, dense_gcv=True):
    rng = np.random.default_rng(seed)
    Op, Reg, y, xtrue, noise_std = build_problem(rng)

    # log grid around a scale-based guess, solved from large to small eps
    eps0 = np.linalg.norm(Op.H @ y) / np.linalg.norm(Reg.H @ (Reg @ (Op.H @ y)))
    epsilons = eps0 * np.logspace(3, -3, neps)

    xs, rnorm, xnorm = [], [], []
    x0 = np.zeros(Op.shape[1], dtype=Op.dtype)
    for eps in epsilons:
        x = solve(Op, Reg, y, eps, x0)
        x0 = x  # warm start
        xs.append(x)
        rnorm.append(np.linalg.norm(y - Op @ x))
        xnorm.append(np.linalg.norm(Reg @ x))
    rnorm, xnorm = np.array(rnorm), np.array(xnorm)

    picks = {}
    icorner, _ = lcurve_corner(epsilons, rnorm, xnorm)
    picks["L-curve"] = icorner
    if noise_std is not None:
        idisc, target = discrepancy(epsilons, rnorm, noise_std, y.size)
        if idisc is None:
            print(f"discrepancy: no eps reaches residual {target:.3e}; extend the grid")
        else:
            picks["discrepancy"] = idisc
    snrs = None
    if xtrue is not None:
        snrs = np.array([snr(xtrue, x) for x in xs])
        picks["best SNR"] = int(np.argmax(snrs))
    if dense_gcv and max(Op.shape) <= 3000:
        igcv, gcv = gcv_dense(Op, Reg, y, epsilons)
        picks["GCV"] = igcv

    for name, i in picks.items():
        extra = f", SNR={snrs[i]:.2f} dB" if snrs is not None else ""
        print(f"{name:12s}: eps={epsilons[i]:.3e}, ||r||={rnorm[i]:.3e}{extra}")

    fig, axs = plt.subplots(1, 3, figsize=(15, 4))
    axs[0].loglog(rnorm, xnorm, ".-k")
    for name, i in picks.items():
        axs[0].loglog(rnorm[i], xnorm[i], "o", label=name)
    axs[0].set_xlabel("||y - Op x||")
    axs[0].set_ylabel("||R x||")
    axs[0].set_title("L-curve")
    axs[0].legend()
    axs[1].loglog(epsilons, rnorm, ".-k", label="||r||")
    if noise_std is not None:
        axs[1].axhline(noise_std * np.sqrt(y.size), color="r", ls="--", label="noise level")
    if snrs is not None:
        ax2 = axs[1].twinx()
        ax2.semilogx(epsilons, snrs, ".-b")
        ax2.set_ylabel("SNR [dB]", color="b")
    axs[1].set_xlabel("eps")
    axs[1].legend()
    ilo, ihi = min(picks.values()), max(picks.values())
    ishow = {"over-regularised": max(0, ilo - 5), "chosen": icorner,
             "under-regularised": min(neps - 1, ihi + 5)}
    if xtrue is not None:
        axs[2].plot(xtrue, "k", lw=2, label="true")
    for name, i in ishow.items():
        axs[2].plot(xs[i], label=f"{name} (eps={epsilons[i]:.1e})")
    axs[2].legend()
    fig.tight_layout()
    fig.savefig("regularization_sweep.png", dpi=120)
    return epsilons, picks


if __name__ == "__main__":
    main()
