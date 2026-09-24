---
name: wrap-operator
description: Wrap a user's own forward model as a PyLops linear operator inside their project (not inside the PyLops library), with a verified adjoint, a dot-test and a small test suite. Use when the user wants to turn existing forward/adjoint code, a script at a URL, or a mathematical description into a PyLops operator they can pass to PyLops solvers (e.g. "make my blurring function a PyLops operator", "wrap this forward model so I can invert it with lsqr", "I have a forward and adjoint, plug them into PyLops").
---

Goal: give the user a PyLops-compatible linear operator for **their** forward
model, living in **their** project, with an adjoint proven correct by the
dot-test. Do not modify the installed `pylops` package; if the user actually
wants to contribute an operator to the PyLops library, point them to
https://pylops.readthedocs.io/en/stable/adding.html instead.

Ask for the forward model only if it is not inferable from the invocation.

## 0. Check the environment

- Find how the project runs Python (look for `uv.lock`, `pyproject.toml`,
  `environment.yml`, `requirements*.txt`, an active venv) and use that runner for
  every command below. Do not switch the user to a different tool.
- Confirm PyLops is importable and note its version:
  `python -c "import pylops; print(pylops.__version__)"`. If it is missing, ask
  before installing it.
- When unsure about a PyLops signature, inspect the installed version
  (`help(pylops.FunctionOperator)`, `inspect.signature(...)`) rather than
  relying on memory.

## 1. Understand the forward model

Get the source (read a local file in full; fetch a URL and extract the code, not
the prose; or take the user's maths). Then write down, before coding:

- the **model** array shape (`dims`) and the **data** array shape (`dimsd`);
  PyLops operators have `shape = (prod(dimsd), prod(dims))` and act on
  flattened vectors;
- that the map is actually **linear** in the model (no clipping, `abs`, data-
  dependent branching, additive offsets). If it is affine (`A x + b`), wrap only
  `A` and handle `b` outside;
- whether it is real or complex, and the dtype to use;
- whether an adjoint is supplied, and whether it is a **true adjoint**
  (\(\mathbf{A}^H\)) rather than an inverse, a pseudo-inverse, a plain transpose
  of a complex operator, or an approximation. This is the most common bug.

If no adjoint exists, derive it (reverse the loop order, transpose each stage,
conjugate complex factors, turn "scatter" into "gather"). If the forward is
written in JAX, `pylops.JaxOperator(Op).rmatvecad(x, y)` computes the adjoint by
automatic differentiation and is a good reference to test a hand-written one
against.

## 2. Pick the lightest construction that works

Prefer, in this order:

1. **Composition of existing PyLops operators.** Many forward models are chains
   of `MatrixMult`, `Diagonal`, `FFT`/`FFT2D`, `Convolve1D`/`ConvolveND`,
   `Restriction`, `FirstDerivative`, `Transpose`, `VStack`/`HStack`/`BlockDiag`
   and `Kronecker`, combined with `*`, `+` and `.H`. The adjoint then comes for
   free and is already tested. Check the operator list in the docs (or
   `dir(pylops)`) before writing new code.
2. **`pylops.FunctionOperator(f, fc, n, m, dtype=...)`** when the user already
   has working forward/adjoint functions on flat vectors and only needs to plug
   them into a solver. Here `n` is the data length and `m` the model length.
   Wrap reshape/flatten inside `f` and `fc` if the functions expect n-D arrays.
3. **A `pylops.LinearOperator` subclass** when the operator is reused, has
   parameters worth keeping as attributes, or is n-dimensional. Use
   `reference/operator_template.py`.

State which option you chose and why.

## 3. Write the operator (option 3)

- Put it where the user's code lives (their package or a new module next to the
  script that will use it). Ask if the location is ambiguous.
- Call `super().__init__(dtype=np.dtype(dtype), dims=dims, dimsd=dimsd, name=name)`;
  `shape` is derived from `dims`/`dimsd`.
- Decorate `_matvec` and `_rmatvec` with `@reshaped` so `x` arrives with shape
  `dims` (and `y` with `dimsd`) and the returned arrays are flattened for you.
- Only use the public PyLops API (`pylops`, `pylops.utils.*`); avoid private
  modules such as `pylops.utils._internal`.
- GPU/CuPy support is optional: add `get_array_module` /
  `to_cupy_conditional` only if the user needs it.
- Give it a numpydoc docstring with the forward and adjoint maths in `Notes`.

## 4. Test it

Use the project's existing test framework and layout; default to `pytest` in a
`tests/` folder if there is none. Start from `reference/test_template.py`:

- `pylops.utils.dottest(Op, nr, nc, rtol=..., complexflag=...)` for every
  configuration (real and complex if both are supported). Never loosen the
  tolerance to make a failing dot-test pass: a failure means the adjoint is
  wrong.
- a forward check against the user's original implementation (or
  `Op.todense() @ x` on a small size);
- a small inversion (`pylops.optimization.basic.lsqr` or `Op / y`) when the
  operator is invertible or well-conditioned enough to make it meaningful;
- tests for any input validation the `__init__` performs, placed before the
  other tests.

Run the tests and iterate until they pass.

## 5. Hand off

Report:

- which construction was chosen, and where the file lives;
- dot-test result and any adjoint corrections made compared to the source;
- a short usage snippet solving the user's inverse problem, e.g.
  `xinv = pylops.optimization.basic.lsqr(Op, y, niter=100)[0]`, reshaped to
  `Op.dims`.
