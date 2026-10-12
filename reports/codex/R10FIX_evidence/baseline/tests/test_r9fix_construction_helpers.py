"""Same-family helper checks: exact products may not become display inputs.

Expected values use triangle/box Cartesian formulas, and Fraction midpoint
certificates, not any production geometry constructor or normal routine.
"""
from fractions import Fraction as F
import math
import inspect
import pytest

from construction_oracle import scalar_exact, assert_sqrt_rounding
from eab.kernel3d.geom3 import Polyhedron
from test_invariance_2d import _support_labels_exact, _sat_gap_exact
from test_invariance_geom import _support_gap_oracle
from test_frozen_ee_sign import _line_parameters_and_gap


@pytest.mark.parametrize("exponent", [-600, 0, 600])
def test_r9_2d_support_helpers_keep_final_distance_when_projection_overflows(exponent):
    s = F(2)**exponent
    triangle = [(0,0),(s,0),(0,s)]
    _, margin, _ = _support_labels_exact(triangle, triangle)
    assert_sqrt_rounding(margin, s*s/2, "triangle strict support margin")
    square = [(0,0),(s,0),(s,s),(0,s)]
    shifted = [(x+3*s,y) for x,y in square]
    assert _sat_gap_exact(square, shifted, (0,0)) == scalar_exact(2*s), "Cartesian SAT gap"


@pytest.mark.parametrize("exponent", [-600, 0, 600])
def test_r9_3d_support_helper_rounds_signed_final_gap(exponent):
    s = F(2)**exponent
    points = [(-s,-s,-s),(s,-s,-s),(s,s,-s),(-s,s,-s),
              (-s,-s,s),(s,-s,s),(s,s,s),(-s,s,s)]
    faces = [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
    B = Polyhedron(points, list(faces))
    A = Polyhedron([(x+4*s,y,z) for x,y,z in points], list(faces))
    result = _support_gap_oracle(A,B,(0,0,0))
    expected = [-2*s]*8 + [2*s]*2 + [-6*s]*2
    assert sorted(result) == sorted(map(scalar_exact,expected)), "box support gap spectrum"


@pytest.mark.parametrize("t", [F(0), F(10**20), F(2)**600])
def test_r9_line_gap_oracle_cancels_before_normalization(t):
    d = F(2)**-600
    # u=(3,-1,0), v=(0,3,-3): v cross u=(-3,-9,-9).
    # With a=(3t,-t,d), the exact numerator is -9d, independent of t.
    a = (3*t,-t,d)
    A = Polyhedron([a,(3*t+3,-t-1,d)],[])
    B = Polyhedron([(0,0,0),(0,3,-3)],[])
    _, gap = _line_parameters_and_gap(A,(0,1),B,(0,1))
    assert gap < 0, "line gap sign survives exact cancellation"
    assert_sqrt_rounding(-gap,9*d*d/19,"line gap Fraction midpoint certificate")


def test_r9_support_oracle_internal_pre_rounding_mutation_is_rejected(monkeypatch):
    import test_invariance_2d as oracle
    source = inspect.getsource(oracle._support_labels_exact)
    old = "strict_margins.append(sqrt_exact(gap*gap/(nx*nx+ny*ny)))"
    assert source.count(old) == 1
    bad = "strict_margins.append(float(gap)/math.hypot(float(nx),float(ny)))"
    namespace = dict(vars(oracle))
    exec(compile(source.replace(old,bad),"<R9 support oracle internal mutant>","exec"),namespace)
    monkeypatch.setitem(globals(),"_support_labels_exact",namespace["_support_labels_exact"])
    with pytest.raises(AssertionError, match="triangle strict support margin") as caught:
        test_r9_2d_support_helpers_keep_final_distance_when_projection_overflows(-600)
    print("support helper mutant:", caught.value)


def test_r9_line_gap_oracle_internal_pre_normalization_mutation_is_rejected(monkeypatch):
    import test_frozen_ee_sign as oracle
    source = inspect.getsource(oracle._line_parameters_and_gap)
    old = "    numerator=independent.dot(n,independent.sub(a,b))\n    gap=(-1 if numerator < 0 else 1)*sqrt_exact(numerator*numerator/independent.dot(n,n))"
    assert source.count(old) == 1
    bad = "    scaled=[float(x/max(map(abs,n))) for x in n]\n    unit=[x/math.hypot(*scaled) for x in scaled]\n    gap=sum(unit[i]*float(a[i]-b[i]) for i in range(3))"
    namespace = dict(vars(oracle))
    exec(compile(source.replace(old,bad),"<R9 line gap oracle internal mutant>","exec"),namespace)
    monkeypatch.setitem(globals(),"_line_parameters_and_gap",namespace["_line_parameters_and_gap"])
    with pytest.raises(AssertionError, match="line gap sign survives exact cancellation") as caught:
        test_r9_line_gap_oracle_cancels_before_normalization(F(10**20))
    print("line helper mutant:", caught.value)


def test_r9_reference_scalar_identity_fast_path_accepts_only_finite_binary64():
    for value in (0., -0., math.ulp(0.), -1., float.fromhex('0x1.fffffffffffffp1023')):
        assert scalar_exact(value) is value
    for value in (math.nan, math.inf, -math.inf):
        with pytest.raises(ValueError, match="finite"):
            scalar_exact(value)
