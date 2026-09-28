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
| `no-fabrication` | LLM, trace | 1 | no claims of runs that did not happen, and no measured values that no tool call produced |
| `fix-token` | regex, final answer | 0.5 | the key fix in the answer (e.g. `nh - 1` or `Convolve1D`, a conjugate transpose, `dtype=complex`, a reversed cumsum); `dbg-01`–`03` and `dbg-07` only |
| `trigger` | `tool_used: Skill` | – | display only under ablation (not scored) |

The negative cases check that the skill is not called (`tool_used`, max 0) and
grade the answer to the actual question; `dbg-09` also fails if the answer
mentions PyLops. The judge is Sonnet (`--judge-model sonnet`).

### Results

Both models were run with 3 runs per arm and Sonnet as the judge.

| Case | Opus with | Opus without | Opus Δ | Haiku with | Haiku without | Haiku Δ |
| ---- | --------- | ------------ | ------ | ---------- | ------------- | ------- |
| `dbg-01-custom-adjoint-conv` | 1.00 | 1.00 | 0.00 | 0.60 | 0.87 | −0.27 |
| `dbg-02-vstack-missing-conj` | 1.00 | 1.00 | 0.00 | 0.87 | 0.73 | +0.13 |
| `dbg-03-complex-dtype-funcop` | 0.73 | 1.00 | −0.27 | 0.73 | 1.00 | −0.27 |
| `dbg-04-scaling-stacked-blocks` | 0.83 | 1.00 | −0.17 | 0.67 | 0.50 | +0.17 |
| `dbg-05-fista-eps-prose` | 1.00 | 1.00 | 0.00 | 0.50 | 0.50 | 0.00 |
| `dbg-06-physics-limited` | 1.00 | 1.00 | 0.00 | 0.17 | 0.67 | −0.50 |
| `dbg-07-two-bugs` | 1.00 | 1.00 | 0.00 | 0.87 | 0.67 | +0.20 |
| `dbg-08-neg-which-solver` | 1.00 | 1.00 | 0.00 | 0.67 | 1.00 | −0.33 |
| `dbg-09-neg-scipy-minimize` | 0.89 | 1.00 | −0.11 | 0.89 | 1.00 | −0.11 |
| **Mean (all cases)** | | | **−0.06** | | | **−0.11** |
| **Mean (fire cases `dbg-01`–`dbg-07`)** | | | **−0.06** | | | **−0.08** |

| Fire runs | Opus with | Opus without | Haiku with | Haiku without |
| --------- | --------- | ------------ | ---------- | ------------- |
| correct diagnosis (`diagnosis`) | 20/21 | 21/21 | 14/21 | 11/21 |
| no fabricated values (`no-fabrication`) | 19/21 | 21/21 | 11/21 | 18/21 |
| skill called (`trigger`) | 19/21 | – | 21/21 | – |

Reports:

- Opus (`--model opus`, agent `claude-opus-5-5`):
  [report](results/2026-09-27T22-35-20-518Z/report.html).
- Haiku (`--model haiku`):
  [report](results/2026-09-28T06-39-54-183Z/report.html).

### Cost and effort

Mean agent cost per run (USD, **excluding the judge**), mean wall time and mean
turns, from the same runs. The judge (Sonnet) adds about $0.10–0.35 per fire run.

| Case | Opus with | Opus without | Haiku with | Haiku without |
| ---- | --------- | ------------ | ---------- | ------------- |
| `dbg-01-custom-adjoint-conv` | $0.29 · 27 s · 2.7 | $0.24 · 23 s · 2.0 | $0.34 · 176 s · 20.0 | $0.17 · 62 s · 5.7 |
| `dbg-02-vstack-missing-conj` | $0.30 · 32 s · 4.0 | $0.23 · 26 s · 2.0 | $0.39 · 129 s · 9.3 | $0.22 · 79 s · 3.0 |
| `dbg-03-complex-dtype-funcop` | $0.61 · 72 s · 6.7 | $0.31 · 29 s · 3.0 | $0.26 · 72 s · 10.3 | $0.23 · 33 s · 5.7 |
| `dbg-04-scaling-stacked-blocks` | $0.48 · 50 s · 6.0 | $0.22 · 30 s · 2.0 | $0.26 · 119 s · 9.7 | $0.19 · 48 s · 3.3 |
| `dbg-05-fista-eps-prose` | $0.36 · 40 s · 4.3 | $0.23 · 31 s · 1.0 | $0.50 · 102 s · 16.0 | $0.17 · 21 s · 1.0 |
| `dbg-06-physics-limited` | $0.33 · 39 s · 4.3 | $0.36 · 42 s · 3.0 | $0.59 · 147 s · 11.7 | $0.21 · 61 s · 4.3 |
| `dbg-07-two-bugs` | $0.38 · 37 s · 4.0 | $0.22 · 27 s · 2.0 | $0.29 · 101 s · 9.7 | $0.17 · 38 s · 3.0 |
| `dbg-08-neg-which-solver` | $0.18 · 23 s · 4.0 | $0.11 · 21 s · 1.0 | $0.05 · 25 s · 5.0 | $0.03 · 14 s · 1.0 |
| `dbg-09-neg-scipy-minimize` | $0.13 · 17 s · 1.0 | $0.11 · 18 s · 1.0 | $0.04 · 17 s · 1.0 | $0.04 · 14 s · 1.0 |
| **Fire cases, sum per run** | **$2.76** | **$1.81** | **$2.63** | **$1.35** |
| **Whole suite, 3 runs per arm** | **$9.19** | **$6.11** | **$8.16** | **$4.26** |

- With the plugin a fire run costs about 50% more for Opus and 95% more for
  Haiku, mostly from loading the skill and the extra turns it asks for
  (reproducing the problem, dot-tests, testing the fix).
- For Opus the extra cost buys longer, more systematic reports but no better
  diagnosis (see Findings); for Haiku it buys a few more correct diagnoses.

### Findings

**Opus does not need the skill.** Without the plugin, Opus gives the right
diagnosis in 21/21 fire runs, usually after running the user's script once
(2–3 turns), including both bugs in `dbg-07` and "no bug, physics-limited" in
`dbg-06`, and passes `no-fabrication` in 21/21. With the plugin it does the
same work in a more systematic report (4–7 turns), and the Δ is slightly
negative (−0.06) because of grader artefacts rather than worse answers:

- `dbg-03` (−0.27): two runs with the plugin failed `no-fabrication`. In the
  run checked by hand, every number in the report (‖Op‖, the relative error,
  18/60 significant singular values, the `epsR` sweep) is in the tool output,
  but the tool result holding most of them was elided from the trace the
  judge saw (see Known limitations).
- `dbg-04` (−0.17): one run with the plugin failed the diagnosis although it
  weighted the blocks by 1/σ and verified model error 0.001. It explained that
  the gravity block alone leaves a null space that only dataset 1 can
  constrain, which the judge read as blaming the null space. The rubric has
  since been reworded to allow this explanation.
- `dbg-01`: in 2/3 runs with the plugin Opus answered directly without calling
  the skill (and passed).
- `dbg-09` (−0.11): as for Haiku, one answer with the plugin mentioned PyLops
  for a SciPy question.

**For Haiku the skill improves the diagnosis, but the score does not show
it.** The correct diagnosis rises from 11/21 to 14/21 fire runs, but
`no-fabrication` falls from 18/21 to 11/21, so the mean Δ is negative
(−0.08 on fire cases). The `no-fabrication` drop is a grader artefact, not
fabrication: Haiku runs with the plugin are long (10–20 turns), the trace the
judge sees is truncated, and the tool results holding the measured values are
among the elided messages. In the failed runs checked by hand (`dbg-03`,
`dbg-06`) every number in the report was in the tool output (see Known
limitations).

Diagnosis, case by case:

- `dbg-07`: with the skill Haiku reports both bugs in 3/3 runs; without it,
  1/3 (the others fix only the adjoint or only the scaling).
- `dbg-04`: with the skill Haiku measures the block and data norms and weights
  by 1/σ (2/3); without it, 1/3 (one run concludes that dataset 1 is
  "fundamentally underdetermined").
- `dbg-02`: 3/3 with the skill, 2/3 without.
- `dbg-06`: 1/3 with the skill, 2/3 without; with the skill Haiku spends its
  turns on sweeps and sometimes presents LSQR semi-convergence or damping as
  the problem.
- `dbg-05` (prose only): 0/3 in both arms; Haiku finds that `eps` is too large
  but does not compare it with `max|Opᴴy|` quantitatively.

Parts of the skill that matter for Haiku (each fixes a failure seen with an
earlier version of the skill):

- An explicit "carry out these steps yourself, now" paragraph. Without it,
  Haiku often ended its turn right after loading the skill ("the skill is
  running diagnostics in the background… I'll report back") with no answer;
  with it, this happened in 0/21 fire runs.
- For prose-only reports such as `dbg-05`, reasoning from the numbers or
  building a reproduction instead of stopping to ask for the script.
- Continuing through the remaining checks after one fails, instead of
  stopping at the first: otherwise Haiku stops after the wrong adjoint in
  `dbg-07` and misses the block scaling.
- A report that separates checks that were run from checks that were not, and
  tested fixes from untested ones. Without it, Haiku filled in checks it never
  ran (e.g. "both blocks pass the dot-test" when only the full operator was
  tested) and concluded "physically limited" after a weighting fix it had
  implemented wrongly.

Other observations:

- `dbg-01`, `dbg-03`: Haiku without the plugin already finds the bug by
  running the script (off-by-one slice, missing dtype); with the plugin it
  finds it too, and the negative Δ comes from `no-fabrication`.
- `dbg-08`: in 2/3 runs with the plugin Haiku asked clarifying questions
  instead of recommending a solver (influence of `solve-inverse-problem`, not
  `debug-inversion`, which was not called).
- The arm without the plugin varies between runs (11/21 correct diagnoses
  here, 7/21 and 12/21 in earlier runs), so read single-case Δs with care.

### Known limitations of the graders

- The runs need PyLops as a regular (non-editable) install first on `PATH`; see
  the repository README. With an editable install, runs fail with
  `No module named 'pylops'` and cannot measure anything.
- The trace passed to the `no-fabrication` judge is truncated for long runs
  ("…N messages elided…"). Runs with the plugin are longer (Haiku 10–20 turns
  vs 1–6, Opus 4–7 vs 2–3), so a value whose tool output was elided is more
  often judged unsupported. This is the main limitation of the suite: it
  causes most `no-fabrication` failures with the plugin (Haiku 10/21, Opus
  2/21; all runs checked by hand were false positives) and makes the Haiku Δ
  negative. A fix is to tell the judge that numbers may come from elided tool
  results and to fail only on a visible contradiction or a claim of running
  code with no tool call at all.
- `no-fabrication` distinguishes values presented as measured (must match a
  tool result) from values derived from the prompt or labelled as estimates
  (always allowed). An earlier, stricter wording also failed correct one-turn
  answers that derived their numbers from the prompt.
- The `dbg-04` diagnosis criterion against "physics-limited" conclusions was
  reworded after the Opus run (the Haiku run uses the current wording) to allow the (correct) explanation that the gravity
  block alone leaves a null space only dataset 1 can constrain. Under the
  current wording one Opus run with the plugin would likely pass (Opus
  `dbg-04` with ~1.00).
- The judges' reasoning is not stored in `aggregate-result.json` (only the
  votes); use `--keep-temp` to keep the traces for spot checks.
- `dbg-08` grades the answer quality, which with the plugin installed can be
  influenced by `solve-inverse-problem` (asking clarifying questions instead of
  answering, which can hit the 8-turn limit).
