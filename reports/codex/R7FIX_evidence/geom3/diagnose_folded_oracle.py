from pathlib import Path
import sys,re,json,math
from decimal import Decimal,localcontext
from fractions import Fraction as F
ROOT=Path.cwd();sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests'),str(ROOT/'tools')]
import test_invariance_interlock as T
import e5a_cover_oracle as O
import e5a2_surface_oracle as S
logs=ROOT/'reports/codex/R7FIX_evidence'
source=logs/'round3_full_suite.log'
if not source.exists(): source=logs/'full_suite.log'
text=source.read_text(encoding='utf-8')
ids=re.findall(r'FAILED tests/test_invariance_interlock.py::test_margin_labels_are_identical_under_rigid_motion\[([^\]]+)\]',text)
rows=[]
for case in dict.fromkeys(ids):
 name,rot,t,s=case.split('-');t=float(t);s=float(s)
 _,a0,b0,d0,*_=T._margin_ref(name)
 a,b=T._rigid(a0,T.ROT_3[rot],t,s),T._rigid(b0,T.ROT_3[rot],t,s)
 # Explicit pre-fix descriptor model; these separated fixtures never clamp.
 old={label:O.witness_distance(a,b,label) for label,_ in O.cover_labels(a,b)
      if O.witness_distance(a,b,label)<=1.5*s*d0}
 for c in T.margin_contacts(a,b,delta=1.5*s*d0):
  if abs(c.distance-old[c.label])<=4*math.ulp(old[c.label]):continue
  kind,fa,fb=c.label
  X,Y,vertex,face=(a,b,fa[1],fb[1]) if kind=='VF' else (b,a,fb[1],fa[1])
  p=tuple(map(F,X.verts[vertex]));ys=tuple(tuple(map(F,v)) for v in Y.verts);ring=Y.faces[face]
  n=O._model(Y)[2][face];nonplanar=any(O.dot(n,O.sub(ys[i],ys[ring[0]])) for i in ring)
  squared=min(S._point_tri_sq(p,tri) for tri in S._ring_triangles(ys,ring))
  with localcontext() as ctx:
   ctx.prec=120;exact=float((Decimal(squared.numerator)/Decimal(squared.denominator)).sqrt())
  row=dict(case=case,label=c.label,nonplanar=bool(nonplanar),old_newell_display=old[c.label],actual=c.distance,independent_triangle=exact,
           exact_squared=str(squared),actual_ulps=abs(c.distance-exact)/math.ulp(exact),old_ulps=abs(old[c.label]-exact)/math.ulp(exact))
  print(row['case'],row['label'],row['actual_ulps'],row['old_ulps'])
  assert nonplanar and abs(c.distance-exact)<=4*math.ulp(exact),row
  rows.append(row)
assert len({r['case'] for r in rows})==16,rows
(ROOT/'reports/codex/R7FIX_evidence/geom3/folded_oracle_diagnosis.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
