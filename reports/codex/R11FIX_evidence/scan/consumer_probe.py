"""Repeat the existing 13 generator consumer and 5 allowed-path probes."""
from pathlib import Path
import importlib.util
import json

ROOT=Path(__file__).resolve().parents[4]

def main():
    spec=importlib.util.spec_from_file_location('r11_scanner',ROOT/'tools/check_exact_construction.py')
    scanner=importlib.util.module_from_spec(spec);spec.loader.exec_module(scanner)
    consumers=['return tuple(g)','return [*g]','return unknown(g)','return next(g)',
               'return g.__next__()','for _ in g:\n        pass','return list(map(abs,g))',
               'return tuple(x for x in g)','return 0 in g','return sum(g)','return any(g)',
               'h=[g]\n    return next(h[0])','return unknown(*g)']
    rows=[]
    for consumer in consumers:
        source=('def bad(q):\n    root=sum\n'
                '    g=(root(vector_rational(q)) for _ in (1,))\n'
                '    root=norm_rational\n    '+consumer+'\n')
        issues=scanner.scan_text(source,'src/eab/generator_consumer.py')
        rows.append({'consumer':consumer,'source':source,'expect':'rounded-vector',
                     'issues':issues,'passed':any(row[3]=='rounded-vector' and row[1]==3 for row in issues)})
    negatives={
        'container_is_not_consumption':'root=sum\n    g=(root(vector_rational(q)) for _ in (1,))\n    root=norm_rational\n    h=[g]\n    return tuple(h)',
        'exhausted_tuple_is_not_reexecution':'root=sum\n    g=(root(vector_rational(q)) for _ in (1,))\n    result=tuple(g)\n    root=norm_rational\n    return tuple(result)',
        'captured_iterable_binding_is_stable':'root=sum\n    g=(saved for saved in [root])\n    root=norm_rational\n    saved=next(g)\n    return saved(vector_rational(q))',
        'ordinary_alias_strong_rebinding':'root=norm_rational\n    root=sum\n    return root(vector_rational(q))',
        'comprehension_scope_is_private':'root=norm_rational\n    [root for root in [sum]]\n    return root(q)',
    }
    for name,body in negatives.items():
        source='def good(q):\n    '+body+'\n'
        issues=scanner.scan_text(source,'src/eab/generator_consumer.py')
        rows.append({'consumer':name,'source':source,'expect':'none','issues':issues,'passed':not issues})
    payload={'count':len(rows),'failed':sum(not row['passed'] for row in rows),'results':rows}
    Path(__file__).with_name('static_consumer_and_negative_results.json').write_text(
        json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(payload,ensure_ascii=False,indent=2))
    return bool(payload['failed'])

if __name__=='__main__':
    raise SystemExit(main())
