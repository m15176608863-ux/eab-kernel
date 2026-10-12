"""Independent oracle-helper range/cancellation gates; raw rational truth only."""
from fractions import Fraction as F
from types import SimpleNamespace
import inspect
import math

import pytest

from construction_oracle import assert_sqrt_rounding, scalar_exact
import e5a_cover_oracle as cover
import e5a_escape_oracle as escape
import e5a_g2_oracle as g2
import perf_cover_oracle_reference as old_cover
import perf_escape_oracle_reference as old_escape


@pytest.mark.parametrize('oracle', [cover, old_cover])
def test_r9_oracle_witness_distance_subtracts_before_rounding(oracle):
    a = SimpleNamespace(verts=[(F(10**8)+F(1, 10**9), 0, 0)], faces=[])
    b = SimpleNamespace(verts=[(F(10**8), 0, 0)], faces=[])
    distance = oracle.witness_distance(a, b, ('VV3', ('vertex', 0), ('vertex', 0)))
    assert_sqrt_rounding(distance, F(1, 10**18))


@pytest.mark.parametrize('oracle', [escape, old_escape])
@pytest.mark.parametrize('exponent', [-600, 600])
def test_r9_oracle_norm_does_not_round_the_intermediate_square(oracle, exponent):
    value = F(2)**exponent
    actual = oracle.norm((value, 0, 0))
    assert actual == math.ldexp(1., exponent), 'oracle-final-norm-range'


@pytest.mark.parametrize('oracle', [escape, old_escape])
def test_r9_oracle_facet_gap_uses_exact_dot_before_unit_construction(oracle):
    # Newell direction (1,1,0), exact displacement (2**53,1-2**53,0):
    # numerator is exactly 1, so signed gap is sqrt(1/2), not 0 or 1.
    p, n = (F(2**53), F(1-2**53), F(0)), (F(1), F(1), F(0))
    a = ((p,), (), (), {}, (((F(1), F(1), F(1)),),))
    b = (((F(0),)*3, (F(1), F(-1), F(0)), (F(0), F(0), F(1))),
         ((0, 1, 2),), (n,), {}, ())
    result = oracle.facet(a, b, ('VF', ('vertex', 0), ('face', 0)), tol=0)
    assert result is not None
    assert result[1] > 0, 'oracle-signed-gap-sign'
    assert_sqrt_rounding(result[1], F(1, 2))


@pytest.mark.parametrize('unit', [escape.unit, old_escape.unit, g2._unit])
def test_r9_oracle_unit_component_has_fraction_midpoint_certificate(unit):
    v = (F(7, 5), F(2, 3), F(1, 7))
    squared = sum(x*x for x in v)
    for got, component in zip(unit(v), v):
        assert_sqrt_rounding(got, component*component/squared)


@pytest.mark.parametrize('oracle', [escape, old_escape])
@pytest.mark.parametrize('depth', [F(1, 7), F(3, 11), F(9, 23)])
def test_r9_oracle_escape_height_rounds_the_exact_plane_ratio(oracle, depth):
    # Common affine shear: top plane z-(2/3)x-(1/5)y=1. A's bottom
    # vertex is at (0,0,-depth), so its upward intersection is exactly 1+depth.
    raw = [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0),
           (0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)]
    faces = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
             (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    def body(offset):
        return SimpleNamespace(verts=[(F(x), F(y), F(z)+F(2, 3)*x+F(1, 5)*y-offset)
                                      for x, y, z in raw], faces=faces)
    rows, _, _ = oracle.candidates(body(depth), body(F(0)), (0, 0, 0))
    heights = [row[0] for row in rows if row[1] == ('VF', ('vertex', 0), ('face', 1))]
    assert heights == [scalar_exact(1+depth)], 'oracle-exact-plane-height-ratio'


def test_r9_oracle_witness_rounding_mutant_is_caught(monkeypatch):
    source = inspect.getsource(cover.witness_distance)
    assert source.count('exact=True') == 1
    namespace = dict(vars(cover))
    exec(compile(source.replace('exact=True', 'exact=False'), '<r9-rounded-witness>', 'exec'), namespace)
    monkeypatch.setattr(cover, 'witness_distance', namespace['witness_distance'])
    with pytest.raises(AssertionError, match='exact root midpoint certificate'):
        test_r9_oracle_witness_distance_subtracts_before_rounding(cover)


def test_r9_oracle_rounded_gap_height_mutant_is_caught(monkeypatch):
    source = inspect.getsource(escape._candidates)
    needle = 'z=scalar_exact(-numerator/normal[2])'
    assert source.count(needle) == 1
    defect = 'z=sqrt_exact(numerator*numerator/nn)*(1 if numerator < 0 else -1)/unit(normal)[2]'
    namespace = dict(vars(escape))
    exec(compile(source.replace(needle, defect), '<r9-rounded-height-ratio>', 'exec'), namespace)
    monkeypatch.setattr(escape, '_candidates', namespace['_candidates'])
    with pytest.raises(AssertionError, match='oracle-exact-plane-height-ratio'):
        test_r9_oracle_escape_height_rounds_the_exact_plane_ratio(escape, F(3, 11))
