---
type: llm
focus: last_message
weight: 1
---
Claim: the final estimate comes from a robust treatment of outliers in the data — an L1/Huber-type data misfit (e.g. `irls(..., kind="data")`), or outlier rejection based on the residuals of such a robust fit (optionally followed by a least-squares refit on the kept data) — and the answer says this is needed because some readings are outliers. Plain least squares on all data as the final answer makes this FALSE.

Answer PASS if this single claim is true, otherwise FAIL. Judge only this claim; ignore everything else about the answer.
