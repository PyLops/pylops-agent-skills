---
max_turns: 40
timeout_seconds: 900
allowed_tools: [Skill, Read, Glob, Grep, Write, Bash]
runs: 3
---
I want to set up an inversion with PyLops for a 1-D layered earth model that I observe through a blurring instrument. To test the approach I'm using a synthetic:

- model `xtrue` with n = 200 samples, zero everywhere except 1.0 on samples 30–69, −0.5 on samples 70–109 and 2.0 on samples 140–169;
- the blur is a Gaussian kernel `h = exp(-0.5 * (t / 5)**2)` for integer t from −20 to 20, normalised to sum to 1 and centred (`pylops.signalprocessing.Convolve1D(200, h=h, offset=20)`);
- data `y = Op @ xtrue + 0.02 * rng.standard_normal(200)` with `rng = np.random.default_rng(0)`.

I'd like the recovered model to be as close to the truth as possible. Please write a runnable Python script for this, saved as `invert.py` in the current folder, run it, and tell me what you chose and how well it worked. The script must print, as its last line, `SNR_DB=<value>` where the value is `pylops.utils.metrics.snr(xtrue, xinv)` computed on the inverted **model** against the true model.
