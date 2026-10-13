"""WO-G6N: unguarded public atan2 silently erases finite Fraction arguments.
Run: python -X utf8 review/repro/support_dual_trig_domain.py
Reference: atan2(x,x)=integral_0^1 1/(1+t*t) dt for x>0. On (0,1),
its integrand lies strictly between 1/2 and 1, so the angle is strictly
in (1/2,1). This exact Fraction enclosure calls no production/libm oracle.
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from fractions import Fraction as F
from eab.dual import Dual, atan2, sin
from eab.numeric_domain import ConstructionDomainError, check_input

for exponent in (-1075,-1100,-2000):
    x=F(2)**exponent
    try:
        check_input(x,"atan2.y")
    except ConstructionDomainError as e:
        print(f"declared engineering envelope rejects 2**{exponent}: {e}")
    else:
        raise AssertionError("review setup must be outside D400")
    scalar=atan2(x,x)
    jet=atan2(Dual(x,(x,)), Dual(x,(F(0),)))
    print(f"exponent={exponent}: scalar atan2={scalar!r}; Dual atan2={jet!r}; exact angle enclosure=(1/2,1)")
    assert scalar == 0.0 and jet.v == 0.0
    assert not F(1,2) < F(scalar) < F(1)
    assert jet.e == (0.5,), "independent derivative (x*x)/(2*x*x)=1/2"
    sine=sin(x)
    print(f"sin exact positive input -> {sine!r} without domain exception")
    assert sine == 0.0
print("CONFIRMED: public atan2 and sin return silently wrong zero outside their engineering envelope")
