"""Read-only G03 scan; internal mutations live only in a temporary namespace."""
from pathlib import Path
import inspect
import json
import math
import sys

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / "src"))
from eab.kernel3d import covers3 as C, g03 as G, g03_surface_oracle as O
from eab.kernel3d.geom3 import Polyhedron, box

FACES = [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
AV = [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,0),(1,-1,1),(1,1,0),(-1,1,1)]
BV = [(1,-1,4),(1,1,3),(-1,1,4),(-1,-1,3),(1,-1,6),(1,1,6),(-1,1,6),(-1,-1,6)]
rows = []
distance = O.separated_distance(AV,FACES,BV,FACES)
assert distance == 2
ma, mb = O.model(tuple(AV),tuple(FACES)), O.model(tuple(BV),tuple(FACES))
assert (AV[5],AV[7]) in ma[2] and (BV[1],BV[3]) in mb[2]
rows.append(dict(check="G6G-04 folded source rings", result=distance,
                 internal_ridges_present=True))

source = inspect.getsource(C.enumerate_covers3)
# Defect: the enumerator's internal accumulation drops every real candidate.
# This is not appending fabricated output after calling production code.
mutated = source.replace("out.append(c)", "pass  # internal all-candidate deletion")
assert source != mutated
namespace = dict(C.__dict__)
exec(compile(mutated,"<read-only G03 internal enumerator mutation>","exec"),namespace)
original = C.enumerate_covers3
try:
    C.enumerate_covers3 = namespace["enumerate_covers3"]
    for tolerance in (1e-9, float("nan"), float("inf"), 1e308):
        A, B = box(), box(center=(3,0,0))
        report = G.g0_distance_completeness3(A,B,radius=0,samples=1,tol=0,atol=tolerance)
        rows.append(dict(check="all candidates deleted", atol=str(tolerance),
                         passed=report.passed, samples=report.samples,
                         worst_abs_error=str(report.worst_abs_error),
                         failures=len(report.failures)))
finally:
    C.enumerate_covers3 = original

# Finite large coordinate geometry whose float AABB subtraction overflows.
m = sys.float_info.max
verts = [(-m,-1,-1),(m,-1,-1),(m,1,-1),(-m,1,-1),
         (-m,-1,1),(m,-1,1),(m,1,1),(-m,1,1)]
A = Polyhedron(verts,FACES)
B = Polyhedron([(x,y+3,z) for x,y,z in verts],FACES)
row = dict(check="finite input AABB subtraction overflow", initial_metrics=str(A.metrics()))
try:
    r=G.g0_distance_completeness3(A,B,radius=0,samples=1,tol=0)
    row.update(passed=r.passed, worst_abs_error=str(r.worst_abs_error))
except Exception as e:
    row.update(fail_loud=type(e).__name__,message=str(e))
rows.append(row)

out = Path(__file__).resolve().parent / "g03_scan.json"
out.write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(rows,ensure_ascii=False,indent=2))
