"""R10/J03 public cone contract.

Oracle uses hand-constructed rays and Fraction dot products to certify the
opposite hemisphere, not production cross/cone predicates or normal builders.
"""
from fractions import Fraction as F

import pytest

from eab.kernel2d.covers import in_cone, normal_cone


@pytest.mark.parametrize("scale,shift,rotation", [
    (F(1), (0, 0), (F(1), F(0))),
    (F(1, 10**9), (10**8, -10**8), (F(3, 5), F(4, 5))),
    (F(10**8), (10**8, -10**8), (F(3, 5), F(4, 5))),
])
def test_public_micro_reflex_cone_rejects_opposite_hemisphere(scale, shift, rotation):
    c, s = rotation
    poly = [(0, 0), (1, 0), (2, F(-1, 100)), (2, 1), (0, 1)]
    transformed = [(scale*(c*x-s*y)+shift[0], scale*(s*x+c*y)+shift[1])
                   for x, y in poly]
    assert normal_cone(transformed, 1, tol=0) is None
    cone = normal_cone(transformed, 1, tol=F(1, 50))
    assert cone is not None
    v = (c*F(1, 200)-s, s*F(1, 200)+c)
    assert all(sum(F(a)*b for a, b in zip(n, v)) < 0 for n in cone)
    assert in_cone(cone, v, tol=F(1, 50)) == -1, "opposite thin sector is exterior"
    assert in_cone(cone, tuple(-x for x in v), tol=F(1, 50)) == 0
    assert in_cone(cone, tuple(-x for x in v), tol=0) == -1


@pytest.mark.parametrize("cone,v,tol,expected", [
    (((1, 0), (0, 1)), (1, 1), 0, 1),
    (((1, 0), (0, 1)), (1, 0), 0, 0),
    (((1, 0), (0, 1)), (-1, -1), 1, -1),
    (((1, 0), (1, 0)), (1, 0), 0, 0),
    (((1, 0), (1, 0)), (-1, 0), 1, -1),
    (((1, 0), (1, F(-1, 100))), (1, 0), F(1, 50), 0),
    (((1, 0), (1, F(-1, 100))), (-1, F(1, 200)), F(1, 50), -1),
    (((1, 0), (0, -1)), (-1, 1), 1, -1),
    (((1, 0), (-1, 0)), (0, 1), 1, -1),
    (((1, 0), (-1, 1)), (0, 1), 0, 1),
])
def test_in_cone_explicit_window_never_creates_reflex_strict_interior(cone, v, tol, expected):
    assert in_cone(cone, v, tol=tol) == expected


@pytest.mark.parametrize("cone", [((0, 0), (1, 0)), ((1, 0), (0, 0))])
def test_in_cone_zero_boundary_ray_is_rejected(cone):
    with pytest.raises(ValueError, match="zero"):
        in_cone(cone, (1, 1))


def test_reflex_strict_gate_kills_original_source_mutation(monkeypatch):
    import inspect
    import eab.kernel2d.covers as module
    source = inspect.getsource(module.in_cone)
    source = source.replace("    if not _cone_nonreflex(lo, hi, w2):\n        return -1\n", "")
    source = source.replace("if cross(lo, hi) > 0 and cross(lo, v)", "if cross(lo, v)")
    namespace = dict(vars(module))
    exec(compile(source, "<r10_original_reflex_mutation>", "exec"), namespace)
    monkeypatch.setitem(globals(), "in_cone", namespace["in_cone"])
    with pytest.raises(AssertionError, match="opposite thin sector is exterior"):
        test_public_micro_reflex_cone_rejects_opposite_hemisphere(F(1), (0, 0), (F(1), F(0)))


def test_local_2d_cover_reflex_windows_do_not_create_strict_cover():
    from eab.kernel2d.covers import ve_cover, vv_cover
    a = [(0, 0), (1, 0), (2, F(-1, 100)), (2, 1), (0, 1)]
    b = [(0, -2), (1, -2), (1, -1), (0, -1)]
    assert ve_cover(a, 1, b, 2, cone_tol=0) is None
    cover = ve_cover(a, 1, b, 2, cone_tol=F(1, 50))
    assert cover is not None and not cover.strict
    assert all(vv_cover(a, 1, b, j, cone_tol=F(1, 50)) is None for j in range(4))


@pytest.mark.parametrize("height", [F(1, 100), F(1, 2**80), F(1, 2)])
@pytest.mark.parametrize("scale,shift", [(F(1), 0), (F(1, 10**9), 10**8), (F(10**8), -10**8)])
def test_public_3d_reflex_arc_rejects_inverse_and_strict_window(height, scale, shift):
    from eab.kernel3d.geom3 import Polyhedron
    from eab.kernel3d.covers3 import edge_arc_contains, vertex_cone_contains
    # Declared roof z=1+h*max(0,x+y-1). The 5->7 ridge is reflex for h>0;
    # its two explicit triangle normals have oriented triple -2h.
    raw = [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0),
           (0, 0, 1), (1, 0, 1), (1, 1, 1+height), (0, 1, 1)]
    faces = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
             (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    def transform(p):
        x, y, z = p
        return (scale*(3*x-4*y)/5+shift, scale*(4*x+3*y)/5-shift, scale*z+shift)
    body = Polyhedron([transform(p) for p in raw], faces)
    for direction in [(0, 0, -1), (0, 0, 1)]:
        assert edge_arc_contains(body, (5, 7), direction, tol=F(1, 50)) == -1
    # At vertex 5 the downward incident edge certifies positive dot with -z.
    assert vertex_cone_contains(body, 5, (0, 0, -1), tol=F(1, 50)) == -1
