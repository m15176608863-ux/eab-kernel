"""Independent SE(2) oracle: rational samples -> interpolation -> Sturm.

Import inventory: fractions.Fraction, functools.cmp_to_key/lru_cache, and
eab.kernel2d.g0_oracle.overlap. G0's transitive imports are fractions,
math.lcm and eab.oracle_construction (display functions are not called).
No se2/algebraic/motion/global_entrance/exact/construction primitive is
imported. Event coefficients are reconstructed from six scalar samples,
not from the production symbolic polynomial formula. Root/sign/set work
below is independently implemented; the common mathematical theorem is
not a shared program primitive. Inputs here are CCW test rings.
"""
from fractions import Fraction as F
from functools import cmp_to_key, lru_cache

from eab.kernel2d.g0_oracle import overlap


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
            self.refine()
            if self.lo == self.hi:
                v = value(p, self.lo)
                return (v > 0)-(v < 0)


def compare(a, b):
    if a.lo == a.hi:
        return -b.sign((-a.lo, 1))
    if b.lo == b.hi:
        return a.sign((-b.lo, 1))
    low, high = max(a.lo, b.lo), min(a.hi, b.hi)
    common = gcd(a.p, b.p)
    if low < high and len(common) > 1 and count(common, low, high):
        return 0
    while not (a.hi <= b.lo or b.hi <= a.lo):
        a.refine()
        b.refine()
    return -1 if a.hi <= b.lo else 1


def roots(p, lo=F(0), hi=F(1)):
    p = squarefree(tidy(p))
    if len(p) <= 1:
        return []
    if len(p) == 2:
        r = -p[0]/p[1]
        return [Root.rational(r)] if lo <= r <= hi else []
    for endpoint in (lo, hi):
        if value(p, endpoint) == 0:
            q, remainder = quotient(p, (-endpoint, F(1)))
            assert remainder == (0,)
            return sorted(roots(q, lo, hi)+[Root.rational(endpoint)], key=cmp_to_key(compare))
    n = count(p, lo, hi)
    if not n:
        return []
    if n == 1:
        return [Root(p, lo, hi)]
    middle = (lo+hi)/2
    if value(p, middle) == 0:
        q, remainder = quotient(p, (-middle, F(1)))
        assert remainder == (0,)
        return sorted(roots(q, lo, hi)+[Root.rational(middle)], key=cmp_to_key(compare))
    return roots(p, lo, middle)+roots(p, middle, hi)


def distinct(values):
    out = []
    for item in sorted(values, key=cmp_to_key(compare)):
        if not out or compare(out[-1], item):
            out.append(item)
    return out


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


def dot(a, b):
    return sum(x*y for x, y in zip(a, b))


def determinant(a, b):
    return a[0]*b[1]-a[1]*b[0]


def difference(a, b):
    return tuple(x-y for x, y in zip(a, b))


def point_at(p, spec, s):
    """Cayley rotation evaluated as two complex products, not production R."""
    u, d, c = spec
    w = F(u)*s
    x, y = difference(p, c)
    # (x+i y)*(1+i w)*(1+i w)/(1+w²).
    first = x-w*y, y+w*x
    second = first[0]-w*first[1], first[1]+w*first[0]
    return tuple(c[k]+s*d[k]+second[k]/(1+w*w) for k in (0, 1))


def ring_at(ring, spec, s):
    return tuple(point_at(p, spec, s) for p in ring)


def event_polynomials(p, q, r, mp, mq):
    def sample(s):
        vertex = point_at(p, mp, s)
        start, end = point_at(q, mq, s), point_at(r, mq, s)
        edge, offset = difference(end, start), difference(vertex, start)
        denominator = (1+(s*mp[0])**2)*(1+(s*mq[0])**2)
        projection = dot(edge, offset)
        return (denominator*determinant(edge, offset), denominator*projection,
                denominator*(dot(edge, edge)-projection))
    values = [sample(F(k)) for k in range(6)]
    answer = tuple(interpolate([v[k] for v in values]) for k in range(3))
    for s in (F(1, 7), F(13, 7)):
        assert tuple(value(p, s) for p in answer) == sample(s), "independent degree-five interpolation identity"
    return answer


def normal_cone(time, ring, i, other, j, own_spec, other_spec):
    before = difference(ring[i], ring[i-1])
    after = difference(ring[(i+1) % len(ring)], ring[i])
    turn = determinant(before, after)
    if turn < 0 or (turn == 0 and dot(before, after) <= 0):
        return False

    def sample(s):
        vertices = [point_at(ring[k % len(ring)], own_spec, s) for k in (i-1, i, i+1)]
        edge = difference(point_at(other[(j+1) % len(other)], other_spec, s),
                          point_at(other[j], other_spec, s))
        u, v = difference(vertices[1], vertices[0]), difference(vertices[2], vertices[1])
        den = (1+(s*own_spec[0])**2)*(1+(s*other_spec[0])**2)
        return den*determinant(edge, u), den*determinant(v, edge), den*dot(edge, u)
    values = [sample(F(k)) for k in range(6)]
    signs = [time.sign(interpolate([v[k] for v in values])) for k in range(3)]
    return signs[0] >= 0 and signs[1] >= 0 and (turn != 0 or signs[2] < 0)


def first_contact(A, B, ma, mb):
    """Independent complete event partition plus G0 rational interval probes."""
    inputs = tuple(x for ring in (A, B) for point in ring for x in point)
    inputs += tuple(x for spec in (ma, mb) for x in (spec[0], *spec[1], *spec[2]))
    assert all(isinstance(x, (int, F)) and not isinstance(x, bool) for x in inputs), \
        "oracle inputs must be exact int/Fraction values"
    state = overlap(A, B)
    if state == 1:
        return {"initial": state, "status": "initial_overlap", "root": None,
                "incidences": set(), "features": set(), "probes": [], "max_degree": 0}
    events, candidates = [], []
    for P, Q, mp, mq, tag in ((A, B, ma, mb, "VE"), (B, A, mb, ma, "EV")):
        for i, vertex in enumerate(P):
            for j, start in enumerate(Q):
                polys = event_polynomials(vertex, start, Q[(j+1) % len(Q)], mp, mq)
                orientation, g, h = polys
                event = (tag, i, j, polys)
                events.append(event)
                possible = roots(orientation) if orientation != (0,) else distinct(
                    roots(g)+roots(h)+[Root.rational(0), Root.rational(1)])
                candidates.extend(t for t in possible if t.sign(g) >= 0 and t.sign(h) >= 0)
    times = distinct(candidates)
    first = Root.rational(0) if state == 0 else (times[0] if times else None)
    labels, covers = set(), set()
    if first is not None:
        for tag, i, j, (f, g, h) in events:
            if first.sign(f) or first.sign(g) < 0 or first.sign(h) < 0:
                continue
            label = (tag, i, j) if tag == "VE" else (tag, j, i)
            labels.add(label)
            P, Q, mp, mq = (A, B, ma, mb) if tag == "VE" else (B, A, mb, ma)
            if normal_cone(first, P, i, Q, j, mp, mq):
                covers.add(label)
            for k, bound in ((j, g), ((j+1) % len(Q), h)):
                if first.sign(bound) == 0:
                    vv = ("VV", i, k) if tag == "VE" else ("VV", k, i)
                    labels.add(vv)
                    covers.add(vv)
    # Every open interval between valid VE roots has constant body state.
    # Independently classify one rational point in *every* such interval.
    cuts = distinct([Root.rational(0)]+times+[Root.rational(1)])
    probes = []
    for left, right in zip(cuts, cuts[1:]):
        while left.hi >= right.lo:
            left.refine()
            right.refine()
        s = (left.hi+right.lo)/2
        probes.append((s, overlap(ring_at(A, ma, s), ring_at(B, mb, s))))
    if state == -1:
        for s, body_state in probes:
            if first is None or first.sign((-s, 1)) > 0:
                assert body_state == -1, "independent interval partition excludes earlier contact"
    return {"initial": state, "status": "contact" if first is not None else "no_contact",
            "root": first, "incidences": labels, "features": covers, "probes": probes,
            "max_degree": max(len(p)-1 for _, _, _, polys in events for p in polys)}


def certificate_root(certificate):
    if certificate.get("rational") is not None:
        return Root.rational(F(certificate["rational"]))
    p = tuple(F(x) for x in certificate["polynomial"])
    lo, hi = (F(x) for x in certificate["interval"])
    return Root(p, lo, hi)
