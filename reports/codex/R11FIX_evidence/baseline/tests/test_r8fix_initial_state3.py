"""3D tight-seam topology: independent Cartesian Minkowski-box union oracle.

The primary oracle uses only interval arithmetic, never production planes,
surface triangulation, overlap, hulls, or angular-arrangement primitives.
"""
from fractions import Fraction as F

import pytest

from eab.kernel3d.geom3 import Polyhedron, box
from eab.kernel3d import entrance3
from eab import margin


def _extrude(ring):
    n = len(ring)
    vertices = [(F(x), F(y), F(z)) for z in (0, 1) for x, y in ring]
    faces = [tuple(reversed(range(n))), tuple(range(n, 2*n))]
    faces += [(i, (i+1)%n, (i+1)%n+n, i+n) for i in range(n)]
    return Polyhedron(vertices, faces)


def _tight_pair():
    B = _extrude([(-1,-1),(2,-1),(2,2),(1,2),(1,0),(0,0),(0,2),(-1,2)])
    A = box((.5,1.,.5),(.5,.5,.25))
    # Exact Minkowski cells: side boxes join across x=0; bottom overlaps both.
    cells = [((-2,2),(F(-5,2),F(-1,2))),
             ((-2,0),(F(-3,2),F(3,2))), ((0,2),(F(-3,2),F(3,2)))]
    assert cells[1][0][1] == cells[2][0][0]
    assert cells[1][1] == cells[2][1]
    assert cells[0][1][1] > cells[1][1][0]
    e_box = [(-2,2),(F(-5,2),F(3,2)),(F(-3,4),F(3,4))]
    assert all(lo < 0 < hi for lo,hi in e_box)
    return A, B


def _rotation(rotated):
    if not rotated:
        return ((F(1),F(0),F(0)),(F(0),F(1),F(0)),(F(0),F(0),F(1)))
    # Exact orthogonal matrix from quaternion (1,2,3,4), not a kernel primitive.
    return tuple(tuple(F(x,15) for x in row) for row in
                 ((-10,2,11),(10,-5,10),(5,14,2)))


def _transform(P, scale, offset, rotated):
    R = _rotation(rotated)
    return Polyhedron([tuple(F(offset[i])+F(scale)*sum(R[i][j]*F(p[j]) for j in range(3))
                              for i in range(3)) for p in P.verts], list(P.faces))


def _direction(d, scale, rotated):
    R = _rotation(rotated)
    return tuple(F(scale)*sum(R[i][j]*F(d[j]) for j in range(3)) for i in range(3))


@pytest.mark.parametrize('scale', [F(1,256),F(1),F(256)])
@pytest.mark.parametrize('offset', [(0,0,0),(10**6,-2*10**6,3*10**6)])
@pytest.mark.parametrize('rotated', [False,True])
def test_3d_tight_fit_initial_topological_interior_uses_exit(scale, offset, rotated):
    A,B = _tight_pair()
    A,B = (_transform(P,scale,offset,rotated) for P in (A,B))
    got = entrance3.first_entrance3(A,B,(0,0,0),_direction((1,1,0),scale,rotated),tol=0)
    assert got.kind == 'exit', 'topological int E must use local exit policy'
    assert got == entrance3.shortest_exit3(A,B,(0,0,0),tol=0)


def test_3d_tight_fit_vertical_motion_does_not_report_missing_entrance():
    A,B = _tight_pair()
    got = entrance3.first_entrance3(A,B,(0,0,0),(0,1,0),tol=0)
    assert got.kind == 'exit', 'tight-fit initial interior is not a missed entrance'


def test_zero_margin_membership_classifies_tight_fit_int_E_not_body_contact():
    A,B = _tight_pair()
    assert margin.inflated_membership(A,B,delta=0) == margin.INSIDE, 'zero-margin E topology mismatch'
    assert margin.body_distance(A,B)[0] == 0, 'physical body distance must remain zero'
    assert margin.inflated_membership(A,B,delta=0,atol=0) == margin.INSIDE
    # A nonzero explicit band/window is still the caller's reporting policy.
    assert margin.inflated_membership(A,B,delta=0,atol=.01) == margin.ON_BOUNDARY


@pytest.mark.parametrize('width', [F(1)-F(1,2**80),F(1),F(1)+F(1,2**80)])
def test_3d_topology_resolves_tight_fit_threshold(width):
    from eab.kernel3d.entrance_topology import entrance_membership3
    A,B = _tight_pair()
    A = Polyhedron([(F(p[0])*width,F(p[1]),F(p[2])) for p in A.verts],list(A.faces))
    want = 0 if width < 1 else 1
    assert entrance_membership3(A,B) == want
    assert margin.inflated_membership(A,B,delta=0) == want


@pytest.mark.parametrize('shear',[0,2**30])
def test_3d_topology_keeps_narrow_exterior_chamber(shear):
    from eab.kernel3d.entrance_topology import entrance_membership3
    B = _extrude([(0,0),(3,0),(3,1),(1,1),(1,3),(0,3)])
    A = box((1.25,1.25,.5),(.25,.25,.25))
    def skew(P):
        return Polyhedron([(F(p[0])+shear*F(p[1])+shear**2*F(p[2]),
                            F(p[1])+shear*F(p[2]),F(p[2])) for p in P.verts],list(P.faces))
    A,B = skew(A),skew(B)
    # Cartesian L complement contains (epsilon,epsilon,0) before this invertible
    # exact shear; its extremely narrow image remains a genuine exterior room.
    assert entrance_membership3(A,B) == 0, 'narrow exterior chamber was lost'
    assert margin.inflated_membership(A,B,delta=0) == margin.ON_BOUNDARY


def test_3d_initial_state_gate_kills_restored_physical_overlap_classifier(monkeypatch):
    from eab.kernel3d.geom3 import polyhedra_overlap
    monkeypatch.setattr(entrance3,'entrance_membership3',polyhedra_overlap)
    with pytest.raises(AssertionError,match='topological int E must use local exit policy'):
        test_3d_tight_fit_initial_topological_interior_uses_exit(F(1),(0,0,0),False)


def test_zero_margin_gate_kills_restored_physical_overlap_classifier(monkeypatch):
    from eab.kernel3d import entrance_topology as topology
    from eab.kernel3d.geom3 import polyhedra_overlap
    monkeypatch.setattr(topology,'entrance_membership3',polyhedra_overlap)
    with pytest.raises(AssertionError,match='zero-margin E topology mismatch'):
        test_zero_margin_membership_classifies_tight_fit_int_E_not_body_contact()


def test_3d_topology_never_calls_independent_g0_oracles(monkeypatch):
    from eab.kernel3d import g03_surface_oracle
    from eab.kernel3d.entrance_topology import entrance_membership3
    def forbidden(*a,**k):
        raise AssertionError('independent G0 oracle leaked into production')
    for name,value in vars(g03_surface_oracle).items():
        if callable(value) and getattr(value,'__module__',None) == g03_surface_oracle.__name__:
            monkeypatch.setattr(g03_surface_oracle,name,forbidden)
    assert entrance_membership3(*_tight_pair()) == 1


@pytest.mark.parametrize('normals,want',[
    (((1,0,0),),2),
    (((1,0,0),(0,1,0),(1,1,0)),6),
    (((1,0,0),(0,1,0),(0,0,1)),8),
    (((1,0,0),(0,1,0),(0,0,1),(1,1,1)),14),
    (tuple((1,k,0) for k in range(7))+((0,1,0),),16),
    (((1,0,0),(1,F(2)**-200,0),(1,0,F(2)**-200)),8),
])
def test_exact_spherical_chambers_cover_rank_one_two_three_and_narrow_cells(normals,want):
    """Independent counts: m rank-2 planes make 2m lunes; 3 independent make 8.

    Four planes in general position make 14 cells. No production primitive is
    used to audit sign signatures, and not one representative may lie on a plane.
    """
    from eab.kernel3d.entrance_topology import _chamber_directions
    directions = list(_chamber_directions(tuple(tuple(map(F,n)) for n in normals)))
    signatures = []
    for d in directions:
        products = [sum(F(n[i])*d[i] for i in range(3)) for n in normals]
        assert all(products)
        signatures.append(tuple(1 if value > 0 else -1 for value in products))
    assert len(signatures) == len(set(signatures)) == want


def test_3d_topology_gate_kills_internal_exterior_chamber_omission(monkeypatch):
    from eab.kernel3d import entrance_topology as topology
    original = topology._chamber_directions
    def omit_exterior(normals):
        for direction in original(normals):
            if not (direction[0] > 0 and direction[1] > 0):
                yield direction
    monkeypatch.setattr(topology,'_chamber_directions',omit_exterior)
    with pytest.raises(AssertionError,match='narrow exterior chamber was lost'):
        test_3d_topology_keeps_narrow_exterior_chamber(0)


def test_3d_topology_gate_kills_internal_loss_of_noncentral_step_bound(monkeypatch):
    import inspect
    from eab.kernel3d import entrance_topology as topology
    source = inspect.getsource(topology.entrance_membership3)
    needle = 'step = min(step,h/(2*abs(slope)))'
    assert source.count(needle) == 1
    namespace = dict(vars(topology))
    exec(source.replace(needle,'step = F(1)'),namespace)
    monkeypatch.setattr(topology,'entrance_membership3',namespace['entrance_membership3'])
    A,B = (_transform(P,F(1,256),(0,0,0),False) for P in _tight_pair())
    with pytest.raises(AssertionError,match='local probe crossed a noncentral plane'):
        assert topology.entrance_membership3(A,B) == 1, 'local probe crossed a noncentral plane'
