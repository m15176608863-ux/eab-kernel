"""WO-G6O: generic sampled geometry rounds Dual coordinates too early.

Independent oracle completes cx-lx/2+lx*u in Fraction before RN-even.
No production geometry/constructor/dual operation computes the reference.
The sampled coordinate u=1/2 is exact, so no libm or mesh idealization issue.
"""
from pathlib import Path
from fractions import Fraction as F
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT/'src'), str(ROOT)]
sys.dont_write_bytecode = True
from eab.dual import Dual
from tools.osteomorphic import osteomorphic_block, osteomorphic_block_generic

for center in (F(2)**-100, F(2)**-400):
    kwargs = dict(nx=2, ny=1, lx=2, amp=0, center=(center, 0, 0))
    raw = osteomorphic_block(**kwargs)
    kwargs['center'] = (Dual(center, (1.0,)), 0, 0)
    generic = osteomorphic_block_generic(**kwargs)
    middle = 4  # i=1, j=0, top: (2*(ny+1))*i
    exact = center - F(2)/2 + F(2)*F(1,2)
    expected = float(exact)
    actual = generic.verts[middle][0]
    assert exact != 0 and expected != 0
    assert raw.verts[middle][0] == expected
    assert actual.v == 0.0 and actual.v != expected
    assert actual.e == (1.0,)
    print(f'center=2**{-(center.denominator.bit_length()-1)}, lx=2, nx=2, amp=0')
    print(f'  independent complete exact midpoint x={exact}; RN-even={expected!r}')
    print(f'  scalar constructor x={raw.verts[middle][0]!r}; generic Dual x={actual!r}')
    print('  all physical inputs in D400; exact coordinate and derivative both representable')

generic = osteomorphic_block_generic(nx=2, ny=1,
    lx=Dual(2.0, (2.0**60,)), center=(Dual(0.0, (1.0,)), 0, 0), amp=0)
middle = 4
expected_jet = F(1) - F(2**60)/2 + F(2**60)*F(1,2)
actual = generic.verts[middle][0]
assert expected_jet == 1 and actual.v == 0.0 and actual.e == (0.0,)
print('center primal=0, center seed=1, lx primal=2, lx seed=2**60, u=1/2')
print(f'  independent complete exact derivative={expected_jet}; generic Dual x={actual!r}')
print('  ordinary-sized geometry: analytic derivative is silently erased by intermediate jet rounding')

print('CONFIRMED: production generic geometry silently replaces a representable nonzero coordinate with zero')
