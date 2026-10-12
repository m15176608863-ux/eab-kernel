from pathlib import Path
p=Path('src/eab/limit.py')
with p.open(encoding='utf-8',newline='') as f:s=f.read()
nl='\r\n' if '\r\n' in s else '\n'
s=s.replace('\r\n','\n')
s=s.replace('from .lp import OPTIMAL, UNBOUNDED, _fl, maximize','from .lp import OPTIMAL, UNBOUNDED, _fl, maximize\nfrom .construction import sqrt_rational')
s=s.replace('''        n = sum((v / m) ** 2 for v in self.normal) ** 0.5
        self.normal = tuple(v / m / n for v in self.normal)''','''        exact = tuple(map(Fraction, self.normal))
        square = sum(v*v for v in exact)
        # Model directions are rounded only after the complete normalization.
        # In particular v/m/n can round a representable subnormal component
        # twice; no rounded norm or scaled component is an intermediate here.
        self.normal = tuple((-1 if v < 0 else 1)*sqrt_rational(v*v/square) for v in exact)''')
start=s.index('def _norm(v) -> float:');end=s.index('\n\nclass _ExactFloat',start)
s=s[:start]+'''def _norm(v) -> float:
    """Checked final root for finite report inputs; explicit infinities stay reports.

    No scaling division is rounded before the final norm. A finite supplied
    vector whose exact norm is outside binary64 range raises, rather than
    creating a spurious infinity/zero in the report.
    """
    if any(not math.isfinite(x) for x in v):
        return math.hypot(*v)
    return sqrt_rational(sum(Fraction(x)**2 for x in v))
''' + s[end:]
with p.open('w',encoding='utf-8',newline='') as f:f.write(s.replace('\n',nl))
