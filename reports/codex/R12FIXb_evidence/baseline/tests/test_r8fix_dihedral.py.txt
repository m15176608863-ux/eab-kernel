"""G6H-03: independent cross-section angle formula; no production oracle primitive."""
from construction_oracle import scalar_exact
from fractions import Fraction as F
import math
import pytest
from eab.kernel3d.geom3 import tetra, Polyhedron


@pytest.mark.parametrize("M", [10**6,10**7,10**8,10**9,10**12,2**50])
@pytest.mark.parametrize("scale", [2.**-400,1.,2.**400])
@pytest.mark.parametrize("reverse", [False,True])
def test_dihedral_turn_preserves_exact_thin_angle_and_orientation(M,scale,reverse):
    # Raw section normals (M+1,M),(M,M-1): cross=-1, dot=2M*M;
    # traversal t=-ez makes the exterior angle positive. Reversing winding
    # flips its sign. Every coordinate is still an exactly represented float.
    P=tetra((0.,0.,0.),(0.,0.,scale),(-M*scale,(M+1)*scale,0.),
            ((M-1)*scale,-M*scale,0.))
    # Topology check must not construct an unrepresentable scaled volume.
    assert all(len(P.edge_traversals(edge)) == 2 for edge in P.edges())
    if scale == 1.:
        assert P.manifold_issues() == []
        assert P.volume() == scalar_exact(F(1,6))
    if reverse:
        P=Polyhedron(P.verts,[tuple(reversed(face)) for face in P.faces])
    expected=math.atan(scalar_exact(F(1,2*M*M))) * (-1 if reverse else 1)
    actual=P.dihedral_turn((0,1))
    assert actual == pytest.approx(expected, rel=2e-15, abs=0.), "exact thin signed dihedral"
    assert (actual>0) != reverse, "nonzero orientation must not be rounded away"



def test_rounded_unit_normal_dihedral_mutant_is_caught(monkeypatch):
    import eab.kernel3d.geom3 as geom
    def rounded_unit_normals(self,edge):
        (f1,a,b),(f2,_,_)=self.edge_traversals(edge)
        t=geom.unit(geom.exact_edge_vector(self,(a,b)))
        n1,n2=self.face_normal(f1),self.face_normal(f2)
        return math.atan2(geom.dot(geom.cross(n1,n2),t),geom.dot(n1,n2))
    monkeypatch.setattr(Polyhedron,"dihedral_turn",rounded_unit_normals)
    with pytest.raises(AssertionError,match="exact thin signed dihedral"):
        test_dihedral_turn_preserves_exact_thin_angle_and_orientation(10**8,1.,False)
