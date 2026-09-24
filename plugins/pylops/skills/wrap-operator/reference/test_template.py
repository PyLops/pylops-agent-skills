"""Skeleton tests for a user-defined PyLops operator.

Adapt the import and the reference forward to your project.
"""

import numpy as np
import pytest
from numpy.testing import assert_array_almost_equal

from pylops.optimization.basic import lsqr
from pylops.utils import dottest

from mypackage.myoperator import MyOperator  # adjust import

par1 = {"ny": 7, "nx": 5, "imag": 0, "dtype": "float64"}  # real
par1j = {"ny": 7, "nx": 5, "imag": 1j, "dtype": "complex128"}  # complex


def reference_forward(param, x):
    """Original (non-PyLops) forward implementation to compare against"""
    return param * x


def test_MyOperator_raises():
    """Check input validation of MyOperator"""
    with pytest.raises(ValueError):
        MyOperator(np.ones((3, 4)), dims=(4, 3))


@pytest.mark.parametrize("par", [(par1), (par1j)])
def test_MyOperator(par):
    """Dot-test, forward and inversion for MyOperator"""
    dims = (par["ny"], par["nx"])
    rng = np.random.default_rng(0)
    param = 1.0 + rng.random(dims) + par["imag"] * rng.random(dims)
    Op = MyOperator(param, dims=dims, dtype=par["dtype"])

    assert dottest(
        Op,
        par["ny"] * par["nx"],
        par["ny"] * par["nx"],
        rtol=1e-6,
        complexflag=0 if par["imag"] == 0 else 3,
    )

    x = np.ones(dims) + par["imag"] * np.ones(dims)
    y = Op @ x.ravel()
    assert_array_almost_equal(y, reference_forward(param, x).ravel(), decimal=6)

    xinv = lsqr(Op, y, x0=np.zeros(Op.shape[1], dtype=Op.dtype), niter=200)[0]
    assert_array_almost_equal(x.ravel(), xinv, decimal=4)
