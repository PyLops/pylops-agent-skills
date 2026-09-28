---
max_turns: 40
timeout_seconds: 900
allowed_tools: [Skill, Read, Glob, Grep, Write, Bash]
runs: 3
---
I'm inverting blurred, noisy measurements of a 1-D property profile. Physically the property can only take values between 0 and 1, and I want the recovered model to respect those bounds. To test the approach I'm using a synthetic:

- model `xtrue` with n = 200 samples, zero everywhere except 1.0 on samples 20–59, 75–79, 110–129 and 150–184;
- the blur is a Gaussian kernel `h = exp(-0.5 * (t / 5)**2)` for integer t from −30 to 30, normalised to sum to 1 and centred (`pylops.signalprocessing.Convolve1D(200, h=h, offset=30)`);
- data `y = Op @ xtrue + 0.05 * rng.standard_normal(200)` with `rng = np.random.default_rng(0)`.

I'd like the recovered model to be as close to the truth as possible while staying within [0, 1]. Please write a runnable Python script for this, saved as `invert.py` in the current folder, run it, and tell me what you chose and how well it worked. The script must print, as its last line, `SNR_DB=<value>` where the value is `pylops.utils.metrics.snr(xtrue, xinv)` computed on the inverted **model** against the true model.
