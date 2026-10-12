"""Minimal downstream adaptation; the escape semantics remain an E5b task."""
from construction_oracle import scalar_exact, sqrt_exact
from fractions import Fraction as F
import math
from types import SimpleNamespace
import inspect
import pytest

from eab.kernel3d import interlock as I

from eab.kernel3d.geom3 import Polyhedron, cross, norm
from eab.kernel3d.interlock import _normal_noise


def test_normal_noise_handles_exact_cross_hidden_by_unit_vector_rounding(monkeypatch):
    """Independent rational edge differences, not production cone primitives."""
    A = Polyhedron([(-0.5499999999999999, -0.5, 1.7321660590032764),
                    (-0.14999999999999997, -0.5, 1.3910452200557695)], [])
    B = Polyhedron([(-0.6, 0.5, 0.7321660590032764),
                    (-0.19999999999999996, 0.5, 0.3910452200557694)], [])
    edge = (0, 1)
    u = tuple(F(b) - F(a) for a, b in zip(A.verts[0], A.verts[1]))
    v = tuple(F(b) - F(a) for a, b in zip(B.verts[0], B.verts[1]))
    n = (u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0])
    sine_squared = sum(x*x for x in n) / (sum(x*x for x in u)*sum(x*x for x in v))
    assert sine_squared > 0
    report_noise = F(A.edge_noise(edge)+B.edge_noise(edge))
    expected = sqrt_exact(report_noise*report_noise/sine_squared)
    cover = SimpleNamespace(label=lambda: ('EE', ('edge', 0, 1), ('edge', 0, 1)))
    actual = I._normal_noise(A, B, cover)
    assert math.isfinite(actual) and actual > 1
    assert math.isclose(actual, expected, rel_tol=2e-15), 'exact-edge-noise'
    # Correct final normalization need no longer collapse these two directions.
    # Preserve the old zero-display-cross case explicitly, without changing the
    # source geometry, rational oracle or acceptance threshold.
    displayed = A.edge_dir(edge)
    with monkeypatch.context() as patch:
        patch.setattr(Polyhedron, 'edge_dir', lambda self, e: displayed)
        assert norm(cross(B.edge_dir(edge), A.edge_dir(edge))) == 0
        hidden = I._normal_noise(A, B, cover)
        assert math.isclose(hidden, expected, rel_tol=2e-15), 'exact-edge-noise-hidden-display'
        assert hidden == actual, 'display-independent-edge-noise'


def test_normal_noise_rejects_nonzero_rounded_cross_fast_path(monkeypatch):
    source = inspect.getsource(I._normal_noise)
    exact = 'sine = sqrt_rational(dot(n, n) / (dot(a, a) * dot(b, b)))'
    assert source.count(exact) == 1
    namespace = dict(vars(I))
    exec(compile(source.replace(exact, 'sine = norm(cross(B.edge_dir(eb), A.edge_dir(ea)))'),
                 '<r7fix-nonzero-rounded-cross-mutation>', 'exec'), namespace)
    monkeypatch.setattr(I, '_normal_noise', namespace['_normal_noise'])
    with pytest.raises(AssertionError, match='exact-edge-noise'):
        test_normal_noise_handles_exact_cross_hidden_by_unit_vector_rounding(monkeypatch)
