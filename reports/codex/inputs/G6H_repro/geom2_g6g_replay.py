"""G6H: full subcase replay of G6G 01/02/03; all arithmetic oracles independent."""
from pathlib import Path
from fractions import Fraction as F
from decimal import Decimal, localcontext
import sys, math, json
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'src'))
from eab.kernel2d import covers as C, g0

out=[]
B=[(0,0),(3,0),(3,1),(1,1),(1,3),(0,3)]
A=[(F(1,2),F(3,2)),(1,F(3,2)),(1,2),(F(1,2),2)]
t=g0.brute_ray_exit(A,B,(1,-1))
assert t==F(1,2), t
baseline=g0.g0_exit_completeness(A,B,[(0,0)],[(1,-1)])
saved_side,saved_vv=C._ve_side,C.vv_cover
def bad_side(P,i,Q,j,*args,**kwargs):
    return -1 if min(p[0] for p in P)==1 or min(p[0] for p in Q)==1 else saved_side(P,i,Q,j,*args,**kwargs)
def bad_vv(P,i,Q,j,*args,**kwargs):
    return None if min(p[0] for p in P)==1 or min(p[0] for p in Q)==1 else saved_vv(P,i,Q,j,*args,**kwargs)
C._ve_side,C.vv_cover=bad_side,bad_vv
try:
    mutant=g0.g0_exit_completeness(A,B,[(0,0)],[(1,-1)])
finally:C._ve_side,C.vv_cover=saved_side,saved_vv
assert baseline.samples==mutant.samples==1 and baseline.passed and not mutant.passed
out.append({'id':'G6G-01','status':'已修','first_exit':str(t),'expected':'1/2','baseline_passed':baseline.passed,'mutant_passed':mutant.passed,'mutant_output':repr(mutant)})

def sq(dx,dy,s):return [(dx,dy),(dx+s,dy),(dx+s,dy+s),(dx,dy+s)]
def sqrt_ref(q):
    with localcontext() as ctx:
        ctx.prec=160
        return float((Decimal(q.numerator)/Decimal(q.denominator)).sqrt())
q=F(2)**-1074;s=F(2)**-600
values=[]
for dx,dy,label in [(float(q),float(q),'binary64 minsubnormal'),(F(149,100)*q,F(49,100)*q,'Fraction subnormal differential')]:
    c=C.vv_cover(sq(dx,dy,s),0,sq(-s,-s,s),2)
    square=F(dx)**2+F(dy)**2
    expected_gap=sqrt_ref(square)
    expected_normal=tuple(sqrt_ref(F(v)**2/square) for v in (dx,dy))
    assert c.gap==expected_gap and c.normal==expected_normal and c.strict, c
    values.append({'input':label,'gap':c.gap,'expected_gap':expected_gap,'normal':c.normal,'expected_normal':expected_normal,'strict':c.strict})
m=sys.float_info.max;h=m/2;k=m/4
A=[(h,h),(h+k,h),(h+k,h+k),(h,h+k)]
B=[(-h-k,-h-k),(-h,-h-k),(-h,-h),(-h-k,-h)]
try:C.vv_cover(A,0,B,2)
except (ArithmeticError,OverflowError) as e:values.append({'input':'maxfinite differential','exception':repr(e)})
else:raise AssertionError('unrepresentable norm must fail loud')
out.append({'id':'G6G-02','status':'已修','subcases':values})

B=[(-h,-h),(h,-h),(h,0),(0,0),(0,h),(-h,h)]
A=[(k,k),(k+k/4,k),(k+k/4,k+k/4),(k,k+k/4)]
try:g0.char_length(A,B)
except (ArithmeticError,OverflowError) as e:length_exception=repr(e)
else:raise AssertionError('unrepresentable diameter must fail loud')
values=[]
for mode in ['distance','exit']:
    if mode=='exit':A=[(-k,k),(k,k),(k,k+k/4),(-k,k+k/4)]
    run=(lambda:g0.g0_distance_completeness(A,B,[(0,0)])) if mode=='distance' else (lambda:g0.g0_exit_completeness(A,B,[(0,0)],[(k,0)]))
    baseline=run()
    C._ve_side=lambda *args,**kwargs:-1;C.vv_cover=lambda *args,**kwargs:None
    try:mutant=run()
    finally:C._ve_side,C.vv_cover=saved_side,saved_vv
    assert baseline.samples==mutant.samples==1 and baseline.passed and not mutant.passed,(mode,baseline,mutant)
    values.append({'mode':mode,'baseline':repr(baseline),'mutant':repr(mutant)})
out.append({'id':'G6G-03','status':'已修','char_length_exception':length_exception,'subcases':values})
print(json.dumps(out,ensure_ascii=False,indent=2))
(ROOT/'review/agents/geom2/g6g_replay.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
