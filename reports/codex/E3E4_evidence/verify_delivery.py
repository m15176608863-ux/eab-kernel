"""Read back the final work-order artifacts, links, hashes and JUnit evidence."""
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlparse, unquote
import xml.etree.ElementTree as ET

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]

def read(name):
    return json.loads((OUT/name).read_text(encoding='utf-8-sig'))

def main():
    final=read('final_full_result.json')
    assert final['returncode']==0 and final['source_unchanged'] and not final['failures']
    for path,digest in final['sha256_before'].items():
        assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest,path
    cases=list(ET.parse(OUT/'final_full.xml').iter('testcase'))
    assert len(cases)==7729 and all(c.find(k) is None for c in cases for k in ('failure','error','skipped'))
    assert any(c.get('classname')=='tests.test_doc_pointers' for c in cases)
    audit=read('test_function_audit.json')
    assert all(audit['ledger_coverage'].values())
    assert len(read('g6e_dispositions.json'))==14
    mutations=read('mutation_results.json')['results']
    assert len(mutations)==10 and all(m['byte_restored'] for m in mutations)
    scope=read('scope_audit.json')
    assert scope['baseline_head_unchanged'] and not scope['fixture_changes'] and not scope['staged'] and not scope['diff_check']
    report=ROOT/'reports/codex/E3E4_report.md'
    text=report.read_text(encoding='utf-8')
    assert text.rstrip().endswith('E3E4_DONE') and '???' not in text
    for file in (report,OUT/'INDEX.md'):
        for url in re.findall(r'\]\((file:///[^)]+)\)',file.read_text(encoding='utf-8')):
            path=Path(unquote(urlparse(url).path).lstrip('/'))
            assert path.exists(),(file,url)
    for item in read('evidence_index.json'):
        assert hashlib.sha256((OUT/item['path']).read_bytes()).hexdigest()==item['sha256'],item['path']
    result=dict(status='PASS',junit_cases=len(cases),failed_or_skipped=0,
                last_line=final['last_line'],source_hashes_unchanged=True,
                dispositions=14,mutations=10,byte_restored=True,
                fixture_hashes_unchanged=scope['tracked_fixture_count'],
                all_modified_old_functions_have_ledger=True,
                report_links_and_evidence_hashes_verified=True,
                report_sha256=hashlib.sha256(report.read_bytes()).hexdigest())
    (OUT/'delivery_qa.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__': main()
