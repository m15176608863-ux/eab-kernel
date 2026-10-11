"""Record the full-suite exit limitation without changing executable source."""
from pathlib import Path
root=Path(__file__).resolve().parents[3]
marker='## WO-E5a2 退出状态：PARTIAL（2026-10-12）'
notice='''

## WO-E5a2 退出状态：PARTIAL（2026-10-12）

本单指定底层门与整数化对拍通过，但完整测试未全绿，不构成里程碑退出。严格表面语义揭示旧 interlock 近竖直事件被噪声政策丢弃：原80个竖墙输入中7格存在独立认证的更低分离高度，当前返回约1.2不是最小逃逸。不能把原最小逃逸门改成只检查安全上界。另有旧并列窗口突变牙失效；加强草案只在证据中，未应用。完整失败清单、实测耗时、独立反证及 WO-E5b 交接以 `reports/codex/E5a2_report.md` 为准；竖墙证书见 `reports/codex/E5a2_evidence/a1/walls_handoff.md`。没有宣称全套≤900秒、正式G6、新worktree或全链精确化通过。
'''
for relative in ('README.md','docs/canon_map.md','docs/exact_predicates_plan.md','docs/exact_3d_design.md'):
    path=root/relative
    with path.open(encoding='utf-8',newline='') as f: old=f.read()
    if marker not in old:
        with path.open('w',encoding='utf-8',newline='') as f: f.write(old+notice)
        print(relative)
