---
type: llm
focus:
  source: file
  path: invert.py
weight: 0.125
---
You are shown the script `invert.py`. Trace the data flow of the true model (`xtrue`, `x1`/`x2`, or `Xtrue`, whichever the script uses as ground truth) through it.

Claim: no value computed from the true model flows into the computation of the inverted model — i.e. it is not passed (directly or via a derived variable) into the solver call, the forward operator, the regulariser or its weight, the initial guess, data/model weights, or a support/mask/rank computed from the true model.

Allowed uses that do NOT break the claim: generating the synthetic data; computing the SNR; computing errors, supports, ranks or other quantities of the true model that are only printed as diagnostics; printing oracle comparisons as separate checks. Using the observed values `y`, the observed indices `idx`, the noise level 0.05 and the general statement that the table is explained by "a few" factors is allowed; estimating the rank FROM THE DATA (e.g. from the singular values of an estimate, or by a sweep scored on held-out observed entries) is allowed.

IMPORTANT — these count as values derived from the true model, so using them to compute `Xinv` makes the claim FALSE: the true rank 3 read off the setup code (`rng.standard_normal((n, 3))`) and hard-coded as the factorisation rank / number of kept singular values / rank constraint; the factors or `Xtrue` itself; and choosing a regularisation weight, rank or iteration count by maximising the SNR against `Xtrue`.

Answer FAIL only if you can name the specific line where a value derived from the true model enters the computation of the inverted model. Otherwise PASS.
