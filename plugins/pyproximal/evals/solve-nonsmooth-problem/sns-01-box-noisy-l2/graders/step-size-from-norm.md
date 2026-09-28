---
type: llm
focus:
  source: file
  path: invert.py
weight: 1
---
You are shown the script `invert.py`.

Claim: every step size of the iterative solver used for the final model (`tau`, `mu`, `alpha`, a learning rate, …) is derived from a quantity computed or justified for this operator — the Lipschitz constant / squared operator norm ‖Op‖² (or ‖K‖² for a stacked operator) obtained with power iteration, `eigs`, an SVD/`np.linalg.norm` of the explicit matrix, or an analytic bound written in a comment (e.g. "a normalised blur kernel has ‖Op‖ ≤ 1") — or the solver uses backtracking / line search (e.g. `tau=None` in `pyproximal.optimization.primal.ProximalGradient`). A solver that needs no step size (e.g. scipy `lsq_linear`, a direct solve) also makes the claim TRUE.

The claim is FALSE if a step size is a hard-coded number (e.g. `tau=0.1`, `tau=1.0`) with no computation or written justification tied to the operator norm.

Answer PASS if this single claim is true, otherwise FAIL. Judge only this claim.
