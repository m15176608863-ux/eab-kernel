"""Scoped WO-E3E4 documentation edits, preserving existing line endings."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BACK = Path(__file__).resolve().parent / 'tmp' / 'docs_baseline'
BACK.mkdir(parents=True, exist_ok=True)


def read(name):
    p = ROOT / name
    dest = BACK / name
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists():
        dest.write_bytes(p.read_bytes())
    with p.open(encoding='utf-8', newline='') as f:
        s = f.read()
    return s, '\r\n' if '\r\n' in s else '\n'


def write(name, s):
    with (ROOT / name).open('w', encoding='utf-8', newline='') as f:
        f.write(s)


name = 'README.md'
s, nl = read(name)
lines = s.splitlines()
for i, line in enumerate(lines):
    if line.startswith('| L1 二维 |'):
        marker = '**按运动方向的首入**：'
        prefix = line.split(marker)[0]
        lines[i] = prefix + ('**E3 二维收尾（WO-E3E4，有定向门、待 G6）**：凸/凹首入初态与判定均对给定数据精确；凹 VE/EV 仿射根、各自时刻段内和前事件漏候选自校验在 Fraction 上完成，t_max 不被容差放宽。'
            '`tied_labels` 只报精确同时，接近项另报 `near_labels`；`shortest_exit` 精确比较在程负间隙的平方距离（局部最浅盖，不声称一般凹对全局最小分离；`test_kernel2d_entrance_e3.py`）。'
            '局部 VE/EV/VV 默认精确，显式长度/角度域窗口只放宽、不抬舍入地板，严格性与窗口活跃分开（`test_kernel2d_covers_e3.py`）；二维 `convex_hull` 返回精确极点，tol 不再隐式删点。'
            'bb52 的 53 条 legacy 窗口盖对账保留；运动首入门对精确微贯入另核局部出口，不把 FIT 内贯入当接触（`test_kernel2d_entrance.py::test_every_legacy_vertex_edge_contact_of_bb52_is_a_first_entrance_along_its_edge_normal`）。'
            '旧静态 `first_entrance_for_vertex` 仍不是一般凹块的运动首入。全套、突变、调用点分类见 `reports/codex/E3E4_report.md`，不等于 G6 退出 |')
    elif line.startswith('| L3 | 极限分析'):
        needle = '三维摩擦锥用 k 边内接棱锥'
        assert needle in line
        lines[i] = line.replace(needle, '**E4 自校验（WO-E3E4，有定向门、待 G6）**：静力平衡、对偶间隙、互补与机构容许性在同一精确模型上用有理数核验，tol 不再决定通过；LP 保留精确解见证，浮点视图用于展示。Fraction 的 10⁻³ 至 10⁻¹⁰⁰ 相对 α 错误、低摩擦/低黏聚、远体与细高体注入由 `test_limit_exact_selfcheck.py` 看护；既有反作用和静力手改门保留。多体可分辨性按各体自身接触形心与臂长，不借无关远体扩大尺度。`contact_forces`/`active` 仍是按 tol 截断的展示，静力证书是 lambdas；输入可分辨性仍非误差界，详见模块文档与工单报告。' + needle)
idx = next(i for i,line in enumerate(lines) if line.startswith('**E2 变更范围'))
lines.insert(idx + 1, '**E3E4 复核边界（2026-10-12）**：本单逐条重放第五轮指定的 14 条旧版本发现，并执行二维/极限分析新门与 10 项一次性源码突变；处置、红断言、旧门改写和全套耗时见 `reports/codex/E3E4_report.md`。这不是 50 条发现全部关闭，也不是六路独立 G6；用户禁止新建 worktree，本单仅本树验证，历史复核不自动覆盖新代码。')
write(name, nl.join(lines) + (nl if s.endswith(nl) else ''))

name = 'docs/canon_map.md'
s, nl = read(name)
replacements = {
    '凹首入、已侵入后的最短出口与局部单盖窗口路径未在 E2 精确化。': '凹首入、已侵入后的局部最浅盖与局部单盖在 E3 补精确化，极限自校验在 E4 改有理数；新门、10 项源码突变和全套结果见 `reports/codex/E3E4_report.md`。不等于独立 G6 或新鲜 worktree 验证。',
    '凹对仍用局部盖 + 容差谓词裁决，已侵入后的最短出口也仍是容差路径，留 E3。bb52 真几何的 53 条 legacy 顶点-边接触逐条对账门仍在。': 'E3 凹对用局部盖 + 精确相交裁决，候选仿射根、各自时刻段内和前事件漏候选自检均用 Fraction；已侵入按精确平方距离选局部最浅盖（不等于一般凹对全局最小分离）。并列只取精确同时，接近项另报。bb52 的 53 条 legacy 窗口盖验证保留，精确初态为侵入的格子改核局部出口。门 `test_kernel2d_entrance_e3.py` 与原 bb52 门。',
    '局部单盖/legacy 窗口仍用 `covers.py:62 normal_cone`、`:89 in_cone`。': 'E3 局部单盖默认也用精确符号，`covers.py:62 normal_cone`、`:89 in_cone` 只接受调用方明示的域窗口，不抬噪声地板。',
    '凹：局部单盖仍采用原窗口规则；': '凹：局部单盖精确，显式域窗口只放宽（`test_kernel2d_covers_e3.py`）；',
    '凹首入和已侵入后的 `shortest_exit` 仍用既有容差路径。': 'E3 凹首入和已侵入后的 `shortest_exit` 采用精确有理数选择；后者只是局部最浅盖。',
    '二维 E2 不主张已精确化凹首入或最短出口；': '二维 E3 精确门为 `test_kernel2d_entrance_e3.py`，brute 共用相交谓词仅作佐证，主 oracle 是闭式与测试内联 Fraction SAT；',
    '局部单盖枚举仍不产出 FF，其 legacy 窗口口径未改（附录 A.4）。': '局部单盖枚举仍不产出 FF；E3 保留明示 legacy 域窗口，不再抬到舍入地板（附录 A.4）。',
    '局部 VV 仍保持原窗口规则，门 `test_r3_numerically_collinear_vertex_yields_no_vv`，未纳入 E2 精确化。': 'E3 局部 VV 对给定坐标精确判锥交与严格活跃，精确平直点不产 VV；舍入成真小角时按真实数据判，门见 `test_kernel2d_covers_e3.py` 及改写后的 `test_r3_numerically_collinear_vertex_yields_no_vv`。',
    '并列报告仍可用窗口，输出法向/间隙/接触点仍是浮点构造；凹首入与已侵入后的最短出口未精确化，留 E3。': 'E3 的 tied_labels 仅含精确同时/同距，near_labels 另作可分辨性报告，不反馈选择；输出法向/间隙/接触点仍为浮点构造。凹首入、最浅局部出口与 brute 已精确化（`test_kernel2d_entrance_e3.py`）；brute 有扫描分辨率限制且与生产共用精确相交，不能冒充独立 oracle。',
    '（强对偶含黏聚耗散、互补残差）': '（E4：含黏聚耗散的静力、强对偶、互补均用有理数精确核；多体见 `limit_multi.py::check_duality_multi`，门 `test_limit_exact_selfcheck.py`、`test_limit_selfcheck.py`、`test_limit_multi.py`；浮点尺度仅作报告/输入可分辨性筛查）',
}
for old, new in replacements.items():
    assert old in s, old
    s = s.replace(old, new)
needle = '**二维**' + nl + nl
assert s.count(needle) == 1
s = s.replace(needle, needle + '- **二维凸包（E3）**：`kernel2d/geom.py::convex_hull` 接 `exact.hull_exact`，默认与显式 tol 均不丢真极点，tol 只保留签名兼容，不隐式简化；需简化的调用方应另行处理，不能以简化包作真值。门 `test_kernel2d_covers_e3.py::test_convex_hull_keeps_true_extreme_point_not_transitive_tolerance_pop`，第五轮 geom.py:434 的原构型与修前红断言见工单报告。' + nl)
write(name, s)

name = 'docs/exact_predicates_plan.md'
s, nl = read(name)
lines = s.splitlines()
for i,line in enumerate(lines):
    if line.startswith('| E3 |'):
        lines[i] = '| E3 | 二维剩余首入、局部 VE/EV/VV、边内与凸包 | WO-E3E4 实现并配门（2026-10-12，待所有者验收/G6）：凹初态/仿射根/段内/相交/漏候选自检在 Fraction 上做，局部出口按精确平方距离选最浅盖；精确并列与 near_labels 分开；显式域窗不抬噪声地板。`test_kernel2d_entrance_e3.py`、`test_kernel2d_covers_e3.py`，全套与突变证据见 `reports/codex/E3E4_report.md` |'
    elif line.startswith('| E4 |'):
        lines[i] = '| E4 | 极限分析有理数自校验 | WO-E3E4 实现并配门（2026-10-12，待所有者验收/G6）：LP 解保留有理数见证，静力/对偶/互补/容许性精确核同一模型；多体可分辨性按本体形心/臂长。`test_limit_exact_selfcheck.py`、既有 selfcheck/multi 门及源码突变；10⁻¹⁰⁰ 注入用 Fraction 保持可表达性，浮点已舍入成原值时不能声称能识别未表达的差异 |'
    elif line.startswith('- `ve_cover` / `ev_cover`'):
        lines[i] = '- E2 当时未修改局部单盖、凹候选和局部出口；E3 已补，见上表与 WO-E3E4 报告。没有实现凹块全局 E/盖裁剪，shortest_exit 不声称凹对全局最小分离。'
write(name, nl.join(lines) + (nl if s.endswith(nl) else ''))
