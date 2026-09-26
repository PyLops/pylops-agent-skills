"""Template for a PyLops inversion script.

Runs as-is on a toy 1-D deconvolution problem. To adapt it, replace
``build_problem`` with the user's operator and data and keep the rest:
dot-test, scaling, the solver call with named outputs, and the convergence
report. Delete the solver branches that are not needed.
"""

import matplotlib.pyplot as plt
import numpy as np

import pylops
from pylops.utils import dottest
from pylops.utils.metrics import snr


def build_problem(rng):
    """ADAPT: return (Op, y, xtrue or None, noise_std or None)."""
    nt = 301
    t = np.arange(nt) * 0.004
    h, _, hcenter = pylops.utils.wavelets.ricker(t[:41], f0=20)
    Op = pylops.signalprocessing.Convolve1D(nt, h=h, offset=hcenter, dtype="float64")

    xtrue = np.zeros(nt)
    xtrue[[50, 120, 125, 200, 260]] = [1.0, -0.6, 0.8, 0.5, -1.0]
    noise_std = 0.02
    y = Op @ xtrue + noise_std * rng.standard_normal(nt)
    return Op, y, xtrue, noise_std


def main(solver="regularized", niter=50, eps=None, seed=0):
    rng = np.random.default_rng(seed)
    Op, y, xtrue, noise_std = build_problem(rng)

    # 1. adjoint must be correct before anything else
    dottest(Op, *Op.shape, rtol=1e-6, raiseerror=True)

    # 2. scale data to O(1) to help Krylov solvers; undo at the end
    yscale = np.max(np.abs(y))
    ys = y / yscale

    # 3. invert (keep full tuples, name what is used)
    cost = None
    if solver == "cgls":
        xinv, istop, iiter, r1norm, r2norm, cost = pylops.cgls(
            Op, ys, x0=np.zeros(Op.shape[1]), niter=niter, damp=eps or 0.0, tol=1e-10
        )
        info = f"istop={istop}, iterations={iiter}"
    elif solver == "regularized":
        D2 = pylops.SecondDerivative(Op.dims, dtype=Op.dtype)
        eps = 0.1 if eps is None else eps  # to be tuned (see tune-regularization)
        xinv, istop, itn, r1norm, r2norm = pylops.regularized_inversion(
            Op, ys, [D2], epsRs=[eps], iter_lim=niter, atol=1e-10
        )
        info = f"istop={istop}, iterations={itn}"
    elif solver == "fista":
        eps = 0.05 if eps is None else eps  # to be tuned
        xinv, iiter, cost = pylops.fista(
            Op, ys, niter=niter, eps=eps, eigsdict=dict(niter=20, tol=1e-4), tol=1e-8
        )
        info = f"iterations={iiter}"
    else:
        raise ValueError(f"unknown solver {solver}")

    xinv = xinv * yscale

    # 4. report
    res = y - Op @ xinv
    relres = np.linalg.norm(res) / np.linalg.norm(y)
    print(f"solver={solver}, {info}")
    print(f"relative data residual = {relres:.3e}")
    if noise_std is not None:
        # expected ||noise|| / ||y||: a residual well below this means overfitting
        expected = noise_std * np.sqrt(y.size) / np.linalg.norm(y)
        print(f"expected (noise) relative residual ~ {expected:.3e}")
    if xtrue is not None:
        print(f"SNR(xtrue, xinv) = {snr(xtrue, xinv):.2f} dB")

    fig, axs = plt.subplots(1, 3 if cost is not None else 2, figsize=(14, 3.5))
    axs[0].plot(y, "k", label="data")
    axs[0].plot(Op @ xinv, "--r", label="modelled")
    axs[0].plot(res, "g", lw=0.5, label="residual")
    axs[0].legend()
    if xtrue is not None:
        axs[1].plot(xtrue, "k", label="true")
    axs[1].plot(xinv, "--r", label="inverted")
    axs[1].legend()
    if cost is not None:
        axs[2].semilogy(cost, "k")
        axs[2].set_title("cost")
        axs[2].set_xlabel("iteration")
    fig.tight_layout()
    fig.savefig(f"inversion_{solver}.png", dpi=120)
    np.save(f"xinv_{solver}.npy", xinv)
    return xinv


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--solver", default="regularized", choices=["cgls", "regularized", "fista"])
    parser.add_argument("--niter", type=int, default=50)
    parser.add_argument("--eps", type=float, default=None)
    args = parser.parse_args()
    main(args.solver, args.niter, args.eps)
