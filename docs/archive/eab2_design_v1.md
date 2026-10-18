# eab2：C++ 接触引擎设计

> WO-C1 · 2026-10-19 · 中文设计稿，供所有者 / Claude 决策。  
> 基线：`D:/eab-wt/cx-c2`，`eab2-design @ 1ce9a91760e22cab7e471e76c39dcc2b786eb6ab`，开始时干净。  
> **本稿不是实现完成或性能达标声明。** Python `src/eab` 是参照实现兼裁判；发生差异，先按 C++ 缺陷处理。本文的新接口、构建目标、测试名和工期均为设计，除明确标为“现有”或“本次实测”的内容外，不表示已经存在。

## 阅读导航与决策摘要

1. [范围、理论合同与移植顺序](#s1)
2. [数值体系：过滤、精确构造与实代数数](#s2)
3. [编译与浮点合同](#s3)
4. [可微层：“划”与“片”分离](#s4)
5. [API、分层与数据模型](#s5)
6. [性能目标与测量计划](#s6)
7. [Python 裁判与差分测试](#s7)
8. [里程碑、验收与工作量](#s8)
9. [五大风险与待决问题](#s9)
10. [来源、术语和验收索引](#sources)

**五条推荐：**

- 先交二维可复用引擎，不交新的 DDA 求解器。v0 覆盖一般凹简单环的 E/O、平移与端点弦查询；v1 交 TIA 二维承载力和参数敏感性；v2 才交五 / 六次代数事件及选定稳健证书。
- 用 **Boost.Multiprecision `cpp_int` + 小型有理数封装** 作共同精确后端；浮点仅过滤 / 提名，精确层决定标签、时间顺序、LP 证书；所有约定为精确构造的显示值 RN-even 一次舍入。
- **精确标签 + 连续表达式的模板求值**，而不是把 `Fraction` 机械替换成 `Dual`。正演原值由精确路径负责；导数标明连续模型、分支和质量，不能伪称量化程序处处可微。
- 仅提供同工具链 C++ 门面及稳定 C ABI；差分通过 Python 标准库 `ctypes`，不引入 pybind。域词汇只在 L5，姊妹仓库零代码依赖。
- 主保证是 Python 差分及少量元门；**不移植 AST 构造门、变异充分性框架、源码哈希绊线**。小型数值反例、错误编译负例和对抗审查保留，但不再长成第二个产品。

### 本单边界、成功标准及回退锚

允许落盘：本文、[一页报告](../reports/codex/C1_report.md)，以及不入库的 `scratch_eab2/` 测量 / 验证材料；不改 `src/`、`tests/`、`tools/`，不改任何姊妹树，不执行 Git 写操作。本次未安装库、未编译产品、未接入宿主。起始两个目标文档均不存在，回退锚是上述基线及原文件保持不变；不自动执行恢复 / 删除。

成功标准：九项问题均有建议、备选和拒绝边界；函数 / 语料可追溯；实测与目标分开；理论按指定原文对照归属；中文 UTF-8 无 BOM；仅允许路径变化；执行现有 `python -m pytest -q` 并如实记录结果。禁止新 worktree，所以本单测试不构成 AGENTS 纪律 D/G6 的产品里程碑退出。

<a id="s1"></a>
## 1. 范围、理论合同与移植顺序

### 1.1 产品定位与分层基线

eab2 是可以被不同宿主调用的**几何 / 接触 / 极限承载引擎**。第一个外域是 TIA 二维：L1 完整接触约束 → L3 承载力 LP → L4 界面参数敏感性。DDA 是第一个只读对账适配器，不是内核命名空间的中心，也不决定 TIA 的数据模型。

按 WO-H1 搬家后的职责设计：`predicates / construction / numeric_domain / rational3 / dual / lp / margin / limit / limit_multi / oracle_construction / kernel2d / kernel3d` 属于通用范围；legacy 槽位、DDA 锚定路径、TIA 逃逸语义属于 `adapters/`。其中 `oracle_construction` 是参照侧独立核验资产，**不因此复制成 C++ 生产依赖**。本树仍有搬家前路径；下表明确现有来源和目标职责，不假称 H1 已合并。

不做：DDA 时间积分 / 开闭迭代 / 弹簧装配重写、宿主接触切换、接触力唯一性承诺、动力学或工程标定、GPU、一般曲面 CAD、完整 SE(2)/SE(3) 配置障碍。外部旧设计中的“直接复制 bdda2 types.hpp”“首次实现”等叙述不沿用；本稿以本工单和原文对照为准，不回写旧正本。[本地设计源 S1、S2](#sources)

### 1.2 必须先固定的集合与状态

采用位移坐标 `t`，A 动、B 固定：

```text
E = { t : (A+t) ∩ B ≠ ∅ } = B−A                 闭障碍
O = { t : int(A+t) ∩ int(B) ≠ ∅ }                开贯入集
body_state    = OUTSIDE / CONTACT / OVERLAP       E外 / E\O / O
topology_state= OUTSIDE / BOUNDARY / INTERIOR      E外 / ∂E / int E
```

原文参考点坐标的 `E(A,B)=B−A+a0` 与此只是坐标变换，API 必须说明使用哪一种。正则闭简单环域中 `closure(O)=E`，但 `O` 可严格小于 `int E`：接触内缝 / 孤立紧配点可能处于 `int E`。**不准用一个 inside 枚举同时代表两个三态。**

输入 v0 为单个无洞简单环：有限 binary64 顶点，至少三点，无零长边、无回折、自交或零面积；允许平直顶点、平行、共线。环可 CW/CCW，规范化后保留输入 ID 映射；不擅自删平直顶点。A/B 本身不支持带洞环不等于 E 不能有洞。多环实体、孔洞输入和不连通实体另立合同，不借一个 `ring_offsets` 字段暗中开放。

### 1.3 理论归属及三个不可混淆的查询

| 内容 | 归属 / 设计口径 |
|---|---|
| E、距离定理、凸性、平移不变性 | 石根华原文及既有 Minkowski / 配置障碍理论，不写本项目首创 |
| 二维有效盖弱覆盖 T2a，`∂E ⊂ ∪C ⊂ E` | Shi 2015 §7–8、2021 §6.1 已有；本项目补全输入假设、平直 / 共线 / VV 闭包及零容差实现 |
| 凹体 cutting 得精确 ∂E 的 T2；T2b 接触骨架 | 原文只陈述 cutting；项目提供严格化算法 / 证明。不能把未裁剪局部盖称为完整外边界 |
| 首入与最短出口概念 | 原文已有；计算算法、并列报告协议是实现选择，不把“选唯一赢家”归于原文 |
| O、`E=closure(O)` 的集合化、rho | 原文没有这一计算体系；不得把 `int E ⇔ 贯入` 归于石根华 |
| SE(2)、仿射一步事件、R1/R2/C1 | 越出原文平移框架；本项目延伸，不称原文算法 |

严格按 [指定原文对照 S1](#sources) 的归属；本单读取的是对照，不冒称重新核读两篇全文。

1. **首入**：从 E 外沿给定路径首次触到闭 E，包含瞬时切触，输出全部并列特征。初态接触 / 贯入单独报告，不伪称它们是分离后的首次碰撞。现有 `GlobalEntrance2.first_entrance()` 对初始 E 返回 0，新高层包装保留这个低层值但添加初态标签。
2. **PD_closed**：int E 中到 ∂E 的距离，即完全脱离闭 E 位移长度的下确界；边界见证仍接触，不是已严格分离。现有 `shortest_exit` 实现此量；它不是 O 的恢复距离，也不是沿一步轨迹的出口时刻。
3. **rho**：O 内到 `∂O=E\O` 的距离，O 外为 0；可终止于内部接触缝或孤立点，不能只扫 ∂E。本稿暂名 `overlap_recovery_distance`，须先补 Python 裁判。

### 1.4 v0 / v1 / v2 函数级清单

下列版本是能力版本，不等同现有 Python 里程碑编号。“裁判先补”指需要另单修改 Python，本单不实施。内部 helper 不要求逐函数同名翻译，公开语义与精确证书才是移植单位。

| 版本 / 优先 | Python 模块与函数（当前树） | 交付能力与取舍 |
|---|---|---|
| v0.0 / C0 | `numeric_domain.exact_input/check_input/check_mu/binary64_argument`；`predicates.cross2_sign/dot2_sign`；`construction.scalar_rational/ratio_rational/vector_rational/sqrt_rational/norm_rational/unit_rational/normalized_difference_rational` | 有限 binary64 全范围精确解码、命名失败、二维谓词和一次舍入；不把工程显示域误当谓词域 |
| v0.0 / C0 | `dual` 的 `Dual/val/is_exact_zero/sin/cos/sqrt/atan2` 合同 | 先建立独立 `Dual<W>` 与值 / 标签 / jet 接缝，防止几何全写死在有理数；不宣称此时已交完整梯度 |
| v0.1 / C1 | `kernel2d.exact` 的 `signed_area2/convexity_violation/entrance_block_exact/membership_exact/vertex_side_exact/ve_side_exact/ev_side_exact/polygons_overlap_exact/entrance_membership_exact`；`geom` 中必要环 / 向量门面 | 凸快路及一般凹环的基本精确语义；旧近似窗口函数不一股脑移植 |
| v0.1 / C1 | `covers.ve_cover/ev_cover/vv_cover/enumerate_covers`；`global_entrance.GlobalEntrance2` 的 `membership/topology/cell_edges/side_probes/clipped_covers/boundary/subdivision`、`global_entrance()` | 一般凹简单环 T1/T2/T2a/T2b；同时保留 E 外边界和完整 E\O，输出几何与来源标签 |
| v0.2 / C2 | `GlobalEntrance2.ray_intervals/first_entrance/distance_to_e/shortest_exit`；`entrance.first_entrance`；`motion_exit.shortest_exit_fast` | T3 平移首入、全并列最短 PD_closed；先正确基线，再加经过差分的快路。`entrance.shortest_exit` 仅为局部最浅盖，不移入全局 PD API |
| v0.2 / C2 | **Python 现无公开函数**：建议 `overlap_recovery_distance`、`translation_lock_certificate` | rho 与原文 §3.10 平移锁定：Python 裁判规格 / 实现 / 反例先行，C++ 随后。未补齐不得把完整 v0 标成完成 |
| v0.2 / C2 | `motion.QuadraticTime/MotionEntrance2/motion_first_entrance` | M4c/P1 通用顶点线性弦的二次事件，整窗域认证；它不是完整 M5d |
| v1 / C3 | `lp.solve/maximize`（含 exact 数据与三类证书）；`limit.wrench/friction_generators/LimitContact/contacts_from_covers/limit_load/check_duality/mechanism_is_admissible` | 二维极限分析；浮点候选 + 精确核验，派生力矩也精确。保留摩擦生成线、黏聚和可分辨性口径；`contacts_from_covers` 仅作旧接口兼容，不充当完整界面装配裁判 |
| v1 / C3 | `limit_multi.LimitBody/BodyContact/contacts_from_covers_multi/limit_load_multi/check_duality_multi/mechanism_is_admissible_multi`，只启用 `dim=2` | TIA 多体 L3，不先拖入三维摩擦锥离散问题 |
| v1 / C3 | `dual` + 几何连续表达式；二维 `margin` 所需冻结接触 / 间隙合同；**新增 LP 参数敏感性裁判** | L4：μ、接触参数、块体倾角的梯度 / 方向导数和并列状态；`margin.py` 当前偏三维，不以文件名声称已存在二维直接对应 API |
| v1 / C3-D | `adapters/bdda2d.py` 读取 / 映射，H1 新适配层；M4c 回放协议 | DDA 15 例 P1 与静态出口离线对账；不搬 df04–df25，不改 bdda2 主线 |
| v2 / C4 | `algebraic.p_gcd/RealAlgebraic/roots_interval/sign_at`；`construction.scalar_algebraic`；`se2.SE2Motion/rotate_rational/se2_slice/se2_first_entrance` | M5a 有理半角 SE(2) 路径，至多五次；不是任意 sin(ωt) 轨迹 |
| v2 / C4 | H1 后 `adapters/bdda2d_motion.py` 的 `area_centroid/rational_half_angle/DDAAnchoredMotion/dda_motion_from_z/p2_p3_bound/projected_sweep/dda_first_entrance/dda_paths` | M5b/P2 六次代数事件与 M5d 全名义对照；DDA 参数解释留 L5，通用多项式符号操作留内核 |
| v2 可选 / C4-R | `model_robustness.separation_certificate/single_cover_certificate/swept_axis_bounds`（R1/R2）；`m5d_exit_certificate.exit_order_certificate`（稳健 C1） | 有界域内保守稳健证书。C1 仅严格凸、跨环非平行、唯一静态出口。R3 放后续研究，不用少量认证冒充全域 |
| 暂不移植 / 独立 v3 | `rational3`、`kernel3d`、三维 `margin/limit`、H1 `adapters/tia3d.py`、三维 DDA 适配 | 三维从凸域另开项目，凹体 / BSP / T3L 退化缺口先研究；v0 可预留 `orient3d` 单元数值门，但不宣称三维引擎 |

`kernel2d/affine_motion.py::fit_affine/AffineFit` 是端点拟合诊断；H1 的 `DDAAffineMotion` 去 `adapters/bdda2d_affine.py`。**一般仿射首入 Python 本身尚无完整实现**，不把 M5b 的特定锚定 P2 误写成任意仿射支持。

v1 的“完整”限定为 **L1 几何接触集合完整**；L3 必须另声明机械接触模态。默认首个 TIA 机械 profile 见 §8.4：已选定直边 / 唯一法向接触；VV/凹角互斥模态未解析时整次力学链明确未证，不能只略过这些盖然后称完整承载力。

### 1.5 E 构造方案：先可对账，再局部化

| 备选 | 优点 | 主要代价 / 拒绝理由 |
|---|---|---|
| A：凸分解 → 凸胞差 → 并与标签骨架（推荐基线） | 对 E/O 同时有直接集合解释，能保留内缝；已有 Python 裁判 | 最坏组合爆炸，需精确剪枝、lazy 查询 |
| B：局部有效盖 + cutting / reduced convolution | 候选可能更少，贴近局部接触 | 必须保留 T2a 弱覆盖和 T2 完整裁剪；仅有效盖不足以生成全部 E\O；不先替代裁判路线 |
| C：全用 CGAL arrangement / Minkowski 包 | 丰富算法与退化处理 | 引入大依赖、许可证及 E/O 语义改装成本；不默认选 |
| D：凸包 / GJK / SAT 代替凹 E | 凸问题快 | 一般凹与接触内缝语义错误，不是同等备选 |

推荐用 A，两个显式选项对应现有 `merge_convex=True`、`compact_subdivision=True`。原体凸合并须精确证明并集等于凸包，不能把重叠配置胞直接按面积相加。T2b 对所有原始 VE/EV 线段完全切分，**不先以有效法锥筛掉内缝**；逐个保留 state=CONTACT 的开段与顶点，包括孤立零维点。人造竖直剖分可不同，实际集合、接触标签与精确查询必须相同。

默认查询按需建胞、AABB 和接触骨架；请求导出完整剖分才物化它。边界只能由精确相交 / 两侧占据决定；包围盒剪枝含等号，用精确界或保证向外的浮点界。缓存按几何内容 / 版本和参数键控，不以对象地址作为语义；局部查询只能在精确排除其余区域后代替全局扫描。

### 1.6 平移锁定证书：严格定义，不借用 DDA “LOCKED”

单对推荐结果：`NOT_CONTACT / REMOVABLE_TRANSLATION / LOCKED_TRANSLATION / UNPROVED`。只有 `body_state=CONTACT && topology_state=INTERIOR` 才签 §3.10 的锁定证书；输出接触见证、int E 证据，以及正的内球半径下界（例如小于 PD_closed 的有理半径）。`OVERLAP` 返回初态贯入，不签合法锁态。

这里“锁定”精确指**不存在任意小的严格分离平移**。它不自动排除沿接触缝滑动的非贯入运动，不意味着无机构、刚度为正或承载力为正，更不证明转动锁定。可移除证书要给边界处通向 E 外的局部方向 / 锥见证，而非仅给一个布尔值。

固定其余块、只让块 i 平移时，以同一位移坐标构造 `E_i=∪j E_ij`、`O_i=∪j O_ij`。在“所有对都不贯入、至少一对接触”下判断 `0∈int E_i`。多个单对各自可移除仍可能由联合障碍围住：逐对 lock 做 OR/AND 都不是正确的组装体证书。20 个块的这种查询是 20 个**单动体、其余固定**证书，不是全组装体可共同运动的完备证明；后者至少还需 L3 的机构与载荷分析，完整运动锁定另题。

**排期取舍：**推荐 rho / 单对锁定纳入 v0，联合固定邻体锁定随 C3 的 TIA 输入闭合；需要先另单补 Python。若所有者不批准补裁判，v0 必须明确减项，不允许用 C++ 自己给自己当裁判。

<a id="s2"></a>
## 2. 数值体系：过滤、精确构造与实代数数

### 2.1 三条数值通道，不建“万能 Scalar”

```text
binary64 输入 bits ──无损解码──> ExactDyadic / Rational(cpp_int)
              │                     │
              └─ FloatFilter ────────┤ 不确定则精确回退
                                    ├─ 标签 / 事件 / LP 证书
                                    └─ exact recipe ──RN-even──> 显示 double
连续参数 + 已定标签 ── Eval<S> ──> 连续输出的导数（S=double 或 Dual<W>）
```

输入 double 是其**给定二进制值的精确有理数**，不是用户心中十进制实数。NaN/±inf 拒绝，−0 输入可保留原始 bits 用于溯源，但精确几何值等于 0。`ExactDyadic` 可用整数尾数与二进指数做加乘快路；除法 / 交点再进约分有理数。统一 `cpp_int`，不要为省一次分配另造有符号大整数体系。

精确谓词支持所有有限 binary64，包括次正规数和极端指数；不能套 `[2^-400,2^400]` 截断。这个工程包络仅按 Python `numeric_domain` 用在相应近似公开构造；`mu` 等参数域也按调用点复制合同。数值域错误、资源耗尽和几何不支持是不同状态。

### 2.2 谓词次数与过滤选择

次数必须注明变量：下表前半是**直接输入坐标**的多项式总次数；运动部分是**时间 s** 的次数。把两者混写会低估过滤误差。

| 谓词 / 用途 | 次数或表达式 | v0/v1 推荐；v2 扩展 |
|---|---|---|
| 坐标排序、闭 AABB | 直接比较次数 1 | 原 binary64 比较精确；构造后坐标以有理比较，不比较显示值 |
| `cross2_sign/dot2_sign` | 两个向量分量的双线性式，次数 2 | 有证明的静态前向误差界；不确定 / 溢出 / 下溢风险即整数精确 |
| `orient2d(a,b,c)`、面积、线段侧 / 原体凹凸 | 差分后行列式，次数 2；多边形面积求和次数仍 2、操作数随 n 增长 | 包含差分舍入的静态界；面积用按操作图的动态界，或直接精确 |
| 顶点锥、VE/EV 有效性、绕数 / 线段相交 | 有限个次数 1/2 的符号与开闭组合 | 复用符号 API，不以 atan2 / epsilon 判断平直或平行 |
| 交点 / 投影参数排序 | 比值的分母先定符号；两个原始叉积比的比较清分母后至多次数 4 | C0 首版直接有理交叉乘；后来可加经证明的过滤 |
| 点到原始线段距离、最短候选比较 | `cross(e,w)^2/dot(e,e)`，分子 4、分母 2；两线段距离比较清分母至多 6；端点距离 2 | 直接精确平方距离，先判投影区段；避免 sqrt 参与排序 |
| 已构造有理顶点的 arrangement、侧探针、E/O | 取决于构造链；**没有统一低次数上限** | 必须保留精确 shadow；首版直接有理，不能照搬原输入 orient2d 误差界 |
| `orient3d`（预留） | 3×3 差分行列式，次数 3 | 特定操作图静态界 + cpp_int；启用三维时另验法锥 / 共面条件 |
| 平移射线入边 | 关于时间次数 1，时间为有理数 | 精确闭区间交；单点区间保留 |
| M4c 顶点线性 P1 | 关联、投影、环域事件关于 s 至多 2 | 精确二次数，符号公式 / 有理隔离；不能用 double 求根排序 |
| M5a 有理 SE(2) | 特定半角参数化消正分母后至多 5 | v2 的平方自由多项式、Sturm、gcd 判等 |
| M5b 锚定 P2 | 消去已证明为正的因子后至多 6 | 同一六次内代数引擎；一般仿射或任意 trig 路径无此承诺 |
| R1/R2/C1 的距离 / 时间预算 | 依证明中的有理 / 多项式不等式，非统一次数 | 原式精确计算；过滤只优化，不改充分条件；输出未证不等于反证 |
| LP 可行 / 约化成本 / Farkas | 派生有理线性系统；分式次数随基规模变 | 浮点给候选，精确重建基、原始与对偶 / 射线核验；不由“足够小”签证书 |

过滤器只返回 `NEGATIVE / ZERO / POSITIVE / UNCERTAIN`；在界包含 0 时走精确回退，不能把“很小”当零。精确为零单列统计。按 `fl` 的实际运算图推导界，用向上包围误差累计；不能把 Shewchuk 某个常数直接套到不同的差分 / 归一化表达式上。[Shewchuk 原始资料](https://www.cs.cmu.edu/~quake/robust.html)

建议 v0 仅优化原始 binary64 的低阶符号，复杂构造先精确；这比第一版同时维护 expansion、有理数和代数数三个后端更可控。备选 Shewchuk 自适应扩展算术擅长低阶行列式，后续仅在剖析显示热点且错误编译 / 指数域均有门时引入；它不能替代有理交点、LP 或 Sturm。

**构造值陷阱：**`b-a` 或有理交点先 RN 再送普通 orient2d，判的是另一个几何。过滤后续精确点必须携带包含其真值的转换区间，运算传播区间；不能认证就回退。不要让 fast path 的坐标成为 exact path 的输入。

### 2.3 一次 RN-even：不依赖库的隐式转换

有理数 `x=n/d`，约定 `d>0`、符号另存。推荐在 eab2 数值边界实现下面短小、可独立差分的算法：

1. `n=0` 输出 +0；否则由整数 bit length 和精确移位比较求 `e=floor(log2(|n|/d))`。
2. 令量化指数 `k=max(e−52,−1074)`；构造 `N=|n|·2^max(−k,0)`、`D=d·2^max(k,0)`。
3. 整数 `q,r=divmod(N,D)`；当 `2r>D` 或 `2r=D 且 q 为奇数` 才令 `q+=1`。
4. 直接编码 `q·2^k` 的 IEEE 位模式；处理尾数进位、正规 / 次正规交界和指数溢出。不要用两个分别舍入的 `convert_to<double>()` 相除。
5. 真值非零却舍到零，默认命名失败；只有显式 `allow_underflow` 的证书附带显示允许 ±0 并标记。溢出到非有限按该字段合同失败；最大有限数上方仍在其舍入胞内的值可以返回最大有限值。

这避免 double rounding，也不依赖 Windows `long double` 是否扩展精度。打包用 `std::bit_cast`，位序转换在序列化层做，不能靠浮点运算环境恰好正确。

`sqrt(n/d)`：求根指数后按 `2k` 移位，`q=isqrt(floor(N/D))`；比较 `4N` 与 `D(2q+1)^2` 决定舍入，平局看 q 奇偶。单位向量第 i 分量用 `sign(v_i)*sqrt(v_i²/Σv_j²)`，**不先把 norm 舍入再除**。`c/sqrt(nn)−offset` 也要比较整个表达式与舍入中点，不能先得到两个 double 再相减。

任意本稿支持的实代数显示，通过“精确实数与有理数比较”在正 binary64 位序中定位相邻数，再比较精确中点；最多约 63 次位序搜索，必要时可用已认证近似缩短区间。区间中点自身不是答案，两个隔离区间重叠也不是根相等证明。

**逐字段范围表必须随 API 发布：**几何构造复刻 `ConstructionDomainError`；LP 现有精确结果的显示可能为 infinity，要保留 exact 证书并标 `DISPLAY_OVERFLOW`，不能把它与数学 `UNBOUNDED` 混同。不为统一风格擅改 Python 既有特殊值口径。

### 2.4 实代数数表示与操作边界

v0 支持 `RationalTime` 或 `QuadraticTime`：有理数，或首一不可约二次多项式及根分支。v2 内部升级为 `RealAlgebraic { primitive_squarefree_integer_polynomial, rational_isolating_interval, root_identity }`，保留二次快路。整数多项式系数 gcd 归一、最高项为正；平方自由化不意味着不可约。

- Sturm 精确计根与有理二分确保每个区间只含指定实根；端点恰为根须单独表示，不能把开闭约定藏起来。
- 不同多项式的根判等用 gcd，并核共同根落在两个指定隔离区间内；不同区间不能仅因同一多项式就判等。排序在排除相等后细化至不交。
- `sign_at(q, α)`：先按定义多项式约化，再用 gcd 零判 / 精确区间符号；循环必须有资源预算，超限返回 `RESOURCE_LIMIT`，不得猜符号。
- 系数序统一常数项在前；外部证书同时写次数、根定位区间、开闭端点、可选有理根。若显示值需要，仍走 RN-even 边界。
- 不开放无界一般代数表达式系统。只需有理多项式在选中根处的符号、时间比较及显示；v2 六次上限不是所有中间 gcd 系数位数上限，仍须记录最大 bit length。

次数在平方自由化**之前**检查，不能用七次可约输入绕过支持域。零多项式表示恒等约束而非“没有接触”：事件层必须处理投影不等式与窗口端点，不送普通孤立根列表后丢弃。

### 2.5 大整数 / 几何库决策

| 方案 | 许可证 / 分发注意 | Windows / MSVC | 性能与维护 | 建议 |
|---|---|---|---|---|
| 自写只头文件大整数 | 自有代码易统一许可，但借用算法 / 代码仍需出处 | 可控，跨平台细节全自担 | 进位、除法、gcd、移位、负数和溢出审计量最大；为引擎增加第二项目 | 不选；只自写薄 Rational 与 RN 边界 |
| Boost.Multiprecision `cpp_int` | Boost Software License 1.0，保留许可证 / 来源；具体分发由所有者确认 | 头文件后端，适配 C++20/MSVC，无强制 GMP DLL | 通常不及 GMP 极大整数，但接入和部署简单；先测位数分布，再考虑后端替换 | **默认推荐**；固定已测版本，可离线 vendor 所需头文件 / 许可证或指定安装包 |
| GMP + MPFR | GMP 双 LGPLv3+ / GPLv2+；MPFR LGPLv3+，静态 / 动态链接的合规义务需确认 | 官方构建路线不以原生 MSVC 为最简目标；MinGW / ABI / DLL 打包需额外工程 | GMP 大整数成熟高性能；MPFR 有正确舍入浮点，可作研究交叉核验，但不自动证明表达式一次舍入 | 仅 profiling 证明 cpp_int 是瓶颈后评估可选后端，不做 v0 必需 |
| CGAL | 组件为 GPL/LGPL 或商业许可，不能笼统称整个库宽松许可 | 有官方 Windows / CMake 路线，但依赖更多 | 强几何算法与精确内核；E/O、标签、T2b 仍需定制，模板 / 编译 / 升级成本高 | 不作默认生产依赖，可另案离线对照 |

上述技术 / 许可事实据 [Boost 后端说明](https://www.boost.org/doc/libs/latest/libs/multiprecision/doc/html/boost_multiprecision/tut/ints.html)、[BSL](https://www.boost.org/LICENSE_1_0.txt)、[GMP 许可](https://gmplib.org/manual/Copying)、[Windows 说明](https://gmplib.org/manual/Notes-for-Particular-Systems)、[MPFR 官方说明](https://mpfr.org/)、[CGAL 许可](https://www.cgal.org/license.html)与[依赖说明](https://doc.cgal.org/latest/Manual/thirdparty.html)，不是法律意见。没有安装、编译或速度实测这些候选，本表不宣称 cpp_int 已满足目标。包固定版本是可复现依赖管理，不是拿源码 hash 相等代替语义验证。

精确包装只保留所需操作、规范符号和显式转换；推荐先封装 Boost `cpp_rational`，不再自写一套通用有理算术。热点可用整数公共分母减少逐项 gcd。所有优化必须与未优化精确路径差分；拒绝“切换更快 double 模式”作为性能补救。

<a id="s3"></a>
## 3. 编译与浮点合同

### 3.1 支持矩阵与目标级选项

推荐主平台 Windows x64 / MSVC C++20，Release `/O2 /fp:precise`；同时 CI 覆盖 clang 和 gcc 的 x86-64。首版不支持 32 位 x87、非 IEEE binary64、任意用户舍入模式。ARM64 可在同样自检和语料通过后单独列入支持，不由“能编译”自动准入。

| 编译器 | 数值目标必须项 | 禁止 / 限制 |
|---|---|---|
| MSVC | `/std:c++20 /O2 /fp:precise`；关键 TU / 表达式显式 `fp_contract(off)`；探测器用支持浮点环境检查的严格设置 | 拒绝 `/fp:fast`、`/fp:contract`；不假定所有版本 precise 都默认禁止收缩；数值核心首版禁 `/GL` 跨 TU 重优化 |
| clang / clang-cl | C++20，`-fno-fast-math -ffp-contract=off` 或经核验的等价 clang-cl 选项 | 拒绝 `-ffast-math`、`-Ofast`、不安全重结合 / reciprocal / finite-only；关键目标禁 LTO |
| gcc | C++20，`-fno-fast-math -ffp-contract=off`，x86-64 SSE2 binary64 | 同上；不使用 x87 扩展寄存器；需要 32 位时必须另立 SSE2-only 支持合同 |

实现时检查**最终实际编译命令**，不能只在 CMake 默认值里搜索一次；命令行后面的选项可能覆盖前面的。宿主可用 fast-math，但谓词 / 构造 / 自检留编译好的受控目标，不在宿主头文件中内联 exact 决策。模板连续层使用公开目标传播相同选项，并对可检测的 fast 模式编译拒绝。

原因：FMA 将乘加从两次舍入变一次，原误差模型与 expansion 的 error-free transform 可能失效；重结合改变操作图；x87 的 80 位中间寄存器和 spill 引入不固定舍入；fast-math 可假设无 NaN/inf/有符号零并重排比较。`/fp:precise` 不是“所有任意设置都安全”的替代词。依据：[Microsoft /fp](https://learn.microsoft.com/en-us/cpp/build/reference/fp-specify-floating-point-behavior?view=msvc-170)、[fp_contract](https://learn.microsoft.com/en-us/cpp/preprocessor/fp-contract?view=msvc-170)、[Clang](https://clang.llvm.org/docs/UsersManual.html)、[GCC](https://gcc.gnu.org/onlinedocs/gcc/Optimize-Options.html)、[Shewchuk 对 x87 的说明](https://www.cs.cmu.edu/~quake/robust.pc.html)。

有理数到 double 用整数位打包本身不受 FMA 影响，但**过滤器不能因错误环境先放过错误符号**，故仍需整个合同。

### 3.2 失败关闭的运行时自检

API `eab2_self_test()` 在创建 context 时必跑一次，每个执行线程在数值批次入口检查环境。返回位掩码与明确原因，失败时不给几何 / LP 答案。禁止悄悄替宿主改 rounding mode 或 FTZ/DAZ。首版明确禁止同一调用期间异步修改 FP 环境。

自检由三层组成，而不是一句 `1+epsilon`：

1. **编译身份**：每个数值 TU 内置其编译器 / 版本、架构、构建模式与受控选项清单；汇总检查无缺项、无 fast 位。使用 `_M_FP_FAST`、`__FAST_MATH__` 等可用宏拒绝已知坏模式；构建器校验不可由宏充分表达的选项。manifest 是构建合同，不是源码 hash 绊线。
2. **实时 FP 环境**：`sizeof(double)=8`、radix=2、digits=53、IEEE 支持；`FE_TONEAREST`；在 x86-64 检查 MXCSR FTZ/DAZ 均关闭。用从外部 / volatile 输入装载的最小正规 / 次正规运算核渐进下溢，不让常量折叠假通过。检查有符号零、有限 / NaN 分类和精确中点 ties-to-even。
3. **与真实数值 TU 同路径探针**：有意非收缩的 `(1+2^-27)*(1-2^-27)-1` 应为 0，融合为 `−2^-54`；用同编译域 noinline 运算函数测，不能用写死 volatile 中间乘积把收缩缺陷掩盖。另测 TwoSum/TwoProduct 重构和若干近消去 orientation，与 cpp_int 结果逐项相等。检查结果由整数 bits 比较，不让被测 fast 分类函数自己证明自己。

**错误选项构建验收：**测试专用构建覆盖 `/fp:fast`、`/fp:contract`、`-ffast-math`、`-ffp-contract=fast`、FTZ、DAZ、非最近舍入以及不支持的 x87。正常构建应在配置 / 编译阶段拒绝；为了测试自检，可仅在测试 harness 允许生成带 `unsupported_build=true` 的坏库，其创建 context 必须返回 `EAB2_FP_CONTRACT`。运行时环境篡改也必须失败。坏编译样本不能作为可发布库。

**可证明边界：**有限算术探针无法识别所有可能的编译选项 / 优化器错误，尤其某个坏选项在选中样本上恰好不改变结果。因此“错误选项库必失败”限定为**受控构建通道及上述负例矩阵**，由编译身份与运行探针共同兑现。若任意手工编译、伪造身份也必须保证失败，这个要求不能仅靠运行时自检实现，应明确列为不可支持；不作虚假承诺。

### 3.3 构建 / 发布交付形态

推荐 CMake 配置，两个主要成品：同工具链 `eab2::engine` 静态库与 C ABI `eab2_c.dll/.so`；C++ 门面不是跨编译器 ABI。Boost 后端保持 private，不把 `cpp_int` 暴露给 C 接口。安装包包含 C 头文件、可选 C++ 头文件、库、许可、版本和 `self_test` 小程序。

替代全头文件库虽易嵌入，却让宿主编译 flags 控制谓词并扩大 ABI/ODR 风险，不推荐。静态与共享库都跑相同语料；动态库用显式绝对路径加载，不靠 Windows 搜索路径碰巧找到另一版 DLL。所有工具链的性能门在语义差分后运行。

<a id="s4"></a>
## 4. 可微层：“划”与“片”分离

### 4.1 为什么不直接 `template<class S>` 替换 Fraction

战略教训不只是 Python 慢，而是把拓扑决策和连续表达式一起固化在 `Fraction` 上，导致“片 + 划”的连续资产无法播种。反过来把所有 Fraction 改成 Dual 也不成立：精确符号 / gcd / 根隔离需要有理数，导数通道既不应进入组合分支，也不适合参加大整数排序。

推荐三个概念接口（仅规格示意，不是本单新增产品代码）：

```cpp
BranchToken classify(const ExactInput&, const Query&);   // 精确原值，产出“划”
CertifiedValue construct(const ExactInput&, const BranchToken&);
template<Scalar S>
PieceResult<S> evaluate_piece(const BranchToken&, const SmoothInput<S>&);
```

`BranchToken` 包含输入版本、完整特征集、相对侧、投影夹持区段、根身份、有效域、全部精确并列及所选 piece ID。参数原值与 token 不匹配则重新分类；不能持旧 token 对任意新原值给无条件梯度。`evaluate_piece` 不新增拓扑分支，必要的分支只能取原值 `val()` 后交回精确分类层。

组合层只看原始 binary64 的精确提升 / 保留的精确构造，不用 `val(rounded_gap)` 或导数的大小改标签。`val()` 是显式取原值的纪律，**不是允许普通浮点比较替代精确谓词的许可证**。

### 4.2 原值合同与导数合同是两件事

`S=double` 是正演，`S=Dual<W>` 一次连续求值同时传播 W 个方向；精确分类和认证构造仅做一次，不为每条导数通道重做几何。`W` 常用 1/4/8，可批播参数；不先实现动态维自动微分图或反向模式。

**关键界面：**普通 double 公式多次舍入不自动等于 Python“精确表达式到输出一次 RN”。正式结果包含 `certified_primal`（认证构造值）、`piece_jacobian`（连续片导数）和 `sensitivity_model`。模板结果的公开原值必须接回同一认证视图，使 double / Dual 的正式原值逐位一致；内部临时值不反流到精确决策。这里“一次舍入”以每个现有公开构造边界为单位，不是声称整个引擎从输入到输出只舍入一次。

导数定义为**未量化连续片模型**的导数，不是 binary64 舍入阶梯函数的数学导数。文档 / JSON 明写这一点，不能用覆盖 `.val` 的手法掩盖模型不同。精确构造与 double 导数并存的推荐备选比较：

| 方案 | 取舍 |
|---|---|
| 全部 jet 通道都用 Fraction / 代数数 | 能对部分代数 jet 精确，但爆炸、trig/LP 基变化仍不可直接解决；不作为一般敏感性默认 |
| 原值和标签精确，连续导数 double（推荐） | 一次 W 通道成本可控；导数不是证书，需状态和误差 / 可分辨性诊断 |
| 原值、标签、导数全 double | 快但丢失本项目精确合同，拒绝 |
| 只做有限差分 | 可作独立验证，昂贵且容易跨标签，不是正式 L4 实现 |

现有 Python `dual.py` 的加减乘除原值、乘 / 商导数已采用 Fraction 完成指定表达式再 RN；因此增加一个**兼容代数 jet 入口**，其 `mul_add` / 商法则 helper 按原合同精确回退并逐位差分。不能宣称普通 bdda2 Dual 的每条 double 导数都与它逐位一致。新的片内灵敏度接口按下文近似合同比较，先在 Python 明确该合同，再发布 C++。

### 4.3 Dual<W> 的最小纪律与来源

推荐独立写一个小型 `Dual<W>{double value; array<double,W> derivative;}`，借鉴 bdda2 的接口纪律，不复制其头文件。只读参考：

- `D:/b-DDA/bdda2/core/types.hpp:28–42,63–100`：W 通道结构、运算、`val()`、`is_exact_zero()`。
- `bdda2/ad/params.hpp:108–120`：无量纲参数播种；`ad/gradient.hpp:121–140`：一次 `run<Dual<W>>` 取得 Jacobian。
- 设计不引入 DDA 的材料槽、自由度、目标函数、GN 反演或 include 路径；没有姊妹构建 / 运行依赖。

约定：禁隐式 double 转换，禁 Dual 比较运算；数学函数用 eab2 的 AD overload，不调用会降为 double 的 `std::sin(Dual)`；通道宽度类型静态一致。恒等更新的零跳过只允许 `is_exact_zero` 同时检查原值及全部通道；不允许仅凭 `val(x)==0` 或 `x!=0` 跳过更新。零长度 norm、奇点 sqrt、非法幂与 `atan2(0,0)` 不默认给零导数，明确 `singular/unsupported`。

备选复制 `types.hpp` 可省少量实现时间，但混入 bdda2 的零范数默认导数与普通舍入口径，还需许可审查。故不推荐。若以后改为复制，必须另行注明授权、原路径、日期和提交版本；本单没有对姊妹执行 Git 命令，不捏造其提交号。参考快照的 SHA-256 仅用于来源记录，不作为构建绊线：`types.hpp=0483483a6fb65722133440614561feb797a790f0d7961bec1dd6109647844f6f`（2026-10-19 只读）。

### 4.4 接触点、法向、间隙、时刻的导数与边界

同标签内分别求值线段投影、交点、归一化法向、带符号间隙等连续式；例如简单事件根 `F(t,θ)=0`，

```text
dt/dθ = − F_θ / F_t                         仅在 F_t ≠ 0 且标签可延续时
dn = (I − n nᵀ) de / ||e||                  对非零法向生成向量 e
```

根的精确时间与标签由代数层确定；`F_t=0` 要精确判，切触 / 重根不返回巨大的“普通梯度”。对于新时间根的连续参数变化，还要核验候选仍是首次、投影区段仍合法，而非只做隐函数求导。

推荐独立字段：

```text
differentiability = smooth | one_sided | tie | singular | unsupported | unresolved
quality = approximate | bounded | exact_jet
sensitivity_model, selected_piece, tied_labels[], near_labels[]
piece_jacobians[], directional_derivative?, reason, validity_conditions
```

- 精确并列与数值接近分开。`near_labels` 是诊断，不改变 `tied_labels`。
- 并列时可报每个合法片的 Jacobian，但不能把字典序第一项当唯一梯度。
- 指定扰动方向后，核准一侧仍合法才报单侧导数；首入是最早可行事件，不可以无条件对所有候选导数取 min。
- 接触法向集值、零距离范数、投影到端点切换、内缝交会和 LP 退化均显式标旗；没有有限导数时不用 NaN 隐式表达成功。
- 双边有限差分必须两侧同标签；边界只对相应一侧检验，并验证片有效性。完整并列点 / 标签集合协变，字典序代表点不要求旋转协变。

### 4.5 LP 值、对偶及界面参数敏感性

标准型遵循 Python：`min cᵀx, Ax=b, x≥0`；`maximize` 显式处理目标和 y 的符号。浮点单纯形只提候选基，精确层核原始数据的最优 / 无界 / 不可行证书；派生力矩、荷载平移和黏聚上限必须精确传递，不能只对已舍入错误矩阵“精确求解”。[本地 S6](#sources)

对稳定可延续基 / 光滑最优片，包络公式为：

```text
dV = xᵀ dc + yᵀ (db − dA x)
```

使用**原始未缩放 LP** 的 `exact_x/exact_y` 及一致的参数导数。`limit.py:667–689` 的显示黏聚 lambdas 与 row_duals 有 cap 变换，不能直接塞入上式。

| 参数 | 必须传播的项 |
|---|---|
| 摩擦 μ | 二维理想摩擦射线 `g±=n±μt`，`∂g±/∂μ=±t`；对应力矩列同步变化 |
| 块体倾角 θ | 接触点 p、法向 n、切向 t、力 g、参考点 o、荷载方向可能同时变；`d[(p−o)×g]=(dp−do)×g+(p−o)×dg` |
| 恒载与活载 | `b=−W_dead` 的导数；活载 α 列属于 A，必须包括 `−yᵀ(dW_live)α`，不只求 RHS 灵敏度 |
| 黏聚、面积 | `cap=c·area` 进相应 RHS；其参数导数与显示 cap 缩放分开 |

若用户需要对偶机构本身的导数，而不只是承载比 V 的导数，对已认证固定基 B 解：

```text
B x'_B = b' − B' x_B
Bᵀ y'  = c'_B − B'ᵀ y
```

不对单纯形的主元选择 / 换基循环做 AD；这是备选中维护和语义风险最大的路线。稳定非退化 / 严格互补可给唯一片内导数；多个最优基 / 机构时只给候选分支或 `tie/unresolved`。若必须确定某方向的一侧导数，需相邻最优面 / 临界方向问题的独立算法和裁判；尤其 A 随参数变化时，任取一个 y 或对其斜率简单 min/max 不足以认证导数。

**摩擦模型缝隙必须决策：**Python `friction_generators` 会把 RN 后的方向作 ULP 邻居选择 / 向内修正以证明锥包含，故并非处处字面 `n±μt`。推荐值严格复刻这套认证生成线；L4 默认采用**基点锚定连续 lift**，`sensitivity_model=anchored_continuous_lp`：

```text
A_lift(θ) = A_cert(θ0) + A_ideal(θ) − A_ideal(θ0)
```

b、c 需要时同样锚定，行 / 列身份固定于当前片。因此在 θ0 的矩阵和值确为认证 LP，可以使用其 exact_x/exact_y 与 lift 的导数套包络公式；这不是完整理想摩擦模型的最优值导数，也不是离散 ULP 选择程序的数学导数。输出 θ0、锚定修正及完整模型 ID。若所有者改选**完整理想连续 LP**，必须另求该模型自己的值、基和 x/y，分别返回 `V_cert` 与 `V_smooth`，不能挪用认证离散 LP 的证书。C3 不得在所有者未确认命名与 Python 裁判前发布无修饰的“精确承载力梯度”。

### 4.6 导数精度如何负责

导数通道使用 double 足以作为首版数值表示，但“几何精确”不自动给它误差证书。每次记录非有限、范围损失、消减诊断与固定基残差；必要时用精确代数 jet helper 或区间误差估计再标 `bounded`。无可靠界时只标 `approximate`；病态 / 符号不定时 `unresolved`，不用 κ 放大的阈值吞掉真实变化。

验收在有尺度的无量纲参数上做解析式与收敛差分；误差预算采用相对量与逐表达式舍入噪声上界的最大值，不设与问题无关的绝对门。近退化格验证正确旗标而不是强迫梯度通过宽容差。若需用导数符号参与认证或优化器安全约束，必须增加有界导数路径；默认 approximate 不能签安全结论。

<a id="s5"></a>
## 5. API、分层与数据模型

### 5.1 L0–L5 映射与纯度

本稿采用当前仓库 README 的 L0 几何 / L1 接触 / L2 裕度 / L3 承载力 / L4 敏感性 / L5 应用层次，不沿用旧正本另一组编号。数字冲突时以本表说明职责，不静默混用。

| 层 | 命名空间 / 建议 CMake 目标 | 职责与允许依赖 |
|---|---|---|
| 横切数值 | `eab2::numeric` / `eab2_numeric` | private cpp_int / rational、过滤、构造、数值域、FP 自检；不知块体用途 |
| L0 | `eab2::geom` / `eab2_geom` | 环、点、特征、包围盒、几何合法域；依赖 numeric |
| L1 | `eab2::contact` / `eab2_contact2` | E/O、盖、首入、PD/rho、平移锁定及通用路径；依赖 L0 |
| L2 | `eab2::margin` / `eab2_margin` | 通用冻结几何裕度 / 距离证据；域窗口由调用者显式给，不含岩石 / DDA 缺省参数 |
| L3 | `eab2::opt`、`eab2::statics` / `eab2_lp`、`eab2_statics` | 通用 LP、刚体平衡、显式摩擦 / 黏聚列策略；依赖数值和几何，不依赖 TIA |
| L4 | `eab2::ad` / `eab2_ad` | Dual 和选片连续表达式、LP 敏感性；小模板头文件 + 编译好的认证核心 |
| L5 | `eab2::adapters::dda`、`::tia` / 各独立目标 | legacy 编号 / 槽位、锚定运动解释、TIA 块形 / 邻接 / 界面参数、应用报告 |
| 外围 | `eab2::c_api` / `eab2_c` | 稳定 C ABI、批量调用、错误边界；不反向成为算法依赖 |

不为每个目录强建独立动态库；目标划分用于依赖与编译控制，可最终合并成少量库。纯度靠小接口、目标依赖和审查守住，不另造 AST 词法禁词框架。`mtype / df05 / Tuple7 / zsto / DDAAnchoredMotion / escape_height / TIA` 等不得成为内核 API 字段；通用刚体、力矩、摩擦系数本身不算域词汇。

H1 对照：旧 `kernel2d/dda_motion.py` → `adapters/bdda2d_motion.py`；`DDAAffineMotion` → `adapters/bdda2d_affine.py`；`kernel3d/interlock.py` 的逃逸语义 → `adapters/tia3d.py`。当前 `contact_record.py` 含 DDA 状态 / 转移槽位，**不能整体复制**。核心只保留几何身份和生命周期需要的通用数据，legacy 属性包独立存在于适配器。

### 5.2 数据对象

| 对象 | 关键字段 / 不变量 |
|---|---|
| `Body2 / Ring2` | 稳定 body ID、input vertex ID、规范 CCW 点列、原序映射、几何版本；对象不可变；状态 / 材料不塞入几何 |
| `FeatureId` | body、维数、源顶点 / 有向边 ID、side；序列位置不是身份；环反向 / 平直链的别名显式映射 |
| `Cover2` | VE/EV 及闭包 VV 视图、A/B 特征、方向、精确参数域 / 端点、全部来源标签；共线合并不能丢来源 |
| `GlobalE2` | 精确凸胞并、闭 AABB、lazy boundary、E\O 骨架、可选完整带标签剖分；算法表示与语义集合区分 |
| `State2` | body_state 与 topology_state 两枚举，不用一个 inside bool |
| `TimeValue` | rational / quadratic / algebraic 句柄、精确证书、显示 double 与显示状态 |
| `EntranceResult` | 初态、NO_EVENT / FIRST_TOUCH / INITIAL_CONTACT / INITIAL_OVERLAP、时间、全部首特征、见证点 / 法向集合、路径 model_id |
| `DistanceResult` | `query_kind=distance_to_E / PD_closed / rho`、精确平方距离、全部最近点 / 片、显示值；并列代表仅供 UI |
| `LockCertificate` | 单动体 / 固定邻体 ID、状态、精确接触与内点 / 可移除方向见证、支持域和半径；不用 DDA LOCKED 枚举 |
| `SensitivityResult` | 模型、参数种子、标签 / 根 / LP 基身份、质量、片内 Jacobian 或方向导数、并列与失败原因 |

输出全部并列用有序规范集合（稳定标签键）；集合的排序规则不是物理裁决。共享标签可能对应同一几何点，既要几何去重视图，也保留多来源标签视图。不要把一次枚举的 `contact_index` 作为跨步身份。

### 5.3 C++ 宿主接口

同工具链宿主可以使用 RAII handle、`span<const Point2>`、`expected` 风格的项目自有结果类型（C++20 不依赖 C++23 `std::expected`），批量创建 body / E 与查询。认证核心异常在 C++ 门面转换为明确错误；产品不修改宿主浮点环境、日志全局变量或分配器配置。

建议调用顺序：`EngineContext` 自检 → 创建不可变 bodies → 对 candidate pairs 创建 E / motion query → 批量查询 → 获取完整 ties 与证书。重复同一块对几何的多行 legacy 接触只计算一次，再由适配器映射回所有行；完整接触发现不能只依赖 legacy 已存在行。

宿主 bdda2 将导出的 geometry / step endpoints / Tuple7 在自身外部或 eab2 适配器转换成通用请求；三维 DDA 目前只预留快照边界，不暴露不存在的三维能力。**接入主线、策略开关、替换装配与新导出均需所有者另行批准**，本稿无授权效力。

### 5.4 稳定 C ABI

正式跨编译器 / CRT 边界走 C ABI。设计符号版本如 `eab2_v1_*`；引擎能力 v0/v1/v2 与 ABI major 不是同一个版本编号。最小函数族：

```text
get_abi_info / self_test / context_create / context_destroy
body2_create / body_destroy / e2_create / e2_destroy
query_membership_batch / query_translation_batch / query_motion_batch
query_distance_batch / query_lock / solve_limit2 / evaluate_sensitivity
result_get_info / result_get_ties / result_export_exact / result_destroy
context_get_error / context_get_counters
```

上述均为建议接口族，具体签名在 C0 冻结，不以一大段假实现充当设计。

- `extern "C"`、导出宏、Windows `__cdecl`；只用固定宽整数、double、裸指针和长度。禁 STL、C++ bool/enum、异常、引用、Boost 类型越界。
- 结构首字段 `uint32_t struct_size, abi_version`；未知尾部可忽略，未知必要 flag 拒绝。只支持声明的 x64 布局；C 和 ctypes 双方检查 sizeof/alignment/offset。
- context/body/E/result 用 opaque handle；注册表或代数句柄校验跨 context / 过期引用，不把任意地址当可解引用对象。
- 输入同步复制或明确只借到调用返回；结果不可变。变长数组用“查大小 → 调用方 buffer”两次读取，绑定同一 result，避免查询期间结果变化。
- 精确值导出规范分子 / 正分母 UTF-8 字符串；代数数导出整数多项式和隔离证书。热路径走二进制 POD，不强迫每个点编码 JSON。
- 由库分配的对象只由库销毁；调用方 buffer 由调用方释放，不跨 CRT `free/delete`。
- 数学状态（无事件、贯入、LP 不可行 / 无界、证书未证）不是调用错误。错误至少含 `INVALID_INPUT / INVALID_HANDLE / UNSUPPORTED / CONSTRUCTION_RANGE / RESOURCE_LIMIT / FP_CONTRACT / INTERNAL_ERROR`。
- C wrapper 捕获所有异常；失败不留下半初始化 handle；错误文本经 buffer 拷贝，生命周期明确。`UNPROVED` 不降级成成功的 `false`。
- 不同 context 可并行；首版同一 context 不可重入。计数器 / 缓存 / 错误均 context 隔离；线程入口 FP 检查不能省。
- 能力探测 `get_abi_info` 包含 `supports_rho/supports_quadratic/supports_se2/supports_lp2` 等，未实现能力返回明确 unsupported，不能输出占位数值。
- 敏感性 seeds / Jacobian 用显式参数数、输出数、通道数及固定行主序；运行时 W 按 `Dual<8/4/1>` 分块，尾块未用通道置零且不导出。大小 / stride 不符拒收；分块不改变标签，原值只认证一次。

### 5.5 Python 调用与替代方案

标准库 `ctypes` 足够覆盖 POD、opaque handles 与调用方数组；配套 `json / struct / fractions / pathlib` 做语料与精确比较。pytest 仍可作为项目已有测试运行器，运行时用户无需安装它。无需 NumPy、pybind、SWIG 或 Cython；选择 pybind 的便利不足以抵消额外工具链和 ABI 接入成本。

批量 ABI 避免每个点 / 标签跨一次 FFI。纯 C++ 计时、C ABI 计时与 ctypes + JSON 端到端计时分开，不用 FFI 慢掩盖几何复杂度，也不用纯核快掩盖实际集成开销。

<a id="s6"></a>
## 6. 性能目标与测量计划

### 6.1 本次微型测量：仅盘点真实负载

本次用标准库逐行解压当前入库的 `fixtures/m4b_shadow/*.jsonl.gz`，不运行 DDA、不访问姊妹 exe。脚本与原始计数在 [scratch 测量脚本](../scratch_eab2/inventory.py)、[JSON 结果](../scratch_eab2/replay_size.json)，均**不入库**。表中 `rows` 是 post_df06 Tuple7 行数，不是唯一块对 / 弹簧数；`geometry rows` 保留来源索引，不能直接称已清洗的物理顶点数。

| 例 | 帧数 | 块数 | 几何行 / 帧中位数 | 接触行 min / median / max |
|---|---:|---:|---:|---:|
| bb03 | 30 | 11 | 82 | 40 / 40 / 40 |
| bb05 | 30 | 4 | 24 | 10 / 10 / 10 |
| bb06 | 30 | 4 | 24 | 8 / 10 / 10 |
| bb09 | 30 | 12 | 70 | 58 / 58 / 61 |
| bb10 | 30 | 12 | 86 | 74 / 74 / 76 |
| bb12 | 30 | 11 | 81 | 48 / 48 / 54 |
| bb50 | 30 | 2 | 80 | 1 / 2 / 2 |
| bb51 | 30 | 11 | 154 | 54 / 54 / 54 |
| bb52 | 30 | 11 | 154 | 54 / 54 / 54 |
| bbF038 | 30 | 2 | 12 | 2 / 2 / 2 |
| bbS038 | 30 | 2 | 12 | 2 / 2 / 2 |
| bbv01 | 30 | 10 | 155 | 156 / 156 / 156 |
| bbv01_dbv01a | 30 | 10 | 155 | 154 / 154 / 154 |
| bbv02 | 30 | 7 | 108 | 88 / 88 / 88 |
| bbv02_dbv02a | 30 | 7 | 108 | 88 / 88 / 88 |

合计 **15 例 × 30 = 450 帧、25,295 接触行**。逐帧中位数 54 行、P95=156、最大 156；块数中位数 10、最大 12；无序全块对候选中位数 45、最大 66，合计 14,970 步—候选块对。P95 用 nearest-rank。两阶段 raw/post 分开盘点，不把它们相加后称每步负载。

环境：Windows 11 x64、Python 3.12.10、Intel Core Ultra 7 270K Plus（24 核 / 24 逻辑处理器）。本次纯盘点墙钟约 **0.192 s**，只说明读取计数成本，**不是 Python 几何性能，更不是 C++ 加速比**；与仓库测试并发，不作独占基准。

现有 M5d 全历史报告另有 1,810 步、15,220 块帧、64,010 步—块对、16,676 初态贯入，其中 C1 认证 4,280、未证 12,396（读取 `reports/codex/M5d_evidence/c1_summary.json`，本次未重算）。这与 450 帧入库切片是不同分母，不能把历史认证率套到当前性能负载。

### 6.2 DDA 每步目标：计全部行，也计完整候选

以下是**待 C0 校准并由所有者冻结的验收建议，不是已达成绩**。硬件首选上述 CPU 单线程、Release `/O2`、固定功耗 / 无并发负载；至少报告三轮独立运行，中位数与逐帧 P95/P99/max，记录时钟、编译器和后端版本。

| 工作负载 | 建议目标 | 计时边界 |
|---|---|---|
| 450 帧 DDA-P1：全部 post_df06 行的首盖 / 初态静态出口 | **逐帧 P95 ≤10 ms，最大 ≤50 ms**；中位规模 54 行，最大 156 行 | 已解析输入；包含当步规范化、精确域检查、按块对去重计算、全部并列和映射回所有行；排除磁盘 / JSON |
| 同帧完整接触发现 | **P95 ≤20 ms，最大 ≤100 ms** | 包含最多 66 对的保守 swept-box 筛选、未被排除者的精确查询；不得只检查 legacy 现有对 |
| 已建不可变 E 的批量 membership | 常规非退化格 **均摊 ≤10 μs / 点** | 热 E、多点，统计所有回退；仅作部件门，不替代上两项 |

几何随步变化不能把“上一步 E 缓存命中”偷偷计入热查询；允许单帧内同块对复用，另报冷构造成本。初态贯入只算**初始静态** PD_closed / rho；从分离出发才走 P1 首入。M5b/P2 尚未进 v0，因此本表不能称“全部真实 DDA 轨迹每步 10 ms”；C4 单独冻结六次事件目标。

若目标未达，优先查原始候选数、cell 数、精确回退位长、重复构造，再做精确剪枝 / 缓存 / 公共分母优化；不通过少算行、丢 ties、改成近似或跳过退化来达标。无数据时不承诺百倍加速。

### 6.3 TIA 二维 20 × 40 顶点目标

基准应由领域所有者提供并冻结真实 TIA 截面，另加可公开的确定性合成版本；目前没有把“20 个非凸块约 40 顶点”这一完整场景实测成既有结果。建议冻结如下工作量，防止用 20 个凸盒替代：

- 4×5 组装、20 个简单非凸环、各 40 顶点（范围 36–44 另列）、至少一半为真正凹顶点；一组非对称一般位置、一组紧配缝 / 孤立点 / 共线族。
- 全 190 对做 broad phase；预定义的水平 / 垂直邻接共 31 对（16+15）全部构造 E，并保留非邻接排除证据。若真实场景的邻接更多，按实际边表另报，不用该数字限流。
- 31 个 pair E 的外边界与 E\O 均可查询；同时对每个块、其余固定，构造联合障碍查询并输出 20 个平移锁定 / 可移除 / 初态非法证书。不能用 31 个 pair lock 布尔值代替联合判定。
- 另做全部 190 对强制构造的压力档，以及尺度 / 大平移 / 旋转档；它们不是同一耗时目标的偷换分母。

**建议冷启动门：31 邻接 E + 20 个固定邻体锁定证书总耗时 ≤5 s，峰值额外内存 ≤512 MiB；全 190 对压力档 ≤30 s / ≤1 GiB。** 包含输入域认证、凸分解、完整接触骨架和锁定所需证据，不含 JSON / 绘图。重复三轮冷对象，不能让进程级 cache 伪装冷启动。资源超限显式报错并保留触发规模，不将未完成项记为“未锁定”。

这组门有风险：40×40 原始 VE/EV 就可达 3,200 条线段 / 对，交叉细分可近二次爆炸；≤5 s 是工程目标而非复杂度保证。C1 应先量 N、凸片对数、原线段数、交点数、骨架尺寸与 bit length；若不可达，所有者决定收窄首版支持的复杂度预算或增加优化工期，不能默默删除完整 E\O。

### 6.4 过滤与成本统计

每个 context 可启用低开销整数计数，至少包括：

```text
predicate_calls[kind], filter_accept[kind], exact_fallback[kind]
fallback_reason = uncertain | exponent_range | derived_exact | disabled_filter
exact_zero[kind], max_integer_bits, gcd_calls, rational_normalizations
cells_before_after_merge, candidate_pairs, excluded_pairs, segment_intersections
root_isolations, root_refinements, gcd_equalities, peak_live_exact_objects
lp_float_candidates, lp_certificate_pass, lp_exact_recovery, pivots
cache_hits/misses, rows_mapped, bytes_peak, stage_wall_time
```

失败比例定义 `uncertain / eligible_filter_calls`；同时给 `all_exact_fallback / all_predicate_calls`，不能把本来强制精确的派生点算成过滤器失败后误导优化。精确零单列；近退化压力集允许 100% 回退，正确性门不设回退上限。常规格可将 ≤10% 作为调查触发线，**不是强迫错误 fast path 的验收指标**。统计开启 / 关闭各计时一次，确认探针开销。

建议先测 `cpp_int` 的 bit length 与 gcd 费用，再决定 expansion 或 GMP；JSON / ctypes 时间另报。微型测量总预算不超过约一小时，本单只做轻量规模盘点，没有借设计单写性能原型产品。

<a id="s7"></a>
## 7. Python 裁判与差分测试

### 7.1 一个小协议，不再造验证产品

生产 C++ 不调用 Python；测试端用同一 JSON case 分别喂 Python 与 C ABI。Python 只使用既有参照实现及少量独立手算例，不复用 C++ 的谓词 / 舍入代码。C++ 的精确 helper 不能反向导入裁判；不通过“共享同一几何原语”制造一致。

主门分四组即可：`numeric`、`geometry_motion`、`statics_ad`、`abi_environment`。语料生成 / 最小化程序应小而直白，产出输入与两侧结果；不用几十层 manifest / 源码绑定流水线。既有 Python 的所有门保持原状，本单不删改；**不移植**静态构造 AST 门、变异充分性框架、源码哈希绊线，不把耗时巨大的历史重放绑定重签流程带到 C++。

源码版本号、依赖版本、算例数据 checksum 可以记录以复现，但 checksum 不相等不等于算法错误，也不以 checksum 相等替代重新计算。少量错误编译负例、数值反例和人工内部故障探针可以检验比较器确实会报错；不建“变异百分比达标”平台。

### 7.2 共享 JSON schema 建议

每个输入有 `schema / case_id / operation / model / input / query / compare_profile`；schema 大版本变化需显式转换。binary64 使用 16 位十六进制 **bits 字符串**，大整数和有理数用字符串，避免 JSON decimal / 语言默认 parser 的隐式舍入。例（概念性完整 membership 请求）：

```json
{
  "schema": "eab2.case.v1",
  "case_id": "unit_squares_touch",
  "operation": "membership2",
  "model": "binary64_exact_simple_ring",
  "input": {
    "bodies": [
      {"id": 1, "vertices": [
        {"id": 0, "xy_bits": ["0000000000000000", "0000000000000000"]},
        {"id": 1, "xy_bits": ["3ff0000000000000", "0000000000000000"]},
        {"id": 2, "xy_bits": ["3ff0000000000000", "3ff0000000000000"]},
        {"id": 3, "xy_bits": ["0000000000000000", "3ff0000000000000"]}
      ]},
      {"id": 2, "vertices": [
        {"id": 0, "xy_bits": ["3ff0000000000000", "0000000000000000"]},
        {"id": 1, "xy_bits": ["4000000000000000", "0000000000000000"]},
        {"id": 2, "xy_bits": ["4000000000000000", "3ff0000000000000"]},
        {"id": 3, "xy_bits": ["3ff0000000000000", "3ff0000000000000"]}
      ]}
    ]
  },
  "query": {"moving": 1, "fixed": 2, "offset_bits": ["0000000000000000", "0000000000000000"]},
  "compare_profile": "exact_states_and_labels"
}
```

正常输出统一 `schema, case_id, call_status, mathematical_status, exact, display, labels, ties, diagnostics`。有理值写 `{"num":"1","den":"3"}`；代数值写 `kind, polynomial_integer_coefficients, interval_lo/hi, endpoint_policy`，可有理化时写 rational。`display` 的 double 也写 bits / `display_status`，不让 `Infinity` 混入非标准 JSON 数字。

P1 输入是两端点逐顶点 bits、路径域 `[0,1]`；P2 使用通用有理路径系数及 model_id，由 DDA 适配器先解释其参数。LP 输入同时包含原始精确派生矩阵表达式 / 有理证书与浮点候选视图，不能只序列化 A 的 RN 显示值再宣称验证了完整模型。

产品输入仍是 binary64。Python 既有 Fraction 测例若不能精确表示为 binary64：要么作为精确内部 primitive 的独立单元语料，要么显式 RN 后让两侧共同接收新输入并重求期望；不把旧 rational 期望强加给已舍入几何。schema 扩展 exact-input 能力必须另行批准，不暗增 C ABI 输入域。

### 7.3 语料来源与覆盖

| 类别 | 现有来源 / 新增计划 | 比较重点 |
|---|---|---|
| 数值历史反例 | `test_r9fix_construction_rounding.py`、`test_m5a_algebraic.py`、`test_lp_certificates.py` 等 | 舍入中点两侧、次正规、溢出胞、严重消减、错误浮点候选 |
| 2D E/O | `test_m3_global2d.py`、`test_m3b_2d.py`、`test_m3c_determinism.py`、`test_kernel2d_covers_e3.py` | L/槽/口袋/紧配缝/孤立点/平直；T2a 覆盖、T2 裁剪、T2b 保留每个维层 |
| DDA 冻结输入 | `fixtures/bdda_df`、`fixtures/m4b_shadow`、`fixtures/m4c_motion/endpoints.json` | 15×30 帧，原始 / 规范编号映射、全部行、P1 与静态出口 |
| M5 | `fixtures/m5a_se2/*.jsonl.gz`、`fixtures/m5a2/*`、既有 M5a/b/d 测试输入 | P1/P2/P3 模型分开、二/五/六次事件、恒共线、整窗非法、R1/R2/C1 拒签域 |
| TIA | 现有二维互锁截面、单体 / 多体 limit 测例；另冻结真实 20×40 场景 | 接触完整性、作用反作用、μ 临界点、非对称力矩参考、联合锁定与机构区别 |
| 近退化生成器 | 新的固定 seed 原始输入生成，保留最小失败 JSON | 共线 / 近平行、相距 1 ULP、极窄边、极端指数、并列最短出口、重根、根极近、负 / 正零 |

生成器先生成合法环与标签已知的小例再扰动，不用拒绝采样只留下容易的“成功”样本。报告尝试数、拒收原因、实际各状态计数；分界点 / 非对称一般位置 / 几何与荷载分别缩放三类格必须都有。现有 full-history 输入未全部落在紧凑 fixtures，长回放只消费冻结导出，缺失则列缺失，不重跑姊妹求解器补齐。

### 7.4 比较矩阵

| 输出 | 正确比较口径 | 禁止做法 |
|---|---|---|
| 状态、有效性、物理特征标签 | 精确相等；按原 ID 映射后规范集合逐项比较 | 以近似 gap 相同代替标签相同；漏并列但选中项相同就通过 |
| E/O 与外边界 | 物理集合 / 物理片及来源标签同构；所有必要 0/1/2 维层查询一致 | 强迫两算法的人造剖分边 / cell 序逐字节相同 |
| 约定一次舍入的构造 | 同一精确目标数的显示 bits 逐位相等（含约定零符号 / 显示状态） | `abs(a-b)<1e-8` 掩盖错舍入；先求 float 后算标签 |
| 有理时间、平方距离、见证 | 约分后的精确值 / 全并列集合相等 | 只比较输出时间 double |
| 代数时间 | 精确有理比较或 gcd + 指定根隔离证书证明同一实根 | “区间有交集即相同”；固定 1e-12 时间窗 |
| LP | 数学状态、最优值、原始 / 对偶 / Farkas / 射线证书；最优面不变量 | 强迫任意最优 x/y 每分量一致；拿某个机构分量当全局性质 |
| 既有兼容代数 jet | 按 Python 原合同逐位比较 | 把普通 double Dual 的偏差忽略却声称完全移植 |
| 新连续导数 | 模型 / 标签 / 质量先相等；光滑片解析 / 收敛 FD；边界核单侧与旗标 | 把跨标签中心差分失败当数值精度问题；任取一个并列梯度 |
| 证书 | CERTIFIED 的完整见证可独立复核；同算法合同要求拒签域一致 | UNPROVED 当不安全 / 不锁定；将几何近似证据当强认证 |

“标签逐项相等”指**语义标签集合**，不是 legacy 候选原序。C++ 对 Python 的语义差分可以严格，C++ 对 DDA legacy 的集合 / 槽位差异仍需如实台账；不因此重写 legacy 顺序。

### 7.5 不一致处理

1. 保存唯一最小 case、两侧结果、API / model / compiler 版本、计数器；停发该能力。
2. 先查接口转换 / 位模式 / 规范 ID，再查 C++ 过滤、精确 fallback、构造、层级接线。默认归类 **C++ 缺陷**，不能先扩大容差。
3. 在 C++ 关闭过滤重跑：差异消失则定位过滤合同；不消失则定位 exact 算法 / 输入模型。Python 不修改。
4. 缩小顶点 / 参数仍保持失败，加入一条具名语义回归；不以输出后追加假数据检验比较器。
5. 只有独立数学证据足以怀疑 Python 时，形成单独裁判修订单交所有者 / Claude；旧期望保留，新版本明确批准后才刷新。禁止同时改两边直到“对上”。
6. 修复后跑对应语料、全部元门及发布矩阵；未处理差异为 0 才可验收，不靠 xfail/skip 升绿。

### 7.6 少量但有力的元门

- **刚体运动与单位：**每个几何 / 力学 API 做非对称参考点、随机旋转、大平移 `|t|∈{0,10³,10⁵}`（预留三维加入 `10⁶`）、几何与荷载独立缩放。距离 ×s、平方距离 ×s²、承载比按相同载荷尺度不变；点 / 法向 / 完整并列集按变换对应。
- **浮点变换的边界：**安全符号置换实现的 90° 旋转，以及每个坐标都可精确表示、无溢出且无下溢舍入的二进尺度可做精确等变格；由整数尾数 / 指数检查可表示性。任意旋转 / 大平移后 RN 会改变给定几何。远离事件且有足够分离界才要求状态协变；近退化 / 坐标消失格则对变换后的实际 binary64 输入重新与 Python 精确差分，不错误要求被舍入掉的几何仍不变。
- **对称交换：**位移坐标 `E(A,B)=−E(B,A)`，交换 A/B 后 VE↔EV、法向 / 作用反作用相应变化；原文 a0/b0 记号须加平移项。最小例包含非轴对称凹环。
- **LP 参考点 / 单位：**接触形心本身移离原点，核逐体平衡与相对功率；不能只挪调用方参数、实际 LP 仍在原对称中心。对偶选取不同只比较最优面不变量。
- **AD 一致：**double 与 Dual 的正式 primal bits 相等；单通道与批通道一致；原值零而导数非零仍参与恒等更新；边界报告 tie/singular。
- **表示 / 调用序：**环循环起点 / 方向、输入 body 顺序、先 membership 后 subdivision 与相反顺序、缓存开关，规范身份下语义一致。

稳健管是 L∞ 盒时，任意旋转后重新包成轴对齐盒会放大集合，充分证书的认证 / 未证状态不要求不变；必须精确变换扰动集合或仅在等价盒变换上比状态。不能把这项与名义刚体不变性混成一条不可能的门。

<a id="s8"></a>
## 8. 里程碑、验收与工作量

### 8.1 退出规则

每个里程碑交：能力清单、固定语料、差分摘要（通过 / 不支持 / 错误逐项计数）、性能分位数、已知限制和一名专责对抗核查员的书面意见。核查员不审自己编写的路径。

本表的“一名核查员”是**工程预验收责任人**，不取代 AGENTS 的六路 G6 独立对抗退出门。产品里程碑要按纪律 D 在所有者允许的新鲜 checkout / worktree 跑全套，并完成六路 G6、0 critical / 0 major 后才更新 README 能力声称。若所有者想把六路改成单人，须先正式修订治理规则，本设计不擅自豁免。

本单只写文档，且明令禁止 worktree，不实施上述未来产品退出动作。文档评审通过 ≠ eab2 C0 通过。

### 8.2 排期表（人日，非本单时长）

下面工期假设一名熟悉本仓库的 C++ 实现者，外加可用的独立审查人；不含等审批 / 接入宿主排期。上下限包含正常返修，不含重大理论新发现。设计单的约三小时目标与以下实现工期没有关系。此处 **C1 是二维 E 移植里程碑**，不是 M5d 的“稳健 C1 证书”，也不是本设计工单 WO-C1 的退出状态。

| 里程碑 / 版本 | 范围 | 差分语料 | 建议性能门 | 一名专责核查员要核什么 | 实现 + 专责预审 |
|---|---|---|---|---|---|
| **C0 / v0.0** | exact 输入、cpp_int/rational、RN 构造、2D 过滤、FP 自检、C ABI 骨架、Dual 最小合同 | 中点 / 极端指数全边界矩阵；至少 10⁵ 随机符号 / 构造；非法输入；错误编译矩阵 | 常规直接 orient/cross 10⁶ 次单线程 ≤0.5 s 的初始预算；精确压力单列，不用快路吞错；以实测调整一次并冻结 | 差分减法是否已舍入、二次舍入、次正规 / FMA、坏编译真被拒绝、C ABI 布局与释放 | 8–12 + 2–3 人日 |
| **C1 / v0.1** | 一般凹环 E/O、T2/T2a/T2b、物理标签、lazy 结构与域验证 | 六类 M3 族、完整分层点 / 边 / 面探针、bb52 21 对、近退化至少 10⁴ 个合法 case | §6 的 membership 门；31 邻接 **E 部分**冷构造预算 ≤4 s，锁定不在本阶段伪测 | 内缝 / 孤立点是否丢失，反射 / 平直锥，隐藏盖是否错当 ∂E，精确剪枝是否漏等号 | 15–22 + 3–4 人日 |
| **C2 / v0 完整** | T3、PD_closed、rho、单对平移锁定；P1 二次事件和整窗域 | 450 帧全部 P1 对账、各类 ties/切触/重根、Python 新 rho/lock 裁判、非法中间环 | DDA 行级 P95 10 ms / max 50 ms；完整候选 P95 20 ms / max 100 ms | 初态分类、出口是否被混成步内事件，锁态不等于贯入，二次根漏端点，最短集合是否全 | 12–18 + 3–4 人日，另需 Python 前置 4–7 人日 |
| **C3 / v1，主线推荐 TIA** | 多体 LP2、所声明机械 profile 下的完整装配、联合固定邻体锁定、μ/倾角 L4、批量 ABI | 20×40 真场景及合成场景；现有 LP 证书族；滑动 / 倾覆临界；多最优面；VV互斥模式拒收；FD / 解析片 | §6 TIA 冷 E+lock ≤5 s；受支持机械 profile 的 LP2/4 通道敏感性暂预算 ≤1 s（≤60 平衡行、≤512 变量，另报黏聚行）；超规格另测 | 摩擦射线/力矩/活载导数、raw x/y 缩放、最优面退化、pair-lock 冒充 assembly-lock、是否把互斥法向强行 AND | 15–25 + 4–5 人日，新增敏感性裁判另需 3–6 人日，机械装配裁判另需 4–7 人日 |
| **C3-D / v1 小适配器** | 只读 DDA 输入与槽位映射、P1/静态出口离线报告 | 15 例所有入库帧、raw/post/VV 第二参考 / 共边槽；不运行姊妹 exe | 纯映射额外开销 ≤核查询 10% 或独立 ≤1 ms/最大帧，均需实测 | raw ID 0 与规范 ID 0 区别，候选保留 / 提升含义，未证名义结果不叫漏检 | 4–6 + 1–2 人日；主线接入不在工期内 |
| **C4 / v2** | 一般实代数时间至多六次，M5a SE2、M5b P2 与完整 M5d 名义 | 既有 M5a/M5b 事件族、真实 M5 冻结帧、五/六次非退化及恒等约束、根极近 / 重根 | 先以裁判同语料为基线，建议 450 帧名义核总计 ≤60 s、单帧 P99 ≤0.5 s；所有精确慢例另列 max | gcd 判等是否定位同一根，正分母消去、零多项式、路径拟合≠真实运动、model_id 不混淆 | 15–22 + 4–5 人日 |
| **C4-R / v2 可选** | R1/R2、受限 C1 稳健证书；R3 不默认移植 | 已有证书 / 未证反例与管边缘样本；M5d 4280/12396 只是历史分母，须实际重跑选定输入 | 单独列认证 / 未证成本；建议同名义输入附加成本中位数 ≤2倍，不为通过率放宽条件 | 全窗、两条管、竞争事件、L∞预算、凸域限制、未证是否被误报不稳健 | 8–15 + 3–4 人日 |

粗计 v0 实现及前置 / 专责预审约 **47–70 人日**；v1 在此基础上再约 **31–51 人日**。六路 G6、宿主审批和可能的算法返工另留 20–30% 计划余量，不宣称这些可以全并行压成一周。C4/C4-R 是否启动由 v1 的真实用途和收益决定。

### 8.3 推荐与备选排程

**推荐：C0 → C1 → C2 → C3(TIA)；C3-D 作为小型并行只读对账；再决定 C4。** 好处是最早对齐所有者“引擎 + TIA 外域”的定位，并让 AD 接缝从 C0 存在，不到最后才发现 Fraction 封死连续层。

备选先 C3-D 再 TIA 可以更快在熟悉数据上看到接触报告，但仍不能以 DDA 窗口 / legacy 顺序定义核心。备选将全部 M5d 名义提前到 v0，代价是 C4 的代数核、P2 域和 15–22 人日实现同步前移；不能只改版本标签、保留二次内核却声称六次事件已支持。

三维独立立项前置：二维 v1 达到真实外域验收，明确三维支持域（先凸后一般凹），解决 / 限定 T3L 平行退化与局部盖候选超集问题。当前不报三维移植工期，以免把研究缺口伪装成机械翻译。

### 8.4 C3 的 L1→L3→L4 验收链

1. TIA 适配器输出 block geometry、固定约束、完整界面接触特征、材料参数及来源；L1 不把同一接触线段随意离散成唯一点。推荐首个机械 profile 为**刚体、小变形、已选定可延续的定向直边接触段与唯一合法法向的 VE**，法向 / 模态由物理界面模型确认，而非随便选一个 tied cover。
2. 几何法向集合不等于一组可以全部做 AND 的约束。两方块只在角点接触时，局部非贯入速度可为 `(vx≤0) OR (vy≤0)`；强行同时约束会排除合法运动方向，在某些组装体中造成虚假锁定。VV、凹角交会、互斥模态未被专门模型解析时返回 `MECHANICAL_UNRESOLVED`，不跳过它们后继续宣称完整 LP。要支持一般 TIA 的全部这类接触，需要另加 mode-aware 分支装配 / 可行性语义与 Python 裁判，不能只增强 Dual 的 tie 旗标。
3. 在已冻结 profile 内，恒 μ、非黏聚且允许任意集中压应力的二维直边接触，可用端点射线表示其可达力 / 力矩锥；有限压力上限、非均匀材料或黏聚不是同一模型，需另给面积 / 强度分配规则和认证。首版 generic `LimitContact` 可保留已有黏聚 LP 接口，但 TIA 自动装配不默认启用黏聚。
4. **先补 Python 装配裁判**：现有 `limit.contacts_from_covers()` 每盖取一个代表点、跳过无 normal 项、并拒绝 `cohesion>0`，不能冒充上述完整界面转换。新增裁判核正长度段、作用反作用、端点力矩、重复来源和互斥模式；表中另计 4–7 人日。若所有者要求 v1 完整一般多模态 TIA，这个估计不足，须重新估价，不能静默降成子域。
5. L3 返回精确 LP 状态 / 值及证书。内部从**不可变、声明完整的 L1 contact-set handle** 装配，才可拒绝遗漏必要约束 / 未解析模态；外部裸接触列表只能标 `caller_supplied/completeness_unknown`，引擎不能凭空知道漏项。初态贯入和非法法向必须显式拒收。L1 几何完整、profile 内装配完整、任意组装体力学完备是三项不同声称。
6. L4 对同一个锚定模型、选片 / 基输出敏感性，核 μ 临界、倾角切换与最优机构不唯一。20×40 几何性能门可独立验收；**完整 TIA 力学链**只在场景的所有接触都被所声明 profile 支持时通过，不把 MECHANICAL_UNRESOLVED 计为通过。
7. 一名领域使用者能从 C ABI/ctypes 复跑完整受支持链，不安装姊妹仓库，不需要 legacy exe；所见限制与状态和差分报告一致。

<a id="s9"></a>
## 9. 五大风险与未决问题

### 9.1 最可能出错 / 最贵的五件事

| 风险 | 早期信号 | 控制措施 / 停止线 |
|---|---|---|
| **1. E/O 混淆导致 TIA 约束或锁定错** | 紧配点被删除、int E 一律报贯入、pair-lock OR 后称整体互锁 | C1 保留完整接触骨架；rho/lock 先补 Python；输出问题域。未有裁判不发布该能力 |
| **2. 精确构造与 AD 原值 / 模型脱节** | double 与 Dual 原值不同；认证摩擦修正的导数被称唯一精确梯度 | 双轨结果、兼容 jet 入口、敏感性模型明名。所有者未选模型则 C3 L4 不退出 |
| **3. 40 顶点凹 E 的组合 / 位长爆炸** | 交点数、胞对数、gcd / 分母位长上升；P95 被少数格主导 | C1 就量真实 20×40，lazy / 精确剪枝 / 合并；资源预算失败关闭。性能不达不能牺牲 E\O |
| **4. 编译器 / 宿主环境破坏过滤保证** | 优化级不同符号不同、FTZ 切换、FMA 探针失败 | 受控 TU、构建身份、每批线程自检、负构建矩阵；未知构建模式拒绝。模板不承载认证决策 |
| **5. 扩大范围与裁判缺口一起进入引擎** | M4c 被宣传真实 DDA 轨迹、P2 被称任意仿射、UNPROVED 被称不稳健、三维先于二维外域 | 能力矩阵与 model_id；C4 后置、三维另立；差异先算 C++ 缺陷，Python 变更另单批准 |

### 9.2 请所有者 / Claude 决定

| ID | 需要决定 | 推荐默认 | 不决定的后果 |
|---|---|---|---|
| D1 | v0 是否包含 rho 与 §3.10 锁定；谁补 Python 裁判 | 包含，先发小单补 rho / 单对及固定邻体合同 | C2 相应能力不能验收；不是本设计单阻塞 |
| D2 | C3 优先 TIA 还是 DDA | TIA 主线，DDA 仅小只读适配器 | 容易重新被 legacy 槽位牵引 |
| D3 | L4 的“承载力梯度”究竟对哪个连续模型 | 默认基点锚定连续 LP，与认证矩阵在基点严格相同；完整 ideal 模型则另求值 / 基 / x/y | 不能混用两模型证书，更不能称梯度精确对应量化程序 |
| D4 | 默认接受 Boost 依赖及其分发方式吗 | cpp_int / cpp_rational 私有封装，锁已验证版本，保留 BSL | 若坚持零外部 C++ 依赖，需另估大整数成本；不能偷用 GMP DLL |
| D5 | 接受 §6 绝对性能目标与真实 TIA 几何清单吗 | C0/C1 首次测量后只校准一次，随后冻结；目标和结果分列 | 未冻结前性能数字只为规划，不作交付成绩 |
| D6 | 完整 M5d 名义是否必须早于 v2 | 否；先 P1/静态，五六次事件在 C4 | 若是，C4 必须连同工期前移，不可假装 P1 足够 |
| D7 | G6 六路退出与轻量差分如何安排人力 | 保留 AGENTS 退出规则，单名专责预审先行；缩验证装置不缩独立审查 | 无权以本稿豁免 G6，README 不提前升级声称 |
| D8 | 何时批准 DDA 主线接缝 | 本单不批准；只交接口和离线对账 | 没有接入并不妨碍引擎设计完成 |
| D9 | 首个 TIA 机械接触 profile：固定界面还是一般多模态 | 首版冻结定向直边 / 唯一法向 VE，先补装配裁判；VV/凹角未解析必须显式未证 | 若真实首例要求一般多模态，C3 需扩范围 / 重估工期，不能称现有 contacts_from_covers 已完整 |

本设计推荐项互相一致：保留精确数学承诺，同时把导数、性能、域模型与研究证书的边界明说；不能用“暂时全 Fraction”回避 L4，也不能用“C++ 快”掩盖完整几何 / 准确比较的成本。

<a id="sources"></a>
## 10. 来源、术语和验收索引

### 10.1 本地一手输入 / 代码依据（本次只读）

- **S1 理论归属正本输入**：[shi_comparison_20261019.md](file:///D:/eab-wt/cx-e2/reports/codex/inputs/shi_comparison_20261019.md)。重点：对照表 A、归属订正、第三节未实现锁定证书。本文归属按此，不沿袭旧 canon_map 的错误转述。
- **S2 分层与历史设计**：[当前 README](../README.md)、[AGENTS](../AGENTS.md)、[外部旧设计 07](file:///D:/E%28A,%20B%29/07%20程序设计·统一接触内核方案.md)。外部 07 只作历史动机，冲突处按工单 / S1 订正。
- **S3 二维全局集合**：[global_entrance.py](../src/eab/kernel2d/global_entrance.py)（237–300 数据、320–349 双三态、406–568 边界与骨架、592–634 首入 / PD）；[M3 设计](m3_global_entrance_design.md) T1/T2/T2a/T2b。理论归属以 S1 为准。
- **S4 数值**：[predicates.py](../src/eab/predicates.py)、[construction.py](../src/eab/construction.py)、[numeric_domain.py](../src/eab/numeric_domain.py)、[dual.py](../src/eab/dual.py)。特别是构造中点和 Dual 代数 jet 的整式舍入合同。
- **S5 路径**：[motion.py](../src/eab/kernel2d/motion.py)、[algebraic.py](../src/eab/kernel2d/algebraic.py)、[M4c](m4c_motion_entrance_design.md)、[M5a](m5a_se2_design.md)、[M5b](m5b_motion_theory.md)、[M5d C1](m5d_c1_theory.md)。H1 目标职责在只读 cx-e2 `adapters/` 观察，最终以其合并清单冻结。
- **S6 力学**：[lp.py](../src/eab/lp.py)、[limit.py](../src/eab/limit.py)、[limit_multi.py](../src/eab/limit_multi.py)。精确数据 / 证书、摩擦射线修正、显示缩放和最优面非唯一性。
- **S7 姊妹可微设计参考**：[types.hpp](file:///D:/b-DDA/bdda2/core/types.hpp)、[ad/params.hpp](file:///D:/b-DDA/bdda2/ad/params.hpp)、[ad/gradient.hpp](file:///D:/b-DDA/bdda2/ad/gradient.hpp)。只借鉴纪律，不产生代码依赖，不在本单复制。
- **S8 规模**：[入库 15 例 manifest](../fixtures/m4b_shadow/manifest.json)、[M5d 历史计数](../reports/codex/M5d_evidence/c1_summary.json)、[本单轻量盘点](../scratch_eab2/replay_size.json)。scratch 不随文档入库，关键计数已完整抄录 §6.1。

### 10.2 官方外部资料（本次核查；选版须在实施时冻结）

- **N1** [Shewchuk：Adaptive Precision Floating-Point Arithmetic and Fast Robust Predicates](https://www.cs.cmu.edu/~quake/robust.html)、[原作者关于 x87 的说明](https://www.cs.cmu.edu/~quake/robust.pc.html)：过滤 / 自适应精确谓词和机器算术前提；不是所有本稿表达式的现成误差界。
- **N2** [Boost 整数后端比较](https://www.boost.org/doc/libs/latest/libs/multiprecision/doc/html/boost_multiprecision/tut/ints.html)、[官方 Multiprecision 仓库](https://github.com/boostorg/multiprecision)：header-only 后端与 cpp_int / GMP 取舍。
- **N3** [Boost Software License 1.0](https://www.boost.org/LICENSE_1_0.txt)：许可依据。
- **N4** [GMP 许可](https://gmplib.org/manual/Copying)、[GMP 特定平台说明](https://gmplib.org/manual/Notes-for-Particular-Systems)：许可选择、Windows / Microsoft C 使用注意。
- **N5** [MPFR 官方项目](https://mpfr.org/)、[MPFR 手册](https://mpfr.org/mpfr-current/mpfr.html)：许可证与正确舍入模式。正确舍入某次 MPFR 操作不等于任意多步表达式一次舍入。
- **N6** [CGAL 包级许可](https://www.cgal.org/license.html)、[编译器与第三方依赖](https://doc.cgal.org/latest/Manual/thirdparty.html)：不能把全部包概括成统一宽松许可。
- **N7** [Microsoft /fp](https://learn.microsoft.com/en-us/cpp/build/reference/fp-specify-floating-point-behavior?view=msvc-170)、[fp_contract pragma](https://learn.microsoft.com/en-us/cpp/preprocessor/fp-contract?view=msvc-170)、[预定义宏](https://learn.microsoft.com/en-us/cpp/preprocessor/predefined-macros?view=msvc-170)：precise、fast、收缩和编译模式探测。
- **N8** [Clang Users Manual](https://clang.llvm.org/docs/UsersManual.html)：浮点模式、fast-math、收缩选项。
- **N9** [GCC Optimize Options](https://gcc.gnu.org/onlinedocs/gcc/Optimize-Options.html)：fast-math、fp-contract 与优化语义。

### 10.3 工单逐项落点

| 工单要求 | 本文位置 | 实施前必须注意 |
|---|---|---|
| 1 范围 / 移植次序 | §1.4–1.6、§8 | rho/lock 是裁判缺口；全 M5d 名义等 C4 |
| 2 数值 / 大整数 / 代数数 | §2 | 推导每个实际过滤表达式的界；Rational 用薄封装，不新造整数库 |
| 3 编译 / 自检 | §3 | 受控构建身份 + 真实探针；有限自检不证明任意未知 flags |
| 4 可微层 | §4 | 精确原值和连续导数分轨；固定片 / LP 基，边界显式 |
| 5 分层 / API / ABI | §5 | H1 后域词在 adapters；ctypes 足够 |
| 6 性能 | §6 | 盘点是本次实测；所有引擎耗时是待测目标 |
| 7 差分 / 元门 / 不移植 | §7 | 语义标签与同一精确构造严格比较，不比较任意人为表示 |
| 8 里程碑 | §8 | 单名预审不替代现行 G6 六路退出 |
| 9 风险 / 待决 | §9 | 不需要这些决策才能交设计，但实现退出前必须冻结 |

**终版阅读提示：**本文件交付的是可执行的设计与验收建议，不是 eab2 已编译、已达性能或已经接入 DDA 的证据。
