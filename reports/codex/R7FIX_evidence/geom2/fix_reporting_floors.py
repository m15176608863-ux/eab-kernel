from pathlib import Path
p=Path('src/eab/kernel2d/geom.py')
with p.open(encoding='utf-8',newline='') as f:s=f.read()
s=s.replace('from fractions import Fraction','from fractions import Fraction\nfrom functools import lru_cache')
s=s.replace('''    return ROUND_C * EPS * C / ell if ell > 0.0 else float("inf")''','''    return _display_fraction(Fraction(ROUND_C*EPS)*Fraction(C)/Fraction(ell)) if ell > 0.0 else float("inf")''')
s=s.replace('''    x, y = map(Fraction, a)
    return sqrt_rational(x*x+y*y)


def unit''','''    return _norm_exact(*map(Fraction, a))


@lru_cache(maxsize=4096)
def _norm_exact(x, y):
    return sqrt_rational(x*x+y*y)


def unit''')
s=s.replace('''    x, y = map(Fraction, a)
    square = x*x+y*y''','''    return _unit_exact(*map(Fraction, a))


@lru_cache(maxsize=4096)
def _unit_exact(x, y):
    square = x*x+y*y''',1)
s=s.replace('''    def component(value):
        return (1 if value>0 else -1)*sqrt_rational(value*value/square) if value else 0.0
    return component(ey),component(-ex)''','''    return unit((ey, -ex))''')
s=s.replace('''    C = max(abs(a[0]), abs(a[1]), abs(b[0]), abs(b[1]), abs(c[0]), abs(c[1]))
    return angle_floor(C, min(hypot(b[0] - a[0], b[1] - a[1]), hypot(c[0] - b[0], c[1] - b[1])))''','''    a, b, c = (tuple(map(Fraction, p)) for p in (a, b, c))
    C = max(abs(v) for p in (a, b, c) for v in p)
    length2 = min(sum((p[k]-q[k])**2 for k in (0, 1)) for p, q in ((a, b), (b, c)))
    return sqrt_rational((Fraction(ROUND_C*EPS)*C)**2/length2) if length2 else float("inf")''')
with p.open('w',encoding='utf-8',newline='') as f:f.write(s)
p=Path('src/eab/kernel2d/entrance.py')
with p.open(encoding='utf-8',newline='') as f:s=f.read()
s=s.replace('from fractions import Fraction','from fractions import Fraction\nfrom math import inf, nextafter')
s=s.replace('''    return round_floor(max(coord_scale(B), coord_scale(A) + max(abs(x0[0]), abs(x0[1])) + norm(d)))''','''    # This is an internal conservative reporting bound, not a float output.
    # Scale before any construction, retain the rational sum, and round the
    # sole radical outward. Its exact square certifies the chosen upper bound.
    factor = Fraction(64)*Fraction(2)**-52
    base = factor*(Fraction(coord_scale(A))+max(abs(Fraction(v)) for v in x0))
    square = factor*factor*sum(Fraction(v)**2 for v in d)
    root = sqrt_rational(square, allow_underflow=True)
    if Fraction(root)**2 < square:
        root = nextafter(root, inf)
    return max(factor*Fraction(coord_scale(B)), base+Fraction(root))''')
s=s.replace('Fraction(ctol + r) ** 2','(Fraction(ctol) + r) ** 2')
s=s.replace('Fraction(tol + _floor(A, B, x0, (0., 0.))) ** 2','(Fraction(tol) + _floor(A, B, x0, (0., 0.))) ** 2')
with p.open('w',encoding='utf-8',newline='') as f:f.write(s)
