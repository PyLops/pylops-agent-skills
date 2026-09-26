"""Diagnostic helpers for PyLops inversions.

Copy next to the user's script (or import from here) and call on a reduced
version of their problem. Only the public PyLops API is used; composite
operators are walked through their ``ops`` (stacks, block diagonals) and
``args`` (products, sums, scalings, adjoints) attributes.

Usage::

    from diagnostics import describe_problem, dottest_blocks, scaling_report, plot_convergence
    describe_problem(Op, y, x0)
    dottest_blocks(Op)
    scaling_report(Op, y)
    plot_convergence(cost, xs=None, xtrue=None)
"""

import numpy as np

import pylops
from pylops.utils import dottest
from pylops.utils.backend import get_array_module


def describe_problem(Op, y, x0=None):
    """Print shapes, dtypes and finiteness of operator, data and starting model."""
    print(f"Op: {Op}  dims={getattr(Op, 'dims', None)} dimsd={getattr(Op, 'dimsd', None)}")
    for name, arr in (("y", y), ("x0", x0)):
        if arr is None:
            continue
        ncp = get_array_module(arr)
        print(
            f"{name}: shape={arr.shape} dtype={arr.dtype} backend={ncp.__name__} "
            f"finite={bool(ncp.all(ncp.isfinite(arr)))} norm={float(ncp.linalg.norm(arr.ravel())):.3e}"
        )
    if y is not None and y.size != Op.shape[0]:
        print(f"!! data size {y.size} != Op.shape[0] {Op.shape[0]}")
    if x0 is not None and x0.size != Op.shape[1]:
        print(f"!! x0 size {x0.size} != Op.shape[1] {Op.shape[1]}")
    if y is not None and np.iscomplexobj(y) != np.issubdtype(Op.dtype, np.complexfloating):
        print(f"!! complexity mismatch: Op.dtype={Op.dtype}, y.dtype={y.dtype}")


def _children(Op):
    """Sub-operators of a composite operator (empty for leaves)."""
    if hasattr(Op, "ops"):
        return list(Op.ops)
    args = getattr(Op, "args", ())
    return [a for a in args if isinstance(a, pylops.LinearOperator)]


def dottest_blocks(Op, complexflag=None, rtol=1e-6, path="Op", verbose=True):
    """Dot-test ``Op`` and, recursively, all its sub-operators.

    Returns a list of (path, shape, passed) tuples. The deepest failing path
    points to the operator whose adjoint is wrong.
    """
    if complexflag is None:
        complexflag = 3 if np.issubdtype(Op.dtype, np.complexfloating) else 0
    results = []
    try:
        ok = dottest(Op, *Op.shape, complexflag=complexflag, rtol=rtol, raiseerror=False)
    except Exception as e:  # operator fails to apply at all
        print(f"{path}: raised {type(e).__name__}: {e}")
        ok = False
    results.append((path, Op.shape, ok))
    if verbose:
        print(f"{'PASS' if ok else 'FAIL'}  {path:40s} {type(Op).__name__} {Op.shape}")
    for i, child in enumerate(_children(Op)):
        results += dottest_blocks(child, complexflag, rtol, f"{path}[{i}]", verbose)
    return results


def column_norms(Op, ncols=50, seed=0):
    """Norms of a random subset of operator columns (cheap scaling check)."""
    rng = np.random.default_rng(seed)
    idx = rng.choice(Op.shape[1], size=min(ncols, Op.shape[1]), replace=False)
    norms = []
    for j in idx:
        e = np.zeros(Op.shape[1], dtype=Op.dtype)
        e[j] = 1.0
        norms.append(np.linalg.norm(Op @ e))
    return idx, np.array(norms)


def scaling_report(Op, y, Regs=(), epsRs=(), niter_eigs=30):
    """Print largest singular value, data scale and regularisation balance."""
    smax = np.abs(Op.eigs(neigs=1, niter=niter_eigs))[0]
    ynorm = np.linalg.norm(y)
    print(f"largest singular value ~ {smax:.3e}")
    print(f"||y|| = {ynorm:.3e}, max|y| = {np.max(np.abs(y)):.3e}")
    print(f"||Op^H y|| = {np.linalg.norm(Op.H @ y):.3e}")
    _, cn = column_norms(Op)
    nz = cn[cn > 0]
    if nz.size:
        print(f"column norms (sample): min={nz.min():.3e} max={nz.max():.3e} "
              f"ratio={nz.max() / nz.min():.1e} zero-columns={np.sum(cn == 0)}")
    for i, (Reg, eps) in enumerate(zip(Regs, epsRs)):
        rmax = np.abs(Reg.eigs(neigs=1, niter=niter_eigs))[0]
        print(f"Reg[{i}]: eps*||R|| = {eps * rmax:.3e} vs ||Op|| = {smax:.3e} "
              f"(ratio {eps * rmax / smax:.1e})")
    if max(Op.shape) <= 3000:
        print(f"condition number (dense) = {np.linalg.cond(Op.todense()):.3e}")
    return smax


def plot_convergence(cost=None, xs=None, xtrue=None, Op=None, y=None, fname="convergence.png"):
    """Plot cost history and, if models per iteration are given, error/residual.

    ``xs`` can be collected with ``callback=lambda x: xs.append(x.copy())``.
    Error that decreases then increases while the residual keeps decreasing is
    the signature of semi-convergence (stop earlier or regularise).
    """
    import matplotlib.pyplot as plt

    npanels = 1 + (xs is not None and (xtrue is not None or Op is not None))
    fig, axs = plt.subplots(1, npanels, figsize=(6 * npanels, 4), squeeze=False)
    if cost is not None:
        axs[0, 0].semilogy(np.abs(cost), "k")
        axs[0, 0].set_title("cost")
        axs[0, 0].set_xlabel("iteration")
    if npanels > 1:
        ax = axs[0, 1]
        if xtrue is not None:
            err = [np.linalg.norm(x.ravel() - xtrue.ravel()) / np.linalg.norm(xtrue) for x in xs]
            ax.semilogy(err, "r", label="model error")
            print(f"min model error at iteration {int(np.argmin(err))} of {len(err)}")
        if Op is not None and y is not None:
            res = [np.linalg.norm(y.ravel() - Op @ x.ravel()) / np.linalg.norm(y) for x in xs]
            ax.semilogy(res, "b", label="data residual")
        ax.legend()
        ax.set_xlabel("iteration")
    fig.tight_layout()
    fig.savefig(fname, dpi=120)
    print(f"saved {fname}")


if __name__ == "__main__":
    # self-check on a problem with a deliberately wrong adjoint in one block
    n = 30
    rng = np.random.default_rng(0)
    A = rng.standard_normal((n, n))
    good = pylops.MatrixMult(A)
    bad = pylops.FunctionOperator(lambda x: A @ x, lambda y: A @ y, n, n)  # not A^T
    Op = pylops.VStack([good, 2.0 * pylops.Diagonal(np.ones(n)) * bad])
    y = Op @ np.ones(n)
    describe_problem(Op, y)
    dottest_blocks(Op)
    scaling_report(Op, y)
