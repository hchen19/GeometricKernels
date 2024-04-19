"""
Product of kernels
"""

import math

import lab as B
from beartype.typing import Dict, List, Optional

from geometric_kernels.kernels.base import BaseGeometricKernel
from geometric_kernels.spaces import Space
from geometric_kernels.utils.product import project_product


class ProductGeometricKernel(BaseGeometricKernel):
    """
    Basic implementation of product kernels.

    :param kernels:
        Kernels to compute the product for.
    :param dimension_indices:
        List of indices the correspond to the indices of the input that should
        be fed to each kernel. If None, assume the each input is layed-out
        flattened and concatenated, in the same order as the factor spaces.
        That is, if the shape of the input is [D1, ..., DN], it is flattened to
        a [D1*...*DN]-array.

        Defaults to None.
    """

    def __init__(
        self,
        *kernels: BaseGeometricKernel,
        dimension_indices: Optional[List[B.Numeric]] = None,
    ):
        self.kernels = kernels
        self.element_shapes = [kernel.space.element_shape for kernel in self.kernels]

        if dimension_indices is None:
            dimensions = [math.prod(shape) for shape in self.element_shapes]
            self.dimension_indices: List[B.Numeric] = []
            i = 0
            inds = B.linspace(0, sum(dimensions) - 1, sum(dimensions)).astype(int)
            for dim in dimensions:
                self.dimension_indices.append(inds[i : i + dim])
                i += dim
        else:
            assert len(dimension_indices) == len(self.kernels)
            for idx in dimension_indices:
                assert idx.dtype == B.Int
                assert B.all(idx >= 0)

            self.dimension_indices = dimension_indices

    @property
    def space(self) -> List[Space]:
        """
        The list of spaces upon which the factor kernels are defined.
        """
        return [kernel.space for kernel in self.kernels]

    def init_params(self) -> List[Dict[str, B.Numeric]]:
        r"""
        Returns the list of `kernel.init_params()` for all factor `kernel`\ s.
        """
        params = [kernel.init_params() for kernel in self.kernels]
        return params

    def K(self, params: List[Dict[str, B.Numeric]], X, X2=None, **kwargs) -> B.Numeric:
        if X2 is None:
            X2 = X

        Xs = project_product(X, self.dimension_indices, self.element_shapes)
        X2s = project_product(X2, self.dimension_indices, self.element_shapes)

        return B.prod(
            B.stack(
                *[
                    kernel.K(p, X, X2)
                    for kernel, X, X2, p in zip(self.kernels, Xs, X2s, params)
                ],
                axis=-1,
            ),
            axis=-1,
        )

    def K_diag(self, params, X):
        Xs = project_product(X, self.dimension_indices, self.element_shapes)

        return B.prod(
            B.stack(
                *[
                    kernel.K_diag(p, X)
                    for kernel, X, p in zip(self.kernels, Xs, params)
                ],
                axis=-1,
            ),
            axis=-1,
        )
