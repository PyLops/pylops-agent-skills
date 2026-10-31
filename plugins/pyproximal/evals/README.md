# Eval findings for the `pyproximal` plugin

This file records what the eval suites in this folder showed when they were
run: scores with and without the plugin, the uplift (Δ = with − without) per
agent model, and known limitations of the graders. How to run the suites is
described in the repository [README](../../../README.md#evals-claude-code-only).

Each run's HTML report is linked below (`results/<timestamp>/report.html`,
next to its `aggregate-result.json`). Scores are on a 0–1 scale; a case passes
only with a score of 1.

Models are named with their version (e.g. Haiku 4.5, Haiku 5.5), because
aliases such as `haiku` move to newer models over time and the suites are
compared across models. The agent model ID of each run is listed next to its
report. When adding a run, pass the full model ID to `--model` (e.g.
`--model claude-haiku-5-5`) and label its columns with that version.

## `solve-nonsmooth-problem` (`sns-*`)

### What the suite tests

| Case | Input | Trap for the naive approach | Right approach |
| ---- | ----- | --------------------------- | -------------- |
| `sns-01-box-noisy-l2` | prose | 1-D blocky model in [0, 1] under a Gaussian blur with 5% noise: unconstrained `lsqr` + clipping tops out at ~12 dB | box constraint inside the solve, e.g. `ProximalGradient` + `Box(0, 1)`: ~20 dB |
| `sns-02-group-sparsity` | pasted code | two sensors sharing the same 6 DCT components, sensor 1 with 8% of its samples: L1 on sensor 1 alone gives ~0.4 dB | joint group sparsity across sensors (`L21` over the stacked DCT coefficients): ~22 dB |
| `sns-03-lowrank-completion` | pasted code | 60×60 rank-3 matrix with 30% noisy entries: zero-fill or least squares give ~1.5 dB | nuclear norm with a `Restriction` (`ProximalGradient` + `Nuclear`): 17–20 dB |
| `sns-04-pnp-median` | pasted code | 64×64 blocky image under a 2-D blur, user asks for a 3×3 median filter as the prior: `lsqr` + median post-filter reaches ~17 dB even with the damping tuned on the truth | Plug-and-Play (`PlugAndPlay` with ADMM or `ProximalGradient`) with the median filter as denoiser: 19–20 dB |
| `sns-05-neg-tikhonov` | pasted code | second-derivative Tikhonov regularisation, belongs to `pylops` `solve-inverse-problem` / `regularized_inversion` | `solve-nonsmooth-problem` must not fire |
| `sns-06-neg-dottest` | pasted code | custom `LinearOperator` whose adjoint has the wrong sign, a debugging question | `solve-nonsmooth-problem` must not fire |

The dB values in the table were measured when the cases were designed, with
PyProximal 0.12.0 and PyLops 2.8.0; the "right approach" values use a
regularisation weight picked by sweeping against the true model, so they are
an upper bound for a truth-free choice (see Known limitations).

Each fire case asks for a script `invert.py` that is run and prints
`SNR_DB=<value>` (model vs true model). Graders per fire case:

| Grader | Type | Weight | Checks |
| ------ | ---- | ------ | ------ |
| `objective-formulation` | LLM, final answer | 1 | the objective is written explicitly, it is the right one for the case (box inside the solve, joint group penalty, low-rank prior, PnP with the median filter), and the final model comes from a PyProximal solver; scipy, cvxpy, PyLops-only solvers or hand-written loops fail even with the right formulation (`sns-02` allows a least-squares debiasing on the support found by the PyProximal solve) |
| `step-size-from-norm` | LLM, `invert.py` | 1 | step sizes derived from a computed or stated operator norm (or backtracking); for ADMM/PnP, `tau` chosen by a stated rule or sweep; a bare hard-coded number fails |
| `script-written-and-run` | regex on the trace | 0.5 | `invert.py` was run and printed `SNR_DB=` |
| `metric-threshold` | regex on the trace | 0.5 | a printed `SNR_DB=` above the case threshold (16 / 15 / 15 / 18.5 dB) |
| `convergence-reported` | LLM, final answer | 0.25 | how the solver stopped (iterations used, cost trend or relative change) |
| `no-truth-leak` | LLM, `invert.py` | 0.125 | the true model (and, for `sns-02`/`sns-03`, the true support, number of components or rank read off the setup code) does not flow into the solve or into choosing its parameters |
| `no-truth-leak-answer` | LLM, final answer | 0.125 | the answer does not report choosing a parameter by comparing against the true model (catches tuning done in exploratory runs outside `invert.py`) |

The negative cases check that the skill is not called (`tool_used`, max 0) and
grade the answer to the actual request (`regularized_inversion` with a
second-derivative operator and a principled weight choice; the sign-flipped
adjoint and its fix).

### Results

All four models were run with 3 runs per arm on the current skill. The judge is
Opus 5.5 for the Sonnet 5.5 run and Sonnet 5.5 for the Opus 5.5 and Haiku runs,
so it is never the agent model. `claude plugin eval` has no effort setting and runs each case with its
own configuration, so agent and judge ran at the models' default effort
(chosen per turn), not at the user's `effortLevel`.

| Case | Opus 5.5 with | Opus 5.5 without | Opus 5.5 Δ | Sonnet 5.5 with | Sonnet 5.5 without | Sonnet 5.5 Δ | Haiku 4.5 with | Haiku 4.5 without | Haiku 4.5 Δ | Haiku 5.5 with | Haiku 5.5 without | Haiku 5.5 Δ |
| ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| `sns-01-box-noisy-l2` | 0.98 | 0.96 | +0.01 | 0.86 | 0.90 | −0.05 | 1.00 | 0.67 | +0.33 | 0.86 | 0.52 | +0.33 |
| `sns-02-group-sparsity` | 1.00 | 0.93 | +0.07 | 1.00 | 0.74 | +0.26 | 0.69 | 0.36 | +0.33 | 0.76 | 0.63 | +0.13 |
| `sns-03-lowrank-completion` | 0.90 | 0.70 | +0.20 | 1.00 | 0.92 | +0.08 | 0.83 | 0.52 | +0.31 | 1.00 | 0.45 | +0.55 |
| `sns-04-pnp-median` | 1.00 | 0.83 | +0.17 | 0.94 | 0.69 | +0.25 | 0.81 | 0.24 | +0.57 | 0.90 | 0.35 | +0.56 |
| `sns-05-neg-tikhonov` | 1.00 | 1.00 | 0.00 | 1.00 | 1.00 | 0.00 | 0.67 | 0.83 | −0.17 | 1.00 | 1.00 | 0.00 |
| `sns-06-neg-dottest` | 1.00 | 1.00 | 0.00 | 1.00 | 1.00 | 0.00 | 1.00 | 1.00 | 0.00 | 1.00 | 1.00 | 0.00 |
| **Mean (all cases)** | | | **+0.08** | | | **+0.09** | | | **+0.23** | | | **+0.26** |
| **Mean (fire cases `sns-01`–`sns-04`)** | | | **+0.11** | | | **+0.14** | | | **+0.39** | | | **+0.39** |

| Fire runs | Opus 5.5 with | Opus 5.5 without | Sonnet 5.5 with | Sonnet 5.5 without | Haiku 4.5 with | Haiku 4.5 without | Haiku 5.5 with | Haiku 5.5 without |
| --------- | ------------- | ---------------- | --------------- | ------------------ | -------------- | ----------------- | -------------- | ----------------- |
| skill called (`trigger`) | 12/12 | – | 12/12 | – | 12/12 | – | 10/12 | – |
| right objective with a PyProximal solver (`objective-formulation`) | 11/12 | 9/12 | 12/12 | 10/12 | 9/12 | 1/12 | 10/12 | 0/12 |
| step sizes from operator norms (`step-size-from-norm`) | 12/12 | 12/12 | 12/12 | 10/12 | 10/12 | 5/12 | 12/12 | 7/12 |
| reports how the solver stopped (`convergence-reported`) | 12/12 | 5/12 | 12/12 | 2/12 | 10/12 | 3/12 | 10/12 | 0/12 |
| no true model in `invert.py` (`no-truth-leak`) | 12/12 | 9/12 | 12/12 | 8/12 | 12/12 | 10/12 | 12/12 | 10/12 |
| no tuning against the true model reported (`no-truth-leak-answer`) | 10/12 | 5/12 | 11/12 | 5/12 | 12/12 | 10/12 | 12/12 | 10/12 |
| SNR above the threshold (`metric-threshold`) | 12/12 | 12/12 | 8/12 | 12/12 | 9/12 | 7/12 | 7/12 | 10/12 |
| mean score | 0.97 | 0.86 | 0.95 | 0.81 | 0.83 | 0.45 | 0.88 | 0.49 |

`solve-nonsmooth-problem` never fired on the negative cases (0/24 runs with the
plugin across the four models).

Reports:

- Opus 5.5 (`--model claude-opus-5-5 --judge-model sonnet`, agent
  `claude-opus-5-5`, judge Sonnet 5.5):
  [report](results/2026-10-31T15-24-56-026Z/report.html).
- Sonnet 5.5 (`--model claude-sonnet-5-5 --judge-model opus`, agent
  `claude-sonnet-5-5`, judge Opus 5.5):
  [report](results/2026-10-09T11-20-39-660Z/report.html).
- Haiku 4.5 (`--model claude-haiku-4-5-20251001 --judge-model sonnet`, agent
  `claude-haiku-4-5-20251001`, judge Sonnet 5.5):
  [report](results/2026-10-09T11-20-54-524Z/report.html).
- Haiku 5.5 (`--model claude-haiku-5-5 --judge-model sonnet`, agent
  `claude-haiku-5-5`, judge Sonnet 5.5):
  [report](results/2026-10-09T11-21-09-796Z/report.html).

### Cost and effort

Mean agent cost per run (USD, **excluding the judge**), mean wall time and mean
turns, from the same runs. The Sonnet 5.5 judge adds about $0.06–0.23 per fire
run and $0.01–0.03 per negative run for the Opus 5.5 agent run; the Opus 5.5 judge adds about $0.18–0.36 per fire run
and $0.01–0.07 per negative run; the Sonnet 5.5 judge about $0.04–0.14 and
$0.00–0.04.

| Case | Opus 5.5 with | Opus 5.5 without | Sonnet 5.5 with | Sonnet 5.5 without | Haiku 4.5 with | Haiku 4.5 without | Haiku 5.5 with | Haiku 5.5 without |
| ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| `sns-01-box-noisy-l2` | $0.59 · 169 s · 10.3 | $0.43 · 135 s · 8.7 | $0.46 · 101 s · 6.0 | $0.37 · 156 s · 10.0 | $0.25 · 104 s · 17.0 | $0.12 · 64 s · 3.0 | $0.11 · 79 s · 10.0 | $0.06 · 69 s · 7.7 |
| `sns-02-group-sparsity` | $0.50 · 132 s · 8.3 | $0.37 · 90 s · 5.0 | $0.38 · 66 s · 5.3 | $0.36 · 59 s · 3.7 | $0.34 · 193 s · 27.3 | $0.32 · 221 s · 25.0 | $0.11 · 85 s · 7.3 | $0.09 · 74 s · 8.3 |
| `sns-03-lowrank-completion` | $0.64 · 174 s · 15.0 | $0.40 · 126 s · 9.0 | $0.38 · 71 s · 7.3 | $0.35 · 65 s · 5.0 | $0.28 · 192 s · 22.0 | $0.19 · 122 s · 12.3 | $0.07 · 121 s · 12.0 | $0.10 · 106 s · 12.7 |
| `sns-04-pnp-median` | $0.43 · 118 s · 8.7 | $0.37 · 125 s · 8.3 | $0.41 · 60 s · 7.7 | $0.32 · 105 s · 7.3 | $0.24 · 119 s · 10.3 | $0.18 · 113 s · 7.0 | $0.09 · 104 s · 20.0 | $0.10 · 62 s · 9.7 |
| `sns-05-neg-tikhonov` | $0.18 · 39 s · 3.0 | $0.15 · 31 s · 2.3 | $0.11 · 21 s · 2.0 | $0.12 · 26 s · 2.3 | $0.06 · 30 s · 1.3 | $0.05 · 28 s · 1.7 | $0.02 · 22 s · 3.3 | $0.02 · 21 s · 1.0 |
| `sns-06-neg-dottest` | $0.12 · 20 s · 1.7 | $0.11 · 18 s · 1.0 | $0.07 · 15 s · 1.0 | $0.06 · 12 s · 1.0 | $0.06 · 34 s · 2.3 | $0.05 · 36 s · 1.0 | $0.01 · 16 s · 1.7 | $0.01 · 13 s · 1.0 |
| **Fire cases, sum per run** | **$2.15** | **$1.57** | **$1.64** | **$1.40** | **$1.10** | **$0.81** | **$0.38** | **$0.35** |
| **Whole suite, all runs per arm** | **$7.33** | **$5.51** | **$5.45** | **$4.75** | **$3.66** | **$2.74** | **$1.24** | **$1.17** |

- With the plugin a fire run costs about 37% more for Opus 5.5, 17% more for Sonnet 5.5, 35% more for
  Haiku 4.5 (more checks, parameter selection and reporting) and about the same
  for Haiku 5.5.
- Judge included, the Opus 5.5 suite cost about $16.40, the Sonnet 5.5 suite about $16.90, the Haiku 4.5 suite
  about $8.50 and the Haiku 5.5 suite about $4.50. The top-level `costUsd` in
  each `aggregate-result.json` is the agent cost of both arms (judge excluded);
  per-run judge cost is stored as `judgeCostUsd`.

### Findings

**Opus 5.5 is already strong without the plugin; the skill adds reporting and
the right library.** It loads the skill in 12/12 fire runs and never on the
negative cases. Fire-case mean 0.97 with the plugin vs 0.86 without (Δ +0.11).
Without the plugin it already hits the SNR threshold (12/12) and derives step
sizes from operator norms (12/12), so the Δ comes from the other graders:
convergence reported in 12/12 vs 5/12 runs, a PyProximal objective in 11/12 vs
9/12, and no tuning against the true model reported (`no-truth-leak-answer`)
in 10/12 vs 5/12.

- `sns-03` (+0.20) and `sns-04` (+0.17) show the largest uplift; the only
  `objective-formulation` miss with the plugin is in `sns-03` (failed by all
  three judge votes).
- `sns-01` (+0.01) and `sns-02` (+0.07) are close to saturated in both arms.

**The description says when to load the skill, and covers the cases where
another tool would also work.** It asks to load the skill "before writing the
objective, choosing a solver or writing optimisation code, even when a SciPy
bounded solver or a hand-written FISTA/ADMM loop would also work", and its
examples include "keep the model within physical bounds" and "recover several
signals that share their components". Haiku 5.5 decides in its first turn
whether to load a skill and skipped this one whenever SciPy or its own loop
could solve the problem: with a purely descriptive wording it loaded it in
4/12 fire runs, with the current one in 10/12. Sonnet 5.5 and Haiku 4.5 load
it in every fire run, and no model fires it on the negative cases.

**Sonnet 5.5 already picks the right formulation; the skill improves how it
chooses parameters and reports.** Without the plugin Sonnet 5.5 writes the
right objective with a PyProximal solver in 10/12 fire runs (the two misses are
`sns-02` runs that solved the joint problem without a PyProximal solver), with
it in 12/12. The rest of the Δ comes from the process graders (table above):
convergence reported in 12/12 vs 2/12 runs and no tuning against the true model
(`no-truth-leak` 12/12 vs 8/12).

- The skill asks for every free parameter (weight, `tau` for ADMM/PnP, rank,
  `niter`) to be chosen by a criterion that does not use the true model. With
  it, Sonnet 5.5 never uses the truth (e.g. the discrepancy principle on
  `sns-01`, `sns-02` and `sns-04`). Without it, Sonnet 5.5 tunes against the true model in
  `invert.py` in 3/3 runs of `sns-01` and reports tuning on the truth in 3/3
  runs of `sns-04`.
- That honesty costs SNR on `sns-01`: the discrepancy principle over-smooths
  the Box + TV solution to 13.0–13.2 dB (vs 20.5–21.4 dB without the plugin),
  so `metric-threshold` fails in 3/3 runs with the plugin and the case shows
  Δ −0.05 (see Known limitations).
- `sns-02` (+0.26): `pyproximal.L21` with the discrepancy principle in 3/3 runs
  with the plugin (19.2–20.3 dB); without it, a PyProximal solver in only 1/3.
- `sns-04` (+0.25): `PlugAndPlay` in 3/3 runs with the plugin; without it,
  `PlugAndPlay` with a hard-coded step in 2/3 runs and tuning on the truth
  reported in 3/3.

**Haiku 4.5 benefits clearly from the skill, in the method as well as in the
reporting.** The skill fires in 12/12 fire runs; the right objective with a
PyProximal solver rises from 1/12 to 9/12 runs:

- `sns-01` (+0.33): with the skill, `ProximalGradient` + `Box` in 3/3 runs
  (19.6–20.0 dB, every run 1.00); without it, no PyProximal solver in 3/3
  (e.g. SciPy `L-BFGS-B` with bounds), at similar SNR but failing
  `objective-formulation` by design.
- `sns-02` (+0.33): with the skill, a PyProximal `ProximalGradient` solve with
  the discrepancy principle in 2/3 runs, but at 6.1–6.3 dB, below the
  threshold; the third run ran out of turns (40). Without it, no PyProximal
  solver in 3/3.
- `sns-03` (+0.31): with the skill, `Nuclear` + `ProximalGradient` in 3/3 runs
  (8.4–20.3 dB where reported); without it, a PyProximal solver in 1/3 runs and
  hand-written or SciPy iterations in 2/3, both tuned against the true matrix.
- `sns-04` (+0.57): with the skill, `PlugAndPlay` + ADMM in 1/3 runs (1.00) and
  no PyProximal solver in 2/3; without it, SciPy or hand-written iterations
  below the threshold in 3/3.
- `sns-05` (−0.17): the skill did not fire on plain Tikhonov (0/3); the answer
  fails the rubric in 2/3 runs with the plugin and 1/3 without.

**Haiku 5.5 benefits as much as Haiku 4.5.** Runs that load the skill score
0.93, the two runs with the plugin that skip it 0.64, and runs without the
plugin 0.49; with the skill it uses a PyProximal solver in 10/10 runs, without
the plugin in 0/12:

- `sns-01` (+0.33): with the skill, `PrimalDual` with `Box` and the
  discrepancy principle in 3/3 runs (13.3–13.5 dB, below the threshold, as for
  Sonnet 5.5); without it, SciPy `lsq_linear` with bounds in 3/3.
- `sns-02` (+0.13): the skill fired in 1/3 runs, which solved the joint `L21`
  problem with `ProximalGradient` (22.1 dB, score 1.00); the other two solved
  it without a PyProximal solver, like every run without the plugin.
- `sns-03` (+0.55): with the skill, `Nuclear` + `ProximalGradient` with a
  norm-based step in 3/3 runs (20.6 dB, every run 1.00); without it,
  `objective-formulation` fails in 3/3 and step sizes are hard-coded in 2/3.
- `sns-04` (+0.56): with the skill, `PlugAndPlay` + ADMM in 3/3 runs
  (17.6–20.4 dB); without it, a hand-written ADMM loop in 3/3.

Parts of the skill that matter for Haiku 4.5 (each fixes a failure seen with an
earlier version of the skill):

- Trigger phrases in the description for joint sparsity, matrix completion and
  denoiser priors: without them the skill did not fire on `sns-03` (0/3) and
  fired only in 2/3 runs of `sns-04`.
- The "not for purely quadratic regularisation" sentence in the description:
  without it the skill fired on `sns-05` in 3/3 runs.
- Solver-table rows for joint sparsity (`L21` over stacked signals) and low
  rank (`Restriction` + `Nuclear`): without them Haiku 4.5 solved `sns-02` one
  signal at a time and ran out of turns in 3/3 runs.
- "Use the PyProximal solver, not a hand-written loop; go back to the table
  after one or two failed attempts".
- Asking for the truth-free criterion used to choose each parameter and for
  convergence as iterations used plus start/end cost.

### Known limitations of the graders

- The runs need PyLops **and PyProximal** as regular (non-editable) installs
  first on `PATH`; see the repository README.
- `metric-threshold` and the truth-leak graders pull in opposite directions:
  the thresholds were set from calibration runs whose weights were picked by
  sweeping against the true model, so a correct truth-free choice (e.g. the
  discrepancy principle on `sns-01`) can fall below them. A run can therefore
  lose 0.5 for tuning honestly or 0.25 for tuning on the truth. The thresholds
  are still well above every naive approach.
- `objective-formulation` fails correct non-PyProximal solutions on purpose
  (scipy bounded solvers, hand-written FISTA/SVT/ADMM/PnP loops), since the plugin is
  about PyProximal; a score without the plugin therefore reflects both the
  formulation and the library used. For Haiku 5.5 this also means that runs
  that skip the skill score like runs without the plugin.
- `no-truth-leak-answer` only sees what the answer reports; tuning against the
  truth in exploratory runs that the answer does not mention goes unnoticed.
- `sns-02` uses a DCT basis: PyProximal 0.12.0's `L21` squares complex values
  instead of their magnitudes, so the original FFT-based tutorial setup would
  have tested that bug rather than the skill. The fix is upstream but not
  released yet.
- The graders of this suite keep only final answers and scripts, not traces,
  so the first-turn decision to skip the skill cannot be inspected; use
  `--keep-temp` to keep the traces for spot checks.
- The judges' reasoning is not stored in `aggregate-result.json` (only the
  votes).
