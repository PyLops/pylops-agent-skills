# PyProximal quick reference

Check the installed version (`help(pyproximal.optimization.primal.ADMM)`) – this
reflects PyProximal 0.12 (requires PyLops ≥ 2.4, Python ≥ 3.11).

## Proximal operators (`pyproximal.<Name>`)

| Term | Operator | Notes |
|---|---|---|
| `σ/2 ‖Op x − b‖²` | `L2(Op=None, b=None, sigma=1., niter=10, warm=True)` | smooth: has `.grad`; prox with `Op` needs an inner solve (`niter`) |
| `σ ‖x‖₁` | `L1(sigma=1., g=None)` | `sigma` may be a callable of the iteration |
| `σ ‖x‖₀` | `L0(sigma)` | non-convex |
| `σ Σ ‖xᵢ‖₂` (groups) | `L21(ndim, sigma=1.)` | with `pylops.Gradient` → isotropic TV |
| TV directly | `TV(dims, sigma, niter)` | inner iterative prox; slower than `L21` + `Gradient` in PrimalDual |
| Huber | `Huber(alpha)` | smooth-ish L1 |
| nuclear norm | `Nuclear(dim, sigma)` | low-rank matrices |
| `l ≤ x ≤ u` | `Box(lower, upper)` | positivity: `Box(0.0, np.inf)` |
| `‖x − c‖ ≤ r` | `EuclideanBall(center, radius)` | |
| `‖x‖₁ ≤ r` | `L1Ball(n, radius)` | |
| `Op x = b` | `AffineSet(Op, b, niter)` | basis pursuit |
| simplex | `Simplex(n, radius, engine)` | |
| stacked blocks of `Kx` | `VStack(ops, nn)` | `nn` = sizes of each block |
| sum of proxes | `Sum(ops, weights, niter)` (Dykstra) | |
| non-convex penalties | `SCAD`, `Log`, `Log1`, `ETP`, `Geman` | |
| custom nonlinear smooth term | subclass `Nonlinear` (`fun`, `grad`, `optimize`) | |

Arithmetic: `2.0 * f` scales (float required: `2 * f` silently returns `None`), `f + v` adds
`vᵀx`, `f.precomposition(a, b)` gives `f(a x + b)` (scalar `a`), `f.H` swaps
`prox` and `proxdual`. Every operator has `prox(x, tau)`, `proxdual(x, tau)`
and `__call__(x)` (value).

## Solvers

| Solver (`pyproximal.optimization.…`) | Minimises | Key args | Returns |
|---|---|---|---|
| `primal.ProximalGradient` | `f(x) + ε g(x)`, `f` smooth | `proxf, proxg, x0, epsg, tau (None → backtracking), acceleration=None / "fista" / "vandenberghe"` | `x` |
| `primal.GeneralizedProximalGradient` | `Σ fᵢ + Σ εⱼ gⱼ` | `proxfs, proxgs, x0, tau, epsg` | `x` |
| `primal.ADMM` | `f(x) + g(x)` | `proxf, proxg, x0, tau` | `(x, z)` |
| `primal.ADMML2` | `½‖Op x − b‖² + g(A x)` | `proxg, Op, b, A, x0, tau` | `(x, z)` |
| `primal.LinearizedADMM` | `f(x) + g(A x)` | `proxf, proxg, A, x0, tau, mu` (μ ≤ τ/‖A‖²) | `(x, z)` |
| `primaldual.PrimalDual` | `f(x) + g(K x)` | `proxf, proxg, A=K, x0, tau, mu, theta=1` (τ μ ‖K‖² < 1) | `x` |
| `primaldual.AdaptivePrimalDual` | same, adaptive steps | `tau, mu` initial | `(x, steps)` |
| `primal.HQS`, `primal.DouglasRachfordSplitting` | `f + g` | | `(x, z)` / `(x, y)` |
| `primal.TwIST` | `½‖b − A x‖² + g(x)` | `proxg, A, b, x0, eigs` | `x` |
| `primal.PPXA`, `primal.ConsensusADMM` | `Σ fᵢ` | `proxfs, x0, tau` | `x` |
| `bregman.Bregman` | outer Bregman loop around any solver | | |
| `pnp.PlugAndPlay` | `f` + denoiser prior | `proxf, denoiser(x, tau), dims, x0, solver` | as solver |
| `palm.PALM` / `iPALM` | bilinear (matrix factorisation) | | `(x, y)` |

Common keyword arguments: `niter`, `tol`, `rtol`, `callback(x)`, `show`.
The class API in `cls_primal` / `cls_primaldual` (`setup/step/run/finalize/solve`)
returns extra information such as `iiter` and cost history.

## Step sizes

- Proximal gradient: `tau ≤ 1/L`, `L` = Lipschitz constant of `∇f`; for
  `f = σ/2‖Op x − b‖²`, `L = σ ‖Op‖²`. `tau=None` enables backtracking.
- PrimalDual: `tau * mu * ‖K‖² < 1`, e.g. `tau = mu = 0.95 / ‖K‖`.
- LinearizedADMM: `mu ≤ tau / ‖A‖²`.
- `‖K‖²`: `pylops.optimization.eigs.power_iteration(K.H @ K, niter=...)[0]`
  (inflate by ~5 %, it converges from below) or `(K.H @ K).eigs(neigs=1)` (may
  not converge); analytically `‖Gradient‖² ≤ 4·ndim / sampling²` (8 in 2-D
  with unit sampling).

## Tutorials

https://pyproximal.readthedocs.io – tutorials: denoising (TV / L1 / Tikhonov),
adaptivepd, basispursuit, constrained (box constraints), groupsparsity,
lowrankcompletion, matrixfactorization, plugandplay, twist, deblending,
relaxed_mumford-shah, nonlinearconstrained.
