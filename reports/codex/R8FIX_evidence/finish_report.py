"""Fill final report only after the machine verification has succeeded."""
from pathlib import Path
import json
import re
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
v = json.loads((OUT/'verification.json').read_text(encoding='utf-8'))
assert v['verified'] is True
meta = v['full_suite']
new = sum(v['new_test_counts'].values())
attempts = [(name,json.loads((OUT/name).read_text(encoding='utf-8'))['elapsed_seconds'])
            for name in ('interrupted_first_full_suite.json','failed_margin_contract_full_suite.json','full_suite.json')]
total = sum(seconds for _,seconds in attempts)
paragraph = f'''最终 pytest 运行 **{meta['elapsed_seconds']:.3f} s 壁钟**，退出码 0；{'低于' if meta['elapsed_seconds'] <= 900 else '超过'} 900 s。使用 4 个本地 worker，完整收集 **{v['junit_testcases']} 格 = 原 9851 + 新增 {new}**，无失败、错误、skip 或 xfail；没有缩格。

- [全套原样日志](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/full_suite.log) · [命令/环境/时间/SHA](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/full_suite.json) · [JUnit逐格结果](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/full_suite.junit.xml)。
- [机器验收](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/verification.json) 为 `verified=true`：{v['tested_snapshot_files']} 个冻结输入文件无漂移/新增，{v['fixture_count']} 个基线夹具字节未改；所有原测试函数和参数装饰器保留，HEAD 未变，`git diff --check` 通过。各旧测试断言的语义改写另有第 4 节台账，AST 检查不冒充语义证明。
- 指针最终同步及定向门通过，实际记录见 [canon日志](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/canon_apply_final.log)；复跑命令如下。
- 三次全仓尝试的累计壁钟 **{total:.3f} s**（中止 {attempts[0][1]:.3f} + 旧合同失败 {attempts[1][1]:.3f} + 最终全绿 {attempts[2][1]:.3f}），{'超过' if total > 900 else '未超过'} 900 s。追加公开差值修复、旧断言合同冲突和完整重跑造成这些额外时间；900 s 内指标仅对应最终完整验收，不把中止/失败伪称成功或藏掉。定向回归、变异和独立审计耗时另留各日志。'''
path = ROOT/'reports/codex/R8FIX_report.md'
with path.open(encoding='utf-8',newline='') as f:
    source = f.read()
assert source.count('__FULL_SUMMARY__') == source.count('__FULL_VERIFICATION__') == 1
source = source.replace('__FULL_SUMMARY__',meta['last_line']).replace('__FULL_VERIFICATION__',paragraph)
source = source.replace('**当前结论：等待最终完整测试；M0 仍待下一轮独立 G6，不因本树修复/全绿而退出。**',
    '**当前结论：原 6 条及本次确认的同类缺陷已修复，最终全套与机器验收通过；修改未提交。M0 仍待下一轮独立 G6，不因本树全绿而退出。**')
source = source.replace('R8FIX_PARTIAL：等待冻结后的最终全套验证','R8FIX_DONE')
assert '__FULL_' not in source and source.rstrip().endswith('R8FIX_DONE')
with path.open('w',encoding='utf-8',newline='') as f:
    f.write(source)
missing=[]
for uri in re.findall(r'\]\((file:///[^\n]+?)\)', source):
    decoded=unquote(urlsplit(uri).path).lstrip('/')
    if decoded.replace('\\','/').lower().startswith('d:/eab-wt/cx-e2/') and not Path(decoded).exists():
        missing.append(uri)
result = dict(report=path.as_uri(), missing_local_links=missing, full_attempt_seconds=attempts,
              total_full_attempt_seconds=total, final_state='R8FIX_DONE')
(OUT/'report_checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
raise SystemExit(bool(missing))
