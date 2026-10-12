"""Independent follow-up checks for the candidate and three polygon optima.

Generator lists and solver fields are merely candidate data. All static,
dual, circular-cone, indexing and reference-point checks below are raw
Fraction dot/cross formulas; no tested wrench/LP/duality helper is used.
"""
from pathlib import Path
from fractions import Fraction as F
import runpy
import sys
ROOT=Path(__file__).resolve().parents[2];sys.dont_write_bytecode=True
ns=runpy.run_path(str(ROOT/'review/repro/support_cone_interlock_relative_bound.py'))
dot,cross=ns['dot'],ns['cross']
candidate,cts,dead,live=ns['candidate'],ns['cts'],ns['dead'],ns['live']
assert len(cts)==64 and len(candidate.lambdas)==4*len(cts)
assert candidate.alpha.exact>0
assert not candidate.row_duals
assert all(F(c.cohesion)==0 and F(c.area)==0 for c in cts)
assert all(len(c.point)==len(c.normal)==3 for c in cts)
assert list(map(F,dead[:3]))==[F(0),F(0),F(-100)]
assert list(map(F,live[:3]))==[F(1),F(0),F(0)]
# Exact first-moment formula independently proves that the load moments use
# the same origin-zero reference as cross(ct.point, force).
assert dead[3]==dead[5]==0 and live[3]==live[5]==0 and live[4]==1
common_load_point=(F(dead[4])/100,F(0),F(1))
assert cross(common_load_point,dead[:3])==tuple(F(v) for v in dead[3:])
assert cross(common_load_point,live[:3])==tuple(F(v) for v in live[3:])
print('CROSSCHECK lower certificate: 64 contacts, zero cohesion, 4*64 lambda indexing, alpha>0, origin-zero load moments PASS')

for k in (5,6,7):
    result,cts,dead,live,N=ns['_interlock_capacity'](.25,1.8,k=k)
    assert len(result.lambdas)==k*len(cts) and not result.row_duals
    assert all(F(c.cohesion)==0 and F(c.area)==0 for c in cts)
    y=[v.exact for v in result.mechanism];alpha=result.alpha.exact
    residual=[F(v)+alpha*F(w) for v,w in zip(dead,live)]
    for i,ct in enumerate(cts):
        directions=ns['friction_generators'](ct.normal,ct.mu,3,k,ct.tangent)
        assert len(directions)==k
        for j,g in enumerate(directions):
            lam=result.lambdas[k*i+j].exact
            assert lam>=0
            column=tuple(F(v) for v in g)+cross(ct.point,g)
            assert dot(y,column)>=0
            for q in range(6):residual[q]+=lam*column[q]
    assert all(v==0 for v in residual)
    assert dot(y,live)==1 and -dot(y,dead)==alpha
    print(f'CROSSCHECK k={k}: independent six-row primal equilibrium + nonnegative multipliers + dual feasibility + drive=1 + equal upper/lower optimum PASS')

def atan_upper(q):
    # 20 terms (even) lower partial sum; add next positive term for upper.
    s=sum(((-1)**j*q**(2*j+1)/F(2*j+1) for j in range(20)),F(0))
    return s+q**41/41
def atan_lower(q):
    return sum(((-1)**j*q**(2*j+1)/F(2*j+1) for j in range(20)),F(0))
pi_upper=16*atan_upper(F(1,5))-4*atan_lower(F(1,239))
assert pi_upper<F(22,7)
print('CROSSCHECK pi<22/7: independent rational Machin/arctan upper interval PASS')
print('RELATIVE_BOUND_CROSSCHECK_PASS')
