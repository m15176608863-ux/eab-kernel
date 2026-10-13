"""Normalize original finding numbers: geometry zero-based, mechanics one-based."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]
E = ROOT / 'review/evidence'
raw = json.loads((ROOT / 'reports/codex/inputs/g6e_findings_raw.json').read_text(encoding='utf-8-sig'))['findings']
runs = json.loads((E / 'root_replay_results.json').read_text(encoding='utf-8'))
by_name = {Path(x['script']).name: x for x in runs}
rows = []
for x in json.loads((E / 'geometry_g6e_replay.json').read_text(encoding='utf-8')):
    number = x['raw_index'] + 1
    run = by_name[Path(x['script']).name]
    rows.append(dict(original_number_one_based=number, supplied_index=x['raw_index'], supplied_base=0,
                     original_file=raw[number-1]['file'], original_summary=raw[number-1]['summary'],
                     script=run['script'], root_exit_code=run['exit_code'],
                     root_verified_output=run['stdout'], root_log=run['log'],
                     current_assessment='旧错误未再现；输出具体语义/新模型限界见几何覆盖报告。'))
for x in json.loads((E / 'mechanics_replays.json').read_text(encoding='utf-8')):
    number = x['raw_one_based']
    run = by_name['mechanics_replays.py']
    rows.append(dict(original_number_one_based=number, supplied_index=number, supplied_base=1,
                     original_file=raw[number-1]['file'], original_summary=raw[number-1]['summary'],
                     script=run['script'], root_exit_code=run['exit_code'],
                     root_verified_output=x['output'], root_combined_log=run['log'],
                     assertion_pass=x['pass'], current_assessment=x['label']))
rows.sort(key=lambda x: x['original_number_one_based'])
numbers = [x['original_number_one_based'] for x in rows]
assert len(numbers) == len(set(numbers)) == 25, numbers
assert all(x['root_exit_code'] == 0 for x in rows)
result = dict(original_count=50, replayed_count=len(numbers), replayed_one_based=numbers,
              not_replayed_one_based=[i for i in range(1,51) if i not in numbers],
              note='根审查方独立执行17个脚本；其中 mechanics_replays 单脚本含10条。统一原始findings[]为1-based，不混用分路索引。',
              rows=rows)
(E / 'root_g6e_replay_ledger.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
print('G6E ROOT REPLAY PASS:', len(numbers), 'distinct original one-based findings:', numbers)
