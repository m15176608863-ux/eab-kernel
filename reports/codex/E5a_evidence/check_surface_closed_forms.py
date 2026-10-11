"""Independent closed-form checks for new exact surface membership APIs."""
from fractions import Fraction as F
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'src'))
from eab.kernel3d.geom3 import Polyhedron, exact_point_in_polyhedron
from eab.kernel3d.exact_geom import triangle_intersection, segment_crosses


def prism(base):
    n = len(base)
    v = [(x,y,z) for z in (F(-1),F(1)) for x,y in base]
    f = [tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]
    f += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    return Polyhedron(v,f)


base = [(F(x),F(y)) for x,y in [(0,0),(3,0),(3,1),(1,1),(1,3),(0,3)]]
unit = prism(base)
count = 0
for scale in (F(1,10**200), F(1,1000), F(1), F(1000), F(10**200)):
    obj = Polyhedron([tuple(scale*v for v in p) for p in unit.verts],unit.faces)
    for x in map(F,(-1,0,.5,1,1.5,3,4)):
        for y in map(F,(-1,0,.5,1,1.5,3,4)):
            for z in map(F,(-2,-1,0,1,2)):
                closed = 0 <= x <= 3 and 0 <= y <= 3 and (x <= 1 or y <= 1) and -1 <= z <= 1
                inside = 0 < x < 3 and 0 < y < 3 and (x < 1 or y < 1) and -1 < z < 1
                want = 1 if inside else 0 if closed else -1
                got = exact_point_in_polyhedron(tuple(scale*v for v in (x,y,z)),obj)
                assert got == want,(scale,x,y,z,got,want)
                count += 1

# Warped top quad ear clips on diagonal (top bottom-right, top upper-left).
# Its roof is exactly 1 + max(0,x+y)*h/2, not a fitted plane or convex hull.
base2 = [(F(x),F(y)) for x,y in [(-1,-1),(1,-1),(1,1),(-1,1)]]
warped_count = 0
for h in (F(1,10**100),F(1,3)):
    obj = prism(base2)
    obj.verts[6] = (F(1),F(1),F(1)+h)
    for x in map(F,(-.75,-.5,0,.5,.75)):
        for y in map(F,(-.75,-.5,0,.5,.75)):
            roof = 1 + max(F(0),x+y)*h/2
            for dz,want in ((-h/10,1),(F(0),0),(h/10,-1)):
                p = (x,y,roof+dz)
                got = exact_point_in_polyhedron(p,obj)
                assert got == want,(h,p,got,want)
                warped_count += 1

out = dict(l_prism_cases=count, scales=['1e-200','1e-3','1','1e3','1e200'],
           warped_roof_cases=warped_count, warped_roof='1+max(0,x+y)*h/2',
           mismatches=0, oracle='independent closed coordinate inequalities; no production geometric primitive')
Path(__file__).with_name('filters_surface_closed_forms.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps(out))
