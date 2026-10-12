"""WO-PERF arrangement variants, exact first-witness values and timings."""
from pathlib import Path
import inspect
import json
import sys
import time
from statistics import median

ROOT = Path(__file__).resolve().parents[4]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'tools'), str(ROOT/'tests')]
from eab.kernel3d import exact_geom as G, exact_sweep as S, interlock as I
from eab.kernel3d.geom3 import Polyhedron, box
from osteomorphic import interlocking_pair
from perf_witness_reference import reference_witness

OUT = Path(__file__).resolve().parent


def compile_variant(source):
    namespace = dict(G.__dict__)
    exec(source, namespace)
    return namespace['_surface_interior_witness']


def timed(fn):
    runs = []
    for _ in range(3):
        start = time.perf_counter()
        fn()
        runs.append(time.perf_counter()-start)
    return median(runs)


def args(A,B):
    at,bt = G.triangles(A),G.triangles(B)
    return at,bt,G._planes(at),G._planes(bt)


def main():
    code=(OUT/'optimized_function.py.txt').read_text(encoding='utf-8-sig')
    same_side='''                source_sides=[dot(m,sub(p,a)) for p in tri]
                if min(source_sides)>=0 or max(source_sides)<=0:
                    continue
'''
    aabb='''            if any(max(v[i] for v in tri)<lo or min(v[i] for v in tri)>hi
                   for i,(lo,hi) in enumerate(qb)):
                continue
'''
    assert same_side in code and aabb in code
    functions=[('baseline',reference_witness),
               ('plane_hoist',compile_variant(code.replace(same_side,'').replace(aabb,''))),
               ('plane_hoist_aabb',compile_variant(code.replace(same_side,''))),
               ('all_three',compile_variant(code)),
               ('all_three_grouped',G._surface_interior_witness)]
    cases=[('box_same',box(),box()),('box_touch',box(),box().translated((2,0,0))),
           ('box_partial',box(),box().translated((.3,.7,-.2))),
           ('box_disjoint',box(),box().translated((3,0,0)))]
    A,B=interlocking_pair(nx=5,ny=2,amp=.3,phase=1.)
    off=(.23,.07,0.)
    sol=I.escape_height_covers(A,B,off)
    cases.extend([('interlock_seated',A,B),('interlock_intruding',S.translate_exact(A,off),B),
                  ('interlock_exact_root',S.translate_exact(A,sol.exact_offset),B)])
    def engineering(P):
        return Polyhedron([tuple(G.F(10**6)+G.F(x)/1000 for x in p) for p in P.verts],list(P.faces))
    cases.extend([(name+'_engineering',engineering(a),engineering(b)) for name,a,b in cases[-3:]])
    rows=[]
    for name,a,b in cases:
        data=args(a,b)
        expected=reference_witness(*data)
        row=dict(case=name,witness=None if expected is None else [str(c) for c in expected])
        for fname,fn in functions:
            assert fn(*data)==expected,(name,fname)
            row[fname+'_seconds']=timed(lambda:fn(*data))
        rows.append(row)
    (OUT/'microbench_variants.json').write_text(json.dumps(rows,indent=2),encoding='utf8')
    print(json.dumps(rows,indent=2))


if __name__=='__main__':main()
