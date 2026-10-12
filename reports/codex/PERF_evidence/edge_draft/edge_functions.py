"""DRAFT ONLY: replace the two edge functions, add _integer_ray above them.

The existing cache keeps the SAME five arguments and maxsize. Only its payload
is changed. This file is not imported by production or pytest collection.
"""


def _integer_ray(v):
    """Exact positive rescaling of a Fraction/integer vector; preserve all signs."""
    den = lcm(*(c.denominator for c in v))
    result = tuple(c.numerator * (den // c.denominator) for c in v)
    divisor = gcd(*result)
    return tuple(c // divisor for c in result) if divisor else result


def _qedge_contains(P, e, d, tol=0.0):
    """Exact oriented wedge; integer rays preserve the normalized-dot window.

    Each vector is multiplied by its own strictly positive rational factor.
    Signs/zeros and value**2/(norm(a)**2*norm(b)**2) therefore do not change.
    Gate: test_perf_edge_frame::test_integer_edge_frame_matches_fraction_reference.
    """
    trav = P.edge_traversals(e)
    if len(trav) != 2:
        return -1
    (f1, a, b), (f2, _, _) = trav
    t = _qedge(P, (a, b))
    n1, n2 = _qnormal(P, f1), _qnormal(P, f2)
    convex, t, h1, h2 = _qedge_frame_cached(t, n1, n2, cross, dot)
    if not convex:
        return -1
    d = _integer_ray(d)
    axial = dot(d, t)
    if _outside_dot_band(abs(axial), d, t, tol):
        return -1
    s1, s2 = dot(h1, d), dot(h2, d)
    if _outside_dot_band(-s1, h1, d, tol) or _outside_dot_band(-s2, h2, d, tol):
        return -1
    return 1 if s1 > 0 and s2 > 0 and axial == 0 else 0


@lru_cache(maxsize=8192)
def _qedge_frame_cached(t, n1, n2, cross_implementation, dot_implementation):
    """Same content/implementation key; store positive-rescaled integer rays."""
    return (dot_implementation(cross_implementation(n1, n2), t) > 0,
            _integer_ray(t),
            _integer_ray(cross_implementation(t, n1)),
            _integer_ray(cross_implementation(n2, t)))
