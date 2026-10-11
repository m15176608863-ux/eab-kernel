"""Read-only source audit; writes only this task's evidence JSON."""
import ast
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT/'reports/codex/E5a_evidence'
prior = ET.parse(OUT/'filters_2d_regression.xml')
bb52 = []
modules = defaultdict(float)
cumulative = 0.0
for case in prior.iter('testcase'):
    elapsed = float(case.get('time'))
    modules[case.get('classname')] += elapsed
    if case.get('classname') == 'tests.test_bb52_g1':
        cumulative += elapsed
        bb52.append({'name':case.get('name'),'seconds':elapsed,'cumulative_seconds':round(cumulative,3)})
full = json.loads((OUT/'full_final.json').read_text(encoding='utf-8'))
patches = []
for path in sorted((ROOT/'tests').glob('test*.py')):
    tree=ast.parse(path.read_text(encoding='utf-8-sig'))
    for node in ast.walk(tree):
        if (isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute)
                and node.func.attr=='setattr' and len(node.args)>1
                and isinstance(node.args[1],ast.Constant)):
            name=str(node.args[1].value)
            if any(w in name for w in ('cone','arc','normal','orient','facet','face','edge','hull','overlap','membership')):
                patches.append({'file':path.relative_to(ROOT).as_posix(),'line':node.lineno,'owner':ast.unparse(node.args[0]),'name':name})
with ZipFile(OUT/'tmp/pre_e5a.zip') as archive:
    unchanged = archive.read('tests/test_bb52_g1.py') == (ROOT/'tests/test_bb52_g1.py').read_bytes()
results = {
    'full_attempt':{'wall_seconds':full['wall_seconds'],'last_line':full['last_line'],'returncode':full['returncode'],'changed_during_run':full['changed_during_run']},
    'prior_2d_suite':'1717 passed in 233.05s',
    'prior_bb52_cases':bb52,
    'prior_module_seconds':dict(sorted(modules.items(),key=lambda item:-item[1])),
    'bb52_test_unchanged_from_pre_e5a_archive':unchanged,
    'performance_conclusion':'The aborted full attempt completed 11 leading bb52 cases in 76.47s; those same cases cost 82.374s in the prior 2D evidence. This is not evidence of regression. bb52 has only 17 items but costs 117.496s because its analyze/retired-vote/mutation loops each visit all 1260 translations. Dot count is not a progress/time estimator. The complete suite still needs a fresh timed run.',
    'geometry_monkeypatch_targets':patches,
    'public_cone_or_arc_patch_targets_remaining':[p for p in patches if p['name'] in ('vertex_cone_contains','edge_arc_contains')],
    'focused_legacy_teeth_gate':{'result':'6 passed in 2.11s','junit':'filters_teeth_audit.xml','tests':['test_all_five_call_sites_route_through_the_single_helper','test_overlap_coplanar_crossing_gate_has_teeth','test_g0_gate_has_teeth_flipped_normals_are_caught','test_position_independence_gate_has_teeth_absolute_edge_direction','test_position_independence_gate_has_teeth_gap_forgets_translation','test_vote1_catches_a_wrong_facet_label']},
    'cache_restoration_probe':{'before_patch':True,'during_exact_normal_flip':False,'after_restore_without_clear':True,'after_clear':True,'note':'Current implementation-keyed caches do not reproduce the prior warm-cache masking concern for this exact-normal mutation.'},
    'scope':'No production or test source edits. Targeted audit, not a full-suite green claim. G2 injection migration owned by covers agent.'
}
(OUT/'filters_performance_teeth_audit.json').write_text(json.dumps(results,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in results.items() if k not in ('prior_bb52_cases','geometry_monkeypatch_targets')},indent=2,ensure_ascii=False))
