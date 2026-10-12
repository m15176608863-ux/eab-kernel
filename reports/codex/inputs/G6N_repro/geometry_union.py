"""WO-G6N independent Fraction audit: orthogonal union solids.
No production geometry helper is used by oracle, model builder or motion reference.
Production functions are called only as the system under test.
"""
import sys, math, random, json, time
from fractions import Fraction as Q
from pathlib import Path
from itertools import product
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
from eab.kernel3d.geom3 import Polyhedron, polyhedra_overlap, point_in_polyhedron, exact_convex_overlap
from eab.kernel3d.entrance_topology import entrance_membership3
from eab.kernel3d.interlock import escape_height_covers
from eab.kernel3d.entrance3 import first_entrance3
from eab.margin import body_distance, inflated_membership

def build(cells, scale=Q(1), shift=(0,0,0), rotate=False):
    occupied=set(cells); faces=[]; vertices=[]; index={}
    def transformed(p):
        p=tuple(Q(x)*scale+Q(t) for x,t in zip(p,shift))
        if rotate:
            x,y,z=p; p=(Q(3,5)*x-Q(4,5)*y,Q(4,5)*x+Q(3,5)*y,z)
        return p
    def put(p):
        if p not in index: index[p]=len(vertices);vertices.append(transformed(p))
        return index[p]
    for x,y,z in sorted(occupied):
        for neighbour, ring in [
            ((x-1,y,z),[(x,y,z),(x,y,z+1),(x,y+1,z+1),(x,y+1,z)]),
            ((x+1,y,z),[(x+1,y,z),(x+1,y+1,z),(x+1,y+1,z+1),(x+1,y,z+1)]),
            ((x,y-1,z),[(x,y,z),(x+1,y,z),(x+1,y,z+1),(x,y,z+1)]),
            ((x,y+1,z),[(x,y+1,z),(x,y+1,z+1),(x+1,y+1,z+1),(x+1,y+1,z)]),
            ((x,y,z-1),[(x,y,z),(x,y+1,z),(x+1,y+1,z),(x+1,y,z)]),
            ((x,y,z+1),[(x,y,z+1),(x+1,y,z+1),(x+1,y+1,z+1),(x,y+1,z+1)])]:
            if neighbour not in occupied: faces.append(tuple(put(p) for p in ring))
    boxes=[tuple((Q(a)*scale+Q(t),Q(a+1)*scale+Q(t)) for a,t in zip(cell,shift)) for cell in sorted(occupied)]
    return Polyhedron(vertices,faces), boxes

def overlap(aa,bb,offset=(0,0,0)):
    touch=False
    for a in aa:
        for b in bb:
            spans=[min(ah+Q(t),bh)-max(al+Q(t),bl) for (al,ah),(bl,bh),t in zip(a,b,offset)]
            if all(w>0 for w in spans):return 1
            if all(w>=0 for w in spans):touch=True
    return 0 if touch else -1

def point_union(p,boxes):
    present=[b for b in boxes if all(lo<=x<=hi for (lo,hi),x in zip(b,p))]
    if not present:return -1
    for signs in product((-1,1),repeat=3):
        if not any(all((lo<x if sign<0 else x<hi) for (lo,hi),x,sign in zip(b,p,signs)) for b in present):return 0
    return 1

def estate(aa,bb,offset=(0,0,0)):
    cells=[tuple((bl-ah,bh-al) for (al,ah),(bl,bh) in zip(a,b)) for a in aa for b in bb]
    return point_union(tuple(Q(x) for x in offset),cells)

def shift_body(p,delta):
    return Polyhedron([tuple(Q(x)+Q(d) for x,d in zip(v,delta)) for v in p.verts],list(p.faces))

def exact_escape(aa,bb,offset):
    forbidden=[]
    for a in aa:
        for b in bb:
            if all(min(a[k][1]+offset[k],b[k][1])>max(a[k][0]+offset[k],b[k][0]) for k in (0,1)):
                forbidden.append((b[2][0]-a[2][1]-offset[2],b[2][1]-a[2][0]-offset[2]))
    def penetrating(t):return any(lo<t<hi for lo,hi in forbidden)
    if not penetrating(Q(0)):return Q(0)
    return next(t for t in sorted({hi for lo,hi in forbidden if hi>0}) if not penetrating(t))

def exact_first(aa,bb,offset,direction,tmax):
    if estate(aa,bb,offset)==1:return 'exit',Q(0)
    times=[]
    for a in aa:
        for b in bb:
            low=Q(0);high=Q(tmax)
            for (al,ah),(bl,bh),x,v in zip(a,b,offset,direction):
                left,right=bl-ah-x,bh-al-x
                if v==0:
                    if not left<=0<=right:break
                else:
                    z,w=left/v,right/v
                    low=max(low,min(z,w));high=min(high,max(z,w))
            else:
                if low<=high:times.append(low)
    return ('entrance',min(times)) if times else ('none',None)

def run():
    start=time.time(); stats={}; failures=[];errors=[]
    def check(kind,case,actual,expected):
        stats[kind]=stats.get(kind,0)+1
        if actual!=expected:failures.append({'kind':kind,'case':case,'actual':str(actual),'expected':str(expected)});print('MISMATCH',failures[-1],flush=True)
    shapes={
      'cube':[(0,0,0)],
      'L':[(0,0,0),(1,0,0),(0,1,0)],
      'U':[(0,0,0),(1,0,0),(2,0,0),(0,1,0),(2,1,0),(0,2,0),(2,2,0)],
      'ring':[(x,y,0) for x in range(3) for y in range(3) if (x,y)!=(1,1)],
      'cavity':[(x,y,z) for x,y,z in product(range(3),repeat=3) if (x,y,z)!=(1,1,1)],
      'step':[(x,y,z) for x,y,z in product(range(2),repeat=3) if z==0 or x==0],
    }
    probes=[(Q(-1),Q(0),Q(0)),(Q(0),Q(0),Q(0)),(Q(1),Q(0),Q(0)),(Q(1,2),Q(1,2),Q(1,2)),(Q(1),Q(1),Q(1)),(Q(3),Q(3),Q(3)),(Q(1,3),Q(2,3),Q(1,5))]
    for scale,trans,rot in [(Q(1),(0,0,0),False),(Q(1,10**9),(10**8,-10**8,10**8),True),(Q(10**8),(0,0,0),True)]:
      for name,cells in shapes.items():
        a,aa=build(cells,scale,trans,rot)
        for local in probes:
          p=tuple(local[k]*scale+trans[k] for k in range(3))
          if rot:x,y,z=p;p=(Q(3,5)*x-Q(4,5)*y,Q(4,5)*x+Q(3,5)*y,z)
          check('point',f'{name}/{scale}/{rot}/{local}',point_in_polyhedron(p,a),point_union(tuple(local[k]*scale+trans[k] for k in range(3)),aa))
    print('POINT_DONE',stats,flush=True)
    rng=random.Random(1401)
    for i in range(95):
      na,nb=rng.choice(list(shapes)),rng.choice(list(shapes))
      # Cavities are expensive; preserve bounded number of them.
      if 'cavity' in (na,nb) and i%9: nb='cube';na='cavity' if i%10==0 else 'L'
      scale=rng.choice([Q(1),Q(1,10**9),Q(10**8)])
      trans=rng.choice([(0,0,0),(Q(10**8),Q(-10**8),Q(10**8))]); rot=i%2==0
      offset=tuple(Q(rng.randint(-8,8),4)*scale for _ in range(3))
      a,aa=build(shapes[na],scale,trans,rot);b,bb=build(shapes[nb],scale,trans,rot)
      roffset=offset
      if rot:x,y,z=offset;roffset=(Q(3,5)*x-Q(4,5)*y,Q(4,5)*x+Q(3,5)*y,z)
      at=shift_body(a,roffset)
      case=f'{i}/{na}/{nb}/s={scale}/x={offset}/rot={rot}'
      check('overlap',case,polyhedra_overlap(at,b),overlap(aa,bb,offset))
      if i<25:check('E_topology',case,entrance_membership3(at,b),estate(aa,bb,offset))
      if i<30:
        try:
          actual=escape_height_covers(a,b,roffset).exact_height
          check('escape',case,actual,exact_escape(aa,bb,offset))
        except Exception as e:errors.append({'kind':'escape','case':case,'error':repr(e)})
      if i<20:
        d=(Q(1)*scale,Q(1,3)*scale,Q(1,5)*scale);rd=d
        if rot:x,y,z=d;rd=(Q(3,5)*x-Q(4,5)*y,Q(4,5)*x+Q(3,5)*y,z)
        try:
          actual=first_entrance3(a,b,roffset,rd,t_max=Q(10),tol=0)
          expected=exact_first(aa,bb,offset,d,Q(10))
          check('first',case,(actual.kind,actual.exact_t if actual.kind!='none' else None),expected)
        except Exception as e:errors.append({'kind':'first','case':case,'error':repr(e)})
      if i%10==0:print('PROGRESS',i,stats,'errors',len(errors),flush=True)
    result={'head':'878d4f0','stats':stats,'failures':failures,'errors':errors,'seconds':round(time.time()-start,3)}
    (ROOT/'review/evidence/geometry_union_results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2),flush=True)
if __name__=='__main__':run()
