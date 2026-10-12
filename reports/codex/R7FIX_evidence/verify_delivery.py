"""Audit tested bytes, fixture fidelity, test retention, and finding JUnit coverage."""
from pathlib import Path
import ast, datetime, hashlib, json, subprocess, xml.etree.ElementTree as ET, zipfile
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'reports/codex/R7FIX_evidence'
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(name,data): (OUT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
base=json.loads((OUT/'baseline.json').read_text(encoding='utf-8'))
snapshot=json.loads((OUT/'tested_source_snapshot.json').read_text(encoding='utf-8'))
changes=[s for s,h in snapshot['files'].items() if not (ROOT/s).is_file() or digest(ROOT/s)!=h]
fixtures=[s for s in base['sha256'] if s.startswith('fixtures/')]
fixture_changes=[s for s in fixtures if not (ROOT/s).is_file() or digest(ROOT/s)!=base['sha256'][s]]
removed=[]; modified_tests=[]
def testnames(source):
 return {n.name for n in ast.walk(ast.parse(source)) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name.startswith('test_')}
with zipfile.ZipFile(OUT/'baseline_tracked.zip') as z:
 for name in z.namelist():
  if name.startswith('tests/') and name.endswith('.py'):
   prior=z.read(name); current=(ROOT/name).read_bytes() if (ROOT/name).is_file() else b''
   missing=sorted(testnames(prior.decode('utf-8-sig'))-testnames(current.decode('utf-8-sig')))
   if missing: removed.append({'file':name,'functions':missing})
   if prior!=current: modified_tests.append(name)
full=json.loads((OUT/'full_suite.json').read_text(encoding='utf-8'))
log_matches_metadata=digest(OUT/'full_suite.log')==full['log_sha256']
cases=ET.parse(OUT/'full_suite.junit.xml').getroot().findall('.//testcase')
prefixes={
 'G6G-01':['test_g6g01_first_exit_checks_isolated_true_boundary_event','test_g6g01_missing_covers_at_first_boundary_rejected'],
 'G6G-02':['test_g6g02_vv_uses_exact_difference_and_independent_unit_normal','test_g6g02_vv_unrepresentable_gap_fails_loud_not_inf'],
 'G6G-03':['test_g6g03_unrepresentable_diameter_does_not_disable_missing_cover_gate'],
 'G6G-04':['test_g6g04_folded_internal_ridges_attain_slab_distance'],
 'G6G-05':['test_g6g05_face_area_rounds_after_final_halving','test_g6g05_face_area_underflow_is_not_silent_zero','test_g6g05_facet_gap_rounds_after_normal_length_division'],
 'G6G-06':['test_g6g06_margin_normal_does_not_subtract_display_points'],
 'G6G-07':['test_g6g07_derived_power_range_not_just_inputs','test_g6g07_minimal_representable_derivative_survives'],
 'G6G-08':['test_g6g08_mass_properties_use_exact_products_before_final_rounding','test_g6g08_centroid_retains_cancellation_even_when_volume_is_representable','test_g6g08_volume_independent_of_cyclic_face_ring_start'],
 'G6G-09':['test_g6g09_window_documents_distinguish_closed_separation_infimum','test_g6g09_tight_closed_cavity_distinguishes_rho_from_pd_closed'],
 'G6G-10':['test_g6g10_readme_oracle_and_canon_status_are_current'],
 'G6G-11':['test_g6g11_priority_claim_is_withdrawn_instead_of_narrowed']}
findings=[]
for key,names in prefixes.items():
 matched=[c for c in cases if any(c.attrib['name']==n or c.attrib['name'].startswith(n+'[') for n in names)]
 missing=[n for n in names if not any(c.attrib['name']==n or c.attrib['name'].startswith(n+'[') for c in matched)]
 failed=[c.attrib['name'] for c in matched if any(c.find(t) is not None for t in ('failure','error','skipped'))]
 findings.append({'id':key,'test_prefixes':names,'matched_cases':len(matched),'missing_prefixes':missing,'not_passed':failed,'verified_green':bool(matched) and not missing and not failed})
failed_all=[c.attrib['name'] for c in cases if any(c.find(t) is not None for t in ('failure','error','skipped'))]
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip()
diffcheck=subprocess.run(['git','-c','core.whitespace=cr-at-eol','diff','--check'],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
(OUT/'diff_check.log').write_bytes(diffcheck.stdout)
(OUT/'working_tree.patch').write_bytes(subprocess.check_output(['git','diff','--binary'],cwd=ROOT))
result={'generated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'head':head,'head_unchanged':head==base['head'],
 'tested_file_count':len(snapshot['files']),'tested_bytes_changed':changes,'fixture_count':len(fixtures),'fixture_changes':fixture_changes,
 'removed_original_test_functions':removed,'modified_original_test_files':modified_tests,
 'junit_testcases':len(cases),'junit_not_passed':failed_all,'full_suite':full,'full_log_matches_metadata':log_matches_metadata,'findings':findings,'diff_check_exit':diffcheck.returncode}
result['verified']=not(changes or fixture_changes or removed or failed_all) and full['exit_code']==0 and log_matches_metadata and all(f['verified_green'] for f in findings) and diffcheck.returncode==0 and result['head_unchanged']
dump('verification.json',result)
changed=subprocess.check_output(['git','diff','--name-only'],cwd=ROOT).decode().splitlines()
new_tests=[p.relative_to(ROOT).as_posix() for p in (ROOT/'tests').glob('test_r7fix*.py')]
inputs=[p.relative_to(ROOT).as_posix() for p in (ROOT/'reports/codex/inputs').rglob('*') if p.is_file() and (p.name.startswith('G6G') or 'G6G_repro' in p.parts)]
important=changed+new_tests+inputs+['reports/codex/R7FIX_report.md','reports/codex/R7FIX_evidence']
artifacts=[{'path':s,'url':(ROOT/s).as_uri(),'sha256':digest(ROOT/s) if (ROOT/s).is_file() else None} for s in important]
dump('artifacts.json',artifacts)
lines=['# R7FIX artifact index','','All paths are inside the authorized worktree.','']
lines.extend('- ['+a['path']+']('+a['url']+')' for a in artifacts)
lines+=['','## Verification and evidence','']
for pattern in ('*.json','*.log','*.xml','*.patch','*/report.md','*/REPORT.md','*/root_report.md','*/mutations.json','*/document_mutations.json'):
 for p in sorted(OUT.glob(pattern)):
  lines.append('- ['+p.relative_to(OUT).as_posix()+']('+p.as_uri()+')')
(OUT/'ARTIFACTS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps({k:result[k] for k in ['verified','head_unchanged','tested_file_count','tested_bytes_changed','fixture_count','fixture_changes','modified_original_test_files','junit_testcases','diff_check_exit']},ensure_ascii=False,indent=2))
raise SystemExit(0 if result['verified'] else 1)
