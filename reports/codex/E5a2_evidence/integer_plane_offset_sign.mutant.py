def _integer_plane(n, p):
    """Positive homogeneous rescaling of n.(x-p)=0; no geometry is rounded."""
    coeffs = (*n, -dot(n, p))
    den = lcm(*(c.denominator for c in coeffs))
    ints = tuple(c.numerator * (den // c.denominator) for c in coeffs)
    common = gcd(*ints)
    ints = tuple(v // common for v in ints)
    return ints, sum(v*v for v in ints[:3])
