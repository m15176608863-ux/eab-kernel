"""Scoped UTF-8/newline-preserving documentation sync; never touches external canon."""
from pathlib import Path

root = Path(__file__).resolve().parents[3]
banner = '> **WO-R8FIX（2026-10-12，修复留树，待独立 G6）**：本轮 G6H 确认 6 条 major；逐条红绿、内部变异、旧门对照、同类扫描和全套实测见 [R8FIX 报告](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_report.md)。当前合同补充见 [R8FIX 设计同步](file:///D:/eab-wt/cx-e2/docs/r8fix_design_sync.md)。本树同步不等于只读外部正本已回写；M0 退出状态不升级。'
for rel in ('README.md', 'docs/canon_map.md', 'docs/exact_predicates_plan.md', 'docs/exact_3d_design.md'):
    path = root/rel
    with path.open(encoding='utf-8', newline='') as stream:
        text = stream.read()
    if '**WO-R8FIX' in text:
        continue
    newline = '\r\n' if '\r\n' in text else '\n'
    first, rest = text.split(newline, 1)
    with path.open('w', encoding='utf-8', newline='') as stream:
        stream.write(first + newline*2 + banner + newline + rest)
