"""R14 physical cone gates.

Oracle: raw Fraction dot/cross and equilibrium; no production geometry,
construction, generator certification or LP checker is used as truth.
"""
from fractions import Fraction as F
import math
from pathlib import Path
import pytest
from eab import limit as L
from eab.limit_multi import contacts_from_covers_multi
from eab.numeric_domain import ConstructionDomainError


def _dot(a,b):
    return sum((F(x)*F(y) for x,y in zip(a,b)),F(0))


def _cone_ok(n,g,mu):
    q=_dot(n,g)
    return q >= 0 and _dot(n,n)*_dot(g,g)-q*q <= F(mu)**2*q*q


@pytest.mark.parametrize("mu",[1e16,1e17,2**20+1,F(2**20)+F(1,2**40)])
@pytest.mark.parametrize("entry",["contact","generator","covers","multi_covers"])
def test_mu_support_bound_is_checked_at_every_public_entry(mu,entry):
    with pytest.raises(ConstructionDomainError,match="mu"):
        if entry=="contact": L.LimitContact((0,0,0),(1,2,3),mu)
        elif entry=="generator": L.friction_generators((0,0,1),mu,3)
        elif entry=="covers": L.contacts_from_covers([],mu=mu)
        else: contacts_from_covers_multi([],0,None,mu=mu)


@pytest.mark.parametrize("normal,tangent",[((1,2,3),(2,-1,0)),((3,-7,2),(1,3,9)),((0,0,1),(1,0,0))])
@pytest.mark.parametrize("mu",[0,2**-400,.5,1.8,2**20])
@pytest.mark.parametrize("k",[4,5,8])
def test_final_generators_are_exactly_unilateral_and_inside_the_circular_cone(normal,tangent,mu,k):
    ct=L.LimitContact((7,-11,2),normal,mu,tangent=tangent)
    directions=L.friction_generators(ct.normal,mu,3,k,ct.tangent)
    assert len(directions)==k
    for j,g in enumerate(directions):
        assert _dot(ct.normal,g)>0,(j,"unilateral generator",g)
        assert _cone_ok(ct.normal,g,mu),(j,"exact circular cone containment",g)


def test_high_supported_mu_single_contact_has_a_finite_safe_capacity():
    mu=2**20
    ct=L.LimitContact((0,0,0),(1,2,3),mu,tangent=(2,-1,0))
    dead=[-1,-2,-3,0,0,0]; live=[2,-1,0,0,0,0]
    result=L.limit_load([ct],dead,live,dim=3,k=4)
    assert result.status=="optimal","finite circular capacity cannot be unbounded"
    n=ct.normal; q=_dot(n,(1,2,3)); nn=_dot(n,n)
    upper=((F(mu)**2+1)*q*q-14*nn)/(5*nn)
    assert result.alpha.exact**2<=upper,"capacity exceeds independent exact circular upper bound"


def test_readme_does_not_assert_the_false_unqualified_relative_capacity_bound():
    text=(Path(__file__).resolve().parents[1]/"README.md").read_text(encoding="utf-8")
    assert "承载比的相对短缺 ≤ 1−cos(π/k)" not in text,"N05 unqualified nonlinear capacity bound"


def test_selfcheck_rejects_uncertified_generator_even_when_generator_certificate_lies(monkeypatch):
    # Inject the fault inside the production certification path, not after
    # enumeration/LP output. Checker uses independent cross-product squares.
    monkeypatch.setattr(L, "_inside_friction_cone", lambda *args: True)
    ct=L.LimitContact((0,0,0),(1,2,3),.5,tangent=(2,-1,0))
    with pytest.raises(ConstructionDomainError,match="selfcheck friction generator"):
        L._check_columns([ct],(0,0,0),3,4)


def test_exact_inward_certificate_has_teeth_when_removed(monkeypatch):
    import inspect
    source=inspect.getsource(L._certified_friction_direction)
    needle="if _inside_friction_cone(n,g,mu):"
    assert needle in source
    scope=dict(vars(L))
    exec(source.replace(needle,"if True:"),scope)
    monkeypatch.setattr(L,"_certified_friction_direction",scope["_certified_friction_direction"])
    with pytest.raises(AssertionError,match="exact circular cone containment"):
        test_final_generators_are_exactly_unilateral_and_inside_the_circular_cone((1,2,3),(2,-1,0),.5,4)


def test_nonlinear_capacity_has_no_universal_cosine_relative_error_bound():
    from test_limit import _interlock_capacity
    # Candidate at mu=1.7 is verified at the larger circular mu=9/5.
    # The LP and generator provide candidate data ONLY, not the oracle.
    candidate,cts,dead,live,N=_interlock_capacity(.25,1.7,k=4)
    assert candidate.status=="optimal"
    alpha_lower=candidate.alpha.exact
    total=[F(0)]*6
    for i,ct in enumerate(cts):
        directions=L.friction_generators(ct.normal,ct.mu,3,4,ct.tangent)
        f=tuple(sum((candidate.lambdas[4*i+j].exact*F(directions[j][a]) for j in range(4)),F(0)) for a in range(3))
        assert _dot(ct.normal,f)>=0,"independent candidate compression"
        q=_dot(ct.normal,f)
        assert _dot(ct.normal,ct.normal)*_dot(f,f)-q*q<=F(9,5)**2*q*q,"independent circular certificate"
        x,y,z=map(F,ct.point)
        moments=(y*f[2]-z*f[1],z*f[0]-x*f[2],x*f[1]-y*f[0])
        for a,v in enumerate((*f,*moments)): total[a]+=v
    assert all(total[a]+F(dead[a])+alpha_lower*F(live[a])==0 for a in range(6)),"independent six exact equilibrium rows"
    tmax=max(abs(F(c.normal[0]))/F(c.normal[2]) for c in cts)
    assert all(F(c.normal[1])==0 and F(c.normal[2])>0 for c in cts)
    assert F(1.8)*tmax<1,"true circle capacity has a finite force-projection upper bound"
    # cos(pi/5)>4/5, cos(pi/6)>4/5, cos(pi/7)>9/10.
    assert F(5)>F(11,5)**2 and F(3,4)>F(4,5)**2
    x=F(22,49)
    assert 1-x*x/2+x**4/24-x**6/720>F(9,10)
    for k,lower_cos in ((5,F(4,5)),(6,F(4,5)),(7,F(9,10))):
        result,new_cts,new_dead,new_live,NN=_interlock_capacity(.25,1.8,k=k)
        assert result.status=="optimal"
        assert [(c.point,c.normal) for c in new_cts]==[(c.point,c.normal) for c in cts]
        assert new_dead==dead and new_live==live and NN==N
        assert result.alpha.exact<lower_cos*alpha_lower,"nonlinear counterexample must defeat a cosine relative bound"


@pytest.mark.parametrize("normal",[(3,4),(1,3),(-7,2)])
@pytest.mark.parametrize("mu",[.5,1.8,2**20])
def test_two_d_final_generators_also_stay_inside_the_exact_physical_cone(normal,mu):
    ct=L.LimitContact((0,0),normal,mu)
    for g in L.friction_generators(ct.normal,mu,2):
        assert _cone_ok(ct.normal,g,mu),"2D exact circular cone containment"


@pytest.mark.parametrize("dim,normal,tangent",[(2,(3,4),None),(3,(1,2,3),(2,-1,0)),(3,(3,-7,2),(1,3,9))])
@pytest.mark.parametrize("k",[4,5,8])
def test_cohesive_columns_are_exactly_tangential_and_in_the_unit_disk(dim,normal,tangent,k):
    ct=L.LimitContact((0,)*dim,normal,.5,cohesion=3,area=2,tangent=tangent)
    columns=L._build_columns([ct],(0,)*dim,dim,k,unit_cohesion=True)
    found=0
    for col,row in zip(columns.cols,columns.row_of):
        if row is not None:
            found+=1
            assert _dot(ct.normal,col[:dim])==0,"cohesive force must be exactly tangential"
            assert _dot(col[:dim],col[:dim])<=1,"cohesive force must lie in the unit disk"
    assert found==(2 if dim==2 else k)



def test_cohesion_projection_is_independently_checked_even_if_constructor_lies(monkeypatch):
    import inspect
    source=inspect.getsource(L._cohesion_directions)
    needle="projected = tuple(b-normal_part*a for a,b in zip(n,v))"
    assert source.count(needle)==1
    scope=dict(vars(L));exec(source.replace(needle,"projected = tuple(v)"),scope)
    monkeypatch.setattr(L,"_cohesion_directions",scope["_cohesion_directions"])
    ct=L.LimitContact((0,0,0),(1,2,3),.5,cohesion=3,area=2,tangent=(2,-1,0))
    with pytest.raises(ConstructionDomainError,match="selfcheck cohesive direction"):
        L._check_columns([ct],(0,0,0),3,4)


@pytest.mark.parametrize("cohesion",[-1.,math.nan,math.inf,-math.inf])
def test_empty_cover_adapter_rejects_invalid_cohesion(cohesion):
    with pytest.raises(ValueError,match="cohesion"):
        L.contacts_from_covers([],mu=.5,cohesion=cohesion)


@pytest.mark.parametrize("field",["cohesion","area"])
@pytest.mark.parametrize("value",[-1.,math.nan,math.inf,-math.inf])
def test_mutated_material_is_rechecked_before_building_any_lp_columns(field,value):
    ct=L.LimitContact((0,0),(0,1),.5,cohesion=1,area=1)
    setattr(ct,field,value)
    with pytest.raises(ValueError,match=field):
        L.limit_load([ct],[0,-1,0],[1,0,0],dim=2)


@pytest.mark.parametrize("normal",[(.6,.8),(1.,3.),(-math.sin(.37),math.cos(.37)),(-7.,2.)])
@pytest.mark.parametrize("mu",[0.,.5,1.8,2**20,2**-40,2**-400])
def test_two_d_final_generator_uses_the_nearest_safe_one_ulp_neighbor(normal,mu):
    # Oracle uses direct exact determinant inequalities for the TWO-DIMENSIONAL
    # cone, not production dot/norm certification or tangent construction.
    n=tuple(F(x) for x in normal)
    t=(-n[1],n[0])
    actual=L.friction_generators(normal,mu,2)
    for sign,g in zip((1,-1),actual):
        initial=tuple(float(n[i]+sign*F(mu)*t[i]) for i in range(2))
        def safe(v):
            x,y=map(F,v)
            normal_work=n[0]*x+n[1]*y
            shear=n[0]*y-n[1]*x
            return normal_work>0 and shear*shear<=F(mu)**2*normal_work*normal_work
        if safe(initial):
            expected=initial
        else:
            grid=[(v,math.nextafter(v,-math.inf),math.nextafter(v,math.inf)) for v in initial]
            candidates=[]
            for x in grid[0]:
                for y in grid[1]:
                    trial=(x,y)
                    sign_retained=all(a==0 or (b!=0 and (a>0)==(b>0)) for a,b in zip(initial,trial))
                    if all(math.isfinite(z) for z in trial) and sign_retained and safe(trial):
                        square=sum((F(a)-F(b))**2 for a,b in zip(initial,trial))
                        candidates.append((square,trial))
            assert candidates,"test grid must have a safe same-sign neighboring representation"
            expected=min(candidates)[1]
        assert g==expected,"2D nearest exactly safe binary64 neighbor"
        assert safe(g),"2D independent determinant cone certificate"
        assert all(a==0 or (b!=0 and (a>0)==(b>0)) for a,b in zip(initial,g)),"nonzero component sign retained"


def test_two_d_neighbor_removal_is_caught_by_the_unchanged_near_lock_gate(monkeypatch):
    import inspect
    from test_lp_certificates import test_near_self_locking_is_certified_within_its_reported_uncertainty_or_loud
    source=inspect.getsource(L._certified_friction_direction)
    needle="if len(n) == 2:"
    assert source.count(needle)==1
    scope=dict(vars(L));exec(source.replace(needle,"if False:"),scope)
    monkeypatch.setattr(L,"_certified_friction_direction",scope["_certified_friction_direction"])
    # This is the old physical error assertion, not a newly relaxed uncertainty
    # or changed analytic reference. The coarse fallback is the actual defect.
    with pytest.raises(AssertionError) as caught:
        test_near_self_locking_is_certified_within_its_reported_uncertainty_or_loud(1e-9,(.37,(3e4,-2e3),1.))
    import linecache
    trace=caught.value.__traceback__
    while trace.tb_next is not None:
        trace=trace.tb_next
    statement=linecache.getline(trace.tb_frame.f_code.co_filename,trace.tb_lineno)
    assert "assert abs(r.alpha - exact) <=" in statement,"mutant must fail original closed-form error budget, not status/uncertainty"
