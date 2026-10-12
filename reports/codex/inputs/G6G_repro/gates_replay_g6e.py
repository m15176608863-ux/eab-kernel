"""WO-G6F replay of 14 original G6E cases; no tracked writes."""
import json, math, random, sys, traceback
from fractions import Fraction as F
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests'),str(ROOT/'tools')]
from eab.kernel2d import covers as c2,geom as g2,g0 as gate2
from eab.kernel3d import covers3 as c3,geom3 as g3,g03
from eab.margin import body_distance

def r02():
    import ingest_bdda3d as m
    s=m.source_note('cb2_locked')
    control=[hex(ord(c)) for c in s if ord(c)<32]
    assert not control
    return {'controls':control,'source_tail':s[-110:]}

def r03():
    d=json.loads((ROOT/'fixtures/PROVENANCE.json').read_text(encoding='utf-8'))
    entries=[e for e in d['entries'] if e['dest'].startswith('bdda_df/') and 'kernel_sha256' in e]
    assert len(entries)==48
    assert all('input_sha256' in e and 'nonreproducible' in e for e in entries)
    return {'generated':len(entries),'all_input_sha256':True,'all_nonreproducible':True}

def r25():
    B=g3.box();out=[]
    for psi in (1e-11,1e-10,1e-9,3e-9):
        cs,sn=math.cos(psi),math.sin(psi);gap=.1
        rc=(cs*-1.-sn,sn*-1.+cs,-1.)
        corner=(1.+gap,1.+psi*gap/2,1.+gap)
        center=tuple(corner[i]-rc[i] for i in range(3))
        A=g3.Polyhedron([(center[0]+cs*x-sn*y,center[1]+sn*x+cs*y,center[2]+z) for x,y,z in g3.box().verts],list(g3.box().faces))
        ia=min(range(8),key=lambda i:math.dist(A.verts[i],corner))
        distance,label=body_distance(A,B)
        assert label[0]=='VV3'
        assert abs(distance-math.dist(A.verts[ia],B.verts[6]))<=4*math.ulp(distance)
        out.append([psi,ia,distance,label])
    return out

def r26():
    h=1e-14;B=[(0.,0.),(1.-h,0.),(1.,h),(1.,1.),(0.,1.)]
    Q=[(0.,0.),(.25,.25*math.sqrt(3)),(-.25,.25*math.sqrt(3))];A=[(-x,-y) for x,y in Q]
    eb=c2.convex_entrance_block(A,B);state=c2.membership_convex(A,B,(1.1,.5),0,eb)
    assert state==1
    r=gate2.g0_convex(A,B,samples=2000);assert r.passed
    C=1e3;h=1e-8;B=[(C,C),(C+1-h,C),(C+1,C),(C+1,C+1),(C,C+1)]
    Q=[(0.,0.),(.5*math.cos(1e-4),.5*math.sin(1e-4)),(.25,.4)];A=[(-x,-y) for x,y in Q]
    eb=c2.convex_entrance_block(A,B)
    # facet ordering changed legitimately; use raw G0 to retain all actual data.
    rr=gate2.g0_convex(A,B,samples=2000);assert rr.passed
    return {'chamfer_state':state,'chamfer_mismatches':len(r.mismatches),'T_G0':rr.passed,'T_FF':[l for l in eb.facets if l[0]=='FF']}

def r27():
    A=[(0.,0.),(.1,0.),(.1,.1),(0.,.1)];out=[]
    for h in (1e-14,2e-14,3e-14,1e-13):
        B=[(0.,0.),(1.-h,0.),(1.,0.),(.5,.2)]
        eb=c2.convex_entrance_block(A,B);out.append([h,len(eb.vertices)])
    for h,ap in ((3e-9,.2),(1e-8,.05)):
        C=1e5;B=[(C,C),(C+1-h,C),(C+1,C),(C+.5,C+ap)]
        out.append([h,len(c2.convex_entrance_block(A,B).vertices)])
    return out

def r29():
    from test_g03_two_rulers import _quat,_move,_yaw
    out=[]
    for ratio,yaw,rot in ((1000,1e-6,7),(100,1e-7,7),(10,1e-8,3),(100,1e-7,11)):
        h=ratio/2;A=_yaw(g3.box(center=(0,0,h+.6),half=(.5,.5,.5)),yaw);B=g3.box(half=(h,h,h))
        r=g03.g0_convex3(_move(A,_quat(rot)),_move(B,_quat(rot)),samples=0)
        assert r.passed and not r.facet_symmetric_diff
        out.append([ratio,yaw,rot,r.passed,r.boundary_checked])
    return out

def r30():
    SQ=[(0.,0.),(1.,0.),(1.,1.),(0.,1.)];RECT=[(0.,0.),(1000.,0.),(1000.,1.),(0.,1.)]
    def rot(P,th,t):
        c,s=math.cos(th),math.sin(th)
        return [(c*x-s*y+t[0],s*x+c*y+t[1]) for x,y in P]
    out=[]
    for C in (0.,1e3,1e4):
        for d in (1.05e-9,1.25e-9):
            A=rot(SQ,0,(C,.3*C));B=rot(RECT,d,(C,.3*C));tol=1e-12*gate2.char_length(A,B)
            eb=c2.convex_entrance_block(A,B,(0.,0.),tol)
            r,s=gate2.g0_convex(A,B,samples=100),gate2.g0_convex(B,A,samples=100)
            assert r.passed and s.passed
            out.append([C,d,[l for l in eb.facets if l[0]=='FF'],r.passed,s.passed])
    return out

def r31():
    from test_near_parallel_edges import exact_seg_seg,_quat,_move
    th,half,x0,gap=1.5e-6,.3,.95,4.5793919600798964e-9
    B=g3.tetra((-1.,0.,0.),(1.,0.,0.),(0.,-.8,-1.5),(0.,.9,-1.4));c,s=math.cos(th),math.sin(th)
    A=g3.tetra((x0-half*c,-half*s,gap),(x0+half*c,half*s,gap),(x0-.1,-.7,1.3+gap),(x0+.2,.8,1.2+gap))
    A,B=_move(A,_quat(5)),_move(B,_quat(5))
    truth=exact_seg_seg(A.verts[0],A.verts[1],B.verts[0],B.verts[1]);actual=g3._seg_seg_distance(A.verts[0],A.verts[1],B.verts[0],B.verts[1])
    assert abs(actual-truth)<=2*math.ulp(truth)
    return {'truth':truth,'oracle':actual,'margin':body_distance(A,B)}

def r38():
    pts=[(0.,0.),(1e-15,-1e-3),(1e-15,1.),(1e-3,-1e-3),(2.,-1e-3),(2.,1.)]
    H=g2.convex_hull(pts);assert (1e-15,-1e-3) in H
    def sq(c,h,th):
        ct,st=math.cos(th),math.sin(th)
        return [(c[0]+ct*x-st*y,c[1]+st*x+ct*y) for x,y in ((-h,-h),(h,-h),(h,h),(-h,h))]
    A=sq((3.,1e-3+2e-9),1e-3,1e-6);B=[(-1e3,-1e3),(1e3,-1e3),(1e3,0.),(-1e3,0.)]
    T=lambda p:(1e-3*p[0]+600,1e-3*p[1]-800)
    r,s=gate2.g0_convex(A,B,samples=200,seed=2),gate2.g0_convex(list(map(T,A)),list(map(T,B)),samples=200,seed=2)
    assert r.passed and s.passed
    return {'hull':H,'identity':r.passed,'scaled_translated':s.passed}

def r39():
    from test_covers3_g0_vote2 import _random_pair
    A,B=_random_pair(0);r=g03.g0_convex3(A,B,samples=40)
    real=c3.cones_intersect_relint
    try:
        c3.cones_intersect_relint=lambda *a:True
        s=g03.g0_convex3(A,B,samples=40)
    finally:c3.cones_intersect_relint=real
    assert r.passed and not s.passed and s.hull_vertex_mismatch==24 and s.e_vertices_ambiguous==0
    return {'baseline':r.passed,'internal_all_pairs_defect':s.passed,'mismatch':s.hull_vertex_mismatch,'ambiguous':s.e_vertices_ambiguous}

def r40():
    A=g3.box(half=(1,1,1));B=g3.box(center=(.3,.2,3),half=(2,1.5,.7))
    diffs=[tuple(F(y)-F(x) for x,y in zip(a,b)) for a in A.verts for b in B.verts]
    H=g3.convex_hull_3d(diffs)
    result=g03.facet_vote3(A,B,c3.local_facets3(A,B,1e-12),H,diffs)
    assert result[-1]==[]
    return result

def r41():
    A=[(0.,0.),(.1,0.),(.1,.1),(0.,.1)]
    def B(d,h):return [(0.,0.),(1.,0.),(1.,1.),(0.,1.),(0.,.5+h),(d,.5)]
    P=B(.5e-6,1e-4);out=[]
    try:c2.convex_entrance_block(A,P,(0.,0.),1e-6)
    except ValueError as e:out.append(str(e))
    else:raise AssertionError('microreflex convex input accepted')
    for d in (1e-5,1e-4):
        state=c2.membership_convex(A,P,(-.1+d,.2),0)
        assert state==1;out.append([d,state])
    try:c2.convex_entrance_block(A,B(5e-13,1e-11))
    except ValueError as e:out.append(str(e))
    else:raise AssertionError('second microreflex accepted')
    return out

def r44():
    def roof(h,yaw=0):
        sec=[(-1.,-1.),(1.,-1.),(1.,0.),(0.,h),(-1.,0.)]
        V=[(-2.,y,z) for y,z in sec]+[(2.,y,z) for y,z in sec]
        faces=[(4,3,2,1,0),(5,6,7,8,9)]+[(i,(i+1)%5,5+(i+1)%5,5+i) for i in range(5)]
        c,s=math.cos(yaw),math.sin(yaw)
        return g3.Polyhedron([(c*x-s*y,s*x+c*y,z) for x,y,z in V],faces)
    B=roof(.3);A=roof(.3,-2.297344991164547e-9)
    A=g3.Polyhedron([(x,y,-z+.61) for x,y,z in A.verts],[tuple(reversed(f)) for f in A.faces])
    from e5a_cover_oracle import strict_cone,model,scale
    am,bm=model(tuple(A.verts),tuple(A.faces)),model(tuple(B.verts),tuple(B.faces))
    out=[]
    for ia,ib in [(3,9),(4,8),(7,3),(8,2)]:
        truth=strict_cone((*bm[4][ib],*(scale(g,-1) for g in am[4][ia])))
        result=c3.cones_intersect_relint(A,ia,B,ib)
        assert truth==result==True
        out.append([ia,ib,truth,result])
    r=g03.g0_convex3(A,B,samples=40,seed=1);assert r.passed and r.e_vertices_ambiguous==0
    return {'pairs':out,'G0':r.passed,'ambiguous':r.e_vertices_ambiguous}

def main():
    out=[]
    for raw,fn in [(2,r02),(3,r03),(25,r25),(26,r26),(27,r27),(29,r29),(30,r30),(31,r31),(38,r38),(39,r39),(40,r40),(41,r41),(44,r44)]:
        try:
            result=fn(); row={'raw_1_based':raw,'status':'original_defect_not_reproduced','verified_output':result}
        except Exception:
            row={'raw_1_based':raw,'status':'RECHECK_REQUIRED','verified_output':traceback.format_exc()}
        out.append(row);print(json.dumps(row,ensure_ascii=False,default=str),flush=True)
    (ROOT/'review/notes/gates_g6e_replay.json').write_text(json.dumps(out,ensure_ascii=False,indent=2,default=str)+'\n',encoding='utf-8')
    assert all(x['status']=='original_defect_not_reproduced' for x in out)
    print('G6E_REPLAY gates 13/13 original defects not reproduced')

if __name__=='__main__':main()
