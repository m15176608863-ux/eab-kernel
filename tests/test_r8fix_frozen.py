"""G6H-02: exact interval/line oracles, no production geometric primitives.

All rotations are the independently checked rational 3-4-5 orthogonal map.
Gap and tangent derivatives follow directly from unrotated interval products;
there is no rounded unit normal in any expected result.
"""
from fractions import Fraction as F
import pytest
from eab.dual import Dual
from eab.kernel3d.geom3 import Polyhedron
from eab.kernel3d.frozen import frozen_normal, frozen_gap
from eab.kernel3d.interlock import escape_height_from_frozen_cover
from eab.margin import body_distance, margin_gap_from_frozen_cover

FACES = [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]


def _box(Q, x, y, z):
    vertices = [(x[0],y[0],z[0]),(x[1],y[0],z[0]),(x[1],y[1],z[0]),(x[0],y[1],z[0]),
                (x[0],y[0],z[1]),(x[1],y[0],z[1]),(x[1],y[1],z[1]),(x[0],y[1],z[1])]
    return Polyhedron([tuple(sum(Q[k][j]*p[j] for j in range(3)) for k in range(3))
                       for p in vertices], FACES.copy())


@pytest.mark.parametrize("c,s,M,gap", [(F(3,5),F(4,5),10**20,F(1)),
    (F(4,5),F(3,5),10**20,F(1)), (F(3,5),F(4,5),10**8,F(1,10**9))])
@pytest.mark.parametrize("swap", [False, True])
@pytest.mark.parametrize("quantity", ["gap", "tangent_derivative"])
def test_frozen_gap_and_jet_do_not_reinterpret_rounded_normals(c,s,M,gap,swap,quantity):
    Q=((c,-s,0),(s,c,0),(0,0,1))
    assert all(sum(Q[k][i]*Q[k][j] for k in range(3)) == int(i==j)
               for i in range(3) for j in range(3))
    A=_box(Q,(gap,gap+1),(F(M,2),F(M,2)+1),(-F(1,4),F(1,4)))
    B=_box(Q,(-1,0),(-M,M),(-1,1))
    if swap:
        A,B=B,A
    distance,label=body_distance(A,B,tol=0)
    assert distance == float(gap)
    assert label[0] == ("FV" if swap else "VF")
    x=tuple(Dual(0.,(float(Q[k][1]*10**20),)) for k in range(3))
    jet=margin_gap_from_frozen_cover(A,B,label,x,0)
    if quantity == "gap":
        assert margin_gap_from_frozen_cover(A,B,label,(0,0,0),0) == float(gap), "frozen signed gap"
        assert jet.v == float(gap), "zero-primal tangent seed changed gap"
        assert frozen_gap(A,B,label,x,frozen_normal(A,B,label,x=x)).v == float(gap)
    else:
        assert jet.e == (0.,), "exact rigid tangent derivative"


@pytest.mark.parametrize("kind", ["VE3", "EV3", "EE"])
@pytest.mark.parametrize("quantity", ["gap", "tangent_derivative"])
def test_all_frozen_line_formulas_keep_large_tangent_cancellation(kind,quantity):
    c,s,M=F(3,5),F(4,5),10**20
    point=(c-s*M,s+c*M,F(0))
    edge=Polyhedron([(F(0),F(0),F(0)),(-s*M,c*M,F(0))],[])
    A,B=Polyhedron([point],[]),edge
    label=("VE3",("vertex",0),("edge",0,1))
    if kind == "EV3":
        A,B=B,A
        label=("EV3",("edge",0,1),("vertex",0))
    elif kind == "EE":
        A=Polyhedron([point,(point[0],point[1],F(1))],[])
        label=("EE",("edge",0,1),("edge",0,1))
    x=(Dual(0.,(-8e19,)),Dual(0.,(6e19,)),Dual(0.,(0.,)))
    result=margin_gap_from_frozen_cover(A,B,label,x,0)
    if quantity == "gap":
        assert result.v == 1., "frozen line distance lost to tangential lever arm"
    else:
        assert result.e == (0.,), "frozen line tangent derivative"


@pytest.mark.parametrize("kind", ["VF", "FV", "EE"])
@pytest.mark.parametrize("seed", [0., 1.])
def test_frozen_lift_plain_and_dual_share_exact_raw_plane_ratio(kind,seed):
    Q=((F(3,5),-F(4,5),0),(0,0,-1),(F(4,5),F(3,5),0))
    M=10**20
    A=_box(Q,(-F(1,2),F(1,2)),(F(M,2),F(M,2)+1),(-F(1,4),F(1,4)))
    B=_box(Q,(-3,0),(-M,M),(-1,1))
    label=("VF",("vertex",0),("face",3))
    if kind == "FV":
        A,B=B,A
        label=("FV",("face",3),("vertex",0))
    elif kind == "EE":
        A=Polyhedron([A.verts[0],A.verts[4]],[])
        B=Polyhedron([B.verts[1],B.verts[2]],[])
        label=("EE",("edge",0,1),("edge",0,1))
    expected=-F(5,8) if kind=="FV" else F(5,8)
    assert escape_height_from_frozen_cover(A,B,label,(0,0,0)) == expected
    jet=escape_height_from_frozen_cover(A,B,label,(Dual(0.,(seed,)),0,0))
    assert jet.v == float(expected), "Dual seed changed exact lift primal"
    assert jet.e == (-.75*seed,), "lift derivative from independent 3-4-5 plane"


@pytest.mark.parametrize("quantity", ["gap", "derivative"])
def test_frozen_margin_rounds_after_subtracting_the_margin_parameter(quantity):
    # The margin parameter is part of the closed form, not a display value.
    # An exact rational tiny excess survives even with a large normal span.
    M=F(10**20)
    A=Polyhedron([(M+1,F(0),F(0))],[])
    B=Polyhedron([(F(0),F(0),F(0))],[])
    label=("VV3",("vertex",0),("vertex",0))
    if quantity == "gap":
        result=margin_gap_from_frozen_cover(A,B,label,(0,0,0),M)
        assert result == 1., "margin was subtracted after gap rounding"
    else:
        x=(Dual(0.,(M+1,)),0,0)
        result=margin_gap_from_frozen_cover(A,B,label,x,Dual(M,(M,)))
        assert result.v == 1.
        assert result.e == (1.,), "margin derivative was subtracted after gap rounding"


@pytest.mark.parametrize("kind", ["VF", "FV", "EE", "VE3", "EV3", "VV3"])
def test_frozen_gap_geometry_jet_retains_rigid_rotation_invariance(kind):
    c,s,M=F(3,5),F(4,5),10**20
    Q=((c,-s,0),(s,c,0),(0,0,1))
    A=_box(Q,(1,2),(F(M,2),F(M,2)+1),(-F(1,4),F(1,4)))
    B=_box(Q,(-1,0),(-M,M),(-1,1))
    label=("VF",("vertex",0),("face",3))
    if kind == "FV":
        A,B=B,A
        label=("FV",("face",3),("vertex",0))
    elif kind in ("EE","VE3","EV3"):
        p=(c-s*M,s+c*M,F(0))
        edge=Polyhedron([(F(0),)*3,(-s*M,c*M,F(0))],[])
        A,B=Polyhedron([p],[]),edge
        label=("VE3",("vertex",0),("edge",0,1))
        if kind=="EV3":
            A,B=B,A
            label=("EV3",("edge",0,1),("vertex",0))
        elif kind=="EE":
            A=Polyhedron([p,(p[0],p[1],F(1))],[])
            label=("EE",("edge",0,1),("edge",0,1))
    elif kind == "VV3":
        A=Polyhedron([(c,s,F(0))],[])
        B=Polyhedron([(F(0),)*3],[])
        label=("VV3",("vertex",0),("vertex",0))
    def rotate_jet(P):
        return Polyhedron([(Dual(x,(-y,)),Dual(y,(x,)),Dual(z,(0.,)))
                           for x,y,z in P.verts], P.faces)
    result=margin_gap_from_frozen_cover(rotate_jet(A),rotate_jet(B),label,(0,0,0),0)
    assert result.v == 1., "rigid rotation changed primal"
    assert result.e == (0.,), "raw-normal derivative cancellation was lost"


@pytest.mark.parametrize("M", [F(10**20),F(10**200),F(10)**400])
@pytest.mark.parametrize("sign", [-1,1])
def test_frozen_margin_irrational_cancellation_has_exact_midpoint_certificate(M,sign):
    # sqrt(M*M+1)-M is positive and representable for these first two cases;
    # M=1e400 puts the result below binary64 and must fail loudly. Squared
    # adjacent-output midpoint comparisons are an independent oracle.
    import math
    A=Polyhedron([(sign*M,F(sign),F(0))],[])
    B=Polyhedron([(F(0),)*3,(F(0),F(0),F(1)),(F(1),-M,F(0))],[(0,1,2)])
    label=("VF",("vertex",0),("face",0))
    if M == F(10)**400:
        with pytest.raises(ArithmeticError, match="below binary64"):
            margin_gap_from_frozen_cover(A,B,label,(0,0,0),sign*M)
        return
    result=margin_gap_from_frozen_cover(A,B,label,(0,0,0),sign*M)
    assert (result>0)==(sign>0)
    magnitude=abs(result)
    lo=(F(math.nextafter(magnitude,0.))+F(magnitude))/2
    hi=(F(math.nextafter(magnitude,math.inf))+F(magnitude))/2
    assert (M+lo)**2 < M*M+1 < (M+hi)**2, "margin output is not correctly rounded"


def test_frozen_margin_final_difference_can_be_finite_with_unrepresentable_intermediate():
    M=F(10)**400
    A=Polyhedron([(M+1,F(0),F(0))],[])
    B=Polyhedron([(F(0),)*3],[])
    label=("VV3",("vertex",0),("vertex",0))
    assert margin_gap_from_frozen_cover(A,B,label,(0,0,0),M) == 1.


def test_frozen_margin_final_jet_can_cancel_before_a_derivative_overflow():
    M=F(10)**400
    A=Polyhedron([(F(1),F(0),F(0))],[])
    B=Polyhedron([(F(0),)*3],[])
    label=("VV3",("vertex",0),("vertex",0))
    result=margin_gap_from_frozen_cover(A,B,label,(Dual(0.,(M+1,)),0,0),Dual(0.,(M,)))
    assert result.v == 1. and result.e == (1.,)


def test_raw_normal_rounding_mutant_is_caught_inside_frozen_gap(monkeypatch):
    import eab.kernel3d.frozen as frozen
    original=frozen._frozen_raw_normal
    def rounded_before_dot(*args,**kwargs):
        raw,derivatives=original(*args,**kwargs)
        display=frozen._unit_jet(raw,derivatives)
        return (tuple(F(c.v if isinstance(c,Dual) else c) for c in display),
                [tuple(F(c.e[k]) for c in display) for k in range(len(derivatives))])
    monkeypatch.setattr(frozen,"_frozen_raw_normal",rounded_before_dot)
    with pytest.raises(AssertionError,match="frozen signed gap"):
        test_frozen_gap_and_jet_do_not_reinterpret_rounded_normals(F(3,5),F(4,5),10**20,F(1),False,"gap")


def test_margin_postround_subtraction_mutant_is_caught(monkeypatch):
    import eab.kernel3d.frozen as frozen
    original=frozen._normalized_difference
    def premature_round(c,nn,offset):
        return original(c,nn,0)-float(offset)
    monkeypatch.setattr(frozen,"_normalized_difference",premature_round)
    with pytest.raises(AssertionError,match="margin was subtracted after gap rounding"):
        test_frozen_margin_rounds_after_subtracting_the_margin_parameter("gap")


@pytest.mark.parametrize("sign", [-1,1])
@pytest.mark.parametrize("step", [0,1,2])
def test_frozen_margin_exact_halfway_rounding_obeys_ties_to_even(sign,step):
    import math
    ulp=F(math.ulp(1.))
    exact=1+(F(step)+F(1,2))*ulp
    A=Polyhedron([(sign*(F(10**20)+exact),F(0),F(0))],[])
    B=Polyhedron([(F(0),)*3,(F(0),F(1),F(0)),(F(0),F(0),F(1))],[(0,1,2)])
    result=margin_gap_from_frozen_cover(A,B,("VF",("vertex",0),("face",0)),(0,0,0),sign*F(10**20))
    expected=1+(step+(step%2))*ulp
    assert result == sign*float(expected)


def test_frozen_margin_exact_zero_and_nonrepresentable_result_are_distinguished():
    import math
    B=Polyhedron([(F(0),)*3],[])
    label=("VV3",("vertex",0),("vertex",0))
    def gap(value,delta):
        return margin_gap_from_frozen_cover(Polyhedron([(value,F(0),F(0))],[]),B,label,(0,0,0),delta)
    assert gap(F(1),F(1)) == 0.
    with pytest.raises(ArithmeticError,match="below binary64"):
        gap(F(1)+F(math.ulp(0.))/4,F(1))
    with pytest.raises(OverflowError,match="finite binary64"):
        gap(F(10)**400,F(1))


@pytest.mark.parametrize("scale", [F(2)**-200,F(1),F(2)**200])
@pytest.mark.parametrize("excess", [-10000,-1,0,1,10000])
def test_margin_contact_difference_is_constructed_before_display_rounding(scale,excess):
    from eab.kernel3d.geom3 import box
    from eab.margin import margin_contacts
    M=F(10**20)
    A=box(((M+excess+1)*scale,F(0),F(0)),(scale,scale,scale))
    B=box((-scale,F(0),F(0)),(scale,2*scale,2*scale))
    rows=margin_contacts(A,B,delta=M*scale,band=(abs(excess)+1)*scale,tol=0)
    assert rows
    first=rows[0]
    assert first.exact_distance_squared == ((M+excess)*scale)**2
    assert first.margin_gap == float(excess*scale), "contact margin rounded before subtraction"
    assert first.closed == (excess<=0)


def test_contact_margin_postround_subtraction_mutant_is_caught(monkeypatch):
    import eab.margin as margin
    from eab.construction import sqrt_rational
    def premature_round(c,nn,offset,**kwargs):
        root=sqrt_rational(c*c/nn,allow_underflow=True)
        return (-root if c<0 else root)-float(offset)
    monkeypatch.setattr(margin,"_normalized_difference",premature_round)
    with pytest.raises(AssertionError,match="contact margin rounded before subtraction"):
        test_margin_contact_difference_is_constructed_before_display_rounding(F(1),10000)
