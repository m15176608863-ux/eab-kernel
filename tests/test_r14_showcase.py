"""Run only the existing arch builder AST: no matplotlib/gallery side effects.

Independent oracle: exact Fraction shoelace area/centroid of returned vertices.
"""
import ast
from fractions import Fraction as F
import math
from pathlib import Path

import pytest
from eab.construction import scalar_rational
from eab.numeric_domain import ConstructionDomainError, check_input, check_mu
from eab.numeric_decode import integer
from eab.limit import LimitContact, wrench
from eab.limit_multi import LimitBody, BodyContact


def _builder(replacements=()):
    path = Path(__file__).resolve().parents[1] / "tools/showcase.py"
    source = path.read_text(encoding="utf-8")
    for old, new in replacements:
        assert source.count(old) == 1
        source = source.replace(old, new)
    tree = ast.parse(source)
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "arch_problem")
    namespace = dict(math=math, Fraction=F, scalar_rational=scalar_rational,
                     check_input=check_input, check_mu=check_mu, integer=integer,
                     LimitContact=LimitContact, wrench=wrench, LimitBody=LimitBody, BodyContact=BodyContact)
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), "exec"), namespace)
    return namespace["arch_problem"]


def _expected_load(poly, rho):
    twice_area = sum(F(p[0])*F(q[1])-F(p[1])*F(q[0]) for p, q in zip(poly, poly[1:]+poly[:1]))
    moment_x = sum((F(p[0])+F(q[0]))*(F(p[0])*F(q[1])-F(p[1])*F(q[0])) for p, q in zip(poly, poly[1:]+poly[:1]))
    fy = -rho*twice_area/2
    # Centroid x=moment_x/(3*twice_area); complete gravity moment = -rho*moment_x/6.
    return [0.0, float(fy), float(-rho*moment_x/6)]


@pytest.mark.parametrize("density", [F(2)**-2000, F(2)**401])
def test_r14_showcase_density_input_outside_demo_domain_is_named(density):
    with pytest.raises(ConstructionDomainError, match="rho"):
        _builder()(rho=density)


def test_r14_showcase_complete_gravity_product_underflow_is_named():
    scale = F(2)**-399
    with pytest.raises(ConstructionDomainError):
        _builder()(r_in=scale, r_out=F(9,8)*scale, rho=F(2)**-400)


@pytest.mark.parametrize("exponent", [-399,0,399])
def test_r14_showcase_gravity_uses_exact_returned_vertex_area(exponent):
    scale = F(2)**exponent
    rho = F(2)**-exponent
    blocks, bodies, _, _, _ = _builder()(r_in=scale, r_out=F(9,8)*scale, rho=rho)
    for poly, body in zip(blocks, bodies):
        expected = _expected_load(poly, rho)
        assert body.dead == expected, "demo gravity and moment complete exact shoelace expression"



def test_r14_showcase_removed_density_domain_mutation_is_caught(monkeypatch):
    import sys
    mutant = _builder((('rho = check_input(rho, "showcase.arch.rho")', "rho = Fraction(rho)"),))
    monkeypatch.setattr(sys.modules[__name__], "_builder", lambda: mutant)
    with pytest.raises(pytest.fail.Exception, match="DID NOT RAISE"):
        test_r14_showcase_density_input_outside_demo_domain_is_named(F(2)**401)


def test_r14_showcase_float_shoelace_mutation_is_caught(monkeypatch):
    import sys
    mutant = _builder((("x0, y0 = map(Fraction, P[i])", "x0, y0 = P[i]"),
                       ("x1, y1 = map(Fraction, P[(i + 1) % len(P)])", "x1, y1 = P[(i + 1) % len(P)]")))
    monkeypatch.setattr(sys.modules[__name__], "_builder", lambda: mutant)
    with pytest.raises(AssertionError, match="demo gravity and moment complete exact shoelace expression"):
        test_r14_showcase_gravity_uses_exact_returned_vertex_area(0)
