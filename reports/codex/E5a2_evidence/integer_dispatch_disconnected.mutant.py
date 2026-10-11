def fraction_vectors(a, b):
    """True only for the six builtin Fraction coordinates used by the fast path."""
    return False and (len(a) == 3 and len(b) == 3
            and type(a[0]) is Fraction and type(a[1]) is Fraction and type(a[2]) is Fraction
            and type(b[0]) is Fraction and type(b[1]) is Fraction and type(b[2]) is Fraction)
