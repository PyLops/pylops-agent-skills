"""Skeleton for a user-defined PyLops operator.

Copy into your own package, rename, and fill in the forward and adjoint.
Delete anything that does not apply.
"""

__all__ = ["MyOperator"]

import numpy as np

from pylops import LinearOperator
from pylops.utils.decorators import reshaped
from pylops.utils.typing import DTypeLike, InputDimsLike, NDArray


class MyOperator(LinearOperator):
    r"""One-line summary of the operator.

    Longer description of what the operator applies in forward mode and what
    its adjoint does.

    Parameters
    ----------
    param : :obj:`numpy.ndarray`
        Description of the main parameter.
    dims : :obj:`tuple`
        Shape of the model.
    dimsd : :obj:`tuple`, optional
        Shape of the data (defaults to ``dims``).
    dtype : :obj:`str`, optional
        Type of elements in input array.
    name : :obj:`str`, optional
        Name of operator (to be used by :func:`pylops.utils.describe.describe`)

    Raises
    ------
    ValueError
        If ``param`` has incompatible shape with ``dims``.

    Notes
    -----
    In forward mode the operator applies

    .. math::
        y_i = \ldots

    and in adjoint mode

    .. math::
        x_i = \ldots

    """

    def __init__(
        self,
        param: NDArray,
        dims: InputDimsLike,
        dimsd: InputDimsLike | None = None,
        dtype: DTypeLike = "float64",
        name: str = "M",
    ) -> None:
        dims = tuple(dims)
        dimsd = dims if dimsd is None else tuple(dimsd)
        if param.shape != dims:
            raise ValueError(f"param shape {param.shape} differs from dims {dims}")
        self.param = param
        super().__init__(dtype=np.dtype(dtype), dims=dims, dimsd=dimsd, name=name)

    @reshaped
    def _matvec(self, x: NDArray) -> NDArray:
        # x has shape self.dims; return an array of shape self.dimsd
        y = self.param * x  # replace with the forward model, y = A x
        return y

    @reshaped
    def _rmatvec(self, y: NDArray) -> NDArray:
        # y has shape self.dimsd; return an array of shape self.dims
        x = self.param.conj() * y  # replace with the adjoint, x = A^H y
        return x
