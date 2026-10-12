"""Ordinary-scale counterexample to an unqualified 1-cos(pi/k) capacity shortfall.

Independent oracle: dead=-e_z, live=e_x and slope normal (-3,0,4).
At equilibrium F=(-alpha,0,1), circular Coulomb mu=1 gives
|4*alpha-3| <= 3*alpha+4, hence the finite capacity is exactly 7.
For a k=4 fan whose tangent hint (4,5,3) bisects the resisting tangent,
the exact ideal diamond has mu_eff=1/sqrt(2). Since 1/sqrt(2)<3/4,
its capacity is below (3/4+3/4)/(1-9/16)=24/7<7/2.
No production LP/geometry primitive computes the reference formula.
"""
from pathlib import Path
from fractions import Fraction as F
import sys
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.dont_write_bytecode = True
from eab.limit import LimitContact, limit_load, check_duality

ct = LimitContact((0.0, 0.0, 0.0), (-3.0, 0.0, 4.0), 1.0,
                  tangent=(4.0, 5.0, 3.0))
dead = [0.0, 0.0, -1.0, 0.0, 0.0, 0.0]
live = [1.0, 0.0, 0.0, 0.0, 0.0, 0.0]
r = limit_load([ct], dead, live, dim=3, k=4)
assert r.status == "optimal"
alpha = r.alpha.exact
raw_full = F(7)
assert alpha < raw_full / 2
# Avoid any dispute about normalized binary64 normal versus the original axis.
ax, ay, az = (F(v) for v in ct.normal)
assert ax < 0 and ay == 0 and az > -ax
stored_full = (-ax + az) / (az + ax)
assert alpha < stored_full / 2
# cos(pi/4)=1/sqrt(2)>1/2, independently by exact squares.
assert F(1, 2)**2 < F(1, 2)
assert F(2) * alpha**2 < stored_full**2
check = check_duality(r, [ct], dead, live, dim=3, k=4)
assert check["ok"]
print("normal=", ct.normal, "mu=1, k=4, tangent=(4,5,3)")
print("status=", r.status, "alpha=", repr(float(r.alpha)), "exact_alpha=", str(alpha))
print("independent original-axis circular capacity=7; exact stored-axis capacity=", str(stored_full))
print("actual/full ratio=", float(alpha/stored_full), "< 1/2 < cos(pi/4)")
print("selfcheck_ok=", check["ok"])
print("CONFIRMED: ordinary supported finite input violates an unqualified capacity-shortfall <= 1-cos(pi/k) claim")
