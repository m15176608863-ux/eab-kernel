"""Consolidate provenance, test migration and required mutation evidence."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
def read(name):
    return json.loads((OUT/name).read_text(encoding='utf-8-sig'))
def write(name,value):
    (OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')

entries=[]
for filename in ['root_test_rewrites.json','geom_test_ledger.json','covers_test_rewrites.json',
                 'filters_test_ledger.json','frozen_test_ledger.json','g2_test_rewrites.json',
                 'invariance_interlock_ledger.json']:
    data=read(filename)
    items=data if isinstance(data,list) else data['entries']
    for item in items:
        entries.append(dict(source_ledger=filename,**item))
write('test_rewrites.json',dict(policy='No test deletion, no new skip/xfail; exact oracle replaces false ideal-boundary invariance, all original cells retained except explicitly audited exact-preserving construction changes.',entries=entries))

def test_names(source):
    tree=ast.parse(source)
    return {node.name for node in ast.walk(tree) if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name.startswith('test_')}
def skips(source):
    tree=ast.parse(source)
    return sum(1 for node in ast.walk(tree) if isinstance(node,ast.Attribute) and node.attr in ('skip','skipif','xfail'))
audit=[]
with zipfile.ZipFile(OUT/'tmp/pre_e5a.zip') as z:
    for name in z.namelist():
        if not name.startswith('tests/') or not name.endswith('.py'): continue
        target=ROOT/name
        old=z.read(name).decode('utf-8-sig')
        new=target.read_text(encoding='utf-8-sig') if target.exists() else ''
        audit.append(dict(file=name,deleted_tests=sorted(test_names(old)-test_names(new)),
                          added_tests=sorted(test_names(new)-test_names(old)),
                          old_skip_xfail_references=skips(old),new_skip_xfail_references=skips(new),
                          changed=old!=new))
write('test_inventory_audit.json',dict(all_old_test_functions_preserved=all(not r['deleted_tests'] for r in audit),
      no_new_skip_xfail_references=all(r['new_skip_xfail_references']<=r['old_skip_xfail_references'] for r in audit),files=audit))
assert all(not r['deleted_tests'] and r['new_skip_xfail_references']<=r['old_skip_xfail_references'] for r in audit)

raw=json.loads((ROOT/'reports/codex/inputs/g6e_findings_raw.json').read_text(encoding='utf-8-sig'))['findings']
dispositions=[]
def finding(idx,status,before,after,gate,note):
    item=raw[idx]
    dispositions.append(dict(raw_index_zero_based=idx,file=item['file'],old_line=item['line'],severity=item['severity'],
      initial_head='a47933682d9764b15e20d7200a6a37a1e8f14aee',disposition=status,before_evidence=before,
      after_evidence=after,gate=gate,notes=note))
finding(23,'PARTIAL_NOT_CLOSED','geom_before.json','geom_dispositions.json',
 'tests/test_geom3_e5a.py::test_exact_segment_crossing_requires_the_point_to_be_inside_the_face',
 'Original legacy counts reproduced:8/40 at1e6,5/40 at4e6. New exact segment/triangle API and both extent teeth exist, but legacy public overlap/segment entries retain heuristics. Ideal transformed contact is not exact coplanarity of rounded inputs; no exemption or false repair claim.')
finding(30,'FIXED','geom_before.json','geom_after.json',
 'tests/test_geom3_e5a.py::test_g6e_near_parallel_oracle_uses_consistent_exact_distance',
 'Before exact4.579391932681403e-9 versus float4.579515276060437e-9 caused RuntimeError. Exact squared-distance coupled branch and scaled sqrt now agree; disabling branch kills target assertion.')
finding(43,'FIXED','covers_before.json','covers_after.json',
 'tests/test_covers3_e5a.py::test_g6e_simplex_barycentric_noise_cannot_delete_a_true_e_vertex',
 'Four original roof vertex pairs returned no intersection before. Exact corrective simplex/KKT and Gordan now keep all. Restored absolute barycentric and float cone cutoffs both killed.')
finding(28,'ELIMINATED_BY_EXACT_SUPPORT','g03_baseline.json','g03_after.json',
 'tests/test_g03_e5a.py::test_fifth_round_ratio_yaw_inputs_have_zero_exemptions',
 'All four ratio/yaw/rotation reproduction cases were false red before, now pass with zero ambiguities and134/138 mandatory boundary samples; triangle-normal noise band removed.')
finding(41,'ELIMINATED_BY_EXACT_SUPPORT','g03_baseline.json','g03_after.json',
 'tests/test_g03_e5a.py::test_fifth_round_original_roof_input_is_not_flattened_by_support_bands',
 'Original roof yaw10^-8.75 false-red input rerun without changing geometry. No hull thickness, support band, sliver or ambiguous logic remains.')
finding(42,'ELIMINATED_BY_EXACT_SUPPORT','g03_baseline.json','g03_after.json',
 'tests/test_g03_e5a.py::test_fifth_round_original_chamfer_has_no_fitted_nonplanar_support',
 'Original off-axis tetra apex and chamfer tested at0,100,1e3,1e4,1e6. Nonplanar plane fitting deleted; support membership uses exact scalar equality.')
finding(39,'FIXED','g03_baseline.json','g03_after.json',
 'tests/test_g03_e5a.py::test_default_facet_vote_has_no_undefined_resolution_scale',
 'Start HEAD default eps=None raised NameError L. eps is compatibility-only and unused by exact comparator; default path now valid.')
finding(38,'ELIMINATED_BY_ZERO_EXEMPTIONS','g03_baseline.json','g03_after.json',
 'tests/test_g03_e5a.py::test_g0_vote_three_rejects_false_local_vertices_instead_of_low_e_exemption',
 'Initial every-pair-is-a-vertex mutation passed with24 exemptions. Same semantic mutation now produces24 true mismatches, passed=False, ambiguous=0.')
finding(49,'ELIMINATED_BY_ZERO_EXEMPTIONS','g03_raw49_baseline.json','g03_final.log',
 'tests/test_g03_e5a.py; tests/test_invariance_geom.py::test_vote_two_ambiguity_band_is_pinned_on_the_generic_cells',
 'Initial truncated-cube loc2glob0amb3drop2 reproduced.4->400ptol mutation escapes the four original targeted cells; no claim to rerun all2955. Widths removed entirely; exact gates forbid all skipped/dropped/ambiguous counts.')
finding(45,'ELIMINATED_BY_EXACT_CERTIFICATE',['geom_g6e271_baseline.log','geom_g6e271_mutant.log'],'geom_dispositions.json',
 'tests/test_hull_robustness.py::test_exact_convexity_oracle_catches_a_point_the_build_was_made_to_ignore',
 'Initial185-test hull group stays green with production fn*100, reproducing escape. Noise certificate replaced with exact all-input support certificate; real ignored2^-80 outside point is caught.')
write('g6e_dispositions.json',dict(scope='Ten explicitly assigned fifth-round locations. Other nearby cover findings are improved by exact predicates but not claimed individually closed without a full baseline replay.',findings=dispositions))

mutations=[]
mutations.append(dict(family='orient3d bound/10',evidence='filters_mutation.json',**read('filters_mutation.json')))
for r in read('geom_mutations_final.json'): mutations.append(dict(family=r['mutated_function'],evidence='geom_mutations_final.json',**r))
for r in read('covers_mutations.json'): mutations.append(dict(family=r['mutation'],evidence='covers_mutations.json',killed=r['exit_code']==1,**r))
for r in read('g03_mutations.json'): mutations.append(dict(family=r['id'],evidence='g03_mutations.json',**r))
write('mutations.json',dict(all_listed_internal_mutants_killed=all(m['killed'] for m in mutations),
 note='The legacy extent mutant was killed too; this does not close its remaining noise semantics. No output-postprocessing fake data counted. Historical escaped mutants recorded separately in dispositions.',mutations=mutations))

changed=subprocess.check_output(['git','diff','--name-only','--diff-filter=ACMRT'],cwd=ROOT).decode().splitlines()
untracked=subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=ROOT).decode().splitlines()
delivery=sorted({p for p in changed+untracked if '/tmp/' not in p and Path(p).name not in ('manifest.json','artifact_index.md','changed_files.json')})
write('changed_files.json',dict(files=[dict(path=p,url=(ROOT/p).as_uri(),sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest()) for p in delivery if (ROOT/p).is_file()]))
files=[p for p in OUT.rglob('*') if p.is_file() and 'tmp' not in p.relative_to(OUT).parts and p.name not in ('manifest.json','artifact_index.md')]
write('manifest.json',{p.relative_to(ROOT).as_posix():dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(files)})
index=['# E5a 证据索引','', '完整实现边界和最终结果以总报告为准；`tmp/` 包含冻结备份、隔离突变与中间复现，未删除原夹具。','',
       f'[工作树]({ROOT.as_uri()}) · [全部交付文件与哈希]({(OUT/"changed_files.json").as_uri()}) · [临时证据目录]({(OUT/"tmp").as_uri()})','', '## 源码、测试与文档','']
for name in delivery:
    if not name.startswith('reports/codex/E5a_evidence/'):
        index.append(f'- [{name}]({(ROOT/name).as_uri()})')
index.extend(['','## 证据',''])
for p in sorted(files):
    index.append(f'- [{p.name}]({p.as_uri()})')
(OUT/'artifact_index.md').write_text('\n'.join(index)+'\n',encoding='utf-8')
print(f'ledger entries={len(entries)}; preserved test files={len(audit)}; required findings={len(dispositions)}; mutants={len(mutations)}')
