"""Finite coordinates and representable truth, but G0's float diameter is inf."""
from pathlib import Path
from fractions import Fraction as F
import sys,json,math
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
from eab.kernel2d import covers as C,g0
m=float.fromhex('0x1.fffffffffffffp1023');h=m/2;k=m/4
# L solid is the union of bottom [-h,h]x[-h,0] and left [-h,0]x[0,h].
# A is in the upper-right void. Nearest distance to either arm is exactly k;
# there is no geometry oracle involved in computing this Cartesian product gap.
B=[(-h,-h),(h,-h),(h,0),(0,0),(0,h),(-h,h)]
A=[(k,k),(k+k/4,k),(k+k/4,k+k/4),(k,k+k/4)]
assert all(math.isfinite(c) for P in (A,B) for p in P for c in p)
truth=F(A[0][0]);assert truth==F(k)>0 and float(truth)==k
length=g0.char_length(A,B);assert math.isinf(length)
baseline=g0.g0_distance_completeness(A,B,[(0,0)])
assert baseline.samples==1 and baseline.passed and baseline.worst_abs_error==0
saved_side,saved_vv=C._ve_side,C.vv_cover
# Delete candidates at their actual cone-validity path, before output exists.
C._ve_side=lambda *args,**kwargs:-1
C.vv_cover=lambda *args,**kwargs:None
try:
    assert C.enumerate_covers(A,B,window=math.inf)==[]
    mutant=g0.g0_distance_completeness(A,B,[(0,0)])
    assert mutant.samples==1 and mutant.passed and math.isinf(mutant.worst_abs_error)
    assert mutant.failures==[]
finally:
    C._ve_side,C.vv_cover=saved_side,saved_vv
out={'all_input_coordinates_finite':True,'independent_exact_distance_display':k,
     'float_characteristic_length':str(length),
     'baseline':{'samples':baseline.samples,'passed':baseline.passed,'worst_abs_error':baseline.worst_abs_error},
     'internal_cone_mutant':{'covers':0,'samples':mutant.samples,'passed':mutant.passed,
                             'worst_abs_error':str(mutant.worst_abs_error),'failures':mutant.failures},
     'cause':'atol*L = inf; abs(inf - finite) > inf is False'}
print(json.dumps(out,indent=2))
