---
type: llm
focus:
  source: file
  path: invert.py
weight: 1
---
You are shown the script `invert.py`.

Claim: the step size / penalty parameter of the solver used for the final image is set in a justified way for this operator:
- for a gradient-type solver (ProximalGradient, or PlugAndPlay with a gradient step on the data term): `tau` is derived from the Lipschitz constant ‖Op‖² computed with power iteration / `eigs` / an analytic bound written in a comment (e.g. "a normalised blur kernel has ‖Op‖ ≤ 1"), or backtracking is used (`tau=None`);
- for ADMM / HQS / Douglas-Rachford (where `tau` is a penalty parameter and there is no Lipschitz condition when the data-term prox is solved exactly): `tau` is chosen by a stated rule tied to the problem (e.g. relative to ‖Op‖², the noise level, or the denoiser strength) or by a small sweep in the script, and the code or a comment says so.

The claim is FALSE if the step size / penalty parameter is a hard-coded number (e.g. `tau=1.0`) with no computation, sweep or written justification.

Answer PASS if this single claim is true, otherwise FAIL. Judge only this claim.
