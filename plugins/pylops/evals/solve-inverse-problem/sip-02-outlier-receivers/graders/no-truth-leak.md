---
type: llm
focus:
  source: file
  path: invert.py
weight: 0.5
---
You are shown the script `invert.py`. Trace the data flow of `xtrue` or `bad` through it.

Claim: no value computed from `xtrue` or `bad` flows into the computation of `xinv` — i.e. it is not passed (directly or via a derived variable) into the solver call, the forward operator, the regulariser, `x0`, data/model weights, or the support/mask used to compute `xinv`.

Allowed uses that do NOT break the claim: generating the synthetic data `y`; computing the SNR; computing transforms, errors, supports or other quantities of `xtrue` or `bad` that are only printed or saved as diagnostics; printing oracle comparisons as separate checks. Using the noise level stated in the prompt (e.g. a noise standard deviation or a fraction of max|d|, even when the script computes it from the clean data) — for example to set a discrepancy-principle target or a tolerance — is also allowed: that information is given to the user, not leaked from the true model.

Answer FAIL only if you can name the specific line where a value derived from `xtrue` or `bad` enters the computation of `xinv`. Otherwise PASS.
