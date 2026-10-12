"""已复現的读者输入保真风险；不假称未声明数学合同被违反。
bdda_geom docstring 明示 floor，故按声明的近重复清洗模型结果允许。
Oracle: 自写 Fraction 绕数，原严格内点；清洗后 A ymax=0，B ymin>0。
"""
from pathlib import Path
import sys,math,csv,json
from fractions import Fraction as F
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
from eab.readers.bdda_geom import load_step_geometries
from eab.kernel2d.covers import membership_convex

def inside(poly,p):
    winding=0
    for a,b in zip(poly,poly[1:]+poly[:1]):
        a,b=tuple(map(F,a)),tuple(map(F,b));px,py=p
        cross=(b[0]-a[0])*(py-a[1])-(b[1]-a[1])*(px-a[0])
        if cross==0 and min(a[0],b[0])<=px<=max(a[0],b[0]) and min(a[1],b[1])<=py<=max(a[1],b[1]):return False
        if a[1]<=py<b[1] and cross>0:winding+=1
        if b[1]<=py<a[1] and cross<0:winding-=1
    return winding!=0

def main():
    T=1e8;u=math.ulp(T)
    A=[(T,0.),(T+u,u),(T+1,0.),(T+1,-1.),(T,-1.)]
    B=[(T-.5,float(F(u)*3/4)),(T+1.5,float(F(u)*3/4)),(T+1.5,1.),(T-.5,1.)]
    p=(F(T)+F(u),F(u)*7/8)
    assert inside(A,p) and inside(B,p),'raw strict overlap certificate'
    path=ROOT/'review/evidence/reader_short_feature.csv'
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.writer(f);w.writerow(['step','block','vidx','x','y'])
        for block,poly,start in ((1,A,1),(2,B,100)):
            for i,(x,y) in enumerate(poly,start):w.writerow([0,block,i,repr(x),repr(y)])
    g=load_step_geometries(path,dup_tol=0.)[0];cleanA=g.blocks[1].poly;cleanB=g.blocks[2].poly
    assert max(F(q[1]) for q in cleanA)==0 and min(F(q[1]) for q in cleanB)>0
    raw=membership_convex(A,B,(0,0),tol=0.);clean=membership_convex(cleanA,cleanB,(0,0),tol=0.)
    assert raw==1 and clean==-1 and g.alias[2]==1
    r={'contract_status':'UNCONFIRMED: L5 near-duplicate floor is explicitly documented; not counted as incorrect answer on the cleaned model','dup_tol_requested':0.,'ulp':u,'strict_overlap_witness':[str(v) for v in p],'raw_state':raw,'read_state':clean,'input_vertices':len(A),'read_vertices':len(cleanA),'alias':g.alias,'source':'src/eab/readers/bdda_geom.py:44-59'}
    print(json.dumps(r,ensure_ascii=False,indent=2));(ROOT/'review/evidence/root_reader_risk.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
if __name__=='__main__':main()
