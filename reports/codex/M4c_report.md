# WO-M4c：二维运动首入接入 b-DDA 影子对账

日期：2026-10-14。起点 `codex-work @ 870045c`；改动未提交。

> **交付状态：M4c_PARTIAL。** 完整回放 1810 步、冻结回放 450 步、最终四分片 12974 项及静态门均已通过。
> 一般非零 δ 稳定性证书、受控性能增量及正式 G6／提交后新鲜工作树退出未完成；边界与证据见下文。

## 1. 范围、恢复与证据边界

目标是在独立 eab 树内，对既有 b-DDA 导出作只读、事后运动对账；不替换检测、不修改或运行姊妹树的程序。
理论先行稿为 [运动首入设计](../../docs/m4c_motion_entrance_design.md)，闭集分类为
[差异台账](../../docs/m4c_difference_ledger.md)。回退锚点是起点 HEAD 和最终文件哈希清单；没有执行回退或 Git 状态修改命令。

两次中断分别为所有者报告的约 08:53 重启、约 09:16 会话终止（其后约 10:37 再重启）。
`baseline_suite/`、`baseline_suite_r2/`、`full_replay/` 未完成运行均整体作废；不拼接分片或已完成子例。
之后 `full_replay_r2/` 因 gzip 截断审计缺口、`full_replay_r3/` 因 malformed-shape 异常包络缺口，
均主动停止、整体作废，未取已完成子例充数；最终生产使用 `full_replay_r4/`。
完整过程见 [恢复记录](M4c_evidence/interruption_recovery.md)。进度落盘只用于判断完整性，不作为跨批次拼接许可。
首次冻结批次虽算完 450 帧，却在发布 expected 时因相对路径处理错误退出，故 `frozen_replay/` 也整体作废；
修复驱动路径规范化后，在 `frozen_replay_r2/` 从头重算 450 帧，不复用已计算帧。
首轮最终全套 r1 又检出新增夹具漏登中央溯源表，及 Windows 进度文件短暂占用造成的 pytest 内部错误。
该轮整体废弃，补齐登记、增加原子写有界重试后，最终全套另在 r2 全新运行；旧片段不作为绿灯证据。

依第二次续单，不再重跑起点基线；M3 计时**不是同字节基线、只作耗时参考**。
最终全套采用本树 tmp 下的新鲜无 `.git` 字节副本；用户禁止 worktree 操作，故不称满足提交后新鲜 worktree 纪律 D。
组件独立审查也不等于全仓六路 G6。

**已发生的约束偏离**：早期几次定向 pytest 漏设 TEMP/TMP，合成负例临时文件写到了用户系统 Temp。
没有删除或改写外树来掩盖；全部外部临时文件范围未知。之后显式指定本树 tmp，未改动或执行姊妹仓库。
见 [环境偏差记录](M4c_evidence/environment_deviations.json)。因此不能声称本次所有临时写入均在允许树内。

## 2. 理论、条件与未证范围

### 2.1 DDA 与本单的轨迹并非同一个概念

只读源码审计确认，`geom/moments.hpp` 的六未知量位移矩阵为
`Tx=(1,0,-dy,dx,0,dy/2)`、`Ty=(0,1,dx,0,dy,dx/2)`，是一阶位移表达；
`update_block_vertices` **另有 sin/cos 有限转动顶点更新**。
因此采用相邻已接受步端点的弦轨迹 `x_i(s)=x_i^k+s(x_i^(k+1)-x_i^k)`，而不声称它等于求解器步内连续圆弧运动。
下文计数和例子中的“实际/真实运动”均是这一**事后端点弦模型**的简称，不增加连续运动真实性主张。
理想单个仿射更新会给仿射同伦，但独立 binary64 舍入后的端点一般不严格共用一个有理仿射矩阵。
时间步回退/重算、块体增删、开挖和身份变化不能静默跨接。

15 例共 1810 个快照步初帧，与同 run `geom.csv` 的 188320 条顶点几何逐值核对；
补末帧之前，要求 step0..step(N-1) 与全部快照对应、step0=initial、stepN=final、身份稳定。
这样得到 N 而非 N-1 个运动区间。冻结前 30 步的末端点另存在源哈希绑定 sidecar。
证据及源码哈希见 [运动学审计](M4c_evidence/kinematics_audit.md)；只认证此次审计过的生产者路径，不推广到任意回退协议。

### 2.2 首入定义与定理状态

对于每个 s 的简单、全维、边长非零多边形实体，令 `E(s)=B(s)⊕(-A(s))`。
分离初态的首入是 `tau=min{s∈[0,1]:0∈E(s)}`，不存在则返回窗口无接触。
闭集定义包括擦触、端点接触和瞬时事件，不要求之后发生贯入。

- **条件数学证明已给**：首次接触不能是稳定的体内交或两边内部横交，否则更早时刻也相交；
  剩下的端点落边、共线区间交均含 VE/EV，VV 是退化。
- **条件数学证明已给**：运动边方向与顶点相对位移均线性，cross 事件方程至多二次。
  恒等共线时另求 dot 闭段条件的变化点，不能丢弃整个事件。
- **精确算术论证已给**：有理数或规范不可约二次多项式加根支表示时刻；符号作有理约化，
  异二次域根用隔离区间比较，相等先识别规范形式；不以 float 近似或 epsilon 合并根。
- **平移退化证明已给**：`0∈E(s) ⇔ s(vA-vB)∈B0-A0`，所以必须与 M3 射线首入逐值一致；
  程序走一般事件路径而非绕回 M3。时刻、有效盖及并列集均有门。
- 这些是纸笔论证与测试，不是程序形式化证明。输入仅单个简单环；“带洞”门为 **E 的洞**，不是多环实体输入。
  域在整个 [0,1] 上检查，不能只检查两个端点。

输出 `incidences` 是全部闭段 VE/EV/VV 关联；`features` 是局部法锥有效 VE/EV 与 VV。
两者必须分开：端点落在边上不保证该参考边是有效首盖。

### 2.3 初态已贯入、替身与预测

初态贯入选择冻结步初几何的 **PD_closed**：到 E 真外边界的距离，保留全部并列最近点及有效特征并集。
这里“真外边界”指整个集合边界 ∂E，**包括 E 的洞壁**；“真”用于排除凸胞内部剖分缝，不是只取最外连通边界。
这不是 rho、沿本步运动的最先脱离、legacy 弹簧深度或动力学穿透量。
初态相触另分类，包括紧配内缝，不把它误称为 E 真外边界。

新增快 PD 使用 M3 凸胞并表示，精确扣除其他胞对有向胞边**外侧邻域**的覆盖区间，
对正长度补段取闭包并求投影。紧配内缝不能只减开胞内部；剪枝须严格大于当前最小值，保留全部并列。
设计 T3a 有论证，独立格网/矩形 oracle、M3 对照与内部变异分别看护边界及并列语义。

平移替身取各块顶点平均位移，`delta` 是两块最大残余 L∞ 位移之和。
**只有 delta=0 被实现为首盖逐值不变证书**。非零统一 UNCERTIFIED，绝不放入认证一致/不一致分母。
设计给出非零 delta 下“目标严格穿越、投影留余量、此前实体及所有竞争特征距离留余量”的充分条件，
但一般区间证书尚未实现。两条轨迹都精确求解所得的描述性差异另计，不冒充稳定性证书。

`state.csv` 有 `tt` 步长，没有完整步初速度；`hh/hh_cur/g7` 是刚度相关量，不是 dt。
从第二步开始额外评价“上一段顶点位移同量外推”，第一步不可用；不把它说成速度×本步 dt。
该预测统计仅在真实运动扫掠盒或 legacy 候选域、且初态分离的条件样本中计算，**不是全体块对预测精度**。
已知域外 false-positive 反例见 [预测范围审查](M4c_evidence/prediction_scope_review.json)。

## 3. 实现与公开 API

| 位置 | 合同 |
|---|---|
| `src/eab/kernel2d/motion.py` | `motion_first_entrance(A0,B0,A1,B1)`；精确时刻、显示时刻、状态、完整关联与有效盖集合。 |
| 同上 | `QuadraticTime`；规范有理/二次代数数、精确比较和多项式符号；显示只经 construction 层。 |
| `src/eab/kernel2d/motion_exit.py` | `shortest_exit_fast(A_or_model,B=None,x=(0,0))`；既有 `Distance2` 合同，全部并列点。 |
| `tools/m4c_motion_replay.py` | 严格读取/配步、全运动扫掠候选、raw/post primary 与 VV secondary 逐条闭集分类。 |
| `tools/m4c_run_replays.py` | 完整源/冻结夹具批次；新目录、逐步记录、最终源码/输入哈希不变检查。 |
| `tools/m4c_run_gates.py` | 新鲜字节导出、4 分片、真实收集/执行核对、0 skip、静态门。 |

没有修改现有 M3/M2 或 b-DDA 语义。浮点输入快照按所存 binary64 精确值处理；
归一化结果保留有理字符串与代数证书，浮点值只供显示。

## 4. 门、变异与独立审查

### 4.1 退化、oracle、集值不变性与数值合同

| 门与具名断言（`tests/`） | 覆盖/口径 |
|---|---|
| `test_m4c_motion.py::test_translation_is_exactly_m3_with_complete_features` | 6 类×3 尺度=18 轨迹：L、槽角楔块、互锁、零间隙、E 洞、共线；精确时刻、显示、全部有效盖集合，失配 0。 |
| `test_translation_convex_m2_has_exact_time_and_same_expanded_tied_set` | 3 类×3 尺度=9 凸轨迹；M2 FF 展开闭端点关联再比较，失配 0。 |
| `test_motion_matches_independent_closed_form_and_integer_oracle` | 手推 `t²+t−1` 及 `(t−1/4)(t−3/4)`；独立有理时刻三态夹住事件，核正确根支和特征。 |
| `test_polynomial_sign_and_order_match_independent_rational_intervals` | 324 次多项式符号、132 次跨域根排序比较；不以近似根排序作 oracle。 |
| `test_public_motion_is_rigid_motion_and_unit_covariant`、`test_complete_multi_feature_sets_are_covariant_not_only_single_ve` | 24 次单 VE 与 54 次多特征集合变换；有理旋转、90°、大平移及尺度，比较集合而非代表。 |
| `test_m4c_exit.py` 的 M3、独立矩形/紧配缝及协变门 | 8 组 M3 全并列对照；三尺度独立闭式、24 次变换；闭外侧覆盖、孤立补点、剪枝丢并列有内部变异。 |
| `test_every_public_motion_numeric_field_has_three_tier_independent_reference`、`test_m4c_numeric.py` | 几何尺度 `2^-400,1,2^397`；显示尺度 `2^-1070,1,2^1022`，独立精确 binary64 舍入单元判据；下溢保留证书、上溢响亮失败。 |
| `test_quadratic_numeric_equality_hash_and_string_set_contract` | 修复审查发现的字符串隐式转换问题；数值等价保持 hash/set/dict 一致，字符串不等且不能排序。 |

纯平移不走返回 M3 结果的专用捷径；指定变异破坏一般线性事件根后，一致门真实报红。
上述计数是样本/比较次数，不是 pytest 节点数；最终全套节点另列第 7 节。
本地最终核心组件重跑为 `70 passed in 1.01s`；不替代全套。

**oracle import 清单**：主闭式/运动事件 oracle 用 `fractions.Fraction`、`math.nextafter/inf`（仅显示中点），
以及独立 `eab.kernel2d.g0_oracle`（其内部为 Fraction、math.lcm、独立 oracle_construction）。
测试文件中的 `GlobalEntrance2`、M2 `first_entrance` 是被标明的一致性通道；
`eab.oracle_construction.scalar_exact/sqrt_exact` 仅用于独立显示参考。
不 import 生产 `_roots`、线多项式、法锥、三角剖分或 SAT 作为 oracle。
额外独立审查的格网 PD oracle 只用 Fraction，二次闭式族另用 `math.isqrt`；
612 个占据格网胞并查询、100 个仿射墙例、9 个二次族、25 个 M3 平移等见审查 JSON。
有限格网胞并压力样本不声称每一个都能实现为单环输入的 E。

新公开构造登记在 [construction inventory](../../docs/r13fix_construction_inventory.md)：
时刻显示唯一经过 construction，精确字段/标签不新增 binary64 构造；PD 复用 `Distance2` 口径。
最终全仓静态结果及豁免增量在第 7 节，不以组件静态代替。

### 4.2 台账、证书与输入门

`test_translation_nonzero_residual_is_uncertified_not_mismatch` 人为增大非平移残差，使证书失效而进入 UNCERTIFIED，
不落认证一致或不一致。非零 δ 的描述性差异与认证率分开。
`test_swept_contact_pair_is_detected_with_both_legacy_tables_empty` 看护未由 legacy 表预筛掉的真实运动接触；
无内部顶点证人的穿透深度保留 null，不能伪造为 0。

冻结门检查全部 450 条帧记录哈希、两时间面的 primary/secondary 闭集成员与计数守恒；
每例首帧另实际生产重算。**常规 pytest 不重新计算全部 450 帧**：另有本次完整冻结计算与所有生产源哈希绑定门，
任一生产源变化即红，必须显式重跑全 450 帧，不能仅靠首帧采样复用旧证据。
少列、错位、跳步、回退/未知 attempt、非规范 CSV 步号、终端错配及 gzip/坏形状输入均有失败门。
入口最外层统一将 `Exception` 记录为带错误类型的 RED、非零退出；不吞 `KeyboardInterrupt/SystemExit`。
最终独立输入审查 36 个负格子全红在预期判据，其中 16 格实际 CLI 子进程；
最终定向测试为 `93 passed, 32 deselected in 2.25s`（92 个回放输入门及 1 个批次发布门），明确 32 个冻结节点不在该定向运行中。
最终全套前另一次完整新增组件及中央夹具溯源预检为 `416 passed in 13.94s`（211 个 M4c 节点 + 205 个溯源节点）。

专项审查还发现批次聚合器曾接受字符串计数，可能伪绿；已修复为非 bool 非负整数计数、有限耗时、
hash 格式及源/规范化逐帧绑定。该驱动不在生产几何代码哈希内；修复时 r4 的几何计算不变且未停止。
其完整旧驱动 summary 保留不覆写，已经由最终驱动 `verify-batch` 对**同一个完整批次**重新验证所有 15 例并通过。
这不是拼接中断帧。冻结批次从开始即使用修复后的驱动。

汇总层另修复末端 CSV 未绑 hash 的漏洞，并把“关联但非盖”与“另一特征先接触”分开计率、
VV 第二参考单独选例。`test_m4c_summary.py` 的 9 门及 3 项内部反事实门通过；最终逐行独立复数另见第 5 节。

### 4.3 六项指定内部变异

| 变异 | 应报红的看护断言/错误 |
|---|---|
| 二次根取错支 | `earliest quadratic branch` |
| 将闭端点误作开端点 | `closed endpoint event lost` |
| 法锥路径丢一个并列盖 | `complete simultaneous cover set` |
| 平移线性根路径被绕空 | `general event path translation consistency` |
| 台账类别折叠入 MATCH | `motion category preserves earlier other feature` |
| 步配对错一位 | `motion geometry pairing mismatch` |

每项先独立控制进程绿，再在被测函数内部注入缺陷；要求 mutant 退出 1 且命中指定断言，不在输出后附加假数据。
最终绑定批次为 [mutations_r6/summary.json](M4c_evidence/mutations_r6/summary.json)：
6/6 控制进程通过、6/6 mutant 命中目标断言，逐项红灯末行为 0.16、0.16、0.17、0.17、0.17、0.17 秒的 `1 failed`。
旧 r1 工具错误和旧源码绑定批次不作为本次最终变异证据。

专项审查由不写相应实现的代理执行，最终证据为
[核心/PD](M4c_evidence/review_kernel_pd.md) 与 [输入/预测](M4c_evidence/review_inputs_prediction.md)。
范围、额外样本及 hash 在同名 JSON；不把两个专项审查拼成全仓六路 G6。

四分片运行器的 Windows 原子替换只对 `PermissionError` 最多尝试 12 次，11 次退避总计不超过 0.65 s；
耗尽仍抛出，其他错误不重试。`test_m4c_runner.py` 的 6 门分别穿过主程序和实际插件函数，
独立审查再用真实 pytest 子进程验证恢复、永久占用及其他异常三种路径；
异常路径非零退出、实际调用节点不完整，不能因 sessionfinish 文件存在或日志有 passed 字样冒充绿。
详见 [运行器审查](M4c_evidence/review_runner.md)。

## 5. 全时程台账、四问与最小复现

### 5.1 完整性、闭集计数与冻结门

[完整摘要](M4c_evidence/full_summary.json)：15 例、1810 步、4 进程，墙钟 **1445.536826 s**。
[冻结摘要](M4c_evidence/frozen_summary.json)：15×30=450 步，墙钟 **178.174404 s**。
全量检查 64010 个“步—块对”，29518 个由精确扫掠盒证明窗口无接触，其余 34492 个求值。
初态贯入 16676 个步—块对全部计算 PD；资源未算 **0**，未分类 **0**，没有静默丢末步。
每个批次均有源/代码哈希、规范化记录及独立的新驱动完整批次复核：
[full](M4c_evidence/full_batch_revalidation.json)、[frozen](M4c_evidence/frozen_batch_revalidation.json)。

| 闭集类别 | 全 raw 主参考 | 全 post 主参考 | 全 VV 第二参考（raw=post） | 冻结 raw 主参考 | 冻结 post 主参考 | 冻结第二参考（raw=post） |
|---|---:|---:|---:|---:|---:|---:|
| FIRST_COVER_MATCH | 40 | 59 | 9 | 23 | 35 | 2 |
| FIRST_INCIDENCE_NOT_COVER | 0 | 0 | 0 | 0 | 0 | 0 |
| OTHER_FEATURE_FIRST | 133 | 114 | 3 | 58 | 46 | 1 |
| NO_CONTACT_IN_STEP | 59490 | 59490 | 5704 | 9499 | 9499 | 962 |
| INITIAL_TOUCH_COVER_MATCH | 661 | 661 | 37 | 661 | 661 | 37 |
| INITIAL_TOUCH_INCIDENCE_NOT_COVER | 8 | 8 | 8 | 8 | 8 | 8 |
| INITIAL_TOUCH_OTHER_FEATURE | 53 | 53 | 6 | 53 | 53 | 6 |
| INITIAL_OVERLAP_PD_MATCH | 14197 | 16190 | 398 | 3298 | 3868 | 91 |
| INITIAL_OVERLAP_PD_OTHER_FEATURE | 67012 | 65019 | 1603 | 11695 | 11125 | 361 |
| INITIAL_OVERLAP_PD_NOT_EVALUATED_RESOURCE | 0 | 0 | 0 | 0 | 0 | 0 |
| **合计** | **141594** | **141594** | **7768** | **25295** | **25295** | **1468** |

第二参考列是每张表各自的数，不将 raw+post 加在一起。所有 legacy 重复行保留。
完整原始计数与精确有理分母见 [四问 JSON](M4c_evidence/four_questions.json)。
独立、只用标准库的后验脚本逐行复数全部 1810 帧，且核对 35 个例子的来源/角色/前帧：
[结果及 68 个新接触块对明细](M4c_evidence/review_probes/summary_artifacts.json)。

### 5.2 四个问题的直接回答

**Q1：legacy 参考是否就是首盖？**

按原工单逐条主参考行比较，在“初态分离且本步确实接触”的 173 行中，raw 一致 **40/173=23.121387%**，
post 一致 **59/173=34.104046%**；另一特征先碰分别 **133/173=76.878613%**、**114/173=65.895954%**。
本组没有“在首时刻关联但非有效盖”的行，不能因此删除该闭集类别。
另有 **59490/59663=99.710038%** 的初态分离参考行在本步根本没有闭集接触；
它们不是“另一边先碰”，也不能默认叫 legacy 误检。

**行比例不是块对错误率。** 68 个本步新接触步—块对都在两张表中出现。
raw 至少一条 primary 首盖的块对为 38/68，考虑任一 primary/secondary 为 **47/68**；
post 分别为 57/68、**66/68**。完全没有首盖参考的块对 raw 为 21，post 为 **2**。
而已有首盖、仍带其他非首盖 primary 行的块对分别为 45、64。
因此不能把 post 的 65.90% 非首盖“行”说成 65.90% 块对选错边。
两个 post 无任一首盖的完整小例为 **bb51 step2 块对(3,9)**、**bb51 step47 块对(1,3)**；
原表都记录了块对，但前者每表 3 个主/次参考、后者每表 2 个参考均未命中首盖。
自包含的两块端点、该对全部原始行、身份别名及根证书见
[两对专项例](M4c_evidence/review_probes/post_no_first_cover_pairs.json)，
[精确复算通过](M4c_evidence/review_probes/post_no_first_cover_pairs_check.json)。

**Q2：有没有本步新接触、两张表都缺席的块对？深度多大？**

本数据为 **0/68**；初态已有相触/贯入但双表均无的步—块对也为 **0**。
故实际漏检深度为 **N/A（没有该类样本）**，不是深度等于 0，也不是证明任意运行无漏检。
人工清空两表的运动样本仍检出 1 个接触、精确 `tau=1/2`，证明枚举不受 legacy 表限制：
`test_swept_contact_pair_is_detected_with_both_legacy_tables_empty`。
该正控制不混入 1810 步计数。实现的深度仅为步末内部顶点净空证人；无证人用 null，非全局 PD、非步内峰值。

**Q3：初贯入参考边与全局最短出口一致吗？**

全部 PD 已算，主参考 raw 为 **14197/81209=17.482052%**，post 为 **16190/81209=19.936214%**。
VV 第二参考两表均为 **398/2001=19.890055%**。分母是贯入状态的参考行，不能换成 16676 个块对。
比较对象为全部最近出口点上的特征并集，非一个任意最近点代表；不由此判定 legacy 力学对错。

**Q4：平移替身与完整端点弦运动不同多少？**

按“接触状态或首盖集合不同”的描述性口径，候选初分离步—块对为 **790/17603=4.487871%**；
若限定真实运动确实接触，则为 **20/68=29.411765%**；若任一轨迹接触，则为 **790/838=94.272076%**。
大多数候选两者均无接触，会稀释第一种比率；三种分母必须一起看。
若按**时刻、接触状态或首盖集合任一不同**的严格首入逐值口径，则为
**838/17603=4.760552%**；实际接触条件下为 **68/68**，任一轨迹接触条件下为 **838/838**。
其中有 **48** 个同状态、同盖却精确时刻不同的块对；16765 个双无接触按双 null 计相同。
此统计以规范精确根证书而非 `time_display` 比较，逐项重核 17603 个 `same_time` 标记：
[时间敏感性证据](M4c_evidence/review_probes/timing_sensitivity.json)。
最小同盖异时身份是 bb03 step1 块对(1,2)，双方证书在该文件；**精确不等不自动表示工程误差很大**。
**17603 个替身全为非零残差、全未认证；认证一致率分母为 0，未定义。**
这些描述性数值不是忽略转动/应变的安全证书。

上一段位移外推的条件样本中，17560/17574 **状态与首盖集相同**（包括双无接触，不比较时刻）、14/17574 不同，29 个首步样本 unavailable，
预测域无效样本 0。这个分母受真实/legacy 候选筛选影响，不能叫在线全对预测准确率。

### 5.3 每例摘要

首盖列分母只取初分离且实际接触的主参考行；PD 列分母只取初贯入主参考行。
新接触/漏检和替身列的单位是“步—块对”；`0/0` 表示无该样本，不是 0% 匹配。
各例完整十类原始计数保存在 full_summary 的 `cases` 中。

| 算例 | 步 | raw 首盖 | post 首盖 | raw PD | post PD | 新接触/漏检 | 替身不同/候选 | 例内秒 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| bb52 | 50 | 2/4 | 2/4 | 839/2216 | 888/2216 | 2 / 0 | 2/365 | 181.57 |
| bb12 | 100 | 8/22 | 10/22 | 1538/4303 | 1779/4303 | 10 / 0 | 43/374 | 27.28 |
| bb50 | 50 | 0/0 | 0/0 | 0/0 | 0/0 | 0 / 0 | 0/49 | 66.42 |
| bb51 | 50 | 3/16 | 3/16 | 313/1705 | 320/1705 | 6 / 0 | 54/621 | 184.61 |
| bb03 | 100 | 5/18 | 8/18 | 960/2492 | 1243/2492 | 9 / 0 | 140/1102 | 35.59 |
| bb05 | 100 | 4/16 | 8/16 | 301/654 | 327/654 | 8 / 0 | 16/266 | 3.55 |
| bb06 | 100 | 2/6 | 3/6 | 269/531 | 299/531 | 3 / 0 | 4/225 | 3.03 |
| bb09 | 100 | 4/16 | 7/16 | 1133/3025 | 1396/3025 | 9 / 0 | 367/1529 | 16.24 |
| bb10 | 100 | 4/17 | 7/17 | 789/2529 | 1256/2529 | 12 / 0 | 140/1730 | 39.60 |
| bbv01 | 100 | 0/0 | 0/0 | 1584/9617 | 1584/9617 | 0 / 0 | 5/1086 | 369.38 |
| bbv01_dbv01a | 400 | 4/36 | 6/36 | 3711/31039 | 4140/31039 | 5 / 0 | 9/6671 | 1335.65 |
| bbv02 | 100 | 0/0 | 0/0 | 695/5669 | 794/5669 | 0 / 0 | 5/495 | 184.87 |
| bbv02_dbv02a | 400 | 2/18 | 3/18 | 2007/17313 | 2106/17313 | 2 / 0 | 5/3088 | 656.53 |
| bbF038 | 30 | 1/2 | 1/2 | 29/58 | 29/58 | 1 / 0 | 0/1 | 0.20 |
| bbS038 | 30 | 1/2 | 1/2 | 29/58 | 29/58 | 1 / 0 | 0/1 | 0.20 |

### 5.4 最小可复现端点例

[minimal_examples.json](M4c_evidence/minimal_examples.json) 以顶点总数、case/step/pair 排序选小例，
保留四个端点几何、前帧、全局编号、精确根证书、原参考行及两种源哈希。
这里的“最小”是此确定排序下选取的小型实物例，不宣称已做数学全局最小化。
35 例已通过 [独立文件复算结果](M4c_evidence/minimal_examples_reproduced.json)；
此复算走生产 API，不冒充独立几何 oracle。

| 结论/JSON 键 | 最小实物定位与结果 |
|---|---|
| `raw_df05:FIRST_COVER_MATCH` | bb09 step76，块对(10,11)；首时刻显示 0.013506123193859555，盖为顶点72—边(79,80)。 |
| `raw_df05:OTHER_FEATURE_FIRST` | 同一块对/时刻，另一个参考顶点79—边(72,73)不是首盖；同一表已有正确参考，正好说明行差异不等于整对漏检。 |
| `raw_df05:NO_CONTACT_IN_STEP` | bb09 step2，块对(10,11)，参考顶点72—边(79,81)，本步无接触。 |
| `raw_df05:INITIAL_OVERLAP_PD_OTHER_FEATURE` | bb09 step77，块对(10,11)；PD 显示约 2.100726898×10^-5（原模型长度单位），出口盖是72—(79,80)，参考79—(72,73)不属该最优集；MATCH 键保存同帧另一条匹配参考。 |
| `TRANSLATION_DIFFERENT` | bb09 step2，块对(10,11)；真实无接触，替身首入约0.2213010654，delta约1.6612×10^-3，未认证。 |
| `TRANSLATION_DIFFERENT_WITH_ACTUAL_CONTACT` | bb03 step26，块对(5,6)；真实首入约0.9203312426，盖55—(45,47)，替身无接触，delta约4.1640×10^-4，未认证。 |
| `PREDICTION_DIFFERENT` | bb05 step3，块对(3,4)；真实首入约0.5244025158，上一段位移预测无接触。 |

补充的两对 post 无首盖例不改变上述 35 例文件：bb51 step2 的首盖为顶点93—边(149,153)，时刻显示约0.3770883463；
step47 的首盖为顶点94—边(38,39)，时刻显示约0.0528476453。
它们从完整 1810 帧中筛选，再用生产求根及独立 Fraction 关联/法锥检查复算，不冒充全独立求根 oracle。

全数据的“漏检为零”是穷举计数结论，不能由单个小例证明；其最小正控制是上述清空两表的 `tau=1/2` 门，
真实正例则是 bb09 step76 的表内接触。全部 VV secondary 类别也有各自 `:secondary:` 键，未挪用 primary 例。

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:TEMP=(Join-Path (Get-Location) 'reports/codex/M4c_evidence/tmp')
$env:TMP=$env:TEMP
python -X utf8 tools/m4c_reproduce_examples.py
python -X utf8 tools/m4c_reproduce_examples.py --name 'raw_df05:OTHER_FEATURE_FIRST'
python -X utf8 reports/codex/M4c_evidence/review_probes/post_no_first_cover_pairs.py --verify-only
python -X utf8 -m pytest -q tests/test_m4c_replay.py::test_swept_contact_pair_is_detected_with_both_legacy_tables_empty
```

## 6. 对 M4 后续的含义与字段提案

legacy 静态窗口内的有效接触与沿本步弦轨迹最先接触不是同一观测量。
无接触步的 legacy 行可能体现容差窗口、保留/匹配设计，不能仅凭本台账认定“误检”；
另外一条边先接触或缺席块对是可复核的几何差异，需要下一阶段结合力、时间离散和接触历程确认物理影响。
PD 特征不一致同样不能直接推成物理错误。具体比例和实例以第 5 节为准。

本数据中的证据优先级应区分：59490 条初分离且本步无接触的参考行，与静态容差窗口的设计目的并不矛盾，
但本单没有逐行证明它们全由某一个容差阈值造成；因此只能称“与窗口/保留机制相容”，不能把所有差异洗成容差设计。
post 中 **2/68** 个新接触块对没有任一主/第二参考命中首盖，是优先追查的几何差异；
其余 66 对已有首盖，再带非首盖行不等于整对漏检。真正双表缺席的新接触块对为 0，不能虚构本单发现漏检。
平移替身在实际发生新接触的 68 对中，有 20 对状态/首盖集不同，足以支持 M5 继续处理转动/应变的必要性，
却不足以证明某个转动模型、接触力或在线替换方案已经正确。

建议只新增导出协议字段（本单不实施）：`accepted_step`、`attempt_id`、accepted/rejected、
`dt_used`、`time_begin/end`、稳定 block/vertex 身份、`topology_revision`、步初形心与六自由度速度、
rotation update mode、暂定/已接受位移、开挖/增删标志。必须明确速度时间层与有限转动积分方式，
之后才有资格评价全体块对的事前预测或开闭迭代暂定位移替换。

## 7. 全套、静态、性能和遗留

### 7.1 最终四分片（全新字节导出）

本次唯一有效最终全套为 `final_suite_r2`，四片最后一行原样如下，顺序为第 1—4 片：

```text
3244 passed in 769.96s (0:12:49)
3244 passed in 761.16s (0:12:41)
3243 passed in 761.02s (0:12:41)
3243 passed in 1503.25s (0:25:03)
```

四片各自真实收集与 call 执行节点数为 3244/3244/3243/3243，合计 **12974**；0 failed、0 skip。
每片的派发、实际收集和实际执行节点多重集合相等；四片并集等于全套收集集合，不用 passed 字样或总数相等替代身份核对。
见 [完整 GREEN summary](M4c_evidence/final_suite_r2/summary.json)、
[独立节点复核](M4c_evidence/review_probes/runner_final_nodes.json)。
全仓静态末行原样为：

```text
exact construction AST gate: 0 violation(s)
```

construction policy 与 HEAD **逐字节未变**；既有豁免 **3103 条，新增 0 条**，没有新增豁免需要逐条解释。
新增公开构造已登记 inventory。最终 [交付审核](M4c_evidence/delivery_audit.json) 核对了 **481 个**导出受测的 src/tests/tools/fixtures 文件与当前文件 SHA256 相同。
两个新增夹具已补登中央 PROVENANCE，旧 198 条逐项不变，保持其 CRLF 与 UTF-8 无 BOM；
[补登审计](M4c_evidence/fixture_provenance_registration.json) 记录前后哈希。
这是一轮完整、独立于作废 r1 的新运行，**不是拼接旧片段**；也不是提交后的新鲜 Git checkout。

复跑须从本树执行，输出目录必须尚不存在：

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONIOENCODING='utf-8'
$env:TEMP=(Join-Path (Get-Location) 'reports/codex/M4c_evidence/tmp')
$env:TMP=$env:TEMP
python -X utf8 tools/m4c_run_gates.py --name final_suite_acceptance_new
```

### 7.2 计时与性能口径

环境为 Python 3.12.10、pytest 9.0.3、Windows 11，4 进程分片；[运行环境指纹](M4c_evidence/runtime_environment.json)。

| 实测量 | 最终值 | 口径 |
|---|---:|---|
| collection + 四片 + 全仓静态墙钟 | 1700.583613 s | 新鲜字节导出之后计时，不含导出复制 |
| 四片 pytest 末行秒数之和 | 3795.39 s | 并行进程各自报告的时长之和，不是墙钟 |
| 全仓静态进程墙钟 | 155.053398 s | 含进程启动与完成轮询 |
| 全部测试 call 阶段累计 | 3523.370647 s | 四片实际报告相加，非墙钟 |
| 211 个 M4c 节点 call 累计 | 19.838791 s | 占全部 call 时间 **0.563063%** |
| M4c call 各片累计 | 2.861172 / 3.766572 / 8.611558 / 4.599488 s | 不含新增代码对既有全仓静态测试成本的间接影响 |
| 15 例 1810 区间回放墙钟 | 1445.536826 s | 完整 full_replay_r4 |
| 15 例 450 区间冻结回放墙钟 | 178.174404 s | 完整 frozen_replay_r2 |

历史 [M3 报告](M3_report.md) 四片为 942.75 / 746.55 / 1596.41 / 643.94 秒；墙钟 1864.6112571 秒（含静态 199.7717682 秒）。
这些**不是同字节基线、只作耗时参考**。虽然新门 call 占比很小，最终墙钟也小于该历史值，
两者都不能证明“相对同字节起点全套增量约 10% 以内”；该性能目标仍列 **未认证**，不捏造受控增量百分比。

### 7.3 交付范围与剩余项

| 工单项目 | 最终状态 |
|---|---|
| DDA 运动学、端点弦定义、VE 二次事件与精确比较论证 | 已落盘并有具名门；条件数学证明，不是程序形式化证明 |
| 精确运动首入、全部并列、整步域外响亮失败 | 已实现，平移 M3/M2、独立闭式、元门和指定变异通过 |
| 初贯入 PD_closed 全并列、两表主/次参考对账 | 已实现；16676 个初贯入步—块对全部求 PD，未算 0 |
| 完整 1810 / 冻结 450 区间、闭集与四问 | 已完成；未分类 0，输入失败闭集、哈希和最小例可复跑 |
| 证书负门与 δ=0 相同轨迹证书 | 已通过；一般 δ>0 区间证书未实现，实物 17603 个替身全未认证 |
| 事前版本 | 已评估上一位移外推，但仅条件候选域；无完整步初速度，字段只提案 |
| 最终四片、节点身份、零 skip、静态与数值合同 | 已通过；不借 PARTIAL 豁免硬门 |
| 约 10% 增量性能目标 | 未认证；仅有当前实测及非同字节历史参考 |
| 全仓六路 G6 与提交后新鲜工作树退出 | 未完成；本次专项独立审查和无 .git 字节导出不冒充退出批准 |

材料输入仍限单环，带洞一致门是 **E 的洞**，不是多环材料支持；端点弦并非连续有限转动。
不更改 b-DDA，不作在线替换或物理正确性判断；没有 commit/push/reset/checkout/stash/worktree 或创建/切换分支，只有只读状态与现有分支/HEAD 核验。
早期 TEMP 越界偏差没有被后续绿色结果抹去，具体范围限制见第 1 节。
最终文件清单、哈希及可点击入口见 [交付索引](M4c_evidence/DELIVERY_INDEX.md) 和 [成果 manifest](M4c_evidence/artifact_manifest.json)。

M4c_PARTIAL：一般非零 δ 首盖稳定性证书未实现；约 10% 增量性能目标缺同字节基线未认证；完整 G6 与提交后新鲜工作树退出未完成；材料输入限单环。
