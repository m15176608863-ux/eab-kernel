"""Final PARTIAL-delivery checks, not a replacement for pytest."""
from pathlib import Path
import hashlib
import json
import subprocess
import xml.etree.ElementTree as ET

E=Path(__file__).resolve().parent
ROOT=E.parents[2]
run=json.loads((E/'final.json').read_text(encoding='utf-8'))
cases=list(ET.parse(E/'final.xml').getroot().iter('testcase'))
new=[c for c in cases if c.attrib['classname'].startswith('tests.test_e5a2_')]
bad=lambda c:c.find('failure') is not None or c.find('error') is not None
assert len(cases)==8002 and sum(map(bad,cases))==49
assert len(new)==95 and not any(map(bad,new))
current={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
         for top in ('src','tests','tools') for p in sorted((ROOT/top).rglob('*.py'))}
assert current==run['source_before']==run['source_after']
diff=subprocess.run(['git','diff','--check'],cwd=ROOT,text=True,encoding='utf-8',capture_output=True)
(E/'diff_check.log').write_text(diff.stdout+diff.stderr,encoding='utf-8')
assert diff.returncode!=0 and diff.stdout.strip()=='tests/test_geom3_overlap_witness.py:389: new blank line at EOF.'
status=subprocess.check_output(['git','status','--short'],cwd=ROOT,text=True,encoding='utf-8')
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
branch=subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()
assert head=='5b09ea399a5277f359f833312638c9bb86f09192' and branch=='codex-work'
record=dict(outcome='PARTIAL',tests=8002,passed=7953,failed=49,new_tests_passed=95,
            original_nodes_preserved=7907,source_matches_full_suite=True,head=head,branch=branch,
            diff_check=dict(exit_code=diff.returncode,message=diff.stdout.strip(),
                            note='Single whitespace warning retained rather than changing frozen tested bytes.'),
            full_suite_is_not_green=True,performance_target_not_met=True,status=status)
(E/'final_delivery_qa.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(record,ensure_ascii=False,indent=2))
