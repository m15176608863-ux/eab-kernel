"""G6N nonconvex distance and 2D entrance topology reference from box unions.
Oracle uses interval products, open/closed cells and Decimal only for final sqrt.
"""
import sys,json,random,math,time
from fractions import Fraction as F
from decimal import Decimal, localcontext
from itertools import product
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT/'review/repro'))
from geometry_union import build,shift_body,overlap
from eab.margin import body_distance,inflated_membership
from eab.kernel2d.covers import membership_convex
from eab.kernel2d.entrance import first_entrance

def ref_distance_squared(aa,bb,offset=(0,0,0)):
    return min(sum(max(bl-ah-t,al+t-bh,0)**2 for (al,ah),(bl,bh),t in zip(a,b,offset)) for a in aa for b in bb)
def sqrt_ref(q):
    with localcontext() as c:c.prec=150;return float((Decimal(q.numerator)/Decimal(q.denominator)).sqrt())
def rot2(p):return (F(3,5)*p[0]-F(4,5)*p[1],F(4,5)*p[0]+F(3,5)*p[1])
def state_union2(cells,x):
    present=[b for b in cells if all(lo<=v<=hi for (lo,hi),v in zip(b,x))]
    if not present:return -1
    for signs in product((-1,1),repeat=2):
      if not any(all((lo<v if sign<0 else v<hi) for (lo,hi),v,sign in zip(b,x,signs)) for b in present):return 0
    return 1

def first_union2(cells,x,d,max_t):
    if state_union2(cells,x)==1:return ('exit',F(0))
    hits=[]
    for cell in cells:
      low=F(0);high=max_t
      for (a,b),v,w in zip(cell,x,d):
        if not w:
          if not a<=v<=b:break
        else:
          t,u=(a-v)/w,(b-v)/w;low=max(low,min(t,u));high=min(high,max(t,u))
      else:
        if low<=high:hits.append(low)
    return ('entrance',min(hits)) if hits else ('none',None)

def run():
    rng=random.Random(1403);stats={};fail=[];errors=[];start=time.time()
    def check(k,a,e,case):
      stats[k]=stats.get(k,0)+1
      if a!=e:fail.append({'kind':k,'actual':str(a),'expected':str(e),'case':str(case)});print('FAIL',fail[-1],flush=True)
    shapes={
     'L':([(0,0),(2,0),(2,1),(1,1),(1,2),(0,2)],[(0,2,0,1),(0,1,1,2)]),
     'U':([(0,0),(3,0),(3,3),(2,3),(2,1),(1,1),(1,3),(0,3)],[(0,3,0,1),(0,1,1,3),(2,3,1,3)]),
     'C':([(0,0),(3,0),(3,1),(1,1),(1,2),(3,2),(3,3),(0,3)],[(0,3,0,1),(0,1,1,2),(0,3,2,3)]),
     'cube':([(0,0),(1,0),(1,1),(0,1)],[(0,1,0,1)])}
    for i in range(180):
      na,nb=rng.choice(list(shapes)),rng.choice(list(shapes));scale=rng.choice([F(1),F(1,10**9),F(10**8)]);T=rng.choice([(F(0),F(0)),(F(10**8),F(-10**8))]);rotate=i%2==0
      def model(name):
        ring,rect=shapes[name]
        points=[(F(a)*scale+T[0],F(b)*scale+T[1]) for a,b in ring]
        cells=[((F(a)*scale+T[0],F(b)*scale+T[0]),(F(c)*scale+T[1],F(d)*scale+T[1])) for a,b,c,d in rect]
        return [rot2(p) for p in points] if rotate else points,cells
      a,aa=model(na);b,bb=model(nb)
      cells=[tuple((bl-ah,bh-al) for (al,ah),(bl,bh) in zip(A,B)) for A in aa for B in bb]
      for j in range(6):
        x=tuple(F(rng.randint(-12,12),4)*scale for _ in range(2));rx=rot2(x) if rotate else x
        check('nonconvex_E2',membership_convex(a,b,rx),state_union2(cells,x),(i,j,na,nb,scale,x,rotate))
      if i<60:
        x=tuple(F(rng.randint(-12,12),4)*scale for _ in range(2));d=(scale,F(1,3)*scale);rx,rd=(rot2(x),rot2(d)) if rotate else (x,d)
        try:
          out=first_entrance(a,b,rx,rd,t_max=F(10));actual=(out.kind,out.t_exact if out.kind!='none' else None)
          check('nonconvex_first2',actual,first_union2(cells,x,d,F(10)),(i,na,nb,scale,x,rotate))
        except Exception as e:errors.append({'kind':'first2','case':i,'error':repr(e)})
    print('2D_DONE',stats,'errors',len(errors),flush=True)
    voxels={
       'cube':[(0,0,0)],
       'L':[(0,0,0),(1,0,0),(0,1,0)],
       'U':[(0,0,0),(1,0,0),(2,0,0),(0,1,0),(2,1,0),(0,2,0),(2,2,0)],
       'ring':[(x,y,0) for x in range(3) for y in range(3) if (x,y)!=(1,1)]}
    for i in range(70):
      na,nb=rng.choice(list(voxels)),rng.choice(list(voxels));scale=rng.choice([F(1),F(1,10**9),F(10**8)]);trans=rng.choice([(0,0,0),(F(10**8),F(-10**8),F(10**8))]);rotate=i%2==0
      a,aa=build(voxels[na],scale,trans,rotate);b,bb=build(voxels[nb],scale,trans,rotate)
      offset=tuple(F(rng.randint(-12,12),4)*scale for _ in range(3));ro=(*rot2(offset[:2]),offset[2]) if rotate else offset
      actual_body=shift_body(a,ro);q=ref_distance_squared(aa,bb,offset);physical=overlap(aa,bb,offset)
      try:
        out=body_distance(actual_body,b)
        check('distance3',out[0],0. if physical>=0 else sqrt_ref(q),(i,na,nb,scale,offset,rotate))
        for delta in [F(0),scale/2,scale,2*scale]:
          expected=1 if physical==1 else (1 if q<delta*delta else 0 if q==delta*delta else -1)
          check('inflated3',inflated_membership(actual_body,b,delta=delta),expected,(i,na,nb,scale,offset,rotate,delta))
      except Exception as e:errors.append({'kind':'margin3','case':i,'error':repr(e)})
    result={'stats':stats,'failures':fail,'errors':errors,'seconds':round(time.time()-start,3)}
    (ROOT/'review/evidence/geometry_distances_results.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2),flush=True)
if __name__=='__main__':run()
