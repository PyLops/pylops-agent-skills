"""Template to port a PyLops workflow to CuPy/JAX and benchmark it against NumPy.

``build_problem(xp, dtype)`` must create every array held by the operators with
the array module ``xp``, so the same code runs on any backend. Runs as-is on a
toy 2-D deblurring problem; backends that are not installed are skipped.

    python benchmark_template.py --sizes 128 512 --dtype float32
"""

import time

import numpy as np

import pylops
from pylops.utils import dottest
from pylops.utils.backend import to_numpy


def build_problem(xp, n, dtype):
    """ADAPT: return (Op, y, x0) with all arrays created through ``xp``."""
    ny = nx = n
    yy, xx = np.meshgrid(np.arange(-8, 9), np.arange(-8, 9), indexing="ij")
    h = np.exp(-(yy**2 + xx**2) / 8.0)
    h = xp.asarray(h / h.sum(), dtype=dtype)
    Op = pylops.signalprocessing.Convolve2D((ny, nx), h=h, offset=(8, 8), dtype=dtype)
    # build on host and move once: JAX arrays do not support in-place assignment
    xtrue = np.zeros((ny, nx), dtype=dtype)
    xtrue[ny // 4 : 3 * ny // 4, nx // 4 : 3 * nx // 4] = 1.0
    y = Op @ xp.asarray(xtrue).ravel()
    x0 = xp.zeros(Op.shape[1], dtype=dtype)
    return Op, y, x0


def solve(Op, y, x0, niter):
    """ADAPT: the user's solver call (use engine="pylops" for wrapper solvers)."""
    return pylops.cgls(Op, y, x0=x0, niter=niter, tol=0.0)[0]


def backends():
    out = {"numpy": (np, lambda: None, lambda Op: Op)}
    try:
        import cupy as cp

        if cp.cuda.runtime.getDeviceCount() > 0:
            out["cupy"] = (cp, lambda: cp.cuda.Device().synchronize(), lambda Op: Op)
    except Exception:
        pass
    try:
        import jax

        jax.config.update("jax_enable_x64", True)
        import jax.numpy as jnp

        out["jax"] = (jnp, lambda: None, pylops.JaxOperator)
    except Exception:
        pass
    return out


def timeit(fn, sync, nrep=5):
    fn()  # warm-up: kernel compilation / JIT
    sync()
    times = []
    for _ in range(nrep):
        t0 = time.perf_counter()
        out = fn()
        if hasattr(out, "block_until_ready"):
            out.block_until_ready()
        sync()
        times.append(time.perf_counter() - t0)
    return float(np.median(times))


def main(sizes=(128, 256), dtype="float32", niter=30):
    rtol = 1e-3 if dtype in ("float32", "complex64") else 1e-8
    rows, ref = [], {}
    for name, (xp, sync, wrap) in backends().items():
        for n in sizes:
            Op, y, x0 = build_problem(xp, n, dtype)
            Op = wrap(Op)
            if name == "numpy":
                dottest(Op, *Op.shape, rtol=rtol * 10, raiseerror=True)
            elif name == "cupy":
                dottest(Op, *Op.shape, rtol=rtol * 10, raiseerror=True, backend="cupy")
            tfwd = timeit(lambda: Op.matvec(x0 + 1), sync)
            tadj = timeit(lambda: Op.rmatvec(y), sync)
            tsol = timeit(lambda: solve(Op, y, x0, niter), sync, nrep=3)
            xinv = np.asarray(to_numpy(solve(Op, y, x0, niter)))
            if name == "numpy":
                ref[n] = xinv
                err = 0.0
            else:
                err = np.linalg.norm(xinv - ref[n]) / np.linalg.norm(ref[n])
            rows.append((name, n, tfwd, tadj, tsol, err))

    print(f"{'backend':8s} {'n':>6s} {'matvec[s]':>10s} {'rmatvec[s]':>11s} "
          f"{'solve[s]':>9s} {'rel.err vs numpy':>17s}")
    for name, n, tf, ta, ts, err in rows:
        flag = "" if err <= rtol * 10 else "  !! mismatch"
        print(f"{name:8s} {n:6d} {tf:10.2e} {ta:11.2e} {ts:9.2e} {err:17.2e}{flag}")
    return rows


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--sizes", type=int, nargs="+", default=[128, 256])
    parser.add_argument("--dtype", default="float32")
    parser.add_argument("--niter", type=int, default=30)
    args = parser.parse_args()
    main(args.sizes, args.dtype, args.niter)
