"""E4 exact self-check gates. Oracle: hand-injected rational errors / analytic equilibrium;
no LP assembly, wrench, or power primitive is shared by the oracle assertions.
"""
import copy
from fractions import Fraction as F
from math import cos, sin

import pytest
import eab.limit as L
import eab.limit_multi as M
from eab.limit import LimitContact as C
from eab.limit_multi import BodyContact as BC, LimitBody as B


def q(v):
    return getattr(v, "exact", F(v))


def slide(mu=1e-5, W=10., cohesion=0., D=0., h=.5):
    cs = [C((D+x, 0.), (0., 1.), mu, cohesion=cohesion, area=1.) for x in (-1., 1.)]
    return cs, [0., -W, -D*W], [1., 0., -h]


@pytest.mark.parametrize("k", [3, 5, 9, 15, 30, 100])
@pytest.mark.parametrize("case", ["small_mu", "small_cohesion", "far", "tall"])
def test_exact_single_static_and_gap_reject_arbitrary_rational_alpha_error(k, case):
    args = dict(mu=1e-5)
    if case == "small_cohesion": args = dict(mu=0., W=1e6, cohesion=5.)
    if case == "far": args = dict(mu=.6, D=1e4)
    if case == "tall": args = dict(mu=.6, h=1e3)
    cs, dead, live = slide(**args)
    r = L.limit_load(cs, dead, live, dim=2)
    assert L.check_duality(r, cs, dead, live, dim=2)["ok"]
    r.alpha = q(r.alpha) * (1 - F(1, 10**k))
    d = L.check_duality(r, cs, dead, live, dim=2)
    assert not d["static_ok"], (k, case, d)
    assert not d["ok"], (k, case, d)


@pytest.mark.parametrize("k", [3, 9, 30, 100])
def test_exact_single_live_solver_path_catches_alpha_injection(monkeypatch, k):
    real = L.maximize
    def skew(A,b,c,**kw):
        r = real(A,b,c,**kw)
        if r.status == "optimal":
            j = next(j for j,v in enumerate(c) if v)
            r.x[j] = q(r.x[j]) * (1-F(1,10**k))
        return r
    monkeypatch.setattr(L, "maximize", skew)
    with pytest.raises(RuntimeError, match="self-check"):
        L.limit_load(*slide(), dim=2)


@pytest.mark.parametrize("k", [3, 9, 30, 100])
def test_exact_admissibility_has_no_tall_body_or_other_body_speed_tolerance(k):
    cs, dead, live = slide(mu=.6, h=1e3)
    r = L.limit_load(cs,dead,live,dim=2)
    r.mechanism = [q(v) for v in r.mechanism]
    r.mechanism[1] -= F(1,10**k)
    assert not L.mechanism_is_admissible(r.mechanism,cs,dim=2)
    assert not L.check_duality(r,cs,dead,live,dim=2)["admissible"]
    slow = C((0.,0.),(0.,1.),0.)
    fast = C((1e4,0.),(0.,1.),0.)
    ms = [[F(0),-F(1,10**k),F(0)], [F(10**20),F(0),F(0)]]
    assert not M.mechanism_is_admissible_multi(ms,[BC(slow,0),BC(fast,1)],dim=2)


@pytest.mark.parametrize("dim", [2,3])
@pytest.mark.parametrize("k", [3,9,30,100])
def test_exact_multi_rejects_small_alpha_and_unrelated_heavy_body(k,dim):
    if dim == 2:
        cs,dead,live=slide()
        bs=[B(dead,live),B([0.,-1e20,-1e24],[0.,0.,0.])]
        bcs=[BC(c,0) for c in cs]+[BC(C((1e4+x,0.),(0.,1.),0.),1) for x in (-1.,1.)]
    else:
        cs=[C((x,y,0.),(0.,0.,1.),1e-5) for x in (-1.,1.) for y in (-.5,.5)]
        bs=[B([0.,0.,-10.,0.,0.,0.],[1.,0.,0.,0.,.5,0.]), B([0.,0.,-1e20,0.,1e24,0.],[0.]*6)]
        bcs=[BC(c,0) for c in cs]+[BC(C((1e4+x,y,0.),(0.,0.,1.),0.),1) for x in (-1.,1.) for y in (-.5,.5)]
    r=M.limit_load_multi(bs,bcs,dim=dim)
    assert M.check_duality_multi(r,bs,bcs,dim=dim)["ok"]
    r.alpha=q(r.alpha)*(1-F(1,10**k))
    d=M.check_duality_multi(r,bs,bcs,dim=dim)
    assert not d["static_ok"] and not d["ok"], d


@pytest.mark.parametrize("v", [1e-6,1e-8])
@pytest.mark.parametrize("D", [1e2,1e4,1e6])
def test_multi_resolvability_uses_only_each_bodys_local_frame(v,D):
    ct=C((1.,0.),(sin(1.2),cos(1.2)),1.)
    body=B([0.,-1.,0.],[-1.,v,0.])
    alone=M.limit_load_multi([body],[BC(ct,0)],dim=2)
    far=B([0.,-10.,-10.*D],[0.]*3)
    both=M.limit_load_multi([body,far],[BC(ct,0)]+[BC(C((D+x,0.),(0.,1.),.5),1) for x in (-.5,.5)],dim=2)
    assert both.status == alone.status == "optimal"
    assert both.alpha == alone.alpha
    assert both.uncertainty == pytest.approx(alone.uncertainty,rel=1e-12)


def test_single_unloaded_far_contact_cannot_hide_a_pure_couple_residual():
    cs,dead,_=slide(mu=.6)
    cs += [C((1e6,0.),(0.,1.),.6)]
    live=[0.,0.,1.]
    r=L.limit_load(cs,dead,live,dim=2)
    r.alpha=q(r.alpha)*F(999,1000)
    assert not L.check_duality(r,cs,dead,live,dim=2)["static_ok"]


@pytest.mark.parametrize("field", ["alpha", "lambda", "mechanism", "row"])
@pytest.mark.parametrize("bad", [float("nan"),float("inf"),float("-inf")])
def test_exact_selfcheck_rejects_nonfinite_edited_fields(field,bad):
    cs,dead,live=slide(mu=0.,cohesion=1.)
    r=L.limit_load(cs,dead,live,dim=2)
    if field == "alpha": r.alpha=bad
    if field == "lambda": r.lambdas[0]=bad
    if field == "mechanism": r.mechanism[0]=bad
    if field == "row": r.row_duals[0]=bad
    with pytest.raises(ValueError,match="finite"):
        L.check_duality(r,cs,dead,live,dim=2)


def test_exact_witness_is_preserved_by_copy_not_by_float_arithmetic():
    import json
    cs,dead,live=slide(mu=.6,h=3.)
    r=L.limit_load(cs,dead,live,dim=2)
    assert isinstance(r.alpha,float) and q(r.alpha) == F(10,3)
    assert L.check_duality(copy.deepcopy(r),cs,dead,live,dim=2)["ok"]
    assert json.loads(json.dumps(r.alpha)) == float(r.alpha)
    assert not hasattr(r.alpha*1.,"exact")
    with pytest.raises(AttributeError): r.alpha.exact = F(0)
    # 显示值不是精确解，显式 float 往返后不再假称静力成立。
    r.alpha=float(r.alpha)
    assert not L.check_duality(r,cs,dead,live,dim=2)["static_ok"]


@pytest.mark.parametrize("poison", ["primal", "dual"])
def test_poisoned_lp_exact_witness_is_rechecked_on_independent_model(monkeypatch,poison):
    real=L.maximize
    def skew(A,b,c,**kw):
        r=real(A,b,c,**kw)
        if r.status == "optimal":
            name="exact_x" if poison == "primal" else "exact_y"
            seq=list(getattr(r,name))
            j=next(j for j,v in enumerate(c) if v) if poison == "primal" else 0
            seq[j]+=F(1,10**100)
            setattr(r,name,tuple(seq))
        return r
    monkeypatch.setattr(L,"maximize",skew)
    with pytest.raises(RuntimeError,match="self-check"):
        L.limit_load(*slide(),dim=2)


@pytest.mark.parametrize("k", [3,9,30,100])
@pytest.mark.parametrize("W", [10.,1e6,1e20])
def test_multi_exact_duality_rejects_statically_feasible_suboptimal_interpolation(k,W):
    # 三块：两块叠放倾覆控制，加任意重的不动无关块。死载 λ0 独立按 N/2 构造。
    bs=[B([0.,-30.,0.],[0.]*3), B([0.,-10.,0.],[1.,0.,-2.]), B([0.,-W,-5.*W],[0.]*3)]
    bcs=[BC(C((x,0.),(0.,1.),1.2),0) for x in (-1.,1.)]
    bcs += [BC(C((x,1.),(0.,1.),1.2),1,0) for x in (-1.,1.)]
    bcs += [BC(C((5.+x,0.),(0.,1.),1.2),2) for x in (-1.,1.)]
    r=M.limit_load_multi(bs,bcs,dim=2)
    f=1-F(1,10**k)
    lam0=[F(n)/2 for n in (20,20,5,5,F(W)/2,F(W)/2) for _ in range(2)]
    r.alpha=q(r.alpha)*f
    r.lambdas=[q(a)*f+(1-f)*b for a,b in zip(r.lambdas,lam0)]
    d=M.check_duality_multi(r,bs,bcs,dim=2)
    assert d["static_ok"],d
    assert F(d["duality_gap_exact"]) > 0 and not d["ok"],d


@pytest.mark.parametrize("loaded_body",[0,1])
@pytest.mark.parametrize("branch",["infeasible","finite"])
def test_multi_unbounded_screen_covers_both_rejection_branches_and_nonzero_body(loaded_body,branch):
    if branch == "infeasible":
        a=-2.2145790363256497
        T=(456126.84150283627,6015705.33931258)
        rot=lambda v:(cos(a)*v[0]-sin(a)*v[1],sin(a)*v[0]+cos(a)*v[1])
        pt=lambda p:tuple(rot(p)[i]+T[i] for i in range(2))
        n=rot((-0.8414709848078965,0.5403023058681398))
        cs=[C(pt((1.,0.)),n,1.),C(pt((1.5,0.)),n,.2,cohesion=1.,area=1.)]
        dead=L.wrench(rot((0.,-10.)),pt((0.,.7)),(0.,0.),2)
        live=L.wrench(rot((1.,0.)),pt((0.,0.)),(0.,0.),2)
    else:
        cs=[C((-2683300.084913029,-1166311.8482405145),(.9854095035625761,.1702002064879991),1.),
            C((-2683300.085281646,-1166311.8485783334),(.9854095035625761,.1702002064879991),.2,cohesion=1e6,area=1e-6)]
        dead=[-6.756375623672026,7.372339413771618,-27662239.917033132]
        live=[-.7372339413771618,-.6756375623672026,953093.6477171098]
    bs=[B(dead,live)]; bcs=[BC(c,loaded_body) for c in cs]
    if loaded_body:
        bs.insert(0,B([0.,-10.,0.],[0.]*3))
        bcs += [BC(C((x,0.),(0.,1.),.5),0) for x in (-1.,1.)]
    r=M.limit_load_multi(bs,bcs,dim=2,k=4)
    assert r.status == "unbounded"
    if branch == "finite":
        assert r.resolvability == "unresolved" and "optimal" in r.resolvability_statuses
    else:
        assert r.resolvability == "nearby_infeasible" and "infeasible" in r.resolvability_statuses
