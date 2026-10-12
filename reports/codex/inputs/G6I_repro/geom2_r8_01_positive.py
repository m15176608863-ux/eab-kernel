"""R8-01 positive replay with independently proven tight-fit Cartesian E."""
from pathlib import Path
from fractions import Fraction as F
import sys,json
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
from eab.kernel2d.entrance import first_entrance
from eab.kernel2d.covers import membership_convex
from eab.kernel2d.exact import polygons_overlap_exact,entrance_membership_exact
U=[(-1,-1),(2,-1),(2,2),(1,2),(1,0),(0,0),(0,2),(-1,2)]
A=[(0,F(1,2)),(1,F(1,2)),(1,F(3,2)),(0,F(3,2))]
# U product decomposition gives E=[-2,2]x[-5/2,3/2], including seam x=0.
actual=first_entrance(A,U,(0,0),(0,1))
assert actual.kind=='exit' and actual.t_exact==0 and actual.gap==0,actual
assert polygons_overlap_exact(A,U)==0
assert entrance_membership_exact(A,U)==membership_convex(A,U,(0,0))==1
print(json.dumps({'id':'G6H-01','status':'FIXED','body_state':0,'E_state':1,'actual':repr(actual)},ensure_ascii=False,indent=2))
