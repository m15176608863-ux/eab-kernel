"""Scoped documentation update; preserve all unrelated historical text."""
from pathlib import Path

root = Path(__file__).resolve().parents[3]

def transform(path, fn):
    with path.open(encoding='utf-8', newline='') as f:
        data = f.read()
    new = fn(data)
    with path.open('w', encoding='utf-8', newline='') as f:
        f.write(new)

def readme(data):
    lines = data.splitlines(keepends=True)
    seen = set()
    for i, line in enumerate(lines):
        if line.startswith('| L0 |') and 'L0' not in seen:
            seen.add('L0')
            lines[i] = '| L0 | 二维已有精确谓词门（见 E2/E3 报告）。**三维 E5a 部分实现，有门、未过 G6**：输入顶点精确凸包、仅精确共面归并、orient3d 保守过滤；显式 `exact_*` 三角表面成员/交点原语（`test_geom3_e5a.py`、`test_hull_robustness.py`、`test_geom3_merge.py`、`test_filtered_predicates.py`）。**旧一般 `polyhedra_overlap` / `point_in_polyhedron` / `segment_crosses_face` 尚未全量迁移**；不能把新增 API 当成旧相交 oracle 已精确。一般表面与显式凸包是不同几何模型，见 `docs/exact_3d_design.md`。既有一般距离/相交门保留，但不能据此宣称一般精确实体相交已完成 |\n'
        elif line.startswith('| L1 三维 |'):
            # Preserve historical G2/M2 constraints, not their obsolete precision claim.
            tail = line[line.index('**G2 对'):]
            tail = tail.replace('候选集来自 facet 型盖、精确谓词裁决', '候选集来自 facet 型盖、既有谓词裁决（完整精确化留 E5b）')
            lines[i] = '| L1 三维 | **E5a 凸路径已有精确门、未过 G6**：凸成员对原始坐标有理 SAT；局部 facet 与独立精确差点凸包标签全量双向核对；票三仅比较极点。G0 强制 E 顶点/棱中点/面重心，零跳样、零 ambiguous/low_e 豁免（`test_g03_e5a.py`、`test_covers3_g0_vote2.py`）。凸模型的标签属于 canonical view，源面非共面时不能直接解释成原 face 编号。一般单盖法锥/参数精确但仍按源面 Newell 语义，外层搜索窗及凹表面接入未完成；凹块 G0 仍只有既有分离侧距离完备性。' + tail
    return ''.join(lines)

def canon(data):
    pairs = {
        '（票三：锥相交裕度）': '（E5a 票三：精确锥交与极点集；差点先有理相减）',
        '三维 G0 的边界带跳过仍存在': 'E5a 三维 G0 同样零跳样，边界探针包含全部 E 顶点/棱中点/面重心；三维显式正 tol 为支撑平面距离带，不是完整欧氏偏移体',
        '三维票一仍跳过边界带。': 'E5a 三维票一也零跳样，票二/三零豁免，强制全部 E 顶点/棱中点/面重心；门 `test_g03_e5a.py`。',
        '三维 G0 仍跳边界带，二维 E2 已零跳样本但未普遍构造逐边界点 ±ε 双侧探针': 'E5a 三维 G0 与二维 E2 均已零跳样本，但未普遍构造逐边界点 ±ε 双侧探针，一般三维实体相交仍未全量精确化',
        '对二面角转角 ≤ tol 的棱返回 −1': '仅对精确平直棱返回 −1（不按噪声压平微二面角）',
        '归并只并**共棱连通**的共面面': '归并只并**共棱连通且精确共面**的面，非共面源面不能误并',
    }
    for old, new in pairs.items():
        assert old in data, old
        data = data.replace(old, new)
    anchor = '**三维**\n'
    assert data.count(anchor) == 1
    note = '''
**E5a 口径（2026-10-12，部分交付、未经 G6）**：显式凸 API 取顶点集的精确凸包，源 faces 只是来源提示。精确凸视图会拆开舍入后非共面的面，标签映射记录在 `source_vertices` / `source_faces`；一般 `vf_cover` 等单盖仍使用源面标签和精确 Newell 面向量，不是任意折面实体的完整法锥。凸定理不可直接外推到这一一般接口。设计与遗漏见 `docs/exact_3d_design.md`、`reports/codex/E5a_report.md`。

- **精确三票，不再是两把带宽尺**：票一独立原输入 SAT，全部随机与 E 顶点/棱中点/面重心计分；票二独立差点凸包按精确支撑集核全部标签；票三局部精确锥交与极点集一致。`ambiguous` 等兼容计数字段只能为零，不能成为通过理由。门 `test_g03_e5a.py` 含边界错票、错凸化、漏标签和极小真棱；oracle `g03_exact.py` 不调用被测几何原语。
- **原语迁移边界**：`exact_point_in_polyhedron` / `exact_segment_crosses_face` / `exact_triangle_intersection` 已有独立门；旧一般 `polyhedra_overlap` 等入口尚未全量接入，不声称一般三角表面三态相交已完成。`_seg_seg_distance` 近平行分支改用精确耦合参数（`test_geom3_e5a.py`）；外层 margin/entrance/interlock/frozen 只做必要兼容，不算 E5b 完成。
'''
    data = data.replace(anchor, anchor + note)
    # Membership branches no longer consume rounded support_gaps3.
    old = '现在：`support_gaps3`'
    new = 'E5a：`membership_convex3(tol=0)` 对 canonical convex view 的有理支撑平面取精确符号，绝不读取浮点 gap 作分支；`support_gaps3` 仅作构造输出。此前的构造说明：`support_gaps3`'
    assert old in data
    data = data.replace(old, new, 1)
    return data

transform(root / 'README.md', readme)
transform(root / 'docs/canon_map.md', canon)
