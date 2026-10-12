"""G6M 自校验独立构造错误候选。Oracle: 改变已知有限最优 alpha 后必不再既静力又强对偶。
对 LP exact 见证同时改浮点视图，防止仅靠视图不匹配拒绝。所有注入发生真实 maximize 返回边界。"""
from pathlib import Path
import sys,json,copy,time
from fractions import Fraction as F
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
from eab import limit as L,limit_multi as M
from unittest.mock import patch

def case(dim,offset,scale,coh):
    o=tuple(F(q) for q in offset); W=F(10)*scale; h=F(3)*scale;half=scale
    cs=[L.LimitContact(tuple(o[i]+ (sx*half if i==0 else sy*half if dim==3 and i==1 else 0) for i in range(dim)), tuple(1 if i==dim-1 else 0 for i in range(dim)),F(1,2),cohesion=coh,area=1) for sx in (-1,1) for sy in ((-1,1) if dim==3 else (0,))]
    p=tuple(o[i]+(h if i==dim-1 else 0) for i in range(dim))
    def wrench(f,p):
        f=list(map(F,f));r=list(map(F,p))
        return f+[r[0]*f[1]-r[1]*f[0]] if dim==2 else f+[r[1]*f[2]-r[2]*f[1],r[2]*f[0]-r[0]*f[2],r[0]*f[1]-r[1]*f[0]]
    dead=wrench(tuple(-W if i==dim-1 else 0 for i in range(dim)),p);live=wrench(tuple(1 if i==0 else 0 for i in range(dim)),p)
    return cs,dead,live

def main():
    t=time.time();c={'single_cases':0,'multi_cases':0,'edited_rejections':0,'injected_rejections':0}
    for dim in (2,3):
      for offset in ((F(0),)*dim,(F(10**6),F(-314159),F(17))[:dim]):
       for scale in (F(1,10**3),F(1),F(10**3)):
        for coh in (F(0),F(1,8)):
         cs,dead,live=case(dim,offset,scale,coh);r=L.limit_load(cs,dead,live,dim=dim,k=4)
         assert r.status=='optimal' and L.check_duality(r,cs,dead,live,dim=dim,k=4)['ok']
         # Independent tipping bound is W*half/h = W/3 and is controlling here.
         assert r.alpha.exact==10*scale/3
         c['single_cases']+=1
         bs=[M.LimitBody(dead,live)];bcs=[M.BodyContact(ct,0) for ct in cs]
         mr=M.limit_load_multi(bs,bcs,dim=dim,k=4);assert mr.alpha.exact==r.alpha.exact and M.check_duality_multi(mr,bs,bcs,dim=dim,k=4)['ok'];c['multi_cases']+=1
         for exponent in (3,30,100):
          bad=copy.deepcopy(r);bad.alpha=bad.alpha.exact*(1-F(1,10**exponent))
          d=L.check_duality(bad,cs,dead,live,dim=dim,k=4)
          assert not d['ok'] and not d['static_ok'];c['edited_rejections']+=1
          bad=copy.deepcopy(mr);bad.alpha=bad.alpha.exact*(1-F(1,10**exponent))
          d=M.check_duality_multi(bad,bs,bcs,dim=dim,k=4)
          assert not d['ok'] and not d['static_ok'];c['edited_rejections']+=1
         for module,call in ((L,lambda:L.limit_load(cs,dead,live,dim=dim,k=4)),(M,lambda:M.limit_load_multi(bs,bcs,dim=dim,k=4))):
          real=module.maximize
          for fld in ('exact_x','exact_y'):
           def corrupt(A,b,c,**kw):
            rr=real(A,b,c,**kw)
            if rr.status=='optimal':
             seq=list(getattr(rr,fld));j=next(i for i,v in enumerate(c) if v) if fld=='exact_x' else 0
             seq[j]+=F(1,10**100);setattr(rr,fld,tuple(seq))
             # consistent altered float view; tiny poison intentionally rounds unchanged
             if fld=='exact_x':rr.x=[float(v) for v in seq]
             else:rr.y=[float(v) for v in seq]
            return rr
           with patch.object(module,'maximize',corrupt):
            try:call()
            except RuntimeError as e:assert 'self-check' in str(e);c['injected_rejections']+=1
            else:raise AssertionError(('corrupted candidate accepted',dim,offset,scale,coh,fld,module.__name__))
    c['seconds']=time.time()-t;print(json.dumps(c,indent=2));(ROOT/'review/evidence/root_selfcheck_pressure.json').write_text(json.dumps(c,indent=2),encoding='utf-8')
if __name__=='__main__':main()
