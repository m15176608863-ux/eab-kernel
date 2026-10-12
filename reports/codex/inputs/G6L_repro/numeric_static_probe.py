from pathlib import Path
import sys,importlib.util,json
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('gate',ROOT/'tools/check_exact_construction.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
bodies={
'map_norm':'return tuple(map(norm_rational, [vector_rational(p, allow_underflow=True)]))[0], noise',
'map_sqrt':'return tuple(map(sqrt_rational, [scalar_rational(sum(x*x for x in p), allow_underflow=True)]))[0], noise',
'iter_alias':'root = next(iter([norm_rational]))\n    return root(vector_rational(p, allow_underflow=True)), noise',
'lambda_late':'root = abs\n    f = lambda: root(vector_rational(p, allow_underflow=True))\n    root = norm_rational\n    return f(), noise',
'zip_norm':'root = next(zip([norm_rational]))[0]\n    return root(vector_rational(p, allow_underflow=True)), noise',
'pop_alias':'box = [norm_rational]\n    root = box.pop()\n    return root(vector_rational(p, allow_underflow=True)), noise',
'reduce_alias':'from functools import reduce\n    root = reduce(lambda x,y:x,[norm_rational])\n    return root(vector_rational(p, allow_underflow=True)), noise',
}
print(json.dumps({name:g.scan_text('def bad(p, noise):\n    '+body+'\n','src/eab/numeric_injected.py') for name,body in bodies.items()},indent=2))
