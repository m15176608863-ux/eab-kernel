"""Read-only independent cross-check of kinetic roots and certificate inputs."""
from pathlib import Path
from fractions import Fraction as F
import json
import sys
import time

ROOT = Path(__file__).resolve().parents[4]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'tests')]
from eab.kernel3d.geom3 import Polyhedron, box, tetra
from eab.kernel3d.interlock import escape_height_covers
from e5b_wall_oracle import earliest_star_escape
from e5a2_surface_oracle import star_relation, _ring_triangles, _times, _minus, _scalar


def shifted(P, offset):
    return Polyhedron([tuple(F(p[k])+F(offset[k]) for k in range(3)) for p in P.verts], P.faces)


def independent_core(P, w):
    vertices = [tuple(map(F, p)) for p in P.verts]
    c = tuple(sum(p[k] for p in vertices)/len(vertices) for k in range(3))
    triangles = [tri for face in P.faces for tri in _ring_triangles(vertices, face)]
    if not all(_scalar(_times(_minus(b,a),_minus(d,a)),_minus(c,a)) < 0 for a,b,d in triangles):
        return None
    radius = max(sum(abs(p[k]-c[k]) for k in range(3)) for p in vertices)
    alpha = min(w/radius, F(1,2))
    return Polyhedron([tuple(c[k]+(1-alpha)*(p[k]-c[k]) for k in range(3)) for p in vertices], P.faces)


start = time.perf_counter()
rows = []
matrix = ((F(1), F(1,4), F(1,7)), (-F(1,4), F(1), F(1,11)), (F(1,9), -F(1,13), F(1)))
for scale in (F(1,1000), F(1), F(1000)):
    for translation in (F(0), F(100000)):
        def moved(P):
            return Polyhedron([tuple(translation*(k+1)+scale*sum(matrix[k][j]*F(p[j]) for j in range(3))
                                     for k in range(3)) for p in P.verts], P.faces)
        A = moved(tetra((0,0,0), (1,0,0), (0,1,0), (0,0,1)))
        B = moved(box((F(1,4),F(1,4),F(1,4)), (F(1,2),)*3))
        offset = (scale*F(1,20), -scale*F(1,30), scale*F(1,17))
        sol = escape_height_covers(A, B, offset)
        root = earliest_star_escape(A, B, offset)
        assert sol.exact_height == root
        assert sol.exact_offset == (offset[0], offset[1], offset[2]+root)
        assert star_relation(shifted(A, sol.exact_offset), B) <= 0
        left = F(0)
        for lo, hi, mid, state in sol.interval_certificate:
            assert lo == left and lo < hi and mid == (lo+hi)/2 and state == 1
            assert star_relation(shifted(A, (offset[0], offset[1], offset[2]+mid)), B) == 1
            left = hi
        assert left == root
        rows.append(dict(scale=str(scale), translation=str(translation), root=str(root),
                         verified_prior_intervals=len(sol.interval_certificate), same_affine_inputs=True))

# Independent finite-window model construction; no production star-core,
# translation, surface event or contact_models helper supplies the oracle.
A = box((0,0,F(13,10)), (F(1,2),)*3)
B = box((0,0,F(1,2)), (F(1,2),)*3)
w = F(1,100)
models = [('exact',A,B)]
for axis in range(3):
    for sign in (-1,1):
        models.append((f'shift_{axis}_{sign}',shifted(A,tuple(w*sign if k == axis else 0 for k in range(3))),B))
for name,P,Q in [('core_A',A,B),('core_B',B,A)]:
    core = independent_core(P,w)
    if core is not None:
        models.append((name,core,Q) if name == 'core_A' else (name,Q,core))
roots = {name:earliest_star_escape(a,b) for name,a,b in models}
sol = escape_height_covers(A,B,(0,0,0),contact_window=w)
assert sol.exact_height == min(roots.values()) == F(19,100)
result = dict(default_cases=rows, window_roots={k:str(v) for k,v in roots.items()},
              window_winner_root=str(sol.exact_height), elapsed_seconds=time.perf_counter()-start,
              status='PASS')
Path(__file__).with_suffix('.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))
