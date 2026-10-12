"""Cross-check all historical edited/renamed gates have a manual adjudication."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'review'
def read(p):return json.loads((OUT/p).read_text(encoding='utf-8-sig'))
registry=read('gates_docs/changed_existing_tests.json')
rows=[]
for path in ('root_migration_final_pass.json','gates_docs/migration_final_pass.json'):
    for row in read(path):
        assert row['full_old_new_text_read']
        rows.append(dict(file=row['file'],old_name=row['function'],new_name=row['function'],
                         full_old_new_text_read=True,manual_adjudication=path,
                         verdict=row['verdict'],reason=row['reason']))
for row in read('geom3/migration_final_pass.json')['entries']:
    assert row['manual_full_body_read']
    rows.append(dict(file=row['file'],old_name=row['name'],new_name=row['name'],
                     full_old_new_text_read=True,manual_adjudication='geom3/migration_final_pass.json',
                     verdict=row['judgment'],reason=row['assertion_review']))
g2=read('geom2/migration_final_pass.json')
for row in g2['same_name_coverage']+g2['renamed_coverage']:
    assert row['read_old_body'] and row['read_new_body'] and row['human_semantic_judgment']
    rows.append(dict(file=row['file'],old_name=row['old_name'],new_name=row['new_name'],
                     full_old_new_text_read=True,manual_adjudication='geom2/migration_final_pass.json',
                     verdict=row['verdict'],reason=row['manual_reason']))
want={(r['file'],r['name']) for r in registry}
got={(r['file'],r['old_name']) for r in rows}
assert len(rows)==len(got)==len(want)==114 and got==want
renames=[r for r in rows if r['old_name']!=r['new_name']]
removed={(r['file'],r['name']) for r in registry if r.get('REMOVED')}
assert len(renames)==6 and {(r['file'],r['old_name']) for r in renames}==removed
result=dict(registry_count=114,same_name_count=108,renamed_with_successor_count=6,
            reviewer_partition=dict(root=18,gates_docs=20,geom3=42,geom2=34),
            registry_exactly_covered=True,all_old_new_bodies_manually_read=True,
            limitation='全文阅读及逐项裁决不等于所有可能变异等价；仅报告明确列出的真实路径变异已执行。六项REMOVED是有实际承接者的改名，不是114项之外再加6项。',
            entries=sorted(rows,key=lambda r:(r['file'],r['old_name'])))
(OUT/'migration_complete_review.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='entries'},ensure_ascii=False,indent=2))
