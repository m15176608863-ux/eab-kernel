"""Folded-solid cone truth from explicit triangle normals and raw edge vectors.

No production normal, triangulator or cone primitive supplies expected values.
The unit-square roof is z=1+h*max(0,x+y-1), declared along diagonal (5,7).
"""
from fractions import Fraction as F
import inspect
import textwrap

import pytest

from eab.kernel3d import covers3 as C
from eab.kernel3d.geom3 import Polyhedron

FACES=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]


def _roof(scale=F(1), shift=F(0), rotated=False):
    raw=[(0,0,0),(1,0,0),(1,1,0),(0,1,0),(0,0,1),(1,0,1),(1,1,F(3,2)),(0,1,1)]
    def transform(p):
        x,y,z=map(F,p)
        if rotated:
            x,y=(3*x-4*y)/5,(4*x+3*y)/5
        return tuple(scale*c+shift for c in (x,y,z))
    return Polyhedron([transform(p) for p in raw],list(FACES))


@pytest.mark.parametrize('rotated', [False,True])
@pytest.mark.parametrize('scale,shift', [(F(1),F(0)),(F(1,2**30),F(0)),
                                        (F(2**30),F(0)),(F(1),F(10**8))])
@pytest.mark.parametrize('edge,direction', [((4,5),(0,0,1)),((4,7),(0,0,1)),
                                           ((5,6),(-1,-1,2)),((6,7),(-1,-1,2))])
def test_public_edge_arc_uses_declared_adjacent_triangle_normal(scale,shift,edge,direction,rotated):
    # These are exactly the adjacent top-triangle normals, hence arc endpoints.
    if rotated:
        x,y,z=map(F,direction)
        direction=((3*x-4*y)/5,(4*x+3*y)/5,z)
    assert C.edge_arc_contains(_roof(scale,shift,rotated),edge,direction)==0, 'declared-triangle-cone-endpoint'


@pytest.mark.parametrize('scale', [F(1),F(1,2**30),F(2**30)])
def test_public_cone_constraints_include_folded_internal_incident_ridge(scale):
    p=_roof(scale)
    # At source vertex 5, triangles (7,4,5),(5,6,7) require edge 5->7.
    expected={tuple(scale*x for x in v) for v in ((0,0,-1),(-1,0,0),(0,1,F(1,2)),(-1,1,0))}
    constraints=C.cone_constraints(p,5,p,5)
    assert set(constraints)==expected|{tuple(-x for x in v) for v in expected}, 'declared-internal-ridge-constraint'


def test_public_vertex_cone_uses_declared_surface_while_source_single_cover_is_explicit(monkeypatch):
    p=_roof()
    seen=[]
    original=C._qvertex_contains
    def traced(P,*args):
        seen.append(any(len(f)==3 and set(f)=={5,6,7} for f in P.faces))
        return original(P,*args)
    monkeypatch.setattr(C,'_qvertex_contains',traced)
    assert C.vertex_cone_contains(p,5,(1,-1,0))==0
    assert seen==[True], 'public-vertex-cone-resolves-declared-surface'


@pytest.mark.parametrize('method,check,message', [
    ('edge_arc_contains',lambda: test_public_edge_arc_uses_declared_adjacent_triangle_normal(F(1),F(0),(4,5),(0,0,1),False),
     'declared-triangle-cone-endpoint'),
    ('cone_constraints',lambda: test_public_cone_constraints_include_folded_internal_incident_ridge(F(1)),
     'declared-internal-ridge-constraint'),
])
def test_solid_cone_gate_rejects_internal_restoration_of_source_topology(monkeypatch,method,check,message):
    source=textwrap.dedent(inspect.getsource(getattr(C,method)))
    source=source.replace('geom3.exact_surface(P)','P').replace('geom3.exact_surface(A)','A').replace('geom3.exact_surface(B)','B')
    namespace=dict(vars(C))
    exec(compile(source,'<r9-solid-cone-mutant>','exec'),namespace)
    monkeypatch.setattr(C,method,namespace[method])
    with pytest.raises(AssertionError,match=message):
        check()


def test_public_edge_arc_resolves_a_convex_internal_diagonal_not_in_source_edges():
    p=_roof()
    p.verts[6]=(F(1),F(1),F(1,2))
    # Raw adjacent normals (0,0,1), (1/2,1/2,1) have a positive
    # oriented triple on 5->7=(-1,1,0), hence a true convex arc.
    assert C.edge_arc_contains(p,(5,7),(0,0,1))==0, 'declared-internal-edge-arc'
    assert C.edge_arc_contains(p,(5,7),(1,1,2))==0, 'declared-internal-edge-arc'
    assert C.edge_arc_contains(p,(5,7),(1,1,4))==1, 'declared-internal-edge-arc'
