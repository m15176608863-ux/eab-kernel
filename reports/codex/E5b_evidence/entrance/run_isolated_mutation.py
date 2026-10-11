from pathlib import Path
import sys
sys.path.insert(0,'src')
import eab.kernel3d.entrance3 as E
s=Path(E.__file__).read_text(encoding='utf8')
old='return (previous + t) / 2'
assert s.count(old)==1
exec(compile(s.replace(old,'return float((previous + t) / 2)'),E.__file__,'exec'),E.__dict__)
import pytest
raise SystemExit(pytest.main(['tests/test_entrance3_exact.py::test_preceding_event_probe_is_strictly_inside_the_exact_interval','-q','-p','no:cacheprovider','--basetemp','reports/codex/E5b_evidence/tmp/isolated_predecessor']))
