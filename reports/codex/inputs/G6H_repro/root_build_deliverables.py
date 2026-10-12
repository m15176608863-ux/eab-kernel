"""Render the read-only audit deliverables after the baseline suite completes."""
from pathlib import Path
import json, hashlib, subprocess, os, re, datetime, xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]
REVIEW=ROOT/'review'
os.environ['GIT_OPTIONAL_LOCKS']='0'
def read(path):return json.loads((ROOT/path).read_text(encoding='utf8'))
def write(path,value):(ROOT/path).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf8')
def link(path,label=None):
    p=ROOT/path
    return f'[{label or path}]({p.as_uri()})'
def inline(s):return str(s).replace('|','\\|').replace('\n',' ').replace('\r',' ')

suite=read('review/logs/full_suite.json')
assert suite['exit_code']==0,suite
junit=ET.parse(REVIEW/'logs/full_suite.junit.xml').getroot()
testcases=junit.findall('.//testcase')
counts=dict(tests=len(testcases),failures=len(junit.findall('.//failure')),
            errors=len(junit.findall('.//error')),skipped=len(junit.findall('.//skipped')))
assert counts==dict(tests=9851,failures=0,errors=0,skipped=0),counts
suite['junit_counts']=counts
suite['pytest_seconds']=float(re.search(r'9851 passed in ([0-9.]+)s',(REVIEW/'logs/full_suite.log').read_text(encoding='utf8')).group(1))
suite['python_version']=subprocess.check_output(['python','--version'],encoding='utf8').strip()

baseline=read('review/baseline.json')
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,encoding='utf8').strip()
changed=[];missing=[]
for name,digest in baseline['files'].items():
    p=ROOT/name
    if not p.exists():missing.append(name)
    elif hashlib.sha256(p.read_bytes()).hexdigest()!=digest:changed.append(name)
status=subprocess.check_output(['git','status','--short','--untracked-files=normal'],cwd=ROOT,encoding='utf8')
integrity=dict(HEAD_before=baseline['HEAD'],HEAD_after=head,tracked_count=len(baseline['files']),
               tracked_changed=changed,tracked_missing=missing,git_status=status,
               checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
assert head==baseline['HEAD'] and not changed and not missing,integrity
assert not any(line and not line.startswith('?? ') for line in status.splitlines()),status
write('review/notes/final_integrity.json',integrity)

findings=read('review/notes/root_confirmed_findings.json')
assert len(findings)==6 and all(f['root_verified'] and f['verified_exit_code']==0 for f in findings)

g6g=[]
for owner in ['geom2','geom3','docs_gates']:
    for r in read(f'review/agents/{owner}/g6g_replay.json'):
        g6g.append({**r,'reviewer':owner})
root_runs=read('review/notes/root_replay_runs.json')
power_old=next(r for r in root_runs if r['script'].endswith('/root_power_range.py'))
power_new=next(r for r in root_runs if r['script'].endswith('/root_power_range_fixed_check.py'))
g6g.append(dict(id='G6G-07',status='已修',reviewer='root',original=power_old,positive=power_new,
                explanation='原876格逐值无错；旧缺陷断言红之外，另存正确值断言版本。'))
g6g.sort(key=lambda r:r['id'])
assert [r['id'] for r in g6g]==[f'G6G-{i:02d}' for i in range(1,12)]
assert all(r['status']=='已修' for r in g6g)

g6e=[];extras=[]
for owner in ['geom2','geom3','docs_gates']:
    for r in read(f'review/agents/{owner}/g6e_replay.json'):
        row={**r,'reviewer':owner}
        if 'g6e_id' in row:row['id']=f'G6E-{row["g6e_id"]:02d}'
        if not re.fullmatch(r'G6E-\d\d',row.get('id','')):extras.append(row);continue
        g6e.append(row)
root_map={
    9:('root_g6e_09.py','近乎平行tangent被明确ValueError拒绝，不再输出非切向棱锥。'),
    11:('root_g6e_11.py','小容量相对恒载格的0.999/0.99/0.9错alpha在真实调用路径/静力自校验均拒绝。'),
    20:('root_g6e_20.py','无关远体速度0/1000/100000均不放宽admissibility；坏候选ok=False。'),
    21:('root_g6e_21.py','静止体恒载10/1e6/1e9均拒绝次优alpha9.99，不再跨体吞对偶间隙。'),
    22:('root_g6e_22.py','far body位置/尺寸1e2/1e4/1e6不改变受载体U；微live的分辨率符合逐体报告。'),
    45:('root_g6e_45.py','单体无载远接触D0/1e4/1e5/1e6均不放宽0.999/0.99/0.9错alpha。'),
}
for i,(name,basis) in root_map.items():
    r=next(r for r in root_runs if r['script'].endswith('/'+name))
    g6e.append(dict(id=f'G6E-{i:02d}',status='已修',reviewer='root',status_basis=basis,
        how_to_reproduce='python -X utf8 review/repro/'+name,verified_output=r['output'],
        exit_code=r['exit_code'],scope='原复现输入/等价当前调用；预期的响亮ValueError不是复现环境失败。'))
mutations=read('review/notes/root_lp_gate_mutations.json')
for i,label,basis in [(23,'G6E23','关闭unbounded分辨率筛查；baseline4绿，变异4个目标报告断言红。'),
                      (47,'G6E47','恢复按速度尺度放宽负功率；baseline32绿，变异3格在admissible目标断言红。')]:
    r=next(r for r in mutations if r['id'].startswith(label))
    g6e.append(dict(id=f'G6E-{i:02d}',status='已修（目标内部变异门有牙）',reviewer='root',
        status_basis=basis,how_to_reproduce='python -X utf8 review/repro/root_lp_gate_mutations.py',
        verified_output=r,scope='目标门范围；不是完整历史/所有可能变异证明。'))
g6e.sort(key=lambda r:r['id'])
assert len({r['id'] for r in g6e})==len(g6e)>=20
missing_old=[f'G6E-{i:02d}' for i in range(1,51) if f'G6E-{i:02d}' not in {r['id'] for r in g6e}]
replay=dict(HEAD=head,g6g=g6g,g6e=g6e,g6e_unique_replayed=len(g6e),g6e_not_replayed=missing_old,
            additional_readonly_evidence=extras,root_augmented_g6g=read('review/notes/root_g6g_augmented_runs.json'))
write('review/G6H_regression_replay.json',replay)

branches=[]
for owner,path in [('root','review/notes/root_branch_classification.json'),
                   ('geom2','review/agents/geom2/branch_classification.json'),
                   ('geom3','review/agents/geom3/branch_classification.json')]:
    x=read(path); rows=x if isinstance(x,list) else x['rows']
    for r in rows:branches.append({**r,'reviewer':owner})
seen={}
for r in branches:seen[(r['file'],r['line'],r.get('condition',''))]=r
write('review/notes/branch_classification_all.json',dict(rows=list(seen.values()),
    unique_rows=len(seen),scope='关键词候选+人工补项，含非浮点分支；分类不是形式证明。',
    geom3_additional=read('review/agents/geom3/branch_classification.json')['additional']))

names=subprocess.check_output(['git','diff','--name-only','d44dd78..HEAD','--','src','tests'],cwd=ROOT,encoding='utf8').splitlines()
hunks=[]
root_files={'src/eab/dual.py','src/eab/limit.py','tests/test_r7fix_dual.py','tests/test_r7fix_limit_construction.py'}
for name in names:
    patch=subprocess.check_output(['git','diff','d44dd78..HEAD','--',name],cwd=ROOT,encoding='utf8')
    if name in root_files:owner='root';reason='幂整数有理导数/范数最终舍入、新独立构造门；未修公共wrench派生乘积。'
    elif '/kernel2d/' in name or name=='tests/test_r7fix_geom2.py':owner='geom2';reason='全部hunks核对；原子格、拓扑事件与内部变异，首入初态漏项另报。'
    elif name=='tests/test_r7fix_docs.py':owner='docs_gates';reason='文本具名门、rho/PD空腔与禁用生产oracle真实调用。'
    else:owner='geom3/docs_gates';reason='全部hunks核对；源三角模型、精确方向证书、最后舍入及原unsafe-output牙。'
    hunks.append(dict(file=name,hunks=patch.count('\n@@ '),reviewer=owner,
                      reviewed_all_current_diff_hunks=True,judgement=reason))
assert len(hunks)==28
write('review/notes/r7_change_coverage.json',dict(base='d44dd78',HEAD=head,files=hunks,
    src_files=sum(r['file'].startswith('src/') for r in hunks),test_files=sum(r['file'].startswith('tests/') for r in hunks)))

data=dict(work_order='WO-G6H',HEAD=head,role='独立审查方；未修代码',counts=dict(critical=0,major=6,minor=0),
          m0_can_exit=False,findings=findings,full_suite=suite,integrity=integrity,
          regression_replay_file='review/G6H_regression_replay.json',g6g_status='11项原范围均已修',
          g6e_unique_replayed=len(g6e),unconfirmed=[
              '独立overlap仅查整边中点的潜在不足未复现。',
              '首入docstring全部相邻中点与实现差异，未证改变答案。',
              'canon历史砖二状态残差，未证当前核心承诺错误。'],
          completion_token='G6H_DONE critical=0 major=6 minor=0')
write('review/G6H_findings.json',data)

table='| ID | severity | file:line | 一句话结论 | 复现/主审日志 |\n|---|---|---|---|---|\n'
details=[]
for f in findings:
    table+=f'| {f["id"]} | major | `{f["file:line"]}` | {inline(f["summary"])} | {link(f["repro_script"],"脚本")} / {link(f["verified_log"],"输出")} |\n'
    # Keep representative output readable; full verbatim evidence lives in JSON/log.
    excerpts={
      'G6H-01':"x0_in_topological_interior=true\nactual.kind='entrance', actual.t_exact=0\nindependent first boundary along +y=3/2",
      'G6H-02':'body_distance=1.0; frozen_gap=6662.338147750939\nswap rotation components: frozen_gap=-6660.338147750939\ntangent_derivative=4440.892098500626; expected=0\nplain lift=5/8; zero-seed Dual primal=-8326.047684688674',
      'G6H-03':'M=100000000; expected_angle=5e-17; actual_angle=0.0\nsigned_volume=0.16666666666666666; convex=true; issues=[]',
      'G6H-04':'dim=2, scale=1e160: expected=[1e160,1e160,0]; actual=[1e160,1e160,nan]\ndim=3, scale=1e200: expected moments=[0,0,0]; actual moments=[nan,nan,nan]\nraised=false',
      'G6H-05':'BASELINE tetra_box_vv/generic: new_gate=PASS, old_gate=PASS\nMUTANT tetra_box_vv/generic: new_gate=PASS, old_gate=AssertionError\nold assertion: complete local facet label set invariance\ncopy source restored SHA256=cded18523b434090da3858ac3213d340f16b6d54570b0d8c69d65a1c585254e5',
      'G6H-06':'T=0: mutant public_error="... missed the nearest pair"; G0 passed=false\nT=1e8: truth=1.4901161193847656e-08; mutant distance=1.4901161193847656e-07\nG0 samples=1, worst_abs_error=1.341104507446289e-07, passed=true, failures=[]\ntracked SHA256 before=after=cf1158aac4906379c66efe1c15a676c61a3c1f254c2195032df3a8f0320ee9cb'}
    details.append(f'### {f["id"]} · major\n\n**位置**：`{f["file:line"]}`。\n\n**具体输入 → 错误输出**：{f["failure_scenario"]}\n\n**可直接运行**：\n\n```powershell\n{f["how_to_reproduce"]}\n```\n\n**主审实跑输出关键字段整理（退出0）**：\n\n```text\n{excerpts[f["id"]]}\n```\n\n完整原样stdout/stderr在 {link(f["verified_log"],"日志")} 与机读 verified_output。\n\n**建议修复（未实施）**：{f["suggested_fix"]}\n')
suite_text='实际使用**串行 pytest**：\n\n```powershell\n$env:PYTHONDONTWRITEBYTECODE=\'1\'\n$env:PYTHONIOENCODING=\'utf-8\'\n'+ ' '.join(suite['command'])+'\n```\n\n'
pytest_seconds=re.search(r'9851 passed in ([0-9.]+)s',(REVIEW/'logs/full_suite.log').read_text(encoding='utf8')).group(1)
suite_text+=f'**9851 passed；0 failed / 0 error / 0 skipped，退出码0**。pytest实际摘要 `{pytest_seconds} s`；包装器墙钟 `{suite["wall_seconds"]:.2f} s`（二者计时范围不同）。{link("review/logs/full_suite.log","全套日志")} · {link("review/logs/full_suite.junit.xml","JUnit逐例结果")} · {link("review/logs/full_suite.json","命令/计时元数据")}。'
integrity_text=f'终态逐字节核对：**{len(baseline["files"])}个已跟踪文件SHA-256全部不变，HEAD不变**；`git status --short` 仅 `?? review/`。'
g6e_text=f'去重重放 **{len(g6e)} / 50 条**，超过工单至少20条要求；另有DDA4.x只读原源码核验（不重复计编号1）。编号为原raw列表的1-based位置。数值原输入/等价复现与文档订正分别列出，不把“承诺缩小”写成“功能已实现”。\n\n| 原编号 | 本轮处置 | 证据来源 |\n|---|---|---|\n'
for r in g6e:
    p={'root':'review/notes/root_replay_runs.json','geom2':'review/agents/geom2/g6e_replay.json',
       'geom3':'review/agents/geom3/g6e_replay.json','docs_gates':'review/agents/docs_gates/g6e_replay.json'}[r['reviewer']]
    if r['id'] in ['G6E-23','G6E-47']:p='review/notes/root_lp_gate_mutations.json'
    g6e_text+=f'| {r["id"]} | {inline(r["status"])} | {link(p,r["reviewer"])} |\n'
g6e_text+='\n未重放：'+', '.join(missing_old)+'。每条具体输入、断言、状态依据、运行输出及限制在 '+link('review/G6H_regression_replay.json','回归台账')+'。不以脚本exit0自动判修复；例如G6E40原先float差点的hull不是精确差点模型，已另核Fraction先作差的默认facet_vote严格结果 `(0,6,0,0,[])`。'
pressure='三维自写Fraction区间oracle **36/36通过**：3个精确正交姿态 × 尺度1e-9/1/1e9 × 平移0/1e3/1e6/1e8；最小真间隙1e-15。成员、距离、法向、delta三态、首入exact_t、出口及E成员均核；另95项定向门通过。这是预定构造族，不是任意凹闭表面穷举。'+link('review/repro/geom3_independent_interval_pressure.py','脚本')+' · '+link('review/logs/geom3_independent_interval_pressure.log','输出')+'。'
template=(REVIEW/'G6H_report.template.md').read_text(encoding='utf8')
for k,v in dict(full_suite=suite_text,integrity=integrity_text,findings_table=table,
                finding_details='\n'.join(details),geom3_pressure=pressure,g6e_replay=g6e_text).items():
    template=template.replace('{{'+k+'}}',v)
assert '{{' not in template
(REVIEW/'G6H_report.md').write_text(template,encoding='utf8')
(REVIEW/'PLAN.md').write_text('''# G6H 只读审查计划与完成记录

- 目标：核当前 HEAD 的数学正确性，不修代码；判定 M0 退出资格。
- 范围：只读全部被审代码/测试/指定正本，所有新产物只写 review/。
- 非目标：不修实现、不写姊妹仓库/正本、不作 Git 写操作。
- 成功标准：自跑全套；11项G6G逐项重放；至少20项G6E；新发现主审实跑确认；中文MD/机读JSON与完整性批评。
- 验证：串行pytest、独立Fraction oracle、真实内部变异目标断言、原字节SHA回读、交付JSON/链接检查。
- 回滚锚：baseline.json 保存1910个tracked文件SHA；变异只在review副本或独立进程函数，均原字节/指针还原。

## 顺序与证据
1. [完成] HEAD/基线及背景确认，先启动完整串行测试。
2. [完成] G6G 11项原脚本+正确值增强重放，原范围均已修。
3. [完成] 分镜九镜头、新diff、同类漏网与G6E 37项；6条major主审逐条实跑。
4. [完成] 9851 passed/1614.33s；报告/JSON/链接验证；1910 tracked SHA不变。

结果：0 critical / 6 major / 0 minor，M0不得退出。详细结论和验证范围见G6H_report.md。
''',encoding='utf8')

# Clickable inventory: list audit files individually, heavy copies/tmp by directory.
items=[]
for p in sorted(REVIEW.rglob('*')):
    if not p.is_file() or any(part in {'copies','tmp','tmp_root_gate'} or part.startswith('tmp_') for part in p.relative_to(REVIEW).parts):continue
    if p.name in {'README.md','evidence_index.json'}:continue
    items.append(dict(path=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size))
index=dict(HEAD=head,files=items,heavy_directories=['review/copies','review/tmp','review/tmp_root_gate'],
           note='索引自身/README不作自引用hash；副本与临时子目录以目录链接交付，原树保护以final_integrity为准。')
write('review/evidence_index.json',index)
md='# G6H 审查证据清单\n\n'+link('review/G6H_report.md','中文报告')+' · '+link('review/G6H_findings.json','机读发现')+' · '+link('review/G6H_regression_replay.json','回归台账')+' · '+link('review/evidence_index.json','文件hash索引')+'\n\n'
for folder in index['heavy_directories']:
    if (ROOT/folder).exists():md+='- '+link(folder)+'（隔离副本或pytest临时文件；不属源码修复）\n'
md+='\n## 文件\n\n'
for r in items:md+='- '+link(r['path'])+f' — {r["bytes"]} bytes\n'
(REVIEW/'README.md').write_text(md,encoding='utf8')
print(json.dumps(dict(result='DELIVERABLES_WRITTEN',counts=data['counts'],suite=counts,
                      g6g=len(g6g),g6e=len(g6e),tracked_unchanged=len(baseline['files']),
                      report_bytes=(REVIEW/'G6H_report.md').stat().st_size),ensure_ascii=False,indent=2))
