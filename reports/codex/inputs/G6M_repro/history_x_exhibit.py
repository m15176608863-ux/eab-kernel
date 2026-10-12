"""Concrete seed-0 field-integrity exhibit for the internally mutated copy."""
from pathlib import Path
import hashlib,os,subprocess,sys,json
ROOT=Path(__file__).resolve().parents[2];folder=ROOT/'review/copies/history_current';p=folder/'src/eab/kernel3d/entrance3.py';raw=p.read_bytes();s=raw.decode('utf-8-sig')
needle='return _restore_sources(Entrance3("entrance", scalar_rational(t), tuple(scalar_rational(_mapped_value) for _mapped_value in exact_x), rep_label,'
change='return _restore_sources(Entrance3("entrance", scalar_rational(t), tuple(scalar_rational(_mapped_value) for _mapped_value in x0), rep_label,'
code='''import sys,random,json
from fractions import Fraction as F
sys.path[:0]=['src','tests']
from eab.kernel3d.geom3 import convex_hull_3d
from eab.kernel3d.entrance3 import first_entrance3
from e5a2_entrance_oracle import convex_ray_interval
rng=random.Random(900)
A=convex_hull_3d([(rng.uniform(-1,1),rng.uniform(-1,1),rng.uniform(-1,1)) for _ in range(8)])
B=convex_hull_3d([(rng.uniform(-1,1),rng.uniform(-1,1),rng.uniform(-1,1)) for _ in range(8)])
start=tuple(rng.uniform(-1,1)+4*c for c in (rng.gauss(0,1),rng.gauss(0,1),rng.gauss(0,1)))
d=tuple(-c/4+.1*rng.gauss(0,1) for c in start)
want=convex_ray_interval(A.verts,B.verts,start,d,8)[0]
got=first_entrance3(A,B,start,d,t_max=8)
expected=tuple(float(F(start[k])+want*F(d[k])) for k in range(3))
print(json.dumps(dict(seed=0,start=start,direction=d,exact_time=str(want),returned_exact_time=str(got.exact_t),expected_rounded_x=expected,returned_x=got.x,x_mismatch=got.x!=expected,kind=got.kind,returned_t=got.t),indent=2))
'''
rows=[]
try:
 for stage in ('baseline','mutant'):
  if stage=='mutant':
   assert s.count(needle)==1;p.write_bytes(s.replace(needle,change).encode('utf-8'))
  r=subprocess.run([sys.executable,'-X','utf8','-c',code],cwd=folder,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),encoding='utf-8',stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  assert r.returncode==0,r.stderr
  v=json.loads(r.stdout);v['stage']=stage;rows.append(v)
 assert not rows[0]['x_mismatch'] and rows[1]['x_mismatch']
 print(json.dumps(rows,ensure_ascii=False,indent=2))
 (ROOT/'review/logs/history_x_exhibit.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
finally:
 p.write_bytes(raw);assert hashlib.sha256(p.read_bytes()).digest()==hashlib.sha256(raw).digest()
