"""Read-only 3D sibling of G6H-01; primary oracle is a Cartesian cell union."""
from dataclasses import asdict
from fractions import Fraction as F
from pathlib import Path
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT/'src'))
from eab.kernel3d.geom3 import Polyhedron, box, polyhedra_overlap
from eab.kernel3d.entrance3 import first_entrance3, shortest_exit3

source = ROOT/'src/eab/kernel3d/entrance3.py'
before = hashlib.sha256(source.read_bytes()).hexdigest()
ring = [(-1,-1),(2,-1),(2,2),(1,2),(1,0),(0,0),(0,2),(-1,2)]
n = len(ring)
vertices = [(float(x),float(y),float(z)) for z in (0,1) for x,y in ring]
faces = [tuple(reversed(range(n))), tuple(range(n,2*n))]
faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
B = Polyhedron(vertices, faces)
A = box((.5,1.,.5),(.5,.5,.25))

# B is a union of three Cartesian boxes. Difference with Cartesian A is
# formed coordinatewise, without any production geometric primitive.
aranges = [(F(0),F(1)),(F(1,2),F(3,2)),(F(1,4),F(3,4))]
branges = [[(-1,2),(-1,0),(0,1)], [(-1,0),(0,2),(0,1)], [(1,2),(0,2),(0,1)]]
cells = [[(F(lo)-aranges[k][1], F(hi)-aranges[k][0]) for k,(lo,hi) in enumerate(b)]
         for b in branges]
assert cells[1][0][1] == cells[2][0][0] == 0
assert cells[1][1:] == cells[2][1:]
assert cells[0][1][1] > cells[1][1][0]
assert cells[0][2] == cells[1][2]
entrance_box = [cells[0][0], (cells[0][1][0],cells[1][1][1]),cells[0][2]]
assert all(lo < 0 < hi for lo,hi in entrance_box)

rows=[]
for direction in ((0,1,0),(1,1,0),(1,0,0)):
    try:
        result=first_entrance3(A,B,(0,0,0),direction,tol=0)
        rows.append(dict(direction=direction, result=asdict(result), error=None))
    except Exception as exc:
        rows.append(dict(direction=direction, result=None, error=f'{type(exc).__name__}: {exc}'))
output=dict(scope='same initial-topology issue as G6H-01, not a normalized-dot construction',
            independent_E_box=entrance_box, x0_topological_interior=True,
            manifold_issues=B.manifold_issues(), body_overlap=polyhedra_overlap(A,B),
            first_entrance_results=rows, shortest_exit=asdict(shortest_exit3(A,B,(0,0,0),tol=0)),
            source_sha_before=before, source_sha_after=hashlib.sha256(source.read_bytes()).hexdigest())
assert output['source_sha_before'] == output['source_sha_after']
text=json.dumps(output,ensure_ascii=False,indent=2,default=str)+'\n'
Path(__file__).with_suffix('.json').write_text(text,encoding='utf-8')
print(text)
