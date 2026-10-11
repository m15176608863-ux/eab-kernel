"""Readonly wall diagnostic; independent Fraction ray witnesses, no production geometry helpers."""
import json,random,sys,time
from fractions import Fraction as F
from pathlib import Path
sys.path[:0]=['tests','tools','src']
import test_interlock_walls as W
from e5a2_surface_oracle import _ring_triangles

def sub(a,b):return tuple(x-y for x,y in zip(a,b))
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def cross(a,b):return a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]
def triangles(P):
 v=[tuple(map(F,p)) for p in P.verts]
 return [t for f in P.faces for t in _ring_triangles(v,f)]
def inside(p,tris):
 for k in range(1,100):
  d=(F(1),F(k),F(k*k+1));hits=0;bad=False
  for a,b,c in tris:
   e1,e2,w=sub(b,a),sub(c,a),sub(p,a);h=cross(d,e2);det=dot(e1,h)
   if not det: continue
   q=cross(w,e1);u,v,t=dot(w,h)/det,dot(d,q)/det,dot(e2,q)/det
   if t<0 or min(u,v)<0 or u+v>1:continue
   if t==0:return False
   if min(u,v)==0 or u+v==1:bad=True;break
   hits+=1
  if not bad:return hits%2==1
 raise AssertionError('independent ray family exhausted')
def witness(A,B):
 aa,bb=triangles(A),triangles(B)
 for P in (A,B):
  v=[tuple(map(F,p)) for p in P.verts]
  c=tuple(sum(p[i] for p in v)/len(v) for i in range(3))
  seeds=v+[tuple(sum(p[i] for p in t)/3 for i in range(3)) for t in (aa if P is A else bb)]
  for p in seeds:
   q=tuple(p[i]+(c[i]-p[i])/2**80 for i in range(3))
   if inside(q,aa) and inside(q,bb):return [str(x) for x in q]
 return None

def main():
 rows=[];t0=time.perf_counter()
 for t,u in [(1e5,4),(1e4,1),(1e3,4),(0.,0)]:
  for seed in range(20):
   r=random.Random(seed);A,L=W._place(W._key(),.7,t,r,u),W._place(W._prism_xz(W.U_PROF,-1.,1.),.7,t,r,u)
   row={'t':t,'ulps':u,'seed':seed}
   try:
    sol=W.escape_height_covers(A,L,(0.,0.,0.));row.update(height=sol.height,label=sol.cover_label)
    brute=W.escape_height_brute(A,L,(0.,0.,0.),hi=2.);row['brute']=brute;row['delta']=sol.height-brute
   except Exception as e:row['error']=repr(e)
   if seed==0 or row.get('delta',0)>1e-6:
    row['point_inside_both_at_0200001']=witness(A.translated((0.,0.,.200001)),L)
    if 'height'in row:row['point_inside_both_before_return']=witness(A.translated((0.,0.,row['height']-1e-6)),L)
   rows.append(row);print(json.dumps(row),flush=True)
   Path('reports/codex/E5a2_evidence/a1/walls_diagnostic.json').write_text(json.dumps({'elapsed':time.perf_counter()-t0,'rows':rows},indent=2),encoding='utf8')
if __name__=='__main__':main()
