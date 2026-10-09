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

All three models were run with 3 runs per arm on the current skill. The judge is
Opus 5.5 for the Sonnet 5.5 run and Sonnet 5.5 for the Haiku runs, so it is
never the agent model. `claude plugin eval` has no effort setting and runs each case with its
own configuration, so agent and judge ran at the models' default effort
(chosen per turn), not at the user's `effortLevel`.

| Case | Sonnet 5.5 with | Sonnet 5.5 without | Sonnet 5.5 Δ | Haiku 4.5 with | Haiku 4.5 without | Haiku 4.5 Δ | Haiku 5.5 with | Haiku 5.5 without | Haiku 5.5 Δ |
| ---- | --------------- | ------------------ | ------------ | -------------- | ----------------- | ----------- | -------------- | ----------------- | ----------- |
| `sns-01-box-noisy-l2` | 0.86 | 0.79 | +0.07 | 1.00 | 0.64 | **+0.36** | 0.65 | 0.50 | +0.15 |
| `sns-02-group-sparsity` | 1.00 | 0.74 | **+0.26** | 0.74 | 0.49 | +0.25 | 0.67 | 0.62 | +0.05 |
| `sns-03-lowrank-completion` | 1.00 | 0.93 | +0.07 | 0.95 | 0.50 | **+0.45** | 1.00 | 0.60 | **+0.40** |
| `sns-04-pnp-median` | 0.95 | 0.69 | **+0.26** | 0.77 | 0.26 | **+0.51** | 0.90 | 0.33 | **+0.57** |
| `sns-05-neg-tikhonov` | 1.00 | 1.00 | 0.00 | 0.83 | 0.83 | 0.00 | 1.00 | 1.00 | 0.00 |
| `sns-06-neg-dottest` | 1.00 | 1.00 | 0.00 | 1.00 | 1.00 | 0.00 | 1.00 | 1.00 | 0.00 |
| **Mean (all cases)** | | | **+0.11** | | | **+0.26** | | | **+0.20** |
| **Mean (fire cases `sns-01`–`sns-04`)** | | | **+0.17** | | | **+0.39** | | | **+0.29** |

| Fire runs | Sonnet 5.5 with | Sonnet 5.5 without | Haiku 4.5 with | Haiku 4.5 without | Haiku 5.5 with | Haiku 5.5 without |
| --------- | --------------- | ------------------ | -------------- | ----------------- | -------------- | ----------------- |
| skill called (`trigger`) | 12/12 | – | 12/12 | – | 7/12 | – |
| right objective with a PyProximal solver (`objective-formulation`) | 12/12 | 10/12 | 8/12 | 0/12 | 7/12 | 2/12 |
| step sizes from operator norms (`step-size-from-norm`) | 12/12 | 9/12 | 12/12 | 7/12 | 12/12 | 6/12 |
| reports how the solver stopped (`convergence-reported`) | 12/12 | 2/12 | 10/12 | 1/12 | 8/12 | 2/12 |
| no true model in `invert.py` (`no-truth-leak`) | 12/12 | 9/12 | 12/12 | 10/12 | 12/12 | 12/12 |
| no tuning against the true model reported (`no-truth-leak-answer`) | 12/12 | 7/12 | 11/12 | 11/12 | 11/12 | 8/12 |
| SNR above the threshold (`metric-threshold`) | 8/12 | 11/12 | 10/12 | 8/12 | 8/12 | 9/12 |
| mean score | 0.95 | 0.79 | 0.87 | 0.47 | 0.81 | 0.51 |

`solve-nonsmooth-problem` never fired on the negative cases (0/18 runs with the
plugin across the three models).

Reports:

- Sonnet 5.5 (`--model claude-sonnet-5-5 --judge-model opus`, agent
  `claude-sonnet-5-5`, judge Opus 5.5):
  [report](results/2026-10-09T09-29-28-985Z/report.html).
- Haiku 4.5 (`--model claude-haiku-4-5-20251001 --judge-model sonnet`, agent
  `claude-haiku-4-5-20251001`, judge Sonnet 5.5):
  [report](results/2026-10-09T09-29-43-860Z/report.html).
- Haiku 5.5 (`--model claude-haiku-5-5 --judge-model sonnet`, agent
  `claude-haiku-5-5`, judge Sonnet 5.5):
  [report](results/2026-10-09T09-29-58-852Z/report.html).

### Cost and effort

Mean agent cost per run (USD, **excluding the judge**), mean wall time and mean
turns, from the same runs. The Opus 5.5 judge adds about $0.10–0.33 per fire run
and $0.01–0.04 per negative run; the Sonnet 5.5 judge about $0.03–0.13 and
$0.01–0.04.

| Case | Sonnet 5.5 with | Sonnet 5.5 without | Haiku 4.5 with | Haiku 4.5 without | Haiku 5.5 with | Haiku 5.5 without |
| ---- | --------------- | ------------------ | -------------- | ----------------- | -------------- | ----------------- |
| `sns-01-box-noisy-l2` | $0.43 · 71 s · 6.7 | $0.36 · 138 s · 9.3 | $0.28 · 129 s · 20.0 | $0.12 · 67 s · 3.0 | $0.07 · 84 s · 10.0 | $0.07 · 52 s · 6.7 |
| `sns-02-group-sparsity` | $0.32 · 74 s · 6.3 | $0.37 · 55 s · 3.0 | $0.45 · 240 s · 39.0 | $0.27 · 171 s · 19.7 | $0.08 · 70 s · 7.0 | $0.13 · 110 s · 8.3 |
| `sns-03-lowrank-completion` | $0.36 · 56 s · 6.3 | $0.32 · 59 s · 4.3 | $0.25 · 160 s · 21.0 | $0.22 · 154 s · 17.3 | $0.11 · 81 s · 12.0 | $0.10 · 105 s · 11.7 |
| `sns-04-pnp-median` | $0.30 · 61 s · 8.3 | $0.30 · 92 s · 8.3 | $0.23 · 135 s · 19.3 | $0.17 · 564 s · 3.3 | $0.09 · 82 s · 14.3 | $0.09 · 61 s · 9.3 |
| `sns-05-neg-tikhonov` | $0.10 · 24 s · 3.3 | $0.09 · 21 s · 2.0 | $0.06 · 34 s · 1.7 | $0.06 · 33 s · 1.7 | $0.02 · 28 s · 4.0 | $0.02 · 23 s · 1.0 |
| `sns-06-neg-dottest` | $0.07 · 12 s · 1.0 | $0.06 · 10 s · 1.0 | $0.04 · 28 s · 1.0 | $0.05 · 31 s · 1.0 | $0.02 · 16 s · 1.7 | $0.01 · 14 s · 1.0 |
| **Fire cases, sum per run** | **$1.40** | **$1.35** | **$1.21** | **$0.77** | **$0.36** | **$0.38** |
| **Whole suite, 3 runs per arm** | **$4.72** | **$4.50** | **$3.94** | **$2.60** | **$1.20** | **$1.25** |

- For Sonnet 5.5 and Haiku 5.5 the plugin costs nothing extra: fire runs cost
  about the same in both arms.
- For Haiku 4.5 a fire run with the plugin costs about 55% more, mostly on
  `sns-01` and `sns-02` (more checks, parameter selection and reporting, and
  two `sns-02` runs that hit the 40-turn limit).
- Judge included, the Sonnet 5.5 suite cost about $15.00, the Haiku 4.5 suite
  about $8.40 and the Haiku 5.5 suite about $4.60. The top-level `costUsd` in
  each `aggregate-result.json` is the agent cost of both arms (judge excluded);
  per-run judge cost is stored as `judgeCostUsd`.

### Findings

**The description says when to load the skill.** It asks to load it "before
writing the objective, choosing proximal operators or a solver, or writing
optimisation code, even when the formulation seems obvious", as for the
`pylops` skills, whose descriptive wording Haiku 5.5 often skipped. Sonnet 5.5
and Haiku 4.5 load it in every fire run, and no model fires it on the negative
cases. Haiku 5.5 still skips it when the problem looks solvable without
PyProximal (see below).

**Sonnet 5.5 already picks the right formulation; the skill improves how it
chooses parameters and reports.** Without the plugin Sonnet 5.5 writes the
right objective with a PyProximal solver in 10/12 fire runs (the two misses are
`sns-02` runs that solved the joint problem without a PyProximal solver), with
it in 12/12. The rest of the Δ comes from the process graders (table above):
convergence reported in 12/12 vs 2/12 runs, step sizes from operator norms in
12/12 vs 9/12, and no tuning against the true model.

- The skill asks for every free parameter (weight, `tau` for ADMM/PnP, rank,
  `niter`) to be chosen by a criterion that does not use the true model. With
  it, Sonnet 5.5 uses the discrepancy principle, held-out observed entries or a
  norm-based `tau`, and never tunes on the truth. Without it, Sonnet 5.5 tunes
  against the true model in `invert.py` in 3/3 runs of `sns-01` and reports
  tuning on the truth in 2/3 runs of `sns-04`.
- That honesty costs SNR on `sns-01`: the discrepancy principle over-smooths
  the Box + TV solution to 13.0–13.4 dB (vs 20.5–21.0 dB without the plugin),
  so `metric-threshold` fails in 3/3 runs with the plugin (see Known
  limitations).
- `sns-02` and `sns-04` (+0.26 each): with the plugin `pyproximal.L21` in 3/3
  runs of `sns-02` and `PlugAndPlay` in 3/3 runs of `sns-04`, with
  norm-based step sizes and reported convergence.

**Haiku 4.5 benefits clearly from the skill, in the method as well as in the
reporting.** The skill fires in 12/12 fire runs; the right objective with a
PyProximal solver rises from 0/12 to 8/12 runs:

- `sns-01` (+0.36): with the skill, `ProximalGradient` + `Box` in 3/3 runs
  (every run 1.00); without it, scipy `L-BFGS-B` or a bounded solver
  in 3/3, which reach similar SNR but fail `objective-formulation` by design.
- `sns-02` (+0.25): one run with the skill solved the joint `L21` problem
  (15.4 dB, score 1.00); two ran out of turns (40) before finishing. Without
  the skill, no run used a joint PyProximal formulation.
- `sns-03` (+0.45): with the skill, `Nuclear` + `Restriction` in 3/3 runs
  (14.6–21.0 dB); without it, hand-written iterations or L-BFGS-B, one of them
  tuned against the true matrix.
- `sns-04` (+0.51): with the skill, `PlugAndPlay` in 1/3 runs (1.00), a
  hand-written PnP loop in 1/3 and the 40-turn limit in 1/3; without it, scipy
  or hand-written loops that miss the threshold in 2/3 runs.
- `sns-05`: the skill did not fire on plain Tikhonov (0/3); one answer per arm
  fails the rubric.

**Haiku 5.5 benefits from the skill when it loads it, but skips it on half
the cases.** It loads the skill in 3/3 runs of `sns-03` and `sns-04` and
scores 1.00 / 0.90 there, against 0.60 / 0.33 without the plugin. On `sns-01`
(1/3) and `sns-02` (0/3) it skips it and solves the problem without a
PyProximal solver, exactly as without the plugin:

| Haiku 5.5, fire runs | skill loaded (7) | skill not loaded (5) | no plugin (12) |
| -------------------- | ---------------- | -------------------- | -------------- |
| mean score | **0.94** | 0.62 | 0.51 |
| right objective with a PyProximal solver | 7/7 | 0/5 | 2/12 |
| reports how the solver stopped | 7/7 | 1/5 | 2/12 |

- `sns-01` asks for a model "within [0, 1]": when it skips the skill, Haiku 5.5
  uses scipy `lsq_linear` with bounds (13.0–20.0 dB). The one run that loaded
  it used `PrimalDual` with `Box` + TV (13.6 dB, below the threshold).
- `sns-02` asks to "reconstruct both full signals": Haiku 5.5 solves it
  without a PyProximal solver (e.g. its own FISTA/L21 iterations) in 3/3 runs
  with and without the plugin, which fails `objective-formulation` by design.
- `sns-03`: with the skill `Nuclear` + `ProximalGradient` with a norm-based
  step in 3/3 runs (20.4–20.7 dB); without it mostly the same formulation,
  but with hard-coded step sizes in 3/3.
- `sns-04`: with the skill `PlugAndPlay` + ADMM in 3/3 runs (17.3–20.2 dB);
  without it a hand-written ADMM loop in 3/3, two of them tuned against the
  truth.

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
