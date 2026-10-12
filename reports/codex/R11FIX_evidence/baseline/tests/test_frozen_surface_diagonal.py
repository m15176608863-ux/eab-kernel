"""Source-ring diagonal EE: independent parallel-plane distance certificate.

B has a ridge at z=1.5, A a bottom edge at binary64 z=1.7. Their projected
edges cross at the origin, so the plane separation is attained and proves the
exact distance independently of production covers, triangulation or predicates.
Exact rational rigid transforms preserve that certificate.
"""
from construction_oracle import scalar_exact
from fractions import Fraction as F
import inspect
import pytest
from eab.kernel3d.geom3 import Polyhedron,box,tetra
from eab.kernel3d import frozen
from eab.margin import body_distance,margin_gap_from_frozen_cover


def _pair(mirrored,scale,translation):
    p=box();vertices=list(p.verts)
    vertices[5]=(1.,-1.,1.5);vertices[7]=(-1.,1.,1.5)
    b=Polyhedron(vertices,p.faces)
    a=tetra((-.5,-.5,1.7),(.5,.5,1.7),(0.,-.3,2.5),(0.,.3,2.5))
    def move(p):
        vertices=[(-x,y,z) if mirrored else (x,y,z) for x,y,z in p.verts]
        # Reverse orientation while retaining the starting vertex, hence the
        # deterministic ear diagonal (5,7) of the same physical folded face.
        faces=[(f[0],*reversed(f[1:])) for f in p.faces] if mirrored else p.faces
        vertices=[(translation+scale*(F(3,5)*F(x)+F(4,5)*F(z)),
                   -2*translation+scale*F(y),
                   3*translation+scale*(-F(4,5)*F(x)+F(3,5)*F(z))) for x,y,z in vertices]
        return Polyhedron(vertices,faces)
    return move(a),move(b)


def _check(mirrored,scale,translation):
    a,b=_pair(mirrored,scale,translation)
    distance,label=body_distance(a,b)
    assert label==('EE',('edge',0,1),('edge',5,7))
    assert (5,7) not in b.edges()
    expected=scalar_exact(scale*(F(1.7)-F(1.5)))
    assert distance==pytest.approx(expected,rel=1e-13,abs=0.)
    sign=frozen.frozen_ee_sign(a,b,(0,1),(5,7))
    gap=margin_gap_from_frozen_cover(a,b,label,(0,0,0),0.,ee_sign=sign)
    assert gap==pytest.approx(expected,rel=1e-13,abs=0.), 'diagonal EE frozen signed distance'
    assert frozen.ee_normal_generic(a,(0,1),b,(5,7),sign)==pytest.approx((.8,0.,.6),abs=1e-14)
    return sign


@pytest.mark.parametrize('mirrored',[False,True])
@pytest.mark.parametrize('scale,translation',[(F(1),F(0)),(F(1,1000),F(10**6)),(F(1000),F(-10**5))])
def test_folded_surface_diagonal_ee_freezes_the_margin_selected_exact_surface(mirrored,scale,translation):
    sign=_check(mirrored,scale,translation)
    assert sign==(1. if mirrored else -1.)


def test_missing_diagonal_topology_internal_mutant_is_killed(monkeypatch):
    source=inspect.getsource(frozen._ee_topology_view)
    needle='return exact_surface(P)'
    assert source.count(needle)==1
    namespace=dict(frozen.__dict__)
    exec(compile(source.replace(needle,'return P'),'<omit-diagonal-topology>','exec'),namespace)
    monkeypatch.setattr(frozen,'_ee_topology_view',namespace['_ee_topology_view'])
    with pytest.raises(AssertionError,match='diagonal EE frozen signed distance'):
        _check(True,F(1),F(0))
