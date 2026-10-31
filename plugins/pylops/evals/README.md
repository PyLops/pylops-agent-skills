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

All four models were run with 3 runs per arm and Sonnet 5.5 as the judge, on
the current skill.

| Case                                    | Opus 5.5 with | Opus 5.5 without | Opus 5.5 Δ | Haiku 4.5 with | Haiku 4.5 without | Haiku 4.5 Δ | Haiku 5.5 with | Haiku 5.5 without | Haiku 5.5 Δ | Gemma 4 31B with | Gemma 4 31B without | Gemma 4 31B Δ |
| --------------------------------------- | ------------- | ---------------- | ---------- | -------------- | ----------------- | ----------- | -------------- | ----------------- | ----------- | ---------------- | ------------------- | ------------- |
| `sip-01-blocky-blur`                    | 1.00          | 0.92             | +0.08      | 0.38           | 0.18              | +0.21       | 0.97           | 0.92              | +0.05       | 0.38             | 0.23                | +0.15         |
| `sip-02-outlier-receivers`              | 1.00          | 1.00             | 0.00       | 0.79           | 0.92              | −0.13       | 0.95           | 0.85              | +0.10       | 0.74             | 0.77                | −0.03         |
| `sip-03-tiny-scale-native`              | 1.00          | 0.92             | +0.08      | 0.46           | 0.44              | +0.03       | 0.97           | 0.87              | +0.10       | 0.44             | 0.74                | −0.31         |
| `sip-04-cs-dct`                         | 1.00          | 0.87             | +0.13      | 1.00           | 0.23              | **+0.77**       | 0.87           | 0.90              | −0.03       | 0.74             | 0.64                | +0.10         |
| `sip-05-neg-broken-inversion`           | 1.00          | 1.00             | 0.00       | 1.00           | 0.67              | +0.33       | 1.00           | 1.00              | 0.00        | 1.00             | 1.00                | 0.00          |
| `sip-06-neg-tune-eps`                   | 1.00          | 1.00             | 0.00       | 0.50           | 0.67              | −0.17       | 1.00           | 1.00              | 0.00        | 1.00             | 1.00                | 0.00          |
| **Mean (all cases)**                    |               |                  | **+0.05**  |                |                   | **+0.17**   |                |                   | **+0.04**   |                  |                     | **−0.01**     |
| **Mean (fire cases `sip-01`–`sip-04`)** |               |                  | **+0.07**  |                |                   | **+0.22**   |                |                   | **+0.06**   |                  |                     | **−0.02**     |

| Fire runs | Opus 5.5 with | Opus 5.5 without | Haiku 4.5 with | Haiku 4.5 without | Haiku 5.5 with | Haiku 5.5 without | Gemma 4 31B with | Gemma 4 31B without |
| --------- | ------------- | ---------------- | -------------- | ----------------- | -------------- | ----------------- | ---------------- | ------------------- |
| skill called (`trigger`) | 12/12 | – | 6/12 | – | 8/12 | – | 0/12 | – |
| right prior/solver (`prior-choice`) | 12/12 | 12/12 | 7/12 | 4/12 | 12/12 | 11/12 | 10/12 | 9/12 |
| SNR above the threshold (`snr-threshold`) | 12/12 | 12/12 | 7/12 | 4/12 | 12/12 | 12/12 | 4/12 | 5/12 |
| reports how the solver stopped (`iterations-or-cost`) | 12/12 | 4/12 | 7/12 | 3/12 | 7/12 | 4/12 | 0/12 | 1/12 |
| reports the residual vs the noise level (`residual-vs-noise`) | 12/12 | 9/12 | 4/12 | 0/12 | 8/12 | 6/12 | 0/12 | 0/12 |
| mean score | 1.00 | 0.93 | 0.66 | 0.44 | 0.94 | 0.89 | 0.58 | 0.60 |

`solve-inverse-problem` never fired on the negative cases (0/24 runs with the
plugin across the four models).

Reports:

- Opus 5.5 (`--model claude-opus-5-5`, agent `claude-opus-5-5`):
  [report](results/2026-10-08T22-43-44-530Z/report.html).
- Haiku 4.5 (`--model claude-haiku-4-5-20251001`, agent `claude-haiku-4-5-20251001`):
  [report](results/2026-10-08T22-43-44-411Z/report.html).
- Haiku 5.5 (`--model claude-haiku-5-5`, agent `claude-haiku-5-5`):
  [report](results/2026-10-08T22-31-43-603Z/report.html).
- Gemma 4 31B (`--model gemma4:31b-cloud`, agent `gemma4:31b-cloud`):
  [report](results/2026-10-31T13-51-54-909Z/report.html). One run (`sip-03`,
  with the plugin) ended with `unrecognized_model` from Claude Code and hit the
  40-turn limit; the other 35 runs completed.

### Cost and effort

Mean agent cost per run (USD, **excluding the judge**), mean wall time and mean
turns, from the same runs. The judge (Sonnet 5.5) adds about $0.02–0.11 per
fire run, and up to ~$0.50–0.95 on `sip-06`, whose long traces are expensive
to grade.

| Case                              | Opus 5.5 with      | Opus 5.5 without    | Haiku 4.5 with       | Haiku 4.5 without    | Haiku 5.5 with      | Haiku 5.5 without   | Gemma 4 31B with    | Gemma 4 31B without |
| --------------------------------- | ------------------ | ------------------- | -------------------- | -------------------- | ------------------- | ------------------- | ------------------- | ------------------- |
| `sip-01-blocky-blur`              | $0.32 · 84 s · 8.3 | $0.26 · 75 s · 5.7  | $0.20 · 92 s · 11.3  | $0.18 · 102 s · 7.3  | $0.07 · 77 s · 11.3 | $0.06 · 64 s · 9.3  | $0.56 · 59 s · 32.7 | $0.37 · 44 s · 23.0 |
| `sip-02-outlier-receivers`        | $0.28 · 49 s · 7.3 | $0.19 · 41 s · 3.3  | $0.18 · 101 s · 12.7 | $0.13 · 68 s · 3.3   | $0.07 · 53 s · 10.3 | $0.06 · 46 s · 9.3  | $0.25 · 29 s · 14.7 | $0.20 · 26 s · 9.7  |
| `sip-03-tiny-scale-native`        | $0.33 · 77 s · 7.0 | $0.23 · 50 s · 4.7  | $0.29 · 182 s · 32.3 | $0.34 · 231 s · 35.3 | $0.08 · 72 s · 8.7  | $0.09 · 70 s · 11.7 | $0.51 · 60 s · 29.0 | $0.47 · 53 s · 29.3 |
| `sip-04-cs-dct`                   | $0.27 · 53 s · 8.0 | $0.20 · 41 s · 3.7  | $0.17 · 117 s · 18.0 | $0.19 · 130 s · 18.3 | $0.07 · 39 s · 7.0  | $0.10 · 44 s · 6.0  | $0.33 · 42 s · 19.0 | $0.41 · 50 s · 24.7 |
| `sip-05-neg-broken-inversion`     | $0.20 · 30 s · 4.3 | $0.13 · 23 s · 2.0  | $0.19 · 139 s · 13.3 | $0.07 · 54 s · 1.0   | $0.04 · 29 s · 4.7  | $0.03 · 25 s · 2.7  | $0.10 · 8 s · 2.0   | $0.10 · 10 s · 2.0  |
| `sip-06-neg-tune-eps`             | $0.83 · 75 s · 9.0 | $0.94 · 78 s · 11.0 | $0.45 · 279 s · 13.3 | $0.43 · 60 s · 5.3   | $0.65 · 60 s · 12.3 | $0.13 · 36 s · 4.3  | $0.23 · 28 s · 5.7  | $0.27 · 22 s · 3.7  |
| **Fire cases, sum per run**       | **$1.20**          | **$0.88**           | **$0.84**            | **$0.84**            | **$0.30**           | **$0.30**           | **$1.65**           | **$1.45**           |
| **Whole suite, all runs per arm** | **$6.66**          | **$5.87**           | **$4.43**            | **$4.01**            | **$2.95**           | **$1.36**           | **$5.92**           | **$5.47**           |

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

**Gemma 4 31B does not use the skill.** It loaded it in 0 of 12 fire runs, so
the plugin has no effect: the mean fire score is 0.58 with the plugin and 0.60
without (Δ −0.02, within run-to-run noise). It picks a reasonable prior in
10/12 runs with the plugin (9/12 without), but rarely reaches the SNR
threshold (4/12 vs 5/12) and never reports the residual vs the noise level
(0/12 in both arms), the part of the workflow that the skill adds for the
other models. On the negative cases it does not fire the skill either (0/6)
and scores 1.00. A fire run costs more than for any Claude model in this table
($1.65 with, $1.45 without) because it needs 15–33 turns per run (Opus 5.5:
4–8). Whether this is a model limitation or a tool-calling problem with this
model through Claude Code (note the `unrecognized_model` error) is not
established.

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

All three models were run with 3 runs per arm and Sonnet 5.5 as the judge, on
the current skill.

| Case | Opus 5.5 with | Opus 5.5 without | Opus 5.5 Δ | Haiku 4.5 with | Haiku 4.5 without | Haiku 4.5 Δ | Haiku 5.5 with | Haiku 5.5 without | Haiku 5.5 Δ |
| ---- | ------------- | ---------------- | ---------- | -------------- | ----------------- | ----------- | -------------- | ----------------- | ----------- |
| `dbg-01-custom-adjoint-conv` | 1.00 | 1.00 | 0.00 | 0.87 | 0.87 | 0.00 | 1.00 | 1.00 | 0.00 |
| `dbg-02-vstack-missing-conj` | 1.00 | 1.00 | 0.00 | 0.53 | 0.47 | +0.07 | 1.00 | 0.87 | +0.13 |
| `dbg-03-complex-dtype-funcop` | 1.00 | 1.00 | 0.00 | 1.00 | 1.00 | 0.00 | 1.00 | 1.00 | 0.00 |
| `dbg-04-scaling-stacked-blocks` | 0.83 | 1.00 | −0.17 | 1.00 | 0.50 | +0.50 | 0.83 | 0.67 | +0.17 |
| `dbg-05-fista-eps-prose` | 1.00 | 1.00 | 0.00 | 0.17 | 0.50 | −0.33 | 1.00 | 1.00 | 0.00 |
| `dbg-06-physics-limited` | 1.00 | 0.83 | +0.17 | 0.50 | 0.33 | +0.17 | 0.83 | 0.83 | 0.00 |
| `dbg-07-two-bugs` | 1.00 | 1.00 | 0.00 | 1.00 | 0.53 | +0.47 | 1.00 | 1.00 | 0.00 |
| `dbg-08-neg-which-solver` | 1.00 | 1.00 | 0.00 | 0.83 | 1.00 | −0.17 | 1.00 | 1.00 | 0.00 |
| `dbg-09-neg-scipy-minimize` | 1.00 | 1.00 | 0.00 | 0.89 | 1.00 | −0.11 | 1.00 | 1.00 | 0.00 |
| **Mean (all cases)** | | | **0.00** | | | **+0.07** | | | **+0.03** |
| **Mean (fire cases `dbg-01`–`dbg-07`)** | | | **0.00** | | | **+0.12** | | | **+0.04** |

| Fire runs | Opus 5.5 with | Opus 5.5 without | Haiku 4.5 with | Haiku 4.5 without | Haiku 5.5 with | Haiku 5.5 without |
| --------- | ------------- | ---------------- | -------------- | ----------------- | -------------- | ----------------- |
| skill called (`trigger`) | 21/21 | – | 21/21 | – | 21/21 | – |
| correct diagnosis (`diagnosis`) | 21/21 | 21/21 | 13/21 | 6/21 | 20/21 | 18/21 |
| no fabricated values (`no-fabrication`) | 20/21 | 20/21 | 17/21 | 19/21 | 20/21 | 20/21 |
| mean score | 0.98 | 0.98 | 0.72 | 0.60 | 0.95 | 0.91 |

`debug-inversion` never fired on the negative cases (0/18 runs with the plugin
across the three models).

Reports:

- Opus 5.5 (`--model claude-opus-5-5`, agent `claude-opus-5-5`):
  [report](results/2026-10-09T08-23-36-827Z/report.html).
- Haiku 4.5 (`--model claude-haiku-4-5-20251001`, agent `claude-haiku-4-5-20251001`):
  [report](results/2026-10-09T08-44-17-973Z/report.html).
- Haiku 5.5 (`--model claude-haiku-5-5`, agent `claude-haiku-5-5`):
  [report](results/2026-10-09T08-23-36-776Z/report.html).

### Cost and effort

Mean agent cost per run (USD, **excluding the judge**), mean wall time and mean
turns, from the same runs. The judge (Sonnet 5.5) adds about $0.07–0.48 per
fire run and $0.00–0.12 per negative run.

| Case | Opus 5.5 with | Opus 5.5 without | Haiku 4.5 with | Haiku 4.5 without | Haiku 5.5 with | Haiku 5.5 without |
| ---- | ------------- | ---------------- | -------------- | ----------------- | -------------- | ----------------- |
| `dbg-01-custom-adjoint-conv` | $0.43 · 44 s · 4.0 | $0.29 · 30 s · 2.0 | $0.32 · 99 s · 13.0 | $0.25 · 66 s · 8.3 | $0.23 · 42 s · 8.0 | $0.16 · 26 s · 2.7 |
| `dbg-02-vstack-missing-conj` | $0.34 · 43 s · 4.0 | $0.26 · 33 s · 2.0 | $0.41 · 119 s · 9.7 | $0.20 · 67 s · 1.7 | $0.20 · 41 s · 7.3 | $0.24 · 32 s · 2.7 |
| `dbg-03-complex-dtype-funcop` | $0.41 · 47 s · 6.0 | $0.29 · 40 s · 4.0 | $0.22 · 50 s · 8.0 | $0.29 · 34 s · 6.0 | $0.36 · 61 s · 10.0 | $0.22 · 29 s · 4.3 |
| `dbg-04-scaling-stacked-blocks` | $0.44 · 57 s · 5.0 | $0.27 · 42 s · 2.3 | $0.30 · 102 s · 8.0 | $0.12 · 26 s · 1.0 | $0.18 · 53 s · 5.7 | $0.27 · 51 s · 3.3 |
| `dbg-05-fista-eps-prose` | $0.37 · 41 s · 4.0 | $0.18 · 31 s · 1.0 | $0.45 · 104 s · 11.0 | $0.17 · 20 s · 1.0 | $0.31 · 41 s · 5.3 | $0.17 · 25 s · 1.0 |
| `dbg-06-physics-limited` | $0.42 · 50 s · 4.7 | $0.29 · 38 s · 3.0 | $0.39 · 173 s · 14.3 | $0.26 · 47 s · 2.3 | $0.24 · 55 s · 6.3 | $0.19 · 39 s · 3.3 |
| `dbg-07-two-bugs` | $0.35 · 46 s · 4.0 | $0.23 · 31 s · 2.0 | $0.31 · 114 s · 13.0 | $0.26 · 68 s · 6.3 | $0.28 · 55 s · 8.3 | $0.22 · 49 s · 3.3 |
| `dbg-08-neg-which-solver` | $0.20 · 33 s · 4.0 | $0.12 · 23 s · 1.0 | $0.09 · 38 s · 6.0 | $0.06 · 16 s · 1.0 | $0.02 · 16 s · 3.3 | $0.05 · 14 s · 1.0 |
| `dbg-09-neg-scipy-minimize` | $0.13 · 20 s · 1.0 | $0.11 · 20 s · 1.0 | $0.04 · 17 s · 1.0 | $0.04 · 16 s · 1.0 | $0.01 · 15 s · 1.0 | $0.02 · 14 s · 1.0 |
| **Fire cases, sum per run** | **$2.76** | **$1.83** | **$2.39** | **$1.54** | **$1.80** | **$1.48** |
| **Whole suite, 3 runs per arm** | **$9.27** | **$6.18** | **$7.56** | **$4.92** | **$5.51** | **$4.63** |

- With the plugin a fire run costs about 50% more for Opus 5.5 and 55% more
  for Haiku 4.5, and about 20% more for Haiku 5.5, mostly from loading the
  skill and the extra turns it asks for (reproducing the problem, dot-tests,
  testing the fix).
- For Opus 5.5 the extra cost buys a check-by-check report but not a better
  diagnosis; for Haiku 4.5 it buys more correct diagnoses; for Haiku 5.5 a few.

### Findings

**The description says when to load the skill.** It asks to load it first,
"before running the user's code, testing a hypothesis or answering, even when
the bug looks obvious from the code". Haiku 5.5 otherwise ran the user's script
or answered directly as soon as it saw the bug, and loaded the skill in only
8/21 fire runs; with the current wording it loads it in 21/21, and the negative
cases still never fire it.

**Opus 5.5 does not need the skill.** Both arms get every diagnosis right
(21/21). Without the plugin Opus 5.5 runs the user's script once or twice and
answers in 1–4 turns, including both bugs in `dbg-07` and "no bug,
physics-limited" in `dbg-06`; with the plugin it does the same work as a
check-by-check report in 4–6 turns. The two `no-fabrication` failures (one per
arm) are discussed in Known limitations.

**Haiku 4.5 gets more diagnoses right with the skill, but the suite stays hard
for it.** Correct diagnoses rise from 6/21 to 13/21 fire runs:

| Haiku 4.5, correct diagnosis | with | without |
| ---------------------------- | ---- | ------- |
| `dbg-01` wrong adjoint slice | 3/3 | 2/3 |
| `dbg-02` missing conjugate | 0/3 | 0/3 |
| `dbg-03` missing complex dtype | 3/3 | 3/3 |
| `dbg-04` block scaling | 3/3 | 0/3 |
| `dbg-05` `eps` too large (prose) | 0/3 | 0/3 |
| `dbg-06` physics-limited, no bug | 1/3 | 0/3 |
| `dbg-07` two bugs | 3/3 | 1/3 |

- The gains are on the cases where the skill's procedure adds a measurement:
  the block norms in `dbg-04` (without the plugin Haiku 4.5 answers in one turn
  and fails all three) and the second bug in `dbg-07`.
- `dbg-05` fails in both arms: Haiku 4.5 compares `eps` with the data amplitude
  instead of the critical value max|Opᴴy|, and with the plugin 2/3 reports
  quote thresholds that the run does not support (`no-fabrication` 1/3).
- `no-fabrication` fails 4/21 runs with the plugin (`dbg-01`, `dbg-05` twice,
  `dbg-06`) and 2/21 without.
- `dbg-08`: in 1/3 runs with the plugin Haiku 4.5 started writing a demo
  script instead of recommending a solver and hit the 8-turn limit.

**Haiku 5.5 does not need the skill, but now always uses it.** It gets 18/21
diagnoses right without the plugin and 20/21 with it, close to Opus 5.5,
including the cases Haiku 4.5 does not solve (`dbg-05`, `dbg-06`):

| Haiku 5.5, correct diagnosis | with | without |
| ---------------------------- | ---- | ------- |
| `dbg-01` wrong adjoint slice | 3/3 | 3/3 |
| `dbg-02` missing conjugate | 3/3 | 2/3 |
| `dbg-03` missing complex dtype | 3/3 | 3/3 |
| `dbg-04` block scaling | 2/3 | 2/3 |
| `dbg-05` `eps` too large (prose) | 3/3 | 3/3 |
| `dbg-06` physics-limited, no bug | 3/3 | 2/3 |
| `dbg-07` two bugs | 3/3 | 3/3 |

- The remaining failures are borderline grades (see Known limitations): two
  `dbg-04` answers (one per arm) ranked the stopping test of `cgls` above the
  block scaling, one `dbg-02` answer gave a correct fix without a complex
  dot-test, and one `dbg-06` answer blamed the L2 prior without naming the
  missing frequencies.
- With the plugin its runs take 5–10 turns instead of 1–4 and cost about 20%
  more.

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
  elided…"), and runs with the plugin are longer (Haiku 4.5: 8–14 turns vs 1–8,
  Haiku 5.5: 5–10 vs 1–4, Opus 5.5: 4–6 vs 1–4). `no-fabrication` therefore
  does not treat a value missing from the visible trace as fabricated: it fails
  only a claim of running code with no tool call at all, or a value presented
  as measured that contradicts a visible tool result. Earlier, stricter
  wordings failed long runs whose measured values sat in elided tool results
  (every such failure checked by hand was a false positive) and correct
  one-turn answers that derived their numbers from the prompt. The current
  check is weaker at catching invented numbers inside elided sections.
- `no-fabrication` still fails some runs whose visible trace shows no
  contradicting value: Opus 5.5 on `dbg-04` with the plugin (split vote; the
  unmatched values are ratios of measured ones) and Haiku 5.5 on `dbg-04`
  without and `dbg-06` with the plugin (the values match the run's own notes
  before an elided section). One Opus 5.5 failure is real: on `dbg-06` without
  the plugin it states "the dot-test also passes" but never ran one.
- `dbg-04` has a second, measurable explanation: `cgls` with its default
  absolute `tol` stops with `istop=1` after ~60 iterations, and `tol=0` lowers
  the model error without any weighting. Answers that rank this first and the
  block scaling second fail criterion 5 of the rubric, which makes these grades
  borderline.
- `dbg-02` asks for a complex dot-test (`complexflag`) when one is cited, so a
  correct fix with a plain dot-test can fail the diagnosis; its `fix-token`
  regex also misses the equivalent fix `y @ self.A.conj()`.
- The judges' reasoning is not stored in `aggregate-result.json` (only the
  votes); use `--keep-temp` to keep the traces for spot checks.
- `dbg-08` grades the answer quality, which with the plugin installed can be
  influenced by `solve-inverse-problem` (asking clarifying questions or writing
  a demo instead of answering, which can hit the 8-turn limit).
- Haiku 4.5 varies a lot between runs: repeating its run with the same skill
  moves single cases by up to ±0.5 (e.g. the Δ of `dbg-04` and `dbg-05`), so
  read its per-case Δs as indicative and its 21-run totals as the result.
