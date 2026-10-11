"""Bind final report, timing analysis and artifact index to completed full run."""
from pathlib import Path
import collections
import hashlib
import json
import re
import subprocess
import xml.etree.ElementTree as ET

E = Path(__file__).resolve().parent
ROOT = E.parents[2]
REPORT = ROOT / 'reports/codex/E5a2_report.md'


def read(name):
    return json.loads((E/name).read_text(encoding='utf-8-sig'))


def save(name, data):
    (E/name).write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


final = read('final.json')
assert final['sources_unchanged_during_run']
current = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
           for top in ('src','tests','tools') for p in sorted((ROOT/top).rglob('*.py'))}
assert current == final['source_after'], 'Source drift after final suite'
inventory = read('collection_audit.json')
assert not inventory['missing_original_nodes']
xml = ET.parse(E/'final.xml').getroot()
cases = list(xml.iter('testcase'))
assert len(cases) == inventory['current_count']
failed = [case for case in cases if case.find('failure') is not None or case.find('error') is not None]
skipped = list(xml.iter('skipped'))
passed_count = len(cases)-len(failed)-len(skipped)
failure_list = [dict(classname=case.attrib['classname'],name=case.attrib['name'],
                     message='\n'.join(child.text or '' for child in case if child.tag in ('failure','error')))
                for case in failed]
save('full_failures.json',failure_list)
stats = collections.defaultdict(lambda: [0,0.0])
for case in cases:
    key = case.attrib['classname'].split('::')[0]
    stats[key][0] += 1
    stats[key][1] += float(case.attrib.get('time',0))
files = [dict(file=k,cases=v[0],seconds=v[1]) for k,v in sorted(stats.items(),key=lambda pair:-pair[1][1])]
old = json.loads((ROOT/'reports/codex/E5a_evidence/performance_breakdown.json').read_text(encoding='utf-8'))
old_files = {row['file']:row for row in old['test_file_durations']}
comparison = [dict(file=row['file'],before_seconds=old_files[row['file']]['seconds'],
                   after_seconds=row['seconds'],before_cases=old_files[row['file']]['cases'],
                   after_cases=row['cases'],ratio=(row['seconds']/old_files[row['file']]['seconds']
                                                   if old_files[row['file']]['seconds'] else None))
              for row in files if row['file'] in old_files]
pytest_seconds = float(re.search(r' in ([0-9.]+)s',final['last_nonempty_line']).group(1))
met = final['wall_seconds'] <= 900 and final['exit_code'] == 0
ideal = final['wall_seconds'] <= 600
reasons = []
if failed: reasons.append(f'全套{len(failed)}失败（竖墙最早逃逸、旧门语义迁移及突变牙）')
if not met: reasons.append(f'≤900s未达，实测墙钟{final["wall_seconds"]:.2f}s')
outcome = 'E5a2_DONE' if met else 'E5a2_PARTIAL：'+'；'.join(reasons)
timing = dict(source='final.xml',wall_seconds=final['wall_seconds'],pytest_seconds=pytest_seconds,
              target_seconds=900,target_met=met,ideal_seconds=600,ideal_met=ideal,
              test_file_durations=files,per_file_comparison=comparison,
              previous_file_source='reports/codex/E5a_evidence/performance_breakdown.json',
              owner_baseline_seconds=1829,unadjusted_wall_ratio_not_speedup=final['wall_seconds']/1829,
              full_suite_passed=final['exit_code']==0,failures=failure_list,
              parallel_diagnostics_after_first_failure=True,
              note='File durations sum JUnit testcase setup/call/teardown. After failures appeared, short agent diagnoses ran in parallel; this is not a clean speed benchmark. Baseline/current semantic workload/count differ.')
save('performance_breakdown.json',timing)
source = REPORT.read_text(encoding='utf-8')


def section(name, content):
    global source
    pattern = rf'(<!-- {name}_START -->).*?(<!-- {name}_END -->)'
    source = re.sub(pattern,lambda m:m.group(1)+'\n'+content.strip()+'\n'+m.group(2),source,flags=re.S)


section('FINAL_RESULT', f'''**最终全套尝试（未全绿）：`{final['last_nonempty_line']}`**

- 包装器墙钟 **{final['wall_seconds']:.2f} s**；pytest 自报 **{pytest_seconds:.2f} s**。≤900 s目标：**{'达到' if met else '未达到'}**；≤600 s理想：**{'达到' if ideal else '未达到'}**。
- 原 {inventory['baseline_count']} 个节点全部保留，当前 **{len(cases)}**，新增 {len(cases)-inventory['baseline_count']}；运行期间及结束后源哈希一致。通过{passed_count}、失败{len(failed)}、跳过{len(skipped)}。**D全绿要求未满足，不得合并成已通过里程碑。**
- A1/A3指定底层接线与独立门已实现，但旧调用层集成收尾仍未完成；A2按允许的有限语义说明方案交付。留树供审查，**不建议按全绿成果合并**，不是G6或新worktree退出。
- 发现失败后并行进行了短诊断，故该墙钟是完整失败运行实测，**不是干净独占提速成绩**；未证明900秒达标。
- [完整全套日志]({(E/'final.log').as_uri()}) · [命令/源哈希/墙钟]({(E/'final.json').as_uri()}) · [失败明细]({(E/'full_failures.json').as_uri()})''')
named = ['test_invariance_interlock','test_invariance_geom','test_interlocking','test_interlock_sensitivity','test_covers3_g0_vote2','test_bb52_g1']
by_name = {row['file'].split('.')[-1]:row for row in comparison}
table = ['### 最终无 profiler 全套中的六文件耗时',
         '', '| 文件 | E5a JUnit / s | E5a2 JUnit / s | 后/前 | 原格→现格 |', '|---|---:|---:|---:|---:|']
for name in named:
    r=by_name[name]
    table.append(f"| {name} | {r['before_seconds']:.3f} | {r['after_seconds']:.3f} | {r['ratio']:.3f} | {r['before_cases']}→{r['after_cases']} |")
table += ['',f"E5a每文件基线来自历史完整JUnit汇总，不与cProfile时间混用；所有者提供的整套基线为1829秒。当前是失败运行，途中有短诊断并发，不计算净提速率。测试数由7907增至{len(cases)}且一般表面语义与独立oracle工作量增加，不能把整套差额归因到单个算术优化。",
          '', '### 当前剩余慢门（最终 JUnit 前15）','', '| 文件 | 格数 | 秒 |', '|---|---:|---:|']
table += [f"| {r['file']} | {r['cases']} | {r['seconds']:.3f} |" for r in files[:15]]
table += ['', f"[完整分文件对比]({(E/'performance_breakdown.json').as_uri()})。" ]
section('TIMING_TABLE','\n'.join(table))
section('FINAL_VERIFICATION', f'''**最终日志最后一行（原样）**：

```text
{final['last_nonempty_line']}
```

墙钟 `{final['wall_seconds']:.6f} s`；时间 `{final['start_utc']}` → `{final['end_utc']}`；退出码{final['exit_code']}；src/tests/tools前后哈希相同，结束后再次读回一致。JUnit共{len(cases)}条，通过{passed_count}、failure/error {len(failed)}、skipped {len(skipped)}。原7907节点无缺失，15个改写旧测试的装饰器不变，18项函数/辅助台账保存全文。62个fixtures文件与初始字节副本全部相同；HEAD仍为`5b09ea3`。

当前doc指针以 `fix_canon_final2.log` 和全套 `test_doc_pointers.py` 为证；追加PARTIAL说明后又运行 `fix_canon_postreport.log` 与 `doc_final.log`，1 passed。其余编排失败日志仅作过程审计，不计入最终成绩。''')
source=source.replace('<!-- FINAL_VERIFICATION_END -->','\n附加样式审计：`git diff --check` 仅报 `test_geom3_overlap_witness.py:389` 末尾多一个空行；为保持冻结测试字节未再编辑，见 `final_delivery_qa.json`。这不是测试通过声明。\n<!-- FINAL_VERIFICATION_END -->')
source = re.sub(r'<!-- OUTCOME -->\n.*\Z','<!-- OUTCOME -->\n'+outcome+'\n',source,flags=re.S)
groups=collections.Counter(r['classname']+'::'+r['name'].split('[')[0] for r in failure_list)
failure_table='\n\n### 完整失败分组（由最终JUnit生成）\n\n| 测试 | 失败格数 |\n|---|---:|\n'
failure_table+='\n'.join(f'| `{name}` | {count} |' for name,count in groups.items())
source=source.replace('<!-- FINAL_VERIFICATION_END -->',failure_table+'\n<!-- FINAL_VERIFICATION_END -->')
REPORT.write_text(source,encoding='utf-8')
contract=(E/'contract.md').read_text(encoding='utf-8')
contract=contract.replace('最终独占全套进行中。原7907节点全部保留，当前8002节点。',
                          f'完整全套尝试完成：{passed_count} passed / {len(failed)} failed，墙钟{final["wall_seconds"]:.2f}s；失败后有短诊断并发，不算独占速度成绩；原7907节点全部保留。最终状态：{outcome}。')
(E/'contract.md').write_text(contract,encoding='utf-8')
save('final_integrity.json',dict(source_matches_final=True,final_source_sha256=current,
                                report_sha256=hashlib.sha256(REPORT.read_bytes()).hexdigest(),
                                tests=len(cases),passed=passed_count,failures=len(failed),skipped=len(skipped),head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                                outcome=outcome))
links = [ ('总报告', REPORT), ('最终测试日志', E/'final.log'), ('最终运行记录', E/'final.json'),
          ('JUnit', E/'final.xml'), ('六文件完整profile与前20', E/'performance_review.md'),
          ('profile机读汇总', E/'profile_summary.json'), ('最终性能分解', E/'performance_breakdown.json'),
          ('测试改写逐条台账', E/'test_rewrites.json'), ('原节点保留审计', E/'collection_audit.json'),
          ('fixtures不变', E/'fixture_unchanged.json'), ('最终源完整性', E/'final_integrity.json'),
          ('A1证明与迁移', E/'a1/report.md'), ('A2/A3语义', E/'a3/notes.md'),
          ('interlock最小桥接', E/'a1/interlock_bridge_report.md'), ('桥接独立审查', E/'a3/interlock_bridge_review.md'),
          ('整数优化突变', E/'integer_mutations.json'), ('共面缺陷注入', E/'a1/mutation_coplanar.json'),
          ('交叉审查与既有缓存限制', E/'cross_review_performance.md'), ('A1/root交叉审查', E/'cross_review_a1_root.md'),
          ('全套失败明细', E/'full_failures.json'), ('竖墙严格反证与E5b交接', E/'a1/walls_handoff.md'),
          ('旧突变牙加强草案（未应用）', E/'a3/steep_tooth_proposal.md'), ('性能算法草案（未部署）', E/'next_performance.md'),
          ('3格零高度失败独立核验', E/'a1/invariance_brute_slide_handoff.md'),
          ('41格margin失败独立核验', E/'a3/margin_failed_exact_audit.md') ]
index=['# E5a2 证据索引','',outcome,'','## 关键入口','']
index += [f'- [{title}]({path.as_uri()})' for title,path in links]
changed_names = subprocess.check_output(['git','diff','--name-only'],cwd=ROOT,text=True).splitlines()
changed_names += [s for s in subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=ROOT,text=True).splitlines()
                  if s.startswith(('src/','tests/','docs/'))]
changed_paths = sorted({ROOT/name for name in changed_names})
changed = [dict(path=p.relative_to(ROOT).as_posix(),url=p.as_uri(),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in changed_paths]
save('changed_files.json',changed)
index += ['', '## 修改或新增的源码、测试与文档', '']
index += [f'- [{r["path"]}]({r["url"]})' for r in changed]
index += ['', '## 完整清单', '',f'- [文件哈希清单]({(E/"manifest.json").as_uri()})',
          '- tmp/ 内是原始源码/测试/输入快照、pytest临时文件及复跑脚本；不是新工作树，也不作为正式fresh-worktree验证。',
          '- *_running.json 保留启动证据，不表示进程仍在运行。中间 failed / diagnostic / mutation 红日志不能误读为最终运行失败。',
          '', '## 顶层及专项文件', '']
index += [f'- [{p.relative_to(E).as_posix()}]({p.as_uri()})' for p in sorted(E.rglob('*'))
          if p.is_file() and 'tmp' not in p.relative_to(E).parts and p.name not in ('INDEX.md','manifest.json')]
(E/'INDEX.md').write_text('\n'.join(index)+'\n',encoding='utf-8')
manifest=[dict(path=p.relative_to(ROOT).as_posix(),url=p.as_uri(),bytes=p.stat().st_size,
               sha256=hashlib.sha256(p.read_bytes()).hexdigest())
          for p in sorted(E.rglob('*')) if p.is_file() and p.name != 'manifest.json']
save('manifest.json',dict(report=dict(path=REPORT.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(REPORT.read_bytes()).hexdigest()),
                          workspace_changes=changed,files=manifest))
bad=[]
for p in (REPORT,E/'INDEX.md'):
    for link in re.findall(r'\]\((file:///[^)]+)\)',p.read_text(encoding='utf-8')):
        if not Path(link.removeprefix('file:///')).exists(): bad.append(link)
assert not bad,bad
print(json.dumps(dict(outcome=outcome,wall_seconds=final['wall_seconds'],tests=len(cases),artifacts=len(manifest),broken_links=bad),ensure_ascii=False))
