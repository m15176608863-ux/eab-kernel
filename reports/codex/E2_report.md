# WO-E2：二维凸路径精确化执行报告

执行日期：2026-10-11 至 2026-10-12。执行位置：[cx-e2](file:///D:/eab-wt/cx-e2)，分支 `e2-exact-wip`。

## 1. 结论与工作边界

E2 实现、旧口径测试改写、定向补门、13 项一次性源码突变和文档修订已完成。**最终全套 7500 passed，399.49 秒；无失败、跳过或 xfail**。所有修改留在本工作树，未提交。

- 初始 HEAD：`c7d8f0743bdd892f18aedb703199f94ac3e64dba`。首次检查源码/文档工作树干净；随后创建证据目录，故 `initial_status.txt` 只记录该目录未跟踪。
- 只编辑本树；未运行 commit、push、reset、checkout、stash 或 worktree 操作；未删除 fixtures。
- 局部 `ve_cover`、`ev_cover`、`vv_cover`、`enumerate_covers` 的函数源文本逐个与 HEAD 比较完全一致；62 个已跟踪 fixture 的原始 blob 哈希全部未变。证据：[范围审计](file:///D:/eab-wt/cx-e2/reports/codex/E2_evidence/scope_audit.json)。
- 本工单不是 G6 退出。按工单禁止新建工作树，**未作新鲜 worktree 验证**；这项纪律 D 检查与独立六路 G6 留给所有者后续验收，不能用本树全绿替代。
- 回滚锚点：上述 HEAD、未提交差异及突变原字节备份。每个突变在 `finally` 中恢复，并核对原始/恢复 SHA-256；没有用 git 丢弃改动。

## 2. 验证结果与耗时

所有 Python 运行均设置 `PYTHONDONTWRITEBYTECODE=1` 并使用 `python -X utf8`；pytest 禁用 cacheprovider，临时目录置于本树证据目录。

| 阶段 | pytest 原样末行 | 说明 |
|---|---|---|
| 改动前二维门 | `34 failed, 1297 passed in 76.51s (0:01:16)` | 工单指定二维文件，通配符在 PowerShell 显式展开，exact 文件不重复收集 |
| 改动前全套 | `35 failed, 7208 passed in 409.91s (0:06:49)` | 35 项完整失败节点见下节与机读台账 |
| 改动后二维门 | `1588 passed in 70.40s (0:01:10)` | 没有失败、跳过或 xfail |
| 指针门 | `1 passed in 0.04s` | 已运行 `tools/fix_canon_ptrs.py --apply` |
| 最终全套 | `7500 passed in 399.49s (0:06:39)` | 最终源码快照全绿；运行前后所有 src/tests Python 文件哈希一致 |

最终全套命令：

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:TEMP="$PWD/reports/codex/E2_evidence/tmp"
$env:TMP=$env:TEMP
python -X utf8 -m pytest -q -p no:cacheprovider tests
```

工单历史参考为 **7169 条、约 463 秒（7 分 43 秒）**；本树改动前实际收集 **7243 条**（7208+35），不是同一测试集合。最终比较会同时列本树实测基线和工单参考，不能把单次耗时差解释成受控性能基准。

最终 pytest 用时 **399.49 秒**，端到端启动计时 **401.02 秒**。相对工单 463 秒参考减少 **63.51 秒（13.7%）**；相对本树改动前 409.91 秒减少 **10.42 秒（2.5%）**。测试数量相对本树原始 7243 条增加 **257 条**，相对工单 7169 条增加 **331 条**。

最终复跑之前还有一轮全套 `7500 passed in 399.16s (0:06:39)`；只读复核随后发现一个测试 docstring 把独立 SAT 写成旧耳切-SAT，修正该注释后重新执行突变与全套，上表以最后一轮为准。两轮均保留日志，未用更快的一轮冒充最终结果。

[最终全套机读记录](file:///D:/eab-wt/cx-e2/reports/codex/E2_evidence/final_full_result.json)包含命令、返回码、墙钟时间、原样末行和运行前源码哈希。

日志：[原始全套](file:///D:/eab-wt/cx-e2/reports/codex/E2_evidence/baseline_full.log)、[最终二维](file:///D:/eab-wt/cx-e2/reports/codex/E2_evidence/final_2d.log)、[最终全套](file:///D:/eab-wt/cx-e2/reports/codex/E2_evidence/final_full.log)。

## 3. 原始失败清单与逐条处置

**35 项均有明确处置，没有删测试或改成 skip/xfail。** 原始失败为 34 项旧语义/旧注入路径门，加 1 项文档指针失效；另外在审查中发现的真实实现缺陷见第 4 节，不能混称全部只是测试过时。

完整逐节点列表（含参数、分类、处置）见 [失败清单 Markdown](file:///D:/eab-wt/cx-e2/reports/codex/E2_evidence/failure_inventory.md) 与 [JSON](file:///D:/eab-wt/cx-e2/reports/codex/E2_evidence/failure_inventory.json)。以下为全部失败族，合计 35 格：

| 原测试（省略目录） | 失败格 | 旧口径 | 新口径及不弱于旧门的理由 |
|---|---:|---|---|
| `test_a_t_vertex_one_ulp_above_the_lowest_edge_is_still_convex` | 4：quarter 0–3 | 一个 ulp 微凹按容差接收，强制 4FF | 改名 `...uses_the_concave_path`：四朝向、三种 tol 均精确拒收；另留真平直对照、原 300 点，对独立 Fraction 矩形减三角缺口闭式 oracle 全等，不跳边界 |
| `test_true_parallel_edges_with_length_ratio_1000_merge_after_rotation` | 10：seed 0–9 | 理想几何平行即强制旋转后 4FF | 改名 `test_parallel_edges_with_length_ratio_1000_merge_only_if_exact_after_rotation`：FF 逐标签等于内联 Fraction 反平行边对；facet 总数同时核对；原随机姿态、单位和 G0 保留，零豁免 |
| `test_a_vertex_fifty_tolerances_inside_the_hull_is_rejected` | 1 | 50t 拒收、0.5t 接收 | 两个原输入不删，均要求精确拒收；精确平直可接受仍由原 96 格门看护 |
| `test_the_length_tolerance_is_the_slack_for_the_long_edge_rotation` | 2：C=1、1e5 | δ=tol/2 合并，δ=2tol 不合并 | 改名 `test_length_tolerance_never_changes_exact_parallel_merging`：原两倾角保留，新增 δ=0 和三种 tol，完整标签/顶点不随 tol 改变；三种几何产物互异 |
| `test_r7_third_vote_hull_vertices_match_and_catch_sign_flip` | 1 | 反转浮点法向必须令旧 G0 红 | 保留浮点法向反号对独立边公式的构造量检查；另把真实 `membership_exact` 内部打坏，要求 G0 **16 个精确边界 0→1** 失配，不靠输出后造假数据 |
| `test_hull_defect_threshold_is_pinned_on_an_edge_away_from_the_start` | 2：深度 2t、0.5t | 2t 拒、0.5t 收；靠已删凸包深度诊断；带内允许失配 | 两个原深度均拒收；每格 2000 随机点加 3 个边界邻点，对不共用耳切/SAT 的独立闭式 Fraction oracle 零错，并要求三种状态都出现 |
| `test_convex_g0_is_invariant` | 14：squares 6、brick_square 8 | 舍入后的平行边仍强求原 FF 标签不变 | 每个变换完整标签对独立全顶点投影 oracle，成员对独立精确 SAT 零错；判据余量在舍入带外仍要求标签/状态不变；边界态不强求理想几何标签，但绝不免除数据正确性检查 |
| `test_every_code_pointer_in_canon_map_names_a_function_at_its_current_line` | 1 | WIP 源码删函数/挪行后文档仍指旧地址 | 更新二维语义、删除已不存在的方向窗指针，再跑指针工具；原断言一字不放松 |

### 原来绿、但仍需加强的门

- `test_degenerate_parallel_edges_membership_still_exact`：删除 `m==0 or b==0` 跳样，保留 500 随机点并增加方块边/角边界，全部对独立精确 SAT。
- 票三微倾 24 格改为 `test_vote_three_keeps_exact_kinks_without_ambiguous_exemptions`：不再 `ambiguous<=2`，要求 `ambiguous=0`、严格顶点精确全等、全部边界参与。
- 随机单位缩放成员门保留 60×20 点，先核 tol=0 精确三态，再核报告带不能翻号；短倒角门取消 FF 短边豁免与 0 跳样。
- T 形短边杠杆门保留 24 格及分离/贯入两侧；改用显式扇片和内联 Fraction 投影 SAT，不经被测耳切/几何原语；明确 1e-6 余量大于舍入界才要求不变。
- 精确层随机门去掉潜在 skip；固定严格凸样本的可分辨性改成必过断言。补精确角序、法锥同向/边界、共线点剔除、微凹分派、平直链、报告带与凸首入闭式门。

**旧门无法按原语义保留的部分**：微凹接收、tol 内合并 FF、噪声带豁免、边界 FF 绝对不变与法向反号影响成员，不是 E2 合同；均已用更精确、覆盖原输入的断言替换，不存在未补偿的删除。窗口化局部盖和 legacy 门继续保持原口径，不能擅自精确化它们。

## 4. 实现修复摘要与独立 oracle

1. **G0 平直链票二真缺陷**：一边有平直分段时，FF 归并后余下 VE/EV 可能只是边界支持，不是严格 facet。原来简单 `glob=非FF` 在单位方块/T 形方块上假红。现在局部严格集、边界集及 walk 标签都核对独立全顶点投影支持集；不是把 ambiguous 两边豁免。
2. **报告带真缺陷**：旧凸路径用舍入后的 `facet_gap` 判断 tol，能把实际内部点吞成 0；非凸回退又经浮点 translate/舍入地板。现在凸路径用精确点到 E 闭线段距离平方，不开平方、不看浮点 gap；外角也按欧氏距离而非 max 支撑间隙。非凸保持精确分类，只在四轴 ±tol 精确探针提供边界见证时报告 0，详见残余边界。
3. **凸首入真缺陷**：WIP 仍用两次 gap 差分斜率和固定角阈值作分支。现在对精确 E 的 inward cross 作有理数半空间裁剪；精确初态、时刻和 `t_max` 比较，不把小非零速度夹平、不用 tol 放行 miss。初始恰相触按闭集定义 t=0，角点全部精确活动侧入并列报告。gap、法向、接触点仅在输出构造；凹首入和 `shortest_exit` 未改。
4. **G0 独立性**：票一 SAT 的坐标差与投影全部内联，脱离 `exact._sub/_cross/_dot` 等被测原语；票二独立全投影；票三独立 Fraction gift-wrap，对照 E 严格顶点。原语毒化测试确认 oracle 不调用被测几何原语。
5. **边界不跳样**：G0 同时保留原浮点舍入探针，并加 Fraction 的真 E 顶点/中点，`band_skipped=0`。没有用增加边界点替换旧随机样本。

报告带新增 166 格在旧真实源代码上为 `13 failed, 153 passed`，修复后 `166 passed`；其中 12 格是带外吞噬/浮点构造缺陷，1 格是显式记录新保守非凸报告政策，不能把后者算成旧实现正确性缺陷。见 [补充说明](file:///D:/eab-wt/cx-e2/reports/codex/E2_evidence/report_band_notes.md)。

## 5. 一次性源码突变结果

执行脚本：[run_mutations.py](file:///D:/eab-wt/cx-e2/reports/codex/E2_evidence/run_mutations.py)。每次只改真实函数内部一处，独立 pytest 进程执行指定门，随后按原字节复原。详细失败堆栈、JUnit、前后 SHA-256 和原文件备份见 [突变目录](file:///D:/eab-wt/cx-e2/reports/codex/E2_evidence/mutations/) 与 [结果 JSON](file:///D:/eab-wt/cx-e2/reports/codex/E2_evidence/mutations/results.json)。

| ID | 突变 | 具体看护断言（测试均在 `test_kernel2d_exact.py`，例外另注） | 结果 |
|---|---|---|---|
| M01 | `_angle_less` 同半平面叉积反号 | `test_angle_order_is_the_exact_cyclic_order_in_both_halfplanes`：八方向序 `(i<j)` 不符 | 1 failed，语义抓住 |
| M02 | 精确平行分支先走 B | `test_exact_parallel_edges_merge_into_ff_and_nothing_else_does`：方块的 4FF 标签不符 | 1 failed，语义抓住 |
| M03 | 删除折回检查 | `test_convexity_rejection_names_the_first_foldback_and_winding_defect` 与 lever 专门诊断门：应 `folds back`，实际 `reflex vertex 2` | 2 failed，**仅诊断抓住；拒收仍由反射检查完成** |
| M04 | 删除 descents 绕圈检查 | `test_convexity_rejection_names_the_first_foldback_and_winding_defect`：绕两遍方块应明确 `winds 2 times`，实际 None | 2 failed；其中直接诊断等式是目标牙，另一个旧星形门 TypeError 不单独当证据 |
| M05 | 删除平直法锥同向检查 | `test_flat_vertex_cone_is_one_ray_not_a_line`：反向射线应 -1，实际 0 | 1 failed，语义抓住 |
| M06 | 法锥严格 `>` 改 `>=` | `test_corner_cone_boundary_is_not_strict`：两条锥边界应 0，实际 1 | 2 failed，语义抓住 |
| M07 | 成员边界 0 改内部 1 | `test_exact_membership_boundary_is_not_the_interior`：方块边/角 × 三尺度应 0 | 6 failed，语义抓住 |
| M08 | strict_vertices 保留共线 | `test_strict_vertices_discard_flat_chain_subdivision_vertices`：应恰四个严格角点/闭式集合 | 2 failed，语义抓住 |
| M09 | hull `<=0` 改 `<0` | `test_exact_hull_discards_collinear_boundary_points`：三尺度共线边点不能多计 | 3 failed，语义抓住 |
| M10 | polygons 相触当分离 | `test_exact_overlap_on_a_concave_l_shape`：L 形接触应 0，实际 -1 | 2 failed，语义抓住 |
| M11 | triangle 相触当分离 | `test_triangle_exact_touch_is_not_separation`：正/反朝向接触应 0 | 6 failed，语义抓住 |
| M12 | 非精确凸 membership 强送凸路径 | `test_membership_nonexact_convex_input_uses_the_simple_polygon_path`：应返回闭式三态，错误路径抛精确凸性 ValueError | 3 failed，实际错误分派被抓 |
| M13 | first_entrance 选路改回 `is_convex(A,r)` | `test_first_entrance_routes_rounded_reflex_input_away_from_the_convex_path`：应返回 t=1 的入口，错误分派抛 ValueError | 1 failed，实际错误分派被抓 |

没有未说明的逃逸。**结论是 12 项目标语义缺陷被捕获，加 1 项专门诊断改变被捕获，不是“13 项均证明拒收/判定能力非冗余”。** 对 M03 没有证明删除折回检查会扩大接受集合；现有示例存在后续反射检查冗余。所有突变都核实失败断言，不把随机生成器报错或测试收集错误充当牙。

## 6. 文档、交付与残余边界

- 已更新 [README](file:///D:/eab-wt/cx-e2/README.md) 的 L1 二维和复核覆盖、[正本映射](file:///D:/eab-wt/cx-e2/docs/canon_map.md) 的二维精确口径/旧方向窗及 G0 三票、[精确谓词计划](file:///D:/eab-wt/cx-e2/docs/exact_predicates_plan.md) 的 E2 状态及 E3 分界。
- 当前 exact 层使用 Fraction，**尚未实现一般位置浮点快路**；计划中的过滤优化不能写成已验证性能事实。
- 非凸 tol=0 分类精确；非凸 tol>0 是**有见证、无带外误吞的保守报告带**，不保证检出全部带内点。完整非凸 E 的欧氏边界报告带未完成，不属于本单二维凸路径的完成声明。
- 凹首入、已侵入后的最短出口、局部候选盖的窗口判据仍是旧容差路径（E3/M3 后续）；构造量仍是浮点。二维凸精确化不等于整个几何核都已精确化。
- 初始浮点输入已经包含舍入，边界几何经刚体运动后的真实数据可以改变；保证的是每组数据的答案正确，不是强制保留理想平行/共线标签。
- 未作工程验证、性能基准认证、姊妹求解器切换或 G6 退出声明；未提交。

交付索引与完整未提交文件清单：[INDEX](file:///D:/eab-wt/cx-e2/reports/codex/E2_evidence/INDEX.md)。

E2_DONE
