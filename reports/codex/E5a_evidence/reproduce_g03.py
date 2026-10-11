"""Reproduce start-HEAD findings; --baseline reads the byte snapshot, not live edits."""
from pathlib import Path
import json
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
if '--baseline' in sys.argv:
    base = OUT / 'tmp' / 'baseline'
    with zipfile.ZipFile(OUT / 'tmp' / 'pre_e5a.zip') as z:
        for name in z.namelist():
            if name.startswith(('src/', 'tests/')):
                z.extract(name, base)
else:
    base = ROOT
sys.path[:0] = [str(base / 'src'), str(base / 'tests')]
from eab.kernel3d import covers3, g03
from eab.kernel3d.geom3 import box, convex_hull_3d, sub
from test_g03_two_rulers import _yaw, _move, _quat
from test_covers3_g0_vote2 import _random_pair

results = []
def run(name, fn):
    try:
        results.append(dict(case=name, result=fn()))
    except Exception as e:
        results.append(dict(case=name, error=repr(e)))

def summary(r):
    return dict(passed=r.passed, mismatch=r.hull_vertex_mismatch,
                ambiguous=r.e_vertices_ambiguous, facets=r.facet_symmetric_diff,
                skipped=r.band_skipped, samples=r.samples)

def default_vote():
    a, b = box(half=(1., 1., 1.)), box(center=(.3,.2,3), half=(2,1.5,.7))
    if '--baseline' in sys.argv:
        d = [sub(y,x) for x in a.verts for y in b.verts]
    else:
        from fractions import Fraction as F
        d = [tuple(F(y[k])-F(x[k]) for k in range(3)) for x in a.verts for y in b.verts]
    return g03.facet_vote3(a,b,covers3.local_facets3(a,b,1e-12),convex_hull_3d(d),d)
run('raw_39_default_facet_vote', default_vote)
for ratio, th, rot in [(1000,1e-6,7),(100,1e-7,7),(10,1e-8,3),(100,1e-7,11)]:
    def ratio_case(ratio=ratio, th=th, rot=rot):
        h=ratio/2
        a=_yaw(box(center=(0,0,h+.6),half=(.5,.5,.5)),th)
        b=box(half=(h,h,h))
        return summary(g03.g0_convex3(_move(a,_quat(rot)),_move(b,_quat(rot)),samples=0))
    run(f'raw_28_ratio_{ratio}_yaw_{th}_R{rot}',ratio_case)

raw=json.loads((ROOT/'reports/codex/inputs/g6e_findings_raw.json').read_text(encoding='utf-8-sig'))
for idx, marker, stop in [(41,'--- F2.py ---','\n# aligned rulers'),(42,'--- F3.py ---','\norig =')]:
    code=raw['findings'][idx]['how_to_reproduce'].split(marker)[1].split(stop)[0]
    code=code.replace("sys.path.insert(0, 'src')",'None')
    import io, contextlib
    def snippet(code=code):
        stream=io.StringIO()
        with contextlib.redirect_stdout(stream):exec(code,{})
        return stream.getvalue()
    run(f'raw_{idx}_original_input',snippet)

def false_vertices():
    a,b=_random_pair(0)
    before=summary(g03.g0_convex3(a,b,samples=0))
    key='cone_intersection_margin' if '--baseline' in sys.argv else 'cones_intersect_relint'
    original=getattr(covers3,key)
    try:
        setattr(covers3,key,(lambda *args:(1.,0.)) if '--baseline' in sys.argv else (lambda *args:True))
        after=summary(g03.g0_convex3(a,b,samples=0))
    finally:setattr(covers3,key,original)
    return dict(before=before,after=after)
run('raw_38_false_vertex_mutation',false_vertices)
suffix='baseline' if '--baseline' in sys.argv else 'after'
(OUT/f'g03_{suffix}.json').write_text(json.dumps(results,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
print(json.dumps(results,ensure_ascii=False,indent=2,default=str))
