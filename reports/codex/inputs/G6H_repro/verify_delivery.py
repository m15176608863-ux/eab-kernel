"""Read-only final artifact, evidence hash, local link and source-byte QA."""
from pathlib import Path
import json, hashlib, re, urllib.parse, subprocess, os

ROOT=Path(__file__).resolve().parents[2]
os.environ['GIT_OPTIONAL_LOCKS']='0'
def read(name):return json.loads((ROOT/name).read_text(encoding='utf8'))
data=read('review/G6H_findings.json')
assert data['counts']==dict(critical=0,major=6,minor=0)
assert data['m0_can_exit'] is False
assert data['full_suite']['mode']=='serial' and data['full_suite']['exit_code']==0
assert data['full_suite']['junit_counts']==dict(tests=9851,failures=0,errors=0,skipped=0)
required=['severity','file:line','summary','failure_scenario','how_to_reproduce','suggested_fix','verified_output']
assert len(data['findings'])==6
for row in data['findings']:
    assert all(isinstance(row[key],str) and row[key] for key in required)
    assert row['root_verified'] is True and row['verified_exit_code']==0
    assert (ROOT/row['repro_script']).is_file() and (ROOT/row['verified_log']).is_file()
    assert row['verified_output'] in (ROOT/row['verified_log']).read_text(encoding='utf8')
    assert '????' not in row['summary']
replay=read('review/G6H_regression_replay.json')
assert len(replay['g6g'])==11 and all(r['status']=='已修' for r in replay['g6g'])
assert replay['g6e_unique_replayed']==37 and len(replay['g6e'])==37
assert len(replay['g6e_not_replayed'])==13
report=(ROOT/'review/G6H_report.md').read_text(encoding='utf8')
assert '{{' not in report and report.splitlines()[-1]==data['completion_token']
assert all(row['id'] in report for row in data['findings'])
link_count=0
for name in ['review/G6H_report.md','review/README.md']:
    for url in re.findall(r'\]\((file:///[^)]+)\)',(ROOT/name).read_text(encoding='utf8')):
        p=Path(urllib.parse.unquote(urllib.parse.urlparse(url).path.lstrip('/')))
        assert p.exists(),(name,url)
        link_count+=1
index=read('review/evidence_index.json')
for row in index['files']:
    p=ROOT/row['path'];raw=p.read_bytes()
    assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256'],row['path']
baseline=read('review/baseline.json')
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,encoding='utf8').strip()==baseline['HEAD']
for name,digest in baseline['files'].items():
    assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
assert len(baseline['files'])==1910
print(json.dumps(dict(result='DELIVERY_QA_PASS',confirmed=data['counts'],
    serial_pytest=data['full_suite']['junit_counts'],g6g_replayed=11,g6e_replayed=37,
    verified_file_hashes=len(index['files']),local_links_checked=link_count,
    tracked_sha_unchanged=1910,HEAD=baseline['HEAD']),ensure_ascii=False,indent=2))
