"""G6J: ordinary intraprocedural premature-rounding AST bypass."""
from pathlib import Path
from fractions import Fraction as F
import importlib.util, math, sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
from eab.construction import scalar_rational, sqrt_rational, norm_rational, vector_rational
spec=importlib.util.spec_from_file_location('gate',ROOT/'tools/check_exact_construction.py')
gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)

snippets={
    'sqrt_keyword': 'def bad(q):\n    return sqrt_rational(value=scalar_rational(q))\n',
    'norm_keyword': 'def bad(q):\n    return norm_rational(values=vector_rational(q))\n',
    'fraction_barrier': 'def bad(q):\n    return sqrt_rational(Fraction(scalar_rational(q)))\n',
    'map_fraction_barrier': 'def bad(q):\n    return norm_rational(tuple(map(Fraction, vector_rational(q))))\n',
    'local_loop': 'def bad(q):\n    v = vector_rational(q)\n    square = Fraction(0)\n    for x in v:\n        square += x*x\n    return sqrt_rational(square)\n',
    'local_append': 'def bad(q):\n    v = []\n    v.append(scalar_rational(q))\n    return sqrt_rational(v[0])\n',
    'augmented_subtraction': 'def bad(a,b):\n    a = scalar_rational(a)\n    b = scalar_rational(b)\n    a -= b\n    return a\n',
}
scope={'Fraction':F,'scalar_rational':scalar_rational,'sqrt_rational':sqrt_rational,
       'norm_rational':norm_rational,'vector_rational':vector_rational}
mid=(F(1)+F(math.nextafter(1.,math.inf)))/2
q=mid*mid+F(2)**-200
for name,source in snippets.items():
    issues=gate.scan_text(source,'src/eab/injected_review.py')
    namespace=dict(scope);exec(source,namespace)
    if name in {'fraction_barrier','local_append','sqrt_keyword'}:
        actual=namespace['bad'](q)
        wanted=math.nextafter(1.,math.inf)
        squared_lower=((F(1)+F(wanted))/2)**2
        assert q>squared_lower
    elif name=='augmented_subtraction':
        a,b=F(1)+F(2)**-53,F(1)
        actual=namespace['bad'](a,b);wanted=2.**-53
    else:
        vector=(F(1)+F(2)**-53,F(2)**-27)
        actual=namespace['bad'](vector);wanted=math.nextafter(1.,math.inf)
        # Independent midpoint proof of the final norm rounding.
        square=sum(x*x for x in vector)
        assert square>mid*mid and square<((F(wanted)+F(math.nextafter(wanted,math.inf)))/2)**2
    print(name,'AST_issues=',issues,'actual=',actual.hex(),'expected=',wanted.hex())
    assert not issues and actual!=wanted
print('STATIC_FRACTION_BARRIER CONFIRMED: 7 silent wrong constructions bypass scanner')
