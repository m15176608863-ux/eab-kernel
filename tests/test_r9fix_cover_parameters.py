"""Exact parameter certificates survive display underflow.

Oracle: Cartesian line projections computed with Fraction only; no production
projection, distance or construction primitive is used for expected parameters.
"""
from fractions import Fraction as F
from dataclasses import replace
import pytest

from eab.kernel3d import geom3 as G, covers3 as C


def _assert_parameters(c, a, b):
    av = [tuple(map(F,p)) for p in a.verts]
    bv = [tuple(map(F,p)) for p in b.verts]
    if c.kind == "EE":
        pa, qa = (av[i] for i in c.a_feature[1:])
        pb, qb = (bv[i] for i in c.b_feature[1:])
        da, db = tuple(y-x for x,y in zip(pa,qa)), tuple(y-x for x,y in zip(pb,qb))
        w = tuple(x-y for x,y in zip(pa,pb))
        dot = lambda u,v: sum(x*y for x,y in zip(u,v))
        aa, bb, ab = dot(da,da), dot(db,db), dot(da,db)
        det = aa*bb-ab*ab
        expected = ((ab*dot(db,w)-bb*dot(da,w))/det,
                    (aa*dot(db,w)-ab*dot(da,w))/det)
    else:
        p, u, v = ((av[c.a_feature[1]], *(bv[i] for i in c.b_feature[1:]))
                   if c.kind == "VE3" else
                   (bv[c.b_feature[1]], *(av[i] for i in c.a_feature[1:])))
        d = tuple(y-x for x,y in zip(u,v))
        expected = (sum((x-y)*z for x,y,z in zip(p,u,d))/sum(z*z for z in d),)
    assert c.exact_params == expected, "exact parameter certificate"
    assert c.in_extent == all(0 <= s <= 1 for s in expected), "exact parameter extent"
    return any(x != 0 and y == 0 for x,y in zip(expected,c.params))


@pytest.mark.parametrize("kind", ["EE", "VE3", "EV3"])
def test_cover_parameter_underflow_keeps_exact_certificate(kind):
    tiny = F(2)**-1076
    a = G.box(center=(F(2), F(2), F(1)+tiny), half=(F(1,2),)*3)
    b = G.box(half=(F(1,2),)*3)
    if kind == "VE3":
        a, b = b, a
    covers = []
    if kind == "EE":
        covers = [C.ee_cover(a,ea,b,eb) for ea in a.edges() for eb in b.edges()]
    elif kind == "VE3":
        covers = [C.ve3_cover(a,i,b,e) for i in range(8) for e in b.edges()]
    else:
        covers = [C.ev3_cover(a,e,b,i) for e in a.edges() for i in range(8)]
    present = [c for c in covers if c is not None]
    assert present
    assert any([_assert_parameters(c,a,b) for c in present]), "tiny nonzero parameter exercised"


def test_missing_parameter_certificate_internal_mutation_is_caught(monkeypatch):
    original = C.ee_cover
    def mutated(*args, **kwargs):
        c = original(*args, **kwargs)
        return replace(c, exact_params=None) if c is not None else None
    monkeypatch.setattr(C, "ee_cover", mutated)
    with pytest.raises(AssertionError, match="exact parameter certificate"):
        test_cover_parameter_underflow_keeps_exact_certificate("EE")
