# M5c 研究合同与证据主张边界复核

## 1. 范围与结论

本次只读核对 R3 的理论、数值合同、命名门及已完成研究证据，并经主代理授权订正数值合同的文义。由 R3 实现作者进行，**不是新增独立几何 oracle，也不是完整六路 G6 审查**。

结论：未发现新的 critical / major；发现并澄清 3 项 minor 文档/覆盖边界问题。只修改 `docs/m5c_numeric_inventory.md`，本复核另落一份 Markdown；没有改动绑定的 src、tools、tests、研究 JSON 或运行收据，也未因文档调整重跑或改写数值结果。`docs/m5c_research_theory.md` 当前文义已准确，无需修改。

| 项目 | 原风险 | 处置 |
|---|---|---|
| 命名门追踪 | R3 诊断/简单环合同仅指向文件或泛称，难以辨认确切门 | inventory 改为下节的现有测试函数名；13 处命名测试引用经 AST 名单核对全部存在 |
| 正分母准入域 | “正分母”可能被理解为接受所有数学上处处正的分母 | 明确当前准入要求分母在整个 `[0,1]` 的 Bernstein 下界严格正；是保守可认证域，不满足时 ValueError，不作错误签发 |
| 有限对抗覆盖 | 920 与 138 条扰动若合称为“时间和身份均核对”会多声称；线性名义轨迹也不能冒称覆盖一般有理 P2 | inventory 明确 920 核身份及括区，138 仅核 contact 状态及身份；90 个名义构造均 D=1，不把它们计作非恒定分母连续扰动覆盖 |

核查入口：[数值合同](file:///D:/eab-wt/cx-e2/docs/m5c_numeric_inventory.md)、[理论证明与 C1 草案](file:///D:/eab-wt/cx-e2/docs/m5c_research_theory.md)、[R3 测试](file:///D:/eab-wt/cx-e2/tests/test_m5c_certificates.py)、[独立对抗复核](file:///D:/eab-wt/cx-e2/reports/codex/M5c_evidence/review_r3.md)。

## 2. R3 主张到命名门

以下测试均位于 `tests/test_m5c_certificates.py`，除特别注明的已有 base 准入门。命名门验证给出的有限构造；任意连续管内路径的保证仍来自充分条件证明，而非把有限样本数充作证明。

| 公开主张 | 现有命名门 / 主 oracle |
|---|---|
| 同时间相减可消去共同平移，不牺牲分离包含性 | `test_common_translation_cancels_exactly`；独立构造平移后的两三角形，精确恒定间隙 |
| 等号不能签为严格分离 | `test_relative_separation_equality_mutation_fails_semantics`；真实内部 `_separation` 的 `>`→`>=`，错误签发穿过公开 API，红于 `equality is not separation` |
| 简单凹环可以获单首盖证书 | `test_concave_single_cover_matches_closed_form_oracle`；独立 tip-wall 闭式首时刻 `(1+db-da)/2` 及唯一右端顶点身份；生产证书输出同时核标签和括区 |
| 不能只凭相邻转角放过非局部自交 | `test_nonlocal_edge_crossing_is_rejected_by_simple_ring_guard`；`test_removed_simplicity_internal_guard_fails_semantics` 将真实内部 `_simple` 返回改为 1，红于 `self-intersecting ring cannot receive first-cover certificate` |
| 近并列、端点/VV 不得在未排除竞争时签发 | `test_near_ties_and_endpoint_ties_are_never_signed`；`test_tangent_touch_and_invalid_indices_are_not_certified` |
| 精确坐标、半径、窗口与非 bool 整数索引准入 | `test_r3_rejects_nonexact_coordinates_radii_and_windows`；`test_tangent_touch_and_invalid_indices_are_not_certified`；base 的 `test_robustness_does_not_accept_invalid_windows_denominators_or_radii` |
| 刚体/单位变化遵守应有协变关系 | `test_relative_simple_certificate_rigid_unit_covariance`；有理旋转、非零大平移、极大/极小单位尺度；L∞ 管依诱导范数保守变换，而不是声称任意旋转下轴对齐管逐点不变 |

已完成测试收据为 **14 收集 = 14 执行，0 失败、0 skip**；上表两项真实内部变异独立于源码哈希门，以具体语义断言杀死。该收据的 4 个声明 source_hashes 当前仍逐一一致。本次未新增/重跑 pytest，因此不把文档核对冒称新的测试运行。

## 3. oracle import 清单与独立性

生产受测对象 `m5c_certificates` 只直接导入 `fractions.Fraction` 与原 `model_robustness`。测试脚手架导入被测对象不等于用它构造期望答案。

1. `tests/test_m5c_certificates.py` 的闭式 oracle：`fractions.Fraction`、`itertools.product`；`pytest` 及 `mutation_support.replace_module_callable` 仅是参数化/真实内部变异脚手架。期望首时刻、标签、拒绝条件不使用生产求根、相交、朝向、投影或包络原语。
2. 常值逐顶点扰动 oracle：`tests/m5c_teeth_oracle.py` 仅导入 `fractions.Fraction`；独立枚举线性入射和闭边投影。
3. 首末独立偏置 oracle：`tests/m4c_independent_oracle.py` 导入 `dataclasses.dataclass`、`fractions.Fraction`、`math.isqrt/lcm`、`eab.kernel2d.g0_oracle.overlap`；独立三点插值/二次代数根与入射判别。
4. `g0_oracle` 的完整直接 imports：`fractions.Fraction`、`math.lcm`、`eab.oracle_construction.sqrt_exact/scalar_exact`。其中 overlap 主体使用独立整数提升、winding 和闭段相交；不经 R3 的几何原语。后两个显示构造 helper 并非该 overlap 路径的几何判定实现。
5. 继续展开仓内 import：`oracle_construction` 导入 `decimal.Decimal/DecimalException/localcontext`、`fractions.Fraction`、`functools.lru_cache`、`math`、`struct`、`numeric_domain.ConstructionDomainError`；`numeric_domain` 导入 `fractions.Fraction`、`math`。这份清单没有遗漏因显示辅助导入而加载的仓内模块，也没有把普通 Fraction 算术误称为共同几何原语。
6. 简单环独立 oracle 在 `tools/m5c_independent_review.py` 内直接枚举闭线段交会与邻边重叠，不调用生产 `_simple/_event/_relative` 来生成期望。
7. 初态管反例使用 `g0_oracle.overlap`，独立性同上；它证明的是显式管内配置存在接触，不是用 R3 的拒绝理由反推真值。

[独立复核脚本](file:///D:/eab-wt/cx-e2/tools/m5c_independent_review.py)的生产调用仅获得待核证书，独立 oracle 另算期望。共同基础设施/标量运算不代表共享生产几何原语。

## 4. 对抗与凹环边界

独立复核的 90 个名义案例获证 23 个，其余 67 个拒绝或不适用。对获证者的 920 条逐顶点常值坐标偏置，同时断言独立首盖标签与首时刻在证书括区；138 条首末独立顶点偏置产生的非刚体线性轨迹，只断言独立结果是 contact 且标签一致。源码中后者没有首时刻括区断言，故**本报告不声称 138 条实测时间括区零失配**。两组均未发现其各自已断言的错误认证。

所有这 90 个名义构造都是 D=1 的仿射轨迹；即使首末顶点偏置不同而不再刚体，它仍不是非恒定分母的 P2。一般有理路径/任意连续扰动的论证来自相对有理恒等式、包络包含性、严格分离和简单环首交定理；这 1058 条有限搜索不直接验证全部此域。

简单环专项为 80 个构造、38 个获证、760 条坐标角点扰动，独立闭段相交 oracle 未发现错认证。6 个结构反例均被拒绝。简单凹环与自交环不能混淆：R3 允许凹性，不允许未排除的非邻边交会、倒折或退化。

理论里的简单性只认证 `[l,h]`；同伦方向论证局限于固定同一时刻的管内配置。没有声称从初态跨过 `[0,l]` 始终简单/方向不变；早期凸包分离已足以排除块间更早接触。振荡连续扰动可以有多个事件根，因此这里保证第一接触特征身份和位置括区，不保证根唯一、导数保持或未知真实物理路径已被观测。

另有 3 个显式初态管反例（bb03、bbF038、bbS038 各 1）属于**不锚定初态的常量半径管**内顶点配置，不能说成真实 P1/P2/P3 初态不一致；真实三模型共享初态。其余 65 个未搜到这个有限角点反例，不等于有稳健初态分离证书。详见[初态管反例](file:///D:/eab-wt/cx-e2/reports/codex/M5c_evidence/research_initial_tube_witnesses.json)。

## 5. 正分母保守准入的只读复现

取 `D(s)=(s-1/2)^2+1/100`，幂系数 `(13/50,-1,1)`。其 `[0,1]` 上真实最小值为 `1/100>0`，但二次 Bernstein 系数是 `(13/50,-6/25,13/50)`，当前整体包络下界不为正。将两个分离的常量三角形分别写成 `Nx=xD, Ny=yD` 后调用公开 `relative_separation_certificate`，本轮只读探针观察到：

`ValueError: positive denominator certificate required`

这不是错误签发，而是当前程序不接纳所有数学有效的正分母表示。base `_validate` 始终在 `[0,1]` 检查，并非只在调用者局部窗口检查。数值合同现已如实登记这一保守域。该探针没有改动生产、没有增加永久 pytest 门，亦没有把拒绝保守性包装为提高认证覆盖率的新功能。

## 6. 研究统计与全时程边界

已完成 r4 研究流遍历 1810 步 / 64010 对，以旧完整回放定位全部 68 个新接触候选，仅对这些 68 对重新求 P1/P2 并核原始 status/features/time。R2 2 对全部保留，R3 合并为 **19/68**，其余 49 对未证；未证集不外推。它不是“R3 再对 64010 对全部重新求根”。最终对新完整回放的全对齐与联合发布是另一项证据，不能由本复核代替。

19 对中 raw 主参考及主参考+VV 各命中 7/19；把明确分列的共边槽也纳入则 19/19；post 主参考 19/19；两阶段均无整对 legacy 行缺失。VV 第二参考在已证 19 对内为零，不应从“全部槽命中”反推 VV 第二参考的命中能力。最小例 bb05 第 3 步块对 [2,3] 的命中在同一 raw 行 m4–m6 共边槽，不是 VV 第二参考。

核查本轮当前文件与既有 source_hashes：research_summary 23 个、research_tests 4 个、review_r3 4 个、research_initial_tube_witnesses 24 个、research_minimal_examples 24 个，均 0 不一致。此处的 4 个指该收据**已声明的哈希项**，不冒称它们是整个解释器的传递 import 闭包；research_summary 的运行时闭包与首尾绑定由原研究脚本负责。[研究摘要](file:///D:/eab-wt/cx-e2/reports/codex/M5c_evidence/research_summary.json)、[测试收据](file:///D:/eab-wt/cx-e2/reports/codex/M5c_evidence/research_tests.json)、[最小例](file:///D:/eab-wt/cx-e2/reports/codex/M5c_evidence/research_minimal_examples.json)。

## 7. C 不得变成已实现主张

当前 C/C1 只有条件定理草案与独立代数/边界文义复核，没有正半径出口排序 API，没有特征存续层实现，也没有对 16676 个初态贯入对重新签发证书。禁止给出这些对中 legacy 主/第二参考是稳健最短出口的数量结论。

C1 限于严格凸、跨环全部边对均严格非平行、全局闭边对应与内部保持均可认证的子域。若 `r=ra+rb`，端点误差给闭边 Hausdorff 界 `η=√2r`；最优平方距离 q 满足 `q>2r²`，所有其余 q_j 满足 `h=q_j-q-8r²>0` 与 `h²>32qr²`，才得到同一闭边的严格距离序保持。全部闭边的严格唯一间隙已排除最优点在端点时与邻边并列；额外双投影门只是冗余保守层。

并列组对外有间隙只保最优者仍落组内，不保组中每一标签持续并列；非凸全局入口块边界可能出现新暴露特征，不能拿原始顶点管直接替代每一出口特征的 Hausdorff 界。理论已经明确这些边界。**C 保持 PARTIAL；不登记任何伪造的实现或数据结论。**
