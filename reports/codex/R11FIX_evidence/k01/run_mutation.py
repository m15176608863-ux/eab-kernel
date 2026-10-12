"""Delete one key step inside the real scanner, then run its exact watchdog."""
from pathlib import Path
import importlib.util
import sys

ROOT = Path(__file__).resolve().parents[4]
spec = importlib.util.spec_from_file_location('k01_tests', ROOT / 'tests/test_r11fix_static_flow.py')
tests = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tests)
if sys.argv[1] == 'zero_path':
    scan = tests._mutant_scan('new_head = joined(entry, head, backedge)', 'new_head = backedge or head')
    tests._assert_cone_rejected(scan, tests.LOOPS[0])
else:
    old = 'if new_head == head:\n                    break\n                head = new_head\n            # Only condition/exhaustion'
    scan = tests._mutant_scan(old, 'if True:\n                    break\n                head = new_head\n            # Only condition/exhaustion')
    source = '''def bad(q):
    root = abs
    saved = abs
    for _ in range(3):
        saved(vector_rational(q))
        saved = root
        root = norm_rational
    root = abs
    saved = abs
'''
    issues = scan(source)
    assert any(row[1:4] == (5, 'bad', 'rounded-vector') for row in issues), 'K01 loop-internal callable fixed-point assertion'
