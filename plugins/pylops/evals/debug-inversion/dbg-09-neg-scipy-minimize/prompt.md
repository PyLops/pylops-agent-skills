---
max_turns: 8
timeout_seconds: 120
allowed_tools: [Skill, Read, Glob, Grep]
runs: 3
---
My logistic regression trained with `scipy.optimize.minimize(loss, w0, jac=grad, method="BFGS")` doesn't converge: it stops with "Desired error not necessarily achieved due to precision loss" and the weights keep growing if I raise maxiter. Features are raw (some in the thousands, some around 0.01). What should I check?
