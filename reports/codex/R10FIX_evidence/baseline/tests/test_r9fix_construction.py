"""R9 exact construction regressions.

Oracles use Cartesian interval truth and rational hull KKT / binary64 midpoint
certificates. They share no production geometry, normal or distance primitive.
"""
from fractions import Fraction as F
import math
import ast
import inspect

import pytest

from eab.kernel3d.geom3 import Polyhedron, tetra
from eab.kernel3d.covers3 import cone_intersection_margin, cones_intersect_relint
from e5b_margin_oracle import check_exact_margin
from test_near_parallel_edges import exact_seg_seg
from construction_oracle import scalar_exact


@pytest.mark.parametrize("multiplier", range(1, 25))
def test_g6i03_cone_margin_rounds_exact_norm_not_nearest_point(multiplier):
    quantum = F(2)**-1074
    delta = multiplier*quantum
    d = scalar_exact(delta)
    assert F(d) == delta
    constraints = ((-F(1), F(1), -delta), (-delta, -F(1), F(1)),
                   (F(1), -delta, -F(1)))
    point = (-delta/3,)*3
    square = delta*delta/3
    assert all(sum(x*y for x, y in zip(point, row)) == square for row in constraints)
    units = next(j for j in range(2*multiplier+1)
                 if F(multiplier*multiplier, 3) < F(2*j+1, 2)**2)
    assert F(2*units-1, 2)**2 < F(multiplier*multiplier, 3) < F(2*units+1, 2)**2
    A = tetra((0., 0., 0.), (1., -1., d), (d, 1., -1.), (-1., d, 1.))
    B = A.reflected()
    assert cones_intersect_relint(A, 0, B, 0) is True
    actual, _ = cone_intersection_margin(A, 0, B, 0)
    assert actual == scalar_exact(units*quantum), ("G6I-03 exact cone margin", multiplier, actual, units)


def _separated_cubes(exponent):
    s = F(2)**exponent
    signs = [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),
             (-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]
    faces = [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
    B = Polyhedron([(p[0]*s, p[1]*min(s, 1), p[2]*min(s, 1)) for p in signs], list(faces))
    A = Polyhedron([(x+4*s,y,z) for x,y,z in B.verts], list(faces))
    return A, B, s


@pytest.mark.parametrize("exponent", [-600, -540, -500, 0, 600])
def test_g6i04_margin_oracle_certifies_root_across_squared_range(exponent):
    A, B, s = _separated_cubes(exponent)
    check_exact_margin(A, B, 3*s, state=-1, minimum_squared=4*s*s)


def test_g6i04_near_parallel_oracle_display_preserves_small_gap():
    gap = 1e-200
    actual = exact_seg_seg((0.,0.,0.), (1.,0.,0.), (0.,gap,0.), (1.,gap,0.))
    assert actual == gap, "G6I-04 oracle display rounds the final root"


def test_g6i03_real_internal_component_first_mutation_is_rejected(monkeypatch):
    import eab.kernel3d.covers3 as production
    source = inspect.getsource(production.cone_intersection_margin)
    old = "return norm_rational(p), noise"
    assert source.count(old) == 1
    namespace = dict(vars(production))
    exec(compile(source.replace(old, "return norm(_float_vector(p)), noise"),
                 "<G6I-03 internal mutant>", "exec"), namespace)
    monkeypatch.setitem(globals(), "cone_intersection_margin", namespace["cone_intersection_margin"])
    with pytest.raises(AssertionError, match="G6I-03 exact cone margin") as caught:
        test_g6i03_cone_margin_rounds_exact_norm_not_nearest_point(1)
    print("G6I-03 internal mutant:", caught.value)


def _premature_sqrt_mutant(value, **kwargs):
    # Deliberate forbidden construction, exclusively for an internal-path tooth.
    return math.sqrt(float(value))


@pytest.mark.parametrize("function_name,assertion", [
    ("body_distance", "default-exact distance construction"),
    ("margin_contacts", "default-exact cover distance"),
])
def test_g6i04_real_internal_squared_first_mutation_is_rejected(monkeypatch, function_name, assertion):
    import eab.margin as production
    source = ast.parse(inspect.getsource(getattr(production, function_name)))
    count = 0
    for node in ast.walk(source):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr == "sqrt_rational"):
            node.func = ast.Name(id="_premature_sqrt_mutant", ctx=ast.Load())
            count += 1
    assert count > 0, "mutant must penetrate the real construction expression"
    namespace = dict(vars(production), _premature_sqrt_mutant=_premature_sqrt_mutant)
    exec(compile(ast.fix_missing_locations(source), "<G6I-04 internal mutant>", "exec"), namespace)
    monkeypatch.setattr(production, function_name, namespace[function_name])
    with pytest.raises(AssertionError, match=assertion) as caught:
        test_g6i04_margin_oracle_certifies_root_across_squared_range(-600)
    print("G6I-04 internal mutant", function_name, ":", caught.value)
