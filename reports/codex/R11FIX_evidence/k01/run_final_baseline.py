"""Replay the final new semantic gates against the frozen pre-fix scanner."""
from pathlib import Path
import importlib.util
import pytest

ROOT = Path(__file__).resolve().parents[4]
path = ROOT / 'reports/codex/R11FIX_evidence/baseline/tools/check_exact_construction.py'
spec = importlib.util.spec_from_file_location('k01_frozen_baseline', path)
baseline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(baseline)

class FrozenScanner:
    def pytest_collection_modifyitems(self, items):
        for item in items:
            if item.module.__name__.endswith('test_r11fix_static_flow'):
                item.module.gate = baseline

raise SystemExit(pytest.main([
    '-q', str(ROOT / 'tests/test_r11fix_static_flow.py'),
    '-k', 'not removing',
    '--basetemp=' + str(ROOT / 'reports/codex/R11FIX_evidence/tmp/k01_final_baseline'),
], plugins=[FrozenScanner()]))
