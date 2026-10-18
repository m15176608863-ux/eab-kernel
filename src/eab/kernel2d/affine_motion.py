"""Exact endpoint affine fit and a rational DDA-shaped trajectory proposal.

This module does NOT solve general affine-motion first contact or certify the
unknown physical path. See docs/m5a2_affine_theory.md for the proof boundary.
Gates: tests/test_m5a2_affine.py. All public numerical inputs are int/Fraction.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction as F


def _q(value):
    if not isinstance(value, (int, F)) or isinstance(value, bool):
        raise ValueError("affine motion requires exact integers or Fractions")
    return F(value)


def _point(point):
    if len(point) != 2:
        raise ValueError("affine motion requires two-dimensional points")
    return tuple(_q(v) for v in point)


def _matrix(matrix):
    if len(matrix) != 2:
        raise ValueError("affine motion requires a 2 by 2 matrix")
    return tuple(_point(row) for row in matrix)


def _apply(matrix, point):
    return tuple(sum(matrix[i][j]*point[j] for j in (0, 1)) for i in (0, 1))


@dataclass(frozen=True)
class AffineFit:
    center: tuple
    translation: tuple
    matrix: tuple
    residuals: tuple

    def __post_init__(self):
        object.__setattr__(self, "center", _point(self.center))
        object.__setattr__(self, "translation", _point(self.translation))
        object.__setattr__(self, "matrix", _matrix(self.matrix))
        residuals = tuple(_point(row) for row in self.residuals)
        if not residuals:
            raise ValueError("affine fit requires a nonempty residual table")
        object.__setattr__(self, "residuals", residuals)

    @property
    def delta(self):
        """Exact maximum coordinate residual; not a physical-path certificate."""
        return max(abs(v) for row in self.residuals for v in row)

    @property
    def endpoint_certificate(self):
        return "EXACT_AFFINE_ENDPOINTS" if self.delta == 0 else "UNCERTIFIED_NONAFFINE_ENDPOINTS"

    def endpoint(self, point):
        point = _point(point)
        mapped = _apply(self.matrix, tuple(point[k]-self.center[k] for k in (0, 1)))
        return tuple(self.center[k]+self.translation[k]+mapped[k] for k in (0, 1))


def fit_affine(start, end):
    """Exact equal-vertex-weight least-squares affine fit, not an L-infinity fit.

    The input ring must span the plane; topology pairing is positional.
    The normal-equation denominator is strictly positive, with no threshold.
    Gate: test_fit_matches_independent_three_point_and_normal_equation_oracles.
    """
    start, end = tuple(map(_point, start)), tuple(map(_point, end))
    if len(start) != len(end) or len(start) < 3:
        raise ValueError("affine fit requires equal vertex counts, at least three")
    center = tuple(sum(p[k] for p in start)/len(start) for k in (0, 1))
    target = tuple(sum(p[k] for p in end)/len(end) for k in (0, 1))
    x = tuple(tuple(p[k]-center[k] for k in (0, 1)) for p in start)
    y = tuple(tuple(p[k]-target[k] for k in (0, 1)) for p in end)
    xx = sum(p[0]*p[0] for p in x)
    xy = sum(p[0]*p[1] for p in x)
    yy = sum(p[1]*p[1] for p in x)
    determinant = xx*yy-xy*xy
    if determinant <= 0:
        raise ValueError("affine fit initial points do not span the plane")
    cross = tuple(tuple(sum(q[i]*p[j] for p, q in zip(x, y)) for j in (0, 1)) for i in (0, 1))
    matrix = tuple(((row[0]*yy-row[1]*xy)/determinant,
                    (row[1]*xx-row[0]*xy)/determinant) for row in cross)
    translation = tuple(target[k]-center[k] for k in (0, 1))
    residuals = tuple(tuple(q[k]-sum(matrix[k][j]*p[j] for j in (0, 1)) for k in (0, 1))
                      for p, q in zip(x, y))
    return AffineFit(center, translation, matrix, residuals)
