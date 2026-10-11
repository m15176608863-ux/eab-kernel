"""Fill verified completion facts only after the final full-suite evidence exists."""
from pathlib import Path
import json
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
result = json.loads((HERE / 'final_full_result.json').read_text(encoding='utf-8'))
assert result['returncode'] == 0 and not result['source_changed_during_run']
match = re.fullmatch(r'(\d+) passed in ([\d.]+)s(?: \([^)]*\))?', result['last_line'])
assert match, result['last_line']
count, seconds = int(match[1]), float(match[2])
def comparison(reference):
    change = reference - seconds
    return f'{"减少" if change >= 0 else "增加"} **{abs(change):.2f} 秒（{abs(100*change/reference):.1f}%）**'
p = ROOT / 'reports/codex/E2_report.md'
s = p.read_text(encoding='utf-8')
s = s.replace('**最终全套验证运行中，结果待下节更新**。',
              f'**最终全套 {count} passed，{seconds:.2f} 秒；无失败、跳过或 xfail**。')
s = s.replace('| 最终全套 | **运行中** | 结束后填入原样末行与耗时，不提前报绿 |',
              f"| 最终全套 | `{result['last_line']}` | 最终源码快照全绿；运行前后所有 src/tests Python 文件哈希一致 |")
anchor = '不能把单次耗时差解释成受控性能基准。'
addition = (f'\n\n最终 pytest 用时 **{seconds:.2f} 秒**，端到端启动计时 **{result["wall_seconds"]:.2f} 秒**。'
            f'相对工单 463 秒参考{comparison(463)}；'
            f'相对本树改动前 409.91 秒{comparison(409.91)}。'
            f'测试数量相对本树原始 7243 条增加 **{count-7243} 条**，相对工单 7169 条增加 **{count-7169} 条**。'
            '\n\n最终复跑之前还有一轮全套 `7500 passed in 399.16s (0:06:39)`；'
            '只读复核随后发现一个测试 docstring 把独立 SAT 写成旧耳切-SAT，修正该注释后重新执行突变与全套，'
            '上表以最后一轮为准。两轮均保留日志，未用更快的一轮冒充最终结果。'
            '\n\n[最终全套机读记录](file:///D:/eab-wt/cx-e2/reports/codex/E2_evidence/final_full_result.json)'
            '包含命令、返回码、墙钟时间、原样末行和运行前源码哈希。')
assert s.count(anchor) == 1
s = s.replace(anchor, anchor + addition)
s = s.replace('- 局部 `ve_cover`、`ev_cover`、`vv_cover`、`enumerate_covers` 的既有窗口化实现保持不变。',
              '- 局部 `ve_cover`、`ev_cover`、`vv_cover`、`enumerate_covers` 的函数源文本逐个与 HEAD 比较完全一致；62 个已跟踪 fixture 的原始 blob 哈希全部未变。证据：[范围审计](file:///D:/eab-wt/cx-e2/reports/codex/E2_evidence/scope_audit.json)。')
s = s.replace('E2_BLOCKED：最终全套验证尚在运行，待结果写入',
              '交付索引与完整未提交文件清单：[INDEX](file:///D:/eab-wt/cx-e2/reports/codex/E2_evidence/INDEX.md)。\n\nE2_DONE')
with p.open('w', encoding='utf-8', newline='') as f:
    f.write(s)

plan = ROOT / 'docs/exact_predicates_plan.md'
with plan.open(encoding='utf-8', newline='') as f:
    s = f.read()
old = '已实现并配定向门（2026-10-11，WO-E2）：'
new = f'WO-E2 已完成（2026-10-12；本树全套 {count} passed，待所有者验收/G6）：'
assert s.count(old) == 1
with plan.open('w', encoding='utf-8', newline='') as f:
    f.write(s.replace(old, new))
print(result['last_line'])
print('Report completed; final marker E2_DONE')
