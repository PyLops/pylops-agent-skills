# Eval findings for the `pyproximal` plugin

This file records what the eval suites in this folder showed when they were
run: scores with and without the plugin, the uplift (Δ = with − without) per
agent model, and known limitations of the graders. How to run the suites is
described in the repository [README](../../../README.md#evals-claude-code-only).

Each run's HTML report is linked below (`results/<timestamp>/report.html`,
next to its `aggregate-result.json`). Scores are on a 0–1 scale; a case passes
only with a score of 1.

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

Both models were run with 3 runs per arm. The judge is Opus for the Sonnet
run and Sonnet for the Haiku run, so it is never the agent model.

| Case | Sonnet with | Sonnet without | Sonnet Δ | Haiku with | Haiku without | Haiku Δ |
| ---- | ----------- | -------------- | -------- | ---------- | ------------- | ------- |
| `sns-01-box-noisy-l2` | 0.86 | 0.83 | +0.02 | 0.83 | 0.60 | +0.24 |
| `sns-02-group-sparsity` | 0.99 | 0.74 | **+0.25** | 0.49 | 0.50 | −0.01 |
| `sns-03-lowrank-completion` | 1.00 | 0.92 | +0.08 | 0.61 | 0.36 | +0.25 |
| `sns-04-pnp-median` | 0.83 | 0.61 | **+0.23** | 0.40 | 0.31 | +0.10 |
| `sns-05-neg-tikhonov` | 1.00 | 1.00 | 0.00 | 0.17 | 0.83 | **−0.67** |
| `sns-06-neg-dottest` | 1.00 | 1.00 | 0.00 | 1.00 | 1.00 | 0.00 |
| **Mean (all cases)** | | | **+0.10** | | | **−0.02** |
| **Mean (fire cases `sns-01`–`sns-04`)** | | | **+0.15** | | | **+0.14** |

Reports:

- Sonnet (`--model sonnet --judge-model opus`):
  [report](results/2026-09-28T20-10-23-616Z/report.html).
- Haiku (`--model haiku --judge-model sonnet`):
  [report](results/2026-09-28T20-10-23-875Z/report.html).

### Cost and effort

Mean agent cost per run (USD, **excluding the judge**), mean wall time and mean
turns, from the same runs. The Opus judge adds about $0.22–0.35 per fire run
and $0.03–0.05 per negative run; the Sonnet judge about $0.06–0.11 and
$0.01–0.02.

| Case | Sonnet with | Sonnet without | Haiku with | Haiku without |
| ---- | ----------- | -------------- | ---------- | ------------- |
| `sns-01-box-noisy-l2` | $0.38 · 68 s · 6.3 | $0.52 · 153 s · 11.3 | $0.28 · 141 s · 23.3 | $0.12 · 72 s · 3.7 |
| `sns-02-group-sparsity` | $0.44 · 72 s · 6.3 | $0.41 · 54 s · 3.0 | $0.44 · 289 s · 41.0 | $0.23 · 129 s · 9.3 |
| `sns-03-lowrank-completion` | $0.33 · 57 s · 6.3 | $0.33 · 60 s · 6.7 | $0.21 · 116 s · 10.3 | $0.20 · 109 s · 6.7 |
| `sns-04-pnp-median` | $0.39 · 58 s · 9.0 | $0.33 · 78 s · 7.7 | $0.22 · 132 s · 16.3 | $0.16 · 98 s · 10.0 |
| `sns-05-neg-tikhonov` | $0.10 · 21 s · 2.3 | $0.12 · 22 s · 4.0 | $0.19 · 305 s · 15.3 | $0.06 · 31 s · 2.3 |
| `sns-06-neg-dottest` | $0.09 · 14 s · 1.0 | $0.07 · 10 s · 1.0 | $0.06 · 49 s · 2.7 | $0.06 · 37 s · 2.7 |
| **Fire cases, sum per run** | **$1.54** | **$1.59** | **$1.14** | **$0.71** |
| **Whole suite, 3 runs per arm** | **$5.21** | **$5.35** | **$4.17** | **$2.47** |

- For Sonnet the plugin costs nothing extra: fire runs cost about the same in
  both arms, and on `sns-01` the arm without the plugin spends more turns on
  sweeps against the true model.
- For Haiku a fire run with the plugin costs about 60% more, mostly on
  `sns-02` (all three runs hit the 40-turn limit, see Findings) and `sns-01`
  (more checks and iterations).
- Judge included, the Sonnet suite cost about $17.50 and the Haiku suite
  about $8.70. The top-level `costUsd` in each `aggregate-result.json` is the
  agent cost of both arms (judge excluded); per-run judge cost is stored as
  `judgeCostUsd`.

### Findings

**Sonnet already picks the right formulation; the skill improves how it
chooses parameters and reports.** Without the plugin Sonnet writes the right
objective with a PyProximal solver in 10/12 fire runs (the two misses are a
hand-written group-sparsity FISTA on `sns-02`), with it in 12/12. The Δ comes
from the process graders:

| Sonnet, fire runs | with | without |
| ----------------- | ---- | ------- |
| right objective with a PyProximal solver (`objective-formulation`) | 12/12 | 10/12 |
| reports how the solver stopped (`convergence-reported`) | 11/12 | 3/12 |
| no true model in `invert.py` (`no-truth-leak`) | 12/12 | 9/12 |
| no tuning against the true model reported (`no-truth-leak-answer`) | 11/12 | 5/12 |
| SNR above the threshold (`metric-threshold`) | 6/12 | 12/12 |

- The skill asks for every free parameter (weight, `tau` for ADMM/PnP, rank,
  `niter`) to be chosen by a criterion that does not use the true model. With
  it, Sonnet uses the discrepancy principle (`sns-01`, `sns-02`), held-out
  observed entries (`sns-03`) or a norm-based `tau` (`sns-04`). Without it,
  Sonnet sweeps the weight or `tau` against the true model in 7/12 fire runs
  (`sns-01` 3/3, `sns-03` 1/3, `sns-04` 3/3), in `invert.py` or in
  exploratory runs it then reports.
- That honesty costs SNR: on `sns-01` the discrepancy principle over-smooths
  the Box + TV solution to ~13 dB (vs 20.2–20.9 dB tuned on the truth) and on
  `sns-04` the PnP result with a norm-based `tau` is 17.6 dB (vs 20.8 dB), so
  both fail `metric-threshold` in 3/3 runs with the plugin. This is why the Δ
  on `sns-01` is only +0.02 (see Known limitations).
- `sns-02` (+0.25): without the plugin Sonnet solved the joint problem
  without PyProximal (its own group soft-threshold) in 2/3 runs; with it, it
  used `pyproximal.L21` in 3/3.
- `sns-04` (+0.23): in 3/3 runs without the plugin `tau` was hard-coded after
  a sweep against the truth (`step-size-from-norm` and `no-truth-leak-answer`
  fail).
- The skill never fired on the negative cases (0/6).

**Haiku gets a similar fire-case uplift (+0.14), but mostly on one case, and
the skill over-triggers.** Haiku rarely reaches the right formulation in
either arm (3/12 fire runs with the plugin, 0/12 without):

- `sns-01` (+0.24): with the skill Haiku used `ProximalGradient` + `Box` in
  3/3 runs (one also added an L2 penalty and was graded wrong on a 1–2 split
  vote); without it, scipy `L-BFGS-B` or `lsq_linear` with bounds in 3/3,
  which reach similar SNR but fail `objective-formulation` by design.
- `sns-02` (−0.01): with the skill Haiku never used `L21`. It tried
  independent or weighted L1 and support detection, and all three runs hit the
  40-turn limit without a final answer. Without it, independent L1 or a
  hand-written support transfer from sensor 2. The skill lists group sparsity
  but does not show how to couple signals with `L21`.
- `sns-03` (+0.25): the skill fired in 0/3 runs, so this Δ is run-to-run
  variance of the same unassisted behaviour (hand-written SVT or rank-3
  iterative hard thresholding, one `ProximalGradient` + `Nuclear` run).
- `sns-04` (+0.10): the skill fired in 2/3 runs; one used `PlugAndPlay` with
  ADMM (20.2 dB), the others TV or a hand-written gradient + median loop.
  Without it, hand-written loops in 3/3 (5–7 dB in two runs).
- `sns-05` (−0.67): the skill fired on plain Tikhonov in 3/3 runs and steered
  Haiku to PyProximal solvers for a quadratic problem; one run hit the 25-turn
  limit. This removes most of the fire-case gain from the suite mean.

Follow-ups for the skill suggested by these runs: a worked group-sparsity
example (`L21` over stacked signals), a description that fires for Haiku on
matrix completion and Plug-and-Play, and a clearer "not for quadratic
(Tikhonov) problems" boundary in the description.

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
  (scipy bounded solvers, hand-written FISTA/SVT/ADMM), since the plugin is
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
