# 追加只读交叉扫描（源与测试零修改）

> 本文冻结的是发现时的只读扫描状态；此后主任务批准同治，三维初态和默认零裕度成员现已修复。红绿、内部变异和独立交叉核验见[三维补充报告](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/initial_state/REPORT_3D.md)。下文“当前”“未改”均指首次扫描时，不代表最终遗留。

## 新确认的同类初态问题

扫描发现 **G6H-01 的三维同构问题仍存在**，位置 `src/eab/kernel3d/entrance3.py::first_entrance3` 初态仍以 `polyhedra_overlap(At,B,0)==1` 决定是否调用局部 `shortest_exit3`。

构造：将二维原 U 形沿 `z∈[0,1]` 挤出；A 是 `box(center=(.5,1,.5),half=(.5,.5,.25))`。独立 Cartesian 三箱差集并给出：

```text
E = [-2,2] × [-5/2,3/2] × [-3/4,3/4]
x0 = (0,0,0) ∈ int(E)
B.manifold_issues() = []
polyhedra_overlap(A,B) = 0
```

当前实际输出：

- `d=(1,1,0)` 或 `(1,0,0)`：`kind='entrance', t=0`。
- `d=(0,1,0)`：`RuntimeError: first_entrance3: no in-extent facet-cover candidate, yet the bodies touch at t = Fraction(0, 1); the candidate set missed an earlier entrance`。
- 直接 `shortest_exit3` 则返回 `kind='exit', gap=0`（局部最浅盖；不声称全局 PD）。

这不是新数值相消，而是同一“实体仅接触不等于拓扑 ∂E”的几何分类问题。未改三维源；已交主任务决定修复或如实列遗留。

- [可复跑脚本](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/initial_state/scan_3d_initial_state.py)
- [实际结果及源 SHA 前后相同证据](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/initial_state/scan_3d_initial_state.json)

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -X utf8 reports/codex/R8FIX_evidence/initial_state/scan_3d_initial_state.py
```

## 本次检查的数值路径

本次限定排除正在由其他代理修改的 frozen / margin 以及主代理负责的 LP。

| 路径 | 检查结论 |
|---|---|
| `covers3._qnormal / _qedge / _project_face / vf_cover / fv_cover / ee_cover / ve3_cover / ev3_cover / vv3_cover` | 活动判定、间隙分子、平方距离、投影参数在 `_qvector` 提升后形成；未发现先单位法向 dot 再判组合的活动路径。 |
| `covers3._cover_in_window / facet_plane3 / facet_gap3 / support_gaps3 / membership_convex3` | 距离窗和成员用原始数据的精确分子/分母；公开 gap 用最终 `sqrt_rational`，不是舍入单位法向 dot。 |
| `entrance3` 的候选时刻、`shortest_exit3` 的平方深度、`merge_degenerate` | 使用精确方向和平面；未确认新的大跨度相消。上述初态实体/拓扑混用则确有反例。 |
| `geom3.angle_between / face_area / centroid / _segment_closest_points / _point_face_distance / exact_*` | 相关派生量先精确；本次未确认新的相消反例。 |
| `exact_sweep.surface_events / star_core / contact_models` | Fraction 输入与有理平面/事件处理；没看到单位化结果回流到分支。 |
| `geom3._active_normals / _gordan_direction / _contact_cone_witness / _inward_vertex_direction`；`covers3._orth` | 内部仍保留旧浮点单位化/噪声代码，但源码搜索未见当前公开生产调用路径；不将死私有路径的潜在问题冒充公开 API 确认缺陷。 |
| `geom3.manifold_issues / _find_interior_point` | 仍使用诊断平面度窗口或试探构造；有精确成员复验/失败时报错。有限扫描未确认静默错误，未声称其证明级完备。 |

这是限时、静态为主加具体运行反例的交叉扫描；不是任意尺度或所有公开 API 的无缺陷证明。
