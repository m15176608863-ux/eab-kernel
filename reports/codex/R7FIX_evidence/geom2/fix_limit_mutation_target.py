from pathlib import Path
p=Path('tests/test_r7fix_limit_construction.py')
with p.open(encoding='utf-8-sig',newline='') as f:s=f.read()
s=s.replace('from eab.limit import LimitContact, _norm','from eab.limit import LimitContact')
s=s.replace('assert _norm(vector)', 'assert limit_module._norm(vector)')
s=s.replace('        _norm((sys.float_info.max, sys.float_info.max))','        limit_module._norm((sys.float_info.max, sys.float_info.max))')
s=s.replace("monkeypatch.setattr(sys.modules[__name__], '_norm', old_norm)","monkeypatch.setattr(limit_module, '_norm', old_norm)")
with p.open('w',encoding='utf-8',newline='') as f:f.write(s)
