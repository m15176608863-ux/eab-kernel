"""E5b exact-time and exact-coplanarity gates.

Oracle: direct rational coordinate inequalities / all-chord integer SAT in
 e5a2_entrance_oracle; no production geometric primitive is an oracle.
"""
from fractions import Fraction as F
import math
import pytest
from eab.kernel3d.geom3 import Polyhedron, box
from eab.kernel3d.entrance3 import first_entrance3, merge_degenerate
from eab.kernel3d.covers3 import enumerate_covers3
from e5a2_entrance_oracle import convex_ray_interval


def _rational_motion(P, t, scale):
    return Polyhedron([(scale*(F(3,5)*F(x)-F(4,5)*F(y))+t,
                        scale*(F(4,5)*F(x)+F(3,5)*F(y))-2*t,
                        scale*F(z)+3*t) for x,y,z in P.verts], P.faces)


@pytest.mark.parametrize('half', [F(1,2),F(1,20),F(1,50),F(1,200)])
@pytest.mark.parametrize('offset,scale', [(0,F(1)),(10**3,F(1)),(10**6,F(1,1000))])
def test_exact_first_time_and_ties_match_independent_sat_at_large_size_ratios(half,offset,scale):
    a=box(center=(F(13,10),F(-21,10),51+half),half=(half,)*3)
    b=box(half=(F(50),)*3)
    a,b=(_rational_motion(p,F(offset),scale) for p in (a,b))
    d=(0,0,-scale)
    expected=convex_ray_interval(a.verts,b.verts,(0,0,0),d,2)
    result=first_entrance3(a,b,(0,0,0),d,t_max=2)
    assert expected[0] == result.exact_t == 1
    assert result.kind == 'entrance' and result.label[0] == 'FF'
    assert len(result.members) == len(result.tied_labels) == 4


def test_exact_predecessor_selfcheck_never_rounds_back_to_the_event():
    # At 1e20 the former floating resolution subtraction is exactly a no-op.
    # The direct coordinate oracle proves t*=1e20 and every 0<=t<t* is separated.
    time=F(10**20)
    a=box(center=(time+1,0,0),half=(F(1,2),)*3)
    b=box(half=(F(1,2),)*3)
    assert min(p[0] for p in a.verts)-max(p[0] for p in b.verts) == time
    assert float(time)-2e-9 == float(time)
    result=first_entrance3(a,b,(0,0,0),(-1,0,0))
    assert result.kind == 'entrance' and result.exact_t == time
    assert result.label[0] == 'FF' and len(result.members) == 8


@pytest.mark.parametrize('height',[F(1,2),F(1,1000),F(1,10**12),F(1,2**80)])
def test_degenerate_merge_never_coalesces_distinct_exact_planes(height):
    from test_entrance3_concave import _prism
    step=_prism([(F(0),F(0)),(F(2),F(0)),(F(2),1-height),
                 (F(1),1-height),(F(1),F(1)),(F(0),F(1))],F(-1),F(1))
    a=box(center=(F(1),F(0),F(3,2)),half=(F(1),F(1,2),F(1,2)))
    covers=[c for c in enumerate_covers3(a,step,window=float('inf'))
            if c.kind=='VF' and c.normal[2]>.5 and c.in_extent]
    assert len(covers)==4
    families=merge_degenerate(a,step,covers)
    assert sorted((rep[0],len(members)) for rep,members in families)==[('FF',2),('FF',2)]
    assert len({rep[2] for rep,_ in families})==2


def test_exact_tie_set_does_not_merge_distinct_sub_float_times():
    a=box(center=(0,0,2),half=(F(1,2),)*3)
    # Affine shear makes exactly one lowest x-edge, difference 2^-80 in height.
    epsilon=F(1,2**80)
    a=Polyhedron([(F(x),F(y),F(z)+epsilon*F(y)) for x,y,z in a.verts],a.faces)
    b=box(half=(1,1,F(1,2)))
    result=first_entrance3(a,b,(0,0,0),(0,0,-1))
    assert result.exact_t == 1-epsilon/2
    assert result.label[0]=='FE' and len(result.members)==2
    assert len(result.tied_labels)==2


def test_nearly_tangential_approach_keeps_its_exact_nonzero_event():
    a=box(center=(0,0,F(7,4)),half=(F(1,2),)*3)
    b=box(half=(F(2**70),F(2),F(1,2)))
    epsilon=F(1,2**50)
    result=first_entrance3(a,b,(0,0,0),(1,0,-epsilon))
    assert result.kind=='entrance' and result.exact_t==F(3,4)/epsilon


@pytest.mark.parametrize('rot,translation',[(3,0),(5,10**5)])
def test_nonplanar_source_faces_expose_the_actual_triangle_for_frozen_use(rot,translation):
    from test_entrance3 import _rot,_mat,_rx,_ry,_quat,_apply,SLAB
    from eab.kernel3d.frozen import frozen_normal
    original=_rot(box(half=(.5,)*3),_mat(_ry(.2),_rx(.3))).translated((.1,-.2,2.))
    rotation=_quat(rot)
    shift=tuple(translation*c for c in (.6,-.48,.64))
    move=lambda p: Polyhedron([tuple(shift[i]+_apply(rotation,v)[i] for i in range(3)) for v in p.verts],p.faces)
    a,b=move(original),move(SLAB)
    result=first_entrance3(a,b,(0,0,0),_apply(rotation,(.05,.02,-1.)))
    assert result.label==('VF',('vertex',1),('face',1))
    assert result.surface_label[:2]==result.label[:2]
    assert result.surface_label[2][2]=='triangle'
    normal=frozen_normal(a,b,result.surface_label)
    assert normal==pytest.approx(result.normal,abs=1e-14)
    # Independent determinant of the named triangle proves its exact plane.
    _,_,_,i,j,k=result.surface_label[2]
    p,q,r=[tuple(map(F,b.verts[v])) for v in (i,j,k)]
    u=tuple(q[h]-p[h] for h in range(3)); v=tuple(r[h]-p[h] for h in range(3))
    n=(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])
    velocity=tuple(map(F,_apply(rotation,(.05,.02,-1.))))
    point=tuple(F(a.verts[1][h])+result.exact_t*velocity[h] for h in range(3))
    assert sum(n[h]*(point[h]-p[h]) for h in range(3))==0


@pytest.mark.parametrize('half',[.5,.05,.02,.005])
@pytest.mark.parametrize('rotation,translation',[(0,0.),(7,0.),(11,0.),(0,1e3),(7,1e3),(11,1e3)])
def test_g6e_small_drop_on_large_rotated_body_has_the_exact_first_time(half,rotation,translation):
    """Original fifth-round 24-cell family, against independent tetra-union SAT.

    The star-core decomposition and SAT axes use only the test oracle's raw
    ring code; no production overlap, normal, event, cover or hull primitive.
    """
    from test_invariance_geom import Motion
    from e5a2_surface_oracle import _tetrahedra
    motion=Motion(rotation,translation,1.)
    a=motion.poly(box(center=(1.3,-2.1,51.+half),half=(half,)*3))
    b=motion.poly(box(half=(50.,)*3))
    direction=motion.vec((0.,0.,-1.))
    times=[]
    for ta in _tetrahedra(a):
        for tb in _tetrahedra(b):
            interval=convex_ray_interval(ta,tb,(0,0,0),direction,2)
            if interval is not None:times.append(interval[0])
    assert times
    result=first_entrance3(a,b,(0,0,0),direction,t_max=2)
    assert result.kind=='entrance' and result.exact_t==min(times)
    assert result.t==pytest.approx(1.,abs=1e-10)


def test_selfcheck_catches_an_earlier_contact_even_after_the_bodies_separate_again(monkeypatch):
    """Independent axis-aligned rectangle union: first entry at .9, not 3.9."""
    from test_entrance3_concave import _prism
    import eab.kernel3d.entrance3 as entrance
    ground=_prism([(0,0),(4,0),(4,2),(3,2),(3,1),(1,1),(1,2),(0,2)],-1,1)
    a=box(center=(-1.,0.,1.5),half=(.1,.1,.1))
    expected=-F(max(p[0] for p in a.verts))
    assert entrance.first_entrance3(a,ground,(0,0,0),(1,0,0)).exact_t==expected
    real=entrance.enumerate_covers3
    def omitted(a,b,**kwargs):
        def left(c):
            f=c.b_feature
            ids=[f[1]] if f[0]=='vertex' else (b.faces[f[1]] if f[0]=='face' else f[1:])
            return all(b.verts[i][0]<=1 for i in ids)
        return [c for c in real(a,b,**kwargs) if not left(c)]
    monkeypatch.setattr(entrance,'enumerate_covers3',omitted)
    with pytest.raises(RuntimeError,match='missed an earlier entrance'):
        entrance.first_entrance3(a,ground,(0,0,0),(1,0,0))


def test_preceding_event_probe_is_strictly_inside_the_exact_interval():
    from eab.kernel3d.entrance3 import _preceding_probe
    lower=F(1); upper=lower+F(1,2**80)
    probe=_preceding_probe(upper,(F(0),lower,upper))
    assert lower < probe < upper
    assert probe-lower == upper-probe
