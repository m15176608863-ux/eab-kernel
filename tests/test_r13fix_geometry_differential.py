"""Public geometric constructions versus independent rational formulas.

Oracle primitives: local Fraction determinants, projection, shoelace/moments,
and construction_oracle's independent binary64-cell search. No production
geometric helper is used to compute expected values. Each scalar/component is
compared exactly (not absolute-tolerance allclose). Transcendental angles are
explicitly libm-coefficient contracts, not correctly rounded real atan2 claims.
"""
from fractions import Fraction as F
import inspect
import math
import textwrap

import pytest

from construction_oracle import scalar_exact, sqrt_exact, unit_exact
from eab.kernel2d import geom as G2, covers as C2
from eab.kernel2d import g0 as Q2
from eab.kernel3d import geom3 as G3, covers3 as C3, exact_geom as E3


def q(v):
    return tuple(F(x) for x in v)


def minus(a, b):
    return tuple(x-y for x, y in zip(q(a), q(b)))


def times(a, b):
    return sum((x*y for x, y in zip(q(a), q(b))), F(0))


def wedge(a, b):
    a, b = q(a), q(b)
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def newell(verts, face):
    p = [q(verts[i]) for i in face]
    return tuple(sum((wedge(a, b)[k] for a, b in zip(p, p[1:]+p[:1])), F(0)) for k in range(3))


def fv(values):
    return tuple(scalar_exact(x) for x in values)


def poly2(s):
    return [(s, 2*s), (4*s, 2*s), (4*s, 6*s), (s, 6*s)]


def poly3(s):
    # Noncentral, non-cubic, exact rational shear; no production box constructor.
    vertices = [(s*(1+2*x+y), s*(2+3*y+z), s*(3+4*z))
                for x, y, z in ((0,0,0),(1,0,0),(1,1,0),(0,1,0),
                                (0,0,1),(1,0,1),(1,1,1),(0,1,1))]
    faces = [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
    return G3.Polyhedron(vertices, faces)


@pytest.mark.parametrize("dimension", [2, 3])
@pytest.mark.parametrize("scale", [math.ldexp(1., -538), 1., math.ldexp(1., 1020)])
def test_public_dot_cross_round_after_cancellation(dimension, scale):
    module = G2 if dimension == 2 else G3
    if scale > 1:
        a, b = (scale, scale), (scale, -scale)
        expected_dot = 0.
        c, d = (scale, scale), (scale, scale)
    else:
        a, b = (scale, scale), (2*scale, 2*scale)
        expected_dot = scalar_exact(times(a, b))
        c, d = (scale, -scale), (2*scale, 2*scale)
    if dimension == 3:
        a, b, c, d = (*(a), 0.), (*(b), 0.), (*(c), 0.), (*(d), 0.)
    assert module.dot(a, b) == expected_dot, "public dot exact final construction"
    expected_cross = F(c[0])*F(d[1])-F(c[1])*F(d[0])
    actual = module.cross(c, d)
    assert (actual if dimension == 2 else actual[2]) == scalar_exact(expected_cross), "public cross exact final construction"


@pytest.mark.parametrize("dimension", [2, 3])
def test_public_dot_cross_reject_unrepresentable_nonzero(dimension):
    module = G2 if dimension == 2 else G3
    tiny = math.ulp(0.)
    a, b = (tiny, 0.), (tiny, 0.)
    c, d = (tiny, 0.), (0., tiny)
    if dimension == 3:
        a, b, c, d = (*a, 0.), (*b, 0.), (*c, 0.), (*d, 0.)
    with pytest.raises(ArithmeticError):
        module.dot(a, b)
    with pytest.raises(ArithmeticError):
        module.cross(c, d)


@pytest.mark.parametrize("exponent", [-1070, -600, 0, 600, 1018])
def test_public_norm_normal_and_edge_components_match_rational_reference(exponent):
    s = F(2)**exponent
    for module, vector in ((G2, (3*s, 4*s)), (G3, (3*s, -4*s, 12*s))):
        assert module.norm(vector) == sqrt_exact(times(vector, vector)), "norm final component"
        assert module.unit(vector) == unit_exact(vector), "unit exact components"
    P = poly2(s)
    for i, p in enumerate(P):
        d = minus(P[(i+1)%4], p)
        assert G2.outward_normal(P, i) == unit_exact((d[1], -d[0])), "2D edge normal"
        cone = C2.normal_cone(P, i)
        prev = minus(p, P[i-1])
        assert cone == (unit_exact((prev[1], -prev[0])), unit_exact((d[1], -d[0])))
    P = poly3(s)
    for fi, face in enumerate(P.faces):
        assert P.face_normal(fi) == unit_exact(newell(P.verts, face)), "3D face normal"
    for edge in P.edges():
        assert P.edge_dir(edge) == unit_exact(minus(P.verts[edge[1]], P.verts[edge[0]])), "3D edge direction"
    for vi in range(len(P.verts)):
        expected = [unit_exact(minus(P.verts[e[1] if e[0] == vi else e[0]], P.verts[vi]))
                    for e in P.edges() if vi in e]
        assert P.vertex_edge_dirs(vi) == expected, "incident edge direction components"


@pytest.mark.parametrize("exponent", [-537, -530, 0, 500, 509])
def test_public_area_turn_side_match_exact_shoelace(exponent):
    s = F(2)**exponent
    P = poly2(s)
    area2 = sum((F(a[0])*F(b[1])-F(a[1])*F(b[0]) for a,b in zip(P,P[1:]+P[:1])), F(0))
    assert G2.signed_area(P) == scalar_exact(area2/2), "signed area final rounding"
    for i in range(4):
        u, v = minus(P[i], P[i-1]), minus(P[(i+1)%4], P[i])
        determinant = u[0]*v[1]-u[1]*v[0]
        assert G2.vertex_turn(P, i) == scalar_exact(determinant), "vertex turn final rounding"
    # Force public floating-output overload without changing exact coordinates.
    p, a, b = (tuple(scalar_exact(x) for x in v) for v in (P[2], P[0], P[1]))
    u, v = minus(b, a), minus(p, a)
    assert G2.point_side(p, a, b) == scalar_exact(u[0]*v[1]-u[1]*v[0]), "point-side final rounding"
    assert G2.centroid(P) == fv((F(5)*s/2, 4*s)), "polygon centroid moments"
    body = poly3(s)
    for fi, face in enumerate(body.faces):
        n = newell(body.verts, face)
        assert body.face_area(fi) == sqrt_exact(times(n, n)/4), "face area final halving"


@pytest.mark.parametrize("exponent", [-359, -350, 0, 330, 338])
def test_public_volume_and_centroid_match_independent_tetrahedral_moments(exponent):
    P = poly3(F(2)**exponent)
    volumes, moments = [], [F(0), F(0), F(0)]
    for face in P.faces:
        for j in range(1, len(face)-1):
            a,b,c = (q(P.verts[k]) for k in (face[0], face[j], face[j+1]))
            v = times(a, wedge(b,c)); volumes.append(v)
            for k in range(3): moments[k] += v*(a[k]+b[k]+c[k])
    volume6 = sum(volumes, F(0))
    assert P.volume() == scalar_exact(volume6/6), "volume exact final sum"
    assert P.centroid() == fv(x/(4*volume6) for x in moments), "centroid exact first moments"


@pytest.mark.parametrize("exponent", [-1070, 0, 1018])
def test_public_2d_cover_fields_match_exact_projection_and_gap(exponent):
    s = F(2)**exponent
    A, B = poly2(s), [(x+5*s,y) for x,y in poly2(s)]
    covers = list(C2.enumerate_covers(A, B, window=math.inf))
    assert {c.kind for c in covers} == {"VE", "EV"}, "both 2D projected constructor families exercised"
    corner = [(x,y+6*s) for x,y in B]
    vv = C2.vv_cover(A,2,corner,0)
    assert vv is not None and vv.kind == "VV", "2D vertex pair constructor exercised"
    delta = minus(A[2],corner[0])
    assert vv.gap == sqrt_exact(times(delta,delta)), "VV gap"
    assert vv.normal == unit_exact(delta), "VV normal"
    assert vv.point_a == A[2] and vv.point_b == corner[0]
    for c in covers:
        if c.kind == "VV":
            delta = minus(A[c.a_index], B[c.b_index])
            assert c.gap == sqrt_exact(times(delta, delta)), "VV gap"
            assert c.normal == unit_exact(delta), "VV normal"
            assert c.point_a == A[c.a_index] and c.point_b == B[c.b_index]
            continue
        vertex, ring, index = (A[c.a_index], B, c.b_index) if c.kind == "VE" else (B[c.b_index], A, c.a_index)
        origin, end = q(ring[index]), q(ring[(index+1)%len(ring)])
        d, w = minus(end, origin), minus(vertex, origin)
        along = times(w,d)/times(d,d)
        witness = fv(origin[k]+along*d[k] for k in range(2))
        n = (d[1], -d[0]); numerator = times(n,w)
        assert c.param == scalar_exact(along), "cover projection parameter"
        assert c.point == witness, "cover projection point"
        assert c.gap == (-1 if numerator < 0 else 1)*sqrt_exact(numerator*numerator/times(n,n)), "cover signed gap"
        assert c.normal == unit_exact(n if c.kind == "VE" else tuple(-x for x in n)), "cover normal"
        assert C2.facet_gap(A,B,c.label(),(0,0)) == c.gap
    distance, _ = Q2.brute_polygon_distance(A,B)
    assert distance == scalar_exact(2*s), "2D independent distance output"


@pytest.mark.parametrize("exponent", [-1070, 0, 1018])
def test_public_3d_closest_point_and_distance_constructions(exponent):
    s = F(2)**exponent
    pts = [(3*s,-s,0),(3*s,s,0),(3*s,0,2*s)]
    assert C3.closest_point_of_convex_hull_to_origin(pts) == fv((3*s,0,0)), "closest hull exact vector"
    assert C3.cone_relint_direction(pts) == (-1.,0.,0.), "cone direction exact vector"
    # Exact-distance primitive witnesses are independently chosen active sets.
    a,b,c = (0,0,0),(4*s,0,0),(0,4*s,0)
    point = (s,s,3*s)
    assert E3.point_segment_distance_squared(point,a,b) == 10*s*s
    assert E3.point_triangle_distance_squared(point,(a,b,c)) == 9*s*s
    assert E3.segment_distance_squared(a,b,(2*s,-s,3*s),(2*s,s,3*s)) == 9*s*s
    # Anisotropic rational solids make nearest feature unique in the x direction.
    A = G3.box(center=(0,0,0),half=(s,s,s))
    B = G3.box(center=(5*s,0,0),half=(s,s,s))
    assert G3.brute_feature_distance(A,B,squared=True) == 9*s*s
    assert G3.brute_feature_distance(A,B) == scalar_exact(3*s), "surface distance once-rounded"


@pytest.mark.parametrize("exponent", [-1070, 0, 1018])
def test_public_facet_normal_and_support_gap_are_independently_derived(exponent):
    s = F(2)**exponent
    A = G3.box(center=(0,0,0),half=(s,s,s))
    B = G3.box(center=(5*s,0,0),half=(s,s,s))
    x = (8*s,2*s,-3*s)
    expected = []
    for body, other, flip in ((B,A,False),(A,B,True)):
        for face in body.faces:
            n = newell(body.verts,face)
            if flip: n = tuple(-v for v in n)
            chosen = max(other.verts,key=lambda p:times(n,p)) if flip else min(other.verts,key=lambda p:times(n,p))
            p = minus(chosen,body.verts[face[0]]) if flip else minus(body.verts[face[0]],chosen)
            numerator = times(n,minus(x,p))
            expected.append((-1 if numerator < 0 else 1)*sqrt_exact(numerator*numerator/times(n,n)))
    assert C3.support_gaps3(A,B,x) == expected, "support signed distances all components"
    # Axis-aligned cubes have merged face/face labels; plane geometry is unique.
    for label in C3.local_facets3(A,B):
        n,p = C3.facet_plane3(A,B,label)
        # Independent support identity, rather than reusing returned plane point.
        supporting = max(times(n,b) for b in B.verts)-min(times(n,a) for a in A.verts)
        assert times(n,p) == supporting, "facet exact support plane"
        assert C3.facet_normal3(A,B,label) == unit_exact(n)
        numerator = times(n,x)-supporting
        assert C3.facet_gap3(A,B,label,x) == (-1 if numerator < 0 else 1)*sqrt_exact(numerator*numerator/times(n,n))


@pytest.mark.parametrize("exponent", [-1070, -537, 0, 509, 1018])
def test_all_six_public_3d_cover_constructors_compare_every_numeric_field(exponent):
    s = F(2)**exponent
    # Anisotropy makes subnormal gaps and near-overflow gaps coexist with a
    # representable face area, rather than failing early on an unrelated area.
    A = G3.box(center=(3*s,0,0),half=(s,1,1))
    B = G3.box(center=(0,0,0),half=(s,1,1))
    cases = [(C3.vf_cover(A,0,B,3), "VF", (), 4.),
             (C3.fv_cover(A,5,B,1), "FV", (), 4.),
             (C3.ee_cover(A,(0,3),B,(1,5)), "EE", (0.,0.), None),
             (C3.ve3_cover(A,0,B,(1,2)), "VE3", (0.,), None),
             (C3.ev3_cover(A,(0,3),B,1), "EV3", (0.,), None)]
    for c,kind,parameters,area in cases:
        assert c is not None and c.kind == kind, "all six public cover paths exercised"
        assert c.normal == (1.,0.,0.), "cover normal components"
        assert c.gap == scalar_exact(s), "cover gap component"
        assert c.point_a == fv((2*s,-1,-1)), "cover A witness components"
        assert c.point_b == fv((s,-1,-1)), "cover B witness components"
        assert c.params == parameters, "cover line parameters"
        assert c.area == area, "cover area final component"
        assert c.exact_gap_squared == s*s and c.exact_gap_sign == 1, "cover exact gap certificate"
        if area is not None:
            assert c.exact_area_squared == 16, "cover exact area certificate"
    A = G3.box(center=(3*s,3*s,3*s),half=(s,s,s))
    B = G3.box(center=(0,0,0),half=(s,s,s))
    c = C3.vv3_cover(A,0,B,6)
    assert c is not None and c.kind == "VV3"
    assert c.normal == unit_exact((s,s,s)), "VV3 normal components"
    assert c.gap == sqrt_exact(3*s*s), "VV3 gap component"
    assert c.point_a == fv((2*s,2*s,2*s)) and c.point_b == fv((s,s,s))
    assert c.exact_gap_squared == 3*s*s and c.exact_gap_sign == 1


@pytest.mark.parametrize("exponent", [-1070, 0, 1018])
def test_public_angles_and_exact_topology_constructors_keep_scaled_coordinates(exponent):
    s = F(2)**exponent
    P = poly2(s)
    assert G2.turn_angle(P,1) == math.pi/2
    assert C2.cone_width(((s,0),(0,s))) == math.pi/2
    assert G3.angle_between((s,0,0),(0,s,0)) == math.pi/2
    assert G2.interior_point(P) == (2*s,F(10)*s/3), "exact interior witness coordinates"
    # Returned hulls select supplied coordinates; no geometric constructor may
    # silently round a rational source point even below the binary64 range.
    assert set(G2.convex_hull(P+[G2.interior_point(P)])) == set(P)
    body = G3.box(center=(0,0,0),half=(s,s,s))
    assert all(body.dihedral_turn(edge) == math.pi/2 for edge in body.edges())
    expected = {q(p) for p in body.verts}
    assert set(G3.convex_hull_3d(body.verts).verts) == expected
    H, band = G3.convex_hull_3d_eps(body.verts)
    assert set(H.verts) == expected and band == 0.
    assert set(G3.exact_convex_view(body).verts) == expected
    assert set(G3.exact_surface(body).verts) == expected
    assert set(G3.merge_coplanar(body).verts) == expected


@pytest.mark.parametrize("exponent", [-1070, -600, 0, 600, 1018])
def test_relative_noise_diagnostics_do_not_round_away_scale_before_ratio(exponent):
    s = F(2)**exponent
    P = G3.box(center=(0,0,0),half=(s,s,s))
    coefficient = F(64)*F(math.ulp(1.))
    expected_edge = scalar_exact(coefficient/2)
    expected_face = scalar_exact(coefficient)
    for edge in P.edges():
        assert P.edge_noise(edge) == expected_edge, "edge relative diagnostic exact ratio"
        assert P.dihedral_noise(edge) == 2*expected_face, "dihedral relative diagnostic sum"
    for fi in range(6):
        assert P.face_noise(fi) == expected_face, "face relative diagnostic exact final ratio"
    for vi in range(8):
        assert [value for _,value in P.vertex_edges(vi)] == [expected_edge]*3, "vertex edge relative diagnostic ratios"


@pytest.mark.parametrize("function", [G2.round_floor,G3.noise_floor])
def test_absolute_noise_diagnostic_rejects_unrepresentable_nonzero(function):
    with pytest.raises(ArithmeticError):
        function(math.ulp(0.))


def test_public_face_area_at_overflow_edge_rounds_final_area():
    P = G3.Polyhedron([(0,0,0),(F(2)**512,0,0),(0,F(2)**512,0)],[(0,1,2)])
    try:
        actual = P.face_area(0)
    except OverflowError as error:
        raise AssertionError("representable final face area rejected") from error
    assert actual == scalar_exact(F(2)**1023), "exact final face area"


def test_geometry_differential_rejects_real_internal_early_sqrt_mutation(monkeypatch):
    source = textwrap.dedent(inspect.getsource(G3.Polyhedron.face_area))
    old = "return _eg.sqrt_rational(_eg.dot(n, n) / 4)"
    assert old in source
    scope = dict(vars(G3))
    exec(source.replace(old,"return 0.5 * _eg.sqrt_rational(_eg.dot(n, n), allow_underflow=True)"),scope)
    monkeypatch.setattr(G3.Polyhedron,"face_area",scope["face_area"])
    # 2*area must overflow while the requested area fits: inject before output.
    with pytest.raises(AssertionError,match="representable final face area rejected") as caught:
        test_public_face_area_at_overflow_edge_rounds_final_area()
    print("face_area internal early-sqrt mutant:", caught.value)


def test_geometry_differential_dot_gate_rejects_internal_float_products(monkeypatch):
    monkeypatch.setattr(G3,"dot",lambda a,b:a[0]*b[0]+a[1]*b[1]+a[2]*b[2])
    with pytest.raises(AssertionError,match="public dot exact final construction") as caught:
        test_public_dot_cross_round_after_cancellation(3, math.ldexp(1.,1020))
    print("dot internal float-product mutant:", caught.value)


def test_geometry_differential_cross_gate_rejects_internal_float_products(monkeypatch):
    monkeypatch.setattr(G2,"cross",lambda a,b:a[0]*b[1]-a[1]*b[0])
    with pytest.raises(AssertionError,match="public cross exact final construction") as caught:
        test_public_dot_cross_round_after_cancellation(2, math.ldexp(1.,-538))
    print("cross internal float-product mutant:", caught.value)


def test_noise_differential_gate_rejects_internal_early_absolute_floor(monkeypatch):
    source = textwrap.dedent(inspect.getsource(G3.Polyhedron.edge_noise))
    start = source.index("    d = exact_edge_vector")
    old = ("    d = exact_edge_vector(self, e)\n"
           "    coefficient = 64.*math.ulp(1.)*float(coord_scale(*self.verts))\n"
           "    return coefficient / norm(d)\n")
    scope = dict(vars(G3))
    exec(source[:start]+old,scope)
    monkeypatch.setattr(G3.Polyhedron,"edge_noise",scope["edge_noise"])
    with pytest.raises(AssertionError,match="edge relative diagnostic exact ratio") as caught:
        test_relative_noise_diagnostics_do_not_round_away_scale_before_ratio(-1070)
    print("edge_noise internal early-floor mutant:", caught.value)


@pytest.mark.parametrize("exponent", [-1074, -600, 0, 600, 1021])
def test_public_float_coordinate_operations_match_independent_components(exponent):
    s = math.ldexp(1.,exponent)
    for module,dimension in ((G2,2),(G3,3)):
        a,b = (s,)*dimension, (2*s,)*dimension
        assert module.add(a,b) == fv(F(x)+F(y) for x,y in zip(a,b)), "coordinate add final components"
        assert module.sub(a,b) == fv(F(x)-F(y) for x,y in zip(a,b)), "coordinate subtract final components"
    assert G2.translate([(s,2*s)],(2*s,s)) == [fv((3*F(s),3*F(s)))], "2D translated components"
    assert G3.mul((s,2*s,3*s),2.) == fv((2*F(s),4*F(s),6*F(s))), "coordinate product final components"
    body = G3.box(center=(s,2*s,3*s),half=(s,s,s))
    expected = [(F(s)*(1+x),F(s)*(2+y),F(s)*(3+z))
                for x,y,z in ((-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),
                              (-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1))]
    assert body.verts == [fv(p) for p in expected], "box exact coordinate components"
    assert body.translated((s,s,s)).verts == [fv(x+F(s) for x in p) for p in expected]


def test_public_float_coordinate_operations_reject_nonfinite_or_erased_outputs():
    maximum = math.nextafter(math.inf,0.)
    for module,dimension in ((G2,2),(G3,3)):
        a,b = (maximum,)*dimension, (maximum,)*dimension
        with pytest.raises(OverflowError): module.add(a,b)
        with pytest.raises(OverflowError): module.sub(a,tuple(-x for x in b))
    with pytest.raises(ArithmeticError): G3.mul((math.ulp(0.),0.,0.),.5)
    with pytest.raises(OverflowError): G3.mul((maximum,0.,0.),2.)
    with pytest.raises(OverflowError): G2.translate([(maximum,0.)],(maximum,0.))
    with pytest.raises(OverflowError): G3.box(center=(maximum,0.,0.),half=(maximum,1.,1.))
    body = G3.box(center=(maximum,0.,0.),half=(0.,1.,1.))
    with pytest.raises(OverflowError): body.translated((maximum,0.,0.))


def test_coordinate_range_gate_rejects_internal_unchecked_addition(monkeypatch):
    monkeypatch.setattr(G2,"add",lambda a,b:(a[0]+b[0],a[1]+b[1]))
    with pytest.raises(pytest.fail.Exception,match="DID NOT RAISE") as caught:
        test_public_float_coordinate_operations_reject_nonfinite_or_erased_outputs()
    print("coordinate internal unchecked-add mutant:",caught.value)
