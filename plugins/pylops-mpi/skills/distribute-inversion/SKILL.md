---
name: distribute-inversion
description: Distribute an existing single-process PyLops workflow over MPI with PyLops-MPI - choose what to split (blocks, sources, frequencies, a spatial axis), map operators to MPIBlockDiag / MPIVStack / MPIHStack / stacked and derivative operators, build DistributedArrays with the right partition (SCATTER vs BROADCAST) and local shapes, dot-test, solve with pylops_mpi solvers (cgls, cg, ista, fista), and run with mpiexec, optionally on GPUs with CuPy/NCCL. Use when the user says "my PyLops inversion does not fit in memory / is too slow on one node", "parallelise this over shots / frequencies with MPI", "port this to pylops-mpi".
---

Goal: an MPI version of the user's PyLops script that gives the same result as
the serial one on a small case, scales to their real size, and is launched with
`mpiexec`. Do not modify the installed `pylops` / `pylops_mpi` packages.

## 0. Check the environment

- Use the project's Python runner. Check versions:
  `python -c "import pylops, pylops_mpi, mpi4py; print(pylops.__version__, pylops_mpi.__version__, mpi4py.__version__)"`
  and that an MPI implementation is available (`mpiexec --version`).
- PyLops-MPI changes quickly (new operators and solvers every release): inspect
  the installed API (`help(pylops_mpi.MPIBlockDiag)`, `dir(pylops_mpi)`) rather
  than relying on memory. Keep `pylops`, `pylops_mpi` and `pyproximal` versions
  mutually compatible (released versions from the same period); mixing a
  development checkout of one with a release of another can break imports or
  solvers.
- Installing: MPI itself first (conda `openmpi`/`mpich` recommended), then
  `pip install pylops-mpi`; `mpi4py-fft` for the distributed FFTs. Ask before
  installing, and ask before launching MPI jobs on the user's machine (they may
  prefer to run them on a cluster/CI).

## 1. Decide what to distribute

Read the serial script and find the natural split:

| Structure of the serial problem | Pattern | PyLops-MPI |
|---|---|---|
| independent sub-problems `yᵢ = Aᵢ xᵢ` (e.g. post-stack inversion per inline, per frequency with no coupling) | block diagonal | `MPIBlockDiag(ops=[Aᵢ])` – model and data **SCATTER** |
| one model, data in blocks `yᵢ = Aᵢ x` (shots in LSM/FWI-like, receivers, time windows) | vertical stack | `MPIVStack(ops=[Aᵢ])` – model **BROADCAST**, data **SCATTER** |
| several models summed into one data `y = Σ Aᵢ xᵢ` (e.g. blended sources) | horizontal stack | `MPIHStack(ops=[Aᵢ])` – model **SCATTER**, data **BROADCAST** |
| large dense matrix | distributed matmul | `MPIMatrixMult(A_local, M, kind="summa" or "block")` |
| operator already written for full arrays, identical on all ranks | replicated | `asmpilinearoperator(Op)` / `MPILinearOperator(Op)` – **BROADCAST** |
| regularisation coupling the split axis | derivatives with halo exchange | `MPIFirstDerivative`, `MPISecondDerivative`, `MPILaplacian`, `MPIGradient`, `MPIHalo` |
| data + regularisation terms | stacking MPI operators | `MPIStackedVStack([Op, eps * Reg])` with `StackedDistributedArray([y, zeros])` |
| MDC / Fredholm over frequencies, FFTs | specialised | `pylops_mpi.waveeqprocessing.MPIMDC`, `pylops_mpi.signalprocessing.MPIFredholm1`, `MPIFFT2D`, `MPIFFTND`, `MPINonStationaryConvolve1D` |

Each rank builds **only its own blocks** (its shots, frequencies, slices):
split the index range with `from pylops_mpi.DistributedArray import local_split`
(`local_split(global_shape, comm, Partition.SCATTER, axis)`) or explicit
`rank * n : (rank + 1) * n` slicing, and load only the corresponding data.

## 2. Build arrays with the right partition

- `DistributedArray(global_shape, partition=Partition.SCATTER|BROADCAST, axis=0,
  local_shapes=..., dtype=...)`, fill each rank's part with `x[:] = local_values`;
  or `DistributedArray.to_dist(full_array, partition=...)` when the full array
  exists (small cases).
- Match the partition to the operator (table above); a mismatch raises
  `ValueError` or silently re-distributes data.
- For SCATTER arrays, pass `local_shapes=Op.local_shapes_m` (model) /
  `Op.local_shapes_n` (data) from `MPIBlockDiag`/`MPIVStack` so each rank's local
  size matches its blocks; the default even split only matches when blocks have
  equal size.
- Writing to a BROADCAST array broadcasts rank 0's values to all ranks.
- `x0` is **required** by `pylops_mpi` solvers and must have the model partition
  (`x0 = x.zeros_like()` or a DistributedArray filled with the starting model).

## 3. Write the script

Adapt `reference/mpi_template.py` (both the block-diagonal and the stacked
patterns are there):

- one script run by every rank; `rank = MPI.COMM_WORLD.Get_rank()`;
- dot-test with `pylops_mpi.utils.dottest(Op, u, v, nr, nc)` where `u`, `v` are
  DistributedArrays with the model/data partitions;
- solvers: `pylops_mpi.cgls(Op, y, x0, niter, damp, tol)` →
  `(x, istop, iiter, r1norm, r2norm, cost)`, `pylops_mpi.cg(Op, y, x0, niter, tol)` →
  `(x, iiter, cost)`; sparsity `pylops_mpi.ista` / `pylops_mpi.fista` (recent
  versions) with `pylops_mpi.optimization.eigs.power_iteration` for the step;
  proximal solvers in `pylops_mpi.proximal` (recent versions);
- **collective calls** (`asarray()`, `norm()`, `dot()`, solvers, operator
  applications) must be executed by **all ranks**; guard only printing, plotting
  and file writing with `if rank == 0:`;
- gather to rank 0 (`x.asarray()`) only for final output and small cases; for
  large models write per-rank files or use parallel I/O;
- keep the serial script: compare results on a small case (template's
  `serial_check`).

## 4. GPUs (optional)

- CuPy: create the local operators with CuPy arrays, `DistributedArray(..., engine="cupy")`,
  and bind one GPU per rank (`cp.cuda.Device(rank % ndev).use()`).
- NCCL for GPU-to-GPU communication: create the communicator with
  `pylops_mpi.utils._nccl.initialize_nccl_comm()` (private module – check the
  installed docs/examples for the current entry point) and pass
  `base_comm_nccl=...` to DistributedArrays; `NCCL_PYLOPS_MPI=0` disables it.
  Check the PyLops-MPI GPU page for which operators support NCCL.

## 5. Run and verify

- Run with `mpiexec -n <N> python script.py` (on a cluster, the scheduler's
  launcher, e.g. `srun`). Start with `-n 2` on a small case, compare with the
  serial run, then scale. If the user asked not to run MPI jobs locally, do only
  static checks (`python -m py_compile`, API inspection) and give them the
  command to run.
- Timing: `from pylops_mpi.utils.benchmark import benchmark, mark` (decorator
  `@benchmark`, `mark("label")` inside it) in recent versions, or `MPI.Wtime()` around the solve with a barrier.

## 6. Hand off

Report: the split chosen and why, the operator/partition mapping, the files
created, the dot-test and serial-vs-MPI comparison, the exact launch command,
and any version constraints discovered.
