"""Verify final audit structure, evidence paths, counts and stored hashes."""
from pathlib import Path
import hashlib
import json
import re
from urllib.parse import unquote

ROOT=Path(__file__).resolve().parents[2]
REV=ROOT/'review'
d=json.loads((REV/'G6N_findings.json').read_text('utf-8'))
report=(REV/'G6N_report.md').read_text('utf-8')
assert '\ufffd' not in report
assert len({f['id'] for f in d['findings']})==len(d['findings'])
counts={s:sum(f['severity']==s for f in d['findings']) for s in ('critical','major','minor')}
assert counts==d['confirmed_counts']
sentinel='G6N_DONE critical={critical} major={major} minor={minor}'.format(**counts)
assert report.strip().splitlines()[-1]==sentinel
required={'severity','file:line','conclusion','failure_scenario','how_to_reproduce','suggested_fix','verified_output','repro_path'}
for f in d['findings']:
    assert required<=f.keys(), (f['id'],required-f.keys())
    assert f['primary_verified'] is True
    assert (ROOT/f['repro_path']).is_file()
    assert (ROOT/f['file']).is_file()
    assert (ROOT/f['verified_log']).is_file()
    assert f['verified_output'].strip()
hrefs=[]
for name in ('G6N_report.md','ARTIFACTS.md'):
    for uri in re.findall(r'\]\((file:///[^)]+)\)',(REV/name).read_text('utf-8')):
        p=Path(unquote(uri[len('file:///'):]))
        assert p.exists(), (name,str(p))
        hrefs.append(uri)
manifest=json.loads((REV/'ARTIFACTS.json').read_text('utf-8'))
for row in manifest['artifacts']:
    p=ROOT/row['path']
    assert p.stat().st_size==row['bytes'],row['path']
    assert hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256'],row['path']
qa={'json_parsed':True,'required_finding_fields':True,'primary_verified_all':True,
    'confirmed_counts':counts,'report_final_line':sentinel,
    'local_links_checked':len(hrefs),'artifact_hashes_checked':len(manifest['artifacts']),
    'all_checks_passed':True}
(REV/'evidence/deliverable_qa.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2),encoding='utf-8')
print('DELIVERABLE_QA_PASS',counts,'links=',len(hrefs),'hashes=',len(manifest['artifacts']))
