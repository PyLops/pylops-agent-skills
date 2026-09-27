---
max_turns: 40
timeout_seconds: 900
allowed_tools: [Skill, Read, Glob, Grep, Write, Bash]
runs: 3
---
I'm setting up a 1-D gravity-style inversion with PyLops. In SI units the forward operator is `Op = 6.674e-11 * pylops.signalprocessing.Convolve1D(200, h=h, offset=30)` with `h = np.exp(-0.5 * (t / 8)**2)` for integer t from −30 to 30 (not normalised). The model is a density contrast in kg/m³: `xtrue = 300 * exp(-0.5 * ((z - 90) / 15)**2) - 150 * exp(-0.5 * ((z - 150) / 10)**2)` with `z = np.arange(200)`. The data are `d = Op @ xtrue` plus Gaussian noise with standard deviation 1% of `max|d|`, drawn with `np.random.default_rng(0)`.

The model is expected to be smooth. Important constraint: the inversion must stay PyLops-native (PyLops' own solvers, not scipy's), because we will move this to CuPy later. Keep the model in kg/m³ in the output. Please write a runnable Python script for this, saved as `invert.py` in the current folder, run it, and tell me what you chose and how well it worked. The script must print, as its last line, `SNR_DB=<value>` where the value is `pylops.utils.metrics.snr(xtrue, xinv)` computed on the inverted **model** against the true model.
