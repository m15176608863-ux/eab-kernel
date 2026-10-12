"""A tight-fit seam is interior E, not a first boundary entrance at t=0.

Oracle is a union of Cartesian Minkowski rectangle intervals, not winding,
triangulation, cones, g0_oracle, or any eab primitive.
"""
from pathlib import Path
from fractions import Fraction as F
import sys,json
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
from eab.kernel2d.entrance import first_entrance
U=[(-1,-1),(2,-1),(2,2),(1,2),(1,0),(0,0),(0,2),(-1,2)]
A=[(0,F(1,2)),(1,F(1,2)),(1,F(3,2)),(0,F(3,2))]
# U = bottom union left union right (closed product cells).
body_A=(F(0),F(1),F(1,2),F(3,2))
body_B=[(-1,2,-1,0),(-1,0,0,2),(1,2,0,2)]
E=[(F(x0)-body_A[1],F(x1)-body_A[0],F(y0)-body_A[3],F(y1)-body_A[2]) for x0,x1,y0,y1 in body_B]
assert E==[(F(-2),F(2),F(-5,2),F(-1,2)),(F(-2),F(0),F(-3,2),F(3,2)),(F(0),F(2),F(-3,2),F(3,2))]
# The two upper cells share x=0 and together form the FULL closed rectangle
# [-2,2] x [-3/2,3/2]. The bottom cell fills [-5/2,-1/2] at all x.
# Therefore the exact E union is [-2,2] x [-5/2,3/2]. Its x=0 seam is interior.
assert E[1][0]==E[0][0] and E[1][1]==E[2][0] and E[2][1]==E[0][1]
assert E[1][2:]==E[2][2:] and E[0][3]>E[1][2]
first_boundary_t=F(3,2)
assert F(-2)<0<F(2) and F(-5,2)<0<first_boundary_t
for eps in (F(1,4),F(1,2**80)):
    assert F(-2)<-eps<eps<F(2) and F(-5,2)<-eps<eps<first_boundary_t
actual=first_entrance(A,U,(0,0),(0,1))
assert actual.kind=='entrance' and actual.t_exact==0 and actual.gap==0,actual
out={'id':'G6H-GEOM2-01','severity':'major','independent_E_rectangle':['[-2,2]','[-5/2,3/2]'],'x0_in_topological_interior':True,'expected_initial_policy':'exit (per entrance.py initial-interior contract), not entrance on a boundary','first_boundary_along_positive_y':str(first_boundary_t),'actual':repr(actual),'incorrect_boundary_time':str(actual.t_exact)}
print(json.dumps(out,ensure_ascii=False,indent=2))
(ROOT/'review/agents/geom2/tight_fit_initial_state_output.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
