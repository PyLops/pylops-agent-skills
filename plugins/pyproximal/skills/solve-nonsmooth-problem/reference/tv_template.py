"""Template for a non-smooth inverse problem with PyProximal + PyLops.

Runs as-is on a toy 2-D deblurring problem with isotropic total variation:

    mode "tv":      min_x 1/2 ||y - B x||^2 + lam ||grad x||_{2,1}
                    f = L2(Op=B, b=y), g = lam * L21, K = Gradient      (PrimalDual)
    mode "tv+box":  same, plus lower <= x <= upper
                    f = Box, g = [L2(b=y) ; lam * L21] (pyproximal.VStack),
                    K = VStack([B, Gradient])                          (PrimalDual)

ADAPT ``build_problem`` (operator, data, true model) and the terms; keep the
step-size computation from ||K||^2, the cost callback and the checks.
"""

import matplotlib.pyplot as plt
import numpy as np

import pylops
import pyproximal
from pylops.utils.metrics import snr


def build_problem(rng):
    """ADAPT: return (B, y, xtrue or None, dims)."""
    ny, nx = 64, 80
    xtrue = np.zeros((ny, nx))
    xtrue[10:30, 10:40] = 1.0
    xtrue[35:55, 30:70] = 0.5
    xtrue[20:50, 55:65] = 0.8
    h = np.outer(np.hanning(9), np.hanning(9))
    B = pylops.signalprocessing.Convolve2D((ny, nx), h=h / h.sum(), offset=(4, 4))
    y = B @ xtrue.ravel() + 0.02 * rng.standard_normal(ny * nx)
    return B, y, xtrue, (ny, nx)


def spectral_norm_sq(K, niter=100, safety=1.05):
    """||K||^2 = largest eigenvalue of K^H K, via power iteration.

    Power iteration always returns an estimate (ARPACK ``eigs`` may raise
    ``ArpackNoConvergence``) but approaches it from below: inflate it slightly
    so that the step-size condition still holds.
    """
    from pylops.optimization.eigs import power_iteration

    eig = power_iteration(K.H @ K, niter=niter, tol=1e-6, dtype=K.dtype)[0]
    return safety * float(np.abs(eig))


def main(mode="tv", lam=0.02, niter=300, lower=0.0, upper=np.inf):
    rng = np.random.default_rng(0)
    B, y, xtrue, dims = build_problem(rng)
    D = pylops.Gradient(dims, edge=True, kind="forward", dtype=B.dtype)
    lam = float(lam)  # prox scaling requires floats: 2 * f returns None, 2.0 * f works

    if mode == "tv":
        proxf = pyproximal.L2(Op=B, b=y, niter=20, warm=True)  # prox needs an inner solve
        proxg = lam * pyproximal.L21(ndim=2)
        K = D
    elif mode == "tv+box":
        proxf = pyproximal.Box(lower, upper)
        proxg = pyproximal.VStack(
            [pyproximal.L2(b=y), lam * pyproximal.L21(ndim=2)],
            nn=[B.shape[0], D.shape[0]],
        )
        K = pylops.VStack([B, D])
    else:
        raise ValueError(mode)

    # step sizes: tau * mu * ||K||^2 < 1
    L = spectral_norm_sq(K)
    tau = mu = 0.95 / np.sqrt(L)
    print(f"mode={mode}, ||K||^2 ~ {L:.3f}, tau=mu={tau:.3e}")

    def cost(x):
        return 0.5 * np.linalg.norm(y - B @ x) ** 2 + lam * pyproximal.L21(ndim=2)(D @ x)

    costs = []
    x0 = np.zeros(B.shape[1])
    xinv = pyproximal.optimization.primaldual.PrimalDual(
        proxf, proxg, K, x0, tau=tau, mu=mu, theta=1.0, niter=niter,
        callback=lambda x: costs.append(cost(x)),
    )

    print(f"final cost={costs[-1]:.4e}, relative change last 10 its="
          f"{abs(costs[-1] - costs[-11]) / abs(costs[-11]):.1e}")
    if mode == "tv+box":
        print(f"bounds respected: {xinv.min() >= lower - 1e-8 and xinv.max() <= upper + 1e-8}")
    if xtrue is not None:
        print(f"SNR blurred={snr(xtrue.ravel(), y):.2f} dB, inverted={snr(xtrue.ravel(), xinv):.2f} dB")

    fig, axs = plt.subplots(1, 4, figsize=(16, 3.5))
    for ax, img, title in zip(axs[:3], [xtrue, y, xinv], ["true", "data", f"inverted ({mode})"]):
        if img is not None:
            ax.imshow(np.reshape(img, dims), cmap="gray", vmin=0, vmax=1)
        ax.set_title(title)
    axs[3].semilogy(costs)
    axs[3].set_title("cost")
    fig.tight_layout()
    fig.savefig(f"nonsmooth_{mode.replace('+', '_')}.png", dpi=120)
    return xinv


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", default="tv", choices=["tv", "tv+box"])
    parser.add_argument("--lam", type=float, default=0.02)
    parser.add_argument("--niter", type=int, default=300)
    args = parser.parse_args()
    main(args.mode, args.lam, args.niter)
