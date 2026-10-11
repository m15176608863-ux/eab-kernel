import hashlib,json,pathlib,sys,time
sys.path[:0]=[str(pathlib.Path('src').resolve()),str(pathlib.Path('tests').resolve())]
from test_e5a2_surface import l_block
from eab.kernel3d import exact_geom as E
from fractions import Fraction as F
P=l_block();tris=E.triangles(P)
points=[(F(x,7),F(y,7),F(z,7)) for x in range(-1,23,3) for y in range(-1,23,3) for z in (0,3,7)]
t=time.perf_counter();values=[E._point_in_triangles(p,tris) for p in points];elapsed=time.perf_counter()-t
r={'query_count':len(points),'seconds':elapsed,'values':values,'source_sha256':hashlib.sha256(pathlib.Path('src/eab/kernel3d/exact_geom.py').read_bytes()).hexdigest()}
out=pathlib.Path('reports/codex/E5a2_evidence/a1')/('point_query_'+sys.argv[1]+'.json');out.write_text(json.dumps(r,indent=2),encoding='utf-8');print(elapsed)
