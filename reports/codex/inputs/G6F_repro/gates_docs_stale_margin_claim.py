"""Reproduce a current canon_map code-description mismatch without edits."""
from pathlib import Path
from fractions import Fraction as F
import sys,json
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
from eab.kernel3d.geom3 import box
from eab.margin import entrance_block_convex

lines=(ROOT/'docs/canon_map.md').read_text(encoding='utf-8-sig').splitlines()
line=next((i+1,s) for i,s in enumerate(lines) if '仍先浮点构造 b−a' in s)
A=box(center=(1.,0.,0.),half=(.5,.5,.5))
B=box(center=(1e16,0.,0.),half=(4.,.5,.5))
E=entrance_block_convex(A,B)
exact_min=min(F(b[0])-F(a[0]) for a in A.verts for b in B.verts)
rounded_min=min(b[0]-a[0] for a in A.verts for b in B.verts)
actual_min=min(F(v[0]) for v in E.verts)
assert actual_min==exact_min and actual_min!=F(rounded_min)
output={'doc_line':line[0],'doc_claim':'margin.entrance_block_convex 仍先浮点构造 b−a',
        'exact_min_x':str(exact_min),'rounded_difference_min_x':str(F(rounded_min)),
        'actual_min_x':str(actual_min),'code_actually_preserves_exact_input_difference':True}
print(json.dumps(output,ensure_ascii=False,indent=2))
