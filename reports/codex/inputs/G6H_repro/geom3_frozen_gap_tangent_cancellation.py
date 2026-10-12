"""G6H: independent rotated-interval gap and rigid-tangent derivative oracle.
No production dot/cross/normal/triangulation is used by the oracle. A and B are
images of exact interval products under a directly proved rational orthogonal Q.
Their nearest source VF face gap is independently 1 (or 1e-9) and tangent motion
has zero derivative. This is the label actually returned by body_distance.
"""
from pathlib import Path
from fractions import Fraction as F
import sys,json
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"src"))
from eab.kernel3d.geom3 import Polyhedron
from eab.margin import body_distance,margin_gap_from_frozen_cover
from eab.kernel3d.frozen import frozen_normal
from eab.dual import Dual
FACES=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
def make(Q,x,y,z):
    v=[(x[0],y[0],z[0]),(x[1],y[0],z[0]),(x[1],y[1],z[0]),(x[0],y[1],z[0]),
       (x[0],y[0],z[1]),(x[1],y[0],z[1]),(x[1],y[1],z[1]),(x[0],y[1],z[1])]
    return Polyhedron([tuple(sum(Q[k][j]*p[j] for j in range(3)) for k in range(3)) for p in v],FACES.copy())
rows=[]
for c,s,M,gap in [(F(3,5),F(4,5),10**20,F(1)),(F(4,5),F(3,5),10**20,F(1)),
                    (F(3,5),F(4,5),10**8,F(1,10**9))]:
    Q=((c,-s,F(0)),(s,c,F(0)),(F(0),F(0),F(1)))
    assert all(sum(Q[k][i]*Q[k][j] for k in range(3))==int(i==j) for i in range(3) for j in range(3))
    A=make(Q,(gap,gap+1),(F(M,2),F(M,2)+1),(-F(1,4),F(1,4)))
    B=make(Q,(-1,0),(-M,M),(-1,1))
    # Interval products overlap in y and z, are separated by gap in x.
    # Q preserves squared length. Therefore distance=gap; A's lower-x vertices
    # project into B's upper-x face, and that is the uniquely nearest plane.
    d,label=body_distance(A,B,tol=0)
    assert d==float(gap) and label[0]=="VF"
    n=frozen_normal(A,B,label)
    actual=margin_gap_from_frozen_cover(A,B,label,(0,0,0),0)
    # A rigid tangent translation remains within B's y span near time 0;
    # distance has exactly zero derivative. Binary64 seeds are exact integers.
    speed=10**20
    x=tuple(Dual(0.,(float(Q[k][1]*speed),)) for k in range(3))
    dual=margin_gap_from_frozen_cover(A,B,label,x,0)
    rows.append(dict(M=str(M),gap=str(gap),Q=Q,body_distance=d,label=label,
                     normal=n,frozen_gap=actual,expected_gap=float(gap),
                     tangent_seed=tuple(float(Q[k][1]*speed) for k in range(3)),
                     frozen_gap_dual_primal=dual.v,tangent_derivative=dual.e[0],expected_derivative=0.0))
    assert abs(actual-float(gap))>float(gap),(actual,gap)
    assert abs(dual.e[0])>1000,dual
print(json.dumps(dict(result="CONFIRMED",rows=rows),default=str,indent=2))
print("CONFIRMED: nearest frozen cover gives wrong signed gap and nonzero derivative for exact rigid tangential motion")

# The lift API fixes the plain-primal case with the exact raw-plane ratio,
# but dispatches zero-seeded Dual input back through the rounded normal.
from eab.kernel3d.entrance3 import shortest_exit3
from eab.kernel3d.interlock import escape_height_from_frozen_cover
Q=((F(3,5),-F(4,5),0),(0,0,-1),(F(4,5),F(3,5),0))
M=10**20
A=make(Q,(-F(1,2),F(1,2)),(F(M,2),F(M,2)+1),(-F(1,4),F(1,4)))
B=make(Q,(-3,0),(-M,M),(-1,1))
label=("VF",("vertex",0),("face",3))
exit_result=shortest_exit3(A,B,(0,0,0),tol=0)
assert label in exit_result.members and exit_result.gap == -.5
plain=escape_height_from_frozen_cover(A,B,label,(0,0,0))
jet=escape_height_from_frozen_cover(A,B,label,(Dual(0.,(0.,)),0,0))
# In this basis, vertical motion has normal coordinate 4h/5; A min x=-1/2.
# It ceases intrusion at h=5/8, while all tangent/lateral intervals stay interior.
assert plain==F(5,8)
assert jet.v < -1000 and jet.e==(0.,)
print(json.dumps(dict(zero_seed_dual_lift=dict(actual_label=label,chosen_members=exit_result.members,
 plain_exact=str(plain),zero_seed_dual_primal=jet.v,zero_seed_dual_derivative=jet.e,
 expected_primal=.625,expected_derivative=(0.,))),indent=2))
print("CONFIRMED: adding a zero Dual seed changes the exact plain lift 5/8 into a negative huge lift")
