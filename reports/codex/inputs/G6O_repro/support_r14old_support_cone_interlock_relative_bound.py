"""The exact README/test_limit interlock family defeats an unqualified cos bound.

Production LP supplies one candidate using mu=1.7. The independent verifier
accepts it as a feasible force system for the *true circular cone* at mu=1.8
only after raw Fraction six-equilibrium and circular-cone inequalities pass.
Thus its alpha is a certified LOWER bound on true capacity, not an oracle
obtained by trusting the production LP/cone/duality checker. k=5,6,7 then have
capacity less than cos(pi/k) times that lower bound, hence also less than
cos(pi/k) times true capacity. No Patton-only true-capacity assumption is used.
"""
from pathlib import Path
from fractions import Fraction as F
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/"src"),str(ROOT/"tests")]
sys.dont_write_bytecode=True
from test_limit import _interlock_capacity
from eab.limit import friction_generators

def dot(a,b):return sum((F(x)*F(y) for x,y in zip(a,b)),F(0))
def cross(a,b):
    a,b=tuple(F(x) for x in a),tuple(F(x) for x in b)
    return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])

candidate,cts,dead,live,N=_interlock_capacity(.25,1.7,k=4)
assert candidate.status=="optimal"
alpha_lower=candidate.alpha.exact
target_mu=F(9,5) # no greater than supplied binary64 1.8
sum_w=[F(0)]*6
checked=active=0
for i,ct in enumerate(cts):
    # These vectors are candidate data, NOT the independent oracle. We do not
    # trust their tangency, unit length, safety, or resultant equilibrium.
    directions=friction_generators(ct.normal,ct.mu,3,4,ct.tangent)
    force=tuple(sum((candidate.lambdas[4*i+j].exact*F(directions[j][a])
                     for j in range(4)),F(0)) for a in range(3))
    normal=tuple(F(x) for x in ct.normal)
    nn,normal_dot=dot(normal,normal),dot(force,normal)
    assert normal_dot>=0,(i,"tensile force candidate")
    assert dot(force,force)*nn-normal_dot**2 <= target_mu**2*normal_dot**2,(i,"candidate outside true circular cone")
    moment=cross(ct.point,force)
    for a,x in enumerate((*force,*moment)):sum_w[a]+=x
    checked+=1;active+=any(force)
for a in range(6):
    assert sum_w[a]+F(dead[a])+alpha_lower*F(live[a])==0,(a,"exact independent equilibrium")
print(f"CIRCULAR_CONE_STATIC_CERTIFICATE contacts={checked}, active={active}, six_exact_residuals=0, circular inequalities=PASS")
print("certified true-circle capacity lower bound alpha/N=",float(alpha_lower/F(N)))
assert all(F(c.normal[1])==0 and F(c.normal[2])>0 for c in cts)
t_max=max(abs(F(c.normal[0]))/F(c.normal[2]) for c in cts)
assert F(1.8)*t_max<1
# Every circular-cone force then has F_z>=0 and -F_x <= U*F_z.
# Summation proves a finite circle upper bound U*N even without ignoring moments.
finite_circle_upper=(t_max+F(1.8))/(1-t_max*F(1.8))
print("independent force-projection finite circular upper bound alpha/N<=",float(finite_circle_upper))

# Rational lower bounds on cos(pi/k): k5 uses (1+sqrt(5))/4>4/5;
# k6 uses sqrt(3)/2>4/5. k7 uses the alternating cosine lower polynomial
# at 22/49 (>pi/7), whose value is >9/10.
assert F(5)>F(11,5)**2
assert F(3,4)>F(4,5)**2
x=F(22,49)
cos7_lower=1-x*x/2+x**4/24-x**6/720
assert cos7_lower>F(9,10)
for k,lower_cos in ((5,F(4,5)),(6,F(4,5)),(7,F(9,10))):
    result,new_cts,new_dead,new_live,NN=_interlock_capacity(.25,1.8,k=k)
    assert result.status=="optimal"
    assert [(c.point,c.normal) for c in new_cts]==[(c.point,c.normal) for c in cts]
    assert new_dead==dead and new_live==live and NN==N
    assert all(F(c.mu)>=target_mu for c in new_cts)
    assert result.alpha.exact<lower_cos*alpha_lower
    print(f"k={k}: alpha/N={float(result.alpha)/N:.17g}, ratio to certified circular lower bound={float(result.alpha.exact/alpha_lower):.17g} < {lower_cos} < cos(pi/{k})")
print("CONFIRMED: same interlock geometry at ordinary mu=1.8 violates relative capacity shortfall <=1-cos(pi/k)")
