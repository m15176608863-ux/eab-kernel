"""Restore the old window display branch in the real function body, in memory."""
import sys,inspect,textwrap
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'src'))
import pytest
import eab.margin as M
source=textwrap.dedent(inspect.getsource(M.margin_contacts))
needle='else:\n            w = _exact.sqrt_rational(d2, allow_underflow=True)'
assert source.count(needle)==1
namespace=dict(vars(M))
exec(compile(source.replace(needle,'elif contact_window is None or not ctol:\n            w = _exact.sqrt_rational(d2, allow_underflow=True)'),
             '<r9-window-output-mutant>','exec'),namespace)
M.margin_contacts=namespace['margin_contacts']
raise SystemExit(pytest.main(['-q','-p','no:cacheprovider','tests/test_r9fix_window_distance.py',
    '-k','not rejects_restored','--basetemp=reports/codex/R9FIX_evidence/tmp/geom2/window_mutant']))
