"""Run live internal mutants and record the precise semantic assertion killed."""
from pathlib import Path
import json
import runpy
import sys
import traceback
import pytest
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'src'))
t=runpy.run_path(str(ROOT/'tests/test_r7fix_geom3.py'))
G,C,M=t['G'],t['C'],t['M']
F,I,U=t['F'],t['I'],t['U']
rows=[]
cases=[
('G6G-04',G,'brute_feature_distance','_surface_distance_edges(A)','A.edges()',
 lambda:t['test_g6g04_folded_internal_ridges_attain_slab_distance'](0,I,F(1))),
('G6G-05',C,'facet_gap3','numerator = dot(n, sub(_qvector(x), p))',
 'numerator = Fraction(float(dot(n, sub(_qvector(x), p))))',
 lambda:t['test_g6g05_facet_gap_rounds_after_normal_length_division'](1,'facet')),
('G6G-06',M,'cover_witness','if c.in_extent and c.exact_gap_sign is not None and c.normal is not None:',
 'if False:',lambda:t['test_g6g06_margin_normal_does_not_subtract_display_points'](F(1,10**9),10**8,I,False)),
('G6G-08',G,'_mass_properties','relative = tuple(_eg.sub(p, origin) for p in points)',
 'relative = tuple(tuple(float(x) for x in _eg.sub(p, origin)) for p in points)',
 lambda:t['test_g6g08_mass_properties_use_exact_products_before_final_rounding'](-600)),
('SCAN-edge-face',G,'brute_feature_distance','if _surfaces_intersect(*triangles):','if False:',
 t['test_r7fix_brute_surface_distance_includes_edge_face_crossings']),
]
for finding,module,name,old,new,check in cases:
 with pytest.MonkeyPatch.context() as mp:
  t['_inject'](mp,module,name,old,new)
  try:
   check()
  except AssertionError as e:
   print(f'\n{finding}: KILLED at {e}')
   traceback.print_exc(file=sys.stdout)
   rows.append(dict(finding=finding,implementation=name,mutation=new,assertion=str(e),status='KILLED'))
  else:
   rows.append(dict(finding=finding,status='SURVIVED'))
(ROOT/'reports/codex/R7FIX_evidence/geom3/mutations.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
assert all(r['status']=='KILLED' for r in rows), rows
