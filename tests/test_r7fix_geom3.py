"""R7 3D construction regressions.

The primary oracles use fixed slab inequalities, axis-product integration and
rational rounding midpoints, not eab projection, hull, distance or triangulation.
"""
from construction_oracle import scalar_exact
from fractions import Fraction as F
import inspect
import math
import textwrap

import pytest

from eab.kernel3d import geom3 as G
from eab.kernel3d import covers3 as C
from eab import margin as M

FACES = [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
TRIS = [(1,0,3),(3,2,1),(7,4,5),(5,6,7),(4,0,1),(1,5,4),
        (5,1,2),(2,6,5),(6,2,3),(3,7,6),(7,3,0),(0,4,7)]
AV = [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,0),(1,-1,1),(1,1,0),(-1,1,1)]
BV = [(1,-1,2),(1,1,1),(-1,1,2),(-1,-1,1),(1,-1,4),(1,1,4),(-1,1,4),(-1,-1,4)]
I = ((1,0,0),(0,1,0),(0,0,1))
R = ((F(3,5),0,F(4,5)),(0,1,0),(-F(4,5),0,F(3,5)))
U = F(1,2**1074)


def _ridge_pair(gap=F(2), translation=0, rotation=I, scale=F(1), triangles=False):
    def pose(p):
        return tuple(F(translation)+scale*sum(F(rotation[k][j])*F(p[j]) for j in range(3)) for k in range(3))
    faces = TRIS if triangles else FACES
    return (G.Polyhedron([pose(p) for p in AV], list(faces)),
            G.Polyhedron([pose((x,y,F(z)+gap)) for x,y,z in BV], list(faces)))


@pytest.mark.parametrize('translation,rotation,scale', [(0,I,F(1)), (10**6,R,F(3,2)), (10**5,R,F(1,2**20))])
def test_g6g04_folded_internal_ridges_attain_slab_distance(translation, rotation, scale):
    # z(A)<=1, z(B)>=3, and manual ridge midpoints attain (0,0,1)/(0,0,3).
    assert tuple((F(AV[5][k])+AV[7][k])/2 for k in range(3)) == (0,0,1)
    assert all(sum(rotation[k][i]*rotation[k][j] for k in range(3)) == (i==j) for i in range(3) for j in range(3))
    a,b = _ridge_pair(translation=translation,rotation=rotation,scale=scale)
    assert G.brute_feature_distance(a,b) == scalar_exact(2*scale), 'folded-ridge-slab-distance'
    at,bt = _ridge_pair(translation=translation,rotation=rotation,scale=scale,triangles=True)
    assert G.brute_feature_distance(at,bt) == G.brute_feature_distance(a,b), 'same-surface-source-independence'


@pytest.mark.parametrize('height,expected', [(F(29,10)*U,scalar_exact(U)), (F(31,10)*U,scalar_exact(2*U)), (F(7,2)*U,scalar_exact(2*U))])
def test_g6g05_face_area_rounds_after_final_halving(height,expected):
    p = G.Polyhedron([(0,0,0),(1,0,0),(1,height,0)],[(0,1,2)])
    assert p.face_area(0) == expected, 'area-final-rounding'


def test_g6g05_face_area_underflow_is_not_silent_zero():
    p = G.Polyhedron([(0,0,0),(1,0,0),(1,U,0)],[(0,1,2)])
    with pytest.raises(ArithmeticError, match='binary64'):
        p.face_area(0)


@pytest.mark.parametrize('sign', [-1,1])
@pytest.mark.parametrize('method', ['facet','support'])
def test_g6g05_facet_gap_rounds_after_normal_length_division(sign,method):
    t = G.Polyhedron([(0,0,0),(1,0,0),(0,1,0),(0,0,1)],[(0,2,1),(0,1,3),(0,3,2),(1,2,3)])
    x = (F(1)+sign*F(51,20)*U,0,0)
    # 1 < (51/20)^2/3 < (3/2)^2 certifies nearest subnormal is U.
    assert 1 < F(51,20)**2/3 < F(3,2)**2
    gap = C.facet_gap3(t,t,('VF',('vertex',0),('face',3)),x) if method=='facet' else C.support_gaps3(t,t,x)[3]
    assert gap == sign*scalar_exact(U), 'signed-gap-final-rounding'


@pytest.mark.parametrize('gap,translation,rotation,swap', [
    (F(1,10**9),0,I,False), (F(1,10**9),10**8,I,False),
    (F(1,5*10**7),10**8,R,False), (F(1,5*10**7),10**8,R,True)])
def test_g6g06_margin_normal_does_not_subtract_display_points(gap,translation,rotation,swap):
    a,b = _ridge_pair(gap,translation,rotation,triangles=True)
    if swap:
        a,b = b,a
    expected = tuple((1 if swap else -1)*scalar_exact(rotation[k][2]) for k in range(3))
    cs = M.margin_contacts(a,b,delta=2*gap,tol=0)
    assert len(cs) == 1 and cs[0].exact_distance_squared == gap*gap
    assert cs[0].distance == scalar_exact(gap)
    assert cs[0].normal == pytest.approx(expected,abs=2e-16), 'exact-local-margin-normal'


@pytest.mark.parametrize('exponent', [-600,600])
def test_g6g08_mass_properties_use_exact_products_before_final_rounding(exponent):
    s,h = math.ldexp(1.,exponent), math.ldexp(1.,-exponent)
    p = G.box(half=(s,s,h))
    # Independent integration over a Cartesian product of three intervals.
    expected = scalar_exact(8*F(s)*F(s)*F(h))
    assert p.volume() == expected, 'axis-product-volume'
    assert p.centroid() == (0.,0.,0.), 'axis-product-centroid'


def test_g6g08_centroid_retains_cancellation_even_when_volume_is_representable():
    s,h = 2.**-600,2.**600
    assert G.box(half=(s,s,h)).centroid() == (0.,0.,0.), 'axis-product-centroid'


@pytest.mark.parametrize('shift', [0,1,2])
def test_g6g08_volume_independent_of_cyclic_face_ring_start(shift):
    s,h = 2.**-600,2.**600
    faces = [(0,2,1),(0,1,3),(0,3,2),(1,2,3)]
    faces[-1] = faces[-1][shift:]+faces[-1][:shift]
    p = G.Polyhedron([(0.,0.,0.),(0.,0.,h),(s,0.,0.),(0.,s,0.)],faces)
    assert p.volume() == scalar_exact(F(s)*F(s)*F(h)/6), 'tetra-ring-independent-volume'
    assert p.centroid() == (s/4,s/4,h/4), 'tetra-axis-centroid'


def test_r7fix_unit_retains_extreme_components_before_normalization():
    # Exact z lies above midpoint 3U/2 although rounding z first yields U.
    v = (F(1),F(1),F(43,20)*U)
    assert v[2]**2/(2+v[2]**2) > (F(3,2)*U)**2
    assert G.unit(v)[2] == scalar_exact(2*U), 'normalized-component-final-rounding'
    assert C._qunit(v)[2] == scalar_exact(2*U), 'cover-normal-final-rounding'


def test_r7fix_inflated_normal_retains_extreme_final_component():
    point = G.Polyhedron([(0,0,0)],[])
    assert M.inflated_normal(point,(F(1),F(1),F(43,20)*U))[2] == scalar_exact(2*U), 'inflated-normal-final-rounding'


def test_r7fix_face_normal_does_not_discard_one_underflowed_cross_component():
    s = 2.**-600
    p = G.Polyhedron([(0.,0.,0.),(s,0.,1.),(0.,s,1.)],[(0,1,2)])
    # n=(-s,-s,s*s); the unit z component is s/sqrt(2+s*s), not zero.
    assert p.face_normal(0)[2] == pytest.approx(s/math.sqrt(2), rel=2e-16,abs=0), 'face-normal-local-small-component'


def _inject(monkeypatch,module,name,old,new):
    original = getattr(module,name)
    source = textwrap.dedent(inspect.getsource(original))
    assert old in source
    namespace = dict(vars(module))
    exec(compile(source.replace(old,new),'<r7fix-internal-mutation-'+name+'>','exec'),namespace)
    monkeypatch.setattr(module,name,namespace[name])


def test_g6g04_internal_mutation_dropping_folded_ridges_is_caught(monkeypatch):
    _inject(monkeypatch,G,'brute_feature_distance','_surface_distance_edges(A)','A.edges()')
    with pytest.raises(AssertionError,match='folded-ridge-slab-distance'):
        test_g6g04_folded_internal_ridges_attain_slab_distance(0,I,F(1))


def test_g6g05_internal_mutation_rounding_norm_before_halving_is_caught(monkeypatch):
    source = textwrap.dedent(inspect.getsource(G.Polyhedron.face_area))
    namespace = dict(vars(G))
    exec(compile(source.replace('_eg.sqrt_rational(_eg.dot(n, n) / 4)',
                               '_eg.sqrt_rational(_eg.dot(n, n)) / 2'),'<r7fix-area-mutation>','exec'),namespace)
    monkeypatch.setattr(G.Polyhedron,'face_area',namespace['face_area'])
    with pytest.raises(AssertionError,match='area-final-rounding'):
        test_g6g05_face_area_rounds_after_final_halving(F(29,10)*U,scalar_exact(U))


def test_g6g05_internal_mutation_rounding_plane_numerator_is_caught(monkeypatch):
    _inject(monkeypatch,C,'facet_gap3','numerator = dot(n, sub(_qvector(x), p))',
            'numerator = F(float(dot(n, sub(_qvector(x), p))))'.replace('F(','Fraction('))
    with pytest.raises(AssertionError,match='signed-gap-final-rounding'):
        test_g6g05_facet_gap_rounds_after_normal_length_division(1,'facet')


def test_g6g06_internal_mutation_reverting_to_display_normal_is_caught(monkeypatch):
    _inject(monkeypatch,M,'cover_witness',
            'if c.in_extent and c.exact_gap_sign is not None and c.normal is not None:',
            'if False:')
    with pytest.raises(AssertionError,match='exact-local-margin-normal'):
        test_g6g06_margin_normal_does_not_subtract_display_points(F(1,10**9),10**8,I,False)


def test_g6g08_internal_mutation_rounding_before_cross_product_is_caught(monkeypatch):
    # Restore genuinely early float cross products inside the mass reduction.
    # Fraction wraps the already damaged products only so new public cross/mul
    # range guards cannot mask the targeted nonzero-volume assertion.
    _inject(monkeypatch,G,'_mass_properties',
            'weight = _eg.dot(a, _eg.cross(b, c))',
            'weight = _eg.dot(a, tuple(Fraction(float(b[i])*float(c[j])-float(b[j])*float(c[i])) '
            'for i,j in ((1,2),(2,0),(0,1))))')
    with pytest.raises(AssertionError,match='axis-product-volume'):
        test_g6g08_mass_properties_use_exact_products_before_final_rounding(-600)


def test_r7fix_margin_normal_underflow_retains_exact_direction_certificate():
    tiny = U/4
    a = G.box(center=(F(2),F(2),F(1)+tiny),half=(F(1,2),)*3)
    b = G.box(half=(F(1,2),)*3)
    contact = M.margin_contacts(a,b,delta=2,tol=0)[0]
    assert contact.exact_distance_squared == 2+tiny*tiny
    assert contact.normal[2] == 0.0
    assert contact.exact_normal_direction is not None, 'underflow-direction-certificate'
    v = contact.exact_normal_direction
    assert v[0] == v[1] and v[2]/v[0] == tiny > 0, 'underflow-direction-certificate'
    with pytest.raises(ArithmeticError,match='binary64'):
        G.unit((F(1),F(1),tiny))


def test_r7fix_volume_underflow_does_not_erase_exact_mass_before_centroid():
    p = G.box(half=(2.**-600,)*3)
    with pytest.raises(ArithmeticError,match='binary64'):
        p.volume()
    assert p.centroid() == (0.,0.,0.), 'centroid-before-volume-rounding'


def test_r7fix_metrics_cannot_create_infinite_acceptance_scale_from_finite_coordinates():
    p = G.box(half=(float.fromhex('0x1.fffffffffffffp+1023'),)*3)
    with pytest.raises(OverflowError):
        p.metrics()


def test_r7fix_internal_mutation_normal_certificate_is_required(monkeypatch):
    _inject(monkeypatch,M,'margin_contacts',
            'd2, direction))','d2, None))')
    with pytest.raises(AssertionError,match='underflow-direction-certificate'):
        test_r7fix_margin_normal_underflow_retains_exact_direction_certificate()


def test_r7fix_brute_surface_distance_includes_edge_face_crossings():
    # The first B edge crosses z=0 at (0,0,0), strictly inside triangle A.
    a = G.Polyhedron([(-1,-1,0),(1,-1,0),(0,1,0)],[(0,1,2)])
    b = G.Polyhedron([(0,0,-1),(0,0,1),(2,0,1)],[(0,1,2)])
    assert G.brute_feature_distance(a,b) == 0.0, 'edge-face-intersection-distance'


def test_r7fix_internal_mutation_omitting_edge_face_crossings_is_caught(monkeypatch):
    _inject(monkeypatch,G,'brute_feature_distance','if _surfaces_intersect(*triangles):','if False:')
    with pytest.raises(AssertionError,match='edge-face-intersection-distance'):
        test_r7fix_brute_surface_distance_includes_edge_face_crossings()


@pytest.mark.parametrize('scale',[2.**-600,2.**600])
def test_r7fix_angle_between_avoids_intermediate_cross_range_loss(scale):
    assert G.angle_between((scale,0.,0.),(0.,scale,0.)) == math.pi/2, 'angle-range-invariance'
    assert G.angle_between((scale,0.,0.),(scale,scale,0.)) == math.pi/4, 'angle-range-invariance'
