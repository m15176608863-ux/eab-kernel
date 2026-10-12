"""Read-only source audit and evidence/report finalization; writes reports only."""
from pathlib import Path
import datetime
import hashlib
import json
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent


def decode(path):
    raw = path.read_bytes()
    return raw.decode('utf-16' if raw.startswith((b'\xff\xfe', b'\xfe\xff'))
                      else 'utf-8-sig', errors='replace')


def main():
    subprocess.run([sys.executable, '-X', 'utf8', str(OUT/'audit_scope_and_tests.py')],
                   cwd=ROOT, check=True)
    full = json.loads((OUT/'full_suite.json').read_text(encoding='utf8'))
    assert not full['source_drift']
    assert all(r['exit_code'] == 0 and r['expected'] == r['tests'] and
               not(r['skipped'] or r['failures'] or r['errors']) for r in full['results'])
    single = json.loads((OUT/'full_single.json').read_text(encoding='utf8'))
    assert single['exit_code'] == 0 and single['tests'] == single['expected'] == full['collected']
    assert not single['source_drift']
    assert not any(single[key] for key in ('failures','errors','skipped'))
    # Verify the frozen suite still represents every current source byte.
    freeze = json.loads((OUT/'full_source_freeze.json').read_text(encoding='utf8'))
    assert freeze == json.loads((OUT/'full_single_source_freeze.json').read_text(encoding='utf8'))
    assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest() == sha for p,sha in freeze.items())
    diff = subprocess.check_output(['git','diff','--no-ext-diff','--binary'], cwd=ROOT)
    (OUT/'tracked_changes.patch').write_bytes(diff)
    status = subprocess.check_output(['git','status','--porcelain=v1'], cwd=ROOT)
    (OUT/'final_git_status.txt').write_bytes(status)
    subprocess.run(['git','-c','core.whitespace=cr-at-eol','diff','--check'], cwd=ROOT, check=True)

    rows = [
        ('G6I-01','major','test_r9fix_entrance_domain.py','geom2_red.log','geom2_targeted_final.log',
         '_facet_in_domain -> True; finite source edge labels','geom2_mutation.log'),
        ('G6I-02','major','test_r9fix_topology.py','topology_before.log','topology_legacy_final.log',
         'exact_surface(self) -> self; roof concavity / reflex ridge / real dihedral','topology_after.log'),
        ('G6I-03','major','test_r9fix_construction.py','construction_red.log','construction_green.log',
         'norm(_float_vector(p)); G6I-03 exact cone margin','construction_green.log'),
        ('G6I-04','major','test_r9fix_construction.py','construction_red.log','construction_green.log',
         'sqrt(float(d2)) inside real body_distance/margin_contacts; default-exact construction','construction_green.log'),
        ('G6I-05','minor','test_r9fix_topology.py','topology_before.log','topology_legacy_final.log',
         'component check -> total-volume check; disconnected-inward-component','topology_after.log'),
        ('G6I-06','minor','test_r9fix_docs.py','docs_red.log','final3_preflight.log',
         'replace corresponding current clause by original stale text; G6I-06','final3_preflight.log'),
    ]
    matrix = [dict(id=i,severity=sev,test='tests/'+test,red=red,green=green,
                   internal_mutation=mutation,mutation_evidence=log,
                   included_in_final_suite=True) for i,sev,test,red,green,mutation,log in rows]
    (OUT/'finding_matrix.json').write_text(json.dumps(dict(findings=matrix,
        supplemental_workstreams=['unified constructors and midpoint certificates',
          'whole-repository AST boundary and migration', 'finite domains and declared solid cones',
          'oracle/mechanics/window/parameter/G03 same-family fixes', 'preservation/full-suite/docs/canon audit'],
        formal_G6_exit_claim=False),ensure_ascii=False,indent=2),encoding='utf8')

    logs = []
    for path in sorted(OUT.rglob('*.log')):
        if 'tmp' in path.relative_to(OUT).parts:
            continue
        text = decode(path)
        lines = [line for line in text.splitlines() if line.strip()]
        logs.append(dict(path=path.relative_to(OUT).as_posix(),bytes=path.stat().st_size,
                         sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                         last_line=lines[-1] if lines else '',
                         pytest_summary=[x for x in lines if re.search(r'\d+ (?:passed|failed|skipped).* in \d',x)][-1:]))
    (OUT/'log_catalogue.json').write_text(json.dumps(logs,ensure_ascii=False,indent=2),encoding='utf8')

    audit = json.loads((OUT/'change_and_test_audit.json').read_text(encoding='utf8'))
    index = ['# R9FIX 成果与证据清单','',
        '原始日志保留失败和中间状态；最终结论以主报告及 full_suite.json 为准。',
        '分项小结保留过程时序；scope review 指出的最后遗漏均以主报告补修记录为准。',
        'tracked_changes.patch 仅含已跟踪文件 diff；新增文件直接交付于工作树，完整哈希见 full_source_freeze.json。','',
        f"- 原始 {audit['baseline_test_nodes']} 节点全部保留，最终 {audit['final_test_nodes']} 节点。",
        f"- 跟踪改动 {len(audit['tracked_changed'])} 文件；旧测试文件 {len(audit['test_ast'])}；fixture 零改动。",'',
        '## 关键入口','',
        '[主报告](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_report.md) · '
        '[设计同步](file:///D:/eab-wt/cx-e2/docs/r9fix_design_sync.md) · '
        '[机器核查矩阵](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/finding_matrix.json)', '',
        '## 源码、测试与文档改动','']
    initial = json.loads((OUT/'initial_state.json').read_text(encoding='utf8'))['sha256']
    changed = set(audit['tracked_changed']) | {p for p in freeze if p not in initial}
    for relative in sorted(changed):
        index.append(f'- [{relative}]({(ROOT/relative).as_uri()})')
    index += ['', '## 文件清单（临时文件按目录列）', '',
              f'- [临时验证目录]({(OUT/"tmp").as_uri()}/)', '']
    for path in sorted(OUT.rglob('*')):
        if not path.is_file() or 'tmp' in path.relative_to(OUT).parts or path.name in ('INDEX.md','evidence_manifest.json'):
            continue
        rel = path.relative_to(OUT).as_posix()
        index.append(f'- [{rel}]({path.as_uri()})')
    (OUT/'INDEX.md').write_text('\n'.join(index)+'\n',encoding='utf8')
    files = []
    for path in sorted(OUT.rglob('*')):
        if path.is_file() and 'tmp' not in path.relative_to(OUT).parts and path.name != 'evidence_manifest.json':
            files.append(dict(path=path.relative_to(OUT).as_posix(),bytes=path.stat().st_size,
                              sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    (OUT/'evidence_manifest.json').write_text(json.dumps(dict(
        generated_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        report_sha256=hashlib.sha256((ROOT/'reports/codex/R9FIX_report.md').read_bytes()).hexdigest(),
        files=files),
        ensure_ascii=False,indent=2),encoding='utf8')
    print('FINAL_EVIDENCE_PASS',len(files),'files, current source matches frozen green suite')


if __name__ == '__main__':
    main()
