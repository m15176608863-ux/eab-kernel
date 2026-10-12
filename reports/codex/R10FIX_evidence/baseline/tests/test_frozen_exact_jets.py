"""Exact polynomial jet oracle: hand-expanded determinant, no production helper."""
from fractions import Fraction as F
import pytest
from eab.dual import Dual
from eab.kernel3d.geom3 import Polyhedron, exact_convex_view
from eab.kernel3d.frozen import ee_normal_generic, face_normal_generic, frozen_ee_sign
from eab.kernel3d.covers3 import local_facets3, facet_normal3


def test_frozen_micro_cross_keeps_primal_and_all_derivative_channels():
    e=2.**-27
    a=Polyhedron([(0.,0.,0.),(1.+e,1.,0.)],[])
    b=Polyhedron([(0.,0.,0.),(1.,1.-e,0.)],[])
    # Binary64 determinant is zero; exact determinant is +2^-54.
    assert 1.-(1.+e)*(1.-e)==0
    assert F(1)-F(1.+e)*F(1.-e)==F(1,2**54)
    assert ee_normal_generic(a,(0,1),b,(0,1))==(0.,0.,1.)
    va=[tuple(Dual.const(c,2) for c in p) for p in a.verts]
    va[1]=(va[1][0],va[1][1],Dual(0.,(1.,2.)))
    out=ee_normal_generic(Polyhedron(va,[]),(0,1),b,(0,1))
    assert [v.v for v in out]==[0.,0.,1.]
    assert [v.e[0] for v in out]==[(1.-e)*2**54,-2**54,0.]
    assert [v.e[1] for v in out]==[(1.-e)*2**55,-2**55,0.]


def test_frozen_face_jet_does_not_erase_a_micro_area():
    e=2.**-27
    vertices=[(0.,0.,0.),(1.+e,1.,0.),(1.,1.-e,0.)]
    p=Polyhedron(vertices,[(0,1,2)])
    assert face_normal_generic(p,0)==(0.,0.,-1.)
    dv=[tuple(Dual.const(c,1) for c in point) for point in vertices]
    dv[1]=(dv[1][0],dv[1][1],Dual.seed(0.,1,0))
    result=face_normal_generic(Polyhedron(dv,[(0,1,2)]),0)
    assert [v.v for v in result]==[0.,0.,-1.]
    assert [v.e[0] for v in result]==[-(1.-e)*2**54,2**54,0.]


def test_frozen_and_facet_normal_use_one_exact_orientation_on_the_same_view_and_window():
    from test_frozen_ee_sign import _stack
    a,b=map(exact_convex_view,_stack(.17,.03,4,1e5))
    labels=[lab for lab in local_facets3(a,b) if lab[0]=='EE']
    assert labels
    for label in labels:
        ea,eb=label[1][1:],label[2][1:]
        value=ee_normal_generic(a,ea,b,eb,frozen_ee_sign(a,b,ea,eb,tol=0.))
        assert value==facet_normal3(a,b,label)
