"""Exact erosion gates: closed-form sets and an independent cell-cover oracle.

The principal oracle splits a requested square into orthogonal cells and
checks coverage by input rectangles. It does not use the production contact
arrangement, convex clipping, ring containment or global obstacle builder.
"""
from fractions import Fraction as F
import random

import pytest

from eab.kernel2d.erosion import (
    erode_polygon_exact, octagon_element, square_element,
)


L_RING = ((0, 0), (4, 0), (4, 1), (1, 1), (1, 4), (0, 4))
NECK_RING = (
    (0, 0), (2, 0), (2, F(3, 4)), (4, F(3, 4)), (4, 0), (6, 0),
    (6, 2), (4, 2), (4, F(5, 4)), (2, F(5, 4)), (2, 2), (0, 2),
)


def _area(poly):
    return sum((a[0]*b[1]-a[1]*b[0]
                for a, b in zip(poly, poly[1:]+poly[:1])), F(0))/2


def _covered_box(p, delta, rectangles):
    """Exact area-cell coverage of a box; closedness supplies all boundaries."""
    x0, x1, y0, y1 = p[0]-delta, p[0]+delta, p[1]-delta, p[1]+delta
    xs = sorted({x0, x1} | {x for r in rectangles for x in r[:2] if x0 < x < x1})
    ys = sorted({y0, y1} | {y for r in rectangles for y in r[2:] if y0 < y < y1})
    return all(any(a <= (x+xx)/2 <= b and c <= (y+yy)/2 <= d
                   for a, b, c, d in rectangles)
               for x, xx in zip(xs, xs[1:]) for y, yy in zip(ys, ys[1:]))


def _winding_inside(p, poly):
    """Independent integer winding, not the production parity routine."""
    winding = 0
    for a, b in zip(poly, poly[1:]+poly[:1]):
        cross = (b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0])
        if cross == 0 and min(a[0], b[0]) <= p[0] <= max(a[0], b[0]) and min(a[1], b[1]) <= p[1] <= max(a[1], b[1]):
            return True
        if a[1] <= p[1] < b[1] and cross > 0:
            winding += 1
        if b[1] <= p[1] < a[1] and cross < 0:
            winding -= 1
    return winding != 0


@pytest.mark.parametrize("element", ["square", "octagon"])
@pytest.mark.parametrize("delta", [F(0), F(1, 16), F(3, 8)])
def test_convex_rectangle_erosion_closed_form(element, delta):
    result = erode_polygon_exact(((0, 0), (5, 0), (5, 2), (0, 2)), delta, element)
    assert result.status == "ACCEPTED"
    assert result.polygon == ((delta, delta), (5-delta, delta),
                              (5-delta, 2-delta), (delta, 2-delta))
    assert _area(result.polygon) == (5-2*delta)*(2-2*delta)


@pytest.mark.parametrize("delta", [F(1, 16), F(1, 4), F(3, 8)])
def test_concave_erosion_is_not_intersection_of_input_halfplanes(delta):
    result = erode_polygon_exact(L_RING, delta)
    expected = ((delta, delta), (4-delta, delta), (4-delta, 1-delta),
                (1-delta, 1-delta), (1-delta, 4-delta), (delta, 4-delta))
    assert result.status == "ACCEPTED"
    assert result.polygon == expected
    assert _area(result.polygon) == 2*(4-2*delta)*(1-2*delta)-(1-2*delta)**2


@pytest.mark.parametrize("delta", [F(1, 16), F(1, 4), F(3, 8)])
def test_rational_octagon_reflex_bevel_closed_form(delta):
    result = erode_polygon_exact(L_RING, delta, "octagon")
    corner = 1-F(5, 12)*delta
    expected = ((delta, delta), (4-delta, delta), (4-delta, 1-delta),
                (corner, 1-delta), (1-delta, corner),
                (1-delta, 4-delta), (delta, 4-delta))
    assert result.status == "ACCEPTED"
    assert result.polygon == expected
    square = erode_polygon_exact(L_RING, delta)
    assert _area(result.polygon)-_area(square.polygon) == (F(7, 12)*delta)**2/2


@pytest.mark.parametrize("poly,rectangles", [
    (L_RING, ((0, 4, 0, 1), (0, 1, 0, 4))),
    (NECK_RING, ((0, 2, 0, 2), (2, 4, F(3, 4), F(5, 4)), (4, 6, 0, 2))),
])
def test_concave_erosion_against_independent_orthogonal_cell_oracle(poly, rectangles):
    """G0 oracle: rectangle-cell coverage versus production contact arrangement."""
    delta = F(1, 8)
    result = erode_polygon_exact(poly, delta)
    assert result.status == "ACCEPTED"
    for x in range(-1, 50):
        for y in range(-1, 34):
            p = (F(x, 8), F(y, 8))
            assert _winding_inside(p, result.polygon) == _covered_box(p, delta, rectangles)


@pytest.mark.parametrize("element", ["square", "octagon"])
def test_disconnected_erosion_and_exact_thin_neck_are_rejected(element):
    thin = erode_polygon_exact(NECK_RING, F(1, 4), element)
    assert thin.status == "REJECTED"
    assert thin.reason == "LOWER_DIMENSIONAL_REMNANT"
    assert thin.polygon == ()
    split = erode_polygon_exact(NECK_RING, F(3, 8), element)
    assert split.status == "REJECTED"
    assert split.reason == "MULTIPLE_RINGS"
    assert split.polygon == ()
    assert len(split.rings) == 2
    assert all(_area(p) > 0 for p in split.rings)


@pytest.mark.parametrize("delta", [F(1), F(2)])
def test_vanished_and_zero_area_erosion_are_rejected(delta):
    result = erode_polygon_exact(((0, 0), (2, 0), (2, 2), (0, 2)), delta)
    assert result.status == "REJECTED"
    assert result.reason == "EMPTY_OR_DEGENERATE"
    assert not result.polygon


def test_element_vertex_only_containment_misses_an_indentation(monkeypatch):
    """Inject the wrong containment primitive internally, not into its output."""
    from eab.kernel2d import erosion
    p = tuple((F(x), F(y)) for x, y in (
        (0, 0), (6, 0), (6, 6), (4, 6), (4, 2), (2, 2), (2, 6), (0, 6)))
    k = tuple((2*x, 2*y) for x, y in square_element())
    # The asymmetric notch misses the element average, but crosses its edge.
    p = tuple((F(x), F(y)) for x, y in (
        (0, 0), (6, 0), (6, 6), (F(9, 2), 6),
        (F(9, 2), 2), (4, 2), (4, 6), (0, 6)))
    assert not erosion._contains_element(p, k, (F(3), F(3)))
    monkeypatch.setattr(erosion, "_segment_in_open_convex", lambda *args: False)
    with pytest.raises(AssertionError):
        assert not erosion._contains_element(p, k, (F(3), F(3)))


def test_element_vertices_on_cavity_edges_do_not_certify_filled_containment():
    from eab.kernel2d import erosion
    p = tuple((F(x), F(y)) for x, y in (
        (0, 0), (3, 0), (3, 3), (2, 3), (2, 1), (1, 1), (1, 3), (0, 3)))
    k = tuple((x/2, y) for x, y in square_element())
    assert not erosion._contains_element(p, k, (F(3, 2), F(2)))


@pytest.mark.parametrize("element", [square_element(), octagon_element()])
@pytest.mark.parametrize("shift", [F(0), F(1000), F(100000)])
def test_erosion_exact_rigid_motion_and_units(element, shift):
    """Rotate both body and element; an axis-fixed element is not isotropic."""
    generator = random.Random(7901)
    for scale in (F(1, 1024), F(1), F(8)):
        u = F(generator.randrange(1, 8), generator.randrange(9, 16))
        c, s = (1-u*u)/(1+u*u), 2*u/(1+u*u)
        def rotate(p):
            return c*p[0]-s*p[1], s*p[0]+c*p[1]
        def transform(p):
            x, y = rotate(p)
            return scale*x+shift, scale*y-3*shift/7
        baseline = erode_polygon_exact(L_RING, F(1, 4), element)
        moved = erode_polygon_exact(tuple(transform(p) for p in L_RING),
                                    scale/4, tuple(rotate(p) for p in element))
        assert moved.status == "ACCEPTED"
        assert set(moved.polygon) == {transform(p) for p in baseline.polygon}
        assert _area(moved.polygon) == scale**2*_area(baseline.polygon)


def test_input_validation_orientation_zero_and_nonsymmetric_element():
    forward = erode_polygon_exact(L_RING, 0)
    reverse = erode_polygon_exact(tuple(reversed(L_RING)), 0)
    assert forward == reverse
    for delta in (-1, F(-1, 100)):
        with pytest.raises(ValueError, match="nonnegative"):
            erode_polygon_exact(L_RING, delta)
    with pytest.raises(ValueError, match="convex"):
        erode_polygon_exact(L_RING, 1, L_RING)
    with pytest.raises(ValueError, match="origin strictly"):
        erode_polygon_exact(L_RING, 1, ((0, 0), (1, 0), (1, 1), (0, 1)))
    with pytest.raises(ValueError, match="not simple"):
        erode_polygon_exact(((0, 0), (2, 2), (0, 2), (2, 0)), 0)
    asymmetric = ((-1, -1), (2, -1), (2, 1), (-1, 1))
    answer = erode_polygon_exact(((0, 0), (5, 0), (5, 2), (0, 2)), F(1, 4), asymmetric)
    assert answer.polygon == ((F(1, 4), F(1, 4)), (F(9, 2), F(1, 4)),
                              (F(9, 2), F(7, 4)), (F(1, 4), F(7, 4)))
