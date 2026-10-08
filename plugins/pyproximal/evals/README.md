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

Both models were run with 3 runs per arm on the current skill. The judge is
Opus 5.5 for the Sonnet 5.5 run and Sonnet 5.5 for the Haiku 4.5 run, so it is
never the agent model. `claude plugin eval` has no effort setting and runs each case with its
own configuration, so agent and judge ran at the models' default effort
(chosen per turn), not at the user's `effortLevel`.

| Case | Sonnet 5.5 with | Sonnet 5.5 without | Sonnet 5.5 Δ | Haiku 4.5 with | Haiku 4.5 without | Haiku 4.5 Δ |
| ---- | ----------- | -------------- | -------- | ---------- | ------------- | ------- |
| `sns-01-box-noisy-l2` | 0.86 | 0.92 | −0.06 | 0.98 | 0.67 | **+0.31** |
| `sns-02-group-sparsity` | 1.00 | 0.74 | **+0.26** | 0.79 | 0.58 | +0.20 |
| `sns-03-lowrank-completion` | 1.00 | 0.90 | +0.10 | 0.94 | 0.32 | **+0.62** |
| `sns-04-pnp-median` | 0.90 | 0.74 | +0.17 | 0.50 | 0.31 | +0.19 |
| `sns-05-neg-tikhonov` | 1.00 | 1.00 | 0.00 | 0.67 | 0.83 | −0.17 |
| `sns-06-neg-dottest` | 1.00 | 1.00 | 0.00 | 1.00 | 1.00 | 0.00 |
| **Mean (all cases)** | | | **+0.08** | | | **+0.19** |
| **Mean (fire cases `sns-01`–`sns-04`)** | | | **+0.12** | | | **+0.33** |

Reports:

- Sonnet 5.5 (`--model sonnet --judge-model opus`, agent `claude-sonnet-5-5`,
  judge Opus 5.5):
  [report](results/2026-09-29T20-31-30-286Z/report.html).
- Haiku 4.5 (`--model haiku --judge-model sonnet`, agent `claude-haiku-4-5-20251001`,
  judge Sonnet 5.5):
  [report](results/2026-09-29T20-10-19-343Z/report.html).

The graders of this suite keep only final answers and scripts, so these two
runs do not store the agent model ID; the versions above are those the
`sonnet` and `haiku` aliases resolved to at the time of the runs.

### Cost and effort

Mean agent cost per run (USD, **excluding the judge**), mean wall time and mean
turns, from the same runs. The Opus 5.5 judge adds about $0.21–0.36 per fire run
and $0.02–0.04 per negative run; the Sonnet 5.5 judge about $0.05–0.20 and
$0.01–0.04.

| Case | Sonnet 5.5 with | Sonnet 5.5 without | Haiku 4.5 with | Haiku 4.5 without |
| ---- | ----------- | -------------- | ---------- | ------------- |
| `sns-01-box-noisy-l2` | $0.45 · 67 s · 6.3 | $0.49 · 92 s · 8.3 | $0.28 · 113 s · 23.7 | $0.12 · 58 s · 4.7 |
| `sns-02-group-sparsity` | $0.46 · 71 s · 7.3 | $0.40 · 55 s · 3.0 | $0.45 · 222 s · 26.0 | $0.38 · 204 s · 21.0 |
| `sns-03-lowrank-completion` | $0.42 · 70 s · 6.7 | $0.44 · 64 s · 5.0 | $0.29 · 163 s · 25.3 | $0.23 · 157 s · 12.7 |
| `sns-04-pnp-median` | $0.33 · 55 s · 6.3 | $0.45 · 86 s · 6.7 | $0.17 · 98 s · 8.0 | $0.15 · 100 s · 6.0 |
| `sns-05-neg-tikhonov` | $0.11 · 21 s · 2.3 | $0.09 · 25 s · 3.3 | $0.08 · 39 s · 2.7 | $0.07 · 28 s · 1.0 |
| `sns-06-neg-dottest` | $0.06 · 11 s · 1.0 | $0.07 · 11 s · 1.0 | $0.05 · 35 s · 1.0 | $0.06 · 50 s · 1.3 |
| **Fire cases, sum per run** | **$1.67** | **$1.79** | **$1.20** | **$0.88** |
| **Whole suite, 3 runs per arm** | **$5.50** | **$5.86** | **$3.98** | **$3.04** |

- For Sonnet 5.5 the plugin costs nothing extra: fire runs cost about the same in
  both arms (slightly less with it on `sns-04`, where the arm without the
  plugin sweeps `tau` against the true model).
- For Haiku 4.5 a fire run with the plugin costs about 35% more, mostly on
  `sns-01` and `sns-03` (more checks, parameter selection and reporting).
- Judge included, the Sonnet 5.5 suite cost about $19.30 and the Haiku 4.5 suite
  about $9.80. The top-level `costUsd` in each `aggregate-result.json` is the
  agent cost of both arms (judge excluded); per-run judge cost is stored as
  `judgeCostUsd`.

### Findings

**Sonnet 5.5 already picks the right formulation; the skill improves how it
chooses parameters and reports.** Without the plugin Sonnet 5.5 writes the right
objective with a PyProximal solver in 10/12 fire runs (the two misses are
`sns-02` runs that solved the joint problem without PyProximal), with it in
12/12. The rest of the Δ comes from the process graders:

| Sonnet 5.5, fire runs | with | without |
| ----------------- | ---- | ------- |
| right objective with a PyProximal solver (`objective-formulation`) | 12/12 | 10/12 |
| reports how the solver stopped (`convergence-reported`) | 12/12 | 3/12 |
| no true model in `invert.py` (`no-truth-leak`) | 12/12 | 9/12 |
| no tuning against the true model reported (`no-truth-leak-answer`) | 12/12 | 6/12 |
| SNR above the threshold (`metric-threshold`) | 7/12 | 12/12 |

- The skill asks for every free parameter (weight, `tau` for ADMM/PnP, rank,
  `niter`) to be chosen by a criterion that does not use the true model. With
  it, Sonnet 5.5 uses the discrepancy principle, held-out observed entries or a
  norm-based `tau`, and never tunes on the truth. Without it, Sonnet 5.5 tunes
  against the true model in 6/12 fire runs (`sns-01` 2/3, `sns-03` 1/3,
  `sns-04` 3/3), in `invert.py` or in exploratory runs it then reports.
- That honesty costs SNR: on `sns-01` the discrepancy principle over-smooths
  the Box + TV solution to 13.0–13.4 dB (vs 19.7–21.0 dB without the plugin)
  and on `sns-04` the PnP result with a norm-based `tau` is 17.6–18.9 dB (vs
  20.8 dB). `metric-threshold` fails in 3/3 and 2/3 of these runs, which is
  why `sns-01` shows Δ −0.06 (see Known limitations).
- `sns-02` (+0.26): without the plugin Sonnet 5.5 did not use PyProximal in 2/3
  runs; with it, it used `pyproximal.L21` in 3/3.
- The skill never fired on the negative cases (0/6).

**Haiku 4.5 benefits clearly from the skill, in the method as well as in the
reporting.** With the plugin the skill fires in 11/12 fire runs, and:

| Haiku 4.5, fire runs | with | without |
| ---------------- | ---- | ------- |
| right objective with a PyProximal solver (`objective-formulation`) | 9/12 | 0/12 |
| reports how the solver stopped (`convergence-reported`) | 8/12 | 5/12 |
| SNR above the threshold (`metric-threshold`) | 10/12 | 8/12 |

- `sns-01` (+0.31): with the skill, `ProximalGradient` + `Box` in 3/3 runs
  (~19.6 dB); without it, scipy `L-BFGS-B` or `lsq_linear` with bounds in 3/3,
  which reach similar SNR but fail `objective-formulation` by design.
- `sns-02` (+0.20): with the skill, one joint `L21` problem in 3/3 runs;
  without it, independent L1 or hand-written support transfer. The weight is
  now the weak point: the SNR threshold passes in only 1/3 runs with the
  skill.
- `sns-03` (+0.62): with the skill, `Nuclear` + `Restriction` in 3/3 runs;
  without it, hand-written SVT, rank-3 hard thresholding or least squares.
  Two runs with the skill still report choosing the weight against the true
  matrix.
- `sns-04` (+0.19): the skill fires in 3/3 runs but Haiku 4.5 still writes its own
  "gradient step + median filter" loop instead of calling `PlugAndPlay` (one
  run tried it with a wrong import path and fell back to its loop), so
  `objective-formulation` fails in 3/3. The loops are correct proximal-gradient
  PnP iterations and pass the SNR threshold in 3/3 runs (1/3 without the skill).
- `sns-05` (−0.17): the skill fired on plain Tikhonov in 1/3 runs; the
  description now states that quadratic regularisation belongs to the `pylops`
  plugin.

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
  formulation and the library used.
- `no-truth-leak-answer` only sees what the answer reports; tuning against the
  truth in exploratory runs that the answer does not mention goes unnoticed.
- `sns-02` uses a DCT basis: PyProximal 0.12.0's `L21` squares complex values
  instead of their magnitudes, so the original FFT-based tutorial setup would
  have tested that bug rather than the skill. The fix is upstream but not
  released yet.
- The judges' reasoning is not stored in `aggregate-result.json` (only the
  votes); use `--keep-temp` to keep the traces for spot checks.
