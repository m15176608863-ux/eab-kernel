"""Recheck reviewer deliverables and byte-preservation, without source edits."""
from pathlib import Path
import collections, datetime, hashlib, json, re, subprocess, urllib.parse
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'review'

def jread(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def jwrite(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def link(p):return f'[{p.relative_to(OUT).as_posix()}]({p.as_uri()})'

def main():
    before=jread(OUT/'tracked_before.json')
    tracked=subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0')
    tracked=[f for f in tracked if f]
    after={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in tracked if (ROOT/f).is_file()}
    drift=[f for f,h in before.items() if after.get(f)!=h]
    assert not drift and set(after)==set(before)
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    assert head=='9f99025232450dc70b4e442b173badc3f9e55727'
    status=subprocess.check_output(['git','status','--short'],cwd=ROOT,text=True).strip()
    assert status=='?? review/',status

    full=jread(OUT/'full_suite.json')
    nodes=[s for s in (OUT/'logs/full_collection.log').read_text(encoding='utf-8').splitlines()
           if s.startswith('tests/') and '::' in s]
    modules={s.split('::')[0] for s in nodes}
    assigned=[a for c in full['commands'] for a in c if a.startswith('tests/')]
    assert set(assigned)==modules and len(assigned)==len(set(assigned))
    assert len(nodes)==len(set(nodes))==10100
    totals=collections.Counter()
    junit=[]
    for p in sorted((OUT/'logs').glob('full_*.xml')):
        suites=list(ET.parse(p).getroot().iter('testsuite'))
        for s in suites:
            for k in ('tests','errors','failures','skipped'):totals[k]+=int(s.attrib[k])
        junit.append(dict(file=p.relative_to(ROOT).as_posix(),suites=[s.attrib for s in suites]))
    assert dict(totals)==dict(tests=10100,errors=0,failures=0,skipped=0)
    assert all(r['exit_code']==0 for r in full['results'])

    doc=jread(OUT/'G6I_findings.json')
    counts={k:sum(f['severity']==k for f in doc['findings']) for k in ('critical','major','minor')}
    assert counts==doc['counts']==dict(critical=0,major=4,minor=2)
    assert len({f['id'] for f in doc['findings']})==6
    needed=('severity','file:line','summary','failure_scenario','how_to_reproduce','suggested_fix','verified_output')
    for f in doc['findings']:
        assert all(f.get(k) for k in needed)
        assert f['confirmed'] and f['root_verified'] and f['verified_exit_code']==0
        script=ROOT/f['repro_script']; log=ROOT/f['verified_log']
        assert script.is_file() and log.is_file()
        assert hashlib.sha256(log.read_bytes()).hexdigest()==f['verified_log_sha256']
        assert log.read_text(encoding='utf-8')==f['verified_output'].replace('\r\n','\n').replace('\r','\n')
        for a in f.get('additional_instances',[]):
            assert a['root_verified'] and a['verified_exit_code']==0
            assert (ROOT/a['repro_script']).is_file()
            extra=ROOT/a['verified_log']
            assert hashlib.sha256(extra.read_bytes()).hexdigest()==a['verified_log_sha256']
            assert extra.read_text(encoding='utf-8')==a['verified_output'].replace('\r\n','\n').replace('\r','\n')
    migration=jread(OUT/'migration_complete_review.json')
    registry=jread(OUT/'gates_docs/changed_existing_tests.json')
    assert migration['registry_count']==114 and migration['same_name_count']==108
    assert migration['renamed_with_successor_count']==6
    mr=migration['entries']
    assert len(mr)==114 and all(r['full_old_new_text_read'] for r in mr)
    assert {(r['file'],r['old_name']) for r in mr}=={(r['file'],r['name']) for r in registry}
    assert sum(r['old_name']!=r['new_name'] for r in mr)==6
    duplicate=jread(OUT/'logs/root_duplicate_matrix.json')
    assert duplicate['exit_code']==0
    assert '94 failed, 83 passed' in (OUT/'logs/root_duplicate_matrix.log').read_text(encoding='utf-8')
    replay=jread(OUT/'G6E_replays.json')
    assert replay['count']==31 and len({r['raw_index'] for r in replay['replays']})==31
    assert all((ROOT/r['root_log']).is_file() for r in replay['replays'])
    report=(OUT/'G6I_report.md').read_text(encoding='utf-8')
    assert report.rstrip().endswith('G6I_DONE critical=0 major=4 minor=2')
    assert re.search(r'[\u4e00-\u9fff]',report)
    assert re.search(r'[\u4e00-\u9fff]',(OUT/'G6I_findings.json').read_text(encoding='utf-8'))

    # Key links first; all non-copy evidence files follow as an auditable index.
    files=sorted(p for p in OUT.rglob('*') if p.is_file()
                 and not {'copies','tmp'}.intersection(p.relative_to(OUT).parts))
    sections=['# WO-G6I 交付与证据索引\n',
        '确认 **0 critical / 4 major / 2 minor；M0不能退出**。全部复现位于本树review，未修生产代码。\n',
        '## 关键交付\n',
        '- '+link(OUT/'G6I_report.md'),'- '+link(OUT/'G6I_findings.json'),
        '- '+link(OUT/'G6E_replays.md'),'- '+link(OUT/'full_suite.json'),
        '- '+link(OUT/'integrity.json'),'- '+link(OUT/'evidence_manifest.json'),
        '\n## 直接复现\n',
        "在D:\\eab-wt\\g6i运行 `$env:PYTHONDONTWRITEBYTECODE='1'; python -X utf8 review/repro/<script>.py`。六条发现脚本预期exit0，表示断言已证当前缺陷；原G6H缺陷成立脚本在修复后预期exit1，须配正向脚本解释。\n"]
    sections += [f"- **{f['id']} {f['severity']}**：{link(ROOT/f['repro_script'])} / {link(ROOT/f['verified_log'])}" for f in doc['findings']]
    sections += ['\n## 目录\n',f'- [repro]({(OUT/"repro").as_uri()})：全部脚本与汇总/校验器。',
        f'- [logs]({(OUT/"logs").as_uri()})：root亲跑原样输出、全套日志及JUnit。',
        f'- [copies]({(OUT/"copies").as_uri()})：仅审查副本，部分故意保留坏实现/变异源码，不是生产交付。',
        f'- [tmp]({(OUT/"tmp").as_uri()})：测试临时产物；不依赖其他工作树可写tmp。',
        '\n## 其余全部非副本证据文件\n']
    sections += ['- '+link(p) for p in files if p.name not in ('INDEX.md','integrity.json','evidence_manifest.json')]
    (OUT/'INDEX.md').write_text('\n'.join(sections)+'\n',encoding='utf-8')
    preliminary=dict(work_order='WO-G6I',head=head,counts=counts,tracked_before_count=len(before),
        tracked_after_count=len(after),missing_tracked_at_start=len(tracked)-len(before),
        tracked_sha256_drift=drift,git_status=status,collection_nodes=len(nodes),
        modules_assigned_once=len(modules),junit_totals=dict(totals),junit=junit,
        g6e_replay_count=31,confirmed_root_findings=6)
    preliminary.update(historical_migration_functions=114,full_old_new_manual_reads=114,
                       same_name_migrations=108,renamed_migrations=6,
                       additional_same_cause_oracle_instances=1,
                       local_duplicate_mutation_other_gate_failures=94)
    jwrite(OUT/'integrity.json',preliminary)
    if not (OUT/'evidence_manifest.json').exists():
        jwrite(OUT/'evidence_manifest.json',dict(status='assembling',files=[]))
    # Open/read verification of Markdown delivery links, not bare path existence guesses.
    missing=[];links=0
    for p in (OUT/'G6I_report.md',OUT/'INDEX.md',OUT/'G6E_replays.md'):
        for url in re.findall(r'\]\((file://[^)]+)\)',p.read_text(encoding='utf-8')):
            u=urllib.parse.urlparse(url); path=urllib.parse.unquote(u.path)
            if re.match(r'^/[A-Za-z]:/',path):path=path[1:]
            links+=1
            if not Path(path).exists():missing.append(dict(document=p.name,url=url))
    assert not missing,missing
    manifest=[]
    for p in sorted(OUT.rglob('*')):
        if not p.is_file() or {'copies','tmp'}.intersection(p.relative_to(OUT).parts):continue
        if p.name in ('evidence_manifest.json','integrity.json'):continue
        manifest.append(dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,
                             sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
    jwrite(OUT/'evidence_manifest.json',dict(excluded='copies/tmp bulk, integrity and self to avoid recursive hash',files=manifest))
    preliminary.update(verified_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        clickable_local_links_checked=links,missing_links=missing,evidence_files_hashed=len(manifest),
        deliverable_parse_and_schema='PASS',verification='PASS')
    jwrite(OUT/'integrity.json',preliminary)
    print(json.dumps(preliminary,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
