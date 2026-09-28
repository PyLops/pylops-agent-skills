---
type: llm
focus:
  source: file
  path: invert.py
weight: 0.125
---
You are shown the script `invert.py`. Trace the data flow of the true model (`xtrue`, `x1`/`x2`, or `Xtrue`, whichever the script uses as ground truth) through it.

Claim: no value computed from the true model flows into the computation of the inverted model — i.e. it is not passed (directly or via a derived variable) into the solver call, the forward operator, the regulariser or its weight, the initial guess, data/model weights, or a support/mask/rank computed from the true model.

Allowed uses that do NOT break the claim: generating the synthetic data; computing the SNR; computing errors, supports, ranks or other quantities of the true model that are only printed as diagnostics; printing oracle comparisons as separate checks. Using information the user states as known (the blur kernel, the noise level 0.01, the 3×3 median filter) is also allowed. Choosing a regularisation weight, `tau` or iteration count by maximising the SNR against `xtrue` makes the claim FALSE.

Answer FAIL only if you can name the specific line where a value derived from the true model enters the computation of the inverted model. Otherwise PASS.
