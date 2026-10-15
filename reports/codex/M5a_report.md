# WO-M5a：二维带转动的入口块与首入

日期：2026-10-15。执行树：`D:/eab-wt/cx-e2`；起点 `codex-work / 3bf5e955d8ea669846a088f50223e17e76475947`。

## 0. 结论与阅读入口

**研究级 PARTIAL，不宣称 M5 里程碑退出。** 已实现有理 SE(2) 轨迹的精确首入、五次实代数时间、固定角切片、M3/M4c 纯平移退化、独立 oracle、内部语义变异及 1810 步影子回放。支持域为单简单环、每块一步转角不超过 90°。它是指定插值模型，不是 b-DDA 未观测的步内真实运动。

- 20 个“平移替身与弦模型不同”的新接触样本：SE(2) 与弦模型 **7 对同状态同完整首盖，13 对不同**。
- 全部 68 个弦模型新接触样本：**51 对同完整首盖、2 对仍接触但换盖、15 对不接触；精确时刻相等为 0**。
- 15220 次端点拟合全部 `δ>0`；**64010 个步—无序块对全部未认证，认证 0**。不能把新模型的 973 个新接触解释为物理正确性改善或 legacy 缺陷。
- 最终新鲜字节副本四片 **13254 收集＝执行、0 skip**；静态构造门 **0 违例**。源字节、UTF-8 无 BOM 与运行文件大小审计通过，详见 §7。不是提交后 worktree 或 G6 退出证明。

关键入口：[先行理论](../../docs/m5a_se2_design.md)、[证据索引](M5a_evidence/DELIVERY_INDEX.md)、[三个问题与逐对数据](M5a_evidence/three_answers.json)、[中文回放报告](M5a_evidence/replay_report.md)。

所有运行文件均在本工作树内；未写姊妹仓库、未运行它们的程序、未执行 Git 写操作。

## 1. 合同、范围与回退锚

目标是在明确的刚体插值路径上求闭集首次接触：返回精确时刻、完整闭段关联、有效盖及全部并列、初态、窗口无接触；贯入初态比较量冻结为步初 `PD_closed`。不替换任何姊妹内核，不承诺工程认证，不构造整个三维配置空间曲面安排。

开始时只读核对分支、HEAD 和干净状态。回退锚为该 HEAD、`baseline_suite_r1` 的只读 `git archive` 导出及最终 [文件哈希清单](M5a_evidence/artifact_manifest.json)。没有执行回退、commit、push、stash、checkout、reset、branch 或 worktree 写操作。

本单禁止新建 worktree，故最终全套在本树 `M5a_evidence/tmp/` 下的**新鲜字节导出**执行，不冒称提交后全新 Git checkout。提交、合并后新鲜 worktree 与六路 G6 仍由所有者安排。

共享文档仅增补 M5 内容；`fixtures/PROVENANCE.json` 仅追加 16 条本单夹具。原 M4c 的 `frozen_summary.json` 仅刷新当前代码绑定并链接本单重验证证据：450 帧原路径完整重算、历史夹具及结果不改。详见 [回放交付审计](M5a_evidence/replay_delivery_audit.json)。

## 2. 理论：定义、条件、证明状态

完整推导在 [先行设计](../../docs/m5a_se2_design.md)，在核心代码实施前写入；实现时再补精确剪枝证明与具名门索引。下列“证明”指所列条件下的数学推导，不是程序形式化验证，也不是从有限测试推导普遍正确。

### 2.1 对象与接触族（T1）

对紧致正则闭多边形实体 A、B：

```text
C = {(t,θ): (Rθ A+t) ∩ B ≠ ∅}
P = {(t,θ): int(Rθ A+t) ∩ int(B) ≠ ∅}
Eθ = {t: (t,θ)∈C} = B ⊕ (−Rθ A)
```

实体三态为 `C` 外／`C\P`／`P`，与拓扑外部／边界／内部不同；紧配合相触可能是接触内缝。固定切片等式由 `t=b−Rθa` 的存在性直接证明，不要求凸性。全体 C 不能作为一个固定二维 Minkowski 差使用。

VE 族满足 `cross(e,Rθa+t−b)=0` 且 `0≤dot(e,Rθa+t−b)≤|e|²`；EV 对称交换两块；VV 满足 `Rθa+t=b`。配置障碍边界包含于这些闭接触族之并，但反包含不成立：方程还包含贯入关联和接触内缝。平行重叠含端点—边事件。程序的 `features` 是 M3 同口径局部法锥标签，不冒称整个 C 边界认证。

### 2.2 精确旋转、轨迹与次数（T2、T3）

```text
R(u) = [[1−u²,−2u],[2u,1−u²]] / (1+u²)
X_i(s,x) = c_i+s d_i+R(s u_i)(x−c_i),   0≤s≤1
```

`RᵀR=I, det R=1`，两端精确闭合，所有点对距离保持；`u=tan(θ/2)` 的单 chart 数学范围为 `−π<θ<π`。程序路径保守限制 `|u_i|≤1`，并非声称参数化在 90° 失效。转角参数只收整数/Fraction；坐标中的有限 binary64 被解释为该浮点数的精确有理值。

两块各自使用世界轨迹，避免把两条运动错误压成“相对参考点线性移动”。设 `D_i=1+(su_i)²`、`M_i=D_iR(su_i)`，局部 A 顶点 a、B 边起点 b 和向量 e，令：

```text
Q=D_A D_B>0
W=(c_A+s d_A−c_B−s d_B)D_A+M_A a
F=cross(M_B e,W)−Q cross(e,b)
G=dot(M_B e,W)−Q dot(e,b)
H=|e|²Q−G
```

精确关联当且仅当 `F=0,G≥0,H≥0`。F/G/H 次数不超过 **5**；一个运动块对固定块不超过 3，固定轴单块纯转动不超过 2。清分母保持符号，不使用平方消元制造伪根。

首次接触存在性来自紧致性与闭性；非平行边内部横交会稳定地产生内部交叠，不可能是从分离到接触的首次位形；平行边相交含至少一个端点—边关联。因此双向 VE/EV 枚举完备，VV 为端点退化。`F≡0` 时枚举 G/H 根及窗口端点，不能略过恒共线。最早根确定后重新取全部关联及盖集合。

本模型不是匀角速度：`θ(s)=2 atan(su_i)`。单体固定轴单调转动可仅重参数化而保持顺序；同时平移或双体运动时，改变角速度律一般改变配置路径及接触顺序。更不能从端点推断 b-DDA 在步内采用了本插值。

### 2.3 实代数时间、退化与特例（T4、T5）

- 平方自由化 `p/gcd(p,p')`、Sturm 变化数、精确有理二分隔离全部不同根；闭区间端点根单列保留。
- 两个指定根判等用 gcd 与隔离区间中的共同根身份，不以区间相交或“gcd 非常数”单独判等。不同根细分至分离；代数根处多项式符号也用精确公共根/区间证明。
- Horner 包含界或 Bernstein 系数证书证明闭区间严格同号时才排除，未知回退 Sturm；Bernstein 内部系数允许为零，但首尾严格同号及基函数正性仍可证明全窗严格同号。重根、端点根不能剪掉。
- RealAlgebraic 显示值经 `construction.scalar_algebraic` 精确比较 binary64 中点并 RN-even 舍入；已识别有理单点回传 QuadraticTime 时显示走原 `scalar_rational`。判定路径不使用显示值或 epsilon。
- `u_A=u_B=0` 时轨迹逐点等于 M4c 弦轨迹、相对位移线性进入 M3 的 `B−A`。实现没有直接返回旧 API 的零转动捷径；一般事件代码本身受逐值退化门约束。
- 初态贯入不伪造一个运动首入时刻：保留 `initial_overlap`，惰性提供步初完整边界（含 E 洞壁）的 `PD_closed`。不是旋转逃逸距离或弹簧压入量。

闭式门：边长 2 正方形中心转动撞 `x=6/5` 墙、`u1=1` 时首根满足 `11s²−10s+1=0`（两个实根中较早者）；绕顶点杠杆闭式门使用 `s²−8s+4=0`。这些门同时核对身份与首根，不能只核一个近似角。

协变证明使用 `T(x)=λQx+z`：同时变换几何、参考点、位移并保持 u，有 `X'_i(s,T(x))=T(X_i(s,x))`。时刻、状态、带身份集合不变；PD 距离乘 λ。只挪参考点而不改轨迹合同不属于这个不变性主张。

### 2.4 拟合与认证条件（T6）

参考点取两端顶点均值，平移取其精确差；居中协方差提出旋转参数。精确单位协方差直接恢复有理半角；否则有理平方根或 `2^-80` 整数平方根网格提出参数，再作 `2^40` 分母上限的确定性有理近似。**这不是“有理参数集上的全局最优拟合”主张。** 最终几何和残差全部重新用精确有理数计算：

```text
δ_i = max_j || y_j − (c_i+d_i+R(u_i)(x_j−c_i)) ||∞
δ_pair = δ_A+δ_B
```

δ 汇集应变、快照 binary64 舍入和拟合近似，不能单独分解。只有 δ=0 标为 `CERTIFIED_RIGID_ENDPOINT_MODEL`，其含义也仅为**指定刚体模型与端点精确相容**；不代表与弦轨迹相同，更不认证实际连续运动。δ>0 全部 `UNCERTIFIED_NONRIGID_ENDPOINTS`。

仅有端点残差不能约束任意连续轨迹的中途偏离；首盖平局还可被任意小扰动拆分。一般 δ>0 首盖不变证书需要整段误差界、横截与竞争事件间隔等额外条件。本单未证明/实现此证书，明确 PARTIAL。

### 2.5 文献逐条核验状态

| 文献 | 本次状态 | 使用范围 |
|---|---|---|
| LaValle, *Planning Algorithms* (2006), Ch.4 §§4.2.1、4.3.1–4.3.3 | **已核原文（相关节，非全书）** | 配置空间、C-障碍、平移差及旋转接触代数化；不把本单五次轨迹证明归给该书。[作者 PDF](https://lavalle.pl/planning/ch4.pdf) |
| Basu, Pollack, Roy, *Algorithms in Real Algebraic Geometry*, 2nd ed. (2006) | **未核原文** | 只核作者书目/下载页，不代替本单 Sturm/gcd 推导。[作者页面](https://www.math.purdue.edu/~sbasu/bpr-posted1.html) |
| 石根华 E(A,B) 及正本列出的历史实现论文 | **未核原文** | 不主张优先性、忠实重现原算法或真实 DDA 步内轨迹 |

M3/M4c 设计、报告、差异台账与计划的 M5/诚实条款作为本地合同读入；它们不是外文论文原文核验。

## 3. 实现与 API

| 文件/API | 合同 |
|---|---|
| `kernel2d/algebraic.py::RealAlgebraic` | 次数≤5，生成多项式+指定根隔离区间；compare、sign_polynomial、refine、certificate、time；无隐式浮点身份判断，不可哈希 |
| `roots_interval(p,lo,hi)` | 有理系数低次到高次，窗口全部不同实根精确排序 |
| `kernel2d/se2.py::SE2Motion(u1,translation,center)` | 两点端闭合的规定刚体路径；at/endpoint 输出有理坐标；`|u1|>1` 或无效参数报错 |
| `rotate_rational(point,u)` | 任意有限精确有理半角的坐标旋转；不是路径跨 chart 支持 |
| `se2_slice(A,B,u)` | 旋转 A 后直接复用 M3 `GlobalEntrance2` |
| `se2_first_entrance(A0,B0,motion_a,motion_b)` | `SE2Entrance2`，含 initial_state、status、exact_time、incidences、features、tied_features、pd_closed |
| `construction.scalar_algebraic(compare)` | 唯一新增 binary64 显示边界；精确比较回调，不允许把返回值当成精确谓词输入 |
| `tools/m5a_se2_replay.py` | case/batch/freeze/revalidate-m4c/reproduce；离线拟合、回放、冻结与复现 |

`initial_state` 为 −1/0/+1，`status` 为 contact/no_contact/initial_overlap。代数时间用 RealAlgebraic；已识别为有理单点的结果保留原 QuadraticTime 容器兼容 M4c 逐值比较（高次生成式的有理根仍可留在 RealAlgebraic 表示）。`features` 及 `tied_features` 是完整盖集合，`incidences` 另含非盖闭段关联；不能取序列第一个当作唯一接触。

材料只收单个简单全维环，支持凹形、平直相邻边与 CW 输入身份还原；自交、回折/零长边及材料多环响亮拒绝。**E 可有洞与材料本身支持多环不是一回事。** 未实现 SE(2) 最短逃逸、全 C 边界安排、跨 chart 分段。

## 4. 门与 oracle 独立性

主张到测试的完整索引见设计 §10。最终新增 M5a 测试节点 128：代数 26、轨迹 38、独立 oracle 15、回放 49；新夹具使既有溯源参数门另增 16。合计较起点 13110 增加 144，最终收集 13254。

| 必须门 | 实际覆盖与具名门 |
|---|---|
| 纯平移最重要一致门 | `test_zero_rotation_is_exactly_m3_and_m4c_all_fields`：L、槽角楔、互锁截面、零间隙、E 洞、共线，三档尺度；比精确时刻、初态、关联、盖及并列，不止状态 |
| 初态与闭窗口 | `test_initial_states_zero_motion_and_persistent_collinearity_equal_m4c`、`test_rotating_closed_endpoint_is_not_lost`、`test_initial_pd_is_frozen` |
| 闭式独立几何 | `test_square_center_rotation_closed_form_and_two_real_roots`、`test_pivot_rotation_has_independent_lever_closed_form`，包含首根、完整特征与三档 |
| 随机独立差分 | `test_random_complete_events_match_independent_sturm_and_g0`：固定种子十个真正双体五次例，加无接触/并列例，共 12 几何输入、132 个分段 G0 探针；含凹形、无理时刻、多特征 |
| 代数数 | 独立有理二分、随机已知因式、重根、共同根、相邻根间距 `2^-90`、错误根支、端点根、精确符号；见 `test_m5a_algebraic.py` |
| 元门 | `test_se2_is_rigid_frame_and_unit_covariant`、`test_two_rotating_translating_bodies_transform_with_their_reference_points`：90°系列及固定种子有理旋转，平移 0/1e3/1e5/1e6，尺度 1e−9/1/1e8；比较集合 |
| 范围与方向 | `test_clockwise_feature_identity_and_unsupported_domains_are_explicit`：CW 身份、坏环、浮点角参数、近π大转角拒绝 |
| 拟合与认证 | 精确刚体合成例 δ=0、微小非零残差不能入认证分母；三档残差显示；安全投影包含与等号不剔除，均有内部语义变异 |
| 冻结门 | 15×30 全帧哈希/分类/分母守恒、15 个实际拟合重算、3 个实际非零转角块对首入重算；见 `test_m5a_replay.py` |

### 4.1 Oracle import 清单与自校验

`tests/m5a_independent_oracle.py` 的完整 import 清单为：

```python
from fractions import Fraction as F
from functools import cmp_to_key, lru_cache
from eab.kernel2d.g0_oracle import overlap
```

oracle 自己实现 Cayley 坐标、6 个有理时点插值事件多项式（另 2 点核验）、多项式/Sturm/gcd、代数根符号与法锥；不 import 生产 se2、algebraic、motion、exact 或 GlobalEntrance2。G0 用独立实体三态原语，不与生产初态 `polygons_overlap_exact` 共用。测试 harness 同时调用 oracle 和被测 API，不被包装为“oracle 内部独立性”。

自校验含闭式、重复/邻近/无理根、轨迹两端；独立全事件根分段与有理探针共同使用，不把稀疏采样本身当作连续完备性证明。另有 120 个多项式、95 个根的独立差分审阅记录：[algebra_random_independent_review.json](M5a_evidence/algebra_random_independent_review.json)。

### 4.2 数值合同与静态门

新增公开构造已登记 [inventory](../../docs/r13fix_construction_inventory.md) 的 M5a 段。有理坐标、系数、参数、证书及整数状态不作为 binary64 构造量；代数时间显示与回放残差显示分别走 construction 边界。显示门含次正规、小/中/大三档、舍入中点、下溢及溢出；多项式系数三档含 `2^-400/1/2^397`，产物互异明确检查。

静态扫描器仅新增 `scalar_algebraic` 为**有舍入来源的 construction intrinsic**，不是任意精确函数白名单。原 3103 个政策条目不改；新增 **117 个 AST 位置及局部词法范围源码 SHA 绑定准入**（含 2 个模块级位置）：construction 17、algebraic 28、se2 25、独立 oracle 42、测试 helper 5。数量并不为零，不能写“无新增豁免”。每条理由和 pin 见 [static_admissions.json](M5a_evidence/static_admissions.json)。

独立静态复核验证旧条目、117 个 pin、24 个局部变异使 117/117 条失效，10/10 个恶意样例被相应来源/默认拒绝规则拦截；[报告](M5a_evidence/static_review.md) 明确列出局限：pin 非传递闭包，且复核者是 42 个 oracle 站点作者，不伪称全量作者独立。专项静态全仓扫描 `exact construction AST gate: 0 violation(s)`，141 项静态回归通过；最终全套再次扫描见 §7。

## 5. 变异有牙证据

有效批次 [mutations_r2/summary.json](M5a_evidence/mutations_r2/summary.json)。每项复制真实源码到本树 tmp、替换被测函数内部后启动新进程；7 个正常对照都绿、7 个缺陷都红在预期语义断言。**未选任何源码哈希门**；SHA 仅记录来源，不参与杀死变异。

| 内部变异 | 预期报红断言（原文） | 结果 |
|---|---|---|
| 根隔离区间错一位 | `isolation bit retains the selected root` | 对照绿，变异此断言红 |
| 取最后一个而非首个实根 | `earliest square-wall real root` | 同上 |
| 判等改为近似 | `near roots are algebraically distinct` | 同上 |
| 转动 x 分量 sin 符号错 | `square-wall complete first feature` | 同上 |
| 零转动绕开一般事件路径 | `general path must retain translation events` | 同上 |
| endpoint 误取半步 s=1/2 | `trajectory final endpoint closure` | 同上 |
| 五次项截断 | `independent first-root identity rejects lost degree-five term` | 同上 |

早期内存补丁试验曾被 `_validated_ring` 缓存掩盖，已记录为 verification error：清空变异前后缓存并复测；最终外部源变异用新进程，排除这个假绿原因。未隐藏早期失败，见 [工作日志](M5a_evidence/WORK_LOG.md)。

## 6. 影子对账：直接回答三个问题

### 6.1 完整性与计数单位

一个未中断的新批次覆盖 15 例、1810 区间、64010 个步—无序块对，4 工作进程，997.846868 秒。全部类别闭合，未分类 0。中间大记录在忽略的 tmp，永久摘要为 [full_summary.json](M5a_evidence/full_summary.json)。

安全宽阶段在 legacy 候选之外逐对证明剔除 29518 对；保留 34492 对进一步处理，其中投影包含证明剔除 8623、同初始几何复用 16889、实际 SE(2) 事件枚举 8980。保留部分初态分离 17603、相触 213、贯入 16676。初态/冻结 PD 与弦结果明确复用哈希绑定 M4c 历史值，**不是本批次全量重算 M4c**；旧路径另做了 450 帧新鲜重算。

冻结来源为这一完整批次的 15×30 前缀；16 个新文件均入溯源。pytest 检查全部 450 帧冻结记录及闭合合同，并重算 15 个拟合和 3 个非零转角事件对；**不声称日常 pytest 重做了 450 帧全部根隔离**。完整重算保留为证据脚本以控制常规耗时。

### 6.2 问题一：与弦模型是否一致？

| 群组 | 同状态同完整首盖 | 仍接触但换盖 | SE(2) 无接触 |
|---|---:|---:|---:|
| M4c 的 68 个弦模型新接触对 | 51 | 2 | 15 |
| 其中平移替身有差异的 20 对 | 7 | 1 | 12 |

20 对的逐对表见 [replay_report.md](M5a_evidence/replay_report.md)，机器记录见 [three_answers.json](M5a_evidence/three_answers.json)。即便盖相同，68 对中精确时刻相等为 0。

同一 17603 个初态分离保留候选对下，SE(2)/弦状态或首盖差异为 937，平移替身/弦历史差异为 790。**加入转动并不必然更接近端点弦**：本模型同时移除了应变并改变步内路径。SE(2) 新接触 973 对不是物理错误计数。

最小例 **bb52，第 1 步，块对 (2,6)**：弦模型在显示时刻约 `0.0001486242818254717` 首触 `VE(57,124,125)`；平移替身和 SE(2) 均为窗口无接触。其 A/B 残差约 `0.0043747805841905215 / 0.009949253573530093`，所以这只是未认证模型差异。

### 6.3 问题二：legacy 参考是不是刚体模型首盖？

只对分离初态的首盖成员关系回答；初始相触、初始贯入的 PD 比较另列。按**无序步—块对去重**，VV 次参考与主参考取命中并集：

| 群组 | 阶段 | 任一参考首盖命中 | 有参考但不命中 | legacy 无该对 |
|---|---|---:|---:|---:|
| SE(2) 的 973 个新接触对 | raw_df05 | 645 | 328 | 0 |
| 同上 | post_df06 | 955 | 18 | 0 |
| 弦模型的 68 个新接触对 | raw_df05 | 39 | 29 | 0 |
| 同上 | post_df06 | 51 | 17 | 0 |
| 争议 20 对 | raw_df05 | 4 | 16 | 0 |
| 同上 | post_df06 | 7 | 13 | 0 |

68 对在原弦模型下任一参考命中为 raw 47、post 66；上述改成 39/51。逐参考行（不是块对）刚体主参考首盖命中 raw 406、post 716；VV 次参考各 244。完整八类行计数、每个 M4c→SE(2) 转移及去重分母都在 `three_answers.json`，不能混用两种计数单位。

最小例仍为 **bb52/1/(2,6)**：原 legacy 参考 `VE(57,124,125)` 在弦模型为 `FIRST_COVER_MATCH`，在刚体模型变为 `NO_CONTACT_IN_STEP`。这不是“选错刚体首盖”，而是刚体模型根本没有接触；更不推断 legacy 真实物理错误。

### 6.4 问题三：δ 多大、认证多少？

15220 次逐块拟合，δ=0 为 **0**、δ>0 为 **15220**；认证步—块对 **0**，未认证 **64010**。L∞ 残差使用快照原几何单位：

| 分位 | 显示值 |
|---|---:|
| 最小 | 6.901346436899115e−16 |
| 中位数 | 0.0022171352173461093 |
| p95 | 0.034415493885976714 |
| 最大 | 0.18454965299659865 |

每个量的精确分数保留在 JSON。最小例 **bbv02_dbv02a，第 54 步，块 5**（复现配对 (2,5)）：最大残差精确为
`2201011120905552493157656769684521651 / 11926389918197887131608482271392169984`。

三个问题的小例均带原始端点、稳定编号与参考，且已实际重执行：[输入](M5a_evidence/minimal_examples.json)、[复现输出](M5a_evidence/minimal_examples_reproduced.json)。第三例重算拟合与 SE(2) 初态，若初态贯入，其 PD 仍按已声明合同复用历史冻结量，不声称该小例重新解 PD。不能用“残差很小”改标为认证；合成 δ=0 的代码门只证明标签逻辑，不补造真实数据中的认证案例。

## 7. 全套、静态、性能与交付审计

### 7.1 基线

只读 HEAD archive 新鲜字节导出，全套四片收集=执行=13110，0 skip，静态 0 违例。末行原样：

```text
3278 passed in 831.24s (0:13:51)
3278 passed in 810.00s (0:13:30)
3277 passed in 827.50s (0:13:47)
3277 passed in 1527.86s (0:25:27)
```

含收集、四片及静态总墙钟 1710.529766 秒。[原始摘要](M5a_evidence/baseline_suite_r1/summary.json)。

### 7.2 最终四片

`final_suite_r1` 一个完整批次，全套四片 **13254 收集＝派发＝实际 call 执行、0 skip**；setup/call/teardown 全 passed。基线的 13110 个节点全部保留，0 移除；新增 144。最终四片最后一行原样如下，按分片 1–4 排列：

```text
3314 passed in 739.15s (0:12:19)
3314 passed in 714.95s (0:11:54)
3313 passed in 737.78s (0:12:17)
3313 passed in 1426.50s (0:23:46)
```

静态门原样末行：

```text
exact construction AST gate: 0 violation(s)
```

静态扫描 150.045795 秒；含收集、四片及静态总墙钟 **1611.406236 秒**。证据：[最终摘要](M5a_evidence/final_suite_r1/summary.json)、[节点同一性](M5a_evidence/node_identity_audit.json)、[静态日志](M5a_evidence/final_suite_r1/exact_construction.txt)。Python 3.12.10、pytest 9.0.3、Windows 11；环境详情见 [runtime_environment.json](M5a_evidence/runtime_environment.json)。

实际执行导出 5549 个文件在执行前后均与清单逐字节相同；当前工作树 5466 个非本单生成输出的被测输入也与该导出相同，遗漏输入 0。报告/证据可在数值冻结后生成，这个排除范围显式列在 [delivery_audit.json](M5a_evidence/delivery_audit.json)，没有借此排除源码、测试、夹具、政策、README、设计或旧报告。

### 7.3 性能口径

最终 [performance.json](M5a_evidence/performance.json) 分开记录三种量：

| 量 | 基线 | 最终 | 解释 |
|---|---:|---:|---|
| 收集+四片+静态总墙钟 / 秒 | 1710.529766 | 1611.406236 | 比值 0.942051，本轮下降约5.79% |
| 全部 call 阶段累计墙钟 / 秒 | 3702.303548 | 3346.494255 | 比值0.903895；并行累计值不是实际总耗时或CPU时间 |
| 新 M5a 128项 call 累计 / 秒 | — | 11.012202 | 占基线累计call约0.2974%；尚不含新增16个既有溯源参数与共享静态政策的间接成本 |

新门按文件累计：代数0.102404、独立oracle1.967311、回放6.629170、轨迹2.313317秒；四片新增门最大累计为4.193697秒。全时程997.85秒回放不在常规pytest路径，采用冻结证据及小样本真实重执行。

这轮实测未出现5%耗时回归，但**不把“新门占比0.30%”偷换成“全套回归≤5%已认证”**。共享机器同时有另一工单，基线与最终各一轮不构成受控性能实验；`controlled_environment=false`。约5%目标的强验收仍需独占/稳定负载、多轮对照，因此留在PARTIAL而不是用一次更快数字消项。

### 7.4 审阅边界

[理论专题复核](M5a_evidence/theory_review.md)、[静态专题复核](M5a_evidence/static_review.md)、[交付独立复核](M5a_evidence/delivery_review.md) 各自声明审阅范围、作者关系和限制。它们不是六路完整 G6，不以专题“未发现”替代里程碑退出条件。

执行节点完整性以收集/派发/实际 call 的多重集合逐项比较，并检查 setup/call/teardown 全 passed、0 skip；大于 1 MB 的节点清单和执行记录均在忽略路径，不纳入提交。最终字节审计核实际执行副本及当前所有被测输入，排除范围仅本单生成的证据/报告，详见 [delivery_audit.json](M5a_evidence/delivery_audit.json)。

## 8. 可复跑命令与失败处置

以下命令只写本树，新批次使用新名字；不要拼接或续用中断批次。先在本工作树运行：

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONIOENCODING='utf-8'
$env:TEMP='D:/eab-wt/cx-e2/reports/codex/M5a_evidence/tmp/manual'
$env:TMP=$env:TEMP
New-Item -ItemType Directory -Force -Path $env:TEMP | Out-Null
python -X utf8 tools/m5a_run_gates.py --name owner_review_r1
python -X utf8 tools/m5a_finalize_evidence.py --suite owner_review_r1 --baseline baseline_suite_r1
python -X utf8 tools/m5a_se2_replay.py reproduce --examples D:/eab-wt/cx-e2/reports/codex/M5a_evidence/minimal_examples.json --out D:/eab-wt/cx-e2/reports/codex/M5a_evidence/tmp/manual/examples.json
```

runner 内部统一给 pytest 加 `-p no:cacheprovider` 与显式 `--basetemp`。全时程重跑命令（沿用上面环境，输出使用一个不存在的新目录）：

```powershell
python -X utf8 tools/m5a_se2_replay.py batch --mode full --jobs 4 --out D:/eab-wt/cx-e2/reports/codex/M5a_evidence/tmp/replay/full_owner_r1
```

其**必要本地输入不由 `--help` 自动下载或恢复**：

1. `reports/codex/M5a_evidence/tmp/replay/inputs/<case>/{shadow.jsonl,geom.csv}`。只读原件逐例路径及哈希由 [M4c 运动学审计](M4c_evidence/kinematics_audit.json) 的 `cases[].files` 给出；原源清单来自 `D:/eab-wt/m02-int/reports/codex/M4b_evidence/replay_sources_final.json`，实际两文件通常在 `D:/bdda-wt/shadow/bdda2/build/m4b/modified_runs/<id>/shadow/`。需要时仅复制到本树 tmp 并核哈希，绝不在源树运行程序。
2. `reports/codex/M4c_evidence/full_replay_r4/<case>/{audit.json,normalized.jsonl.gz}`，为本树被忽略的历史弦结果。不得覆盖当前完整历史；没有证据证明另一只读树保有同路径备份，不能假设它随提交传递。在新克隆缺失该组材料时，要先使用本地工具重算 M4c：

```powershell
# 示意单例；仅用于尚不存在目标材料的新树，15例分别运行。
python -X utf8 tools/m4c_motion_replay.py reports/codex/M5a_evidence/tmp/replay/inputs/bb52/shadow.jsonl --geometry-csv reports/codex/M5a_evidence/tmp/replay/inputs/bb52/geom.csv --case bb52 --pd-edge-limit 0 --out D:/eab-wt/cx-e2/reports/codex/M4c_evidence/full_replay_r4/bb52
```

M5a 逐文件核 M4c 归一化哈希及原始两端数据哈希；来源变化不能悄悄复用旧摘要。完整大材料不入库；日常 450 帧冻结门与三个最小例无需外树或求解器即可运行。全时程重新生成仍以原始快照可用为前提。

已记录的早期失败：缓存遮住内存变异、PS5 中文管道 needle 断言、PS5 重定向 UTF-16、静态新增站点默认拒绝、M4c 重验证相对输出路径发布失败。对应分别修复后完整重跑；无隐藏拼接。旧 M4c 发布失败批次明确作废，后用绝对路径重跑完整 450 帧。[WORK_LOG.md](M5a_evidence/WORK_LOG.md) 和 [encoding_normalization.json](M5a_evidence/encoding_normalization.json) 保留证据。

## 9. 遗留与到 SE(3) 还差什么

1. δ>0 首盖不变的一般充分条件证书未建立；需要整段误差界而不是端点阈值。
2. 未恢复 b-DDA 真实步内运动；不能由 sin/cos 有限端点更新推断本单连续插值。
3. 大于 90°、跨半角 chart、多圈运动未支持；材料多环未支持（E 洞已在退化门覆盖）。这些合法但不在支持域的需求明确报错，不静默近似。
4. 未构造全 SE(2) 障碍边界安排、旋转最短逃逸及其全局证书。
5. SE(3) 仍需旋转多 chart/四元数合同、双体 VF/FV/EE 完备事件、共面/共线退化分支、次数/复杂度证明、独立三维 oracle 与拟合残差信任合同。二维五次上界不能直接搬到三维。
6. 受控约 5% 性能验收、提交/合并后新鲜 Git checkout 与作者独立六路 G6 尚未完成；当前改动不宣称通过里程碑退出门。

M5a_PARTIAL：δ>0首盖稳定性证书；大角度/跨chart及材料多环；受控5%性能验收；提交后新鲜checkout与完整六路G6。
