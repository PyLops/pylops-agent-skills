# Eval findings for the `pylops` plugin

This file records what the eval suites in this folder showed when they were
run: scores with and without the plugin, the uplift (Δ = with − without) per
agent model, and known limitations of the graders. How to run the suites is
described in the repository [README](../../../README.md#evals-claude-code-only).

Each run's HTML report is linked below (`results/<timestamp>/report.html`,
next to its `aggregate-result.json`). Scores are on a 0–1 scale; a case passes
only with a score of 1.

## `solve-inverse-problem` (`sip-*`)

### What the suite tests

| Case | Input | Trap for the naive approach | Right approach |
| ---- | ----- | --------------------------- | -------------- |
| `sip-01-blocky-blur` | prose | blocky model under a Gaussian blur: L2/Tikhonov tops out at ~14 dB | TV (L1 on the first derivative), e.g. `splitbregman`: 18–30 dB |
| `sip-02-outlier-receivers` | pasted code | 10% outliers in the data: `lsqr` gives ~2.5 dB | robust data misfit, e.g. `irls(kind="data")`: ~60 dB |
| `sip-03-tiny-scale-native` | prose | data ~1e-7 with PyLops-native solvers: the absolute `tol` stops `cgls` at iteration 0, x = 0 | rescale data/operator, invert, undo the scaling: 10–35 dB |
| `sip-04-cs-dct` | pasted code | 25% random samples of a DCT-sparse signal: least squares/smoothing ~1–2 dB, wrong `fista` `SOp` direction ~2.6 dB | sparsity in the DCT: >40 dB |
| `sip-05-neg-broken-inversion` | pasted code | broken adjoint, belongs to `debug-inversion` | `solve-inverse-problem` must not fire |
| `sip-06-neg-tune-eps` | pasted code | L-curve request, belongs to `tune-regularization` | `solve-inverse-problem` must not fire |

Each fire case asks for a script `invert.py` that is run and prints
`SNR_DB=<value>` (model vs true model). Graders per fire case:

| Grader | Type | Weight | Checks |
| ------ | ---- | ------ | ------ |
| `prior-choice` | LLM, final answer | 1 | the right prior/solver for the case, with a reason |
| `snr-threshold` | regex on the trace | 1 | a printed `SNR_DB=` above the case threshold (17 / 30 / 10 / 15 dB); also proves the script was run |
| `no-truth-leak` | LLM, `invert.py` | 0.5 | the true model does not flow into the computation of `xinv` |
| `script-exists` | file exists | 0.25 | `invert.py` was created |
| `residual-vs-noise` | LLM, final answer | 0.25 | data residual of the final model compared with the noise level |
| `iterations-or-cost` | LLM, final answer | 0.25 | how the solver stopped (iterations used, exit status or cost trend) |

The negative cases check that the skill is not called (`tool_used`, max 0) and
grade the answer to the actual request. The judge is Sonnet
(`--judge-model sonnet`).

### Results

Both models were run with 3 runs per arm and Sonnet as the judge.

| Case | Opus with | Opus without | Opus Δ | Haiku with | Haiku without | Haiku Δ |
| ---- | --------- | ------------ | ------ | ---------- | ------------- | ------- |
| `sip-01-blocky-blur` | 1.00 | 0.90 | +0.10 | 0.54 | 0.18 | **+0.36** |
| `sip-02-outlier-receivers` | 0.97 | 0.95 | +0.03 | 0.82 | 0.85 | −0.03 |
| `sip-03-tiny-scale-native` | 0.90 | 0.79 | +0.10 | 0.59 | 0.56 | +0.03 |
| `sip-04-cs-dct` | 1.00 | 0.97 | +0.03 | 0.72 | 0.23 | **+0.49** |
| `sip-05-neg-broken-inversion` | 1.00 | 1.00 | 0.00 | 0.83 | 0.50 | +0.33 |
| `sip-06-neg-tune-eps` | 0.83 | 1.00 | −0.17 | 0.67 | 0.67 | 0.00 |
| **Mean (all cases)** | | | **+0.01** | | | **+0.20** |
| **Mean (fire cases `sip-01`–`sip-04`)** | | | **+0.07** | | | **+0.21** |

Reports:

- Opus (agent `claude-opus-5-5`, default model):
  [report](results/2026-09-27T15-52-05-846Z/report.html).
- Haiku (`--model haiku`):
  [report](results/2026-09-27T07-13-48-211Z/report.html).

### Cost and effort

Mean agent cost per run (USD, **excluding the judge**), mean wall time and mean
turns, from the same runs. The judge (Sonnet) adds about $0.01–0.10 per run,
and up to ~$0.45–0.80 on `sip-06`, whose long traces are expensive to grade.

| Case | Opus with | Opus without | Haiku with | Haiku without |
| ---- | --------- | ------------ | ---------- | ------------- |
| `sip-01-blocky-blur` | $0.33 · 93 s · 8.7 | $0.24 · 73 s · 5.7 | $0.25 · 145 s · 25.0 | $0.12 · 77 s · 6.0 |
| `sip-02-outlier-receivers` | $0.28 · 53 s · 8.3 | $0.20 · 41 s · 4.7 | $0.16 · 112 s · 15.7 | $0.10 · 66 s · 8.0 |
| `sip-03-tiny-scale-native` | $0.34 · 71 s · 9.7 | $0.26 · 57 s · 6.3 | $0.29 · 216 s · 22.7 | $0.28 · 176 s · 32.0 |
| `sip-04-cs-dct` | $0.30 · 47 s · 7.0 | $0.24 · 38 s · 4.0 | $0.22 · 158 s · 20.0 | $0.21 · 133 s · 27.3 |
| `sip-05-neg-broken-inversion` | $0.17 · 23 s · 4.0 | $0.13 · 22 s · 2.3 | $0.15 · 122 s · 10.0 | $0.05 · 44 s · 1.0 |
| `sip-06-neg-tune-eps` | $0.78 · 72 s · 9.0 | $0.82 · 82 s · 12.3 | $0.42 · 92 s · 8.7 | $0.85 · 94 s · 8.0 |
| **Fire cases, sum per run** | **$1.24** | **$0.95** | **$0.91** | **$0.71** |
| **Whole suite, 3 runs per arm** | **$6.57** | **$5.70** | **$4.46** | **$4.83** |

- With the plugin, a fire run costs about 30% more for both models (Opus
  $1.24 vs $0.95, Haiku $0.91 vs $0.71 for the four fire cases), mostly from
  loading the skill and the extra turns it asks for (checks, convergence report).
- For Opus that extra cost buys only better reporting (see Findings); for
  Haiku it buys a better method on `sip-01` and `sip-04`.
- The lower Haiku cost with the plugin on `sip-06` is partly one run that
  stopped early without an answer (see Known limitations), not an efficiency gain.
- The top-level `costUsd` in each `aggregate-result.json` is the agent cost of
  both arms (judge excluded); per-run judge cost is stored as `judgeCostUsd`.

### Findings

**Opus does not seem to benefit from the skill.** Without the plugin, Opus
already avoids every trap: it picks TV for the blocky model, IRLS for the
outliers, rescales the tiny data and uses a sparse DCT inversion. Both arms
pass the SNR threshold in 12/12 fire runs (29–65 dB), and the prior/solver
choice is graded correct in 11/12 runs in each arm. The small positive Δ on
the fire cases (+0.07) comes only from reporting:

| Opus, fire runs | with | without |
| --------------- | ---- | ------- |
| reports how the solver stopped (`iterations-or-cost`) | 12/12 | 4/12 |
| reports the residual vs the noise level (`residual-vs-noise`) | 11/12 | 9/12 |

On `sip-03` one run in each arm used `regularized_inversion` with its default
engine (scipy) instead of `engine="pylops"`, so the skill did not prevent that
trap either. On `sip-06` the one failing run with the plugin built the L-curve
but recommended the value picked by GCV rather than by the L-curve corner;
this is a borderline grade and explains the −0.17 on that case.

**Haiku does benefit from the skill.** Mean Δ is +0.20, and the uplift is in
the method, not only in reporting:

- `sip-01`: with the skill Haiku chose TV in 2/3 runs; without it, L2/Tikhonov
  in 3/3 (4.8–13.7 dB).
- `sip-04`: with the skill Haiku used a sparse DCT/FFT inversion in 3/3 runs
  (one reached 42 dB); without it, smoothing regularisation in 3/3 (~2 dB).
- `sip-05` (negative case): `solve-inverse-problem` correctly did not fire, but
  the answers improved with the plugin (2/3 correct adjoint fixes vs 0/3 without:
  Haiku reversed the filter but kept the wrong `[:nt]` slice). This reflects the
  sibling skills in the plugin, not `solve-inverse-problem`.

Limits of the Haiku uplift:

- Haiku with the plugin still passes no fire case fully: after choosing the
  right prior it tunes the weights poorly and stays below the SNR thresholds
  on `sip-01` (best 16.1 dB) and in 2/3 runs of `sip-04` (7.5–8 dB).
- Haiku called the skill in only 7 of 12 fire runs (`sip-02` and `sip-03`: 1/3
  each). When the skill does not fire, the arm with the plugin behaves like the
  arm without it, which is why those cases show Δ ≈ 0. The skill description is
  a lever for weaker models.
- Reporting (residual vs noise, iterations) fails in both arms most of the time.

### Known limitations of the graders

- The trace passed to LLM judges is truncated for long runs
  ("…N messages elided…"), so rubrics avoid claims that need the whole trace;
  `no-truth-leak` reads `invert.py` directly for this reason.
- `no-truth-leak` allows using the noise level stated in the prompt (e.g. 1%
  of the clean data's maximum) even though the script computes it from the
  true model. The Haiku run predates this wording and `no-truth-leak` failed 2
  of 3 runs of `sip-03` with the plugin, most likely for this reason (about −0.08 on that
  case); with the current wording it passed 24/24 fire runs with Opus.
- The negative cases also score the quality of the answer, so their Δ measures
  the sibling skills (`debug-inversion`, `tune-regularization`) rather than
  `solve-inverse-problem`.
- In one Haiku run of `sip-06`, `tune-regularization` ended with "the skill is
  running in the background… I'll report back" and no answer; this is a plugin
  issue to follow up, not a grader issue.
- Run-to-run variance is of the same size as Δ for Opus (a single borderline
  judge vote moves a case by ±0.1–0.2): use `runs: 3` (the default) or more
  before drawing conclusions.
