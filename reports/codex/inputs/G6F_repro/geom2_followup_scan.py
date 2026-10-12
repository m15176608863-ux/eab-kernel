from pathlib import Path
from fractions import Fraction as F
import sys,random,math,json
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
from eab.kernel2d import entrance as E,covers as C

def cross(a,b,c):return (F(b[0])-F(a[0]))*(F(c[1])-F(a[1]))-(F(b[1])-F(a[1]))*(F(c[0])-F(a[0]))
def hull(ps):
 ps=sorted(set(map(tuple,ps)));cur=start=ps[0];out=[]
 while True:
  out.append(cur);nxt=next(p for p in ps if p!=cur)
  for p in ps:
   z=cross(cur,nxt,p)
   if z<0 or z==0 and sum((F(p[k])-F(cur[k]))**2 for k in (0,1))>sum((F(nxt[k])-F(cur[k]))**2 for k in (0,1)):nxt=p
  cur=nxt
  if cur==start:return out

def sat(A,B,x=(0,0)):
 A=[(F(a[0])+F(x[0]),F(a[1])+F(x[1])) for a in A];B=[tuple(map(F,b)) for b in B];touch=False
 for P,Q in ((A,B),(B,A)):
  for j,p in enumerate(P):
   q=P[(j+1)%len(P)];n=(q[1]-p[1],p[0]-q[0]);pa=[sum(n[k]*v[k] for k in (0,1)) for v in P];pb=[sum(n[k]*v[k] for k in (0,1)) for v in Q]
   gap=max(min(pa)-max(pb),min(pb)-max(pa))
   if gap>0:return -1
   if gap==0:touch=True
 return 0 if touch else 1

def d2segment(x,a,b):
 u=[F(b[k])-F(a[k]) for k in (0,1)];v=[F(x[k])-F(a[k]) for k in (0,1)]
 uu=sum(z*z for z in u);t=max(F(0),min(F(1),sum(u[k]*v[k] for k in (0,1))/uu))
 return sum((v[k]-t*u[k])**2 for k in (0,1))
def selected2(A,B,x,lab):
 kind,i,j=lab
 P,Q,k,l=(A,B,i,j) if kind=='VE' else (B,A,j,i)
 p=[F(P[k][q])+(F(x[q]) if kind=='VE' else -F(x[q])) for q in (0,1)];a,b=Q[l],Q[(l+1)%len(Q)]
 return d2segment(p,a,b)

def general_state(A,B,x=(0,0)):
 # fixed fan on star-shaped L polygons, independent of production ear clipping
 ans=-1
 for i in range(1,len(A)-1):
  for j in range(1,len(B)-1):
   ans=max(ans,sat([A[0],A[i],A[i+1]],[B[0],B[j],B[j+1]],x))
 return ans

def oracle_ray(A,B,x,d,bound):
 X,D=tuple(map(F,x)),tuple(map(F,d));times={F(0)}
 for P,Q,V,Y in ((A,B,D,X),(B,A,(-D[0],-D[1]),(-X[0],-X[1]))):
  for p in P:
   for j,q in enumerate(Q):
    r=Q[(j+1)%len(Q)];ex,ey=F(r[0])-F(q[0]),F(r[1])-F(q[1]);wx,wy=F(q[0])-F(p[0])-Y[0],F(q[1])-F(p[1])-Y[1]
    den=V[0]*ey-V[1]*ex
    if den:
     t=(wx*ey-wy*ex)/den;s=(wx*V[1]-wy*V[0])/den
     if 0<=t<=F(bound) and 0<=s<=1:times.add(t)
    elif wx*ey-wy*ex==0:
     vv=sum(z*z for z in V)
     for u in (q,r):
      t=sum((F(u[k])-F(p[k])-Y[k])*V[k] for k in (0,1))/vv
      if 0<=t<=F(bound):times.add(t)
 for t in sorted(times):
  if general_state(A,B,(X[0]+t*D[0],X[1]+t*D[1]))>=0:return t
 return None

rng=random.Random(260612062);results={'convex_exit_cases':0,'concave_ray_cases':0,'mismatches':[],'exceptions':[]}
for scale in (1e-9,1.,1e9):
 for off in (0,1e8):
  if scale==1e-9 and off:continue
  for repeat in range(35):
   A=hull([(off+scale*rng.uniform(-2,2),-off+scale*rng.uniform(-2,2)) for _ in range(8)]);B=hull([(off+scale*rng.uniform(-2,2),-off+scale*rng.uniform(-2,2)) for _ in range(8)])
   x=(scale*rng.uniform(-.4,.4),scale*rng.uniform(-.4,.4))
   if sat(A,B,x)!=1:continue
   diff=hull([(F(b[0])-F(a[0]),F(b[1])-F(a[1])) for a in A for b in B])
   truth=min(d2segment(x,p,diff[(j+1)%len(diff)]) for j,p in enumerate(diff))
   got=E.shortest_exit(A,B,x)
   computed=selected2(A,B,x,got.label)
   if computed!=truth:results['mismatches'].append({'type':'convex_exit','A':A,'B':B,'x':x,'got':str(computed),'truth':str(truth),'label':got.label})
   results['convex_exit_cases']+=1
L=[(0,0),(3,0),(3,1),(1,1),(1,3),(0,3)]
for scale in (1e-9,1,1e9):
 for off in (0,1e8):
  if scale==1e-9 and off:continue
  for repeat in range(30):
   theta=rng.uniform(-math.pi,math.pi);co,si=math.cos(theta),math.sin(theta)
   A=[(off+scale*(co*x-si*y),-off+scale*(si*x+co*y)) for x,y in L]
   theta=rng.uniform(-math.pi,math.pi);co,si=math.cos(theta),math.sin(theta)
   B=[(off+scale*(co*x-si*y),-off+scale*(si*x+co*y)) for x,y in L]
   x=(scale*8,scale*rng.uniform(-5,5));d=(-scale,scale*rng.uniform(-1,1));bound=20
   truth=oracle_ray(A,B,x,d,bound)
   try:got=E.first_entrance(A,B,x,d,t_max=bound)
   except Exception as exc:results['exceptions'].append({'type':type(exc).__name__,'message':str(exc),'A':A,'B':B,'x':x,'d':d,'truth':str(truth)});continue
   if got.t_exact!=truth:results['mismatches'].append({'type':'concave_ray','A':A,'B':B,'x':x,'d':d,'got':str(got.t_exact),'truth':str(truth)})
   results['concave_ray_cases']+=1
print(json.dumps(results,ensure_ascii=False,indent=2))
(ROOT/'review/notes/geom2_followup_scan.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf8')
