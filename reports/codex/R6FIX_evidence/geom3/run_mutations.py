"""Replay internal mutants and print the exact guarding assertion traceback."""
from contextlib import contextmanager
import importlib
import json
from pathlib import Path
import re
import sys
import traceback

ROOT = Path(__file__).resolve().parents[4]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'tests')]
import pytest

evidence = []


@contextmanager
def audited_raises(expected, *, match=None):
    try:
        yield
    except expected as error:
        if match is not None and re.search(match, str(error)) is None:
            raise
        evidence[-1]['guard'] = str(error)
        evidence[-1]['exception'] = type(error).__name__
        traceback.print_exc(file=sys.stdout)
    else:
        raise AssertionError('mutant did not reach its expected guarding assertion')


cases = [
    ('G6F-01', 'test_r6fix_geom3', 'test_g6f01_mutation_restoring_cached_alias_is_caught'),
    ('G6F-01-scan', 'test_r6fix_geom3', 'test_g6f01_mutation_returning_raw_topology_cache_is_caught'),
    ('G6F-02', 'test_r6fix_geom3', 'test_g6f02_mutation_dropping_oriented_ring_check_is_caught'),
    ('G6F-03', 'test_r6fix_geom3', 'test_g6f03_mutation_restoring_hidden_dihedral_band_is_caught'),
    ('G6F-09', 'test_r6fix_geom3', 'test_g6f09_mutation_rounding_mixed_translation_is_caught'),
    ('G6F-09-scan', 'test_r6fix_geom3', 'test_g6f09_mutation_rounding_nominal_report_before_exact_solve_is_caught'),
    ('norm-scan', 'test_r6fix_geom3', 'test_r6fix_mutation_rounding_squared_norm_is_caught'),
    ('near-parallel-existing-gate', 'test_geom3_e5a', 'test_g6e_near_parallel_legacy_parameter_mutation_is_killed'),
]

for finding, module, name in cases:
    evidence.append({'finding': finding, 'test': f'{module}::{name}'})
    print(f'\n=== INTERNAL MUTANT {finding}: {name} ===')
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(pytest, 'raises', audited_raises)
        getattr(importlib.import_module(module), name)(patch)
    assert 'guard' in evidence[-1]
    evidence[-1]['status'] = 'KILLED_BY_GUARDING_ASSERTION'
    print(evidence[-1]['status'])

Path(__file__).with_name('mutations.json').write_text(
    json.dumps(evidence, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(f'\n{len(evidence)} internal mutants killed by the intended assertion')
