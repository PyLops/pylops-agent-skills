---
type: llm
focus:
  source: file
  path: invert.py
weight: 0.125
---
You are shown the script `invert.py`. Trace the data flow of the true model (`xtrue`, `x1`/`x2`, or `Xtrue`, whichever the script uses as ground truth) through it.

Claim: no value computed from the true model flows into the computation of the inverted model — i.e. it is not passed (directly or via a derived variable) into the solver call, the forward operator, the regulariser or its weight, the initial guess, data/model weights, or a support/mask/rank computed from the true model.

Allowed uses that do NOT break the claim: generating the synthetic data; computing the SNR; computing errors, supports, ranks or other quantities of the true model that are only printed as diagnostics; printing oracle comparisons as separate checks. Using the observed samples, the sampling indices `iava1`/`iava2`, the operators, the noise level 0.01 and the general statement that the two signals share the same few DCT components is allowed.

IMPORTANT — these count as values derived from the true model, so using them to compute `x1inv`/`x2inv` makes the claim FALSE: the true component indices `icomp` (e.g. building a basis or a support from them, or restricting the solve to those components), the true amplitudes `amps1`/`amps2`, the true coefficients `X1`/`X2`, the true number of active components used as a hard constraint (e.g. `L01Ball(..., 6)` or keeping the 6 largest coefficients because the setup has 6 components), and choosing a regularisation weight, threshold or iteration count by maximising the SNR against `x1`/`x2`.

Answer FAIL only if you can name the specific line where a value derived from the true model enters the computation of the inverted model. Otherwise PASS.
