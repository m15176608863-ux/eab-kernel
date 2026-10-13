"""WO-G6N: independent exact certificate disproving the advertised safe cone.

No tested force/LP/construction primitive enters the oracle. Given n=(1,2,3),
dead=-n and live=(2,-1,0), exact orthogonality n.live=0 and norms squared
14 and 5 prove every circular Coulomb cone equilibrium has 5*alpha**2 <=
14*mu**2. This is an upper bound even if a discrete cone has extra restrictions.
"""
from pathlib import Path
from fractions import Fraction as F
import json
import math
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'));sys.dont_write_bytecode=True
import eab.limit as L

def main():
    raw=(F(1),F(2),F(3));p=(F(2),F(-1),F(0))
    assert sum(a*b for a,b in zip(raw,p))==0
    assert sum(v*v for v in raw)==14 and sum(v*v for v in p)==5
    # The six-dimensional extension adds exactly zero moments at the origin.
    dead=[-1.,-2.,-3.,0.,0.,0.];live=[2.,-1.,0.,0.,0.,0.]
    records=[]
    for mu in (1e16,1e17):
        ct=L.LimitContact((0.,0.,0.),(1.,2.,3.),mu,tangent=(2.,-1.,0.))
        axis=tuple(F(v) for v in ct.normal)
        # Also certify the circular cone around the exact *stored* normal:
        # this excludes a dispute about ideal vs rounded normalization.
        axis_square=sum(v*v for v in axis)
        dead_normal=sum(v*q for v,q in zip(axis,raw))
        assert sum(v*q for v,q in zip(axis,p))==0
        stored_upper_squared=((F(mu)**2+1)*dead_normal**2-14*axis_square)/(5*axis_square)
        generators=L.friction_generators(ct.normal,ct.mu,3,4,ct.tangent)
        normal_powers=[sum(v*F(g) for v,g in zip(raw,force)) for force in generators]
        stored_powers=[sum(v*F(g) for v,g in zip(axis,force)) for force in generators]
        r=L.limit_load([ct],dead,live,dim=3,k=4)
        data={'mu':mu,'status':r.status,'alpha':float(r.alpha),'resolvability':r.resolvability,
              'uncertainty':r.uncertainty,'generators':generators,
              'normal_power_exact':[str(v) for v in normal_powers],
              'stored_normal_power_exact':[str(v) for v in stored_powers],
              'independent_circular_upper_squared':str(14*F(mu)**2/5),
              'stored_normal_circular_upper_squared':str(stored_upper_squared)}
        if r.status=='optimal':
            data['alpha_exact']=str(r.alpha.exact)
            data['returned_upper_ratio_squared']=str(5*r.alpha.exact**2/(14*F(mu)**2))
            assert 5*r.alpha.exact**2 > 14*F(mu)**2,'must breach independent cone upper bound'
            assert r.alpha.exact**2>stored_upper_squared,'must breach exact stored-normal cone too'
            check=L.check_duality(r,[ct],dead,live,dim=3,k=4)
            assert check['ok'],'the returned rounded-direction model self-check passes'
            data['selfcheck_ok']=check['ok']
        else:
            assert r.status=='unbounded' and math.isinf(r.alpha),'finite circular cone cannot be unbounded'
            assert min(stored_powers)<0,'actual generated forces include tensile rays against stored normal'
        print(f"mu={mu:.17g}: status={r.status}, alpha={r.alpha:.17g}, "
              f"circle_upper={mu*math.sqrt(14/5):.17g}, resolvability={r.resolvability}")
        print('  generator raw-normal powers=',[float(v) for v in normal_powers])
        if r.status=='optimal':print('  exact alpha squared / circular upper squared=',float(F(data['returned_upper_ratio_squared'])), 'selfcheck_ok=',data['selfcheck_ok'])
        records.append(data)
    (ROOT/'review/evidence/limit_cone_safety_results.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
    print('LIMIT_CONE_SAFETY_CONFIRMED 2 supported finite-input counterexamples')

if __name__=='__main__':main()
