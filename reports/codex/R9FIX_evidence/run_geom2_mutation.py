"""Internal finite-domain mutation; no production-file edits or fake outputs."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / 'src')]
import pytest
from eab.kernel2d import entrance as E
E._facet_in_domain = lambda *args: True
raise SystemExit(pytest.main(['-q', '-p', 'no:cacheprovider',
    'tests/test_r9fix_entrance_domain.py', '-k', 'collinear_support',
    '--basetemp=reports/codex/R9FIX_evidence/tmp/geom2/mutant']))
