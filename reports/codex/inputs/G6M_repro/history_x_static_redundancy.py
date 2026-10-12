"""Check the independent static gate on the same internal x-field mutant.
This is a redundancy check, not a claim that all tests stay green.
"""
from pathlib import Path
import hashlib,json,importlib.util
ROOT=Path(__file__).resolve().parents[2];folder=ROOT/'review/copies/history_current'
p=folder/'src/eab/kernel3d/entrance3.py';raw=p.read_bytes();s=raw.decode('utf-8-sig')
needle='return _restore_sources(Entrance3("entrance", scalar_rational(t), tuple(scalar_rational(_mapped_value) for _mapped_value in exact_x), rep_label,'
change='return _restore_sources(Entrance3("entrance", scalar_rational(t), tuple(scalar_rational(_mapped_value) for _mapped_value in x0), rep_label,'
assert s.count(needle)==1
spec=importlib.util.spec_from_file_location('history_gate',folder/'tools/check_exact_construction.py');gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)
baseline=gate.scan_text(s,'src/eab/kernel3d/entrance3.py',repository_root=folder)
p.write_bytes(s.replace(needle,change).encode('utf-8'))
try:
    mutant=gate.scan_text(p.read_text(encoding='utf-8-sig'),'src/eab/kernel3d/entrance3.py',repository_root=folder)
    d=dict(baseline_issues=baseline,mutant_issues=mutant,count_baseline=len(baseline),count_mutant=len(mutant),restored_sha256=hashlib.sha256(raw).hexdigest())
    print(json.dumps(d,ensure_ascii=False,indent=2))
    (ROOT/'review/logs/history_x_static_redundancy.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
finally:
    p.write_bytes(raw);assert hashlib.sha256(p.read_bytes()).digest()==hashlib.sha256(raw).digest()
