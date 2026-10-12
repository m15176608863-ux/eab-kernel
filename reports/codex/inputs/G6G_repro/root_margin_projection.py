"""Independent interval-product distance oracle: translation of a convex box.
No tested distance/projection/SAT primitives appear in the oracle.
"""
from pathlib import Path
from fractions import Fraction as F
import sys,json
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'src'))
from eab.kernel3d.geom3 import box,exact_point_in_convex_polyhedron
from eab.margin import nearest_point_on_convex_entrance,distance_to_convex_entrance,inflated_normal
s=F(1,10**9)
rows=[]
for T in (F(0),F(10**3),F(10**8)):
 E=box(center=(T+2*s,0,0),half=(s,s,s)); x=(T,0,0)
 # E is [T+s,T+3s] x [-s,s]^2; x=(T,0,0), unique projection=(T+s,0,0).
 expected=(T+s,F(0),F(0)); truth=float(s)
 got=distance_to_convex_entrance(E,x); p=nearest_point_on_convex_entrance(E,x); n=inflated_normal(E,x)
 row=dict(translation=str(T),expected_distance=truth,reported_distance=got,expected_projection=list(map(str,expected)),reported_projection=p,expected_normal=(-1,0,0),reported_normal=n,exact_state=exact_point_in_convex_polyhedron(x,E))
 assert row['exact_state']==-1
 rows.append(row)
assert rows[0]['reported_distance']==rows[0]['expected_distance']
assert rows[-1]['reported_distance']==0 and rows[-1]['reported_normal'] is None
print(json.dumps(rows,ensure_ascii=False,indent=2))
(Path(__file__).resolve().parents[2]/'review/notes/root_margin_projection.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
