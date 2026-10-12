"""Unconfirmed contract boundary: no silent wrong result, so not a finding.
Direct Fraction coordinate data removes the separate box constructor domain.
"""
from fractions import Fraction as F
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
from eab.kernel3d.geom3 import Polyhedron,polyhedra_overlap
from eab.kernel3d.entrance_topology import entrance_membership3
from eab.margin import body_distance,inflated_membership
faces=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
def cube(s,c):
    return Polyhedron([(c[0]+x*s,c[1]+y*s,c[2]+z*s) for x,y,z in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]],faces)
rows=[]
for exponent in [-400,-1000,-1070,-1074]:
    s=F(2)**exponent;a=cube(s,(F(0),)*3);b=cube(s,(4*s,F(0),F(0)))
    row={'exponent':exponent,'exact_gap':str(2*s),'exact_overlap':polyhedra_overlap(a,b),'exact_E':entrance_membership3(a,b)}
    for name,fn in [('body_distance',lambda:body_distance(a,b)),('inflated_membership',lambda:inflated_membership(a,b,delta=0))]:
      try:row[name]=str(fn())
      except Exception as e:row[name]=type(e).__name__+': '+str(e)
    rows.append(row)
print(json.dumps(rows,indent=2))
(ROOT/'review/evidence/geometry_unconfirmed_range.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
