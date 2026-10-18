"""DDA endpoint-shaped affine trajectory proposal (L5 adapter)."""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction as F

from ..kernel2d.affine_motion import AffineFit, fit_affine, _q, _point, _matrix, _apply


@dataclass(frozen=True)
class DDAAffineMotion:
    """X=c+s*d+[R(s*u)+s*E](x-c), with E=M-R(u).

    This additive strain arrangement follows b-DDA's finite-rotation endpoint
    update, but u need not recover its internal angle and E need not be symmetric.
    No assumption about non-inversion or the physical interpolant is implicit.
    Gate: test_additive_trajectory_matches_independent_component_oracle.
    """
    matrix: tuple = ((F(1), F(0)), (F(0), F(1)))
    u1: F = F(0)
    translation: tuple = (F(0), F(0))
    center: tuple = (F(0), F(0))

    def __post_init__(self):
        object.__setattr__(self, "matrix", _matrix(self.matrix))
        object.__setattr__(self, "u1", _q(self.u1))
        object.__setattr__(self, "translation", _point(self.translation))
        object.__setattr__(self, "center", _point(self.center))
        if abs(self.u1) > 1:
            raise ValueError("affine rational rotation supports |u1|<=1")

    @property
    def correction(self):
        u = self.u1
        cosine, sine = (1-u*u)/(1+u*u), 2*u/(1+u*u)
        rotation = ((cosine, -sine), (sine, cosine))
        return tuple(tuple(self.matrix[i][j]-rotation[i][j] for j in (0, 1)) for i in (0, 1))

    @property
    def orientation_preserving_sufficient(self):
        """Neumann sufficient condition only; false means unknown, not inversion.

        Gate: test_orientation_sufficient_bound_and_degenerate_counterexample.
        """
        return 2*max(sum(abs(v) for v in row) for row in self.correction) < 1

    def at(self, point, s):
        point, s = _point(point), _q(s)
        if not 0 <= s <= 1:
            raise ValueError("affine time is outside the closed unit window")
        u = s*self.u1
        cosine, sine = (1-u*u)/(1+u*u), 2*u/(1+u*u)
        x, y = tuple(point[k]-self.center[k] for k in (0, 1))
        strain = _apply(self.correction, (x, y))
        return (self.center[0]+s*self.translation[0]+cosine*x-sine*y+s*strain[0],
                self.center[1]+s*self.translation[1]+sine*x+cosine*y+s*strain[1])

    def endpoint(self, point):
        return self.at(point, F(1))

    def corrected_at(self, point, endpoint_residual, s):
        """A specified, endpoint-closing interpolant; NOT an inferred true path.

        Difference from at() is exactly s*residual, hence <=s*delta in L-inf.
        Gate: test_linear_residual_correction_closes_data_without_certification.
        """
        s, residual = _q(s), _point(endpoint_residual)
        value = self.at(point, s)
        return tuple(value[k]+s*residual[k] for k in (0, 1))

