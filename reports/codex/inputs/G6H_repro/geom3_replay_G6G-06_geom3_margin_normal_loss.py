"""Independent slab+ridges oracle: exact nearest vector normal survives translation.
Input faces are already triangles; no nonplanar-ring API assumption is needed.
"""
from pathlib import Path
from fractions import Fraction as F
import sys,json,math
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'src'))
from eab.kernel3d.geom3 import Polyhedron
from eab.margin import body_distance,margin_contacts
TRIS=[(1,0,3),(3,2,1),(7,4,5),(5,6,7),(4,0,1),(1,5,4),(5,1,2),(2,6,5),(6,2,3),(3,7,6),(7,3,0),(0,4,7)]
AV=[(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,0),(1,-1,1),(1,1,0),(-1,1,1)]
BV=[(1,-1,2),(1,1,1),(-1,1,2),(-1,-1,1),(1,-1,4),(1,1,4),(-1,1,4),(-1,-1,4)]
I=((1,0,0),(0,1,0),(0,0,1));R=((F(3,5),0,F(4,5)),(0,1,0),(-F(4,5),0,F(3,5)))
assert all(sum(R[k][i]*R[k][j] for k in range(3))==(i==j) for i in range(3) for j in range(3))
rows=[]
for gap,T,Q in [(F(1,10**9),F(0),I),(F(1,10**9),F(10**8),I),(F(1,5*10**7),F(10**8),R)]:
 def pose(p):return tuple(T+sum(F(Q[k][j])*F(p[j]) for j in range(3)) for k in range(3))
 a=Polyhedron([pose(p) for p in AV],TRIS.copy())
 b=Polyhedron([pose((x,y,F(z)+gap)) for x,y,z in BV],TRIS.copy())
 assert not a.manifold_issues() and not b.manifold_issues()
 # Independent original-frame slab: A hasz<=1, B hasz>=1+gap, two
 # fixed manual ridge midpoints attain these faces; orthogonality preserves
 # min distance gap and gives exact normal B->A=-Q*e_z.
 assert max(v[2] for v in AV)==1 and min(v[2] for v in BV)==1
 expected=tuple(-float(Q[k][2]) for k in range(3))
 cs=margin_contacts(a,b,delta=2*gap,tol=0)
 assert len(cs)==1 and cs[0].distance==float(gap) and cs[0].exact_distance_squared==gap*gap
 c=cs[0]
 rows.append(dict(gap=str(gap),translation=str(T),rotation='identity' if Q==I else 'exact_3_4_5',
 expected_normal=expected,reported_normal=c.normal,reported_distance=c.distance,label=c.label,
 point_a=c.point_a,point_b=c.point_b,body_distance=body_distance(a,b,tol=0)[0]))
assert rows[0]['reported_normal']==rows[0]['expected_normal']
assert rows[1]['reported_normal'] is None and rows[1]['point_a']==rows[1]['point_b']
assert rows[2]['reported_normal'] is not None
error=max(abs(x-y) for x,y in zip(rows[2]['reported_normal'],rows[2]['expected_normal']))
assert error>0.05
print(json.dumps(dict(result='CONFIRMED',rows=rows,rotated_normal_max_abs_error=error),indent=2))
print('CONFIRMED exact default margin distance remains correct but public normal is erased or directionally wrong by rounded global EE witnesses')
