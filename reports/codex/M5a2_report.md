# WO-M5a2：验收遗留修补与 DDA 仿射步内运动

日期：2026-10-15。起点：`58733eb5f3ea9999615ab7a6d5a24c74ee7fa9c1`，初始工作树干净。

## 0. 交付结论与范围

**A 已完成。整单19个有限内部变异均由语义断言击杀；最终四片 13360 项全绿，收集=执行、0 skip，静态构造门0违例。B7 完成；B8 的坐标轨迹族完成，但一般精确首入未实现；B9 的正残差首盖稳定证书、B10 的完整三模型四问题重算仍为 PARTIAL。**

只写 `D:/eab-wt/cx-e2`；没有修改 `cx-m4`、b-DDA、其他姊妹仓库或设计文档正本；没有 commit、push、reset、checkout、stash、branch、worktree 操作。只读 Git 查询及 `git archive HEAD` 用于起点审计与基线导出。纯标准库实现，pytest 是已有测试基础设施。

原 M5a 夹具未改；`fixtures/PROVENANCE.json` 仅新增 `m5a2/revalidation.json`，旧条目逐值不变。原 3103 条及 M5a 的 117 条准入均保持原值。没有修改 README 的里程碑完成声明；本报告不替代 Claude 的独立验收。

### 关键成果

- [交付文件与哈希清单](file:///D:/eab-wt/cx-e2/reports/codex/M5a2_evidence/artifact_manifest.json)
- [450 帧完整重验证](file:///D:/eab-wt/cx-e2/fixtures/m5a2/revalidation.json)
- [1810 步仿射审计摘要](file:///D:/eab-wt/cx-e2/reports/codex/M5a2_evidence/affine_full_summary.json)
- [仿射理论与证明状态](file:///D:/eab-wt/cx-e2/docs/m5a2_affine_theory.md)
- [数值合同增量](file:///D:/eab-wt/cx-e2/docs/m5a2_numeric_inventory.md)
- [静态逐站点准入](file:///D:/eab-wt/cx-e2/reports/codex/M5a2_evidence/static_admissions.json)

## 1. A：逐条处置

### A1 回放账本的独立语义门

新增 `tests/test_m5a2_replay.py`。期望值直接调用生产 SE(2)/M4c 内核；测试内独立建立拟合输入、特征编号映射、状态/盖/关联分类表，不调用回放分类器或结果转换器，也不从 `code_hashes` 导出任何期望。

| 真实帧 / 块对 | SE(2) / 弦状态 | 盖集合 | 目的 |
|---|---|---|---|
| bb05 第4步 (1,4) | contact / no_contact | 不同 | 弦无接触不能旁路 SE(2) |
| bb05 第4步 (2,4) | no_contact / no_contact | 相同 | 相同结论与真实宽阶段排除 |
| bb10 第7步 (5,6) | contact / contact | 不同 | 不能仅比较接触布尔值 |
| bb12 第2步 (2,9) | contact / contact | 相同 | 同盖但不同无理时刻 |

冻结 pair 行及两阶段 legacy 行逐字段核验：模型状态、完整盖/关联集合、精确时间与显示、认证、残差、路径、三种模型比较标志、原始 tuple7、index、reference 及四个 category 字段。新增完整 focused-frame 门还检查顶层字段集合、输入摘要、blocks、stats、phase counts/secondary_counts/transitions；不再只检查 pair 结果。

几何内核是这里的参考对象，**本门证明回放接线/分类/序列化语义，不冒称另一个独立几何 oracle**。独立几何正确性继续由 M5a 的插值/Sturm/G0 oracle 门承担。

内部变异包含模型对调、弦无接触捷径、分类误用弦结果，以及统计桶对调、块形心字段串错、phase counts 误用弦分类。前三项在 tmp 中真实重跑 bb05 全30帧，调用生产 `freeze()`，重新生成压缩夹具及其哈希；先屏蔽源码哈希绊线，fresh hash 全通过之后，仍被新语义断言击穿。不是给产物追加假行。

### A2 精确极小残差

单位方块端点取 `x'=(1+2δ)x, y'=y`，测试先证明实际拟合残差等于 δ，再核 `UNCERTIFIED_NONRIGID_ENDPOINTS`。

δ 覆盖 `Fraction(1,2**1074)`、`Fraction(1,10**100)`、`Fraction(1,2**52)`。原生产分支已正确，本项增加缺失的语义门。把内部 `delta == 0` 改成 `delta <= 2^-52`，红在“strictly positive exact residual must remain UNCERTIFIED”。

### A3 小转角宽阶段界

u 取正负 `10^-1 … 10^-6`，使用非对称瘦四边形，覆盖尺度变化、大平移、固定种子有理旋转、11个有理时刻。期望坐标由测试内有理旋转分量直接展开，不共享 `rotate_rational/at/endpoint/_swept_bounds` 或多项式原语；参数化还断言产物互异。

把 `_swept_bounds` 内系数 2 改成 9/5，红在“小角度扫掠界包含真实路径”断言。抽样门是对已证明系数的回归看护，不代替连续包络的解析证明。

### A4 有理首入时刻统一容器

选择出口规范化方案：新增 `RealAlgebraic.as_rational()`；SE(2) 首入出口若精确识别为有理根，就统一返回 `QuadraticTime(rational)`。不更改旧 `QuadraticTime` 实现，也不把一般 `RealAlgebraic` 改成可 hash。

二次式用判别式整数平方核验。高次式用本原整数多项式的首项系数 B 给有理根分母界，小素数无根证据可提前排除，否则精确细化到区间宽度 `<1/(2B²)` 后做有理重构，且同时核“候选在选定区间内”和“精确代入为零”。推导见 [精确子报告](file:///D:/eab-wt/cx-e2/reports/codex/M5a2_evidence/exact_report.md)。

最小例 L=5,h=3：`10s/(1+s²)=3`，即 `(3s−1)(s−3)=0`，首时刻 `1/3`。门包含与 Fraction/旧时刻的双向相等、hash、集合去重及混合排序，以及随机有理旋转、尺度、大平移。另守大分母高次有理根、无理根拒绝及“区间外另一有理根不能冒充当前根”。

边界：此方案统一的是 **SE(2) 出口的有理时刻**，不是声明任意两类无理代数容器都可混排。最坏大分母界可能增加精确二分成本，不能把有限性能结果当复杂度上界。

### A5 比较器逐站点准入

新增 `algebraic-comparator-site` 规则，直接参数、属性 callable、别名、关键字等传给 `scalar_algebraic` 不能继承构造器名字的“精确”待遇。只准入两个已有数值站点：`RealAlgebraic.time` 的精确比较器，以及构造器内部 `-compare(-q)` 符号反转递归。独立审查的15种 adversarial callable 形式均拒绝。

旧3220条准入原值不变，新增170条逐站点说明，包括测试编排/精确对象接口。23条旧作用域审查因新增首时刻规范化或 oracle 输入断言而失效，采取**单独追加续审记录**，绑定旧条目完整哈希及新作用域哈希；续审本身不授予任何当前站点准入。当前站点另有精确 AST/作用域 pin。测试验证续审不能用于修改后作用域或无关节点。

静态检查只是有限 Python 子集的维护辅助，不是运行时任意回调精确性的形式证明。关闭新规则的真实内部变异会在比较器拒绝语义断言上报红。

### A6 小项与超时

- 独立 oracle `first_contact` 开始前断言全部顶点、u、平移和参考点均为 int/Fraction，拒绝 bool；删除内部断言后类型门报红。
- 公共 `RealAlgebraic` 用 `(3x−1)(x−2)`、闭区间 `[1/3,1]` 看护下端点根；同时拒绝含两个根的 `[1/3,2]`。端点赋值反向变异红在精确根语义。
- `same_time` 覆盖同一二次式的两个无理分支、错误分支及不同多项式同半区。两个内部缺陷分别命中分支/多项式断言。
- 新门运行器每个测试（含 setup/teardown）有 watchdog，默认900秒；非终止 `RealAlgebraic.refine` 注入用0.25秒演示，子进程退出124且不能写完整执行证据。collection/static 等外层步骤另有7200秒有限 deadline；拒绝 NaN/Inf/非正超时。
- 导出完整性同时比较文件路径集合与每个文件字节，新增、删除或修改源文件都使退出门为 RED。

## 2. A 的重验证与变异证据

修改代数数与 SE(2) 后，完整重算15×30冻结前缀，共450帧；67.699秒。全部 JSON 字段一致，精确时刻证书表示变化实际为0。旧夹具没有重冻结覆盖。新 manifest 绑定62个历史输入、生产闭包与重验证脚本；旧源哈希门改为核对当前完整重验证凭据，未取消绊线。

| 变异组 | 有限内部缺陷数 | 看护方式 / 证据 |
|---|---:|---|
| 回放、宽阶段、无理 same_time | 9 | [回放变异摘要](file:///D:/eab-wt/cx-e2/reports/codex/M5a2_evidence/replay_mutations_r5/summary.json)；模型/分类前三项真实重新 freeze |
| 极小残差、有理根/容器、oracle 输入、闭下端点 | 6 | [精确变异摘要](file:///D:/eab-wt/cx-e2/reports/codex/M5a2_evidence/exact_mutations_r2/summary.json) |
| 比较器站点规则 | 1 | [静态规则变异](file:///D:/eab-wt/cx-e2/reports/codex/M5a2_evidence/static_mutations_r1/summary.json) |
| 仿射拟合、正残差认证、残差校正 | 3 | [仿射变异](file:///D:/eab-wt/cx-e2/reports/codex/M5a2_evidence/affine_mutations.json) |

合计19个有限内部缺陷；另外有单测内部非终止与外层步骤非终止探针。所有指定变异均要求先控制绿，再在指定语义断言上红；哈希不作为击杀依据。证据工具使用全新运行目录，不能续接中断结果。

## 3. B：理论、实现与证明状态

### B7 精确仿射拟合：完成

按顶点身份配对，等顶点权重形心 c、t，令 `X_i=p_i−c, Y_i=q_i−t`：

```text
C = Σ X_i X_i^T,  H = Σ Y_i X_i^T
M = H C^-1, d = t-c
e_i = q_i - [c+d+M(p_i-c)], δ_aff = max_i ||e_i||∞
```

输入张成平面时 C 正定，该式为唯一最小二乘解；不是 L∞ 最优拟合。全部 Fraction，无绝对容差。主 oracle 使用独立的未中心化3×3 Cramer 解，不共享拟合原语。残差向量有刚体坐标协变门，尺度为 `2^-400/1/2^397`，另含随机有理旋转与大平移。L∞范数本身不是一般旋转不变量，未作此错误声明。

只读核对 b-DDA `bdda2/geom/moments.hpp::update_block_vertices`：实数端点结构为 `c+d+[R(θ)+E](x−c)`，E为对称常应变，有限转动与应变是**相加**而不是相乘。快照有逐顶点 binary64 舍入，故通常不严格仿射相容；本单没有恢复内部自由度或运行姊妹求解器。

### B8 有理轨迹族：坐标实现完成，一般首入 PARTIAL

```text
R(v) = [[1-v²,-2v],[2v,1-v²]]/(1+v²)
E* = M-R(u)
X(s,p) = c+s*d+[R(s*u)+s*E*](p-c)
Xhat_i(s) = X(s,p_i)+s*e_i
```

X 精确闭合拟合映射端点；Xhat 精确闭合原始快照端点，但正残差时一般不再是共同仿射映射。E*未必对称；角时间律是 `2 atan(su)`，不是 `sθ`；不能把该提议族说成 b-DDA 实际连续路径。

已证明并配门：E*=0 时逐坐标等于 M5a SE(2)；u=0 时 X 等于拟合端点弦，Xhat 等于原始快照弦。最小扩张方块 `x_right=1+2s` 对 x=2 的墙首接触为1/2。

事件坐标分母严格正，顶点分子次数≤3，异块点差分子次数≤5，点在线及投影事件分子次数通用上界≤8。此次数推导完成，但八次根隔离、一般仿射首入、路径域与法锥完备性尚未实现。没有暗中放宽已验收实代数数的五次上限。

### B9 正残差认证：明确 PARTIAL

对**指定**校正族，有恒等式 `Xhat_i−X_i=s e_i`，故整段顶点及同重心边点偏差≤sδ_aff；这部分证明及实现完成。共同仿射路径还提供 Neumann 非反转充分条件 `2||E*||∞<1`，false只表示未知；此条件不自动覆盖逐顶点校正环。

尚缺严格横截、竞争事件与非首事件间隔、校正环有效性，以及究竟认证“首盖身份/顺序”还是“同一精确时刻”的完整合同。因此没有实现 δ>0 首盖稳定证书。

未知实际轨迹不能由端点误差单独约束：`h(s)=4K s(1−s)` 两端为零，中点任意大。该反例不能否定对**预先限定扰动族**证明稳定性的可能性；本单仅如实说明该证明未完成。

1810步共64010块对帧：63910个正仿射残差、100个零残差。**首盖/物理路径认证0，未认证64010**。500个块帧的端点拟合残差严格为零，只是端点属性，不是接触认证。

## 4. 1810 步分布与三模型诊断

最终仿射审计 `affine_full_r4` 完整重跑1810步、15220块帧，约50.12秒。逐块原始表放 ignored tmp；冻结摘要约409KB，含精确分位数、各算例/输入/源码哈希和最小例。

| 指标 | 中位数 | P95 | 最大值 |
|---|---:|---:|---:|
| δ_rigid | 2.2171e-3 | 3.4415e-2 | 1.8455e-1 |
| δ_aff | 4.6149e-14 | 1.6085e-13 | 2.5882e-13 |
| δ_aff / 块最大坐标跨度 | 1.1197e-16 | 3.7510e-16 | 1.0993e-15 |
| δ_aff / (快照最大绝对坐标×2^-52) | 0.3245 | 0.6678 | 1.0310 |
| δ_rigid / 最近正间隙 | 3.1533e-2 | 2.2178e1 | 1.3246e11 |
| δ_aff / 最近正间隙 | 1.3468e-13 | 5.1456e-9 | 2.9449 |

最近间隙是初始时刻到其他实体块集合的最小欧氏距离。1494块帧间隙为正；13726块帧间隙为零，明确排除除零归一化，不以 epsilon 替换。坐标×2^-52 只是描述尺度，不是误差定理。δ_aff总体接近舍入量级，但仍可大于实际微小间隙，不能由此认证。

15个算例逐项中位数及精确分布见 [理论§7.1](file:///D:/eab-wt/cx-e2/docs/m5a2_affine_theory.md) 与 [冻结 JSON](file:///D:/eab-wt/cx-e2/reports/codex/M5a2_evidence/affine_full_summary.json)。15220个刚体拟合残差均逐值复现历史 M5a 记录。

### B10 已完成的部分与不能推出的结论

历史937个 SE(2)/弦首结果差异：933个伴随刚体端点状态翻转，4个端点状态相同；这937个样本中，仿射拟合端点状态与原快照不一致为0。**这是伴随状态分层，不是因果分解**：不能写“933个纯端点原因、4个纯路径原因”。相同重叠状态不代表同一端点形状/盖，状态翻转也不排除路径同时起作用。

| M4c/M5a 四问题 | 本单仿射处置 |
|---|---|
| legacy 选边是否首盖 | 一般仿射首入未实现，未重算；PARTIAL |
| 漏检 | 不能由端点状态替代步内事件，未重算；PARTIAL |
| 初始已压入的参考边与全局最短出口 | 三模型共享初始环，该静态几何问题不随后续插值改变；仅复用历史证据，没有冒称新增独立全量 PD 重算 |
| 三模型差异的端点/路径原因分解 | 已做937样本端点分层；完整反事实共同端点路径与精确首盖分解未完成，PARTIAL |

每个关键数据结论的自包含最小例：

- bb05 第3步 (2,3)：端点状态翻转。
- bb05 第9步 (1,4)：端点状态相同而历史首结果不同。
- bbF038 第1步块1与邻块2：δ_aff/gap≈2.945。

[最小例 JSON](file:///D:/eab-wt/cx-e2/reports/codex/M5a2_evidence/affine_minimal_examples.json) 内嵌全部精确顶点；[复验脚本](file:///D:/eab-wt/cx-e2/reports/codex/M5a2_evidence/affine_minimal_examples.py) 默认读取最小例与冻结总摘要并核对摘要哈希，不依赖 ignored 全时程原件。

## 5. 独立复核、imports 与已关闭缺陷

独立数值期望 imports：拟合/轨迹用 `fractions.Fraction`，参数化用固定seed `random.Random`；精确边界用整数因式/有理杠杆公式；原 M5a oracle 用 Fraction、functools 和独立 `g0_oracle.overlap`（传递 math.lcm；显示模块不参与本路径判定）。回放接线门直接使用生产内核但独立分类，性质范围已单列。变异编排的 inspect/compile/pytest/unittest.mock 不是数值 oracle。详见各测试模块 docstring 和分项报告。

本轮交叉复核由非对应代码作者执行。R1/R2 独立数值对照包含120个拟合、120个轨迹和100个间隙样本，及1810步统计重新聚合，零失配；R5另有353个精确代数/边界样本零失配。

| 路线 | 范围 | 当前结论 / 证据 |
|---|---|---|
| R1/R2 | 仿射理论与数据、回放语义及变异 | 0 critical / 0 major / 0未关闭minor；[报告](file:///D:/eab-wt/cx-e2/reports/codex/M5a2_evidence/review_affine_replay.md) |
| R3/R4 | 静态准入、inventory、运行器、交付边界 | 0 critical / 0 major / 0未关闭minor；两套全节点、三阶段及字节导出已独立读回GREEN；[报告](file:///D:/eab-wt/cx-e2/reports/codex/M5a2_evidence/review_static_runner.md) |
| R5 | 精确代数与认证边界 | 0 critical / 0 major / 0 minor；[报告](file:///D:/eab-wt/cx-e2/reports/codex/M5a2_evidence/review_exact.md) |
| R6 | 报告与最终证据一致性 | 0 critical / 0 major / 0未关闭minor；报告、最终证据及交付边界终审通过；[报告](file:///D:/eab-wt/cx-e2/reports/codex/M5a2_evidence/review_report.md) |

这些交叉复核只覆盖本单已实现范围；B的PARTIAL项不是“经审查已完成”，也不替代下达方独立验收。

已发现并处理，而非隐藏的缺陷：

1. **major：输入绑定竞态。** 拟合开始后修改已读快照，早版会将旧计算结果绑定新输入哈希。已对 snapshot/terminal/历史normalized/audit 四类消费文件做 batch/worker 前后封闭哈希；原 `x+=1000` 反例复验明确拒绝。修复后1810步全批重跑，不复用早版数据。
2. **minor：聚合账本缺门。** stats桶交换曾逃过 pair 行门；新增 focused-frame 全字段门及3个内部变异，重新验证。
3. **minor：非有限超时可绕过。** NaN/Inf现在在 CLI、plugin及外层run入口拒绝。
4. **minor：导出新增文件漏查。** 新增路径集合对比，真实 runner sandbox 的“运行中新增源码”应为 RED。
5. **minor：仿射 CLI 路径/worker边界。** 新增单目录名与 resolve 后根范围检查，workers限1..4；修复后完整 r4 重跑。
6. **minor：最小例与报告绑定。** 最小例复验增加冻结总摘要哈希检查；本报告同步更正其依赖范围，不再描述为只读取一个文件。

## 6. 全套四分片、静态与性能

最终有效轮次为 [final_suite_r3](file:///D:/eab-wt/cx-e2/reports/codex/M5a2_evidence/final_suite_r3/summary.json)，四片最后一行按片号原样如下：

```text
3340 passed in 772.64s (0:12:52)
3340 passed in 1325.65s (0:22:05)
3340 passed in 606.45s (0:10:06)
3340 passed in 928.20s (0:15:28)
```

静态门最后一行原样：

```text
exact construction AST gate: 0 violation(s)
```

[逐节点审计](file:///D:/eab-wt/cx-e2/reports/codex/M5a2_evidence/node_identity_audit.json)：全局收集、分片派发、各片实际收集、实际call的多重集合完全相同，13360=13360，所有setup/call/teardown均passed，0 skip。相对起点13254项，[净增106项、删除0项](file:///D:/eab-wt/cx-e2/reports/codex/M5a2_evidence/suite_delta.json)：其中新test_m5a2四文件105项，新增夹具的自动溯源检查1项。

[交付审计](file:///D:/eab-wt/cx-e2/reports/codex/M5a2_evidence/delivery_audit.json) 为GREEN：执行导出及当前代码的路径集合/字节均无失配，旧3220准入不变、新170、续审23；旧216个PROVENANCE条目逐值不变，只新增本单重验证夹具；编码、BOM及提交候选大文件违规均为0。

全量测试用新建字节导出，执行前后核路径集合和全部字节；没有创建 worktree。按本单明确禁令，这不能冒称“新鲜 Git worktree”满足仓库默认纪律D；`fresh_git_checkout=false` 已记录。所有 pytest 禁用 cacheprovider 并显式 basetemp，TEMP/TMP均在本单 evidence/tmp。

`baseline_suite_r1` 的旧维护门因两次完整静态扫描超过180秒，被判RED；整批另名重跑 `baseline_suite_r2`，没有复用三片绿结果。`final_suite_r1` 因独立审查强化而主动中断，标 INVALIDATED_BY_REVIEW；`final_suite_r2` 因恢复静态准入文件原有 LF 字节格式而作废，标 INVALIDATED_BY_ENCODING_REPAIR。最终用全新导出 `final_suite_r3`，不拼接前两轮结果。默认900秒上限不改变非终止探针的0.25秒红证据。

性能见 [原始机器摘要](file:///D:/eab-wt/cx-e2/reports/codex/M5a2_evidence/performance.json)：

| 口径 | 基线 baseline_suite_r2 | 最终 final_suite_r3 | 观察 |
|---|---:|---:|---|
| 全部测试call累计秒 | 3558.873 | 3370.426 | 比值0.94705 |
| 整批wall秒（含collection/static） | 1601.373 | 1496.516 | 比值0.93452 |
| 新四个test_m5a2文件105项call秒 | — | 3.06133 | 占基线call的0.08602% |
| 最后独立静态扫描秒 | 130.034 | 130.040 | 0违例 |

新增门实测开销远低于约5%预算，全套本轮也没有观察到耗时增加。共享主机同时有其他工单且四片负载不同，`controlled_host=false`；这些数据不证明代码加速，也不是受控的5%性能认证。没有把独立全时程证据重算、内部变异批次或审查探针加进默认全套门。

## 7. 复跑、回滚与遗留

```powershell
$env:TEMP = "$PWD/reports/codex/M5a2_evidence/tmp"
$env:TMP = $env:TEMP
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:PYTHONIOENCODING = 'utf-8'
python tools/m5a2_run_gates.py --name final_suite_fresh
python tools/check_exact_construction.py
python tools/m5a2_affine_replay.py --workers 4 --run-name affine_full_fresh
python reports/codex/M5a2_evidence/affine_minimal_examples.py
```

运行目录必须全新。450帧冻结重验证脚本不会覆盖现有 manifest，需要所有者先明确归档旧 manifest 后再完整运行；默认 pytest 不依赖未跟踪的1810步输入。完整1810步原始快照仍保留在已有 M5a ignored tmp，不声称 fresh clone 无需外部证据就能重新生成全时程；新冻结摘要与三个最小例可随交付独立审读/重算。

回滚锚点为起点提交和 `reports/codex/M5a2_evidence/tmp/rollback_58733eb/` 中修改前字节备份；未执行任何破坏性 Git 恢复。完整文件清单含每个新增/修改文件的哈希。超过1MB的日志与节点/执行清单只在 ignored tmp，提交候选证据已做大小与 UTF-8 无BOM审计。

遗留退出条件：一般八次代数事件求解与独立 oracle；明确扰动族下首盖身份的严格横截/间隔证书；1810步完整三模型四问题及共同端点反事实原因分解；Claude 独立验收。没有用残差小、测试绿或端点同状态替代这些证明。

M5a2_PARTIAL：B8一般仿射精确首入；B9正残差首盖稳定证书；B10完整三模型四问题与端点/路径因果分解
