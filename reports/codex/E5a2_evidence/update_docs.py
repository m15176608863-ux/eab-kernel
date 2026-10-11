"""Update only the four requested status/design documents, preserving newlines."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def edit(file, replacements, append=''):
    path = ROOT / file
    with path.open(encoding='utf-8', newline='') as stream:
        original = stream.read()
    text = original
    for old, new in replacements:
        assert text.count(old) == 1, (file, old)
        text = text.replace(old, new)
    if append:
        newline = '\r\n' if '\r\n' in original else '\n'
        text = text.rstrip('\r\n') + newline * 2 + append.strip().replace('\n', newline) + newline
    with path.open('w', encoding='utf-8', newline='') as stream:
        stream.write(text)


edit('README.md', [
    ('**旧一般 `polyhedra_overlap` / `point_in_polyhedron` / `segment_crosses_face` 尚未全量迁移**；不能把新增 API 当成旧相交 oracle 已精确。一般表面与显式凸包是不同几何模型，见 `docs/exact_3d_design.md`。既有一般距离/相交门保留，但不能据此宣称一般精确实体相交已完成',
     '**E5a2 已将旧一般三入口接入精确三角化表面路径**（`test_e5a2_surface.py`）：仅对有效、定向朝外、闭合、嵌入的表面；非平面环确定性耳切，不自动凸化。一般重叠用有理平面分区及内部见证，涵盖共面分支；非法/自交表面不在证明范围。一般表面与显式凸包是不同模型，见 `docs/exact_3d_design.md`。实测与未达项见 `reports/codex/E5a2_report.md`，不是 G6 退出'),
    ('一般单盖法锥/参数精确但仍按源面 Newell 语义，外层搜索窗及凹表面接入未完成；凹块 G0 仍只有既有分离侧距离完备性。',
     'E5a2 枚举窗口从原坐标精确比较距离平方，正 tol 凸成员带为完整欧氏边界距离（`test_e5a2_covers.py`），不读构造 gap 作这些分支。一般非平面源环单盖仅为 Newell 向量/首顶点锚平面/源拓扑描述符，不是折面实体完整法锥；反例门固定见证不在折面上、环起点改变描述平面及标签域分离。凹块 G0 仍只有既有分离侧距离完备性。'),
])

edit('docs/canon_map.md', [
    ('三维显式正 tol 为支撑平面距离带，不是完整欧氏偏移体',
     'E5a2 三维显式正 tol 改为到完整 E 边界的欧氏距离带，外角/外棱不能仅用支撑平面距离判带内（`test_e5a2_covers.py::test_membership_report_band_is_euclidean`）'),
    ('旧一般 `polyhedra_overlap` 等入口尚未全量接入，不声称一般三角表面三态相交已完成。',
     'E5a2 的旧一般 `polyhedra_overlap` / `point_in_polyhedron` / `segment_crosses_face` 已接精确三角表面路径，限有效朝外闭合嵌入表面；一般重叠的平面分区/共面内部有理见证由 `test_e5a2_surface.py` 看护，源码删除共面支路的突变命中目标断言。'),
    ('一般三维实体相交仍未全量精确化；G1 不比锁态',
     'E5a2 已接通有效闭合三角表面的精确实体三态，但一般单盖折面法锥与 E5b 后继判据仍未完成；G1 不比锁态'),
], '''### E5a2 补充边界（有门，未过 G6）

- 一般单盖：源非平面 ring 只解释为精确 Newell 向量、首顶点锚平面、投影绕数及源邻接描述符；即使算术精确，见证也不一定在折面实体上。门 `test_e5a2_covers.py::test_source_ring_descriptor_is_not_a_folded_surface_cover`、`::test_source_ring_descriptor_keeps_source_labels_separate_from_convex_views`。
- 枚举域窗与构造输出分开：六类盖从原数据比较精确距离平方；`Cover3.gap` 仍是浮点构造，不影响窗口开闭。恢复 gap 分支的内部突变由真实下溢格捕获。
- 本单没有新浮点过滤或新缓存层。性能改动为精确整数代数、既有缓存载荷的等价整数形式及不影响答案的延后计算；逐 Fraction 对拍见 `test_e5a2_integer_arithmetic.py`、`test_e5a2_bilinear_integer.py`。完整 profile/全套计时与未达项见 `reports/codex/E5a2_report.md`。
''')

edit('docs/exact_predicates_plan.md', [
    ('**WO-E5a 部分实现，未验收、未过 G6**', '**WO-E5a 按部分完成验收为 `5b09ea3`，E5a2 续作留树、未过 G6**'),
    ('一般旧 `polyhedra_overlap` / `point_in_polyhedron` / `segment_crosses_face` 入口尚未全量迁移，不能称三维几何核已全部精确。',
     'E5a2 已将三个旧一般入口接入有效朝外闭合嵌入表面的精确三角化语义，正 tol 凸成员为完整欧氏边界带，枚举窗口不再读构造 gap。一般源环单盖只保证 Newell 锚平面描述符边界，不声称完整折面法锥。门 `test_e5a2_surface.py`、`test_e5a2_covers.py`；这仍不是三维所有调用层全部精确。'),
    ('以 `reports/codex/E5a_report.md` 的独立整套实测为准。', 'E5a2 的完整 profile、整数化对拍、全套实测及未达项以 `reports/codex/E5a2_report.md` 为准；目标为 <=900 秒、理想 <=600 秒。'),
    ('- 一般多边形面上的单盖暂以精确 Newell 面向量解释局部法锥，不是完整折面实体语义。新 `exact_*` 表面原语不等于旧入口已接通；凹块全局 E、一般精确实体相交及 E5b 的完整迁移仍未完成。',
     '- 一般非平面源环单盖只解释为精确 Newell 向量及首顶点锚平面/源拓扑描述符，**不称为折面实体法锥**。E5a2 已接旧一般表面入口，限有效朝外闭合嵌入表面；凹块全局 E、完整折面法锥及 E5b 的迁移仍未完成。'),
    ('- `membership_convex3(tol=0)` 为精确三分；显式正 tol 保留支撑平面距离带，不是完整欧氏偏移体。`enumerate_covers3` 外层浮点 gap 搜索窗仍为遗留适配点。',
     '- `membership_convex3(tol=0)` 为精确三分；E5a2 正 tol 是完整欧氏边界带，外部用精确最近凸组合证书，平面距只作下界。`enumerate_covers3` 六类窗口改用原数据精确距离平方；后继 margin/entrance/interlock/frozen 的构造量分支不因此自动精确。'),
])

edit('docs/exact_3d_design.md', [
    ('全套目标600秒，交付实测而非预估。', 'E5a2 全套目标 <=900 秒（理想 <=600 秒），交付实测而非预估。'),
], '''## 8. WO-E5a2 已接线范围与仍不可推论的范围

### 一般闭表面

旧 `point_in_polyhedron`、`segment_crosses_face`、`polyhedra_overlap` 已调用有理表面路径。契约前提为有效、定向朝外、闭合、嵌入的有界表面；不声称自动修复自交、非流形或反向输入。凸 SAT 快路先证明输入每个三角平面对全部原顶点均为支撑平面，不能用凸包替换一般实体。

一般内部重叠：用对方所有三角平面分割每个三角面；共面时还按对方三角边直线分割。每个开二维单元内对方成员状态不变。非空有界三维交集必有一片开边界，或者位于另一实体内部，或者两表面共面且内侧一致。单元有理重心沿内向法线推进，步长是所有平面的首个正截距的一半；再以精确成员核验其同时在两体严格内部，得到证书，而不是随机微推。点成员用精确射线退化换向；线段接口只报告横穿，非共面折棱切向接触不应算穿透。门与内部突变见 `test_e5a2_surface.py` 及本单报告。

点的正 tol 是到三角表面的欧氏报告带；实体相交的正 tol **只在分离侧**报告表面距离带，真实内部重叠始终为 1。旧门中舍入后真实微贯入从“相触”转为内部，原输入/全部网格保留，以独立精确 oracle 迁移；margin 的贯入哨兵因此随之生效，但本单不宣称 margin 其余分支已精确。

### 一般单盖的有限解释（A2 选择允许的边界说明方案）

源面标签的 VF/FV 用 Newell 方向及通过首顶点的锚平面；域判据用主投影绕数；棱/顶点方向由源拓扑产生。对非平面环，这只是描述符：循环移动首顶点可以改变 gap，投影见证可能不在任意源三角面上。两个实值反例门固定此界限（`test_e5a2_covers.py`）；不可称其为三角化折面实体的完整法锥或真实接触见证。canonical convex-view 的标签域独立保留。

### 距离窗口与性能

枚举六类窗口用原坐标的精确平方距离，盖 gap/normal/witness 仍是构造输出。凸 E 正 tol 的内侧最短支撑平面距离等于边界距离；外侧支撑平面距仅是下界，剩余候选由 `conv({b-a-x})` 的精确最小范数点证书裁决。外角例及恢复平面带的真实内部突变有门。

性能优化没有引入新的浮点过滤或缓存层：三维 Fraction 点叉积延迟到最后一次规范化，独立 SAT 与凸成员平面用等价整数行，二维已为 Fraction 的符号用整数分子，EE 参数延后到锥接受之后。既有浮点/Dual 算术次序与独立 oracle 边界不变；逐值对拍、profile、实测和保留的 E5b 工作见 `reports/codex/E5a2_report.md`。本单禁止新 worktree，所有本树回归都不是正式独立六路 G6 退出。
''')
print('Updated README, canon_map, exact_predicates_plan and exact_3d_design.')
