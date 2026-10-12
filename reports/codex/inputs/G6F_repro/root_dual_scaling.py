"""Finite-input Dual operations versus independent analytic/Fraction oracle."""
import sys
from pathlib import Path
from fractions import Fraction as F
import math
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))
from eab.dual import Dual, atan2

def main():
    for scale in (1.0, 1e200, 1e-200):
        x = Dual(scale, (1.0,))
        y = Dual(scale, (0.0,))
        expected = -F(1) / (2*F(scale))
        try:
            got = atan2(y,x)
            print(f'atan2 scale={scale!r} primal={got.v!r} derivative={got.e[0]!r} expected={float(expected)!r} equal={got.e[0] == float(expected)}')
            assert math.isfinite(float(expected))
            assert (got.e[0] == float(expected)) == (scale == 1.0)
        except Exception as e:
            assert scale == 1e-200 and isinstance(e, ZeroDivisionError)
            print(f'atan2 scale={scale!r} exception={type(e).__name__}: {e} expected={float(expected)!r}')
    # This quotient equals the identity parameter, with derivative 1.
    scale = 1e200
    got = Dual(scale,(scale,)) / scale
    assert got.v == 1 and math.isinf(got.e[0])
    print(f'division={got!r} expected=Dual(1.0,(1.0,))')
    # All inputs and the correct derivative are finite at a much smaller scale.
    got = Dual(1e-200,(1e-200,)) / 1e-200
    assert got.v == 1 and got.e[0] == 0
    print(f'division_small={got!r} expected=Dual(1.0,(1.0,))')
    for p in (0.0, 1.0, 2.0):
        try: print(f'zero_power_{p}={Dual(0.0,(1.0,)) ** p!r}')
        except Exception as e: print(f'zero_power_{p}={type(e).__name__}: {e}')

if __name__ == '__main__': main()
