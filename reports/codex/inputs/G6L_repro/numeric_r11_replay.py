from pathlib import Path
from fractions import Fraction as F
import sys,json,math,hashlib,importlib.util,inspect
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
from eab.kernel2d.geom import orient2d,triangulate
spec=importlib.util.spec_from_file_location('numeric_gate',ROOT/'tools/check_exact_construction.py');gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)
from eab.kernel3d import covers3 as covers
from eab.kernel3d.geom3 import tetra
N=2**53
def truth(a,b,c):
 d=(F(a[0])-F(c[0]))*(F(b[1])-F(c[1]))-(F(a[1])-F(c[1]))*(F(b[0])-F(c[0]));return (d>0)-(d<0)
wrong=[]
for e in (53,54,55,60):
 for ax in range(1,17):
  for bx in range(1,17):
   for ay,by in ((3.,4.),(1.,2.),(7.,11.)):
    p=((2**e+ax,ay),(2**e+bx,by),(float(2**e),0.));got=orient2d(*p);want=truth(*p)
    if got!=want:wrong.append((p,got,want))
P=[(N+2,7.),(N+3,11.),(float(N),0.)]
assert not wrong and triangulate(P)==[(0,1,2)]
source_path=ROOT/'src/eab/kernel3d/covers3.py';before=hashlib.sha256(source_path.read_bytes()).hexdigest();source=source_path.read_text(encoding='utf8');old='return norm_rational(p), noise'
u=math.ulp(0.0);shape=tetra((0.,0.,0.),(1.,-1.,u),(u,1.,-1.),(-1.,u,1.));results=[]
for label,loop in [('tuple','for _ in ():'),('range','for _ in range(0):'),('while','while False:')]:
 body='root = norm_rational\n    '+loop+'\n        root = abs\n    return root(vector_rational(p, allow_underflow=True)), noise'
 mutant=source.replace(old,body);ns=dict(vars(covers));exec(compile(inspect.getsource(covers.cone_intersection_margin).replace(old,body),'<R11 replay>','exec'),ns)
 actual=ns['cone_intersection_margin'](shape,0,shape.reflected(),0)[0];issues=gate.scan_text(mutant,'src/eab/kernel3d/covers3.py')
 assert actual==0 and any(i[2:4]==('cone_intersection_margin','rounded-vector') for i in issues)
 results.append({'label':label,'mutant':repr(actual),'issues':issues})
assert before==hashlib.sha256(source_path.read_bytes()).hexdigest()
print(json.dumps({'R11_mixed_grid':3072,'wrong':len(wrong),'triangulate':triangulate(P),'R11_zero_loops':results,'tracked_source_unchanged':True},ensure_ascii=False,indent=2))
