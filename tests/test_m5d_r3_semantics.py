"""M5d R3 refusal gates and threshold-edge adversaries.

Oracle import inventory: m5d_r3_oracle -> fractions, functools, math only;
m5c_teeth_oracle -> fractions only. Production imports are SUT/input adapters.
No production intersection, interval, root or orientation is an oracle.
"""
from fractions import Fraction as F
from functools import lru_cache
from itertools import product
from random import Random

import pytest
from mutation_support import replace_module_callable
from m5c_teeth_oracle import translation_first_events, point_strictly_inside
from m5d_r3_oracle import first_events, affine_perturb, point
from eab.kernel2d import m5c_certificates as cert
from eab.kernel2d import model_robustness as adapters
from eab.kernel2d.dda_motion import DDAAnchoredMotion

DIAMOND = ((-2, 0), (-1, F(-1, 2)), (0, 0), (-1, F(1, 2)))
WALL = ((1, -2), (3, -2), (3, 2), (1, 2))


def paths(ring, velocity=(0, 0)):
    return tuple(((F(x), F(velocity[0])), (F(y), F(velocity[1])), (F(1),)) for x,y in ring)


def early_case(which):
    if which == 'late':
        # x-1=400(s-2/5)(s-1/2)(s-3/5). First bottom-edge
        # contact is 17/40, but nominated wall contact is 3/5.
        coefficients, height, speed = (F(-47),F(296),F(-600),F(400)), F(-11), F(20)
        bracket, witness = (F(59,100),F(61,100)), F(43,100)
    else:
        # x-1=400(s-1/10)(s-1/5)(s-3/5). First bottom-edge
        # contact is 3/20, before the omitted first half of [0,l].
        coefficients, height, speed = (F(-19,5),F(80),F(-360),F(400)), F(-13,4), F(5)
        bracket, witness = (F(5999,10000),F(6001,10000)), F(4,25)
    aa=tuple(((F(x)/10+coefficients[0],)+coefficients[1:],(F(y)+height,speed),(F(1),))
             for x,y in DIAMOND)
    assert point_strictly_inside(point(aa[3], witness), WALL)
    assert witness < bracket[0]
    return aa, paths(WALL), ('VE',2,3), bracket, 0, 0


@pytest.mark.parametrize('which', ('late','early'))
def test_r3_complete_early_window_rejects_prebracket_contact(which):
    assert cert.single_cover_certificate(*early_case(which)) is None, \
        'R3 complete early window rejects prebracket contact'


def test_r3_ev_competitor_precedes_nominated_ve():
    a=((-2,-10),(0,0),(-2,10)); b=((1,1),(3,-1),(3,3))
    assert translation_first_events(a,b,(4,0)) == (F(3,10),(('EV',1,0),))
    assert cert.single_cover_certificate(paths(a,(4,0)),paths(b),('VE',1,0),(F(1,4),F(11,20))) is None, \
        'R3 EV competitor precedes nominated VE'


@pytest.mark.parametrize('side', (-1,1))
def test_r3_both_projection_sides_reject_line_extensions(side):
    a=tuple((x,y+5*side) for x,y in DIAMOND)
    assert translation_first_events(a,WALL,(2,0)) == (None,())
    assert cert.single_cover_certificate(paths(a,(2,0)),paths(WALL),('VE',2,3),(F(2,5),F(3,5))) is None, \
        'R3 both projections reject a line extension'


def test_r3_final_panel_rejects_departed_endpoint():
    a=((F(-198,1000),F(1403,1000)),(F(-1198,1000),F(2403,1000)),(F(-2198,1000),F(1903,1000)))
    assert translation_first_events(a,WALL,(2,1)) == (None,())
    assert cert.single_cover_certificate(paths(a,(2,1)),paths(WALL),('VE',0,3),(F(29,50),F(3,5))) is None, \
        'R3 final panel rejects the departed endpoint'


def test_r3_linf_tube_requires_l1_dual_normalization():
    a=((0,0),(2,0),(0,2)); b=((2,2),(4,2),(2,4)); radius=F(3,5)
    # Allowed translations (+r,+r),(-r,-r) overlap along diagonal.
    assert point_strictly_inside((F(3,2),F(3,2)),tuple((x-radius,y-radius) for x,y in b))
    assert point_strictly_inside((F(3,2),F(3,2)),tuple((x+radius,y+radius) for x,y in a))
    assert cert.relative_separation_certificate(paths(a),paths(b),radius,radius) is None, \
        'R3 L1 dual normalization rejects overlapping coordinate tubes'


def budget_case(radius):
    a=tuple((10*x,10*y) for x,y in DIAMOND)
    b=((1,-20),(3,-20),(3,20),(1,20))
    return paths(a,(2,0)), paths(b), ('VE',2,3), (F(2,5),F(3,5)), radius, radius


@pytest.mark.parametrize('radius',(F(7,100),F(1661,25000)))
def test_r3_endpoint_and_edge_error_budget_contract_refuses(radius):
    # Contract counterexample, NOT a claim that every omitted conservative
    # term admits an actual false first label for this particular geometry.
    assert cert.single_cover_certificate(*budget_case(radius)) is None, \
        'R3 endpoint and edge error budget contract refuses'


@pytest.mark.parametrize('moving',('vertex','edge'))
def test_r3_endpoint_budget_prevents_actual_out_of_bracket_contact(moving):
    height=19 if moving=='edge' else 0
    a=tuple((10*x,10*y+height) for x,y in DIAMOND); b=((1,-20),(3,-20),(3,20),(1,20))
    radius=F(3,100); bracket=(F(1,4),F(51,100))
    perturbed_a=tuple((x-radius,y) for x,y in a) if moving=='vertex' else a
    perturbed_b=tuple((x+radius,y) for x,y in b) if moving=='edge' else b
    time,labels=translation_first_events(perturbed_a,perturbed_b,(2,0))
    assert labels == (('VE',2,3),) and time==F(103,200)>bracket[1]
    ra,rb=(radius,0) if moving=='vertex' else (0,radius)
    assert cert.single_cover_certificate(paths(a,(2,0)),paths(b),('VE',2,3),bracket,ra,rb) is None, \
        'R3 endpoint budget rejects actual out-of-bracket first contact'


def test_r3_bilinear_budgets_include_both_endpoints_and_all_terms():
    p=paths(((2,5),(4,6),(1,6)))
    q=paths(((-2,1),(4,-3),(5,6)))
    result=cert._event(p,q,0,0,F(1,7),F(2,11),F(0),F(0))
    # U=(6,-4), W=(4,4), V=(-2,8): unequal endpoint L1 lengths
    # are essential to expose ev=ew or a reused W length.
    expected_w=F(4,11)*8+F(25,77)*10+2*F(4,11)*F(25,77)
    expected_v=F(4,11)*10+F(25,77)*10+2*F(4,11)*F(25,77)
    assert expected_w != expected_v
    assert result[3] == expected_w, 'R3 W endpoint budget includes edge-length and mixed errors'
    assert result[4] == expected_v, 'R3 V endpoint budget includes edge-length and mixed errors'


def p2_input_paths(ring,u,translation,center,strain):
    # Exact data construction, not an oracle. The dedicated adapter identity
    # test below verifies this fixture really is the specified P2 family.
    answer=[]
    for px,py in ring:
        x,y=px-center[0],py-center[1]
        ex=strain[0][0]*x+strain[0][1]*y
        ey=strain[1][0]*x+strain[1][1]*y
        dx,dy=translation
        answer.append(((px,dx-2*u*y+ex,u*u*(center[0]-x),u*u*(dx+ex)),
                       (py,dy+2*u*x+ey,u*u*(center[1]-y),u*u*(dy+ey)),
                       (F(1),F(0),u*u)))
    return tuple(answer)


def p2_specs(offset=0):
    return ((F(1,10),(F(23,10),F(1,10)),(offset,0),
             ((F(1,100),F(1,200)),(F(1,200),F(1,50)))),
            (F(-1,5),(F(3,10),F(1,10)),(offset+2,0),
             ((F(-3,200),F(7,1000)),(F(7,1000),F(1,100)))))


def p2_case(offset=0):
    a=tuple((x+offset,y) for x,y in DIAMOND)
    b=tuple((x+offset,y) for x,y in WALL)
    ma,mb=p2_specs(offset)
    aa,bb=p2_input_paths(a,*ma),p2_input_paths(b,*mb)
    assert aa[0][2] != bb[0][2] and len(aa[0][2]) == len(bb[0][2]) == 3
    return aa,bb,('VE',2,3),(F(2,5),F(1,2))


def test_r3_unequal_moving_strained_fixture_is_actual_p2():
    for offset in (0,-100):
        aa,bb,_,_=p2_case(offset)
        for ring,spec,expected in zip((DIAMOND,WALL),p2_specs(offset),(aa,bb)):
            moved=tuple((x+offset,y) for x,y in ring)
            motion=DDAAnchoredMotion(*spec)
            assert adapters.dda_paths(moved,motion)==expected, 'R3 fixture is the actual unequal-denominator P2'


def test_r3_unequal_p2_denominators_reject_false_time_bracket():
    a,b,label,_=p2_case(-100); bracket=(F(3,10),F(2,5))
    first,labels=first_events(a,b)
    assert labels == (label,) and first.sign((-bracket[1],1)) > 0
    assert cert.single_cover_certificate(a,b,label,bracket) is None, \
        'R3 unequal P2 denominators reject a false time bracket'


@lru_cache(maxsize=1)
def threshold_bracket():
    args=p2_case()
    lower,upper=F(0),F(1,8)
    assert cert.single_cover_certificate(*args,lower,lower) is not None
    assert cert.single_cover_certificate(*args,upper,upper) is None
    for _ in range(40):
        middle=(lower+upper)/2
        if cert.single_cover_certificate(*args,middle,middle) is None:
            upper=middle
        else:
            lower=middle
    assert lower > 0 and upper-lower == F(1,2**43)
    assert upper-lower <= lower*F(1,2**24)/64, "threshold bisection uncertainty is below edge offset / 64"
    return lower,upper


def perturbations(a,b,radius,seed=5101626,count=6):
    rng=Random(seed)
    result=[]
    for index in range(count):
        all_errors=[]
        for ring in (a,b):
            errors=tuple(tuple(tuple(radius*F(rng.randrange(-8,9),8) for _ in (0,1))
                               for _ in (0,1)) for _ in ring)
            assert all(abs(v)<=radius for row in errors for pair in row for v in pair)
            all_errors.append(errors)
        # Different vertex errors and different time endpoints establish that
        # these are genuinely nonrigid, time-varying tube paths.
        assert len({row for errors in all_errors for row in errors}) > 2
        result.append(tuple(affine_perturb(ring,errors) for ring,errors in zip((a,b),all_errors)))
    return result


@pytest.mark.parametrize('factor',(F(1,2),1-F(1,2**24)))
def test_r3_threshold_edge_nonrigid_p2_perturbations_preserve_first_label_and_time(factor):
    a,b,label,bracket=p2_case(); lower,upper=threshold_bracket(); radius=lower*factor
    result=cert.single_cover_certificate(a,b,label,bracket,radius,radius)
    assert result is not None, 'R3 threshold-edge radius must be certified'
    seen=set()
    for aa,bb in perturbations(a,b,radius):
        first,labels=first_events(aa,bb)
        assert labels == (label,), 'R3 threshold-edge nonrigid first label agrees with independent oracle'
        assert first.sign((-bracket[0],1))>0 and first.sign((-bracket[1],1))<0, \
            'R3 threshold-edge nonrigid first time lies in the open bracket'
        seen.add((aa,bb))
    assert len(seen)==6, 'fixed-seed perturbation products must be distinct'


def transformed(paths_,scale,offset,u):
    from m5d_r3_oracle import add
    c,s=(1-u*u)/(1+u*u),2*u/(1+u*u)
    return tuple((add(add(tuple(scale*c*x for x in p[0]),tuple(-scale*s*y for y in p[1])),tuple(offset[0]*v for v in p[2])),
                  add(add(tuple(scale*s*x for x in p[0]),tuple(scale*c*y for y in p[1])),tuple(offset[1]*v for v in p[2])),p[2]) for p in paths_)


@pytest.mark.parametrize('scale,offset,u',(
    (F(1), (0,0), F(0)),
    (F(1,2**40), (10**6,-10**6), F(2,7)),
    (F(2**30), (-10**5,10**3), F(-3,8)),
))
def test_r3_p2_certificate_rigid_unit_covariance(scale,offset,u):
    a,b,label,bracket=p2_case()
    # Deliberately interior radius avoids claiming the sufficient enclosure
    # algorithm has an invariant maximal certifiable radius.
    radius=scale*(abs((1-u*u)/(1+u*u))+abs(2*u/(1+u*u)))/100000
    aa,bb=(transformed(ring,scale,offset,u) for ring in (a,b))
    result=cert.single_cover_certificate(aa,bb,label,bracket,radius,radius)
    assert result is not None and result['label']==label, 'R3 moving P2 rigid-unit covariance'
    first,labels=first_events(aa,bb)
    assert labels==(label,) and first.sign((-bracket[0],1))>0 and first.sign((-bracket[1],1))<0


# Calling the named gates directly bypasses source-hash/frozen-summary tripwires.
# Each replacement mutates real SUT code, before any result is produced.
MUTATIONS=(
 ('early_skip','diagnose_single_cover','_separation(a, b, ra, rb, F(0), lo, panels)','dict(gap_lower=F(1))',
  test_r3_complete_early_window_rejects_prebracket_contact,('late',),'R3 complete early window'),
 ('early_short_first_half','diagnose_single_cover','F(0), lo, panels','F(0), lo/2, panels',
  test_r3_complete_early_window_rejects_prebracket_contact,('late',),'R3 complete early window'),
 ('early_only_second_half','diagnose_single_cover','F(0), lo, panels','lo/2, lo, panels',
  test_r3_complete_early_window_rejects_prebracket_contact,('early',),'R3 complete early window'),
 ('omit_ev','diagnose_single_cover','((a, b, ra, rb, "VE"), (b, a, rb, ra, "EV"))','((a, b, ra, rb, "VE"),)',
  test_r3_ev_competitor_precedes_nominated_ve,(),'R3 EV competitor'),
 ('omit_projection_g','diagnose_single_cover','min(g[0]-ew, h[0]-ev)','h[0]-ev',
  test_r3_both_projection_sides_reject_line_extensions,(1,),'R3 both projections'),
 ('omit_projection_h','diagnose_single_cover','min(g[0]-ew, h[0]-ev)','g[0]-ew',
  test_r3_both_projection_sides_reject_line_extensions,(-1,),'R3 both projections'),
 ('omit_last_panel','diagnose_single_cover','base._panels(lo, hi, panels):','base._panels(lo, hi, panels)[:-1]:',
  test_r3_final_panel_rejects_departed_endpoint,(),'R3 final panel'),
 ('linf_instead_l1','_separation','abs(n[0])+abs(n[1])','max(abs(n[0]),abs(n[1]))',
  test_r3_linf_tube_requires_l1_dual_normalization,(),'R3 L1 dual normalization'),
 ('wrong_equal_denominator_branch','_relative','if p[2] == q[2]:','if True:',
  test_r3_unequal_p2_denominators_reject_false_time_bracket,(),'R3 unequal P2 denominators'),
 ('omit_endpoint_end_budget','diagnose_single_cover','endpoint_end=end[0][0]-end[3]','endpoint_end=end[0][0]',
  test_r3_endpoint_budget_prevents_actual_out_of_bracket_contact,('vertex',),'R3 endpoint budget rejects actual'),
 ('omit_w_endpoint_error','_event','ew = du*_length1(w, lo, hi)+dw*_length1(u, lo, hi)+2*du*dw','ew = dw*_length1(u, lo, hi)+2*du*dw',
  test_r3_endpoint_and_edge_error_budget_contract_refuses,(F(7,100),),'R3 endpoint and edge error budget'),
 ('omit_edge_length_error','_event','ew = du*_length1(w, lo, hi)+dw*_length1(u, lo, hi)+2*du*dw','ew = du*_length1(w, lo, hi)+2*du*dw',
  test_r3_endpoint_budget_prevents_actual_out_of_bracket_contact,('vertex',),'R3 endpoint budget rejects actual'),
 ('omit_edge_length_error_moving_B','_event','ew = du*_length1(w, lo, hi)+dw*_length1(u, lo, hi)+2*du*dw','ew = du*_length1(w, lo, hi)+2*du*dw',
  test_r3_endpoint_budget_prevents_actual_out_of_bracket_contact,('edge',),'R3 endpoint budget rejects actual'),
 ('omit_mixed_error','_event','ew = du*_length1(w, lo, hi)+dw*_length1(u, lo, hi)+2*du*dw','ew = du*_length1(w, lo, hi)+dw*_length1(u, lo, hi)',
  test_r3_endpoint_and_edge_error_budget_contract_refuses,(F(1661,25000),),'R3 endpoint and edge error budget'),
 ('reuse_wrong_endpoint_budget','_event','ev = du*_length1(v, lo, hi)+dw*_length1(u, lo, hi)+2*du*dw','ev = ew',
  test_r3_bilinear_budgets_include_both_endpoints_and_all_terms,(),'R3 V endpoint budget'),
)


@pytest.mark.parametrize('case',MUTATIONS,ids=[row[0] for row in MUTATIONS])
def test_r3_internal_mutations_die_at_the_named_semantic_assertion(monkeypatch,case):
    _,name,before,after,gate,args,message=case
    replace_module_callable(monkeypatch,cert,name,[(before,after)])
    with pytest.raises(AssertionError,match=message):
        gate(*args)


@pytest.mark.parametrize('which,term',product(('w','v'),(0,1,2)))
def test_r3_each_internal_error_term_has_independent_budget_teeth(monkeypatch,which,term):
    terms=[f'du*_length1({which}, lo, hi)','dw*_length1(u, lo, hi)','2*du*dw']
    before=f'e{which} = '+'+'.join(terms)
    after=f'e{which} = '+'+'.join(t for i,t in enumerate(terms) if i!=term)
    replace_module_callable(monkeypatch,cert,'_event',[(before,after)])
    with pytest.raises(AssertionError,match=f'R3 {which.upper()} endpoint budget'):
        test_r3_bilinear_budgets_include_both_endpoints_and_all_terms()


def test_r3_independent_oracle_root_partition_matches_exact_factorization():
    from m5d_r3_oracle import roots,compare,Root
    for polynomial,expected in (
        ((F(-3,32),F(11,16),F(-3,2),F(1)),(F(1,4),F(1,2),F(3,4))),
        ((F(1,4),F(-1),F(1)),(F(1,2),)),
        ((F(0),F(-1),F(1)),(F(0),F(1))),
    ):
        found=roots(polynomial)
        assert len(found)==len(expected)
        assert all(compare(root,Root.rational(time))==0 for root,time in zip(found,expected)), \
            'independent Sturm worklist preserves exact endpoints and repeated roots'
