# R9FIX 交付要素只读核对：G6I-02 / 05 / 06

## 范围与结论

本次为执行团队内部交付核对：读取原始 findings、相关源码/文档/测试和已保存日志，只写本目录报告与补丁建议，不修改冻结的 src/tests/tools/docs，不运行长测试。**不是独立六路 G6，也不授权 M0 退出。**

- G6I-02 / 05 原始建议、修前红、修后绿、真实函数内部变异与契约限制均有可定位证据。
- G6I-06 原始三个位置已修，已有红绿；当前文本门仅禁三段旧措辞，建议增强为正向契约检查和实际句段回退。另发现 README 路线段同类历史/现态混写，已通知主执行者；本报告生成时尚待其处理。
- 本次未重新跑全套，最终全套结果/耗时以主执行者最后冻结运行及总报告为准，不拿下列选组绿替代全套或 G6。

## 原始建议与逐条交付核对

输入：[G6I findings](file:///D:/eab-wt/cx-e2/reports/codex/inputs/G6I_findings.json)。本表是原 6 条中的 3 条，法锥同类扩展不另虚增发现数量。

| 项 | 原始建议与最终修法 | 修前红与修后绿 | 变异及目标断言 |
|---|---|---|---|
| G6I-02 major | 声明三角拓扑判凸性/凹棱，或明确拒收非平面源环。实现选择支持：`is_convex/reflex_edges/dihedral_turn` 先取 `exact_surface`，补出真实 `(5,7)`；公共法锥同类也已迁移，不能只补 descriptor 文案。 | [topology_before.log](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/topology_before.log)：`66 failed, 2 passed, 4 deselected in 0.64s`（含 05）；[topology_after.log](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/topology_after.log)：`200 passed in 0.97s`；扩组选组 [topology_legacy_final.log](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/topology_legacy_final.log)：`526 passed in 98.36s (0:01:38)`。 | [test_r9fix_topology.py](file:///D:/eab-wt/cx-e2/tests/test_r9fix_topology.py) 编译真实方法，将 `P = exact_surface(self)` 回退为 `P = self`；命中 `declared-roof-midpoint-concavity`、`declared-folded-reflex-ridge`、`actual-surface-right-angle`。公共法锥移除 exact_surface 的独立日志 [solid_cones_mutation.log](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/solid_cones_mutation.log)：`37 failed, 2 deselected in 0.20s`，不是注入假返回记录。 |
| G6I-05 minor | 逐连通表面分量核朝向/嵌套或收窄诊断；空腔不可机械要求全正体积。实现两者均做：精确分量体积、嵌套奇偶朝向、接触相交分量拒绝；文档撤销空列表的完整流形认证含义。 | 同一 topology 红绿日志保存 `64 + (-8) > 0` 仍漏报的原场景；额外守合法空腔、错误空腔、三层壳、反向外壳、接触相交及 `2^±600`。 | 真实 `_component_orientation_issues` 替换为仅总有理体积判断；`disconnected-inward-component` 报红。该内部变异由 `pytest.raises` 捕获，所以通过的变异测试在选组汇总中显示绿；不能把汇总绿误写成未触发缺陷。 |
| G6I-06 minor | 同步现态，历史格子/历史未审查状态标旧 HEAD，保留砖二未实现。canon 砖二现在区分命题 7 API 与命题 8/完整控制；README 明确历史 canon 重审不等于当前 G6/M0；invariance header 明确每格实际输入独立精确 oracle、没有隐式 tol_eff。 | [docs_red.log](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/docs_red.log)：`3 failed, 3 passed in 0.09s`；[docs_green.log](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/docs_green.log)：`6 passed in 0.05s`。 | 当前 `test_r9fix_docs.py` 将旧词附加到实际文档输入并检查 `G6I-06` 断言，属于文本输入变异，不是几何内部变异。可增强为替换当前对应句段，且逐条删除新契约边界后红，建议补丁见下。 |

公共法锥完整同类记录见 [solid_cones_summary.md](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/solid_cones_summary.md)；选组末行 `264 passed in 7.71s`。先前 topology_summary 的“公共法锥只收窄 descriptor 文案”是中间方案，已在该报告原位置订正，不再作为最后交付契约。

## 仍须明确的真实契约限制

1. **几何输入域**：实体凸性与凹棱以声明的闭合、嵌入、外向表面为前提，不把 `is_convex` 当所有非法网格的完整验收器。声明三角表面保留输入顶点编号，折面内部对角可以查询；不等于对源环做凸包或悄悄重编号。
2. **单盖和公共实体法锥不同**：公共法锥入口用声明表面；单盖显式 `_source_*` / `_q*` 和 `face_normal` 等 source-ring 描述符仍有窄契约，不是非平面折面实体的完整法锥。下一轮审查应区分这两个 API 层，不将豁免扩散到实体判定。
3. **诊断不是全域证书**：`manifold_issues` 不认证单个连通分量无自交、顶点链为圆或全部输入有效性。嵌套方向规则建立在不相交嵌入闭壳前提上；源环平面度仍是带 tol 的诊断，不参与实体分支。声明折面可能合法而其源环平面度诊断非空，不能反向混为实体拒收。
4. **角度与构造**：谓词符号精确；开方/比值/单位化走统一构造边界。`atan2` 的最终角度显示没有声称全域正确舍入。允许显示下溢的例外必须保留精确分支/证书，不能作为清零物理量的许可。
5. **文档真实未完成项**：命题 8 碰撞锥/完整首入控制（砖二）、一般凹体全局 E 等未完成项不能由命题 7 首入 API 已有而升级为完成。历史 canon 被独立审查不等于本次修改被独立审查。
6. **元检查局限**：静态 AST 门针对已知错误家族，不能形式化证明任意动态 Python 类型与全部数值数据流正确；文本门同样只能守已列契约片段，不能证明所有文档语义无矛盾。

## G6I-06 同类剩余及增强建议（尚未应用）

只读扫描发现 README “路线”段在历史 `<details>` 之外：本次读取时第 206 行仍称 canon_map“已写、与本文同批提交，未经 G6”，第 214 行仍称 GAP3 订正“未经 G6”；与已修第 109 行现态说明矛盾。第 205 行还保留“首入实现挪 M2”的旧口径。已通知主执行者。最小处理是把该路线段**明确标为历史 HEAD `094861c` 快照**，并给当前状态跳转说明；不抹除历史记录，不升级当前 M0。

准备的 [docs_gate_proposed.patch](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/docs_gate_proposed.patch) 仅增强 `tests/test_r9fix_docs.py`：

- 保留原三段旧措辞禁用断言，不放松；每条增加当前关键边界文本断言。
- 回退变异替换实际唯一新句段，不再 append 任意旧词。
- 增加删除新契约关键语句的变异，包括“命题 8/控制未实现”“历史审查不等于 M0”“逐格 oracle/无隐式地板”等。
- 草案在内存编译，`__file__` 设为预定 tests 目标路径；未写 tests。9 次测试函数/参数格调用成功，3 个句段回退和 9 个关键边界删除均命中预期断言，见 [docs_gate_proposal_check.log](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/docs_gate_proposal_check.log)。这是建议验证，不冒充已应用的 pytest 结果。
- README 路线段的新历史标记尚待主执行者决定，未把未落盘措辞写进草案硬编码门；应用时宜另守该历史标记及当前跳转提示。

## G03 首轮全套失败的根因与证据补交

详细记录在 [topology_summary.md 的 G03 末节](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/topology_summary.md)。两层根因：旧 NaN 注入探针被自动迁到只接收有限数据的 `scalar_exact`，检查本身先抛错；且生产 G03 报告器把坏显示候选传给更严格的新 norm 构造器，也抛错而不是出失败报告，原路径还略过 `None`。

修复保留原断言强度：NaN 探针直接读其原生 binary64 值；G03 `_display_witness_distance` 显式检查 None/非有限，再精确相减后构造距离。坏候选计为 construction failure，不能被其它有限最小候选藏住；精确 feature completeness 不受污染。

- [g03_display_before.log](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/g03_display_before.log)：`5 failed, 4 passed, 1 deselected in 0.36s`。
- [g03_display_after.log](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/g03_display_after.log)：`10 passed in 0.20s`。
- [test_r9fix_g03_construction.py](file:///D:/eab-wt/cx-e2/tests/test_r9fix_g03_construction.py)：枚举器内部注入 NaN、±Inf、None；去掉真实显示验证门的变异命中 `g03-invalid-display-recorded`。

此处全部为已存在证据的复核链接；没有重跑或假定本次最终全套已经完成。

## 主执行者收尾订正

README 路线已明确历史化；tests/test_r9fix_docs.py 增强门已应用，并补两处 entrance docstring 的现态门。第 7 节等过程中的待处理说明是当时状态，最终以主报告为准。

[最终主报告](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_report.md)。
