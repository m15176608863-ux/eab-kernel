"""Read-only independently verify candidate-plane step certificates and box-union states."""
from pathlib import Path
from fractions import Fraction as F
import hashlib,json,sys,time
ROOT=Path(__file__).resolve().parents[4];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests')]
from eab.kernel3d import entrance_topology as tested
from eab.kernel3d.geom3 import Polyhedron,box
from test_r8fix_initial_state3 import _tight_pair,_extrude
OUT=Path(__file__).resolve().parent

def minus(a,b):return tuple(x-y for x,y in zip(a,b))
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def ring_model(P):
    v=tuple(tuple(F(x) for x in p) for p in P.verts);planes=[];edges=set()
    for face in P.faces:
        p=[v[i] for i in face];n=(F(0),)*3
        for a,b in zip(p,p[1:]+p[:1]):n=tuple(x+y for x,y in zip(n,cross(a,b)))
        assert any(n) and all(dot(n,minus(q,p[0]))==0 for q in p),'audit uses exact planar source rings'
        planes.append((n,p[0]))
        edges.update(tuple(sorted((v[i],v[j]))) for i,j in zip(face,face[1:]+face[:1]))
    return v,planes,edges

def raw_config_planes(A,B):
    av,ap,ae=ring_model(A);bv,bp,be=ring_model(B);out=[]
    for n,b in bp:
        out.extend((n,dot(n,minus(a,b))) for a in av)
    for n,a in ap:
        out.extend((n,dot(n,minus(a,b))) for b in bv)
    for a,aa in ae:
        for b,bb in be:
            n=cross(minus(aa,a),minus(bb,b))
            if any(n):out.append((n,dot(n,minus(a,b))))
    return out

def cube_union_state(cells,p):
    if any(all(lo<p[i]<hi for i,(lo,hi) in enumerate(cell)) for cell in cells):return 1
    if any(all(lo<=p[i]<=hi for i,(lo,hi) in enumerate(cell)) for cell in cells):return 0
    return -1

tight=[((-2,2),(F(-5,2),F(3,2)),(F(-3,4),F(3,4)))]
lshape=[((F(-3,2),2),(F(-3,2),0),(F(-3,4),F(3,4))),
        ((F(-3,2),0),(F(-3,2),2),(F(-3,4),F(3,4)))]
cases=[('tight_seam',*_tight_pair(),tight,0)]
a=box((1.25,1.25,.5),(.25,.25,.25));b=_extrude([(0,0),(3,0),(3,1),(1,1),(1,3),(0,3)])
for shear in (0,2**30):
    def skew(P):return Polyhedron([(F(p[0])+shear*F(p[1])+shear**2*F(p[2]),F(p[1])+shear*F(p[2]),F(p[2])) for p in P.verts],list(P.faces))
    cases.append(('l_corner_shear_'+str(shear),skew(a),skew(b),lshape,shear))
rows=[];source=Path(tested.__file__);before=hashlib.sha256(source.read_bytes()).hexdigest()
for name,A,B,cells,shear in cases:
    start=time.perf_counter();central,limits=tested._configuration_planes(A,B);raw=raw_config_planes(A,B)
    signs=[];checked=0
    for d in tested._chamber_directions(central):
        step=F(1)
        for n,h in limits:
            slope=dot(n,d)
            if slope:step=min(step,h/(2*abs(slope)))
        shift=tuple(step*x for x in d)
        for n,h in raw:
            value=h+dot(n,shift)
            assert value!=0,'probe on true candidate plane'
            if h:assert h*value>0,'certified step crossed independent original candidate plane'
        original=(shift[0]-shear*shift[1],shift[1]-shear*shift[2],shift[2])
        want=cube_union_state(cells,original)
        assert want!=0,'independent box-union probe lies on boundary'
        moved=Polyhedron([tuple(F(p[i])+shift[i] for i in range(3)) for p in A.verts],list(A.faces))
        assert tested.polyhedra_overlap(moved,B,0)==want,'actual probe vs independent interval union'
        checked+=1;signs.append(want)
    answer=0 if -1 in signs else 1
    assert tested.entrance_membership3(A,B)==answer
    rows.append({'case':name,'original_planes':len(raw),'checked_all_chambers':checked,'outside_chambers':signs.count(-1),'inside_chambers':signs.count(1),'expected_topology':answer,'seconds':time.perf_counter()-start})
    print(rows[-1])
after=hashlib.sha256(source.read_bytes()).hexdigest();assert before==after
(OUT/'topology3_step_audit.json').write_text(json.dumps({'source_sha256':before,'rows':rows,
 'independence':'Plain Fraction cyclic ring normals, raw source edge pairs, signed plane no-crossing checks; original Cartesian interval-union truth after independent inverse shear. No tested geometry primitive generates expected geometry.'},indent=2),encoding='utf-8')
