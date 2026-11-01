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

## Evals (Claude Code only)

Each plugin can ship an eval suite under `plugins/<plugin>/evals/` that measures
whether its skills actually help. Cases are grouped in one subfolder per skill
(`evals/<skill>/`) and their names start with a short skill prefix, so a single
skill can be run on its own with `--case '<prefix>-*'`. Every case is a folder
with a `prompt.md` (the user request, plus run settings in the front matter) and
a `graders/` folder of pass/fail checks: LLM-judged rubrics (e.g. "uses a
robust data misfit for data with outliers") and deterministic checks (e.g. "the
script printed an SNR above the threshold"). Each skill keeps at least one negative
case, so a filtered run still checks that the skill does not over-trigger.

The `pylops` plugin currently has evals for:

| Skill | Folder | Prefix |
| ----- | ------ | ------ |
| `solve-inverse-problem` | `evals/solve-inverse-problem/` | `sip-` |
| `debug-inversion` | `evals/debug-inversion/` | `dbg-` |
| `tune-regularization` | `evals/tune-regularization/` | `trg-` |

`solve-inverse-problem` cases (each asks for a script `invert.py` that is run and prints `SNR_DB=<value>` for the inverted model):

| Cases | What they test |
| ----- | -------------- |
| `sip-01`–`sip-04` | Inversions with a trap for the naive approach (blocky model under blur, outliers in the data, data of order 1e-7 with PyLops-native solvers, compressive sensing in the DCT): graded on the SNR reached, the prior chosen, not using the true model inside the inversion, and on reporting the residual vs the noise level and how the solver stopped |
| `sip-05`–`sip-06` | Negative cases next to sibling skills (a broken operator for `debug-inversion`, an L-curve request for `tune-regularization`): the skill should *not* trigger |

`debug-inversion` cases (each shares a misbehaving inversion, as a script or in prose, and asks what is wrong):

| Cases | What they test |
| ----- | -------------- |
| `dbg-01`–`dbg-07` | A wrong adjoint (off-by-one slice, missing conjugate, forward instead of reverse cumsum), a missing complex `dtype`, badly scaled stacked blocks, an `eps` far too large for `fista`, a result limited by the physics rather than a bug, and a case with two independent bugs: graded on the diagnosis and fix, and on not reporting values that no command in the run produced |
| `dbg-08`–`dbg-09` | Negative cases (choosing a solver for a new problem, a SciPy optimisation question): the skill should *not* trigger |

`tune-regularization` cases (each asks for a script `sweep.py` that is run and prints the recommended value, e.g. `EPS_CHOSEN=<value>`):

| Cases | What they test |
| ----- | -------------- |
| `trg-01`–`trg-05` | Choosing a regularisation knob for a working inversion: `epsRs` by L-curve and discrepancy (`regularized_inversion`), `damp` of `lsqr` by the discrepancy principle, the scale of `eps` in `fista`, `niter` of `cgls` as implicit regularisation, and `damp` by GCV on a small dense problem with unknown noise: graded on the sweep design, the criterion used, the value reached, not using the true model to pick it, and on not reporting values that no command in the run produced |
| `trg-06` | Negative case (build an inversion from scratch): `solve-inverse-problem` should fire and `tune-regularization` should *not* |

The `pyproximal` plugin currently has evals for:

| Skill | Folder | Prefix |
| ----- | ------ | ------ |
| `solve-nonsmooth-problem` | `evals/solve-nonsmooth-problem/` | `sns-` |

`solve-nonsmooth-problem` cases (each asks for a script `invert.py` that is run and prints `SNR_DB=<value>` for the inverted model):

| Cases | What they test |
| ----- | -------------- |
| `sns-01`–`sns-04` | Non-smooth problems with a trap for the naive approach (bounds on a blurred noisy model, two signals with a shared sparse support, low-rank matrix completion, a median filter as a Plug-and-Play prior): graded on writing the objective and solving it with a PyProximal solver, deriving step sizes from operator norms, the SNR reached, reporting convergence, and not using the true model inside the inversion or to choose its parameters |
| `sns-05`–`sns-06` | Negative cases (plain Tikhonov regularisation, a failing dot-test): the skill should *not* trigger |

### Requirements

Most cases let the agent write and run Python (e.g. a dot-test or the user's
script), so the eval needs:

- **PyLops (with NumPy and SciPy), and PyProximal for the `pyproximal` plugin,
  installed as regular, non-editable packages in the Python that is first on
  `PATH` when you start `claude plugin eval`.**
  The runs are sandboxed and can only read a few locations outside their working
  directory: an editable install (`pip install -e`) of a PyLops checkout
  elsewhere on disk fails inside the sandbox with `No module named 'pylops'`,
  and the sandbox also blocks installing packages from PyPI. If your usual
  environment has an editable install, put another one first on `PATH` for the
  run, e.g. `PATH=/path/to/env/bin:$PATH claude plugin eval ...`, and check it
  with `python -c "import pylops; print(pylops.__file__)"` (the path must be
  inside that environment's `site-packages`).
- `--allow-tools "Write,Bash"`, as in the commands below. Without it, cases
  that expect scripts to be run cannot pass in either arm.

Both apply to every eval suite in this repository. When neither arm runs any code, 
check the traces for `No module named 'pylops'` before reading anything into the scores.

Run the suites from the plugin folder with `claude plugin eval`; more specifically for the `pylops` plugin:

```bash
cd plugins/pylops

# All skills: each case runs 3 times with and without the plugin
claude plugin eval . --ablation with-without --judge-model sonnet --allow-tools "Write,Bash" -j 4

# One skill only (here solve-inverse-problem)
claude plugin eval . --case 'sip-*' --ablation with-without \
  --judge-model sonnet --allow-tools "Write,Bash" -j 4

# Same with a cheaper agent model, pinned to a model version
claude plugin eval . --case 'sip-*' --model claude-haiku-5-5 --ablation with-without \
  --judge-model sonnet --allow-tools "Write,Bash" -j 4

# Quick check: one run each, report kept local
claude plugin eval . --case 'sip-*' --runs 1 --ablation with-without \
  --judge-model sonnet --allow-tools "Write,Bash" --no-publish
```

- `--ablation with-without` also runs a baseline without the plugin and reports
  the score difference, i.e. the uplift the skills provide. A run over all skills
  blends their deltas: run each skill on its own (`--case '<prefix>-*'`) for its
  headline uplift.
- `--case <glob>` filters cases by name; `--runs`, `-j` and the other flags work
  the same with or without it.
- `--judge-model sonnet` uses Sonnet instead of the default Haiku to grade the
  rubrics, which is more reliable for technical answers.
- `--model <model>` sets the model of the agent under test (an alias such as
  `haiku`, `sonnet` or `opus`, or a full model ID such as `claude-haiku-5-5`;
  default: your current model). Weaker models can show a larger uplift
  from the skills; keep the judge different from the agent model. Aliases move
  to newer models over time, so pass the full model ID when the run will be
  recorded, and name the model with its version (e.g. Haiku 5.5) in the
  findings READMEs.
- `--allow-tools "Write,Bash"` lets the agent write and run Python scripts
  (e.g. a dot-test); see [Requirements](#requirements) for the Python environment
  they need.
- `-j 4` runs up to 4 cases at once; they share your account's rate limit.
- `--no-publish` keeps the HTML report local instead of uploading it to claude.ai.

Results (`aggregate-result.json` and `report.html`) are written to
`plugins/<plugin>/evals/results/<timestamp>/`.

The same commands work for the `pyproximal` plugin from `plugins/pyproximal`
(e.g. `--case 'sns-*'`).

Findings from the runs (scores, uplift per model, known grader limitations) are
recorded per skill in [`plugins/pylops/evals/README.md`](plugins/pylops/evals/README.md)
and [`plugins/pyproximal/evals/README.md`](plugins/pyproximal/evals/README.md);
generate their tables as described in [Table Generation](#table-generation).

To plot those tables as one bar chart per skill (mean score per model, with and
without the plugin, in decreasing order), run `python scripts/eval_plot.py`: it
reads the committed READMEs and writes a self-contained `web/index.html`.
Model logos are picked up from `asset/<family>.(svg|png)` (e.g. `opus.svg`,
`haiku.svg`); a coloured initial is drawn when one is missing.

To add a new case, run `claude plugin eval init` from the plugin folder for a guided setup, or `claude plugin eval init --bare <name>` for a blank template, and follow the structure of the existing cases: put the case in `evals/<skill>/` and start its name with the skill's prefix.

### Table Generation

Generate the tables of the findings READMEs from the results rather than
copying numbers by hand, with [`scripts/eval_tables.py`](scripts/eval_tables.py):

```bash
python scripts/eval_tables.py \
  "Opus 5.5=plugins/pylops/evals/results/<timestamp>" \
  "Haiku 5.5=plugins/pylops/evals/results/<timestamp>"
```

- Each argument is one run, `LABEL=FOLDER`: the label is the column name in
  the tables (include the model version), the folder is the results folder that
  `claude plugin eval` wrote for that run (its path is on the `Report:` line at
  the end of the run). Quote each pair, since labels contain spaces.
- Give one pair per model, in column order. All runs must be of the same suite.
- The script only prints: the results table (with, without and Δ per case), the
  cost table (cost, wall time and turns per run), and per model the skill
  trigger rate, negative cases where the skill fired, and grader pass counts on
  fire runs, also split by whether the skill was loaded. It also prints each
  run's `--model` value, to check that labels and folders match.

## Contributing

Contributions are welcome and greatly appreciated!

To add or modify a skill:

- Add/modify a skill as `plugins/<plugin>/skills/<skill-name>/SKILL.md` (`<plugin>` is
`pylops`, `pylops-mpi` or `pyproximal`), with any reference files next to it.
A new plugin also needs its own `plugins/<plugin>/.claude-plugin/plugin.json` and
an entry in `.claude-plugin/marketplace.json`.

- Add new evals and run them (see ``Evals (Claude Code only)`` for more details). This provides evidence that the new skill provides an uplift (or not!)

- Bump `version` in `plugins/<plugin>/.claude-plugin/plugin.json` and check that the skill is picked up:

    ```bash
    npx skills add . --list
    claude plugin validate --strict .
    for p in plugins/*/; do claude plugin validate --strict "$p"; done
    ```

**Note:** keep the instructions agent-agnostic: describe actions (e.g. "fetch the URL", "run the tests") rather than tool names of a specific agent.


## License

LGPL-2.1, see [LICENSE](LICENSE).
