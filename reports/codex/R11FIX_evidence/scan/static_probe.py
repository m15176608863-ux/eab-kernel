"""Run precise local CFG probes, with no appended fallback root invocation."""
from pathlib import Path
import importlib.util
import json
import sys
import time

ROOT=Path(__file__).resolve().parents[4]
EVIDENCE=Path(__file__).parent

def main():
    spec=importlib.util.spec_from_file_location('r11_independent_scanner',ROOT/'tools/check_exact_construction.py')
    scanner=importlib.util.module_from_spec(spec);spec.loader.exec_module(scanner)
    cases=json.loads((EVIDENCE/'static_baseline_probes.json').read_text(encoding='utf8'))
    cases.extend([
        {'case':'import_scope_independence','source':
         'from eab.construction import norm_rational as build\n'
         'def bad(q):\n    return build(vector_rational(q))\n'
         'def safe():\n    from builtins import abs as build\n'},
        {'case':'with_suppressed_exception','source':
         'from contextlib import suppress\n'
         'def bad(q):\n    root=norm_rational\n'
         '    with suppress(ValueError):\n        raise ValueError()\n        root=abs\n'
         '    return root(vector_rational(q))\n'},
        {'case':'loop_heap_allocation_summary','rule':'rounded-root','source':
         'def bad(q):\n    old=None\n'
         '    for _ in range(2):\n        new=[]\n'
         '        if old is not None:\n            return sqrt_rational(old[0])\n'
         '        new.append(scalar_rational(q))\n        old=new\n'},
        {'case':'loop_backedge_callsite_only','source':
         'def bad(q):\n    root=abs\n    saved=abs\n'
         '    for _ in range(3):\n        saved(vector_rational(q))\n'
         '        saved=root\n        root=norm_rational\n'},
        {'case':'loop_backedge_container_callsite_only','source':
         'def bad(q):\n    root=abs\n    box=[abs]\n'
         '    for _ in range(3):\n        box[0](vector_rational(q))\n'
         '        box=[root]\n        root=norm_rational\n'},
        {'case':'comprehension_backedge_only','source':
         'def bad(q):\n    root=abs\n    saved=abs\n'
         '    [(saved(vector_rational(q)), (saved:=root), (root:=norm_rational)) for _ in range(3)]\n'},
    ])
    # This file preserves the first recheck outputs, but every stored source is
    # rerun here against the current scanner instead of trusting those outputs.
    extensions=EVIDENCE/'static_review_extensions.json'
    if extensions.exists():
        cases.extend(json.loads(extensions.read_text(encoding='utf8')))
    # Final targeted recheck only: assert success/failure and ordered dict
    # key/value (including **unpacking); these were confirmed after first freeze.
    cases.extend([
        {'case':'assert_success_skips_message','source':
         'def bad(q):\n    root=norm_rational\n'
         '    assert True, (root:=abs)\n    return root(vector_rational(q))\n'},
        {'case':'assert_failure_evaluates_message','source':
         'def bad(q):\n    root=abs\n    try:\n'
         '        assert False, (root:=norm_rational)\n'
         '    except AssertionError:\n        pass\n    return root(vector_rational(q))\n'},
        {'case':'dict_interleaved_values','source':
         'def bad(q):\n    root=norm_rational\n'
         '    d={"x":root(vector_rational(q)), (root:=abs):1}\n    return d\n'},
        {'case':'dict_unpack_order','source':
         'def bad(q):\n    root=norm_rational\n'
         '    d={**{"x":root(vector_rational(q))}, (root:=abs):1}\n    return d\n'},
    ])
    start=time.perf_counter();result=[]
    for case in cases:
        issues=scanner.scan_text(case['source'],'src/eab/k01_independent_injected.py')
        rule=case.get('rule','rounded-vector')
        result.append({'case':case['case'],'source':case['source'],'expected_rule':rule,
                       'issues':issues,'missed':not any(row[3]==rule for row in issues)})
    output=Path(sys.argv[1]) if len(sys.argv)>1 else EVIDENCE/'static_probe_results.json'
    payload={'elapsed_seconds':time.perf_counter()-start,'count':len(result),
             'missed':sum(row['missed'] for row in result),'results':result}
    output.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(payload,ensure_ascii=False,indent=2))
    return bool(payload['missed'])

if __name__=='__main__':
    raise SystemExit(main())
