---
type: llm
focus: last_message
weight: 0.125
---
Claim: the final answer does NOT report that any parameter of the final reconstruction (a regularisation weight, threshold, step size / penalty parameter, rank, support, number of iterations, filter size, …) was chosen, tuned or selected by comparing against the true model `Xtrue` (or the rank 3 read off the setup code) — e.g. "I picked λ with the best SNR against xtrue", "tau=5 was chosen by SNR against the truth", "oracle tuning", a sweep whose selection criterion is the SNR / error w.r.t. the true model.

Reporting the SNR against the true model as the final quality metric, or showing an SNR-vs-parameter table as a diagnostic while the parameter was actually chosen by a criterion that does not use the true model (discrepancy principle, residual vs noise level, held-out observed data, L-curve, a stated scale argument), does NOT break the claim.

Answer PASS if this single claim is true, otherwise FAIL. Judge only this claim; ignore everything else about the answer.
