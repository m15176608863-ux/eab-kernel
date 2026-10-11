def dot(a, b):
    d0 = a[0].denominator * b[0].denominator
    d1 = a[1].denominator * b[1].denominator
    d2 = a[2].denominator * b[2].denominator
    den = lcm(d0, d1, d2)
    num = (a[0].numerator * b[0].numerator * (den // d0)
           + a[1].numerator * b[1].numerator * (den // d1)
           - a[2].numerator * b[2].numerator * (den // d2))
    return Fraction(num, den)
