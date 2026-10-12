# R8FIX 二维初态与同类扫描子报告

## 范围与验收

- 主项：G6H-01，凹 E 紧配内缝的初态分类。
- 修改：[entrance.py](file:///D:/eab-wt/cx-e2/src/eab/kernel2d/entrance.py)、[exact.py](file:///D:/eab-wt/cx-e2/src/eab/kernel2d/exact.py)、[covers.py](file:///D:/eab-wt/cx-e2/src/eab/kernel2d/covers.py)、[geom.py](file:///D:/eab-wt/cx-e2/src/eab/kernel2d/geom.py)。新增 [48 格回归门](file:///D:/eab-wt/cx-e2/tests/test_r8fix_initial_state.py)。无旧测试改写、删减、skip 或 xfail。
- 回滚锚点：本目录 `before_entrance.py / before_exact.py / before_covers.py / before_geom.py` 为各自首次修改前的逐字节副本；不执行恢复，不覆盖其他任务的修改。
- 全部写入限于本工作树；未执行 Git 写操作。已有 CRLF/LF 用 `newline=''` 保留；`git -c core.whitespace=cr-at-eol diff --check -- src/eab/kernel2d tests/test_r8fix_initial_state.py` 通过。

## G6H-01：body 内部相交不等于拓扑 int(E)

### 修前红

独立 oracle 将 U 形体分为三个闭矩形，其差集矩形合并为 `E=[-2,2]×[-5/2,3/2]`。初态 `(0,0)` 严格位于该矩形内部；A 与两臂仅实体边界相触并不意味着位于 `∂E`。

[修前输出](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/initial_state/red.log) 原样末行：

```text
26 failed, 2 deselected in 0.41s
```

其中 24 格初态测试命中指定断言：

```text
assert got.kind == 'exit', ('topological interior must use exit policy', got)
E assert 'entrance' == 'exit'
```

另 2 格命中同类公开 membership 缺陷：`assert covers.membership_convex(A, B, p) == want`，实际 `0`，独立矩形 oracle 要求 `1`。

### 根因与修法

`polygons_overlap_exact` 正確报告实体内部交集 / 仅接触 / 分离；它不是一般凹对的拓扑 E 分类器。保留其原合同，另加 `entrance_membership_exact`：

1. 实体严格重叠或分离时直接返回正确状态。
2. 仅相触时，对耳切三角片形成精确三角片对 Minkowski 单元。
3. 取含初态的单元，以活动半空间构成局部切锥；检查所有活动直线的开角扇区是否被切锥并覆盖。
4. 每个扇区均被覆盖才是 int(E)，否则是真边界。全部分支只用 Fraction，无有限 epsilon 探针或舍入法向。

生产实现不调用 `g0_oracle`；该 oracle 的整数绕数 / 局部直线安排仍独立。新主门仅用 Cartesian 区间合并，不调用生产耳切、凸包、法锥或成员原语。

覆盖：原始 U、非对称 U；三尺度 `2^-8,1,2^8`；共同大平移 `0,1e6`；90° 旋转；精确紧配阈值 `1±2^-80`；经 `2^40` 剪切压窄的真实外部扇区；真实 E 边界和边界外小距离仍正确分类。

### 合同边界

本项修复的是进入 `shortest_exit` 的初态策略。该既有 API 明确为局部 VE/EV 最浅盖，不是一般凹对的全局 penetration depth。因此紧配缝可以返回 `kind='exit', gap=0`，这既不声称真实 `∂E` 距离为零，也不声称一次局部平移能使全部接触同时脱开。模块说明和函数说明已明确这一点；测试核对初态输出与既有 `shortest_exit` 一致，没有偷偷扩张或替换全局 PD 合同。

### 内部复原变异

把生产 `entrance.entrance_membership_exact` 恢复为旧 `polygons_overlap_exact`，而不是篡改输出，24 格均在上述 `kind` 断言红：

```text
24 failed, 24 deselected in 0.44s
```

[原样变异输出](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/initial_state/mutation_entrance.log) · [SHA 前后相同证据](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/initial_state/mutation_entrance.json)

## 同类扫描：已确认并同步修复的 3 处

### S2D-01：凹 membership 的相同拓扑误分类

`covers.membership_convex` 的非凸 fallback 与其四轴报告带探针原先均调用实体相交分类，故把内缝当边界，并可把虚假内缝当 tol 边界见证。二者均改为精确拓扑 E 分类；凸路径不变。

修前 2 格红见主红日志。复原生产 fallback 后仍在目标 `E topology mismatch` 断言红：`2 failed, 46 deselected in 0.10s`。

[变异日志](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/initial_state/mutation_membership.log) · [源哈希证据](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/initial_state/mutation_membership.json)

### S2D-02：cone_width 的极薄角相消及中间乘积范围错误

`cone_width` 原先先算浮点叉积/点积。给定有限 binary64 向量 `(1,1-2^-53)`、`(1-2^-53,1-2^-52)` 的精确叉积为 `-2^-106`，实际角应为 `-6.162975822039156e-33`，原实现返回 `0`；共同缩放 `2^-600/2^600` 还分别返回 `0/NaN`，而正确角为 `atan2(1,3)`。

修法：精确叉积和点积共同正缩放后才转 float、调用 atan2；非零角不可表达时响亮报错。零向量原先的 `0` 报告兼容性未扩张为新的判定。

- [修前红](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/initial_state/red_cone_width.log)：`4 failed, 1 passed, 37 deselected in 0.12s`。
- 恢复真实旧函数后：[变异日志](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/initial_state/mutation_cone_width.log)，`5 failed, 1 passed, 42 deselected in 0.12s`。多出的红格是追加的不可表达非零角必须报错门。
- [源哈希证据](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/initial_state/mutation_cone_width.json)。

### S2D-03：point_side 的同类行列式构造错误

公开 `point_side(p,a,b)` 原先先做浮点差/叉积。`M=2^40` 或 `2^50`，`a=(0,0),b=(M+1,M),p=(M,M-1)` 的精确行列式为 `-1`，却返回 `0`；共线 `1e200` 输入返回 `NaN` 而非 `0`。

修法：先精确提升、精确差和行列式，然后只对浮点调用者做最终受检舍入；纯有理调用者保留 Fraction，以免削弱 `interior_point` 的精确最远点排序。

- [修前红](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/initial_state/red_point_side.log)：`3 failed, 1 passed, 44 deselected in 0.13s`。
- [恢复旧函数变异](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/initial_state/mutation_point_side.log)：`3 failed, 1 passed, 44 deselected in 0.12s`；红在 `signed determinant lost` / 共线零行列式断言，不是偶然标签或浮点顶点选择。
- [源哈希证据](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/initial_state/mutation_point_side.json)。

## 扫描未见相同缺陷的路径及边界

- 二维 kernel 没有 Dual-through frozen/解析导数模块；实际冻结闭式在三维模块，由主任务其他子项审查。
- `covers._line_data / ve_cover / ev_cover / facet_gap / _project`，`entrance._feature_data / _contact_report / _facet_points`：均先精确坐标差、未归一化行列式或投影，再形成最终显示量。新增 3 个 `M=2^20,2^40,2^50` 大切向跨度、精确行列式为 1 的门，核对 `facet_gap / ve_cover / _contact_report`，全部通过；它们没有三维冻结路径“先单位法向再 dot”那条相消。
- `geom.turn_angle / vertex_turn / norm / unit / centroid / outward_normal` 已用 Fraction 派生量或受检平方根；未在本轮扫描中确认新的同类错误。`point_side` 是该层漏下的公开派生量，已补。
- `g0_oracle.ray_exit` 已在前轮区别真正外部扇区与紧配内缝，没有移用生产新 helper，从而保留独立性。
- 未声称完成任意凹 E 全局距离/全局 PD；非凸 tol 报告仍是已文档化的保守四轴见证，不声称欧氏带完备。

## 验证与可复跑命令

共同环境：

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONIOENCODING='utf-8'
New-Item -ItemType Directory -Force reports/codex/R8FIX_evidence/tmp | Out-Null
python -X utf8 -m pytest -q -p no:cacheprovider tests/test_r8fix_initial_state.py --basetemp=reports/codex/R8FIX_evidence/tmp/initial_green
```

[最终新门日志](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/initial_state/green.log)：

```text
48 passed in 0.33s
```

[变异重跑脚本](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/initial_state/replay_mutations.py)：

```powershell
python -X utf8 reports/codex/R8FIX_evidence/initial_state/replay_mutations.py entrance
python -X utf8 reports/codex/R8FIX_evidence/initial_state/replay_mutations.py membership
python -X utf8 reports/codex/R8FIX_evidence/initial_state/replay_mutations.py cone_width
python -X utf8 reports/codex/R8FIX_evidence/initial_state/replay_mutations.py point_side
```

每条预期退出码 `1`，均在子进程内恢复旧生产路径；磁盘生产源码 SHA 前后相同。常规测试本身还包含捕获这些目标 AssertionError 的变异守卫，正常跑全绿。

### 二维宽回归中间失败的如实记录

1. [首轮宽回归](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/initial_state/regression.log)：`1777 passed, 8191 deselected, 7 errors in 150.35s (0:02:30)`。7 个错误是 basetemp 父目录未建立的 `tmp_path` setup `WinError 3`，没有断言失败；创建父目录后排除。
2. [第二轮宽回归](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/initial_state/regression_final.log)：`3 failed, 1795 passed, 8195 deselected in 156.78s (0:02:36)`。运行期间追加 `cone_width` 行数，旧 Python 进程中函数 `co_firstlineno` 与新源文件错位，3 条 inspect-based mutation 门读到相邻函数（实际输出明确为 `_facet_normal_own` / `_ve_side`），导致 `source.count(needle)==1` 失败；没有改写、放松这 3 条旧门。
3. 源冻结后新进程重跑全部 48 格新门、失败的 `test_r7_third_vote_hull_vertices_match_and_catch_sign_flip`、整个 `test_perf_2d_directions.py`：[定向复核](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/initial_state/frozen_recheck.log) `77 passed in 0.82s`。

最终全仓结论以主任务在源冻结后跑的全套日志为准，本子报告不把中途宽回归声称为全绿退出门。新鲜 worktree 与 G6 独立退出审查仍由主任务明确其工单边界。

## 扩展同类扫描：三维初态与默认零裕度成员

同一实体接触/拓扑边界混用已在三维首入、默认精确零裕度成员确认并修复；完整数学方法、独立区间 oracle、修前 14 红、四个真实内部变异，以及冻结后 `30 passed in 3.41s` / 新旧门 `142 passed in 34.98s` 见[三维追加报告](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/initial_state/REPORT_3D.md)。局部出口零深度不等于全局 ∂E 的合同边界保持明确。
