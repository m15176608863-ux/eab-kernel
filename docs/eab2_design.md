# eab2：C++ 接触引擎设计

> **第二版，按 Claude 四路评审修订** · WO-C1 · 2026-10-19  
> 工作树 `D:/eab-wt/cx-c2`，基线 `eab2-design @ 1ce9a91760e22cab7e471e76c39dcc2b786eb6ab`。Python `src/eab` 是参照实现兼裁判；不一致先按 C++ 缺陷处理。本文是设计，不是实现完成声明。

**改动摘要**
- 主线重排为 C0 → C1 → C3-TIA → C2 余项与 C3-D 合并对账 → 再定 C4；C0 与 T1a 并行。
- C0 只做 MSVC 14.44 x64、纯精确谓词与 RN-even 构造，缩减浮点与验证装置。
- TIA profile 1 明定关联流动、边界类型、完整原始接触段与局部自由锥凸性规则。
- 区分不可严格分离、缝滑、平移不可动及整体一阶可动性；增加阈值括号。
- 二维敏感性默认 ideal_exact_2d；补精确稳定性、退化方向导数与临界参数导数。
- 补 T1a 八项裁判前置、TIA 数据对象、分阶段 ABI 冻结及确定性工作上限。
- 性能只报告；写入既有测量及其口径，D1–D9 改为已定。
- 退出按 H1：Claude 安排一名非作者对抗核查员、0 critical / 0 major，加新鲜树复现。

### 第二版修订 r3

- 通用精确 LP 前移至 C3-L1 入口，由 L1/L3 共用；总工期不变。
- 接触约束按每个接触点的自由锥生成，禁止把原始端点关联或体对凸性直接当机械约束；v1 不枚举模态。
- 钉住一阶零锥、无界射线、μ_crit、Mills/Freund 单 LP 与开/闭阈导数的精确定义和接口字符串。
- 恢复 ABI 错误/数学状态边界，补独立扇区 oracle 与 binary64 精确关系元门。
- v1 按原字节移入 archive 并加替代说明；本版原地修订，报告以最终 SHA-256 供 T1a 钉版。

## 导航与本单合同

[§1 范围](#s1) · [§2 数值](#s2) · [§3 编译](#s3) · [§4 可微层](#s4) · [§5 API](#s5) · [§6 性能](#s6) · [§7 差分](#s7) · [§8 里程碑](#s8) · [§9 决策与风险](#s9) · [§10 来源](#sources)

本轮 r3 只改本文、[交付报告](../reports/codex/C1_report.md)并整理归档文档；不再新建一份设计归档，也不改上一轮的根 `.gitignore`。第一版逐字节保存在 [设计归档](archive/eab2_design_v1.md)、[报告归档](../reports/codex/archive/C1_report_v1.md)，其 [设计归档说明](archive/README.md)与[报告归档说明](../reports/codex/archive/README.md)明确已被第二版取代。旧方案与历史链接不构成本版依赖。其余工作树与姊妹仓库只读，不改产品代码、不跑测试、不做 Git 写操作。

完成标准：既有综合报告 §2.1–2.14 及 D1–D9 无回退，r3 的1–11项有报告落点；T1a前置八项保留原编号，具体规范按r3修订；最终设计SHA-256写入报告。C0可直接下单；当前文档不依赖临时评审/测量文件；UTF-8无BOM、归档字节不变、改动范围合规。本轮不执行产品编译、差分、性能或新鲜树验收。

<a id="s1"></a>
## 1. 范围、理论合同与移植顺序

### 1.1 定位与分层基线

eab2 是供不同宿主调用的几何、接触、极限分析引擎。**TIA 二维为第一外域**：L1 完整接触约束 → L3 关联流动极限分析 → L4 界面参数敏感性；DDA 是之后的首个离线对账适配器，不定义内核术语。固定端、无限抗压的 G1–G4 输出阈值与模式；有限承载力首例采用 G5 力控预压，不能把无界读成承载力数值。

按 WO-H1 搬家后的分层设计：`predicates / construction / numeric_domain / rational3 / dual / lp / margin / limit / limit_multi / oracle_construction / kernel2d / kernel3d` 为通用范围；legacy 槽位、DDA 锚定路径、TIA 逃逸语义归 `adapters/`。`oracle_construction` 是 Python 独立核验资产，不复制为 C++ 生产依赖。本树的旧模块路径只是来源索引；H1 合入后按其清单重定路径，不在内核保留 adapter 兼容转发。

非目标：DDA 积分、开闭迭代或弹簧装配重写；接入 bdda2 主线；动力学标定；GPU；一般曲面 CAD；完整 SE(2)/SE(3) 配置障碍。三维另立项。姊妹仓库零代码依赖，输入只消费冻结导出。

### 1.2 集合、输入和状态

A 动、B 固定，统一使用位移坐标 t：

```text
E = {t : (A+t) ∩ B ≠ ∅} = B−A              闭障碍
O = {t : int(A+t) ∩ int(B) ≠ ∅}             开贯入集
body_state     = OUTSIDE / CONTACT / OVERLAP   E外 / E\O / O
topology_state = OUTSIDE / BOUNDARY / INTERIOR  E外 / ∂E / int E
```

原文参考点坐标 `E(A,B)=B−A+a0` 与此差一个坐标平移。正则闭简单环域中 `closure(O)=E`，但 O 可严格小于 int E；内缝和孤立紧配接触点可在 int E。两种三态必须分开，禁止“inside 即贯入”。

首版几何域：单个无洞简单环，有限 binary64 坐标；至少三点，无零长边、回折、自交和零面积，允许共线、平直顶点。允许 CW/CCW，规范化保留原 ID，不擅删平直顶点。输入不支持洞不等于 E 不能有洞；多环实体另定合同。−0 的输入 bits 保留溯源，几何值视为 0。NaN/Inf 拒收。

### 1.3 理论归属与查询语义

| 内容 | 归属 / 边界 |
|---|---|
| E、距离、凸性、平移不变性 | 石根华原文及既有 Minkowski / 配置障碍理论，不作首创宣传 |
| §4.5 对称定理 | Shi 2015；位移坐标为 E(A,B)=−E(B,A)，参考点坐标另带平移项 |
| §4.7 可移除定理；§3.10 平移锁定判据 | Shi 2015；后者是无任意小严格分离平移，不是组装体不可动定理 |
| T2a 有效盖弱覆盖，∂E ⊂ ∪C ⊂ E | Shi 2015 §7–8、2021 §6.1 已有；本项目补输入假设和退化闭包 |
| T2 cutting 得精确边界；T2b 完整接触骨架 | 原文陈述 cutting；本项目严格化算法与证明，未裁剪盖不等于边界 |
| 首入与最短出口 | 概念原文已有；具体算法、并列协议为实现选择 |
| O、E=closure(O) 的集合化及 rho | 原文没有这一计算体系；不能把 int E 等价贯入归于原文 |
| SE(2)、仿射一步事件、R1/R2/C1 | 超出原文平移框架的项目延伸；稳健证书本版不排程 |

归属按 [S1 原文对照](#sources)，不冒称本单重读全文。三个距离/事件不能混用：

- **首入 T3**：从 E 外沿路径首次触及闭 E，包含瞬时切触和全部并列；初态在 E 时保留低层 t=0，另报初态，不伪称新碰撞。
- **PD_closed**：int E 到 ∂E 的距离，是严格脱离闭 E 位移长度的下确界；边界见证仍接触。不是贯入恢复距离，也不是沿步轨迹出口时刻。
- **rho / overlap_recovery_distance**：O 内到 ∂O=E\O 的距离，O 外为 0，可结束于内缝/孤立点。Python 另发小裁判单，随后续 DDA 阶段移植，不是 v0/TIA 前置。

### 1.4 版本与函数级移植清单

版本不是 Python 里程碑编号：v0 为 C0/C1 二维数值与集合底座；v1 先 TIA，后 DDA；v2 待决定的高次事件。下表是语义移植，不要求照译内部 helper。

| 版本 / 阶段 | Python 来源模块与函数 | 推荐范围及备选取舍 |
|---|---|---|
| v0 / C0 | `numeric_domain.exact_input/check_input/check_mu/binary64_argument`；`predicates.cross2_sign/dot2_sign`，二维 orient | 精确 binary64 解码、全部纯精确符号；不先引入浮点过滤 |
| v0 / C0 | `construction.scalar_rational/scalar_algebraic/ratio_rational/vector_rational/sqrt_rational/norm_rational/unit_rational/normalized_difference_rational` | 全部构造合同逐位对齐；scalar_algebraic 的 compare→RN 边界不等于 C0 实现 Sturm |
| v0 / C0 可选，C3 前补齐 | `dual.Dual/val/is_exact_zero/sqrt` 的接口纪律 | 独立最小 Dual；不逐位移植 Python dual.py 的 jet；sin/cos/atan2 等按实际连续片再增 |
| v0 / C1 | `kernel2d.exact.signed_area2/convexity_violation/entrance_block_exact/membership_exact/vertex_side_exact/ve_side_exact/ev_side_exact/polygons_overlap_exact/entrance_membership_exact` | 一般凹简单环精确输入、集合成员、凸快路；不移旧近似窗口 |
| v0 / C1 | `covers.ve_cover/ev_cover/vv_cover/enumerate_covers`；`global_entrance()/GlobalEntrance2.membership/topology/cell_edges/clipped_covers/subdivision/boundary` 的语义 | M3 T2/T2a/T2b；E、O、内缝/孤立点；∂E 从紧凑 T2b 导出，**不照搬 boundary/side_probes 慢算法**。支持局部 t=0 查询，无须每次建全局骨架 |
| v1 / C3-L1 入口 | `lp.solve/maximize` 的精确求解/证书层及齐次可行性 | 横切 `eab2::opt`，L1、L3共同依赖；先于VV冗余与一阶可动性，不等待C3-L3 |
| v1 / C3-L1 | T1a 新增 `translation_lock_certificate/assemble_contact_set2/first_order_free_twists` | 单对/固定邻体联合不可分离证书、按接触点装配、非贯入锥、一阶单体/多体可动性；v1未解析真VV返回MECHANICAL_UNRESOLVED |
| v1 / C3-L3 | `limit.wrench/limit_load/check_duality/mechanism_is_admissible`；`limit_multi.LimitBody/BodyContact/limit_load_multi/check_duality_multi/mechanism_is_admissible_multi` 的 dim=2 子集；T1a `limit_load_ideal_exact_2d/critical_parameter` | 在共用精确LP核上装配力学、端板DOF及阈值证书；不以 `contacts_from_covers(_multi)` 当完整装配，不默认移黏聚 |
| v1 / C3-L4 | T1a `evaluate_sensitivity2`；连续几何片及所需二维 margin 合同 | ideal_exact_2d、有限值dV、μ_crit隐函数导数；`margin.py`当前偏三维，不能据文件名声称已具备二维API |
| v1 / C2余项+C3-D | `GlobalEntrance2.ray_intervals/first_entrance/distance_to_e/shortest_exit`；`entrance.first_entrance`；`motion_exit.shortest_exit_fast`；新增 rho | T3、全并列 PD_closed/rho；局部 `entrance.shortest_exit` 不移入全局 PD；先精确基线再快路 |
| 同上 | `motion.QuadraticTime/MotionEntrance2/motion_first_entrance`；H1 后 `adapters/bdda2d.py` | M4c/P1 顶点线性弦二次事件、整窗域认证、15例离线映射；M5d 名义中的 P1/静态部分，不称完整 M5d |
| v2 / C4 待定 | `algebraic.p_gcd/RealAlgebraic/roots_interval/sign_at`；`se2.SE2Motion/rotate_rational/se2_slice/se2_first_entrance` | M5a 有理半角 SE(2) 至多五次，非任意 sin(ωt) 路径 |
| 同上 | H1 `adapters/bdda2d_motion.py` 的 `area_centroid/rational_half_angle/DDAAnchoredMotion/dda_motion_from_z/p2_p3_bound/projected_sweep/dda_first_entrance/dda_paths` | M5b 特定锚定 P2 六次、M5d 其余名义；DDA 参数解释在 L5 |
| 不排程 | `model_robustness` R1/R2、`m5d_exit_certificate.exit_order_certificate` 稳健 C1 | 保留历史来源，不移植向内线，不设独立稳健证书里程碑 |
| 暂不移植 | `rational3/kernel3d`、三维 margin/limit、`adapters/tia3d.py`、三维 DDA | 二维外域验收后独立立项，先明确凸/凹域及退化缺口 |

`AffineFit/fit_affine` 是通用端点拟合诊断，`DDAAffineMotion` 搬至 `adapters/bdda2d_affine.py`；M5b 不等于已有一般仿射首入。T1 A.2(c) 的 M5a 路径研究在 v1 保持 Python-only，属 T1b，不阻塞 C3。

#### 1.4.1 Python 裁判前置清单（T1a）

以下八项**逐字转录综合报告 §5.5**，保留交接编号；其中“5.4”指综合报告的敏感性修订。它们由Claude另发T1a产出，不是本单已实现功能。r3补充/订正的具体规范以本文§1.6、§4.5–4.6、§5.2/5.4及§7为准：点自由锥而非体对判据、无模态枚举、精确证书与字符串均须同步，不得把历史摘要当豁免。§8.3按同编号签收。

1. 通用 kernel2d `translation_lock_certificate`（单对 + 固定邻体联合）。
   - 字段与设计 LockCertificate 一致，状态 ∈ {NOT_CONTACT, REMOVABLE_TRANSLATION, NOT_SEPARABLE_TRANSLATION, UNPROVED}。
   - 外加细化 {TRANSLATION_IMMOBILE, SEAM_SLIDING(射线)}，以及局部锥覆盖见证和有理 r。
   - 不含域词汇。
2. 通用 limit 层的完整界面接触装配裁判。
   - 输入为 t=0 骨架；每条极大共线正长度接触段给出端点射线。（r3 订正：逐接触点 F_p 生成约束，见 §4.5）
   - 处理作用与反作用、重复来源去重；凸性判据下，真 VV 返回 `MECHANICAL_UNRESOLVED` 或作冗余丢弃。（r3 订正：冗余只在 twist 空间证明后丢弃并附证书，见 §4.5）
   - 不经过 `contacts_from_covers`：它会跳过 normal=None 的盖、接受 gap>0 的盖，且每个盖只取一点。
3. 未归一化精确 2D 生成元的 opt-in 函数，以及 5.4 的敏感性裁判。
4. `critical_parameter` 括号裁判。
5. `first_order_free_twists`：单体/多体、感知模态，作为建议中的 L1 API。（r3 订正：v1 不枚举模态，未解析真 VV 时返回 `MECHANICAL_UNRESOLVED`，见 §1.6）
6. 每个算例导出 eab2.case.v1 JSON，附墙钟耗时。
7. 输入数值域：
   - 拟交给 C++ 的子集全部用 binary64 可表示的值。
   - 每条界面折线只构造一次、RN 一次，两侧块和边界体引用同一组 double。
   - 边界体的面在块顶点处结束，即没有 T 形接点；确实需要时，让接点在 binary64 下与邻边的叉积精确为 0。
   - RN 之后用精确谓词复核：每个预期接触都是 CONTACT，且没有新增凹角；记录 xy_bits。
   - 纯有理族和腐蚀族只留在 Python。
8. 状态枚举、`MECHANICAL_UNRESOLVED`、`sensitivity_model` 字符串与设计逐字一致。

### 1.5 E 构造选择与局部查询

| 备选 | 取舍 |
|---|---|
| 凸分解→凸胞差→并集与完整标签骨架（推荐） | E/O 有直接集合解释，Python 已有裁判；组合数大，采用精确合并、AABB、惰性查询 |
| 局部有效盖→cutting / reduced convolution | 可能减少候选，但有效盖不足以表示全部 E\O；不能以 T2a 冒充 T2/T2b |
| CGAL arrangement/Minkowski | 算法丰富，依赖与许可、标签改装成本大；首版不选 |
| 凸包/GJK/SAT 代替凹 E | 不是相同语义，拒绝作为一般凹解法 |

保留 `merge_convex/compact_subdivision` 的精确语义。T2b 原始 VE/EV 段完整切分，CONTACT 开段、端点、孤立点均保留，不先按有效盖法锥删除内缝。∂E 从骨架两侧占据导出，小例对 Python boundary；不把逐片昂贵 side_probes 路线翻译成产品。人为竖直剖分允许不同，比较规范物理集合。

C1 同时提供 **0 处局部胞/切锥和原始接触来源段查询**，供 C3 使用；它不是只取规范 E\O 边。按需物化全局骨架，局部结论必须有精确排除证据。AABB 含等号，使用精确界；缓存以不可变几何版本为键，受单一 context 管理。

### 1.6 不可分离、缝滑与一阶可动性

`LockCertificate.status ∈ {NOT_CONTACT, REMOVABLE_TRANSLATION, NOT_SEPARABLE_TRANSLATION, UNPROVED}`。初态任一邻体OVERLAP（Python membership=1）即返回非法初态拒签原因，不进入这四个合法锁定状态。对合法CONTACT初态，Shi §3.10回答**是否不存在任意小严格分离平移**。单对0∈int E或固定邻体联合 `E_i=∪j E_ij` 的内点证据可签NOT_SEPARABLE_TRANSLATION；OUTSIDE邻体不贡献接触段，无CONTACT邻体时为NOT_CONTACT。

增加精确非贯入平移锥：在0处保留逐对原始接触骨架，排除 `∪j O_ij` 的方向。**细化只对NOT_SEPARABLE_TRANSLATION给出**：锥={0}报TRANSLATION_IMMOBILE，非零报SEAM_SLIDING并附精确有理射线。REMOVABLE_TRANSLATION附精确分离射线，不给缝滑细化；无接触自由运动也不命名缝滑。

证据是**局部锥覆盖**：各邻体过0的胞及切锥；S¹每段弧明确标三类之一：贯入（附阻挡特征）/保持接触/分离。r为正有理数，且 **r²严格小于到所有不过0的相关胞边的精确平方距离**；不是把通常无理的最近距离叫有理r，也不依赖联合PD_closed或全局内球。证书可引用产品胞；独立扇区oracle不得复用这些胞（§7.4）。

逐对NOT_SEPARABLE做OR是固定邻体联合不可分离的**充分但不完全**证书；逐对可移除不蕴含联合可移除；两者都不是组装体互锁证书。两对各自可移除，联合仍可能只能沿一条缝双向滑动。G5内块、Koureas块2用作区分例；提交C++的平行面版本须用二进有理斜率/坐标使RN为恒等，历史有理方向±(−1/10,1)不能直接当binary64子集的精确方向。

C3增加 `first_order_mobility(assembly)`，Python裁判为 `first_order_free_twists`：单体对固定邻体、多体两版，按Assembly2的FIXED_BODY及dof_mask消去受限自由度，**只有v_n≥0，无剪胀**。v1不做模态枚举；ContactSet2含未解析真VV即返回MECHANICAL_UNRESOLVED，裸角对角方块的可动性查询也必须如此。

在实际自由twist坐标v中记法向约束矩阵G，自由锥为 `{v:Gv≥0}`。**锥={0}当且仅当G满列秩且下述归一化精确LP最优值为0**：`max 1ᵀ(Gv), s.t. Gv≥0, 1ᵀ(Gv)≤1`。必须先核精确秩：ker G非零即有双向自由线，单靠该LP看不到它。非零锥以精确双描述给生成元（含线性空间两向）；零锥给每个±e_k的非负法向旋量组合证书，即 `Gᵀλ_k^±=±e_k, λ_k^±≥0`。双描述不是模态枚举。共用LP核在C3-L1入口先交付（§5.1/§8.2）。

一阶锥={0}推出不可动；非零锥只给一阶候选，**不推出存在有限运动**。L3的关联承载力是另一问题，禁止“L3无界⇒几何不可动”。

<a id="s2"></a>
## 2. 数值体系

### 2.1 三通道，不造万能 Scalar

```text
binary64 bits → 无损二进有理数 → 精确标签 / 事件 / LP证书
                           └→ exact recipe → RN-even → CertifiedValue
连续参数 + 精确 BranchToken → evaluate_piece<S> → 连续片导数
未来可选过滤器仅提名符号，不确定则走同一精确层
```

v0 纯精确，`cpp_int`/二进有理整数快路及私有 Rational；输入减法也在精确层，不能把已 RN 的 b−a 当原始差分。所有有限 binary64 都可进入精确谓词，包括次正规和极端指数。Python `numeric_domain` 的工程显示包络只施加于对应近似公开构造，不能截断精确谓词输入域。资源上限失败与数值域错误分开。

### 2.2 谓词次数与将来的过滤选择

| 类别 | 次数（除标明时间外，均相对原始坐标） | 选择 |
|---|---|---|
| 排序、AABB | 1 | 原始 double 比较或构造有理比较；AABB 精确界 |
| cross/dot、orient2d、面积、原边侧、凹凸 | 2；面积项数随顶点增长 | C0 直接整数/有理；以后低阶静态界可选 |
| VE/EV 锥、绕数、线段交会 | 多个 1/2 次符号的组合 | 不用 atan2/epsilon；直接精确 |
| 原始叉积比的交点/参数排序 | 清分母后至多 4 | 分母符号先定，直接精确交叉乘 |
| 点到原始段平方距离/比较 | 分子4、分母2；比较≤6 | 精确平方距离，不先 sqrt |
| 剪裁段/构造端点距离比较 | 依构造链，混合可达8、构造端点可达10；并非统一原始2次 | v1 直接有理；实际链的界在过滤入口再定 |
| T3 平移时间 | 时间1次 | 精确有理闭区间，保留单点 |
| M4c/P1 线性顶点运动 | 时间≤2次 | DDA 阶段二次数精确排序/隔离 |
| M5a / M5b | 特定半角模型清正分母后时间≤5 / ≤6次 | C4 精确实代数；一般仿射/trig 无此上限 |
| LP 可行性、约化成本、Farkas | 有理线性系统，次数随基规模 | 浮点仅提候选，原始精确数据核证 |
| 三维 orient3d | 3 | 不进 C0，三维项目另定 |

备选 Shewchuk 式扩展算术适合低阶行列式，但不能替代交点、LP、Sturm；静态界便宜但限定操作图，动态区间通用但成本更高。**推荐先纯精确，T1 剖析确认瓶颈后才引入过滤**。派生有理点携带 exact shadow，普通 double 过滤不能冒充对真点的判定。N6–N8/F12eng 的入口清单在 §8.6，不在本版展开实现。

### 2.3 精确目标只 RN-even 一次

对 x=n/d、d>0，符号另存：

1. n=0 输出约定 +0；非零用整数 bit length 与精确移位比较求 `e=floor(log2(|n|/d))`，显式守卫 `msb(0)`。
2. `k=max(e−52,−1074)`；`N=|n|·2^max(−k,0)`、`D=d·2^max(k,0)`。
3. 整数 `q,r=divmod(N,D)`；仅当 `2r>D` 或 `2r=D 且 q 为奇数` 才进位。
4. 用 `bit_cast` 打包 q·2^k，处理跨 binade 进位与次正规/正规交界，不用 `double(n)/double(d)`，不依赖 long double。
5. 非零真值舍到零默认命名失败；仅明确 `allow_underflow` 的显示边界允许带状态的 ±0。最大有限值上方、仍处其舍入胞内的数**必须返回最大有限值**；`|x|≥2^1024−2^970` 按构造合同失败，不能任意钳位。

`sqrt(n/d)` 用整数平方根与 `4N` 对 `D(2q+1)^2` 的中点比较，ties 看 q 奇偶。单位向量分量为 `sign(v_i)·sqrt(v_i²/Σv_j²)`，不先 RN norm 再除。`normalized_difference_rational` 的 `c/sqrt(nn)−offset` 必须整体对中点比较，不先舍入两项。

`scalar_algebraic(compare)` 接收精确实数与有理数的比较能力，在正 binary64 位序搜索邻数，再比较有理中点；溢出胞的概念上邻取 **2^1024**，不是 Inf。有理/平方根 compare 足以验证 C0 边界，完整根引擎留 C4。

几何构造失败对应 Python `ConstructionDomainError`；LP 精确值仍可保存而显示溢出，此时 `display_status=DISPLAY_OVERFLOW`，不等于数学 UNBOUNDED。需要 NaN 占位时固定 quiet-NaN bits `7ff8000000000000` 并带 display_status，不能把任意 NaN payload 纳入成功位比较。每个导出字段发布其有限域、零符号和下溢合同。

### 2.4 实代数数（后置能力）

DDA 阶段时间采用 RationalTime/QuadraticTime。C4 的 `RealAlgebraic` 只需整数多项式、指定实根的有理隔离区间及开闭端点，不开放通用 CAS。存储多项式可 primitive/squarefree，平方自由不等于不可约；系数常数项在前。

Sturm 计根并细化；不同多项式以 gcd 加指定隔离区间证明相同实根，重叠区间本身不是判等。`sign_at(q,α)` 用 gcd 零判和精确隔离；排序先排等值再分离。零多项式是恒等约束，不能丢为“无事件”；端点根显式处理。资源超限返回 RESOURCE_LIMIT，不猜符号。N9 的 Sturm 正缩放与 N10 的非规范根身份须在 C4 入口冻结，见 §8.6。

### 2.5 大整数与依赖选择

| 方案 | 许可/构建 | 性能/维护取舍 | 结论 |
|---|---|---|---|
| 自写只头文件整数 | 可自控许可和 MSVC 适配 | 除法、gcd、进位、移位审计量大，变成第二个产品 | 不选；只写薄封装与 RN 边界 |
| Boost.Multiprecision | BSL 1.0；cpp_int/cpp_rational 可头文件，原生 MSVC 部署简单 | 大位数可能不及 GMP，先实测；维护量最小 | **已定：vendored、钉版本、随附 BSL** |
| GMP/MPFR | GMP LGPLv3+/GPLv2+，MPFR LGPLv3+；原生 MSVC 不是最简构建路线，DLL/静态分发需审查 | 大整数成熟；MPFR 某步正确舍入不保证复合表达式一次舍入 | 首版不用，必要时另案评估 |
| CGAL | 包级 GPL/LGPL 或商业许可；CMake/依赖更多 | 算法丰富，E/O 与标签仍需定制，模板维护重 | 非默认生产依赖 |

这些既有资料列于 [§10](#sources)；不宣称本次测过候选库速度。D4 已决定 Boost，**具体已测版本号由 C0 入口钉定**，不是使用 latest 浮动下载。Int 与私有 `cpp_rational` 包装均 `et_off`，表达式必须在封装边界求值，Boost 表达式类型不得外泄。可用公共分母减少 gcd，必须对未优化精确路径差分；不另写通用 Rational 库。

<a id="s3"></a>
## 3. 编译与浮点合同

### 3.1 C0 支持域与将来扩展

C0 **仅 MSVC 14.44 x64**，VS 自带 CMake≥3.21/Ninja，仿只读 `bdda2/build.bat`。受控数值 TU：

```text
/std:c++20 /O2 /utf-8 /permissive- /fp:precise /MD
fp_contract(off)
禁止 /arch:AVX*、/GL、/fp:fast、/fp:contract
```

默认 x64 SSE2 路线，不支持 x87 扩展寄存器精度；FMA 会把两次舍入变一次，破坏按分步图证明的过滤界及导数复现。fast-math 还会重结合、假定有限数、改变 signed-zero/次正规语义。纯精确谓词和整数 RN 不依赖这些浮点技巧，但模板片/环境边界仍受最小合同约束。ISA、编译器与后端版本写构建身份，禁 /GL 防跨 TU 重优化。

将来支持 clang/gcc 的目标保留：C++20，`-fno-fast-math -ffp-contract=off`，拒 `-ffast-math/-Ofast`，受控目标禁 LTO；尚未支持，不纳入 C0 矩阵。它们的收缩模式不能靠宏完整检测，不能声称通过公开 CMake target 传播 flags 就控制了宿主。公开头只用局部且恢复的 pragma；不复制 bdda2 文件级无 push/pop 的 pragma。

### 3.2 最小自检与失败关闭

编译期拒 `_M_FP_FAST / __FAST_MATH__ / _M_FP_CONTRACT`。`eab2_self_test` 在 context 创建和数值批次入口检查当前调用线程：

- IEEE binary64 布局，`FE_TONEAREST`；MXCSR FTZ/DAZ 关闭，**第7–12位异常屏蔽位全部置位**，防未屏蔽溢出先触发 SEH。
- ties-to-even、有符号零、渐进下溢；加载运行时输入，结果用整数 bits 检查，避免常量折叠。
- 一条同受控 TU 的收缩探针 `(1+2^-27)*(1-2^-27)-1`：分步应为 0，融合为 −2^-54。不能把中间乘积强制 volatile 后声称检测了收缩。

失败统一返回 `EAB2_FP_CONTRACT`，不给几何/LP 答案，不替宿主修改 FP 环境。调用期间不得异步更改环境。默认 ISA 没有 FMA，探针通常不会触发；**它不是任意错误编译选项的万能识别器**。受控构建拒不支持 flags；已知坏环境必须失败。任意手工伪造构建身份不能仅靠有限探针保证发现，不作这种承诺。

每 TU 清单、负构建矩阵、跨编译器以及过滤器均推迟至 §8.6 的性能优化入口。最小坏环境拒绝检查仍在 C0；它不是负构建全矩阵。

### 3.3 交付形态与模板控制

同工具链 C++ 静态库及独立 C ABI DLL；跨编译器边界只承诺 C ABI，不让 STL/Boost/Dual 穿过 DLL。静态库用 C++ 测试可执行文件，ctypes 加载测试 DLL 的绝对路径，不能直接加载 `.lib`。

库敏感性入口在受控 TU 显式实例化 `Dual<1|4|8>`；公开头用 `extern template`、带版本 inline namespace 及隐藏可见性/明确 DLL 导出边界，避免宿主 COMDAT 合并改变库实例。宿主自行实例化模板可用，但**不承诺导数位可复现**。认证原值只从编译核心的 CertifiedValue 导出。全头文件生产库虽好嵌入，却扩大 flags/ODR 风险，不推荐。

<a id="s4"></a>
## 4. 可微层：“划”与“片”分离

### 4.1 分类、构造、连续求值

Python 的 Fraction 固化了精确拓扑，但不能承载 Dual；把 Fraction 全改 Dual 又会破坏符号、gcd 和证书。推荐签名上分三步，以下仅接口草图：

```cpp
BranchToken classify(const ExactInput&, const Query&);  // 精确原值决定组合标签
CertifiedValue construct(const ExactInput&, const BranchToken&);
template<class S> PieceResult<S> evaluate_piece(const BranchToken&, const SmoothInput<S>&);
```

Token 含输入版本、特征集合、相对侧、夹持区段、事件根、有效域、全部精确并列及 piece ID。原值变化先重新精确分类；不让 Dual 通道影响标签。连续求值中的择支只经 `val()` 取原值，涉及几何组合变化则返回分类层，不用普通浮点比较替代精确谓词。

### 4.2 正式原值与导数的合同

S=double 是片内正演/诊断；S=Dual<W> 一次传播 W 个方向。**正式原值唯一来自 construct() 的 CertifiedValue**；double 临时结果和 Dual.value 不直接导出，也不反流为精确判据输入。每个公开构造边界一次 RN，不是整个引擎从头到尾只舍入一次。

输出分 `certified_primal`、`piece_jacobian`、`sensitivity_model`。导数是未量化连续片的导数，不是 binary64 阶梯函数的导数。优先 double 导数通道：全有理 jet 成本大且不能解决模态切换；全 double 标签不满足语义；有限差分只作核验。删除兼容 Python dual.py jet 的逐位移植义务，libm 值不作逐位承诺。

### 4.3 Dual<W> 来源与纪律

推荐独立实现小型 `Dual<W>{value, derivative[W]}`，不复制姊妹头文件。只读借鉴 `bdda2/core/types.hpp` 的 val/全通道零判与 `ad/params.hpp` 播种、`ad/gradient.hpp` 一次 Jacobian 用法；本仓库零代码依赖。若后来复制，须另记授权、原路径和提交版本，不能本单默认复制。

无隐式 double 转换；不用会降型的 math 调用；宽度是静态类型。恒等更新仅当 `is_exact_zero` 检查**全部通道**才可跳过，禁止仅凭 value==0 或 `!=0` 跳过。sqrt 奇点、零长 norm、非法幂、atan2 原点返回明确状态。C0 可选只做 +−×÷、sqrt，C3 按需要扩整数/半整数幂等，不预建大型 AD 图。

### 4.4 连续几何与标签边界

同标签内求接触点、非零法向、间隙和事件时刻；简单根 `F(t,p)=0` 有 `dt/dp=−F_p/F_t`，F_t 必须精确非零且该根仍为合法首入。投影区段、初态、竞争事件、几何域同时保持才有效。非零法向生成向量 e 的 `dn=(I−nnᵀ)de/||e||` 仅属连续片。

```text
differentiability = smooth | one_sided | tie | singular | unsupported | unresolved
quality = approximate | bounded | exact_jet
selected_piece, tied_labels[], near_labels[], piece_jacobians[]
directional_derivative?, reason, validity_conditions, sensitivity_model
```

精确并列与数值接近分开；字典序赢家只用于显示，不是假唯一梯度。指定扰动方向，确认一侧合法后报单侧值；不能无条件对全部候选斜率取 min。重根、零距离、端点切换、内缝交会显式标旗。持久平局可保留多个标签而同一连续输出；不要因标签不唯一就无条件丢掉可证方向导数。

### 4.5 TIA profile 1 与完整接触装配

**已定 profile ID=`profile1`**：刚体、小变形、无限抗压、非黏聚、恒定μ、**关联流动**；二维直边接触端点射线及精确未归一化生成元。其对偶约束为 `v_n≥μ|v_t|`（剪胀）。相对非关联库仑摩擦模型，这是**不安全侧的承载力上界模型**，不能标安全承载力；非关联互补/MPEC另立后续profile。

边界类型逐字冻结：

- `FIXED_BODY`：相应自由度全部固定；G1–G4固定端的首版主输出为阈值/模式，不能把UNBOUNDED画成有限承载力。无恒载的0/不可行/无界与有恒载时可能出现的有限值分开报告。
- `FORCE_CONTROLLED_PLATE`：端板附 `dof_mask`，顺序 `(x,y,rotation)`，1为自由、0为双向约束；P是死荷载，不是位移约束。用于G5闭式的端板只放开x，即 `[1,0,0]`，竖向/转动均固定。G5基准为奇数个等高h矩形块、竖直平界面、块宽关于受荷中块对称、左端固定、右端板面跨满高h；P沿−x作用于端板，中块沿x=L/2受竖直向下单位活载，无自重。此时 `F=min(2μP,4Ph/(L−b))`，b为中块宽；改变掩码或载荷位置不能继续套此闭式。全部边界/荷载由T1a记录，不默认复用不支持部分DOF的旧limit_multi装配。

**装配函数 `assemble_contact_set2` → ContactSet2**，分接触点枚举与约束生成两步：

1. window 0、t=0：OVERLAP邻体作为非法初态拒收；OUTSIDE邻体不贡献接触段；每个CONTACT邻体（Python membership=0）的**全部原始VE/EV关联**进入装配，包含t=0恰为原始段端点者。它们用于枚举物理接触点p及来源，不逐条生成半平面。不取∂E盖/剪裁盖，也不只取规范E\O输出边；中间坡度关联可能仅t=0接触，仍约束转动。
2. **按每个接触点p，而非按体对判凸性**：由两体在p的局部锥 `K_a(p),K_b(p)`（坐标原点移至p；边内点为半平面、顶点为顶点锥）精确求点自由平移锥 `F_p={t:(t+int K_a(p))∩int K_b(p)=∅}`。

| 点自由锥 | profile1处理 |
|---|---|
| F_p凸：边内点；正长度共线段端点（含平齐角点）；锯齿拐点；凸顶点落入凹顶点，无论有无边重叠 | 只取F_p的边界半平面（1或2条）作该点约束，N指向受力体；跨点/段取AND |
| F_p非凸：凸–凸顶点对且无共线边重叠（真VV） | 以禁止开贯入锥的两条边界半平面给两个模态，不能强行AND |
| 真VV的禁止开锥在实际twist空间内精确LP证不可达 | 析取冗余，可丢弃并保存不可达证书 |
| 真VV非冗余或未证 | ContactSet2标MECHANICAL_UNRESOLVED；v1不做模态枚举 |

特别禁止：平齐角点处，对方水平边的端点式原始关联**不得额外生成半平面**；关联保留为来源标签。体对纯平移自由锥即使凸，也可能掩盖该对某个接触点在转动时的真VV，不能代替逐点F_p。

每条极大共线正长度段在两端点各取该段法向一条；同一点与F_p导出的同向边界约束精确去重，不添加虚假端点约束。不同坡度不合并。每接触作用/反作用只记一次（a受+g、b受−g），(A,B)/(B,A)重复来源去重但保留全部标签。

真VV析取只有在**实际单体/多体twist自由度上，含转动、含端板dof_mask**，以接触点相对速度 `v_a(p)−v_b(p)`（各含平移与ω×r）经齐次归一化精确LP证明禁止开锥不可达，才可丢弃。不能用epsilon判开锥为空，不能以仅平移空间的不可达证据代替。

具名回归及预期：

| 场景 | 必须结果 |
|---|---|
| 两段折线锯齿互补接触 | 能解析，保留两段与端点，无虚假关联约束 |
| 无其他约束的角对角方块 | 装配与一阶可动性均MECHANICAL_UNRESOLVED |
| 角对角加实际twist空间内不可达的附加约束 | 丢弃冗余析取，附精确不可达证书 |
| G5平齐角点，N=3、L=3、h=P=1、等宽且上述掩码/载荷 | μ=0时承载力精确0；μ=1/4时精确1/2 |
| 同一体对内边接触+VV：A=[0,1]²；B=(0,0),(0,1/2),(−1/2,1/2),(−1,5/4),(0,1),(−1/4,2),(−2,2),(−2,0) | MECHANICAL_UNRESOLVED；A相对B的twist(1,1,3/2)可达(0,1)处禁止锥，不能用该体对凸平移锥吸收VV |
| 凸顶点落入凹顶点且无边重叠 | F_p为凹口闭锥，能解析，只取其两边法向 |

C3入口逐接触点冻结G1–G5的F_p类型/profile适用性。L1完整几何、profile内完整装配、任意组装体机械完备是不同声称；裸接触列表标 `completeness_unknown`，不能进入声称完整的认证链。有限σ_c/线性化M–N帽行是profile2，先T1b研究，不进C3。

### 4.6 LP 证书、阈值与敏感性

以下定义供T1a逐字引用；符号均指原始未缩放精确LP，不用显示矩阵或舍入射线代替证书。

#### 4.6.1 精确LP与UNBOUNDED证书

通用内核标准型为 `min cᵀx, Ax=b, x≥0`；maximize显式变号。物理承载力以下采用 `max cᵀx`，对偶 `min bᵀy, Aᵀy≥c`。共用精确LP核在C3-L1入口先交付；浮点只提基/状态，精确层在原始数据上核最优/Farkas/无界证书，失败则精确求解。派生力矩/活载列也精确。

**UNBOUNDED证书 = 精确可行点x0（A x0=b，x0≥0）+ 精确改进射线r（A r=0，r≥0，目标分量=1）**。承载力LP目标分量为α，即r_α=1；一般max目标等价归一化为cᵀr=1。二者由辅助精确LP求得，再以原始数据核等式/不等式。`lp.py`现有ray只是浮点视图，不作证书，不通过它反推“精确”分量。自应力 `A x_s=0, x_s≥0, (x_s)_α=0` 只可作夹持解释附加，不能替代改进射线。显示溢出、数学无界、几何不可动三者不同；无界不报伪有限承载力。

#### 4.6.2 ideal_exact_2d与法向方向

`limit_load_ideal_exact_2d`为Python新opt-in，`sensitivity_model=ideal_exact_2d`。每条已保留的点自由锥边界约束先固定受力体a：**N指向受力体a**；e取该约束对应的a在该接触处的CCW边向量，若来源为对方b的边，则取b的CCW边向量反向，即 `N=rot90(e_a)=rot−90(e_b)`。令 `T=e_a, g±=N±μT`，a受+g、b受−g；凹口两条保留半平面各取一组g±，不能任取另一入射边。

非黏聚二维下，未归一化生成元只是理想单位射线的正列缩放，不改锥/最优值；binary64顶点与μ下全部精确有理，故本模型 **V_cert=V_ideal**，不声称等于旧RN修正生成元模型。不得复用会单位化并RN法向的旧LimitContact来承载N；另立精确接触记录，原合同不变。legacy仅作对比，复刻 `limit.py:259–269` 搜索/平局/3D回退步长并有ULP例；anchored lift留三维或黏聚。

#### 4.6.3 稳定基与退化方向导数

力矩参考点o冻结为与参数无关常量，`do≡0`。稳定基：基满秩、原/对偶可行、`x_B>0`且全部非基约化成本≠0，并保持标签/骨架有效域。固定基公式用原始未缩放LP的exact_x与 **`lp.maximize` 的exact_y（Aᵀy≥c）**：

```text
dV = xᵀdc + yᵀ(db−dA·x)
B x'_B = b'−B' x_B                 Bᵀ y' = c'_B−B'ᵀ y
```

不用 `limit.py:667–689` 经cap变换后的lambdas/row_duals。`dg±/dμ=±T`；θ、幅值、波长、h为共享界面参数，两块及相关边界体给一致种子；传播接触点、T/N、力矩和荷载列，`d[(p−o)×g]=dp×g+(p−o)×dg`。活载系数在A中，不能只微分RHS。validity_conditions必含“L1接触骨架不变”。

不稳定时先求原最优面回收锥 `{r≥0,Ar=0,cᵀr=0}` 及对偶最优面回收锥。非零射线报 **differentiability=singular、reason=possibly_discontinuous**，附射线、不报斜率；枚举不含discontinuous，不宣称全部退化点都真的不连续。

两侧最优集均非空有界、V*=V有限时，Mills/Freund的最大化方向导数
`V′(d)=max_{X*} min_{Y*}[xᵀdc+yᵀ(db−dA·x)]`
用**一个精确LP**计算：

```text
V′(d) = max (dc)ᵀx + cᵀz + V*·s
s.t. Ax = b,  cᵀx = V*,  x ≥ 0,
     Az + b·s + (dA)x = db,  z ≥ 0,  s 自由。
```

(dA,db,dc)是给定方向d的精确种子；对±d各解一次，反向同时反号三者。记D+=V′(d)、D−=V′(−d)，正向坐标的右导为D+、左导为−D−；比较 **D+=−D−**，不是直接比较两次LP值。相等仅证明该查询方向的双侧导数一致，满足已声明有效域时该方向报smooth，否则one_sided/tie；保留tied_labels。

以上max_X min_Y属物理最大化模型；内核min标准型用min_X max_Y。映射 `c_min=−c_max, y_min=−y_max, V_max=−V_min` 后再变回输出。例 `min p·x1, x1+x2=1, x≥0` 在p=0沿正向导数为0而非1，不能把最大化公式贴到最小化问题。

G5一般是退化最优面，有限承载力敏感性不能强套稳定基公式，应走上述LP并核闭式；稳定基公式另用人工非退化例核。G5有限滑移/铰接切换值 `μ_switch=2h/(L−b)` 不是下一节定义的无界阈值μ_crit。

#### 4.6.4 critical_parameter的精确返回合同

固定几何、边界/荷载，μ_max为非负有限binary64。定义
`μ_crit := inf{μ∈[0,μ_max]: L3 UNBOUNDED}`，参数域中的μ按连续实数理解。`critical_parameter(assembly,param)`返回 **(status, μ_lo, μ_hi, attained, 证书)**，不得把μ_crit误定义成首次网格采样无界的μ。

- 普通有证括号：μ_lo附驱动≥1的精确机构或Farkas不可行证书，μ_hi附§4.6.1的精确可行点+改进射线。attained表示μ_crit处是否UNBOUNDED；只有精确阈值/开闭证书才能给true/false，普通非零宽括号尚不能判定时为None（JSON null）。
- μ=0已UNBOUNDED：μ_lo=μ_hi=0、attained=true，无下端机构证书，附0处无界证书。
- `[0,μ_max]`内恒有界（如所述G5）：μ_hi=None、reason=bounded_on_domain，附μ_max处机构证书；不声称域外永不无界。不可行端点另附Farkas并如实报状态，不伪装有限容量。
- 缺所需端点证书返回UNPROVED与原因，不硬造括号。闭式/精确阈值已知时另给exact_threshold并标开/闭；非binary64精确点只作有理/代数证书，不塞入double查询字段。保存临界基多项式，完整代数根能力仍后置。

**二分在二进有理数上进行，返回及送入C++的端点必须binary64可表示；只对param=μ执行。** 单调性来自精确摩擦锥随μ嵌套，与是否归一化无关；binary64舍入的认证生成元不保证嵌套。其他参数不假定单调。

二进有理数不自动等于可表示的binary64：精确中点若需超过53位，须在binary64网格选严格内点再精确查询，不能在RN后不缩区间还继续循环。相邻binary64端点已无内点时保留有效认证括号并报 `reason=input_resolution_limit`，不宣称已得精确阈值，也不把已有双端证据降成UNPROVED；attained仍按证据而非区间宽度决定。

#### 4.6.5 开/闭阈的隐函数导数

`dμ_crit/dp=−φ_p/φ_μ`，φ须定义在μ_crit处仍成立的那端证书上，证书基在临界点非奇异且 `φ_μ≠0`：

- **闭阈**（μ_crit处UNBOUNDED）：取改进射线基中于μ<μ_crit一侧越零的分量；以进入列e写 `r_e=1, r_B=−B⁻¹A_e`，记录所用分量/列/归一化，目标改进归一化另按§4.6.1核验。
- **开阈**（μ_crit处有界）：取机构基上 `φ_k=y_Bᵀw_k` 于μ>μ_crit一侧越零的非基接触约束，w_k为该接触列（目标系数为0；一般列slack写 `A_kᵀy−c_k`）。开阈时原侧接触力可发散，不能寻找不存在的原侧越零分量代替。
- `φ_μ=0`或证书基奇异报singular。多个越零分量逐一求斜率；同斜率仍保留tied_labels及有效方向，不同斜率报one_sided/tie，不由任意首个标签代替。

这是阈值导数，不是LP值包络，也不是“μ_crit对μ的导数”。尚无精确阈值/临界基证据时不从数值括号中点给认证斜率。L4主目标为μ_crit括号及其可证的隐函数导数；dV仅用于有限承载力区。

### 4.7 导数精度与核验

double 通道默认 `quality=approximate`，几何精确不意味着导数有误差证书；检查非有限、固定基残差及条件敏感性。需要导数符号签安全结论时另做有界/精确路径，不能加宽容差冒充认证。相对尺度与逐表达式舍入噪声控制误差，不用与问题无关的绝对阈值。

Python 精确固定基导数/解析例为主核验。差商只作收敛证据：先证明 `[p0,p0±Δ]` 在同一基与同一 L1 骨架内，再报告 convergence_order 或精确二阶差分的 O(Δ) 行为；不能以极小 Δ 数值相等证明导数。单通道与批通道比较数学通道一致性，不要求不同 W 的浮点执行路径逐位相等。

<a id="s5"></a>
## 5. API、分层与数据模型

### 5.1 L0–L5 与 H1 纯度

| 层 | 命名空间 / 目标库 | 职责 |
|---|---|---|
| 横切数值 | `eab2::numeric / eab2_numeric` | 私有 Int/Rational、构造、自检；未来过滤 |
| 横切精确优化 | `eab2::opt / eab2_lp` | 通用精确LP求解/三类证书及齐次可行性；C3-L1入口交付，L1/L3共同依赖，只依赖numeric，不依赖接触装配或statics |
| L0 | `eab2::geom / eab2_geom` | 环、点、特征、精确输入合法域 |
| L1 | `eab2::contact / eab2_contact2` | E/O、盖/原始段、首入、PD/rho、局部锥与一阶可动性 |
| L2 | `eab2::margin / eab2_margin` | 通用冻结接触/几何裕度；窗口由调用者给 |
| L3 | `eab2::statics / eab2_statics` | 在共用opt核上装配刚体平衡、边界DOF与显式接触模型；不依赖TIA |
| L4 | `eab2::ad / eab2_ad` | 片内模板和固定基/阈值敏感性 |
| L5 | `eab2::adapters::tia, ::dda` / 各目标 | 界面参数与场景、legacy 槽位、锚定路径解释、报告 |
| 外围 | `eab2::c_api / eab2_c` | C ABI、批量和错误边界 |

依赖为numeric→opt，contact2的VV冗余/可动性与statics各自调用opt，**不是L1依赖L3，也不让opt反向依赖ContactSet2**。目标是依赖边界，不强迫拆成多个DLL。内核不含 `df05/mtype/Tuple7/zsto/escape_height/TIA` 等域字段；通用摩擦、力矩、刚体不算域词。H1后 `dda_motion` 和 `model_robustness.dda_paths` 在 `adapters/bdda2d_motion.py`，DDAAffineMotion在 `adapters/bdda2d_affine.py`，三维逃逸在 `adapters/tia3d.py`；通用algebraic/se2/fit_affine留核心。旧ContactRecord的域槽位不能整体复制。

### 5.2 数据对象与不变量

| 对象 | 内容与约束 |
|---|---|
| `Body2 / Ring2` | 不可变顶点 bits、body/vertex ID、原环到 CCW 的映射、几何版本；不塞材料/legacy 状态 |
| `FeatureId` | body、维数、原顶点/有向边 ID、side；容器位置不是身份 |
| `Cover2` | VE/EV/VV 来源、精确域、全部标签；法向可集值；不冒充全部机械接触 |
| `EntranceSet2` | 凸胞与原始 VE/EV 来源段、惰性 T2b/边界、E/O 双三态；只归属一个 context |
| `FirstEntrance2 / ExitResult2` | 初态、path/model ID、精确有理/代数时间或平方距离、见证、全部 ties、显示状态 |
| `TieSet` | 按稳定 ID 排序的语义集合，别名映射；不按近似时间合并 |
| `LockCertificate` | §1.6 的 status/refinement、接触见证、局部胞/切锥、S¹ 覆盖、有理 r、分离或缝滑射线、拒签原因 |
| `Assembly2` | 体与固定体、邻接候选及完整性、profile ID、boundary_type/dof_mask、载荷；不能把“没有输入的邻体”默认为已排除 |
| `ContactSet2` | 不可变完整性标记、每个接触点F_p及保留边界半平面、全部原始段/端点来源、twist空间冗余证书、未解析真VV列表；不能按体对凸性或逐条原始关联生成约束，绑定Assembly/几何版本 |
| `LimitProblem2` | profile、原始 exact A/b/c、行列和作用反作用映射、恒定参考点、边界/荷载、可解析性；显示矩阵不是真值 |
| `LimitResult2` | 精确状态/值、x/y、Farkas、UNBOUNDED 时精确可行点 x0 + 改进射线（r_α=1，§4.6.1）、自应力可选、可解析性、display_status；不强迫非唯一 x/y 唯一 |
| `SensitivityResult2` | 模型、参数/种子、基/片、quality、可微性、导数/括号、有效条件；非有限/未解析不伪装成功 |

原始来源段用于机械装配；规范 E\O 骨架用于几何导出/差分。两者可以引用同一来源，但不能互相替代。

**Python/C++对齐词汇（r3冻结）**：

| 类别 | 逐字合同 |
|---|---|
| 边界 | `FIXED_BODY` / `FORCE_CONTROLLED_PLATE`；端板必附dof_mask，`(x,y,rotation)`中1自由、0固定 |
| 模型/完整性 | profile ID=`profile1`；sensitivity_model=`ideal_exact_2d`；裸输入完整性=`completeness_unknown` |
| 对象名 | 两侧均为 `Assembly2 / ContactSet2 / LockCertificate / LimitProblem2 / LimitResult2 / SensitivityResult2`，字段按本节及查询专节对齐 |
| 通用装配/精确模型/敏感性函数 | `assemble_contact_set2` / `limit_load_ideal_exact_2d` / `evaluate_sensitivity2` |
| 可微性 | `smooth / one_sided / tie / singular / unsupported / unresolved`；不增加discontinuous；回收锥异常为singular+reason=`possibly_discontinuous` |

`translation_lock_certificate/first_order_free_twists`是Python裁判名，分别对C++查询族`query_lock/first_order_mobility`；`solve_limit2`是求解门面，使用profile1时调用`limit_load_ideal_exact_2d`语义。跨语言映射显式记录，不另造`evaluate_sensitivity`别名。词汇冻结不等于提前冻结C3发布ABI。

### 5.3 C++ 宿主、线程与工作上限

C++20 门面用不可变 handle/view、RAII、span 和显式结果状态；只承诺同工具链 ABI。静态库与 DLL 都隐藏 Boost 后端。v0/v1 内部单线程；不同 context 可由宿主并发，但 Body/E/lazy 缓存只能归属一个 context，不共享未物化 E，context 本身不重入。生命周期由 context/结果释放 API 管理。

context 选项包含确定性上限：胞数、排布片数、整数位长、根细化次数；结果回显实际选项与触发原因。超过上限返回 RESOURCE_LIMIT，不能报 OUTSIDE/UNPROVED 的数学否定；墙钟取消另报 CANCELLED，不用超时改变判定语义。批量操作明定部分成功或原子失败，不受线程调度改变输出排序。

### 5.4 C ABI 与冻结时点

采用固定宽度整数、`struct_size/abi_version`、opaque handle、显式长度数组和 `extern "C"`；不用 C++ bool/异常/STL/编译器 enum 布局。所有异常在边界转状态；内存在分配侧释放，可两阶段查询所需 buffer 长度，不跨 CRT free。错误含 code/field/index，不依赖可变全局 last_error。

v1必须保留以下合同，C0先冻结其状态边界与能力探测语义：

- `call_status`与`mathematical_status`分离。成功计算得到无事件、OVERLAP、INFEASIBLE、UNBOUNDED或UNPROVED不是调用错误；UNPROVED不降级为成功的false，数值结果无效时不能填0占位。LockCertificate遇OVERLAP可成功返回非法初态拒签原因，但不伪造四状态中的一个。
- `get_abi_info`报告已实现能力、版本/结构尺寸和支持域；未实现能力明确标unsupported，相应调用返回UNSUPPORTED，不能返回占位时间/距离/承载力。v0缺rho/SE(2)/LP2是能力缺席，不是几何否定。
- 每个handle核所属context、类型与世代；跨context或已释放/过期handle拒收。失败不留下半初始化handle，不把部分分配泄漏给调用者；批处理已完成结果的所有权与部分失败协议显式。
- 种子与Jacobian的长度、维度、stride和缓冲区容量必须匹配声明；检查尺寸乘法溢出，任何不符拒收，不截断/补零。错误详情由context持有，其生命周期显式，禁止异常穿过C边界。

| call_status错误类（C导出可加统一EAB2_前缀） | 含义 |
|---|---|
| INVALID_INPUT | 非法数值/几何输入、尺寸/stride/种子不一致 |
| INVALID_HANDLE | 跨context、错误类型、过期或失效handle |
| UNSUPPORTED | 未实现能力/超出已声明模型域，非数学false |
| CONSTRUCTION_RANGE | 精确构造显示范围违反该字段合同；可保存exact结果的显示溢出则另用display_status |
| RESOURCE_LIMIT | 确定性工作上限耗尽，不是数学否定 |
| FP_CONTRACT | 浮点合同不满足，对应EAB2_FP_CONTRACT |
| INTERNAL_ERROR | 未预期内部异常/不变量破坏，结果不可用 |
| CANCELLED | 外部取消，与数学结论及确定性资源限额分开 |

**各 ABI 族在实现它的里程碑入口冻结工作签名**，不是 C0 冻结全部产品 ABI：

| 阶段 | 冻结的工作接口族 |
|---|---|
| C0 | 正式 `get_abi_info/self_test/context_create/context_destroy/context_get_error`；测试专用 numeric_batch |
| C1 | body/E 创建、membership/topology、本地原始接触查询、result_export_exact；差分用测试入口，不急于发布宿主 ABI |
| C3 | `query_lock(assembly,moving_body)`、`assemble_contact_set2`、`solve_limit2/limit_load_ideal_exact_2d`、`evaluate_sensitivity2`、`critical_parameter`、`first_order_mobility` |
| DDA / C4 | 相应时间/路径/出口族，只在能力实现入口冻结 |

C3 敏感性几何种子形状 `[n_params×n_vertices×2]`，行主序，绑定稳定顶点顺序，外加恒载/活载种子；共享界面参数不得给两侧矛盾种子。v0 数值/几何差分走 test-only 入口。**发布用稳定 C ABI 在 C3 末，对照真实 TIA ctypes 使用者冻结**；此后扩展只做版本化追加。D8 未批准宿主接入，v0 不冻结或加固 bdda2 主线接缝。

### 5.5 Python 调用与替代方案

标准库 ctypes 足够：显式绝对 DLL 路径、版本/结构尺寸核验、批量输入、exact JSON 导出、库侧释放。避免每个标签一次 FFI。pybind 能便利对象绑定，却增加第三方/解释器 ABI，当前无必要。C++ 内核、C ABI、ctypes+JSON 三类计时分别报告。

<a id="s6"></a>
## 6. 性能：现有证据与后续测量

### 6.1 原版规模盘点及既有 DDA 计时

原版标准库只读盘点 `fixtures/m4b_shadow/*.jsonl.gz`：15例×30=450帧，**25,295 条 post_df06 接触行**；逐帧中位54、P95/最大156，块数中位10、最大12；全块对候选中位45、最大66。行不是唯一块对/弹簧数。原盘点墙钟约0.192s，只是读取计数，不是几何测速。本次不重测。

下表耗时来自入库 [M4c fix_frozen_replay summary](../reports/codex/M4c_evidence/fix_frozen_replay/summary.json)，并非新 C++ 结果；每族30帧。接触行来自原版盘点。

| 族 | 块数 | 接触行 min/median/max | 历史族耗时 s | 族均值 s/帧 |
|---|---:|---:|---:|---:|
| bb03 | 11 | 40/40/40 | 10.4591843 | 0.348639 |
| bb05 | 4 | 10/10/10 | 1.0204482 | 0.034015 |
| bb06 | 4 | 8/10/10 | 0.9184597 | 0.030615 |
| bb09 | 12 | 58/58/61 | 5.0789732 | 0.169299 |
| bb10 | 12 | 74/74/76 | 11.3577177 | 0.378591 |
| bb12 | 11 | 48/48/54 | 8.1812175 | 0.272707 |
| bb50 | 2 | 1/2/2 | 43.5137831 | 1.450459 |
| bb51 | 11 | 54/54/54 | 116.4524805 | 3.881749 |
| bb52 | 11 | 54/54/54 | 117.1554784 | 3.905183 |
| bbF038 | 2 | 2/2/2 | 0.1894695 | 0.006316 |
| bbS038 | 2 | 2/2/2 | 0.1909663 | 0.006366 |
| bbv01 | 10 | 156/156/156 | 104.1924464 | 3.473082 |
| bbv01_dbv01a | 10 | 154/154/154 | 113.6438347 | 3.788128 |
| bbv02 | 7 | 88/88/88 | 55.7063141 | 1.856877 |
| bbv02_dbv02a | 7 | 88/88/88 | 59.5734046 | 1.985780 |

合计 **647.6341782 s 是 jobs=4 并发运行的各族墙钟之和**；批次墙钟177.274538s，不是单线程450帧耗时。计时含输入读取/hash、oracle、PD、P1及其他预测、raw/post映射、输出，不能冒充纯 PD_closed+P1 内核耗时。重族均值3.5–3.9s/帧；summary 没有逐帧时间，**没有可据此直接报告的耗时 P95/max**。旧10ms目标意味着至少百倍量级加速要求而非证据，本版撤为历史预算，不作门。

### 6.2 DDA 对账测量协议（后于 TIA）

C2余项+C3-D 报每步全部 post_df06 行的首盖/初态静态出口：包括规范化、域检查、块对复用、全部并列及映射回所有行；纯核计时为 **PD_closed+P1，rho 排除或独立列**。另报完整最多66候选块对的 broad phase/精确查询，不只检查 legacy 已有行。初态 CONTACT/OVERLAP 与从分离出发的事件分组，不称 P1 等于真实 DDA 轨迹。

每族给冷输入/热对象、纯核/ABI/端到端、中位/P95/P99/max、规模和错误状态。固定一个 P 核、记录核 ID、CPU/编译器/后端版本，至少多轮独立测量；以上历史结果未满足该隔离条件，不作跨机加速比。绝对阈值全部 **只报告、待 T1a/实际基线后定**，不阻塞 v0。

### 6.3 TIA 20×40 与现有紧配凹对测量

Claude 四路评审及其核实给出的 Python 紧凑 T2b 数据：

| 样本 | 原始 VE/EV 段 | 排布片 | 分母最大位长 | 紧凑 T2b |
|---|---:|---:|---:|---:|
| 40顶点紧配凹对 | 3,152 | 28,962 | 165 | 约10.0s/对 |
| 复核39顶点紧配凹对 | 2,966 | 23,246 | 155 | 约7.7s/对 |

参考 boundary 约1,240–1,700s/对是评审用片数×side_probes 单次成本的**估算**，不是全跑实测。本版据此选紧凑骨架导出 ∂E，不移植参考慢算法。旧31对E≤4s，相对T2b需约60–80倍；旧E+锁定≤5s及内存上限均不再作验收门。

WO-C1 的20块、每块约40顶点规模实验保留，但只报告：

- 对齐4×5非凸简单环，允许36–44顶点，完整190对 broad phase；**31条边邻接+24对角VV=55个接触对**全部计入，明确VV数量。不得把31当完整邻接；若形状改变邻接，按精确检测的实数报告，不硬套55。
- 对实际全部邻接构造可查询 E/O、∂E、E\O；对20个单动体/其余固定给 Shi 分类及 TRANSLATION_IMMOBILE/SEAM_SLIDING 细化（细化仅对 NOT_SEPARABLE_TRANSLATION；REMOVABLE_TRANSLATION 附精确分离射线）。它不是多体整体运动证书。
- 另列190对强制构造压力档，不与邻接档混分母。局部锁定不强制全局骨架；几何完整但机械未解析的对仍计入耗时并报状态，不能算完成了全链有限承载力。
- 冻结的 TIA 主工况为 **T1a G1–G5 扫描**，T1a 同时记录 Python 墙钟；真实工程截面为可选。LP 报 ≤60 平衡行、约1,500列及实际规模，而非旧512列预算。

TIA 全邻接E+锁定、多体LP、L4分别计时，报告冷构造/局部查询/内存。所有绝对性能阈值只报告、待定；若要设后续预算，由 Claude 据 T1a 实测另行确认，不能追认未经测量的百倍承诺。

### 6.4 最小统计与过滤失败比例

保留阶段墙钟、输入/接触/胞/片数量、最大位长、工作上限触发，以及实际需要的 LP 精确恢复次数。没有“至少25个计数器”的配额，也不以样本10⁵/10⁴作出口门。

v0 没有过滤器，过滤失败比例记 **N/A（未启用）**，不是100%失败。若之后启用，记录 eligible_calls、filter_accept、uncertain、exact_fallback：`uncertain/eligible_calls` 是过滤失败率，另报 `all_exact_fallback/all_calls`，强制精确派生点单列；精确零单列。同时测过滤/回退各自成本、统计 off/on 比例，不设强迫低回退率的正确性门。近退化100%回退允许，只要答案正确。

<a id="s7"></a>
## 7. Python 裁判与差分测试

### 7.1 Runner、H1 与失败处理边界

主保证是 Python 差分加少量元门；**不移植静态构造 AST 门、变异充分性框架、源码哈希绊线**。保留具名小反例和证书独立复核，不为测试再造一个产品。

Python裁判不得导入或复用C++的谓词、舍入或精确helper，**包括经ctypes DLL复用**；不以共享原语制造一致。ctypes只能调用被测实现并取出待比较结果，不能成为Python期望值路径的一部分。

未来 `tools/eab2_diff.py --dll <absolute-path> --suite <name>` 是独立 CLI，**不进默认 pytest 收集**；未给 DLL、版本不匹配、加载失败均硬失败，不能 skip 后绿灯。静态库用独立 C++ test executable；DLL numeric/query test-only 入口解决 ctypes 可达性。

与 H1：Python 默认快档/显式慢档不因 DLL 缺席被污染。产品里程碑报告分别列 H1 档与 eab2 suite；选定全档要求收集/执行节点多重集合相等、0 skip、0 failed；不豁免差分缺席。H1 合入后 re-key 路径/入口。本次文档单不执行这些未来命令，也不重跑全套 Python。

### 7.2 共享 eab2.case.v1 格式

JSON UTF-8，schema/version/case_id、输入来源、profile/path/model、查询参数、输入bits、期望状态/精确证书分开。输出显式分 `call_status / mathematical_status / display_status`（§5.4），不把UNPROVED写成false。bits为 `bit_cast<uint64_t>` 的**最高十六进制位在前、小写、恰16位**，与主机内存字节序无关；−0=`8000000000000000`，拒输入NaN/Inf。有理数用约分十进制整数串n/d，d>0，零统一0/1；代数证书记录多项式和指定根隔离区间。

```json
{
  "schema": "eab2.case.v1", "case_id": "two-triangles-touch",
  "profile": "geometry2d", "query": "membership",
  "bodies": [
    {"id": "A", "xy_bits": [["0000000000000000", "0000000000000000"], ["3ff0000000000000", "0000000000000000"], ["0000000000000000", "3ff0000000000000"]]},
    {"id": "B", "xy_bits": [["3ff0000000000000", "0000000000000000"], ["4000000000000000", "0000000000000000"], ["3ff0000000000000", "3ff0000000000000"]]}
  ],
  "translation_bits": ["0000000000000000", "0000000000000000"],
  "expected": {"body_state": "CONTACT"}
}
```

这是 A 动、B 固定的 E 成员 schema 示意；assembly查询还须边界/邻接/荷载，不把省略字段当默认固定体。标签引用稳定原ID、排序后的完整集合。来源/observable字段明确；hash只用于追踪输入版本，不作为源码变动就失败的绊线。T1a导出是正式语料；纯有理/腐蚀输入不偷渡入binary64 C ABI。

T1a先提交assembly/lock/first_order/limit/critical/sensitivity各查询族的schema草案，由Claude确认后再批量导出；其中参考点、荷载、boundary_type/dof_mask、profile1、接触点来源/F_p、期望状态/精确证书、attained及None/null、墙钟均明确。不能从这个membership示例推断其余字段；对象与函数名按§5.2，输入/证书编码按本节。

### 7.3 语料与覆盖而非配额

| 来源 | 覆盖重点 |
|---|---|
| 既有 construction/rounding 测例与边界矩阵 | 中点两侧、严重消减、次正规、溢出胞、整式一次舍入；一个随机生成器 |
| M3 global2d/2d/determinism/covers 测例 | L/槽/口袋、内缝、孤立点、平直、T2a弱覆盖与T2裁剪区别 |
| T1a G1–G5、现有 LP 证书族 | §4.5六个具名回归：锯齿、裸VV、twist冗余、平齐角点、同对边接触+VV、凸顶点入凹口；边界掩码、精确ray/Farkas、临界点、退化、非对称参考点 |
| `fixtures/bdda_df`、`m4b_shadow`、`m4c_motion/endpoints.json` | 后续15×30帧、raw/post映射、所有行/P1/初态出口 |
| `fixtures/m5a_se2`、m5a2及M5事件例 | C4五/六次、恒共线、重根、极近根、整窗非法；不提前装入C0 |
| 固定seed近退化生成 | 1ULP、近平行/共线、极窄边、正负零、极端指数；保留最小失败JSON |

分界点、非对称一般位置、尺度变化三类必须覆盖，不设数量配额。报告尝试/接受/非法域状态；不要只留下容易格。缺冻结导出则列缺失，不启动姊妹exe补数据。

### 7.4 比较口径与 C1 规范形

状态/有效性及语义标签集合逐项精确相等；一次RN构造逐位相等；有理时刻/平方距离约分后相等；代数时刻以精确有理判定或 gcd+指定根隔离证明等值，不以区间相交代替判等。LP比较值与证书/最优面不变量，不强迫非唯一x/y同分量。导数先比较模型、标签、状态，再按 §4 的精确裁判/收敛证据，不把普通Dual与Python jet逐位捆绑。

**C1 规范骨架由 Python harness 计算**，输入是双方 `result_export_exact`，内容为：

1. 合并全部来源标签后的极大相对开共线 E\O 段；来源变化处保留分层映射。
2. 孤立点与端点层。
3. 每个面状态样本及其精确边界关联，用于检查E/O和两种三态。

比较规范物理集合精确相等，不比较人造竖直剖分/cell序。Python membership/topology 精确复查 C++ 所有层样本；小M3外边界另对Python boundary。需要反向探测时加 test-only 精确有理查询，不扩发布输入域。规范形不能替代 §4.5 的全部原始接触段装配核查。

**TIA扇区oracle单独守独立性**：临界射线直接由每个接触点处两体各自的入射边方向（含反向）计算，不读GlobalEntrance2的胞/排布。每条临界射线及相邻临界射线间的有理内部方向均测试：可取L1归一化和，夹角≥π时取合适朝向的rot90。用严格位于已认证局部邻域的有理采样位移，样本点分类调用 `kernel2d.exact.polygons_overlap_exact`（1/0/−1）；**不用entrance_membership_exact**，因为它内部调用global_entrance的topology。两侧样本分类不共享被测胞；C1导出层复查可用membership/topology，不得把它冒充这个独立扇区oracle。

### 7.5 不一致处理

保存最小case、双方结果、模型/编译器版本与错误；先按C++缺陷停发该能力。先查bits/ID/ABI，再查exact算法/构造/导出接线；未来若有过滤则关闭重跑定位，但不修改Python迎合结果。加入具名语义回归，不只在结果后追加假数据。只有独立数学证据足以怀疑裁判时，另发Python修订单由Claude批准，保留旧期望及版本边界；禁止同时改双方直到相等。

### 7.6 少量元门与原值接线

元门针对**公开 TIA API**，不对每个内部helper扩张矩阵：

- 刚体运动/单位：非对称几何、几何/荷载分别缩放；在精确可表示且无范围损失的变换下核距离×s、法向/完整标签集协变、承载比按同载荷尺度不变。精确格采用90°倍数旋转、坐标反射、安全二进缩放/平移（大平移例 `|t|∈{0,2^10,2^17}`），逐坐标核RN为恒等；仍保留工程坐标/随机旋转作重新差分格。
- 凡分类依赖精确平行、共线或对称的构型，拟交C++的子集必须选**二进有理斜率与坐标，使RN为恒等**；RN后精确复核这些关系（平行用叉积=0）。不成立者只留Python并标明。随机旋转后只要求对新binary64输入与扇区oracle及按实际顶点的闭式一致，不要求分类/μ_crit不变；不能要求舍入抹掉的几何还不变。
- A/B交换、环方向/循环起点、body顺序、查询/缓存顺序规范后结果一致；字典序代表点不要求旋转协变。
- 力矩参考点冻结且非对称，整块平移使实际接触形心离开原点，以独立静力列核作用反作用/平衡；不得只改一个已被内部忽略的参考点参数。
- **每个导出的原值字段都来自 CertifiedValue**：测试故意令内部double/Dual临时值与RN目标有差异，验证导出未接错；单/批通道一致，原值零但导数非零不跳过，边界旗标真实。

阈值只相对并顾及舍入噪声；要求可证判定时仍用精确核验。语料全绿不是唯一退出门，还需 §8 的独立对抗核查与新鲜树复现。

<a id="s8"></a>
## 8. 里程碑、入口与验收

### 8.1 治理与排程

每个里程碑退出 = **Claude 安排的一名非作者对抗核查员，0 critical / 0 major + 纪律 D 新鲜树复现**。核查员不审自己编写的路径。按 H1 执行，不另加多路预审或相应计划余量。新鲜 checkout/worktree/克隆由所有者在获准流程安排；本单禁止这些动作，不冒称已经复现。只有退出后才升级产品能力声称。

唯一推荐主线：**C0 → C1 → C3-TIA → C2余项与C3-D合并为DDA对账 → 再定C4**。C0 与 T1a 并行，C1/C3 范围待 T1a 经 Claude 验收交付后冻结。综合报告旧位置出现 T1_A_DONE/T1_DONE，拆单后的正式交付标记采用 **T1a_DONE**，仅作为待交接条件，不宣称它现在完成。

备选先DDA能早看到熟悉回放，却把T3/PD/rho/P1延迟变成TIA阻塞，已不选。完整M5d提前需连同代数核/工期前移，D6已否决。三维须独立支持域和工单，不报机械翻译工期。

### 8.2 分项工作量与验收表

一名熟悉项目的实现者，加可用的Claude指派非作者核查员；含正常返修，不含等审批/理论新发现。所有性能列均是**测量报告，非退出阈值**。C1在此是移植阶段，不是WO-C1文档工单，也不是历史稳健C1证书。

| 阶段 | 范围/入口 | 差分语料与正确性退出 | 性能报告 | 非作者要核什么 | 人日 |
|---|---|---|---|---|---:|
| C0 / v0 | §8.4最小数值；与T1a并行 | C++数值测试+construction差分，全部选择语料执行，无DLL硬失败 | 构造/符号耗时，无门 | 先舍入的差分、二次舍入、ties、次正规、溢出胞、环境、内存释放 | 5–8 |
| C1 / v0 | 一般凹E/O、T2/T2a/T2b、局部0查询；T1a后冻结输入/接触接口 | M3族、层样本、规范骨架、近退化；小例boundary对照 | T1a工况与20×40规模；无门 | 内缝/孤立点、隐藏盖、原始段丢失、精确剪枝等号、表示不变量 | 18–26 |
| C3-L1 / v1 | **入口先交横切exact LP核/证书/齐次可行性4–6日**；再交原L1的锁定、非贯入锥、秩/双描述可动性、逐点完整接触集8–14日 | 既有LP证书族先过；T1a八项中1/2/5及§4.5六个回归（其中(d)在L1只核平齐角点F_p类型与无伪半平面，承载力0与1/2在C3-L3退出时核），未解析真VV不枚举 | 共用LP核与局部查询分开，无门 | LP证书、pair OR逻辑、零锥秩条件/双描述、实际twist约束、逐点VV冗余 | 12–20 |
| C3-L3 / v1 | 在共用opt上装配profile1、多体平衡、边界DOF与critical_parameter；不重复移植LP核 | G1–G5、无界x0+归一化射线、阈值开闭/域边界证书 | ≤60行/约1500列实际规模，无门 | 关联上界、端板掩码、力矩/作用反作用、无界目标射线 | 8–14 |
| C3-L4与交付 / v1 | ideal_exact_2d、固定基/方向导数、μcrit、真实ctypes消费、发布ABI冻结 | T1a敏感性、退化/回收锥、单侧/临界基、原值接线 | primal/多通道分开，无门 | raw x/y、模型缩放、do=0、基有效域、非唯一临界斜率 | 12–22 |
| C2余项+C3-D / v1 | T3、PD_closed/rho、P1、15例映射；rho裁判先另单 | 450帧、静态/运动ties、整窗非法、rho内缝；不运行姊妹exe | §6逐族PD+P1，rho单列，无门 | 初态/出口含义、二次根、raw/规范ID、完整候选与行映射 | 20–30，rho小单另计 |
| C4 / v2候选 | M5a/M5b、实代数、M5d其余名义；先满足§8.6入口 | 现有M5冻结族、5/6次、重根/恒等/近根；不含稳健向内线 | 各模型时间/根规模，无门 | gcd同根、Sturm符号、正分母、模型不混、根非规范身份 | 19–27，是否启动另定 |

前五行合计**首个完整C++ TIA结果仍约55–90人日**（5+18+12+8+12到8+26+20+14+22）。这是把4–6日通用LP核从C3-L3前移到C3-L1入口，不增加总量、不形成循环依赖。T1a另单Python裁判时间盒由Claude安排，可与C0并行；若延误则等待，不假装C++已具备裁判。这里不叠加旧多路审查余量，也不是日历完工承诺。

### 8.3 Python 裁判前置清单与 C1/C3 交接

**交接编号按§1.4.1的逐字八项；具体规范按r3订正条款**，尤其§1.6、§4.5–4.6、§5.2/5.4及§7。本表是签收索引，八项缺一列缺口，不能由C++自制替代裁判。T1a由Claude另发，若其工单编号不同须附交叉索引，不按裸编号猜测；C0不等它开工。

| T1a项 | 必交内容（与§1.4.1同编号） | 消费阶段 |
|---|---|---|
| 1 | `translation_lock_certificate`、四状态、两细化、局部锥覆盖及有理r | C3-L1，C1先冻结局部查询 |
| 2 | `assemble_contact_set2`，原始关联枚举/逐接触点F_p、端点射线、作用反作用/去重、twist空间VV冗余 | C1接口/C3-L1/L3 |
| 3 | `limit_load_ideal_exact_2d/evaluate_sensitivity2`，生成元方向、§4.6固定基/Mills单LP/开闭阈敏感性 | C3-L3/L4 |
| 4 | `critical_parameter`定义、binary64端点括号、attained、0/恒有界/缺证分支 | C3-L3/L4 |
| 5 | `first_order_free_twists`单体/多体、DOF掩码、满秩+归一化LP、精确双描述；v1不枚举模态 | C3-L1 |
| 6 | 每例eab2.case.v1导出与墙钟 | C1/C3差分和性能报告 |
| 7 | binary64输入域、界面一次RN共享、T接点规则、CONTACT复核/xy_bits、Python-only族隔离 | C1输入、C3全链 |
| 8 | §5.2冻结的边界/profile/完整性/可微性字符串、对象/函数名；§5.4调用/数学状态分离 | 全部入口/ABI |

入口冻结G1–G5每例边界/dof_mask、荷载、参考点、输入/schema版本，逐接触点列F_p类型（凸/真VV/冗余已证）及profile适用性，核Python敏感性符号。T1a以交付报告末尾的本设计SHA-256钉版，冲突停下报告，不单方面覆盖设计。T1b的路径first_penetration、腐蚀族、文献对照、有限σ_c不阻塞C++v1；A.2(c)仍Python-only。rho另发小裁判单后再进DDA阶段。

### 8.4 C0 详细范围——下一张 C++ 工单直接依据

**做什么**

1. **位置与构建**：在H1整合后的仓库 `eab2/` 子树，`include/eab2/c_api.h`；本单不创建产品子树，也不写cx-e2。`build_eab2.bat`仿只读bdda2/build.bat，VS CMake≥3.21/Ninja、MSVC14.44 x64。§3全部选项，禁/arch:AVX*、/GL。vendored Boost钉已验证版本与BSL，Int/Rational私有et_off。
2. **精确数值**：binary64无损解码，orient2d/cross/dot符号纯精确cpp_int；AABB精确界。不做浮点过滤；有界整数快路可后补，不依赖MSVC未提供的原生`__int128`。
3. **构造**：RN-even有理→double，次正规、跨binade、下溢失败、溢出胞必须maxfinite、阈值≥2^1024−2^970失败；sqrt、有理norm、单位分量、整式normalized_difference。八个公共construction函数全部与Python逐位一致，scalar_algebraic只实现compare→RN边界，用有理/平方根compare语料，不做Sturm。
4. **环境**：编译拒fast/contract宏；self_test检查FE_TONEAREST、FTZ/DAZ、MXCSR7–12屏蔽位、ties-even、符号零及一条收缩探针，失败EAB2_FP_CONTRACT，不改宿主状态。
5. **ABI**：正式导出get_abi_info、self_test、context_create/destroy、context_get_error。test-only numeric_batch输入bits或有理串，输出bits+状态，不进发布数值ABI。**C0同步冻结§5.4的call_status/mathematical_status、错误分类、能力探测、handle验证/失败清理及尺寸/stride拒收合同**，不是提前冻结全部产品ABI。bits规则见§7.2，分配侧释放。
6. **测试**：C++ test executable测静态库及中点/极端指数/次正规边界；独立tools/eab2_diff.py经ctypes实际调用DLL的numeric_batch，不进默认pytest，未给DLL硬失败。既有Python construction语料+边界矩阵+一个随机生成器；样本量/耗时只报告，不设配额和性能门。

**可选，时间盒允许才做**：CertifiedValue具体类型（原值来源规则已经确定，不因类型后补而放松）；最小Dual<W>（+−×÷、sqrt）及单/批通道一致性，不与dual.py逐位比较；Body2简单环合法域认证。未做的可选项由C1/C3接续，不占用核心5–8人日退出。

**不做什么**：浮点过滤器、clang/gcc、负构建矩阵、每TU清单、E/O、LP、发布产品ABI冻结/宿主接缝加固、性能门。

**退出条件**：C++单测与Python差分全绿，实际执行完选定语料；Claude安排一名非作者核查员重点核查：差分减法是否先舍入、二次舍入、次正规与溢出胞、ties、坏环境是否真拒绝、ABI内存释放；**0 critical/0 major**，再由获准流程做纪律D新鲜树复现。不能用本单文档复核替代它。

**工作量/并行**：约**5–8人日**，与T1a并行。正式命令参数/Boost具体版本在C0入口固定；本版不假装脚本、DLL或测试已经存在。

### 8.5 C3 全链退出检查

- T1a八项已签收，profile1边界和G1–G5清单冻结；几何、完整ContactSet2、模态可解析性串联，裸列表不冒充完整。
- 共用精确LP核先于L1完成；L1以原始关联枚举接触点、只从逐点F_p生成约束，§4.5六个回归全部符合预期（(d)的承载力数值在C3-L3退出时核）；未解析真VV的可动性也未解析、不枚举模态。秩/归一化LP、双描述和零锥组合证书齐备，不把L3无界读为互锁。
- L3固定端报阈值/模式，G5力控给有限值区与三类精确证书；σ_c/profile2不混进C3。
- L4用同一ideal_exact_2d原始LP，固定参考点，回收锥与方向导数、μcrit隐函数各守有效域。MECHANICAL_UNRESOLVED是诚实拒签，不计为完整受支持全链通过。
- 一名真实TIA使用者从C ABI/ctypes复跑，不装姊妹仓库/pybind；据此冻结发布ABI。性能只报告，0/0对抗核查及新鲜树为退出。

### 8.6 后置里程碑“入口前须定”

这些是接受但推迟的评审项，不在C0展开算法或装置。

| 入口 | 入口前须定 |
|---|---|
| 性能优化里程碑（T1剖析证明谓词为瓶颈后另立） | **N6**：仅RN下外扩区间，逐操作证明界/nextafter外扩，不用切舍入模式的默认Boost.Interval/CGAL策略。**N7**：绝对下溢项或指数域预检直接精确；无证明的浮点ZERO只作UNCERTAIN。**N8**：实际构造链次数/界，区分原始段4/2、比较≤6与构造端点比较8–10。**F12eng**：接受率、过滤/回退各自耗时、统计off/on成本分别报告，届时决定过滤性能预算，不把评审举例25ns改成门。每TU清单、负构建矩阵、clang/gcc支持一起重新定范围 |
| C4 | 代数事件多项式次数在**平方自由化之前检查**，M5a≤5/M5b≤6，拒七次可约输入借约化绕过支持域。**N9**：canonical存储规范化与positive_scale分离，Sturm链只乘正因子，伪除符号明确；x²+1无根反例。**N10**：root_identity不是规范身份，平方自由不等于不可约；gcd+指定隔离区间精确compare，精确排序后合并等值，不以结构hash作代数时间键 |
| DDA阶段 | rho小裁判单、PD/rho/沿路径出口字段区分、P1路径合同、15例计时拆分、适配ABI工作签名 |
| 三维/profile2 | 所有者另行立项；黏聚/有限压强/3D摩擦离散、对偶/导数模型、支持域和裁判先定 |

<a id="s9"></a>
## 9. 已定决策、风险与剩余入口事项

### 9.1 D1–D9 已定

| ID | 已定结论 | 落点 |
|---|---|---|
| D1 | rho不进v0；§3.10分类、非贯入平移锥、一阶可动性进C3-L1，T1a给通用裁判；rho/单对PD随DDA，rho另发小单 | §1.3–1.6、§8.3 |
| D2 | TIA主线；DDA在首个C++TIA结果后串行，不以P1延迟卡v0 | §8.1–8.2 |
| D3 | ideal_exact_2d，未归一化精确2D生成元，V_cert=V_ideal；legacy只对比，lift留3D/黏聚；L4主μcrit括号/隐函数，dV只有限值区 | §4.6 |
| D4 | 接受vendored钉版Boost.Multiprecision，封装cpp_rational、Int/Rational均et_off、附BSL，不用GMP | §2.5、§8.4 |
| D5 | 不接受绝对目标作门；T1a记录G1–G5墙钟后据此拟C++预算；20×40/DDA只报告 | §6、§8.2 |
| D6 | 不提前完整M5d；T1 A.2(c)依赖M5a的研究在v1保持Python-only | §1.4、§8.3 |
| D7 | 按H1：Claude安排一名非作者对抗核查员，0/0，加纪律D新鲜树复现 | §7.1、§8.1 |
| D8 | 不批准DDA主线接入；v0不冻结/加固宿主ABI，只设计后续接口与离线对账 | §5.4、§8.4 |
| D9 | 冻结profile1：刚体/小变形/无限抗压/非黏聚/恒μ/关联流动；精确未归一化2D端点射线；固定体或带dof_mask的力控端板；VV按**逐接触点F_p**凸性与twist冗余处理。固定端G1–G4主输出阈值/模式；有限σ_c为T1b profile2，不入C3 | §4.5–4.6、§8.5 |

### 9.2 最可能出错或最贵的五件事

| 风险 | 早期信号 | 控制与停止线 |
|---|---|---|
| E/O/原始段混用 | 内缝丢失、只取∂E、把联合不可分离称互锁 | T1a局部裁判、三种不同查询、完整来源段与规范骨架分离；未证不签 |
| 力学profile偷换 | 固定端画有限曲线、自应力当目标无界证据、VV强AND | 显式边界/关联上界、精确改善射线、凸性/冗余证书、G5有限例 |
| 导数模型与原值脱节 | RN射线平台上宣称理想梯度、形心随参、任选最优对偶 | ideal_exact_2d、原值CertifiedValue、do=0、raw x/y、回收锥/临界基裁判 |
| 凹E组合数/位长爆炸 | 约3k段变数万片、全局构造吞没局部请求 | 紧凑骨架、局部查询、确定性上限、T1a真实规模；不靠删约束提速 |
| 编译/范围与裁判缺口叠加 | C0先造过滤/多编译器平台，或没有Python接口先冻ABI | 最小MSVC纯精确C0、分阶段冻结、T1a入口、性能后置、独立核查 |

### 9.3 仍需在入口决定（不是重开D1–D9）

Claude安排T1a具体工单/验收与新鲜树执行人；C0钉Boost具体版本、VS工具路径和命令；T1a后冻结G1–G5实际边界/载荷/输入版本及C1/C3工作接口；以实测拟性能预算；DDA前发rho裁判单；是否启动C4、三维或profile2另行批准。现阶段没有需要再询问才能完成本设计修订的决定。

<a id="sources"></a>
## 10. 来源与核查口径

### 10.1 本地一手输入（只读）

- **S1 理论归属**：[shi_comparison_20261019.md](file:///D:/eab-wt/cx-e2/reports/codex/inputs/shi_comparison_20261019.md)，按对照归属，不沿用旧优先性宣传。
- **S2 评审输入与H1**：`eab2_review_synthesis.md`、`eab2_review_lenses.json`、`v2check_issues.txt`及`t1a_check/`是Claude提供的**评审输入，不在仓库**；不保留本机临时目录链接。关键决定、数据和r3精确定义已写入正文，本轮未运行评审LP脚本。[H1纪律](file:///D:/eab-wt/cx-e2/AGENTS.md)、[H1搬家清单](file:///D:/eab-wt/cx-e2/reports/codex/H1_evidence/P1_relocation.md)为只读分层依据。
- **S3 二维集合**：[global_entrance.py](../src/eab/kernel2d/global_entrance.py)：237–300数据、**320–377双三态**、406–568边界/骨架、592–634首入/PD；[M3设计](m3_global_entrance_design.md)。行号对应当前设计基线，H1后按符号重定。
- **S4 数值**：[predicates.py](../src/eab/predicates.py)、[construction.py](../src/eab/construction.py)、[numeric_domain.py](../src/eab/numeric_domain.py)、[dual.py](../src/eab/dual.py)。以公开构造合同为逐位裁判，不把dual兼容jet扩大成移植目标。
- **S5 路径**：[motion.py](../src/eab/kernel2d/motion.py)、[algebraic.py](../src/eab/kernel2d/algebraic.py)、[M4c](m4c_motion_entrance_design.md)、[M5a](m5a_se2_design.md)、[M5b](m5b_motion_theory.md)。M5稳健材料仅历史，不代表排程。
- **S6 力学**：[lp.py](../src/eab/lp.py)、[limit.py](../src/eab/limit.py)、[limit_multi.py](../src/eab/limit_multi.py)；新opt-in/完整装配裁判由T1a另交，不冒称现有covers转换已满足。
- **S7 姊妹参考**：[types.hpp](file:///D:/b-DDA/bdda2/core/types.hpp)、[ad/params.hpp](file:///D:/b-DDA/bdda2/ad/params.hpp)、[ad/gradient.hpp](file:///D:/b-DDA/bdda2/ad/gradient.hpp)、[build.bat](file:///D:/b-DDA/bdda2/build.bat)。只借鉴纪律/构建，不复制、不改写、不建立依赖。
- **S8 规模/时间**：[15例manifest](../fixtures/m4b_shadow/manifest.json)、[M4c计时summary](../reports/codex/M4c_evidence/fix_frozen_replay/summary.json)。39/40顶点数据来自S2工程路与对抗核实；正文区分直接计时、估算及并发族时间之和。

### 10.2 保留的官方技术资料

以下是第一版已核查的技术依据，本轮按已给评审修订，没有重新宣称核查最新版本：

- [Shewchuk精确谓词](https://www.cs.cmu.edu/~quake/robust.html)、[x87说明](https://www.cs.cmu.edu/~quake/robust.pc.html)：扩展算术与机器前提，不提供本设计所有表达式的现成界。
- [Boost整数后端](https://www.boost.org/doc/libs/latest/libs/multiprecision/doc/html/boost_multiprecision/tut/ints.html)、[BSL1.0](https://www.boost.org/LICENSE_1_0.txt)；实施用钉版副本，不以latest为构建输入。
- [GMP许可](https://gmplib.org/manual/Copying)、[平台说明](https://gmplib.org/manual/Notes-for-Particular-Systems)、[MPFR](https://mpfr.org/)、[CGAL许可](https://www.cgal.org/license.html)、[CGAL依赖](https://doc.cgal.org/latest/Manual/thirdparty.html)：供候选取舍，具体分发由所有者核合规。
- [MSVC /fp](https://learn.microsoft.com/en-us/cpp/build/reference/fp-specify-floating-point-behavior?view=msvc-170)、[fp_contract](https://learn.microsoft.com/en-us/cpp/preprocessor/fp-contract?view=msvc-170)、[预定义宏](https://learn.microsoft.com/en-us/cpp/preprocessor/predefined-macros?view=msvc-170)。
- [Clang手册](https://clang.llvm.org/docs/UsersManual.html)、[GCC优化选项](https://gcc.gnu.org/onlinedocs/gcc/Optimize-Options.html)：将来跨编译器入口再核，不是C0已支持声明。

### 10.3 原工单覆盖索引

| 原WO-C1项 | 落点 |
|---|---|
| 1范围/顺序 | §1、§8；TIA优先，rho与DDA后置 |
| 2数值/大整数/实代数 | §2；纯精确首版，过滤入口§8.6 |
| 3编译/自检 | §3、§8.4；MSVC最小合同 |
| 4可微“片+划” | §4；认证原值与连续导数分轨 |
| 5API/分层 | §5；TIA对象、context、分阶段ABI |
| 6性能 | §6；数据与计时边界，不设绝对门 |
| 7差分/元门 | §7；规范骨架、独立CLI、少量公开TIA元门 |
| 8里程碑 | §8；T1a前置、C0可直接下单 |
| 9风险/决定 | §9；D1–D9已定，入口事项另列 |

本版逐项评审落点及文档核查结果见 [C1交付报告](../reports/codex/C1_report.md)。
