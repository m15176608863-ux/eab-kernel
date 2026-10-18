"""R10 closed initial contact gates: raw Cartesian products are the oracle.

Oracle truth uses only Fraction interval intersection and explicit invertible
rational affine transforms, not production overlap, cones, covers, or events.
The same supplied sets test 2D, 3D, zero-margin and nonpenetrating escape APIs.
"""
from fractions import Fraction as F
import inspect

import pytest

from eab import margin
from eab.kernel2d import entrance as entrance2
from eab.kernel3d import entrance3
from eab.adapters import tia3d as interlock
from eab.kernel3d.geom3 import Polyhedron

FACES = [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
SIGNS = [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),
         (-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]
POSES = [(F(1),(0,0,0),False),
         (F(1,10**9),(10**8,-10**8,10**8),True),
         (F(10**8),(10**8,-10**8,10**8),True)]
MOTIONS = [((1,0,0),F(0)),((1,0,0),F(1,16)),
           ((0,0,1),F(1,16)),((0,0,-1),F(1,16))]


def _pose(v, scale, shift, rotated):
    x,y,z = (F(_r12_item) for _r12_item in v)
    if rotated:
        x,y = F(3,5)*x-F(4,5)*y,F(4,5)*x+F(3,5)*y
    return tuple(scale*c+F(t) for c,t in zip((x,y,z),shift))


def _box(center, pose):
    vertices = [tuple(F(c)+s for c,s in zip(center,p)) for p in SIGNS]
    return Polyhedron([_pose(v,*pose) for v in vertices],list(FACES))


def _pair(pose, contact='face'):
    center = {'face':(F(1,4),F(1,8),2),'edge':(2,F(1,8),2),'vertex':(2,2,2)}[contact]
    # Direct products meet, with one/two/three singleton intersection axes.
    intersection = [(max(F(c)-1,-1),min(F(c)+1,1)) for c in center]
    assert all(lo <= hi for lo,hi in intersection)
    assert sum(lo == hi for lo,hi in intersection) == {'face':1,'edge':2,'vertex':3}[contact]
    # A small simultaneous positive displacement of all active axes separates;
    # hence this physical touch is boundary E rather than an internal seam.
    return _box(center,pose),_box((0,0,0),pose)


@pytest.mark.parametrize('pose',POSES)
@pytest.mark.parametrize('direction,cap',MOTIONS)
def test_initial_face_boundary_is_closed_first_entrance_in_all_review_cells(pose,direction,cap):
    A,B = _pair(pose)
    got = entrance3.first_entrance3(A,B,(0,0,0),_pose(direction,pose[0],(0,0,0),pose[2]),tol=0,t_max=cap)
    assert got.kind == 'entrance', 'closed initial face boundary must not be discarded by motion'
    assert got.exact_t == 0, 'closed initial face boundary has exact first time zero'
    assert got.t == 0 and got.x == (0,0,0) and got.gap == 0
    assert got.label is not None and got.members and got.tied_labels
    assert set(got.members) <= set(got.tied_labels)
    assert got.point_a == got.point_b


@pytest.mark.parametrize('contact',['face','edge','vertex'])
@pytest.mark.parametrize('direction',[(1,0,0),(0,0,1),(0,0,-1)])
def test_initial_lower_dimensional_boundary_keeps_every_contact_direction(contact,direction):
    A,B = _pair(POSES[0],contact)
    got = entrance3.first_entrance3(A,B,(0,0,0),direction,tol=0,t_max=0)
    assert got.kind == 'entrance' and got.exact_t == 0, 'closed lower-dimensional initial boundary was lost'
    assert got.gap == 0


@pytest.mark.parametrize('concave',[False,True])
@pytest.mark.parametrize('direction,cap',[((1,0),0),((1,0),F(1,16)),((0,1),F(1,16)),((0,-1),F(1,16))])
def test_2d_convex_and_concave_initial_boundary_is_closed(concave,direction,cap):
    B = [(0,0),(3,0),(3,1),(1,1),(1,3),(0,3)] if concave else [(0,0),(1,0),(1,3),(0,3)]
    A = [(F(-1,4),3),(F(3,4),3),(F(3,4),4),(F(-1,4),4)]
    # Both B choices contain [0,1] x [1,3], no point has y>3. Thus
    # A intersection B is exactly [0,3/4] x {3}, on the external boundary.
    got = entrance2.first_entrance(A,B,(0,0),direction,tol=0,t_max=cap)
    assert got.kind == 'entrance' and got.t_exact == 0, '2D closed initial boundary was lost'
    assert got.gap == 0 and got.point_a == got.point_b
    assert entrance2.first_entrance_brute(A,B,(0,0),direction,t_max=cap,steps=1) == 0
    local_exit = entrance2.shortest_exit(A,B,(0,0),tol=0)
    assert local_exit.kind == 'exit' and local_exit.gap == 0 and local_exit.t_exact == 0


@pytest.mark.parametrize('pose',POSES)
def test_zero_margin_escape_and_local_exit_keep_initial_boundary(pose):
    A,B = _pair(pose)
    assert margin.inflated_membership(A,B,delta=0,tol=0) == margin.ON_BOUNDARY
    assert margin.inflated_membership(A,B,delta=0,tol=0,atol=0) == margin.ON_BOUNDARY
    local_exit = entrance3.shortest_exit3(A,B,(0,0,0),tol=0)
    assert local_exit.kind == 'exit' and local_exit.gap == 0 and local_exit.exact_t == 0
    for window in (None,0):
        escaped = interlock.escape_height_covers(A,B,(0,0,0),tol=0,contact_window=window)
        assert escaped.exact_height == 0 and escaped.height == 0, 'already nonpenetrating initial boundary needs no lift'
        assert escaped.nonpenetrating_state == 0 and escaped.interval_certificate == ()
    assert interlock.escape_height_brute(A,B,(0,0,0),hi=0) == 0
    assert entrance3.first_entrance_brute(A,B,(0,0,0),(1,0,0),t_max=0,steps=1) == 0


def _assert_axis_aligned_label_has_closed_source_intersection(A,B,label):
    _,af,bf = label
    def coordinates(P,feature):
        if feature[0] == 'vertex':
            return [P.verts[feature[1]]]
        if feature[0] == 'edge':
            return [P.verts[i] for i in feature[1:]]
        return [P.verts[i] for i in P.faces[feature[1]]]
    aa,bb = coordinates(A,af),coordinates(B,bf)
    for axis in range(3):
        assert max(min(p[axis] for p in aa),min(p[axis] for p in bb)) <= min(
            max(p[axis] for p in aa),max(p[axis] for p in bb)), 'initial tied label left its finite source domain'


def test_initial_contact_labels_are_finite_and_motion_independent():
    A,B = _pair(POSES[0])
    outputs = [entrance3.first_entrance3(A,B,(0,0,0),d,tol=0,t_max=cap) for d,cap in MOTIONS]
    assert len({(out.label,out.tied_labels) for out in outputs}) == 1, 'initial closed contact labels must not depend on direction'
    for label in outputs[0].tied_labels:
        _assert_axis_aligned_label_has_closed_source_intersection(A,B,label)


@pytest.mark.parametrize('direction',[(1,0,0),(0,0,1),(0,0,-1)])
def test_3d_concave_ordinary_initial_boundary_is_closed(direction):
    ring = [(0,0),(3,0),(3,1),(1,1),(1,3),(0,3)]
    n = len(ring)
    verts = [(F(x),F(y),F(z)) for z in (0,1) for x,y in ring]
    faces = [tuple(reversed(range(n))),tuple(range(n,2*n))]
    faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    B = Polyhedron(verts,faces)
    A = _box((F(1,4),F(1,8),2),POSES[0])
    # Direct product oracle: B is the union of [0,3]x[0,1]x[0,1]
    # and [0,1]x[0,3]x[0,1]. A meets their top at z=1; z>0
    # displacement strictly separates, so this is not a tight-fit seam.
    got = entrance3.first_entrance3(A,B,(0,0,0),direction,tol=0,t_max=0)
    assert got.kind == 'entrance' and got.exact_t == 0, 'concave initial external boundary must be closed'
    assert got.gap == 0


def test_initial_boundary_gate_kills_removal_inside_first_entrance(monkeypatch):
    source = inspect.getsource(entrance3.first_entrance3)
    needle = 'if initial == 0:'
    assert source.count(needle) == 1
    namespace = dict(vars(entrance3))
    exec(source.replace(needle,'if False:  # mutant: discard initial boundary'),namespace)
    monkeypatch.setattr(entrance3,'first_entrance3',namespace['first_entrance3'])
    with pytest.raises(AssertionError,match='closed initial face boundary must not be discarded by motion') as caught:
        test_initial_face_boundary_is_closed_first_entrance_in_all_review_cells(POSES[0],(1,0,0),F(1,16))
    print('J02 initial-branch mutant killed by:',str(caught.value))


def test_initial_boundary_gate_kills_removal_of_finite_domain_filter(monkeypatch):
    source = inspect.getsource(entrance3.first_entrance3)
    needle = 'if c.in_extent and dot(n, p) == 0:'
    assert source.count(needle) == 1
    namespace = dict(vars(entrance3))
    exec(source.replace(needle,'if dot(n, p) == 0:'),namespace)
    monkeypatch.setattr(entrance3,'first_entrance3',namespace['first_entrance3'])
    with pytest.raises(AssertionError,match='initial tied label left its finite source domain') as caught:
        test_initial_contact_labels_are_finite_and_motion_independent()
    print('J02 finite-domain mutant killed by:',str(caught.value))


def test_initial_boundary_with_nonzero_exact_translation_keeps_closed_time():
    A,B = _pair(POSES[0])
    start = (F(1,8),F(-1,4),F(1))
    A = Polyhedron([tuple(F(p[i])-start[i] for i in range(3)) for p in A.verts],list(A.faces))
    got = entrance3.first_entrance3(A,B,start,(1,0,0),tol=0,t_max=0)
    assert got.kind == 'entrance' and got.exact_t == 0
    assert got.x == (0.125,-0.25,1.0) and got.gap == 0
