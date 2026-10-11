"""Source/test/fixture audit tied to 3566708 and the final JUnit result."""
from pathlib import Path
from collections import Counter
import ast
import hashlib
import json
import subprocess
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent

def save(name,data):
    (OUT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

def functions(path):
    text=path.read_text(encoding='utf-8-sig'); tree=ast.parse(text)
    return {n.name:(n,ast.get_source_segment(text,n)) for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}

rows=[]; removed=[]; decorators=[]
notes={
 'test_invariance_interlock.py':'Same original grids; legacy assertions retained in explicit contact/boundary windows; independent exact oracle added for raw input. Brute zero cells use independent swept SAT, ideal rational cells retain exact zero.',
 'test_interlock_walls.py':'All 4 x 20 raw cells kept and checked against independent earliest-root oracle; original nominal 0.2 and frozen assertions retained in explicit window. Added clearance and ideal grids.',
 'test_interlock_sensitivity.py':'All 72 steep cells and legacy assertions retained; added independently certified in-band branch obligation. Same internal vertical-window mutant now hits missing-branch assertion.',
 'test_e5a2_interlock_bridge.py':'Independent profile oracle compares exact roots. Actual nonpenetration checked on authoritative exact affine endpoint; additional representable roots preserve old floating-endpoint safety.',
 'test_entrance3.py':'t_max is now exact: raw root beyond 0.3 must be none; old entrance assertion retained on exactly representable boundary data.',
 'test_kernel3d_geom.py':'Entrance-block hull assertions use original coordinates rationalised BEFORE differences. Escape uses independent exact swept-SAT root and exact affine endpoint; float display checked to one upward ulp. Same parameter grids and ideal-contact assertions.',
 'test_margin_penetration.py':'Default exact penetration and explicit contact-window modes have separate strong assertions and internal mutants; no tolerance loosening.',
 'test_margin_resolution.py':'Legacy resolution expectations require explicit contact_window; exact raw-input checks added. Same parameter grid.',
 'test_entrance3_concave.py':'Plane family requires exact coplanarity; micro-step regression and tolerance mutant replace an ineffective coarse-step tooth without dropping old input.',
 'test_frozen_ee_sign.py':'All original 32 assertion strings and six engineering-coordinate cells retained in explicit legacy window; same raw cells additionally check default full triangulated cover labels/strictness, independent exact surface distance and frozen sign. Independent test-only ear clipping shares no production primitive.',
 'test_invariance_geom.py':'Original full grid and assertion strings retained in caller-explicit legacy contact window; same raw inputs additionally checked against independent exact triangulated surface labels/distance/state. See margin integration migration ledger.',
 'test_near_parallel_edges.py':'Original near-parallel grids and old contact-zero assertion kept under explicit legacy window; default raw geometry additionally checked against independent exact surface-distance and label oracle.',
 'test_geom3_face_polygon.py':'All old call-site assertions retained. Face-interior rejection injected into the live integer boundary/ray halfspace path as well as the still-live triangle_locate segment path; no result records fabricated.',
}
for old in sorted((OUT/'baseline/tests').glob('test_*.py')):
    new=ROOT/'tests'/old.name
    before=functions(old);after=functions(new) if new.exists() else {}
    for name,(a,source_a) in before.items():
        if name not in after:
            if name.startswith('test_'): removed.append(old.name+'::'+name)
            continue
        b,source_b=after[name]
        if name.startswith('test_') and [ast.dump(d) for d in a.decorator_list]!=[ast.dump(d) for d in b.decorator_list]:
            decorators.append(old.name+'::'+name)
        if ast.dump(a)==ast.dump(b):continue
        asserts_a=[ast.unparse(n) for n in ast.walk(a) if isinstance(n,ast.Assert)]
        asserts_b=[ast.unparse(n) for n in ast.walk(b) if isinstance(n,ast.Assert)]
        rows.append(dict(file='tests/'+old.name,function=name,reason=notes.get(old.name,'See component notes; semantic migration must retain every old node and an equal-or-stronger oracle.'),
                         old_source=source_a,new_source=source_b,
                         old_assertions=asserts_a,new_assertions=asserts_b,
                         assertions_no_longer_literal=list((Counter(asserts_a)-Counter(asserts_b)).elements()),
                         old_sha256=hashlib.sha256(source_a.encode()).hexdigest(),new_sha256=hashlib.sha256(source_b.encode()).hexdigest()))
save('test_rewrites.json',dict(baseline='3566708',rewrites=rows,removed_test_functions=removed,changed_decorators=decorators,
                             warning='Literal/AST differences are evidence for review, not an automatic proof of assertion strength.'))

manifest=json.loads((OUT/'baseline_manifest.json').read_text(encoding='utf8'))
changed_fixtures=[name for name,digest in manifest['fixtures'].items() if not (ROOT/name).exists() or hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=digest]
record=dict(head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
            branch=subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip(),
            changed_fixtures=changed_fixtures,fixture_count=len(manifest['fixtures']),removed_tests=removed,changed_decorators=decorators)
final=OUT/'final.xml'
if final.exists():
    def nodes(path):
        return {c.attrib['classname']+'::'+c.attrib['name']:c for c in ET.parse(path).getroot().iter('testcase')}
    baseline=nodes(ROOT/'reports/codex/E5a2_evidence/final.xml');current=nodes(final)
    missing=sorted(set(baseline)-set(current))
    bad=[k for k,c in current.items() if c.find('failure') is not None or c.find('error') is not None]
    skipped=[k for k,c in current.items() if c.find('skipped') is not None]
    record.update(baseline_nodes=len(baseline),current_nodes=len(current),missing_nodes=missing,failed_nodes=bad,skipped_nodes=skipped)
    completed=OUT/'final.json'
    if completed.exists():
        verified=json.loads(completed.read_text(encoding='utf8'))
        record['source_drift_since_final']=[name for name,digest in verified['source_after'].items()
            if not (ROOT/name).exists() or hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=digest]
    failures=json.loads((ROOT/'reports/codex/E5a2_evidence/full_failures.json').read_text(encoding='utf8'))
    disposition=[]
    for f in failures:
        key=f['classname']+'::'+f['name']
        file=f['classname'].replace('tests.','')+'.py'
        disposition.append(dict(node=key,old_failure=f['message'],resolution=notes.get(file,''),
                                final_status='missing' if key not in current else ('failed' if key in bad else 'passed')))
    save('49_disposition.json',disposition)
    integration=[]
    for f in json.loads((OUT/'integration1_failures.json').read_text(encoding='utf8')):
        key=f['classname']+'::'+f['name']
        file=f['classname'].replace('tests.','')+'.py'
        integration.append(dict(node=key,old_failure=f['message'],resolution=notes.get(file,''),
            final_status='missing' if key not in current else ('failed' if key in bad else 'passed')))
    save('integration1_disposition.json',integration)
    byfile={}
    for c in current.values():
        key=c.attrib['classname'];row=byfile.setdefault(key,dict(nodes=0,seconds=0.))
        row['nodes']+=1;row['seconds']+=float(c.attrib.get('time',0))
    save('performance_by_file.json',dict(sorted(byfile.items(),key=lambda kv:-kv[1]['seconds'])))
    findings=json.loads((OUT/'g6e_3d_disposition.json').read_text(encoding='utf8'))
    unresolved_gates=[]
    for finding in findings:
        verification=[]
        for gate in finding['gates']:
            module,_,test=gate.partition('::')
            prefix='tests.'+module.removesuffix('.py')+'::'+test
            matches=[k for k in current if k.startswith(prefix)]
            failures=[k for k in matches if k in bad or k in skipped]
            verification.append(dict(gate=gate,matched=len(matches),failed=failures))
            if not matches or failures:unresolved_gates.append(gate)
        finding['final_gate_verification']=verification
    save('g6e_3d_disposition.json',findings)
    record['unresolved_g6e_gate_references']=unresolved_gates
save('delivery_audit.json',record)
print(json.dumps(record,ensure_ascii=False,indent=2))
raise SystemExit(int(bool(removed or decorators or changed_fixtures or record.get('missing_nodes') or record.get('failed_nodes') or record.get('skipped_nodes') or record.get('unresolved_g6e_gate_references') or record.get('source_drift_since_final'))))
