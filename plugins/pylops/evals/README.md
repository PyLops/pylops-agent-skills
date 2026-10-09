# Eval findings for the `pylops` plugin

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
grade the answer to the actual request. The judge is Sonnet 5.5
(`--judge-model sonnet`).

### Results

All three models were run with 3 runs per arm and Sonnet 5.5 as the judge, on
the current skill.

| Case | Opus 5.5 with | Opus 5.5 without | Opus 5.5 Δ | Haiku 4.5 with | Haiku 4.5 without | Haiku 4.5 Δ | Haiku 5.5 with | Haiku 5.5 without | Haiku 5.5 Δ |
| ---- | ------------- | ---------------- | ---------- | -------------- | ----------------- | ----------- | -------------- | ----------------- | ----------- |
| `sip-01-blocky-blur` | 1.00 | 0.92 | +0.08 | 0.38 | 0.18 | +0.21 | 0.97 | 0.92 | +0.05 |
| `sip-02-outlier-receivers` | 1.00 | 1.00 | 0.00 | 0.79 | 0.92 | −0.13 | 0.95 | 0.85 | +0.10 |
| `sip-03-tiny-scale-native` | 1.00 | 0.92 | +0.08 | 0.46 | 0.44 | +0.03 | 0.97 | 0.87 | +0.10 |
| `sip-04-cs-dct` | 1.00 | 0.87 | +0.13 | 1.00 | 0.23 | **+0.77** | 0.87 | 0.90 | −0.03 |
| `sip-05-neg-broken-inversion` | 1.00 | 1.00 | 0.00 | 1.00 | 0.67 | +0.33 | 1.00 | 1.00 | 0.00 |
| `sip-06-neg-tune-eps` | 1.00 | 1.00 | 0.00 | 0.50 | 0.67 | −0.17 | 1.00 | 1.00 | 0.00 |
| **Mean (all cases)** | | | **+0.05** | | | **+0.17** | | | **+0.04** |
| **Mean (fire cases `sip-01`–`sip-04`)** | | | **+0.07** | | | **+0.22** | | | **+0.06** |

| Fire runs | Opus 5.5 with | Opus 5.5 without | Haiku 4.5 with | Haiku 4.5 without | Haiku 5.5 with | Haiku 5.5 without |
| --------- | ------------- | ---------------- | -------------- | ----------------- | -------------- | ----------------- |
| skill called (`trigger`) | 12/12 | – | 6/12 | – | 8/12 | – |
| right prior/solver (`prior-choice`) | 12/12 | 12/12 | 7/12 | 4/12 | 12/12 | 11/12 |
| SNR above the threshold (`snr-threshold`) | 12/12 | 12/12 | 7/12 | 4/12 | 12/12 | 12/12 |
| reports how the solver stopped (`iterations-or-cost`) | 12/12 | 4/12 | 7/12 | 3/12 | 7/12 | 4/12 |
| reports the residual vs the noise level (`residual-vs-noise`) | 12/12 | 9/12 | 4/12 | 0/12 | 8/12 | 6/12 |
| mean score | 1.00 | 0.93 | 0.66 | 0.44 | 0.94 | 0.89 |

`solve-inverse-problem` never fired on the negative cases (0/18 runs with the
plugin across the three models).

Reports:

- Opus 5.5 (`--model claude-opus-5-5`, agent `claude-opus-5-5`):
  [report](results/2026-10-08T22-43-44-530Z/report.html).
- Haiku 4.5 (`--model claude-haiku-4-5-20251001`, agent `claude-haiku-4-5-20251001`):
  [report](results/2026-10-08T22-43-44-411Z/report.html).
- Haiku 5.5 (`--model claude-haiku-5-5`, agent `claude-haiku-5-5`):
  [report](results/2026-10-08T22-31-43-603Z/report.html).

### Cost and effort

Mean agent cost per run (USD, **excluding the judge**), mean wall time and mean
turns, from the same runs. The judge (Sonnet 5.5) adds about $0.02–0.11 per
fire run, and up to ~$0.50–0.95 on `sip-06`, whose long traces are expensive
to grade.

| Case | Opus 5.5 with | Opus 5.5 without | Haiku 4.5 with | Haiku 4.5 without | Haiku 5.5 with | Haiku 5.5 without |
| ---- | ------------- | ---------------- | -------------- | ----------------- | -------------- | ----------------- |
| `sip-01-blocky-blur` | $0.32 · 84 s · 8.3 | $0.26 · 75 s · 5.7 | $0.20 · 92 s · 11.3 | $0.18 · 102 s · 7.3 | $0.07 · 77 s · 11.3 | $0.06 · 64 s · 9.3 |
| `sip-02-outlier-receivers` | $0.28 · 49 s · 7.3 | $0.19 · 41 s · 3.3 | $0.18 · 101 s · 12.7 | $0.13 · 68 s · 3.3 | $0.07 · 53 s · 10.3 | $0.06 · 46 s · 9.3 |
| `sip-03-tiny-scale-native` | $0.33 · 77 s · 7.0 | $0.23 · 50 s · 4.7 | $0.29 · 182 s · 32.3 | $0.34 · 231 s · 35.3 | $0.08 · 72 s · 8.7 | $0.09 · 70 s · 11.7 |
| `sip-04-cs-dct` | $0.27 · 53 s · 8.0 | $0.20 · 41 s · 3.7 | $0.17 · 117 s · 18.0 | $0.19 · 130 s · 18.3 | $0.07 · 39 s · 7.0 | $0.10 · 44 s · 6.0 |
| `sip-05-neg-broken-inversion` | $0.20 · 30 s · 4.3 | $0.13 · 23 s · 2.0 | $0.19 · 139 s · 13.3 | $0.07 · 54 s · 1.0 | $0.04 · 29 s · 4.7 | $0.03 · 25 s · 2.7 |
| `sip-06-neg-tune-eps` | $0.83 · 75 s · 9.0 | $0.94 · 78 s · 11.0 | $0.45 · 279 s · 13.3 | $0.43 · 60 s · 5.3 | $0.65 · 60 s · 12.3 | $0.13 · 36 s · 4.3 |
| **Fire cases, sum per run** | **$1.20** | **$0.88** | **$0.84** | **$0.84** | **$0.30** | **$0.30** |
| **Whole suite, 3 runs per arm** | **$6.66** | **$5.87** | **$4.43** | **$4.01** | **$2.95** | **$1.36** |

- With the plugin a fire run costs about 35% more for Opus 5.5 ($1.20 vs
  $0.88), from loading the skill and the extra turns it asks for (checks,
  convergence report). For Haiku 4.5 and Haiku 5.5 both arms cost the same on
  fire cases.
- Haiku 5.5 is about 3× cheaper than Haiku 4.5 on fire cases and 3–4×
  cheaper than Opus 5.5, with runs of 6–12 turns.
- The difference in the whole suite for Haiku 5.5 comes from `sip-06`, where
  `tune-regularization` fires in every run with the plugin.
- The top-level `costUsd` in each `aggregate-result.json` is the agent cost of
  both arms (judge excluded); per-run judge cost is stored as `judgeCostUsd`.

### Findings

**The description is written as an instruction.** It asks to load the skill
before choosing a solver or writing any inversion code, "even when the right
solver or regularisation seems obvious", and points broken inversions and
L-curve requests to the sibling skills. Haiku 5.5 decides in its first turn
whether to load a skill and skips it when it already sees the answer: with a
descriptive wording ("Set up and run the inversion… Use when…") it loaded the
skill in 1 of 12 fire runs, with the current one in 8 of 12, and the negative
cases still never fire it.

**Opus 5.5 does not need the skill for the method; it uses it for reporting.**
Both arms avoid every trap: TV (`splitbregman`) for the blocky model, IRLS for
the outliers, rescaled tiny data and `fista` in the DCT, with the right prior in
12/12 fire runs and SNRs of 28.9–65 dB. With the plugin it loads the skill in
12/12 runs and every fire run scores 1.00; the Δ of +0.07 on fire cases comes
from reporting how the solver stopped (12/12 vs 4/12) and the residual vs the
noise level (12/12 vs 9/12).

**Haiku 4.5 benefits most when the skill fires, but it fires in only half the
runs.** Runs that loaded the skill score 0.92 on average, runs with the plugin
that did not load it 0.40, and runs without the plugin 0.44:

- `sip-04`: the skill fired in 3/3 runs, all scoring 1.00 with a sparse DCT
  inversion (18–33 dB); without it, least squares in 3/3 (1.1 dB). This is the
  whole +0.77.
- `sip-01`: the one run that loaded the skill chose TV but tuned it below the
  threshold (11 dB); the other runs, in both arms, did not use TV (8–14 dB).
- `sip-02`: the run that did not load the skill chose a robust misfit but
  stopped at 22 dB, below the 30 dB threshold, hence −0.13 against an arm
  without the plugin that reached 61–64 dB with IRLS in 3/3.
- `sip-03`: the skill never fired, and both arms mostly fail the scaling trap
  (`prior-choice` 0/3 with the plugin, 1/3 without; one run without hit the
  40-turn limit).
- `sip-05` (negative case): with the plugin the adjoint fix is right in 3/3
  runs, without it in 1/3; this reflects the sibling `debug-inversion` skill,
  not `solve-inverse-problem`.
- `sip-06` (negative case): `tune-regularization` fired in 3/3 runs with the
  plugin, but every answer failed: one picked `epsRs` by the SNR against the
  true model, one called the current value "over-smoothed" while recommending
  a larger weight, and one timed out (see Known limitations). Without the
  plugin 2/3 answers made the same direction error.

**Haiku 5.5 avoids the traps on its own; the skill adds reporting.** Without
the plugin it already picks the right prior in 11/12 fire runs and passes the
SNR threshold in 12/12 (18.6–32.6 dB on `sip-01`, 54–61 dB on `sip-02`,
33–34 dB on `sip-03`, 38–65 dB on `sip-04`). Runs that loaded the skill score
0.97, runs with the plugin that did not load it 0.89, the same as without the
plugin; the gain is in reporting how the solver stopped (6/8 loaded runs vs
4/12 without) and the residual vs the noise level (7/8 vs 6/12).

- The skill fires in 3/3 runs of `sip-01` and `sip-02`, 2/3 of `sip-03` and
  0/3 of `sip-04`. `sip-04` asks to "reconstruct the full signal" from a
  quarter of the samples, which reads as interpolation; the sibling
  `pick-sparsifying-transform` skill claims compressive sensing and
  interpolation, so the description does not compete for it.
- On `sip-03`, one run without the plugin failed `prior-choice` while reaching
  33.7 dB.

### Known limitations of the graders

- The trace passed to LLM judges is truncated for long runs
  ("…N messages elided…"), so rubrics avoid claims that need the whole trace;
  `no-truth-leak` reads `invert.py` directly for this reason.
- `no-truth-leak` allows using the noise level stated in the prompt (e.g. 1%
  of the clean data's maximum) even though the script computes it from the
  true model.
- The negative cases also score the quality of the answer, so their Δ measures
  the sibling skills (`debug-inversion`, `tune-regularization`) rather than
  `solve-inverse-problem`.
- One Haiku 4.5 run of `sip-06` with the plugin timed out after 600 s while
  following `tune-regularization`, with no answer; this is a plugin issue to
  follow up, not a grader issue.
- `sip-04` is graded on the prior, but its wording also matches
  `pick-sparsifying-transform`, so the trigger rate of `solve-inverse-problem`
  on it says more about skill routing than about the skill.
- Run-to-run variance is of the same size as Δ for Opus 5.5 and Haiku 5.5 (a
  single borderline judge vote moves a case by ±0.1–0.2): use `runs: 3` (the
  default) or more before drawing conclusions, and compare runs that loaded the
  skill with runs that did not (`scripts/eval_tables.py` prints this split).

## `debug-inversion` (`dbg-*`)

### What the suite tests

| Case | Input | Problem | Right diagnosis |
| ---- | ----- | ------- | --------------- |
| `dbg-01-custom-adjoint-conv` | pasted code | custom convolution `FunctionOperator`, lsqr error ~0.93 with ringing | adjoint slice off by one sample (`nh - 2` → `nh - 1`), not damping/iterations |
| `dbg-02-vstack-missing-conj` | pasted code | complex steering operator in a `VStack` does not converge | `_rmatvec` is not the Hermitian adjoint (missing conjugate) |
| `dbg-03-complex-dtype-funcop` | pasted code | crash / wrong result with complex data | `FunctionOperator` built without `dtype="complex128"` |
| `dbg-04-scaling-stacked-blocks` | pasted code | joint tomography + gravity, dataset 1 ignored, model error ~0.22 | blocks differ by orders of magnitude; weighting by 1/σ brings the error to ~7e-4 |
| `dbg-05-fista-eps-prose` | prose only | `fista` returns exactly zero for any `niter` | `eps` far above the critical value `max|Opᴴy|`; more iterations cannot help |
| `dbg-06-physics-limited` | pasted code | Ricker deconvolution stuck at error ~0.85 | no bug: band-limited wavelet / null space; change the prior (sparsity), not the code |
| `dbg-07-two-bugs` | pasted code | joint inversion stays at error ~0.27 | wrong cumsum adjoint **and** block scaling; each fix alone does not help |
| `dbg-08-neg-which-solver` | prose | which solver for sparse-spike deconvolution | `debug-inversion` must not fire |
| `dbg-09-neg-scipy-minimize` | prose | SciPy BFGS logistic regression diverges | must not fire and must not bring in PyLops |

Graders per fire case:

| Grader | Type | Weight | Checks |
| ------ | ---- | ------ | ------ |
| `diagnosis` | LLM, final answer | 1 | the right cause and fix for the case, and not blaming damping/iterations/solver (for `dbg-04`, also not blaming the physics) |
| `no-fabrication` | LLM, trace | 1 | no claim of running code without any tool call, and no value presented as measured that contradicts a visible tool result (values derived from the prompt, labelled as estimates, or possibly in elided parts of the trace are allowed) |
| `fix-token` | regex, final answer | 0.5 | the key fix in the answer (e.g. `nh - 1` or `Convolve1D`, a conjugate transpose, `dtype=complex`, a reversed cumsum); `dbg-01`–`03` and `dbg-07` only |
| `trigger` | `tool_used: Skill` | – | display only under ablation (not scored) |

The negative cases check that the skill is not called (`tool_used`, max 0) and
grade the answer to the actual question; `dbg-09` also fails if the answer
mentions PyLops. The judge is Sonnet 5.5 (`--judge-model sonnet`).

### Results

All three models were run with 3 runs per arm and Sonnet 5.5 as the judge.

| Case | Opus 5.5 with | Opus 5.5 without | Opus 5.5 Δ | Haiku 4.5 with | Haiku 4.5 without | Haiku 4.5 Δ | Haiku 5.5 with | Haiku 5.5 without | Haiku 5.5 Δ |
| ---- | ------------- | ---------------- | ---------- | -------------- | ----------------- | ----------- | -------------- | ----------------- | ----------- |
| `dbg-01-custom-adjoint-conv` | 1.00 | 1.00 | 0.00 | 0.87 | 0.87 | 0.00 | 1.00 | 1.00 | 0.00 |
| `dbg-02-vstack-missing-conj` | 1.00 | 1.00 | 0.00 | 0.67 | 0.53 | +0.13 | 0.80 | 0.87 | −0.07 |
| `dbg-03-complex-dtype-funcop` | 1.00 | 1.00 | 0.00 | 1.00 | 1.00 | 0.00 | 1.00 | 0.87 | +0.13 |
| `dbg-04-scaling-stacked-blocks` | 1.00 | 1.00 | 0.00 | 0.67 | 0.67 | 0.00 | 0.67 | 0.83 | −0.17 |
| `dbg-05-fista-eps-prose` | 1.00 | 1.00 | 0.00 | 0.67 | 0.50 | +0.17 | 1.00 | 1.00 | 0.00 |
| `dbg-06-physics-limited` | 1.00 | 1.00 | 0.00 | 0.50 | 0.50 | 0.00 | 1.00 | 1.00 | 0.00 |
| `dbg-07-two-bugs` | 1.00 | 1.00 | 0.00 | 0.60 | 0.60 | 0.00 | 1.00 | 1.00 | 0.00 |
| `dbg-08-neg-which-solver` | 1.00 | 1.00 | 0.00 | 0.83 | 1.00 | −0.17 | 1.00 | 1.00 | 0.00 |
| `dbg-09-neg-scipy-minimize` | 0.89 | 1.00 | −0.11 | 0.89 | 1.00 | −0.11 | 1.00 | 1.00 | 0.00 |
| **Mean (all cases)** | | | **−0.01** | | | **0.00** | | | **−0.01** |
| **Mean (fire cases `dbg-01`–`dbg-07`)** | | | **0.00** | | | **+0.04** | | | **−0.01** |

| Fire runs | Opus 5.5 with | Opus 5.5 without | Haiku 4.5 with | Haiku 4.5 without | Haiku 5.5 with | Haiku 5.5 without |
| --------- | ------------- | ---------------- | -------------- | ----------------- | -------------- | ----------------- |
| correct diagnosis (`diagnosis`) | 21/21 | 21/21 | 10/21 | 6/21 | 18/21 | 19/21 |
| no fabricated values (`no-fabrication`) | 21/21 | 21/21 | 19/21 | 21/21 | 21/21 | 20/21 |
| skill called (`trigger`) | 21/21 | – | 21/21 | – | 8/21 | – |

Reports:

- Opus 5.5 (`--model opus`, agent `claude-opus-5-5`):
  [report](results/2026-09-28T16-33-37-573Z/report.html).
- Haiku 4.5 (`--model haiku`, agent `claude-haiku-4-5-20251001`):
  [report](results/2026-09-28T16-40-57-071Z/report.html).
- Haiku 5.5 (`--model claude-haiku-5-5`, agent `claude-haiku-5-5`):
  [report](results/2026-10-08T21-20-28-233Z/report.html).

### Cost and effort

Mean agent cost per run (USD, **excluding the judge**), mean wall time and mean
turns, from the same runs. The judge (Sonnet 5.5) adds about $0.10–0.35 per fire run.

| Case | Opus 5.5 with | Opus 5.5 without | Haiku 4.5 with | Haiku 4.5 without | Haiku 5.5 with | Haiku 5.5 without |
| ---- | ------------- | ---------------- | -------------- | ----------------- | -------------- | ----------------- |
| `dbg-01-custom-adjoint-conv` | $0.46 · 32 s · 4.0 | $0.18 · 23 s · 2.0 | $0.36 · 95 s · 15.0 | $0.15 · 60 s · 8.0 | $0.28 · 24 s · 2.3 | $0.17 · 25 s · 2.0 |
| `dbg-02-vstack-missing-conj` | $0.38 · 33 s · 5.0 | $0.31 · 24 s · 2.0 | $0.28 · 122 s · 13.0 | $0.21 · 69 s · 3.7 | $0.29 · 34 s · 5.7 | $0.28 · 28 s · 2.3 |
| `dbg-03-complex-dtype-funcop` | $0.39 · 49 s · 6.3 | $0.29 · 31 s · 3.7 | $0.26 · 55 s · 9.3 | $0.22 · 31 s · 6.7 | $0.25 · 37 s · 7.0 | $0.24 · 31 s · 4.7 |
| `dbg-04-scaling-stacked-blocks` | $0.47 · 54 s · 5.3 | $0.28 · 29 s · 2.0 | $0.28 · 92 s · 7.7 | $0.15 · 35 s · 3.3 | $0.23 · 52 s · 4.3 | $0.18 · 39 s · 2.0 |
| `dbg-05-fista-eps-prose` | $0.47 · 41 s · 5.0 | $0.29 · 28 s · 1.0 | $0.31 · 98 s · 12.7 | $0.12 · 21 s · 1.0 | $0.19 · 34 s · 3.7 | $0.19 · 24 s · 1.0 |
| `dbg-06-physics-limited` | $0.45 · 45 s · 5.3 | $0.39 · 37 s · 3.0 | $0.33 · 154 s · 15.3 | $0.17 · 51 s · 4.0 | $0.43 · 47 s · 4.0 | $0.33 · 38 s · 3.3 |
| `dbg-07-two-bugs` | $0.35 · 37 s · 4.7 | $0.25 · 27 s · 2.3 | $0.31 · 134 s · 11.0 | $0.27 · 85 s · 8.0 | $0.51 · 47 s · 4.0 | $0.37 · 46 s · 2.0 |
| `dbg-08-neg-which-solver` | $0.19 · 23 s · 4.0 | $0.11 · 20 s · 1.0 | $0.06 · 38 s · 6.3 | $0.04 · 15 s · 1.0 | $0.06 · 13 s · 1.0 | $0.01 · 17 s · 1.0 |
| `dbg-09-neg-scipy-minimize` | $0.13 · 17 s · 1.0 | $0.11 · 17 s · 1.0 | $0.04 · 14 s · 1.0 | $0.03 · 13 s · 1.0 | $0.02 · 16 s · 1.0 | $0.02 · 12 s · 1.0 |
| **Fire cases, sum per run** | **$2.97** | **$1.98** | **$2.13** | **$1.29** | **$2.17** | **$1.76** |
| **Whole suite, 3 runs per arm** | **$9.87** | **$6.61** | **$6.68** | **$4.09** | **$6.74** | **$5.37** |

- With the plugin a fire run costs about 50% more for Opus 5.5 and 65% more for
  Haiku 4.5, mostly from loading the skill and the extra turns it asks for
  (reproducing the problem, dot-tests, testing the fix).
- For Opus 5.5 the extra cost buys a longer, more systematic report but not a
  better diagnosis; for Haiku 4.5 it buys a few more correct diagnoses.
- For Haiku 5.5 a fire run with the plugin costs about 25% more ($2.17 vs
  $1.76), from the 8 runs that load the skill, and buys no better diagnosis.
- Haiku 5.5 runs are much shorter than Haiku 4.5 runs (with the plugin 2–7
  turns vs 8–15, and half the wall time) but cost about the same per run with
  the plugin and more without it.

### Findings

**Opus 5.5 does not need the skill.** Both arms get every fire case right
(diagnosis 21/21, `no-fabrication` 21/21). Without the plugin Opus 5.5 runs the
user's script once or twice and answers in 2–4 turns, including both bugs in
`dbg-07` and "no bug, physics-limited" in `dbg-06`; with the plugin it does the
same work as a check-by-check report in 4–6 turns. The only difference is
`dbg-09`, where one answer with the plugin mentioned PyLops for a SciPy
question.

**Haiku 4.5 gets somewhat more diagnoses right with the skill, but the suite
stays hard for it.** Correct diagnoses rise from 6/21 to 10/21 fire runs; the
mean Δ is small (+0.04 on fire cases) because most cases fail the diagnosis in
both arms and the gains are one run per case:

| Haiku 4.5, correct diagnosis | with | without |
| ------------------------ | ---- | ------- |
| `dbg-01` wrong adjoint slice | 3/3 | 2/3 |
| `dbg-02` missing conjugate | 1/3 | 0/3 |
| `dbg-03` missing complex dtype | 3/3 | 3/3 |
| `dbg-04` block scaling | 1/3 | 1/3 |
| `dbg-05` `eps` too large (prose) | 1/3 | 0/3 |
| `dbg-06` physics-limited, no bug | 0/3 | 0/3 |
| `dbg-07` two bugs | 1/3 | 0/3 |

- `no-fabrication` now fails only 2/21 Haiku 4.5 runs with the plugin. One is a
  real overclaim: the `dbg-07` report gives a dot-test "ratio −8.5" where the
  tool output shows 1.38 vs −0.998 (about −1.4).
- `dbg-08`: in 1/3 runs with the plugin Haiku 4.5 asked clarifying questions
  instead of recommending a solver and hit the 8-turn limit (influence of
  `solve-inverse-problem`; `debug-inversion` was not called).
- The arm without the plugin varies between runs (6/21 correct diagnoses here,
  7/21–12/21 in earlier runs), so single-case Δs of one run (±0.13–0.17) are
  within run-to-run variance.

**Haiku 5.5 does not need the skill.** It gets 19/21 diagnoses right without
the plugin and 18/21 with it, close to Opus 5.5, including the cases Haiku 4.5
never solved: "no bug, physics-limited" in `dbg-06`, both bugs in `dbg-07` and
the `eps` far above the critical value in the prose-only `dbg-05`, 3/3 in each
arm. Without the plugin it runs the user's script and answers in 1–5 turns.

| Haiku 5.5, correct diagnosis | with | without | skill called |
| ---------------------------- | ---- | ------- | ------------ |
| `dbg-01` wrong adjoint slice | 3/3 | 3/3 | 0/3 |
| `dbg-02` missing conjugate | 2/3 | 2/3 | 2/3 |
| `dbg-03` missing complex dtype | 3/3 | 3/3 | 2/3 |
| `dbg-04` block scaling | 1/3 | 2/3 | 1/3 |
| `dbg-05` `eps` too large (prose) | 3/3 | 3/3 | 1/3 |
| `dbg-06` physics-limited, no bug | 3/3 | 3/3 | 1/3 |
| `dbg-07` two bugs | 3/3 | 3/3 | 1/3 |

- Haiku 5.5 loads `debug-inversion` in only 8/21 fire runs (Haiku 4.5: 21/21),
  so most runs with the plugin behave like runs without it and the per-case Δs
  (±0.07–0.17) are within run-to-run variance.
- `dbg-04` is the only case that still fails on the diagnosis. The one run
  that loaded the skill ranked the absolute `tol` of `cgls` (which stops it at
  iteration 60) as the main cause and the block scaling second; the two other
  failures found the imbalance but explained it mainly through `damp` or
  hinted at a resolution limit (one of them on a split vote).
- `dbg-02`: the two failed diagnoses give a correct fix,
  `(y.conj() @ self.A).conj()`, and most likely fail the rubric's request for
  a complex dot-test (`complexflag`), which they do not mention; these are
  borderline grades.
- `no-fabrication` fails once, without the plugin on `dbg-03`: the answer
  reports an error of "0.13 → 1.32 at `1e-1`" where the tool output shows only
  1.32.
- The negative cases pass in every run in both arms.

Parts of the skill that matter for Haiku 4.5 (each fixes a failure seen with an
earlier version of the skill):

- An explicit "carry out these steps yourself, now" paragraph. Without it,
  Haiku 4.5 often ended its turn right after loading the skill ("the skill is
  running diagnostics in the background… I'll report back") with no answer;
  with it, this happened in 0/21 fire runs.
- For prose-only reports such as `dbg-05`, reasoning from the numbers or
  building a reproduction instead of stopping to ask for the script.
- Continuing through the remaining checks after one fails, instead of
  stopping at the first: otherwise Haiku 4.5 stops after the wrong adjoint in
  `dbg-07` and misses the block scaling.
- A report that separates checks that were run from checks that were not, and
  tested fixes from untested ones. Without it, Haiku 4.5 filled in checks it never
  ran (e.g. "both blocks pass the dot-test" when only the full operator was
  tested) and concluded "physically limited" after a weighting fix it had
  implemented wrongly.

### Known limitations of the graders

- The runs need PyLops as a regular (non-editable) install first on `PATH`; see
  the repository README. With an editable install, runs fail with
  `No module named 'pylops'` and cannot measure anything.
- The trace passed to LLM judges is truncated for long runs ("…N messages
  elided…"), and runs with the plugin are longer (Haiku 4.5: 8–15 turns vs 1–8,
  Opus 5.5: 4–6 vs 1–4). `no-fabrication` therefore does not treat a value missing
  from the visible trace as fabricated: it fails only a claim of running code
  with no tool call at all, or a value presented as measured that contradicts
  a visible tool result. Earlier, stricter wordings failed long runs whose
  measured values sat in elided tool results (every such failure checked by
  hand was a false positive) and correct one-turn answers that derived their
  numbers from the prompt. The current check is weaker at catching invented
  numbers inside elided sections.
- The judges' reasoning is not stored in `aggregate-result.json` (only the
  votes); use `--keep-temp` to keep the traces for spot checks.
- `dbg-08` grades the answer quality, which with the plugin installed can be
  influenced by `solve-inverse-problem` (asking clarifying questions instead of
  answering, which can hit the 8-turn limit).
- The `fix-token` regex of `dbg-02` misses the equivalent fix
  `y @ self.A.conj()`, which one Haiku 5.5 run with the plugin gave (its
  diagnosis passed); this costs 0.2 on that run.
