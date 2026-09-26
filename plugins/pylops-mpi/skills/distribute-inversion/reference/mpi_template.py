"""Template to distribute a PyLops inversion with PyLops-MPI.

Run with, e.g.:

    mpiexec -n 3 python mpi_template.py --pattern blockdiag
    mpiexec -n 3 python mpi_template.py --pattern vstack

Two patterns, pick the one matching the problem:

- ``blockdiag``: independent sub-problems (y_i = A_i x_i), e.g. 3-D post-stack
  inversion split along one spatial axis, one frequency per rank without
  coupling. Model and data are SCATTERed; ``MPIBlockDiag``.
- ``vstack``: one shared model, data split in blocks (y_i = A_i x), e.g. shots
  in least-squares migration. Model BROADCAST, data SCATTER; ``MPIVStack``.

ADAPT ``local_block`` (what each rank builds) and ``local_model``; keep the
array construction with explicit ``local_shapes``, the dot-test, the check
against a serial run on rank 0 (small sizes only) and rank-0-only I/O.
"""

import numpy as np
from mpi4py import MPI

import pylops
import pylops_mpi
from pylops_mpi import DistributedArray, Partition
from pylops_mpi.utils import dottest

comm = MPI.COMM_WORLD
rank, size = comm.Get_rank(), comm.Get_size()


def local_block(rank, n, m):
    """ADAPT: the PyLops operator owned by this rank."""
    rng = np.random.default_rng(100 + rank)
    return pylops.MatrixMult(rng.standard_normal((n, m)), dtype="float64")


def local_model(rank, m):
    """ADAPT: this rank's part of the true model (blockdiag pattern)."""
    return np.sin(np.linspace(0, 2 * np.pi, m) + rank)


def serial_check(Aloc, xloc_or_x, yloc, pattern):
    """Gather blocks on rank 0 and compare with a serial PyLops run (small sizes only)."""
    mats = comm.gather(Aloc.A, root=0)
    ys = comm.gather(yloc, root=0)
    xs = comm.gather(xloc_or_x, root=0)
    if rank == 0:
        if pattern == "blockdiag":
            Op = pylops.BlockDiag([pylops.MatrixMult(M) for M in mats])
            x = np.concatenate(xs)
        else:
            Op = pylops.VStack([pylops.MatrixMult(M) for M in mats])
            x = xs[0]
        print(f"serial == distributed forward: {np.allclose(Op @ x, np.concatenate(ys))}")


def main(pattern="blockdiag", n=40, m=30, niter=100):
    Aloc = local_block(rank, n, m)

    if pattern == "blockdiag":
        Op = pylops_mpi.MPIBlockDiag(ops=[Aloc])
        # model: SCATTER with this rank's block size (avoids silent re-distribution)
        x = DistributedArray(global_shape=Op.shape[1], local_shapes=Op.local_shapes_m,
                             partition=Partition.SCATTER, dtype=Aloc.dtype)
        x[:] = local_model(rank, m)
        xcheck = x.local_array
    elif pattern == "vstack":
        Op = pylops_mpi.MPIVStack(ops=[Aloc])
        # shared model: BROADCAST (writes on rank 0 are broadcast to all ranks)
        x = DistributedArray(global_shape=Op.shape[1], partition=Partition.BROADCAST,
                             dtype=Aloc.dtype)
        x[:] = np.sin(np.linspace(0, 2 * np.pi, m))
        xcheck = x.local_array
    else:
        raise ValueError(pattern)

    # 1. dot-test with arrays partitioned as the operator expects
    u = x.zeros_like()
    u[:] = np.random.default_rng(rank).standard_normal(u.local_shape)
    y = Op @ x
    v = y.zeros_like()
    v[:] = np.random.default_rng(10 + rank).standard_normal(v.local_shape)
    dottest(Op, u, v, *Op.shape, rtol=1e-6, raiseerror=True)
    if rank == 0:
        print(f"{pattern}: Op.shape={Op.shape}, ranks={size}, dot-test passed")

    # 2. optional: compare with serial PyLops on small sizes
    serial_check(Aloc, xcheck, y.local_array, pattern)

    # 3. invert (x0 is required and must have the model partition)
    x0 = x.zeros_like()
    xinv, istop, iiter, r1norm, r2norm, cost = pylops_mpi.cgls(Op, y, x0=x0, niter=niter,
                                                               tol=1e-10)

    # collective calls (asarray, norm, dot) must run on every rank
    err = (xinv - x).norm() / x.norm()
    xfull = xinv.asarray()
    if rank == 0:
        print(f"cgls: iterations={iiter}, relative model error={err:.2e}")
        np.save(f"xinv_{pattern}.npy", xfull)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--pattern", default="blockdiag", choices=["blockdiag", "vstack"])
    args = parser.parse_args()
    main(args.pattern)
