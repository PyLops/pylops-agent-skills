---
max_turns: 8
timeout_seconds: 120
allowed_tools: [Skill, Read, Glob, Grep]
runs: 3
---
I'm setting up a sparse-spike deconvolution of a seismic trace with pylops: `Op = pylops.signalprocessing.Convolve1D(nt, h=wav, offset=len(wav)//2)`, data `y` with some noise, and I expect the reflectivity to be sparse. Nothing is broken yet, I just haven't started — which PyLops solver should I use, and why?
