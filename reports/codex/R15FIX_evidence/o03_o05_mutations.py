"""Rerun actual internal mutations without touching production files."""
from pathlib import Path
from fractions import Fraction as F
import json
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'tests')]
import pytest
import test_r15fix_geometry as T


cases = [
    ('O03', T.M, 'margin_contacts',
     'return [MarginContact((PENETRATING,), 0.0, gap, None, None, None,\n'
     '                              delta >= 0, Fraction(0))]',
     'return [MarginContact((PENETRATING,), 0.0, 0.0 - delta, None, None, None)]',
     lambda: T._assert_penetration_certificate(F(2)**-2000),
     'penetration output must carry exact distance/closed certificates'),
    ('O05', T.I, 'escape_height_covers',
     'height_display_overflow=math.isinf(display)', 'height_display_overflow=False',
     lambda: T._assert_escape_display(T.MAX+1),
     'finite exact root needs explicit upward-display overflow marker'),
    ('SCAN_BRUTE', T.I, 'escape_height_brute',
     'if result.height_display_overflow:', 'if False:',
     T.test_r15_scan_bare_escape_reference_cannot_drop_overflow_marker, 'DID NOT RAISE'),
    ('SCAN_PROFILE_CERTIFICATE', T.I, 'dilatancy_profile',
     '"height_display_overflow": sol.height_display_overflow', '"height_display_overflow": False',
     T.test_r15_scan_profile_keeps_exact_root_and_overflow_certificate,
     'profile must propagate exact root and overflow certificate'),
    ('SCAN_PROFILE_DIFFERENCE', T.I, 'dilatancy_profile',
     "F(out[i + 1]['exact_height']) - F(out[i - 1]['exact_height'])",
     "F(out[i + 1]['h']) - F(out[i - 1]['h'])",
     T.test_r15_scan_profile_differences_exact_roots_before_rounding,
     'affine top-plane slope survives common-height cancellation'),
    ('SCAN_PROFILE_OFFSET', T.I, 'dilatancy_profile',
     'off = tuple(F(d) * F(component) for component in direction)',
     'off = tuple(d * component for component in direction)',
     T.test_r15_scan_profile_offset_retains_complete_exact_product,
     'exact offset product must not collapse distinct sample points'),
]

results = []
for name, module, function, before, after, gate, expected in cases:
    gate()
    with pytest.MonkeyPatch.context() as monkeypatch:
        T._mutate(monkeypatch, module, function, before, after)
        try:
            gate()
        except BaseException as error:
            assert expected in str(error), (name, str(error))
            result = {'id': name, 'function': f'{module.__name__}.{function}',
                      'removed': before, 'inserted': after,
                      'mutation_killed': True, 'failed_assertion': expected,
                      'error_type': type(error).__name__, 'actual_error': str(error)}
        else:
            raise AssertionError(f'{name}: mutation survived')
    gate()
    results.append(result)
    print(f'{name}: KILLED at {expected}')

output = Path(__file__).with_suffix('.json')
output.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'{len(results)} actual internal mutations killed; unmodified gates pass before and after')
