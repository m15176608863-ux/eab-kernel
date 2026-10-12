"""Freeze the review-only deliverable; fail closed on integrity/evidence gaps."""
from pathlib import Path
import json,re,hashlib,subprocess
from datetime import datetime,timezone

ROOT=Path(__file__).resolve().parents[2];R=ROOT/'review'
def read(name):return json.loads((R/name).read_text(encoding='utf-8-sig'))
def dump(name,data):
    (R/name).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
def link(p,label=None):
    p=Path(p)
    if not p.is_absolute():p=ROOT/p
    return f'[{label or p.name}]({p.as_uri()})'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

suite=read('logs/full_suite.json')
assert suite.get('exit_code')==0,'Full suite must complete and be green before delivery.'
assert suite['tracked_sha256_changed']==[]
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
assert head==suite['head']
baseline=read('baseline_hashes.json')
changed=[p for p,h in baseline.items() if not (ROOT/p).is_file() or sha(ROOT/p)!=h]
assert changed==[],changed

sets=[read('notes/geom2_findings.json'),read('notes/geom3_findings.json')['findings'],
      read('notes/root_findings.json'),read('notes/docs_findings.json')]
log_map={
 'g6g_geom2_first_exit_pinch.py':'root_confirm_first_exit_final',
 'g6g_geom2_vv_extremes.py':'root_confirm_vv',
 'g6g_geom2_g0_infinite_scale.py':'root_confirm_g0_infinite_scale',
 'geom3_brute_missing_diagonals.py':'root_confirm_geom3_brute_final',
 'geom3_area_double_rounding.py':'root_confirm_area_and_gap_final',
 'geom3_margin_normal_loss.py':'root_confirm_ee_normal_final',
 'root_power_range.py':'root_confirm_power_final',
 'root_polyhedron_mass_range.py':'root_confirm_mass_final',
 'docs_tight_cavity_pd.py':'root_confirm_cavity_pd_final',
 'docs_residual_claims.py':'root_confirm_docs',
}
items=[]
for f in sum(sets,[]):
    f=dict(f)
    f['summary']=f.pop('conclusion',f.get('summary',''))
    assert not re.search(r'\?{3,}',f['summary']+f['failure_scenario']+f['suggested_fix']),f['id']
    loc=f.get('file:line') or f"{f['file']}:{f['line']}"
    f['file:line']=loc
    script=f.get('repro_script') or re.search(r'review[/\\]repro[/\\][^\s]+\.py',f['how_to_reproduce'])[0]
    script=script.replace('\\','/')
    f['repro_script']=script
    assert (ROOT/script).is_file()
    f['how_to_reproduce']='python -X utf8 '+script
    stem=log_map[Path(script).name]
    meta=read('logs/'+stem+'.json');assert meta['exit_code']==0
    f['verified_output']=(R/'logs'/f'{stem}.log').read_text(encoding='utf-8')
    f['verified_log']='review/logs/'+stem+'.log'
    f['root_verified']=True
    f['repro_sha256']=sha(ROOT/script)
    items.append(f)
items.sort(key=lambda f:{'critical':0,'major':1,'minor':2}[f['severity']])
for n,f in enumerate(items,1):
    f['component_id']=f['id'];f['id']=f'G6G-{n:02d}'
counts={s:sum(f['severity']==s for f in items) for s in ('critical','major','minor')}
assert counts=={'critical':0,'major':9,'minor':2},counts
assert len({f['component_id'] for f in items})==len(items)
unconfirmed=[
 {'summary':'U形tight-fit seam原候选已撤回，不一定为拓扑∂E；最终只计L反角真边界。','counted':False},
 {'summary':'非平面源面is_convex/reflex与三角展开不同；诊断输入合同不明，未确认为合约内错误。','counted':False,'details':'review/notes/geom3_unconfirmed.json'},
 {'summary':'没有确认新的LP精确见证缺口、cache串用或薄壳反例；有限搜索不构成全称正确证明。','counted':False}
]
data={'review':'WO-G6G','head':head,'generated_utc':datetime.now(timezone.utc).isoformat(),
      'confirmed_counts':counts,'m0_exit_allowed':False,'full_suite':suite,
      'scope':'只读审查，所有产物在review；未修改tracked文件，未git写。',
      'findings':items,'unconfirmed':unconfirmed}
dump('G6G_findings.json',data)

g6e=read('notes/docs_g6e_replay_summary.json')
g6e += [{'g6e_id':23,'status':'已修：真实风险屏关闭变异4个目标断言红，原字节SHA已恢复',
         'script':'review/repro/root_lp_gate_mutations.py','verified_output':read('notes/root_lp_gate_mutations.json')[0]},
        {'g6e_id':47,'status':'已修：exact负功率换宽带，目标门3红/29绿，原字节SHA已恢复',
         'script':'review/repro/root_lp_gate_mutations.py','verified_output':read('notes/root_lp_gate_mutations.json')[1]}]
g6e.sort(key=lambda d:d['g6e_id'])
assert [d['g6e_id'] for d in g6e]==list(range(1,51))
dump('G6E_replay_ledger.json',g6e)

lines=['# WO-G6G：G6第七轮独立正确性复审','',
       f"**确认：critical={counts['critical']} / major={counts['major']} / minor={counts['minor']}。M0不得退出。**",'',
       '第六轮12条原始输入均已修；本轮新增9条major与2条minor，不把同类发现重复记为旧案未修。未修改实现代码。','',
       '## 全套自跑结果','',
       f"- HEAD `{head}`。",f"- `{suite['summary'].splitlines()[-1]}`；exit={suite['exit_code']}。",
       f"- 起止 UTC：{suite['started_utc']} → {suite['finished_utc']}；墙钟 {suite['elapsed_seconds']:.3f}s（并行审查共享机器，不能与实现方单跑时长直接比较）。",
       '- 命令：`'+suite['command']+'`；`PYTHONDONTWRITEBYTECODE=1`、`PYTHONIOENCODING=utf-8`。',
       '- tracked SHA-256差异0；'+link('review/logs/full_suite.log','全套原始日志')+' / '+link('review/logs/full_suite.json','命令与完整性元数据')+'。','',
       '## 已确认发现总表','',
       '|编号|严重性|位置|一句话结论|复现|','|---|---|---|---|---|']
for f in items:
    lines.append(f"|{f['id']}|{f['severity']}|`{f['file:line']}`|{f['summary']}|{link(f['repro_script'],'脚本')} / {link(f['verified_log'],'实跑输出')}|")
lines += ['', '## 逐条发现与总审查方核验输出','',
          '以下脚本 exit=0 表示**成功复现所断言的错误**，不是内核已通过新正确性门。每条日志均由总审查方在此HEAD再次运行，脚本SHA随JSON保存。','']
for f in items:
    lines += [f"### {f['id']} · {f['severity']} · {f['summary']}",'',
              '- 位置：`'+f['file:line']+'`。',
              '- 具体输入 → 错误输出：'+f['failure_scenario'],
              '- 直接运行：`'+f['how_to_reproduce']+'`。'+link(f['repro_script'],'复现脚本')+'。',
              '- 建议修复（审查方未实施）：'+f['suggested_fix']]
    if f.get('oracle_independence'):lines.append('- oracle独立性：'+f['oracle_independence'])
    if f.get('classification_basis'):lines.append('- 分级依据：'+f['classification_basis'])
    if f.get('related_locations'):lines.append('- 同根位置：'+', '.join('`'+p+'`' for p in f['related_locations'])+'。')
    lines += ['','```text',f['verified_output'].rstrip(),'```','']
lines.append((R/'notes/report_body.md').read_text(encoding='utf-8'))
lines += ['', '## 6. G6E 50条逐条重放台账','',
          '原输入/等价数值复现、内部等价变异与文档读回须区分；下表是处置核查，不是50个全域数学证明。完整输出：'+link('review/G6E_replay_ledger.json','机读逐案台账')+'。','',
          '|旧ID|当前状态/限制|脚本|','|---|---|---|']
for d in g6e:
    lines.append(f"|{d['g6e_id']}|{d['status']}|{link(d['script'])}|")
lines += ['', '## 7. 交付与复跑','',
          '- '+link('review/G6G_findings.json','最终机读发现')+'；'+link('review/ARTIFACT_INDEX.md','产物索引')+'；'+link('review/verification_integrity.json','tracked完整性及脚本哈希')+'。',
          '- '+link('review/repro/replay_confirmed.py','全部确认发现复跑入口')+'：`python -X utf8 review/repro/replay_confirmed.py`。',
          '- 最终聚合实跑：'+link('review/logs/final_confirmed_replay.log','10个唯一脚本全部复现成功')+'，reproduction_failures=[]。',
          '- 全套可用同一pytest命令重跑，注意删除/重写同一review日志不是修复；实现修复后应另做正确期望门，而非保留本轮“错误复现必须成功”的断言。','',
          f"G6G_DONE critical={counts['critical']} major={counts['major']} minor={counts['minor']}"]
(R/'G6G_report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')

files=['G6G_report.md','G6G_findings.json','G6E_replay_ledger.json','baseline_hashes.json',
       'notes/report_body.md','notes/geom2_coverage.md','notes/geom3_coverage.md','notes/docs_review.md',
       'notes/new_code_diff.patch','notes/whole_src_branches.json','notes/gates_docs_inventory.json',
       'notes/docs_claim_review.json','notes/root_lp_gate_mutations.json','logs/full_suite.log','logs/full_suite.json']
files+=sorted({f['repro_script'].removeprefix('review/') for f in items})
files+=sorted({f['verified_log'].removeprefix('review/') for f in items})
files+=['repro/replay_confirmed.py','repro/build_delivery.py','repro/build_root_findings.py']
files+=['repro/root_g6f10_replay.py','logs/root_g6f10_replay.log','logs/final_confirmed_replay.log','logs/final_confirmed_replay.json']
assert all((R/p).is_file() for p in files)
integrity={'head':head,'tracked_file_count':len(baseline),'tracked_sha256_changed':changed,
           'git_status':subprocess.check_output(['git','status','--short'],cwd=ROOT,text=True),
           'key_artifact_sha256':{p:sha(R/p) for p in files},'root_verified_findings':len(items)}
dump('verification_integrity.json',integrity)
index=['# G6G产物索引','',f'HEAD `{head}`；confirmed0critical/9major/2minor；M0不得退出。','',
       '只读审查；未修实现。最终报告中的链接覆盖关键成果，其余输入、初次运行失败及复制树保留在review。','']
for p in files+['verification_integrity.json']:
    index.append('- '+link('review/'+p))
(R/'ARTIFACT_INDEX.md').write_text('\n'.join(index)+'\n',encoding='utf-8')

bad=[]
for textfile in (R/'G6G_report.md',R/'ARTIFACT_INDEX.md'):
    for url in re.findall(r'\]\((file:///[^)]+)\)',textfile.read_text(encoding='utf-8')):
        from urllib.parse import unquote,urlparse
        path=unquote(urlparse(url).path).lstrip('/')
        if not Path(path).exists():bad.append([str(textfile),url])
assert bad==[],bad
assert (R/'G6G_report.md').read_text(encoding='utf-8').splitlines()[-1]=='G6G_DONE critical=0 major=9 minor=2'
print(json.dumps({'confirmed_counts':counts,'tracked_hash_changes':changed,'g6e_unique_ids':len(g6e),
                  'report_chars':len((R/'G6G_report.md').read_text(encoding='utf-8')),'broken_links':bad},ensure_ascii=False,indent=2))
