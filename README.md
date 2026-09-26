![PyLops-Agent-Skills](https://github.com/PyLops/pylops-agent-skills/blob/main/asset/logo.png)

# Pylops Agent-Skills
Agent skills for scientists that use [PyLops](https://github.com/PyLops/pylops), [PyProximal](https://github.com/PyLops/pyproximal), and [PyLops-MPI](https://github.com/PyLops/pylops-mpi).

Each skill is a folder with a `SKILL.md` file (plus optional reference files)
following the open [Agent Skills](https://agentskills.io) format, so it can be
used by any coding agent that supports skills.

**Note**: skills for developers contributing to the libraries live in the different repository.

## Skills

Skills are grouped in one plugin per library.

### `pylops`

| Skill | What it does |
|-------|--------------|
| `wrap-operator` | Turns your forward model (local code, a URL or maths) into a PyLops operator in your project: picks between composing existing operators, `FunctionOperator` or a `LinearOperator` subclass, checks the adjoint with the dot-test, and adds tests. Triggered by requests such as *"make my blurring function a PyLops operator"*. |
| `solve-inverse-problem` | Picks the solver (`lsqr`, `cgls`, `regularized_inversion`, `fista`, `spgl1`, `splitbregman`, ...) and regularisation for your operator and data, and writes a runnable inversion script that reports convergence. Triggered by requests such as *"invert my data with this operator"*. |
| `tune-regularization` | Chooses regularisation weights, thresholds or iteration counts with an L-curve, the discrepancy principle, GCV or a synthetic test, and produces the sweep script and plots. Triggered by requests such as *"how do I choose epsilon?"* |
| `debug-inversion` | Diagnoses inversions that diverge, stall or look wrong: block-by-block dot-tests, shapes and dtypes, scaling, solver choice, stopping and noise. Reports evidence-backed findings. Triggered by requests such as *"my cgls doesn't converge"*. |
| `accelerate-on-gpu` | Ports a workflow to CuPy or JAX (backend-agnostic operators, dtypes, CPU-only operators, `ToCupy`) and benchmarks it against NumPy. Triggered by requests such as *"run my PyLops inversion on GPU"*. |
| `sliding-patch-processing` | Sets up `Sliding1D/2D/3D` and `Patch2D/3D` with the design and padding helpers, checks tiling and the adjoint, and uses them for local denoising or interpolation. Triggered by requests such as *"apply FFT in overlapping windows"*. |
| `pick-sparsifying-transform` | Compares candidate transforms (FFT, DCT, wavelets, Seislet, curvelets, Radon, ...) with a compressibility test and wires the winner into `fista`/`spgl1`. Triggered by requests such as *"wavelets or curvelets for my data?"* |

### `pyproximal`

| Skill | What it does |
|-------|--------------|
| `solve-nonsmooth-problem` | Writes the problem as f(x) + g(Kx), picks proximal operators (TV, L1, box, ...) and a solver (`ProximalGradient`, `ADMM`, `PrimalDual`, ...), derives step sizes from operator norms and checks convergence. Triggered by requests such as *"add TV and positivity to my inversion"*. |

### `pylops-mpi`

| Skill | What it does |
|-------|--------------|
| `distribute-inversion` | Distributes a single-process PyLops workflow with PyLops-MPI: chooses the split, maps operators to `MPIBlockDiag`/`MPIVStack`/`MPIHStack`, builds `DistributedArray`s with the right partition, dot-tests and solves. Triggered by requests such as *"parallelise my inversion over shots with MPI"*. |

## Installation

### Any agent, via the `skills` CLI

The [`skills`](https://github.com/vercel-labs/skills) CLI installs the skills
into Claude Code, Codex, Cursor, GitHub Copilot, OpenCode and many other agents:

```bash
npx skills add PyLops/pylops-agent-skills --list         # list available skills
npx skills add PyLops/pylops-agent-skills                # interactive installation
npx skills add PyLops/pylops-agent-skills --skill wrap-operator -a codex -g    # direct installation
```

with `-a <agent>` to pick the target agent(s) and `-g` to install for your user
instead of the current project.

### Claude Code plugin marketplace

This repository is also a Claude Code plugin marketplace:

```
/plugin marketplace add PyLops/pylops-agent-skills
/plugin install pylops@pylops-agent-skills
/plugin install pylops-mpi@pylops-agent-skills
/plugin install pyproximal@pylops-agent-skills
```

Skills are then available as `/<plugin>:<skill-name>` (e.g. `/pylops:solve-inverse-problem`).

### Manual

Copy a skill folder (e.g. `plugins/pylops/skills/wrap-operator/`) into the
skills directory your agent reads from (e.g. `.agents/skills/` or
`.claude/skills/`).

## Contributing

Add a skill as `plugins/<plugin>/skills/<skill-name>/SKILL.md` (`<plugin>` is
`pylops`, `pylops-mpi` or `pyproximal`), with any reference files next to it.
A new plugin also needs its own `plugins/<plugin>/.claude-plugin/plugin.json` and
an entry in `.claude-plugin/marketplace.json`.

Then bump `version` in `plugins/<plugin>/.claude-plugin/plugin.json` and check that the skill is picked up:

```bash
npx skills add . --list
claude plugin validate --strict .
for p in plugins/*/; do claude plugin validate --strict "$p"; done
```

**Note:** keep the instructions agent-agnostic: describe actions (e.g. "fetch the URL", "run the tests") rather than tool names of a specific agent.


## License

LGPL-2.1, see [LICENSE](LICENSE).
