---
type: llm
focus: last_message
weight: 1
---
Score PASS only if ALL of the following hold for the final answer:
1. It recommends at least one sparsity-promoting PyLops solver (e.g. fista, ista, spgl1, omp, irls, splitbregman) and gives a reason tied to the sparse reflectivity.
2. It treats the question as solver selection for a new setup. It does NOT frame the answer as diagnosing a broken inversion: no "findings" section, no ranked list of suspected bugs, and no refusal to recommend a solver until diagnostics are run. A one-line sanity dot-test in example setup code, or a tip on choosing eps, is fine and does not fail this criterion.
Otherwise FAIL.
