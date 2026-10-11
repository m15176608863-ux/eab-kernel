def _outside_dot_band(value, a, b, tol):
    """Exact comparison with an explicit dimensionless normalized-dot window."""
    if value <= 0:
        return False
    if tol <= 0:
        return True
    threshold, aa, bb = _squared_tol(tol), _qnorm2(a, dot), _qnorm2(b, dot)
    # Cross-multiply positive denominators; do not construct four intermediate
    # Fractions (or approximate the angular reporting band by a float).
    return (value.numerator**2 * threshold.denominator * aa.denominator * bb.denominator
            >= value.denominator**2 * threshold.numerator * aa.numerator * bb.numerator)
