"""Exact triangle-window lower-bound fast-path equivalence and closed-band oracle.

Primary oracle: triangles in parallel/near-parallel graph planes have a known
minimum vertical gap attained at the same vertex, then exact rational rigid
motions preserve that distance. It shares no production geometric primitive.
The secondary old path is the unmodified all-feature distance implementation,
kept here to ensure the new rejection changes neither true nor false answers.
"""
from construction_oracle import scalar_exact
from fractions import Fraction as F
import random
import pytest
from eab.kernel3d import exact_geom as G


def _full_feature_reference(at,bt,tol):
    tt=tol*tol
    aa=[G._triangle_data(a) for _,a in at];bb=[G._triangle_data(b) for _,b in bt]
    for first in aa:
        a,n,ab=first
        for second in bb:
            b,m,bounds=second
            if any(hi+tol<low or upper+tol<lo for (lo,hi),(low,upper) in zip(ab,bounds)):
                continue
            if G._triangles_intersect_prepared(first,second):return True
            if tol:
                if any(G.point_triangle_distance_squared(p,b)<=tt for p in a):return True
                if any(G.point_triangle_distance_squared(p,a)<=tt for p in b):return True
                if any(G.segment_distance_squared(p,q,u,v)<=tt for p,q in zip(a,a[1:]+a[:1]) for u,v in zip(b,b[1:]+b[:1])):return True
    return False


def _move(p,scale,translation,rotation):
    """Own exact orthogonal maps, never production rotation/normal code."""
    x,y,z=p
    if rotation in (1,2):x,y=F(3,5)*x-F(4,5)*y,F(4,5)*x+F(3,5)*y
    if rotation==2:y,z=F(5,13)*y-F(12,13)*z,F(12,13)*y+F(5,13)*z
    return scale*x+translation,scale*y-2*translation,scale*z+3*translation


def _known_pair(scale,translation,rotation,tilt,delta):
    band=F(1,16)
    lower=((F(-1),F(-1),F(0)),(F(1),F(-1),F(0)),(F(0),F(1),F(0)))
    # Min upper z=band+delta at x=-1, whose projection is a lower vertex.
    upper=tuple((x,y,band+delta+abs(tilt)+tilt*x) for x,y,_ in lower)
    a=tuple(_move(p,scale,translation,rotation) for p in lower)
    b=tuple(_move(p,scale,translation,rotation) for p in upper)
    return [(0,a)],[(0,b)],scale*band


@pytest.mark.parametrize('scale',[F(1,1024),F(1),F(1024)])
@pytest.mark.parametrize('translation',[F(0),F(1000),F(10**6)])
@pytest.mark.parametrize('rotation',[0,1,2])
@pytest.mark.parametrize('tilt',[F(0),F(1,2**60),F(1,100)])
def test_triangle_near_window_preserves_closed_exact_threshold_rigid_motion_and_units(scale,translation,rotation,tilt):
    """243 independent min-distance answers including exact equality and +/-2^-80."""
    values=[]
    for delta in (-F(1,2**80),F(0),F(1,2**80)):
        at,bt,band=_known_pair(scale,translation,rotation,tilt,delta)
        got=G._triangles_near(at,bt,band)
        assert got==(delta<=0), ('closed boundary equality' if not delta else 'subresolution exact side',scale,translation,rotation,tilt,delta)
        assert got==_full_feature_reference(at,bt,band),'new rejection must match old all-feature path'
        values.append(got)
    assert values==[True,True,False], 'parameterized products must differ across the threshold'


def test_triangle_near_rejection_matches_full_feature_path_on_rounded_general_position_inputs():
    """180 deterministic generic/rounded/coplanar inputs, including zero window."""
    rng=random.Random(6012)
    for case in range(180):
        scale=(F(1,1024),F(1),F(1024))[case%3]
        translation=(F(0),F(1000),F(10**6))[(case//3)%3]
        points=[tuple(F(rng.randrange(-16,17),8) for _ in range(3)) for _ in range(6)]
        if case%6==0:points=[(x,y,F(0)) for x,y,z in points]
        a,b=tuple(points[:3]),tuple(points[3:])
        # Independent integer cross only detects unusable generated triangles.
        def valid(tri):
            u=tuple(tri[1][i]-tri[0][i] for i in range(3));v=tuple(tri[2][i]-tri[0][i] for i in range(3))
            return any((u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]))
        if not valid(a):a=((F(0),)*3,(F(1),F(0),F(0)),(F(0),F(1),F(0)))
        if not valid(b):b=((F(0),F(0),F(1)),(F(1),F(0),F(1)),(F(0),F(1),F(1)))
        # Inputs intentionally round only once; no ideal-position oracle is claimed here.
        a=tuple(tuple(F(scalar_exact(c)) for c in _move(p,scale,translation,case%3)) for p in a)
        b=tuple(tuple(F(scalar_exact(c)) for c in _move(p,scale,translation,case%3)) for p in b)
        band=scale*(F(0),F(1,128),F(1,4),F(2))[case%4]
        assert G._triangles_near([(0,a)],[(0,b)],band)==_full_feature_reference([(0,a)],[(0,b)],band),case

@pytest.mark.parametrize('band',[F(1,2**60),F(1,2**120)])
@pytest.mark.parametrize('tilt',[F(0),F(1,2**90)])
def test_triangle_near_coplanar_subresolution_gaps_remain_exact_at_engineering_coordinates(band,tilt):
    scale,translation,rotation=F(1,1024),F(10**6),2
    lower=((F(-1),F(-1),F(0)),(F(1),F(-1),F(0)),(F(0),F(1),F(0)))
    states=[]
    for delta in (-F(1,2**160),F(0),F(1,2**160)):
        upper=tuple((x,y,band+delta+abs(tilt)+tilt*x) for x,y,_ in lower)
        at=[(0,tuple(_move(p,scale,translation,rotation) for p in lower))]
        bt=[(0,tuple(_move(p,scale,translation,rotation) for p in upper))]
        got=G._triangles_near(at,bt,scale*band)
        assert got==(delta<=0),'near-coplanar exact distance compared with explicit window'
        assert got==_full_feature_reference(at,bt,scale*band)
        states.append(got)
    assert states==[True,True,False]


def test_triangle_near_unsafe_plane_threshold_mutation_is_killed_at_closed_boundary(monkeypatch):
    """>= instead of > is injected inside the live rejection helper, not output."""
    import inspect
    source=inspect.getsource(G._triangle_plane_outside_window)
    needle='gap*gap > window_squared*dot(normal,normal)'
    assert source.count(needle)==1
    namespace=dict(G.__dict__)
    exec(source.replace(needle,'gap*gap >= window_squared*dot(normal,normal)'),namespace)
    at,bt,band=_known_pair(F(1),F(0),0,F(0),F(0))
    assert G._triangles_near(at,bt,band), 'unmutated closed boundary is accepted'
    monkeypatch.setattr(G,'_triangle_plane_outside_window',namespace['_triangle_plane_outside_window'])
    def assert_closed_boundary():
        assert G._triangles_near(at,bt,band),'closed boundary equality must not be rejected'
    with pytest.raises(AssertionError,match='closed boundary equality'):
        assert_closed_boundary()
