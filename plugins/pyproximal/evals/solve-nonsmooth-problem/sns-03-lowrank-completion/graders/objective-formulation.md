---
type: llm
focus: last_message
weight: 1
---
Claim: the final answer writes down the optimisation problem it solved explicitly — as a formula or an unambiguous statement of the terms — and that problem is a low-rank matrix completion: a data term only on the OBSERVED entries (e.g. ½‖R vec(X) − y‖² with a restriction / sampling operator or mask) plus a low-rank prior on the whole matrix — a nuclear-norm penalty (e.g. `pyproximal.Nuclear`, singular-value soft-thresholding) or an explicit rank constraint / factorisation X = U Vᵀ with a small rank (hard singular-value thresholding, alternating least squares).

The claim is FALSE if: the missing entries are filled with zeros, a mean, interpolation or plain least squares / Tikhonov without a low-rank prior; the data term includes the unobserved entries as zeros (i.e. fits the zero-filled matrix); or the answer never states the objective it minimised. Showing such baselines only as a comparison is fine.

In addition, the final model must be computed with a proximal algorithm from PyProximal — a solver in `pyproximal.optimization` (ProximalGradient, ADMM, ADMML2, LinearizedADMM, PrimalDual, …) with PyProximal proximal operators. A final model obtained another way makes the claim FALSE even if the formulation is right: e.g. scipy (L-BFGS-B, `lsq_linear`), cvxpy, a PyLops-only solver (fista, spgl1, omp), or a hand-written iterative loop.

Answer PASS if this single claim is true, otherwise FAIL. Judge only this claim; ignore everything else about the answer.
