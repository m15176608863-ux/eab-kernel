"""Read-only cross review of root constructions, independently checked."""
from decimal import Decimal, localcontext
from fractions import Fraction as F
import math
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT/'src'))
from eab.construction import sqrt_rational
from eab.kernel2d.covers import facet_gap
from eab.kernel2d.entrance import first_entrance
from eab.kernel3d.geom3 import box
import eab.margin as M

rng = random.Random(60309)
values = []
for _ in range(1000):
    exponent = rng.randint(-1078, 1022)
    q = F(rng.randrange(1, 2**40), rng.randrange(1, 2**40)) * F(2)**exponent
    values.append(q*q*F(rng.randrange(1, 500), rng.randrange(1, 500)))
for e in (-1074, -1000, -600, 0, 500, 1022):
    for n in (1., math.nextafter(1., 2.)):
        lower = F(math.ldexp(n, e))
        upper = F(math.nextafter(float(lower), math.inf))
        midpoint = (lower+upper)/2
        for side in (-1, 0, 1):
            values.append(midpoint**2 + side*(upper-lower)**2/F(2**300))
maximum = F(float.fromhex('0x1.fffffffffffffp1023'))
checked = 0
for value in values:
    if value > maximum**2:
        try:
            sqrt_rational(value)
        except OverflowError:
            continue
        raise AssertionError('beyond-range root did not fail')
    with localcontext() as ctx:
        ctx.prec = 1600
        expected = float((Decimal(value.numerator)/Decimal(value.denominator)).sqrt())
    got = sqrt_rational(value, allow_underflow=True)
    assert got == expected, (value, got, expected)
    if expected == 0:
        try:
            sqrt_rational(value)
        except ArithmeticError:
            pass
        else:
            raise AssertionError('unrepresentable nonzero root did not fail')
    checked += 1
print(f'sqrt_decimal_reference: {checked} exact matches including subnormal midpoint cases')

# FF contact at a rotated square's edge, both directions and disparate scales.
count = 0
for exponent in (-600, 0, 600):
    s = F(2)**exponent
    for reverse in (False, True):
        c, sn = F(3, 5), F(4, 5)
        def rotate(p):
            return (c*p[0]-sn*p[1], sn*p[0]+c*p[1])
        square = [rotate(p) for p in ((0, 0), (s, 0), (s, s), (0, s))]
        X, D = rotate((2*s, s/2)), rotate((-s, 0))
        if reverse:
            X, D = rotate((-2*s, s/2)), rotate((s, 0))
        result = first_entrance(square, square, X, D)
        assert result.t_exact == 1 and result.gap == 0
        assert result.point_a == result.point_b
        assert facet_gap(square, square, result.label,
                         tuple(x+d for x, d in zip(X, D))) == 0
        count += 1
print(f'rotated_extreme_2d_contact: {count} exact times/zero gaps/coincident witnesses')

# Cached record outputs are independent even after replacing every mutable field.
a, b = box(center=(0, 0, 3)), box()
before = M._resolved(a, b, 0., None, None)
signature = [(c.label(), c.normal, c.gap, c.point_a, c.point_b, w, n, d2)
             for c, w, n, d2 in before[2]]
for c, _, _, _ in before[2]:
    c.a_feature = ('poison',)
    c.normal = (999., 888., 777.)
    c.point_a = None
    c.params = (123.,)
before[2].clear()
after = M._resolved(a, b, 0., None, None)
assert signature == [(c.label(), c.normal, c.gap, c.point_a, c.point_b, w, n, d2)
                     for c, w, n, d2 in after[2]]
view, labels = M._surface_view(tuple(a.verts), tuple(a.faces))
view.verts.clear()
view.faces.clear()
fresh, again = M._surface_view(tuple(a.verts), tuple(a.faces))
assert fresh.verts == a.verts and fresh.faces == a.faces and labels == again
print('margin_cache_isolation: all mutated returned fields and containers isolated')
print('CROSS_REVIEW_PASS')
