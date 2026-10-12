"""Review-owned Fraction oracle; no eab/test oracle primitives reused.

Polygon truth: independent ear decomposition + rational convex clipping area,
then explicit segment intersection for closed-only contact. This is not a
comparison of the two production predicate paths. 3D truth is transformed
Cartesian products and inverse orthogonal frames, never production SAT.
"""
from pathlib import Path
from fractions import Fraction as F
from decimal import Decimal,localcontext
import random,math,sys,json
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
from eab.kernel2d import geom,exact,covers,g0,entrance
from eab.kernel3d.g03_surface_oracle import separated_distance

def orientation(a,b,c):
    return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
def ring_area(P):
    return sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(P,P[1:]+P[:1]))
def triangulate_independent(P):
    P=list(map(lambda p:tuple(map(F,p)),P))
    if ring_area(P)<0:P.reverse()
    out=[]
    while len(P)>3:
        for i,b in enumerate(P):
            a,c=P[i-1],P[(i+1)%len(P)]
            if orientation(a,b,c)<=0:continue
            if any(all(orientation(u,v,z)>=0 for u,v in ((a,b),(b,c),(c,a))) for k,z in enumerate(P) if k not in {i,(i-1)%len(P),(i+1)%len(P)}):continue
            out.append([a,b,c]);P.pop(i);break
        else:
            k=next(i for i,b in enumerate(P) if orientation(P[i-1],b,P[(i+1)%len(P)])==0)
            P.pop(k)
    if ring_area(P):out.append(P)
    return out
def intersect_clip(P,T):
    for a,b in zip(T,T[1:]+T[:1]):
        new=[]
        if not P:return []
        for p,q in zip(P,P[1:]+P[:1]):
            dp,dq=orientation(a,b,p),orientation(a,b,q)
            if dp>=0:new.append(p)
            if (dp<0<dq) or (dq<0<dp):
                t=dp/(dp-dq);new.append(tuple(p[k]+t*(q[k]-p[k]) for k in (0,1)))
        P=new
    return P
def onseg(p,a,b):return orientation(a,b,p)==0 and all(min(a[k],b[k])<=p[k]<=max(a[k],b[k]) for k in (0,1))
def boundary_hit(a,b,c,d):
    z=[orientation(a,b,c),orientation(a,b,d),orientation(c,d,a),orientation(c,d,b)]
    return z[0]*z[1]<0 and z[2]*z[3]<0 or any((not z[i]) and onseg(p,u,v) for i,p,u,v in ((0,c,a,b),(1,d,a,b),(2,a,c,d),(3,b,c,d)))
def classify(A,B):
    A=[tuple(map(F,p)) for p in A];B=[tuple(map(F,p)) for p in B]
    for T in triangulate_independent(A):
        for U in triangulate_independent(B):
            P=intersect_clip(T,U)
            if len(P)>=3 and abs(ring_area(P))>0:return 1
    return 0 if any(boundary_hit(a,b,c,d) for a,b in zip(A,A[1:]+A[:1]) for c,d in zip(B,B[1:]+B[:1])) else -1
def parity_inside(p,P):
    p=tuple(map(F,p));P=[tuple(map(F,q)) for q in P];inside=False
    for a,b in zip(P,P[1:]+P[:1]):
        if onseg(p,a,b):return 0
        if (a[1]>p[1])!=(b[1]>p[1]):
            x=a[0]+(p[1]-a[1])*(b[0]-a[0])/(b[1]-a[1])
            if p[0]<x:inside=not inside
    return 1 if inside else -1
def sqrt_exact(q):
    with localcontext() as c:
        c.prec=150
        return float((Decimal(q.numerator)/Decimal(q.denominator)).sqrt())

rng=random.Random(72211)
S=[(0,0),(1,0),(1,1),(0,1)]
L=[(0,0),(2,0),(2,1),(1,1),(1,2),(0,2)]
U=[(0,0),(3,0),(3,3),(2,3),(2,1),(1,1),(1,3),(0,3)]
FLAT=[(0,0),(1,0),(2,0),(2,1),(0,1)]
raw=[S,L,U,FLAT]
directions=[(1,0),(1,1),(0,1),(-1,1),(-1,0),(-1,-1),(0,-1),(1,-1)]
for i in range(8):raw.append([(F(rng.randint(1,8))*x,F(rng.randint(1,8))*y) for x,y in directions])
# Fully rational rotation, engineering translation, unit scaling; both scalar
# ranges and concave/shallow/boundary cases are in the Cartesian grid.
rotations=[(F(1),F(0)),(F(3,5),F(4,5)),(F(1)-F(2,10**30),F(1,10**15))]
count=inside_count=0;states={-1:0,0:0,1:0}
for i in range(180):
    P,Q=raw[i%len(raw)],raw[(i*5+1)%len(raw)]
    scale=[F(1,2**600),F(1,10**9),F(1),F(10**9),F(2**600)][i%5]
    shift=[F(0),F(10**3),F(10**5),F(10**6),F(10**8)][(i//5)%5]
    c,s=rotations[(i//25)%3]
    displacement=(F(rng.randrange(-4,5),2),F(rng.randrange(-4,5),2))
    def move(p):return (shift+scale*(c*F(p[0])-s*F(p[1])),-3*shift+scale*(s*F(p[0])+c*F(p[1])))
    A=[move((F(x)+displacement[0],F(y)+displacement[1])) for x,y in P]
    B=[move(p) for p in Q]
    truth=classify(A,B)
    got=[geom.polygons_overlap(A,B),exact.polygons_overlap_exact(A,B),covers.membership_convex(A,B,(0,0)),g0.independent.overlap(A,B)]
    assert got==[truth]*4,{'i':i,'got':got,'truth':truth,'A':A,'B':B}
    states[truth]+=1;count+=1
    assert parity_inside(geom.interior_point(A),A)==1
    inside_count+=1

# Random binary64 nonconvex rings separately verify supplied-data answers;
# no ideal-motion exemption is invoked.
for i in range(120):
    P,Q=raw[i%len(raw)],raw[(i*7+3)%len(raw)]
    theta=rng.uniform(-math.pi,math.pi);c,s=math.cos(theta),math.sin(theta)
    scale=[1e-9,1,1e8][i%3];shift=[0,1e3,1e6,1e8][i%4]
    dx,dy=rng.uniform(-3,3),rng.uniform(-3,3)
    def move(p):return (shift+scale*(c*float(p[0])-s*float(p[1])),-shift+scale*(s*float(p[0])+c*float(p[1])))
    A=[move((float(x)+dx,float(y)+dy)) for x,y in P];B=[move(p) for p in Q]
    # Skip only representationally collapsed rings, not geometric boundary.
    if any(A[j]==A[j-1] for j in range(len(A))) or any(B[j]==B[j-1] for j in range(len(B))):continue
    truth=classify(A,B)
    got=[geom.polygons_overlap(A,B),exact.polygons_overlap_exact(A,B),covers.membership_convex(A,B,(0,0)),g0.independent.overlap(A,B)]
    assert got==[truth]*4,{'i':i,'got':got,'truth':truth}
    states[truth]+=1;count+=1

# 3D G0 surface oracle: independently constructed interval products (including
# contact, shallow overlap, separation, containment, and disconnected shells),
# rigid rational rotations and engineering translations.
faces=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
corners=[(x,y,z) for z in (0,1) for x,y in S]
three_count=0
for scale in [F(1,2**600),F(1,10**9),F(1),F(2**600)]:
  for offset in [F(0),F(10**3),F(10**6),F(10**8)]:
    for dx in [F(1,4),F(1)-F(1,2**50),F(1),F(1)+F(1,2**50),F(3,2),F(2)]:
      def move3(p):
        x,y,z=map(F,p)
        return (offset+scale*(F(3,5)*x-F(4,5)*y),-3*offset+scale*(F(4,5)*x+F(3,5)*y),2*offset+scale*z)
      av=[move3((x+dx,y,z)) for x,y,z in corners];bv=[move3(p) for p in corners]
      want=None if dx<=1 else float(scale*(dx-1))
      got=separated_distance(av,faces,bv,faces)
      assert got==want,{'scale':str(scale),'offset':str(offset),'dx':str(dx),'want':want,'got':got}
      three_count+=1
out={'polygon_comparisons':count,'polygon_states':states,'exact_interior_points':inside_count,'surface_product_comparisons':three_count,'result':'PASS',
     'oracle_independence':'review-owned Fraction ear+clipping area/parity; Cartesian interval products; no production/test geometry primitive called for truth'}
print(json.dumps(out,indent=2))
