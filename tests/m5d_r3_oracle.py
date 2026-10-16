"""Independent M5d rational-event oracle; no production imports.

Imports: fractions.Fraction, functools.lru_cache, math.comb.
Polynomial/Sturm code is carried over from the independent M5a test oracle;
its G0 overlap import and all production dependencies are deliberately absent.
Callers provide initially strictly separated rings. All VE/EV incidences are
isolated, including tangencies and closed-segment endpoint incidences.
"""
from fractions import Fraction as F
from functools import lru_cache
from math import comb


def tidy(p):
    p = [F(x) for x in p]
    while len(p) > 1 and p[-1] == 0:
        p.pop()
    return tuple(p) or (F(0),)


def add(p, q):
    return tidy(tuple((p[i] if i < len(p) else 0) +
                      (q[i] if i < len(q) else 0)
                      for i in range(max(len(p), len(q)))))


def multiply(p, q):
    a = [F(0)] * (len(p) + len(q) - 1)
    for i, x in enumerate(p):
        for j, y in enumerate(q):
            a[i+j] += x*y
    return tidy(a)


def value(p, x):
    y = F(0)
    for c in reversed(p):
        y = y*x+c
    return y


def quotient(p, q):
    r = list(tidy(p))
    q = tidy(q)
    if q == (0,):
        raise ZeroDivisionError("oracle zero polynomial divisor")
    out = [F(0)] * max(1, len(r)-len(q)+1)
    while r != [0] and len(r) >= len(q):
        k, c = len(r)-len(q), r[-1]/q[-1]
        out[k] += c
        for i, v in enumerate(q):
            r[i+k] -= c*v
        r = list(tidy(r))
    return tidy(out), tidy(r)


def monic(p):
    p = tidy(p)
    return p if p == (0,) else tuple(x/p[-1] for x in p)


def gcd(p, q):
    p, q = tidy(p), tidy(q)
    while q != (0,):
        p, q = q, quotient(p, q)[1]
    return monic(p)


@lru_cache(maxsize=4096)
def squarefree(p):
    p = tidy(p)
    if len(p) <= 1:
        return p
    deriv = tuple(i*p[i] for i in range(1, len(p)))
    return monic(quotient(p, gcd(p, deriv))[0])


@lru_cache(maxsize=4096)
def sturm(p):
    p = squarefree(p)
    if len(p) <= 1:
        return (p,)
    result = [p, tuple(i*p[i] for i in range(1, len(p)))]
    while True:
        r = quotient(result[-2], result[-1])[1]
        if r == (0,):
            return tuple(result)
        # Positive rescaling keeps signs and prevents coefficient inflation.
        r = tuple(-x for x in r)
        scale = abs(r[-1])
        result.append(tuple(x/scale for x in r))


def variations(p, x):
    signs = []
    for q in sturm(p):
        v = value(q, x)
        if v:
            signs.append((v > 0)-(v < 0))
    return sum(a != b for a, b in zip(signs, signs[1:]))


def count(p, lo, hi):
    if lo >= hi or len(p) <= 1:
        return 0
    assert value(p, lo) != 0 and value(p, hi) != 0, "oracle nonroot interval ends"
    return variations(p, lo)-variations(p, hi)


def interval_value(p, lo, hi):
    low = high = F(0)
    for c in reversed(p):
        products = low*lo, low*hi, high*lo, high*hi
        low, high = min(products)+c, max(products)+c
    return low, high


class Root:
    """Oracle-private exact root; never compared by binary64 approximations."""

    def __init__(self, p, lo, hi):
        self.p, self.lo, self.hi = squarefree(tidy(p)), F(lo), F(hi)
        if self.lo == self.hi:
            assert value(self.p, self.lo) == 0, "oracle rational witness"
        else:
            assert count(self.p, self.lo, self.hi) == 1, "oracle isolated root count"

    @staticmethod
    def rational(x):
        return Root((-F(x), F(1)), F(x), F(x))

    def refine(self):
        if self.lo == self.hi:
            return
        middle = (self.lo+self.hi)/2
        if value(self.p, middle) == 0:
            self.lo = self.hi = middle
        elif count(self.p, self.lo, middle):
            self.hi = middle
        else:
            self.lo = middle

    def sign(self, p):
        p = tidy(p)
        if self.lo == self.hi:
            v = value(p, self.lo)
            return (v > 0)-(v < 0)
        common = gcd(self.p, p)
        if len(common) > 1 and count(common, self.lo, self.hi):
            return 0
        while True:
            a, b = interval_value(p, self.lo, self.hi)
            if a > 0:
                return 1
            if b < 0:
                return -1
            Root.refine(self)
            if self.lo == self.hi:
                v = value(p, self.lo)
                return (v > 0)-(v < 0)


def compare(a: Root, b: Root):
    if a.lo == a.hi:
        return -Root.sign(b, (-a.lo, 1))
    if b.lo == b.hi:
        return Root.sign(a, (-b.lo, 1))
    low, high = max(a.lo, b.lo), min(a.hi, b.hi)
    common = gcd(a.p, b.p)
    if low < high and len(common) > 1 and count(common, low, high):
        return 0
    while not (a.hi <= b.lo or b.hi <= a.lo):
        Root.refine(a)
        Root.refine(b)
    return -1 if a.hi <= b.lo else 1


def distinct(values):
    # Exact insertion order, no comparator escape through opaque callbacks.
    out = []
    for item in values:
        position = 0
        duplicate = False
        while position < len(out):
            ordering = compare(out[position], item)
            if ordering == 0:
                duplicate = True
                break
            if ordering > 0:
                break
            position += 1
        if not duplicate:
            out.insert(position, item)
    return out


def roots(p, lo=F(0), hi=F(1)):
    # Explicit worklist instead of recursive dynamic calls. Every interval is
    # certified by an exact Sturm count; linear/endpoint roots are exact.
    pending = [(squarefree(tidy(p)), lo, hi)]
    answer = []
    while pending:
        polynomial, lower, upper = pending.pop()
        if len(polynomial) <= 1:
            continue
        if len(polynomial) == 2:
            root = -polynomial[0]/polynomial[1]
            if lower <= root <= upper:
                answer.append(Root.rational(root))
            continue
        endpoint_root = None
        for endpoint in (lower, upper):
            if value(polynomial, endpoint) == 0:
                endpoint_root = endpoint
                break
        if endpoint_root is not None:
            reduced, remainder = quotient(polynomial, (-endpoint_root, F(1)))
            assert remainder == (0,)
            answer.append(Root.rational(endpoint_root))
            pending.append((reduced, lower, upper))
            continue
        n = count(polynomial, lower, upper)
        if not n:
            continue
        if n == 1:
            answer.append(Root(polynomial, lower, upper))
            continue
        middle = (lower+upper)/2
        if value(polynomial, middle) == 0:
            reduced, remainder = quotient(polynomial, (-middle,F(1)))
            assert remainder == (0,)
            answer.append(Root.rational(middle))
            pending.append((reduced,lower,upper))
        else:
            pending.append((polynomial,lower,middle))
            pending.append((polynomial,middle,upper))
    return distinct(answer)


def interpolate(samples):
    """Six fixed integer samples, scalar Lagrange interpolation, degree <= 5."""
    result = (F(0),)
    for i, y in enumerate(samples):
        term, denominator = (F(1),), F(1)
        for j in range(len(samples)):
            if i != j:
                term = multiply(term, (-F(j), F(1)))
                denominator *= i-j
        result = add(result, tuple(c*y/denominator for c in term))
    return result


def point(path, time):
    return tuple(value(path[k], time)/value(path[2], time) for k in (0, 1))


def relative(p, q):
    denominator = multiply(p[2], q[2])
    return tuple(add(multiply(p[k], q[2]), tuple(-x for x in multiply(q[k], p[2])))
                 for k in (0, 1)), denominator


def event(vertex, first, last):
    u, du = relative(last, first)
    w, dw = relative(vertex, first)
    v, dv = relative(vertex, last)
    def product(a, b, cross=False):
        return add(multiply(a[0], b[1] if cross else b[0]),
                   tuple((-1 if cross else 1)*x for x in multiply(a[1], b[0] if cross else b[1])))
    # Positive denominators do not affect signs. Remove positive denominator
    # factors exactly; this is an optimization, not a shared geometry primitive.
    polynomials = product(u, w, True), product(u, w), tuple(-x for x in product(u, v))
    out = []
    for poly in polynomials:
        for den in (du, dw, dv):
            divisor = gcd(poly, den)
            if len(divisor) > 1:
                # The monic factor has positive value on [0,1] in this domain.
                assert value(divisor, F(0)) > 0 and not roots(divisor)
                poly = quotient(poly, divisor)[0]
        out.append(poly)
    return tuple(out)


def no_zero_on_unit_interval(poly):
    n = len(poly)-1
    coefficients = tuple(sum(poly[j]*F(comb(i,j),comb(n,j)) for j in range(i+1))
                         for i in range(n+1))
    return min(coefficients) > 0 or max(coefficients) < 0


def initially_separated(a, b):
    # Independent direct fixed-time separating-axis witness. A strict gap
    # between all vertices separates their convex hulls, hence the rings.
    rings = tuple(tuple(point(path, F(0)) for path in ring) for ring in (a,b))
    directions = [(F(1),F(0)),(F(0),F(1))]
    for ring in rings:
        for start,end in zip(ring,ring[1:]+ring[:1]):
            directions.append((end[1]-start[1],start[0]-end[0]))
    for nx,ny in directions:
        first = tuple(nx*x+ny*y for x,y in rings[0])
        second = tuple(nx*x+ny*y for x,y in rings[1])
        if max(first) < min(second) or max(second) < min(first):
            return True
    return False


def first_events(a, b):
    """All first closed-edge incidences after independent initial separation."""
    assert initially_separated(a,b), 'independent oracle initial strict separation'
    candidates = []
    for p, q, tag in ((a,b,'VE'),(b,a,'EV')):
        for i, vertex in enumerate(p):
            for j, first in enumerate(q):
                f, g, h = event(vertex, first, q[(j+1)%len(q)])
                if no_zero_on_unit_interval(f):
                    continue
                times = roots(f) if f != (0,) else distinct(roots(g)+roots(h)+[Root.rational(0),Root.rational(1)])
                for time in times:
                    if time.sign(g) >= 0 and time.sign(h) >= 0:
                        label = (tag,i,j) if tag == 'VE' else (tag,j,i)
                        candidates.append((time,label))
    if not candidates:
        return None, ()
    first = distinct([time for time,_ in candidates])[0]
    return first, tuple(sorted(label for time,label in candidates if compare(time,first)==0))


def affine_perturb(paths, endpoints):
    """Coordinate errors interpolate independent bounded endpoint errors."""
    return tuple(tuple(add(path[k],multiply((errors[k][0],errors[k][1]-errors[k][0]),path[2]))
                       for k in (0,1))+(path[2],)
                 for path,errors in zip(paths,endpoints))
