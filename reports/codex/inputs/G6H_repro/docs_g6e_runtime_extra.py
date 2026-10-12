from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests'),str(ROOT/'tools')]
from eab.kernel3d.geom3 import box
from eab.kernel3d.covers3 import enumerate_covers3
from eab.kernel3d.entrance3 import merge_degenerate
from eab.kernel3d.g03 import g0_convex3
A=box(center=(0,0,1),half=(.5,.5,.5));B=box(half=(1,1,.5))
cs=enumerate_covers3(A,B,window=1e-9,tol=1e-9)
merged=merge_degenerate(A,B,cs)
g=g0_convex3(box(),box(),samples=1)
from dataclasses import fields
from eab.contact_record import ContactRecord
import test_limit_arch as T
out={'G6E04_17':{'dataclass_fields':[f.name for f in fields(ContactRecord)],'cover_kinds':sorted({c.kind for c in cs}),'merged_family_kinds':[m[0][0] for m in merged]},'G6E05':{'passed':g.passed,'band_skipped':g.band_skipped,'samples':g.samples,'boundary_checked':g.boundary_checked,'boundary_probes':g.boundary_probes},'G6E16':{'hinge_mechanisms_arch5':len(T.ARCH5.hinge_mechanisms()),'hinge_mechanisms_arch7':len(T.ARCH7.hinge_mechanisms())}}
assert out['G6E04_17']['cover_kinds']==['VF']
assert out['G6E04_17']['merged_family_kinds']==['FF']
assert 'canonical_order_key' not in out['G6E04_17']['dataclass_fields']
assert g.passed and g.band_skipped==0 and g.samples==1+g.boundary_probes and g.boundary_checked==g.boundary_probes==26
assert out['G6E16']['hinge_mechanisms_arch5']==10 and out['G6E16']['hinge_mechanisms_arch7']==28
print(json.dumps(out,ensure_ascii=False,indent=2));(ROOT/'review/agents/docs_gates/g6e_runtime_extra.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
