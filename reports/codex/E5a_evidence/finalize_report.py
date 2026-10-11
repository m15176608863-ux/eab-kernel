"""Only finalize the leave-tree verification after a complete green run."""
import json
import hashlib
from pathlib import Path
import xml.etree.ElementTree as ET

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
LABEL='full_leave_tree_final'
run=json.loads((OUT/f'{LABEL}.json').read_text(encoding='utf-8'))
assert run['returncode']==0,run['last_line']
assert run['changed_during_run']==[],run['changed_during_run']
assert all(hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==expected
           for path,expected in run['source_test_sha256'].items()),'Post-run source drift'
assert 'passed' in run['last_line'] and 'failed' not in run['last_line']
line=run['last_line']
elapsed=run['wall_seconds']
durations={}
for case in ET.parse(OUT/f'{LABEL}.xml').iter('testcase'):
    name=case.attrib.get('classname','unknown')
    item=durations.setdefault(name,dict(cases=0,seconds=0.0))
    item['cases']+=1
    item['seconds']+=float(case.attrib.get('time','0'))
ordered=sorted((dict(file=name,**item) for name,item in durations.items()),
               key=lambda item:item['seconds'],reverse=True)
(OUT/'performance_breakdown.json').write_text(json.dumps(dict(
    source=LABEL+'.xml',wall_seconds=elapsed,target_seconds=600,
    target_met=elapsed<=600,test_file_durations=ordered),indent=2),encoding='utf-8')
slow_table='\n'.join(f"| `{row['file']}` | {row['cases']} | {row['seconds']:.3f} |"
                     for row in ordered[:8])
report=ROOT/'reports/codex/E5a_report.md'
text=report.read_text(encoding='utf-8')
old='**正在集成验证，尚不得据本草稿声称全绿。最终结果在交付前替换本段。**'
new=f'''最后一次完整回归的 pytest 末行原样：

```text
{line}
```

独立进程 wall clock：**{elapsed:.3f} 秒**；运行前后全部 `src/`、`tests/`、`tools/` Python 文件 SHA256 无漂移，生成本结论前再次核对一致。完整命令、文件哈希、返回码见 [{LABEL}.json]({(OUT/(LABEL+'.json')).as_uri()})；[完整日志]({(OUT/(LABEL+'.log')).as_uri()})、[JUnit]({(OUT/(LABEL+'.xml')).as_uri()})。

命令为 `PYTHONDONTWRITEBYTECODE=1 python -X utf8 -m pytest -q -p no:cacheprovider tests --basetemp=reports/codex/E5a_evidence/tmp/{LABEL}_pytest --tb=short --durations=20 --junitxml=reports/codex/E5a_evidence/{LABEL}.xml`，另显式设 `TEMP/TMP` 到本树证据 tmp。此次完整测试期间没有其它本任务测试并行运行。

600秒目标：**{'达到' if elapsed<=600 else '未达到'}**。纯过滤微基准的加速不能覆盖精确三维几何、一般互锁枚举和新增完整独立 Fraction 候选 oracle 的成本；慢门逐项见日志。没有为达时限删格、skip/xfail 或减少边界探针。

JUnit 各测试文件耗时加总（非热点函数 profiler；包括测试与独立 oracle 成本）：

| 测试文件 | 格数 | 秒 |
|---|---:|---:|
{slow_table}

[全部文件计时]({(OUT/'performance_breakdown.json').as_uri()})。未把测试耗时归因于某个未经 profile 的生产函数。

已执行 `python -X utf8 tools/fix_canon_ptrs.py --apply`，最后一次为 `0 rewritten; 0 kept`。全绿只表示当前留树回归通过，**不解除范围违规，不使工单重新有效，也不是新 worktree/G6 退出**。此前中止/失败的分组日志全部保留，不冒充最终结果。'''
assert old in text
report.write_text(text.replace(old,new),encoding='utf-8')
result=dict(work_order='WO-E5a',delivery_status='E5a_BLOCKED',acceptance='VOID_SCOPE_VIOLATION',
  technical_scope='PARTIAL',full_suite=dict(last_line=line,wall_seconds=elapsed,
   source_drift=run['changed_during_run'],evidence=LABEL+'.json'),
  performance_target_seconds=600,performance_target_met=elapsed<=600,
  required_internal_mutants_killed=11,formal_G6=False,fresh_worktree_verification=False,
  scope_violation_evidence='scope_violation.json',external_cleanup_performed=False,
  remaining=['general legacy exact solid overlap/membership integration',
             'nonplanar general face-ring cover semantics','outer float construction search windows',
             'full E5b margin/entrance/interlock/frozen precision migration'])
(OUT/'final_status.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(line)
print(f'wall_seconds={elapsed:.3f}; code_drift=0; acceptance=VOID_SCOPE_VIOLATION')
attempts=[]
for label,meaning in [('full_verified','Completed but failed: 15 ideal-topology assertions required exact-input migration.'),
                      ('full_verified_final','Intentionally stopped at 413.268 seconds after read-only audit found two test-coverage gaps; not a passed run.'),
                      (LABEL,'Final complete leave-tree check, not valid acceptance after the scope violation.')]:
    data=json.loads((OUT/f'{label}.json').read_text(encoding='utf-8'))
    attempts.append(dict(label=label,meaning=meaning,returncode=data['returncode'],
                         last_line=data['last_line'],wall_seconds=data['wall_seconds'],
                         changed_during_run=data['changed_during_run']))
(OUT/'full_validation_attempts.json').write_text(json.dumps(attempts,indent=2),encoding='utf-8')
