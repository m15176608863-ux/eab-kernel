"""Earliest affine lift against a hollow box: independent 1D forbidden intervals."""
import sys,json
from pathlib import Path
from fractions import Fraction as F
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'src'))
from geom3_independent_stress import make_box,transform
from eab.kernel3d.geom3 import Polyhedron
from eab.kernel3d.interlock import escape_height_covers
from eab.kernel3d.entrance3 import first_entrance3

shellboxes=[((-2,-1),(-2,2),(-2,2)),((1,2),(-2,2),(-2,2)),((-1,1),(-2,-1),(-2,2)),((-1,1),(1,2),(-2,2)),((-1,1),(-1,1),(-2,-1)),((-1,1),(-1,1),(1,2))]
outer=make_box(((-2,2),)*3);inner=make_box(((-1,1),)*3)
shell=Polyhedron(outer.verts+inner.verts,outer.faces+[tuple(j+8 for j in reversed(f)) for f in inner.faces])
def intervals(query):
    return [(F(r[2][0])-query[2][1],F(r[2][1])-query[2][0]) for r in shellboxes
            if all(min(query[k][1],F(r[k][1]))>max(query[k][0],F(r[k][0])) for k in (0,1))]
n=0;errors=[]
for scale,origin in [(F(1),(0,0,0)),(F(1,10**9),(10**8,-10**8,10**8)),(F(10**8),(-17,31,7))]:
  for z in (F(-3,2),F(-5,4),F(5,4),F(3,2)):
    q=((F(-1,4),F(1,4)),(F(-1,4),F(1,4)),(z-F(1,8),z+F(1,8)))
    spans=intervals(q);assert any(lo<0<hi for lo,hi in spans)
    root=min(t for lo,hi in spans for t in (lo,hi) if t>0 and all(not a<t<b for a,b in spans))*scale
    a=transform(make_box(q),(0,1,2),scale,origin);b=transform(shell,(0,1,2),scale,origin)
    for offset in ((0,0,0),(0.,0.,0.)):
      try:
        result=escape_height_covers(a,b,offset)
        assert result.exact_height==root,(result.exact_height,root)
        print(json.dumps({'scale':str(scale),'z':str(z),'offset_types':[type(x).__name__ for x in offset],
                          'expected_root':str(root),'exact_root':str(result.exact_height),'interval_count':len(result.interval_certificate)}),flush=True)
      except Exception as e:
        errors.append({'scale':str(scale),'z':str(z),'offset_types':[type(x).__name__ for x in offset],'exception':type(e).__name__,'message':str(e)})
      n+=1
print('EARLIEST_LIFT_PRODUCT_ORACLE',json.dumps({'queries':n,'errors':errors}),flush=True)
