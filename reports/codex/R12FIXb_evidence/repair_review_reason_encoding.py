"""Repair five explicitly reviewed UTF-8 reasons; never touch an approval pin."""
import copy
import hashlib
import json
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
policy_path = ROOT / 'tools/exact_construction_policy.json'
assert hashlib.sha256(policy_path.read_bytes()).hexdigest() == 'ea5710d7d62ddb8462def6b55cbb1103fa9876fb8423c9a046af51d1600d8729'
policy = json.loads(policy_path.read_text(encoding='utf-8'))
ledger = json.loads((HERE / 'local_review_decisions_final.json').read_text(encoding='utf-8'))
before = copy.deepcopy(ledger['decisions'])
repair_path = HERE / 'src_reason_utf8_corrections.json'
assert hashlib.sha256(repair_path.read_bytes()).hexdigest() == 'c8478ac47c9a1cec05eaffa72bced7796a62a6cceb7258199e3aef8569c8fcd8'
repairs = json.loads(repair_path.read_text(encoding='utf-8'))['corrections']
assert {r['id'] for r in repairs} == {'R12b-L0249','R12b-L0252','R12b-L0476','R12b-L0514','R12b-L0611'}
by_id = {r['id']: r for r in ledger['decisions']}
for r in repairs:
    assert '?' not in r['reason'] and '\ufffd' not in r['reason']
    assert any('\u4e00' <= c <= '\u9fff' for c in r['reason'])
    row = by_id[r['id']]
    assert row['reason'].count('?') > 50
    row['reason'] = r['reason']
    row['review_disposition'] = r['disposition']
    row['review_evidence'] = 'reports/codex/R12FIXb_evidence/src_reason_utf8_corrections.json'
    row['encoding_repair'] = repair_path.name
for old, new in zip(before, ledger['decisions']):
    assert all(old[k] == new[k] for k in ('id','path','function','rule','node','context','category'))
assert not any(r['reason'].count('?') >= 5 or '\ufffd' in r['reason'] for r in ledger['decisions'])
ledger['amends'] = 'local_review_decisions_final.json'
ledger['reason_encoding_repair'] = repair_path.name
destination = HERE / 'local_review_decisions_release.json'
assert not destination.exists()
destination.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='')
policy['waivers'] = [{k:r[k] for k in ('id','path','function','rule','node','context','category','reason','review_evidence')} for r in ledger['decisions']]
policy_path.write_text(json.dumps(policy,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='')
stats = json.loads((HERE / 'local_manifest_statistics_final.json').read_text(encoding='utf-8'))
stats['by_disposition'] = dict(Counter(r['review_disposition'] for r in ledger['decisions']))
stats['representatives'] = {c:[r for r in ledger['decisions'] if r['category']==c][:2] for c in stats['by_category']}
stats['reason_encoding_repairs'] = 5
(HERE / 'local_manifest_statistics_release.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='')
result = {'policy_sha256':hashlib.sha256(policy_path.read_bytes()).hexdigest(),
          'ledger_sha256':hashlib.sha256(destination.read_bytes()).hexdigest(),
          'scope_hashes_refreshed':0,'node_changes':0,'waivers_added_or_removed':0,
          'corrected_reason_ids':[r['id'] for r in repairs], 'replacement_characters_or_corrupt_question_mark_runs':0}
(HERE / 'reason_encoding_repair_receipt.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result))
