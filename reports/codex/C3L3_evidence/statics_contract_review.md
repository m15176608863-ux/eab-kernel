# C3-L3 静力装配合同与具名门素材

## 范围与证据边界

本文是 WO-C3L3 的**实现者自查及报告素材**，不是 Claude 安排的独立对抗核查，也不宣称里程碑已获核查通过。只读核对正式 `statics.hpp`、`statics.cpp`、`test_statics.cpp` 与已有正式构建日志；本次未改源码、未另跑 Python 全档。

依据为 [eab2 设计](../../../docs/eab2_design.md) §4.5、§4.6.1–2、§5.2。当前设计文件 SHA-256 与工单一致：`6d174ecc4f1326d5bac21c56c8d333485fb50bbaef3a12150e94eaff14cb4dac`。Python 对应裁判为 [statics.py](../../../src/eab/kernel2d/statics.py) 的 `_project`、`build_limit_problem2`、`solve_limit_problem2`、`limit_load_ideal_exact_2d`。

正式源码核对指纹：

| 文件 | SHA-256 |
|---|---|
| [statics.hpp](../../../eab2/src/statics.hpp) | `bafd34e8f8df4d9b0e1745c6cf890f2be3ae1b0b9363e9d9ea6a17385aa8a859` |
| [statics.cpp](../../../eab2/src/statics.cpp) | `28604091f7908e97bc6fb4103a706641330f49c716743a381a881bc8f08ec8c4` |
| [test_statics.cpp](../../../eab2/tests/test_statics.cpp) | `6eabf2f2a7194e40b3783e407e8cc2f21015dfd57243b5159e4be2e86bfea59f` |

正式单测原始末行，见 [单测日志](eab2_test_statics.log)：

```text
C3L3_STATICS_OK checks=3916
```

`checks=3916` 是逐项断言执行次数，不是独立物理算例数量。[C++ 构建/测试摘要](cpp_tests.json) 另记录 `100% tests passed, 0 tests failed out of 12`。本文件不替代权威差分结果、收尾快档/全档、规模报告或最终验收结论。

## 一、装配合同与实现逐项对应

设接触点为 `p`，原始精确切向量为 `T`，`N=(-T_y,T_x)` 指向接触记录的受力体 `a`。本层求解标准形：

```text
max alpha
A x = b, x >= 0
A = [G, projected_live], b = -projected_dead
c = (0, ..., 0, 1)
```

`x` 的末分量是非负活载系数 `alpha`；每条保留接触依次占 `g−`、`g+` 两列。

| 合同 | 正式实现定位 | 守护具名门与核验要点 |
|---|---|---|
| 只消费 L1 保留接触，不从所有原始 VV 来源额外造力列 | `build_limit_problem2`，`statics.cpp:51`，遍历 `contacts.constraints`；`solve_limit_problem2` 检查 `REDUNDANT_PROVED` 并报 `true_vv_excluded_from_statics` | `matrix_and_certificates`：冗余角点体对无力约束，列数恰为 `2*constraints.size()+1`，排力适用条件明确输出。固定体之间的正常接触仍可有全零力列，测试不将其误判为 VV 造力 |
| 未归一化精确生成元 `g±=N±mu*T`，不得把向量长度归一化 | `build_limit_problem2` 接触循环，`sign` 顺序 `{-1,1}` | `matrix_and_certificates`：高度为 2 的界面核 `N_x=2`、两摩擦分量 `+1/2,-1/2`，不会被单位法向伪装通过 |
| `a` 受 `+g`、`b` 受 `-g` | 同一循环中 `sense=(i==a)-(i==b)` | `matrix_and_certificates`：共享冻结参考点的相邻体三行列值逐项为相反数；`g5_closed_form_and_masks` 再核实际链条力平衡 |
| 力矩先按冻结参考点 `o` 计算原始精确 `(p-o)×g` | `build_limit_problem2` 中精确 `arm=sub(point,reference_point)`、`cross(arm,force)` | `matrix_and_certificates`：非原点参考点的活载力矩、接触反力矩；`g5_closed_form_and_masks`：三个参考点重参数化后同一物理问题结果不变 |
| DOF 约束施加在独立物理锚点 `a0`，不是代数参考点 | `project`，`statics.cpp:8`：`M_anchor=M_o-(a0-o)×F`，之后按 `dof_mask` 只取自由行；固定体无行 | `g5_closed_form_and_masks`：端板面中点锚定下放开竖向得到 `2/3`、放开转动得到 `4/3`；`rigid_units_and_anchor_translation`：物理锚点随几何整体平移保持 `4/3` |
| 恒载与活载经过相同锚点投影；恒载取负进 `b`，活载进末列 | `build_limit_problem2` 最后一段 `project(live/dead)`；`c.back()=1` | `matrix_and_certificates`：核中块竖向活载 `-1` 及关于 `o=(5/8,-3/8)` 的力矩 `-7/8`；G5 恒载压力闭式及端板反例同时守护符号与投影 |
| 无解析或不完整接触不成为“零承载力” | `limit_load_ideal_exact_2d(ContactSet2,...)`，`statics.cpp:159` | `matrix_and_certificates`：`MECHANICAL_UNRESOLVED` 保持数学状态且无 `problem/exact_value`；完整性未知为 `UNPROVED`；负摩擦与荷载体数不匹配为 `INVALID_INPUT` |
| 复用 C3-L1 优化核，不重写 LP | `solve_limit_problem2`，`statics.cpp:124`，调用 `opt::maximize` 和原始模型 `opt::verify_certificate` | `matrix_and_certificates`：直接标准形检验 OPTIMAL/INFEASIBLE/UNBOUNDED 所需字段；全部几何算例调用测试辅助函数 `verify`，独立逐分量重算矩阵等式/不等式 |
| 公共记录保留原始精确模型、行列映射、冻结参考点和锚点 | `LimitProblem2`、`LimitResult2`，`statics.hpp:26/38`；三个 `export_exact`，`statics.cpp:192/198/205` | `matrix_and_certificates` 检查精确问题导出存在；跨语言逐字段及非唯一证书核验以另行权威 harness 为准，本文不虚报其运行结果 |

### 力矩中的微分边界

本 L3 实现使用原始精确数据计算力矩，关于 `mu` 的列满足精确仿射关系 `g±(mu)=N±mu*T`，其力矩系数也由同一精确叉积得到，供 critical 临界基多项式构造使用。它**没有**新增几何/荷载任意参数的 L4 种子或 `dA` API；不得把此处结果描述成已实现完整 `d[(p-o)×g]` 参数敏感性系统。工单的原始精确力矩要求由上述装配与门守护，L4 全参数导数仍是后续范围。

### 三种精确结果的语义

测试辅助函数 `verify` 只用模型 `A,b,c` 和导出证书计算有理等式/不等式，不调用 simplex 或生产证书检验器作为测试 oracle：

- **OPTIMAL**：`x>=0, A*x=b, A^T*y>=c, c^T*x=b^T*y=exact_value`。`mechanism=exact_y` 是按自由 DOF 排列的锚点速度坐标；其力列非负与末列条件给出 `G^T*y>=0`、`live^T*y>=1`，所以机构驱动至少为 1。**不是 `-y`**。
- **INFEASIBLE**：`A^T*farkas<=0, b^T*farkas=1`。优化核返回的正归一化量被本层精确归一到 1，不从显示浮点数恢复。
- **UNBOUNDED**：分别保留 `x0>=0, A*x0=b` 和 `r>=0, A*r=0, c^T*r=r_alpha=1`。这既不是有限承载力，也不是几何锁定证书。可选自应力未实现、未作为替代见证输出。

列权重、对偶和机构通常不唯一；只应比较具名唯一字段并按上述数学定义检验见证，不能要求与 Python 逐字相同。

## 二、G5 回归 (d)、端板反例与闭式

具名门为 `g5_closed_form_and_masks`（`test_statics.cpp:101`）。主数值 oracle 是端点力/力矩平衡导出的闭式；测试还手写 G5 端点记录，以隔离静力层，并与正式 L1 接触装配路径分别求解。手写端点本身不构成生产接触完整性证明。

限定条件：等高直界面矩形链、左右结构与中块受荷位置满足设计，右端板只放开 `x`，锚点为端板受力面中点，无自重，压力 `P` 为死荷载。此时：

```text
F = min(2*mu*P, 4*P*h/(L-b))
```

当前具名门直接使用等宽链 `L=n,b=1`，覆盖下表。任意改动端板掩码、荷载位置或宽度关系不能继续无条件套此式。

| n | mu | h | P | 两路径共同精确结果 |
|---:|---:|---:|---:|---:|
| 3 | 0 | 1 | 1 | 0，C3-L1 遗留回归 (d) 第一项 |
| 3 | 1/4 | 1 | 1 | 1/2，回归 (d) 第二项 |
| 3 | 2 | 1 | 1 | 2 |
| 5 | 2 | 1 | 1 | 1 |
| 7 | 2 | 1 | 1 | 2/3 |
| 3 | 3/8 | 3/2 | 5/4 | 15/16 |

在 `n=3,h=P=1,mu=2` 且端板锚点 `(3,1/2)` 下：

| 端板 mask | 结果 | 解释 |
|---|---:|---|
| `(1,0,0)` | 2 | 原 G5 闭式边界 |
| `(1,1,0)` | 2/3 | 放开竖向，不能套原闭式 |
| `(1,0,1)` | 4/3 | 绕面中点放开转动，不能把转轴偷换为参考点 |

另以物理锚点 `(0,0)`、mask `(1,0,1)` 核验三个代数参考点 `(0,0)`、`(5/8,-3/8)`、`(131072,-1024)`；接触和荷载力矩同步重参数化后均为 `1/3`。这里**参考点变换不等于移动物理支承**；单独移动锚点本来可以改变物理约束与承载力。

## 三、P1 元门与有效蕴含

### 1. 刚体/单位尺度与锚点

`rigid_units_and_anchor_translation`（`test_statics.cpp:217`）对非原点矩形/水平支承的摩擦受限算例施加 4 个精确旋转、3 个正尺度和 3 个平移量，共 36 组，均保持无量纲活载系数 `1/4`，并逐组核验精确证书。尺度 `{1/1024,1,16}` 与大坐标同时出现；平移 x 分量 `{0,1000,100000}`，y 分量为 `-3*x`。这里平移向量的模长不等于 x 分量。

旋转包括单位阵、90 度与有理 `(cos,sin)=(3/5,4/5),(-5/13,12/13)`。后两者属于**内部精确有理 C++ 路径**，不能冒充有限 binary64 输入 ABI 能无损表达任意旋转；正式 binary64 端到端元门应以权威 harness 的实际输入/结果为准。一般旋转测试选全自由可动体，避免将全局 x/y 掩码错误解释为可任意旋转的约束轴；端板另测物理锚点随几何平移。

本门只覆盖本静力 API 的承载因子与证书，不独自证明任意输入不变性，也不声称已覆盖 critical 的阈值元门或接触标签置换全合同。

### 2. 有效蕴含一：单体一阶零锥 ⇒ profile1 无界

具名门：`valid_implications_and_reverse_counterexample`（`test_statics.cpp:235`）。对 cage 的 L1 零锥证书，逐项核对：

```text
K^T lambda_(k,+) = +e_k, K^T lambda_(k,-) = -e_k, lambda >= 0
(g_minus + g_plus)/2 = N
```

其中 `K` 是保留接触法向在同一锚点自由速度坐标上的约束矩阵。任意目标 wrench `w` 可写成有符号坐标基的非负组合；把每个法向权重在两摩擦生成元间等分，摩擦项精确抵消。于是 `b` 给出可行点的接触部分，`-live` 给出归一化改进射线的接触部分。

测试没有只检查 solver 的 `UNBOUNDED` 标签，而是从 L1 的 `±e_k` 组合**另行构造** `x0` 与 `r`，再核 `A*x0=b`、`A*r=0`、`r_alpha=1`，取 `mu={0,1/4,2}` 及非对称混合恒载/活载。等分抵消是一般代数理由；有限参数门检验其实现，不把三次采样说成全输入域证明。条件限于同一已解析接触集、同一自由坐标及 profile1 的无限抗压无黏聚锥。

### 3. 有效蕴含二：mu=0、零恒载下，单体零锥 ⇔ 六方向无界

同一具名门在 `free/plane/seam/cage` 四种实际几何上，每种测试三坐标的正负六个活载方向，检查“六项全 UNBOUNDED”与 L1 `cone_is_zero` 一致。

数学理由：当 `mu=0`，反力锥由法向 wrench 生成；同时包含 `±e_k` 等价于反力锥铺满三维 wrench 空间，其极锥仅为 `{0}`。零恒载保证 `x0=0` 可行；每个六向单位活载的归一化射线提供相应有符号 wrench 表示。这是同一有限维锥的代数对应，不是把某一次无界当作锁定。

### 4. 有效蕴含三：活载只作用于体 i 时，多体无界 ⇒ 单体无界

同一具名门先检实际多体模型的 `x0/r`，再固定除目标体以外的体，重装接触并核单体证书。覆盖固定外端直链及 G1 三取向：`koureas,mu=0`；`unreversed,mu=1/2`；`reverse_i1,mu=1/4`。

理由：固定其余体后，只保留目标体需要满足的平衡与同样的目标体荷载，原有可行点/改进射线的目标体作用力构成可行见证；不能由此逆推出多体平衡也成立。测试限于上述已解析、重装前后符合 profile1 的几何，不泛化到未解析 VV、改变接触骨架或不同力学模型。

### 5. 必须保留的反向门

G5 `n=3,mu=1/4,h=P=1` 的实际多体链承载力为 `1/2`；固定中块之外的所有体后，中块的 L3 查询为 UNBOUNDED，而其 L1 一阶锥仍非零。具名断言为：

```text
G5 middle body rejects single-to-multi converse
single unbounded is not a first-order lock
```

因此既不能使用“单体无界 ⇒ 多体无界”，也不能使用“无界 ⇒ 单体几何锁定”。

## 四、门的有效性与尚未由本文完成的事项

[可重跑源码 mutation 工具](../../../tools/eab2_c3l3_statics_mutations.py) 将缺陷注入静力装配实现内部，不向结果尾部追加假数据。已执行的三个缺陷分别忽略物理锚点、把两摩擦生成元同号化、把作用反作用同号化；前者由端板反例断言拒绝，后两者由 G5 闭式/回归 (d) 断言拒绝。脚本要求每次精确匹配指定的失败断言，不接受任意异常或不相关红门充数。原始实施与母版 hash、替换次数及日志由 mutation 权威摘要/主报告归档，本文不重复存放其全量产物。

剩余边界：

1. 本文不宣布差分、critical 开闭阈或 P2 规模测量完成；以各自权威日志及 `C3L3_report.md` 为准。
2. 本文不是所有者安排的新鲜 worktree/克隆验证，不把当前工作树构建当成该项完成。
3. 本文不是独立对抗核查，测试全绿也不能替代该核查。
4. profile1 的关联流动结果相对非关联库仑模型是**不安全侧承载力上界模型**；不得标为工程安全承载力。
5. 继承的 `opt` 有单独的确定性 pivot 上限；几何 `max_work_units` 不代表已对 LP 每次有理算术逐项计数，资源统计不得混称。

STATICS_CONTRACT_REVIEW_COMPLETE_IMPLEMENTER_SELFCHECK_ONLY
