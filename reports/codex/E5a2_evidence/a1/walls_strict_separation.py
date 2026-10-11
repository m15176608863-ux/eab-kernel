"""Independent strict disjointness certificate for the seven non-minimal wall returns.
Uses integer SAT on all closed triangle pairs, then Fraction parity rays to rule
out containment. Applicable to these connected closed boundaries; no hull,
production primitives, star-shaped hypothesis or production overlap call.
"""
import importlib.util,json,math,time
from fractions import Fraction as F
from pathlib import Path
spec=importlib.util.spec_from_file_location('WD',Path(__file__).with_name('walls_diagnostic.py'));D=importlib.util.module_from_spec(spec);spec.loader.exec_module(D)
def triangle_separator(a,b):
 ae=[D.sub(a[(i+1)%3],a[i]) for i in range(3)];be=[D.sub(b[(i+1)%3],b[i]) for i in range(3)]
 an,bn=D.cross(ae[0],ae[1]),D.cross(be[0],be[1])
 axes=[an,bn]+[D.cross(u,v) for u in ae for v in be]+[D.cross(an,u) for u in ae]+[D.cross(bn,v) for v in be]
 for n in axes:
  if not any(n):continue
  common=math.gcd(*n);n=tuple(x//common for x in n)
  av=[D.dot(n,p) for p in a];bv=[D.dot(n,p) for p in b]
  gap=max(min(av)-max(bv),min(bv)-max(av))
  if gap>0:return {'axis':list(n),'positive_gap':gap}
 return None

def certify(A,B):
 aa,bb=D.triangles(A),D.triangles(B);origin=aa[0][0]
 denominator=math.lcm(*(x.denominator for tri in aa+bb for p in tri for x in p))
 aaa,bbb=([tuple(tuple(int((p[i]-origin[i])*denominator) for i in range(3)) for p in tri) for tri in seq]for seq in(aa,bb))
 seps=[]
 for i,a in enumerate(aaa):
  for j,b in enumerate(bbb):
   sep=triangle_separator(a,b)
   assert sep is not None, ('no strict separating plane for closed triangle pair',i,j)
   seps.append({'a':i,'b':j,**sep})
 assert not D.inside(aa[0][0],bb),'A contained in B'
 assert not D.inside(bb[0][0],aa),'B contained in A'
 return {'origin':[str(x) for x in origin],'denominator':denominator,'triangle_pairs':len(seps),'a_vertex0_outside_b':True,'b_vertex0_outside_a':True,'separators':seps}

t0=time.perf_counter();rows=[]
for row in json.loads(Path(__file__).with_name('walls_diagnostic.json').read_text())['rows']:
 if row.get('delta',0)<=1e-6:continue
 r=D.random.Random(row['seed']);A,L=D.W._place(D.W._key(),.7,row['t'],r,row['ulps']),D.W._place(D.W._prism_xz(D.W.U_PROF,-1.,1.),.7,row['t'],r,row['ulps'])
 h=(row['height']+row['brute'])/2
 cert=certify(A.translated((0.,0.,h)),L)
 out={k:row[k] for k in ['t','ulps','seed','height','brute']};out.update(smaller_strictly_separating_height=h,certificate=cert);rows.append(out)
 print(json.dumps({k:v for k,v in out.items() if k!='certificate'}),flush=True)
Path(__file__).with_name('walls_strict_separation.json').write_text(json.dumps({'elapsed':time.perf_counter()-t0,'rows':rows},indent=2),encoding='utf8')
