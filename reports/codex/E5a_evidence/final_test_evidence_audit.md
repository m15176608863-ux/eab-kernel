# E5a 留树证据只读复核（测试改写与突变）

## 范围与结论

- 本次在主线程最终全套 `session 13645` 运行期间，仅阅读当前源码、测试、`git diff`、分项台账、突变脚本及既有日志；**未启动测试、未执行突变、未改 src/tests/tools**。本文件是唯一新增文件。
- 本次不作全套通过或耗时结论，也不是独立六路 G6。复核者参与过 filters、frozen、interlock 测试开发，对这些部分的复核不能称为独立作者外审。
- 11 个已记录内部突变均能对应到预期缺陷的红断言；未见通过导入错误、其它异常或输出后塞假数据冒充杀死的记录。
- **不能据此确认所有测试改写均不弱于旧门**：以下两处仍有具体覆盖缺口。它们是测试强度／证据问题，不是本次已复现的运行时产品缺陷。
- 工单已因树外临时写入作废，本复核不改变该结论，也不将补跑视为抵销违规。

## 具体覆盖缺口

### A. 两组 membership 旋转门未替代原退化 facet 数量断言

位置：`tests/test_covers3_membership.py:266-280,284-315`；台账：`covers_test_rewrites.json` 中两个 rotated 测试。

旧门分别检查 `(facet_local, facet_global, facet_degenerate) == (7,7,3)` 和 `(0,0,6)`。新 helper 保留全部 10 + 10 个实际舍入输入，通过独立 Gordan 极射线计数核对顶点，要求 local/global 相等、无 ambiguous、所有边界探针执行；距离、VV3 标签与 inflation 门仍在。这些是实质增强。

但 helper **不读取 `facet_degenerate`**。`G0Report3.passed` 也不检查该计数（`src/eab/kernel3d/g03.py:41-44`）。所以一个仅把这些输入的退化 facet 计数报错、而不改其它量的内部缺陷，不受这两组新门约束。旧常数在实际舍入几何上不成立，删除常数合理；仍需独立精确退化 facet 计数替代，才能宣称旧计数覆盖未损失。其它文件中的计数门不能自动证明这 20 个输入也受到等强约束。

附带 oracle 边界：该 helper 的 `_ray_oracle` 本身独立，但先调用生产 `exact_convex_view` 规范化输入；因此它不是对输入预处理也完全独立的全链路 oracle。`rep.passed` 背后的原始 source G0 另有防丢极点门，缓解但不消除本 helper 的共享预处理事实。

### B. merge 的三类凹拓扑门替换了原舍入输入，而非同时保留

位置：`tests/test_geom3_merge.py:62-69,122-169`；台账：`geom_test_ledger.json` 的 `_place` 条目。

`_place` 从逐步浮点变换改为对已存矩阵、尺度和位移用 Fraction 精确求值。三个受影响测试是顶点 pinch、U 槽两端、三角化 U/L 棱柱归并。原参数和归并结果、体积、manifold、超时断言均保留，且精确平面前提现在成立；这是正确且有价值的“共面归并定理门”。

不过“参数格子保留”不等于“原实际输入保留”：非平凡旋转/尺度的原 float 舍入坐标已不再传入被测函数。台账引用的另一组远坐标 box 双轨门，仅补了 box 的 rounded 输入，不覆盖 pinched/U/L 的 rounded 凹拓扑。因此不能由当前证据推出原浮点凹输入的终止性、保持不该归并的面等回归能力完全保留。后续若要关闭“不弱于旧门”问题，应额外保留原 rounded 三类输入并按其真实精确几何作独立检查；不能继续要求错误的理想共面面数。

## 11 个内部突变与目标断言核对

下表来自既有脚本/日志/JSON 的只读核对；本次没有重新执行。

| # | 内部注入 | 既有红断言 | 判断 |
|---|---|---|---|
| 1 | orient3d 过滤界 / 10 | 过滤结果 `-1`，纯 Fraction 为 `+1`，`assert -1 == 1` | 真符号误判见证，不是仅检查回退次数 |
| 2 | `_quickhull_once` 把所有输入保留为顶点 | `test_geom3_e5a.py:138`，凸包顶点数应为 8 | 命中冗余顶点 |
| 3 | exact coplanar 合并改角度/平面距离近似带 | 同文件 `:108`，真实微脊应保留 7 个面 | 命中误合并 |
| 4 | `exact_geom.segment_triangle` 删除面内判定 | 同文件 `:62`，面外穿平面线段应为 False | 命中精确入口 |
| 5 | legacy `segment_crosses_face` 删除面内判定 | 同文件 `:67`，同一面外线段应为 False | 命中旧入口 |
| 6 | `_seg_seg_distance` 禁用精确近平行分支 | 同文件 `:158`，独立闭式距离误差应不超过 2 ulp | 命中旧独立参数回退 |
| 7 | 棱弧严格 `>` 改 `>=` | `mutation_arc_strict_ge.txt`：端点严格度应为 0 却为 1；3 failed | 命中边界严格性 |
| 8 | 锥交非零改 float norm `> 1e-12` | `mutation_cone_float_cutoff.txt`：4 个真极点对从 True 变 False | 命中被阈值吞掉的锥交 |
| 9 | 单形重心非负改 `>= -1e-12` | `mutation_simplex_barycentric_band.txt`：最近点应为正 eps 点却为原点；2 failed | 命中错误原点包含 |
| 10 | G0 票一 `cov == 0` 时 continue | 边界应检查 26 个而实际 0；`boundary_probes==boundary_checked==26` 红 | 命中边界跳样 |
| 11 | G0 票二比较循环丢第一个真实标签 | `facet_symmetric_diff == []` 红，报告 `hull_only`；6 failed | 命中实际比较遗漏 |

证据源：`filters_mutation.json/log/xml`、`geom_mutations.json` 及 `tmp/run_geom_mutations.py`、`covers_mutations.json` 及三份 `mutation_*.txt`、`g03_mutations.json` 及对应日志；汇总 `mutations.json`。

几何 runner 在被测模块内部替换函数，`finally` 恢复；只将 `AssertionError` 计作 killed，其它异常显式不算。表中 5 项几何 traceback 均落在上述看护断言。其余 isolated package runner 也进入内部生产路径，不是枚举后添加假记录。

历史 g03 宽度 4→400 的逃逸另列 baseline 证据，未混入这 11 个 killed；其既有绿色仅为指定旧子集，不可扩写为旧全套逃逸。

## 证据边界及待刷新项

1. 本次读取时，`test_rewrites.json` 尚未吸收 `geom_test_ledger.json` 最后两条 `test_kernel3d_geom.py` 迁移（分项 13 条、汇总 11 条）；库存仍把该文件标为 unchanged。主线程已明确计划最终全套后重跑 `assemble_evidence.py`。这是**待刷新汇总**，不是新产品缺陷；本文件不宣称刷新已完成。
2. 部分 machine ledger 的 `old_assertions/new_assertions` 仅抽取字面 `assert`，不展开 helper 和 `pytest.raises`，故出现新断言列表为空或只有 `old in src`。人工读 helper 后可以解释门的意义，机器列表自身不足以验证“不减弱”。
3. orient3d/covers/G0 突变记录的源 SHA-256 与本次当前文件一致：分别为 `6d406916e68742905eb95ea97fbfecfaa48007ea37a3c310738f90a8769c56a4`、`e2b7b60cf78433abcc2aa29cd317405c9ce54f0d8c3088fd837e8a4a37a6b546`、`015b4ca4afd6cc6af2694f5fba3394000bbcacddf7aeea97295262e291f22b22`。5 项几何变异 JSON 有替换文本、目标函数、目标门和 traceback，但没有当次源/测试快照哈希；能确认当次目标断言真实红，单靠该 JSON 不能密码学绑定到最终全部源码快照。
4. 这次抽查不是逐个数值格子的重新求值，也未尝试在冻结的最终测试期间复现 A/B 的逃逸。因此 A/B 按“具体门覆盖缺口”报告，不冒称已获得新的可执行 mutant 红/绿对照或新的 G6 major 结论。

## 追加闭环复核（新全套 session 78816 运行期间）

**当前结论：上述 A/B 两处具体覆盖缺口均已关闭；前文保留为初版历史发现，不再表示当前未修状态。** 本次仍仅阅读指定补门、台账和既有运行证据；没有执行测试或变异，没有改 src/tests/tools。本结论不扩大成所有新代码已完成独立 G6，也不改变工单作废结论。

### A 已关闭：原 rounded 输入的完整支撑分类与退化计数

- `tests/test_covers3_membership.py::_raw_support_classification` 从 A/B **原始坐标**构造精确公共分母整数表示，独立枚举各体点三元组法向与两体点对方向叉积。自行按精确支撑集、仿射维数筛选二维 Minkowski facet。未调用生产 hull、canonical-view、支撑或维数原语。
- `_assert_exact_facet_counts` 用 canonical view **仅解码实际标签**为坐标集合；期望 strict 集及 degenerate 数均由原始输入独立生成。实际完整 strict 集、无重复、strict 计数和 `rep.facet_degenerate` 均必须一致。两组原 20 个 rounded 输入、每格 60 样本、原物理断言仍在。
- 另加同样 20 个矩阵的精确 Fraction 仿射格，显式检查行列式非零，保留旧解析 `(7,3,13)` 与 `(0,6,8)` 命题，而没有把已存 R 误称为精确正交矩阵。
- 新牙在真实 `facet_vote3` 源码中将 `degenerate += 1` 改成 `+= 2`，确认旧 `rep.passed` 尚为真，再要求新计数断言以 `(6,3)` 拒绝。不是返回之后篡改 report。读取到的冻结证据为 **`93 passed in 14.88s`**，wall **16.85340079999878 s**，`changed_during_run=[]`。
- 原 Gordan 顶点计数 helper 的共享 canonical 预处理事实未被改写成“完全独立”；本次新加 facet 分类 oracle 独立于该预处理，直接关闭 A 所指出的退化计数字段缺口。

### B 已关闭：原 16 个 rounded 凹输入恢复双轨

- `tests/test_geom3_merge.py::_float_place` 恢复原表达式；本复核只读 `pre_e5a.zip`，经 AST 对比确认旧 `_place` 与新 `_float_place` 除函数名外相同，`_rotation` 亦相同。既有 `merge_rounded_input_audit.json` 进一步记录 16/16 个输入格 `float.hex` 逐坐标相同；本复核没有重新执行这些构造。
- pinch、U prong、三角化 U/L 各原格均重新将 rounded 输入交给生产 merge，并保留超时、原体积界、manifold；前两类原逐面相同断言也恢复。新增 `_assert_exact_merge` 仅使用独立 Fraction 平面、逆向共棱邻接与有向边界多重集，对结果作完整组件边界核对；不是只检查面数或容许任意新增面。原 Fraction 仿射解析轨全部仍在，属于追加而非替换。
- 两条新牙分别在真实组件分组内部禁止合法归并，以及把精确共面条件改成近似带；生产调用成功返回后，必须由 `exact merge boundary mismatch` 这一指定证书断言拒绝。读取到的运行证据为 **`53 passed in 0.87s`**，wall **1.5531715999968583 s**，`changed_during_run=[]`。
- `geom_test_ledger.json` 和 `covers_test_rewrites.json` 均保留初版缺口及修正说明。两份冻结运行 JSON 所记录的全部源/测试文件哈希，经本次只读计算与当前文件比对，差异均为空。

### 几何突变快照绑定及文案边界

- 新 `geom_mutations_final.json` 的 5 项变异仍分别在前表指定的看护断言报 `AssertionError`，且每项记录 `source_drift=[]`、变异函数文本 SHA-256，以及 geom3/exact_geom/predicates/目标 test 的源哈希。本次将这 4 个文件的当前字节 SHA-256 与全部 5 份记录比对，完全一致。因此前述“几何 5 项缺源快照绑定”局限已由**新增证据**补足；旧 JSON 保留作历史记录。
- 只读核到 canon 已区分 G0 的精确 b−a 与 margin 仍先浮点构造差点；设计文档开头明确目标语义不是完成证明；canon/报告明确工单作废、未过 G6；interlock 的原断言保留声称限定为候选/逃逸定向 34 格，并另指向改写的不变性台账。
- 汇总台账仍由主线程在最终全套结束后刷新；本复核没有宣称刷新或最终全套已完成。**在这次限定的 A/B 和 5 项几何变异闭环范围内，未见阻止继续留树最终回归的明显测试强度问题。**
