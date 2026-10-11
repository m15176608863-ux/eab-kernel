"""Read-only exact raw-input diagnosis of the three y-slide zero-height failures.
Witnesses are proposed independently from raw vertices/triangle centroids.
Certification uses the separate Fraction-ray implementation in walls_diagnostic;
no production geometry primitive is consulted for the certificate.
"""
import importlib.util,json,time
from fractions import Fraction as F
from pathlib import Path
p=Path(__file__).parent
spec=importlib.util.spec_from_file_location('D',p/'walls_diagnostic.py');D=importlib.util.module_from_spec(spec);spec.loader.exec_module(D)
import test_invariance_interlock as T
rows=[];start=time.perf_counter()
for t,s,observed in [(1e5,1.,2.3283064365386963e-10),(1e5,1e3,2.3283064365386963e-7),(1e3,1e-3,2.3283064365386963e-13)]:
 A,L=T._ilock('z0.7',t,s);offset=T._vec(T.ROT_Z['z0.7'],s,(0.,.3,0.));At=A.translated(offset)
 raw=D.witness(At,L);row={'rot':'z0.7','t':t,'s':s,'offset':offset,'brute_height_from_final_log':observed,'candidate':raw}
 if raw:
  q=tuple(map(F,raw));aa,bb=D.triangles(At),D.triangles(L)
  plane_values=[D.dot(D.cross(D.sub(b,a),D.sub(c,a)),D.sub(q,a)) for a,b,c in aa+bb]
  row.update(strict_inside_a=D.inside(q,aa),strict_inside_b=D.inside(q,bb),off_all_source_triangle_planes=all(v!=0 for v in plane_values),n_triangles_a=len(aa),n_triangles_b=len(bb))
  assert row['strict_inside_a'] and row['strict_inside_b'] and row['off_all_source_triangle_planes']
 rows.append(row);print(json.dumps(row),flush=True)
(p/'invariance_brute_slide_diagnostic.json').write_text(json.dumps({'elapsed':time.perf_counter()-start,'rows':rows},indent=2),encoding='utf8')
assert all(r['candidate'] for r in rows)
