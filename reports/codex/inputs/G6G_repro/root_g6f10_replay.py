"""G6F10 exact difference model/documentation replay, with recorded output."""
from pathlib import Path
from fractions import Fraction as F
import sys,json
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
from eab.kernel3d.geom3 import box
from eab.margin import entrance_block_convex
A=box(center=(1.,0.,0.),half=(.5,.5,.5))
B=box(center=(1e16,0.,0.),half=(4.,.5,.5))
E=entrance_block_convex(A,B)
# Independent Cartesian-product difference: minimum b - maximum a.
truth=min(F(p[0]) for p in B.verts)-max(F(p[0]) for p in A.verts)
rounded=F(min(b[0]-a[0] for a in A.verts for b in B.verts))
actual=min(F(p[0]) for p in E.verts)
doc=(ROOT/'docs/canon_map.md').read_text(encoding='utf-8-sig')
assert actual==truth and actual!=rounded
assert '仍先浮点构造 b−a' not in doc
claim=next((i+1,s) for i,s in enumerate(doc.splitlines()) if '先有理化输入再作 b−a' in s)
print(json.dumps({'old_case':'G6F10','status':'已修','independent_exact_min':str(truth),
                  'early_float_min':str(rounded),'actual_min':str(actual),'current_claim':claim},ensure_ascii=False,indent=2))
