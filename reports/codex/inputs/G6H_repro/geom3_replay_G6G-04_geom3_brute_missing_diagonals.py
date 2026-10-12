"""Independent slab/ridge distance certificate; no eab distance/hull/SAT oracle.
A={|x|,|y|<=1,-1<=z<=1-|x+y|/2};
B={|x|,|y|<=1,3+|x-y|/2<=z<=6}.
Both are convex, valid, outward closed embedded surfaces. Their triangulated
roof/bottom ridges attain (0,0,1),(0,0,3); slab separation gives lower bound 2.
"""
from pathlib import Path
from fractions import Fraction as F
import sys,json,math
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'src'))
from eab.kernel3d.geom3 import Polyhedron,brute_feature_distance,point_in_polyhedron
FACES=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
TRIS=[(1,0,3),(3,2,1),(7,4,5),(5,6,7),(4,0,1),(1,5,4),(5,1,2),(2,6,5),(6,2,3),(3,7,6),(7,3,0),(0,4,7)]
AV=[(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,0),(1,-1,1),(1,1,0),(-1,1,1)]
BV=[(1,-1,4),(1,1,3),(-1,1,4),(-1,-1,3),(1,-1,6),(1,1,6),(-1,1,6),(-1,-1,6)]
a,b=Polyhedron(AV,FACES.copy()),Polyhedron(BV,FACES.copy())
# Geometry proof from the fixed manual input, independent of every eab helper:
assert max(v[2] for v in AV)==1 and min(v[2] for v in BV)==3
p=tuple((F(AV[5][k])+AV[7][k])/2 for k in range(3))
q=tuple((F(BV[1][k])+BV[3][k])/2 for k in range(3))
assert p==(0,0,1) and q==(0,0,3)
assert sum((x-y)**2 for x,y in zip(p,q))==4
# Fixed roof triangles form the roof graph 1-|x+y|/2; fixed bottom triangles
# form 3+|x-y|/2. This also directly witnesses no self-intersection.
for tri in ((7,4,5),(5,6,7)):
 assert all(F(z)==1-F(abs(x+y),2) for x,y,z in (AV[i] for i in tri))
for tri in ((1,0,3),(3,2,1)):
 assert all(F(z)==3+F(abs(x-y),2) for x,y,z in (BV[i] for i in tri))
expected=2.0
source_result=brute_feature_distance(a,b)
expanded_result=brute_feature_distance(Polyhedron(AV,TRIS),Polyhedron(BV,TRIS))
row=dict(independent_distance=expected,source_result=source_result,expanded_same_surface=expanded_result,
 source_A_top_ring=FACES[1],source_B_bottom_ring=FACES[0],omitted_ridge_edges=((5,7),(1,3)),
 ridge_witness_a=list(p),ridge_witness_b=list(q),source_witness_membership=(point_in_polyhedron(p,a),point_in_polyhedron(q,b)))
print(json.dumps(row,default=str,indent=2))
assert expanded_result==expected
assert source_result==math.sqrt(6) and source_result>expected
print('CONFIRMED source-ring brute_feature_distance silently overestimates exact surface distance; true=2, returned=sqrt(6)')
