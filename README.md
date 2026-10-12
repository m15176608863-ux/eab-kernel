# eab-kernel

> **WO-R14FIX（2026-10-13，待独立复审）**：5 条 G6N major 的修复与同类扫描见 [报告](reports/codex/R14FIX_report.md)。现行支持域按 [物理量分项](docs/r14fix_design_sync.md)：摩擦 μ∈[0,2^20]，最终射线独立认证圆锥包含；精确角度/一般幂参数先检查无损 binary64，文本先精确解析再查 RN 输出域。撤回一般承载相对余弦界，保留有条件的理想模型集合夹逼。M0 所有者决定、M4a 离线边界不变，不宣称独立 G6 通过。

> **WO-R13FIXb 数值支持域（2026-10-13）**：判定继续对任意有限 binary64 / int / Fraction 精确；构造按声明域保证 RN-even 或所列误差界，超域须抛含量名的 `ConstructionDomainError`。基础近似输入域为非零 `[2^-400, 2^400]`，但仍需核输出范围；已有全域正确的代数构造不收窄。合同与推导见 [支持域定义](docs/exact_predicates_plan.md#r13fixb-numeric-domain)，实现未闭合项见 [138 项清单](docs/r13fix_construction_inventory.md) / [R13FIXb 报告](reports/codex/R13FIXb_report.md)；不能据此声称全 API 已满足该合同。


> **WO-R13FIX 当前定位（2026-10-13）**：静态工具及子集准入是辅助代码检查，不是安全保证；公开构造量与独立有理参考的极端尺度逐值差分是主保证要求。类生命周期漏传播与事件返回字段脱钩已补门；全部 API 的未覆盖项不能以静态零诊断代替。以 [本轮设计同步](docs/r13fix_design_sync.md) 与 [R13FIX 报告](reports/codex/R13FIX_report.md) 为准，下文旧轮次“静态保证/默认拒绝”不能当作现行安全承诺。M0 所有者决定、M4a 离线边界和外部正本只读约束不变。

> **WO-R12FIXb（2026-10-12，工作树重做，待独立复审）**：静态构造门改为按构造数据流准入，支持已知 int/Fraction、统一构造调用及不流入禁止构造的普通 float 运算。撤掉 R12FIX 的整库依赖冻结；例外仅锁 AST 站点和所在函数源码，未知动态/高阶形态仍默认拒绝。例外压缩是否达到 200 条、近似旧路径与人工排除范围以 [R12FIXb 报告](reports/codex/R12FIXb_report.md) 为准，不能把扫描零违例当作任意 Python 的数值证明。可维护性、实际内部变异、原 11368 节点保留和全套实测见报告；现行合同见 [设计同步](docs/r12fix_design_sync.md)。R12FIX 旧报告是历史证据，其全库冻结方案不再适用。本单不宣称新鲜 worktree 或独立 G6 通过，M0 所有者决定和 M4a 门不变。

> **WO-R11FIX（2026-10-12，工作树修复，待独立复审）**：输入实际为 G6K-K01、K02 两条 major；本轮修复与全部验证证据以 [R11FIX 报告](reports/codex/R11FIX_report.md) 与 [本树设计同步](docs/r11fix_design_sync.md) 为准。静态构造门合流 callable/绑定/舍入来源；数值谓词不得把任意精确输入的转换误差忽略。M0 已按所有者决定退出，独立正确性复审并行继续；本单不变更该决定、不宣称独立 G6 通过、不回写外部只读正本，保留 M4a 门。

> **WO-M4a / M0 所有者决定（决定日期 2026-10-12；工单原误写 10-17，已订正）**：M0 按“连续四轮独立复审无 critical”口径退出，转入 M4。第六至十轮 critical/major/minor 分别为 **1/7/4、0/9/2、0/6/0、0/4/2、0/4/1**；剩余 major 在独立复审线上继续修。本单不重新核验这些轮次、不触碰 `cx-e2`/`g6*`。这是所有者调整的 M0 退出口径，不等于原 G6 的 0 critical / 0 major；下面保留历史状态。M4a 只做离线影子数据与接缝核验，不修改 b-DDA。结果见 [M4a 报告](file:///D:/eab-wt/cx-m4/reports/codex/M4a_report.md)。

> **M4a 实测（2026-10-12）**：15 输入配对 × 3 步、45 帧离线影子；未知分类 0，三处必需内部变异均被目标断言捕获；全套 `10923 passed in 1191.84s (0:19:51)`。门为 `tests/test_m4_bdda_shadow.py`，VV 读取身份修复由 `tests/test_m4_bdda_vv_reader.py` 看护。使用显式域窗口内的静态局部盖，不是本步真实运动首入，不是力学轨迹等价；`BDDA_DETECT` 只提案、未改姊妹，也未执行新鲜 worktree/独立 G6。差异见 [台账](file:///D:/eab-wt/cx-m4/docs/m4_difference_ledger.md)。

> **WO-R10FIX（2026-10-12，已验收合入 `5591702`）**：G6J-J01～J05 的修复、同类扫描及验证见 [R10FIX 报告](reports/codex/R10FIX_report.md) 与 [设计同步](docs/r10fix_design_sync.md)。外部设计正本保持只读。

> **WO-R9FIX（2026-10-12，已验收合入 `0e9ef93`）**：处置 G6I-01～06：二维共线链首入先核有限源特征域；实体凸性/凹棱及公共法锥按声明三角拓扑；壳方向按嵌套分量核验；精确到浮点统一构造并有独立中点证书与 AST 门。源单盖描述符仍是独立窄域，不等于折面实体完整法锥。设计同步见 `docs/r9fix_design_sync.md`；红绿/变异/全套见 `reports/codex/R9FIX_report.md`。本单未新建 worktree，不是独立六路 G6，不宣称 M0 退出。


> **WO-R8FIX（2026-10-12，修复留树，待独立 G6）**：本轮 G6H 确认 6 条 major；逐条红绿、内部变异、旧门对照、同类扫描和全套实测见 [R8FIX 报告](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_report.md)。当前合同补充见 [R8FIX 设计同步](file:///D:/eab-wt/cx-e2/docs/r8fix_design_sync.md)。本树同步不等于只读外部正本已回写；M0 退出状态不升级。

> **WO-R6FIX（2026-10-12，修复留树，待独立复核）**：第六轮确认 12 条（1 critical / 7 major / 4 minor），原审查见 [G6F 输入](file:///D:/eab-wt/cx-e2/reports/codex/inputs/G6F_report.md)。修复、修前红/修后绿、内部变异、同类扫描和完整测试结果统一见 [R6FIX 报告](file:///D:/eab-wt/cx-e2/reports/codex/R6FIX_report.md)。本次本树测试不等于独立六路 G6，且按工单禁止创建 worktree；M0 退出状态不升级。


> **E5 已完成（窗口为局部贯入厚度口径，WO-PERF 所有者定稿）**：保留兼容参数名 `contact_window`；它不是整体最短分离平移的欧氏贯入深度 PD 阈值。贯入相触报告只承诺“六轴非贯入证书 ⇒ rho ≤ w”或“星核薄壳证书 ⇒ 每个重叠区位于径向厚度 ≤ w 的壳内”。这里 `rho = inf{||d||₂ : int(A+d)∩int(B)=∅}`；正本 01 的 `PD_closed = inf{||d||₂ : (A+d)∩B=∅}` 是闭集完全分离的下确界，两者对一般闭表面不相同，六轴不保证 PD_closed≤w；报贯入也不推出 PD_closed>w。六轴及 L1 壳构造依赖坐标系，斜向短脱离可能漏，不保证旋转不变性。默认精确路径不使用该政策。闭合空腔反例门 `test_r7fix_docs.py::test_g6g09_tight_closed_cavity_distinguishes_rho_from_pd_closed` 固定两种口径；其他独立 oracle、限制反例与内部突变门见 [窗口门](file:///D:/eab-wt/cx-e2/tests/test_perf_contact_window.py)，定稿与性能证据见 [WO-PERF 报告](file:///D:/eab-wt/cx-e2/reports/codex/PERF_report.md)。此“已完成”指工单契约项，不冒充未经执行的独立六路 G6。


> **WO-E5b（2026-10-12，工作树实现，未经 G6）**：默认按给定数据精确判定，`contact_window=None` 不含隐式 ctol；显式窗口是调用方的局部贯入厚度报告政策（非 PD）。精确运动事件与证明读取 `exact_height` / `exact_offset`（互锁）和 `exact_t` / `surface_label`（首入），不能将浮点显示高度再逐顶点舍入后当作同一证书。当前验收、窗口数学定义、全部原格迁移与残余限制以 [E5b 报告](file:///D:/eab-wt/cx-e2/reports/codex/E5b_report.md) 和 [三维设计](file:///D:/eab-wt/cx-e2/docs/exact_3d_design.md) 的 E5b 节为准。下文 E5a/E5a2 退出段是历史记录，不是 E5b 当前结果。


**把 DDA 的接触层重写成一个以石根华入口块 E(A,B) 为理论内核的、域无关的接触引擎。**

不是又一个 DDA。DDA 是它的第一个域适配器，也是唯一有 legacy 可对账的那个——所以从它起步，
但内核一层不许知道自己在算岩石。

- 设计正本：`D:\E(A, B)\07 程序设计·统一接触内核方案.md`
- 理论正本：`D:\E(A, B)\01 E(A,B) 理论内核·精细版.md`
- 去岩石化正本：`D:\E(A, B)\03 广义接触·裕度即接触与理论内核的去岩石化.md`
- 纪律：`AGENTS.md`

## 为什么要重写

现存六份平行接触实现（`df.c` / refkernel / cpp 一代 / bdda2 / `tf.cpp` / bdda3d，加导师线 DDA4.x）
**没有一份能给另一份当裁判**：要么共享同一段历史逻辑因而共享同一个缺陷，要么不输出可对账的中间量。
三维接触枚举尤其**没有任何独立 oracle**。而且这六份全都把"接触几何"与"岩石本构"焊在一起，
拆不开就出不了岩石。

## 分层：什么是域无关的，什么必须可插

| 层 | 内容 | 域无关？ |
|---|---|---|
| **L0 体与位形空间** | 多面体/多边形；允许哪些运动（平移 / SE(2) / SE(3) / 仿射可变形 / 关节空间） | 结构无关，**位形空间本身是域给的** |
| **L1 入口块 · 盖机器** | E(A,B)=a₀+B⊕(−A)、法锥有效性、四类盖 + 低维盖、首入裁决（**订正（2026-09-24）**：这是该层应有的内容，不是已交付；**2026-10-10 起**二维、三维各有按运动方向定义的第一版（M2，有门、未经独立重审，见下表 L1 二维 / 三维行））、完备性门 | **是。这是内核，不许出现任何域词汇** |
| **L2 裕度层** | 膨胀：`E(A_δ,B) = E(A,B) ⊕ B_δ`。安全距离变成接触量；球膨胀 = C^{1,1} 正则化，消灭顶点处的法向集值 | **是。这是"去岩石化"的铰链**（原文"尚未实现"——**订正（2026-09-24）**：已于 09-20 落地，现状见下表 L2 行） |
| **L3 互补 · 求解层** | LCP / 优化；**本构由域插入**（岩石的摩尔-库仑、夹具的摩擦模型、游戏的恢复系数） | 框架无关，本构是域的 |
| **L4 可微层** | 多通道对偶；"片 + 划"——盖给分划，片内解析求导 | **是** |
| **L5 域适配器** | DDA（岩石）、TIA 互锁设计、护面块体、码垛稳定、caging、机器人接触… 每个域在这里提出**自己的问题** | 否，这里就是域 |

关键是 L5:**盖机器是共享基底，"问题"坐在上面。** 岩石问"这个接触传多少力"；
互锁设计问"荷载传递比是多少"；caging 问"自由空间的连通分量有不有界"；
码垛问"这一垛稳不稳"。同一台机器，不同的问题。

## 诚实门：不是所有领域都配得上这套理论

**2×2 选题判据**（03 号文档）：任务要**骑在（广义）接触边界上** × 接触**模态要紧**。
两条都满足才值得做。公路自动驾驶两条都不满足（需求侧全栈只消费距离/最近点/相交三种弱谓词），
已判死。L5 是一个域**证明自己过了 2×2** 的地方，不是许愿池。

> **⛔ 2026-10-10 G6 第四轮（第三轮修复之后，a72acb7）：仍未通过——45 条原始 → 40 条去重，40 条全部确认（1 critical、14 major、25 minor）+ 5 处盲区。** 见 `reports/g6d_20261010.md`。critical 是二维成员判定把短边（T 形顶点边）的原始法向当整个 E 的半平面（第三轮那句话"判据要加被测方向自己的噪声"的第四处遗漏）；major 集中在 G0 三票门的"两把尺"（凸包按 1e-12·L 压平、局部侧按舍入噪声判，说不清只豁免一边）、多体自校验在共同形心判定、近平行棱的最近点参数（盖路径与 oracle 同一公式同错）。全部已在 699f481 与其后一提交修复、配门与突变体（例外如实记在报告末节）。**第五轮待跑**（增设"未读文件"与"设计正本 07"两路）。
>
> **被审对象的位置（第四轮盲区 1）**：`main` 与 `origin/main` 冻结在 b6468f3（09-24，G6 第一轮未通过）直到 M0 退出；M0.2 起的全部集成在本地分支 `m03-limit`（无远程，gh 未登录）；每轮审查针对一个写明的 HEAD（第三轮 2090944、第四轮 a72acb7），之后的提交不属于该轮。
>
> **⛔ 2026-10-10 G6 第三轮（M0.3 之后，2090944）：仍未通过（28 条全部确认：12 条 major 级、16 条 minor；完整性批评者另记 2 处 major 级盲区）。** 见 `reports/g6c_20261010.md`。根因三类：三维几何核的逐特征噪声政策漏了三项（EE 候选法向与棱×棱候选要除以 sinθ、低维盖见证方向自身的 fl/|v|、棱参数带的杠杆项）；裕度层钳零与收表两把尺不一致留下一个贯入窗口；二维核的凸性前提与平行边合并各有一处朝向/短边依赖。全部已在 4922c30 与 9e88720 修复，每条配门并做了突变体检验（记录在报告末节；三处如实记为例外：凸包待查池复查没有能让它变红的输入，G0 票二的"说不清优先于异常"与"候选噪声除以 sinθ"单独撤回不红、同时撤回才红，票二第二候选判据与带冗余）；不变性元门加入了本轮 major 所在的四对几何。**第四轮待跑。**
>
> **⛔ 2026-09-27 G6 第二轮（M0.2 之后，814fdea）：仍未通过（2 critical、8 major、22 minor + 1 处 major 级盲区）。** 见 `reports/g6b_20260927.md`。两条 critical 都是 M0.2 修容差时在三维几何核里引入的回归（长度/角度/无量纲量混用、用全局最短棱折算角度容差），裕度层在块体有一条极短棱或间隙 ≤ 1e-9 m 时会丢掉真实的最近接触、答"安全"。LP 层经五轮复核改为对给定数据精确，这一轮未发现静默给错。下一步 M0.3：几何核改为精确谓词。**下表所有 ✔ 在 M0.3 修复并通过 G6 之前一律不可信。**
>
> **⛔ 2026-09-24 G6 独立重审：未通过（6 critical、7 major、18 minor + 3 处 major 级盲区）。** 见 `reports/g6_20260924.md`。
> 系统性根因是**绝对容差遍布内核、而测试从不平移/旋转/放到工程坐标**：SI 单位的百米岩块报承载力 0、工程坐标下报承载力 ∞、旋转的平行面块对距离返回 ∞、等高横梁交叉贯入被判分离（裕度层重新 fail-unsafe）。另：G2 的 "legacy" 实为 3-b-dda 手写期望清单（报告标题与措辞 09-27 已订正）；G4 的真值口径有误，按 df22 终判重算后"砖一静态版关闭"仍成立（5/61），读法 2、3 的数字已订正（`reports/g4_multistep_first_datum.md`）。**下表所有 ✔ 在 M0.2 修复并再次通过 G6 之前一律不可信。**

> **状态声明（2026-09-24，M0 修复已合并；测试基线 8376ec2，main 现为 094861c——其后只改了 `src/eab/limit.py` 的模块文档）**：09-21 独立审查确认的 31 条缺陷（2 critical + 15 major + 14 minor）
> 已在 M0 的四组分支上修复并合并（b747c3b / ddec237 / 822f0cd / b1bbd27）；每组合并前都有一名独立验证者对照代码复核过，
> 但**复核结论并不全是"通过"**，合并之后主干上也还有没经过复核的提交——见下面的例外。
> 修复过程中还发现并修掉了几处**审查清单之外**的缺陷（见下文"审查外发现"）。
> **但 G6 独立重审还没有跑。** 在它跑完之前，下表 ✔ 的含义是"修复者声称 + 验证者复核 + 括号里那条测试看护"，
> **不是"重审通过"**；没经过验证者复核的在该处另行注明。`docs/plan_20260921.md` 第 36 行原文是：
> "**声称在 G6 之后才许进 README**"。按这条规矩，**下表是 M0 的状态记录，其中的 ✔ 都是临时标记，要等 G6 之后才算进入 README 的声称**；
> 下表里有一批旧表没有的 ✔（例如 L1 三维"凸块 G0 三票"、L1 二维"凹块 G0 已重做"），它们同样只是临时标记。
> 完全没有经过任何复核的那一项（跨层行）不打 ✔，写"有门·未经任何复核·待 G6"。
> 例外（以下或复核未通过、或没有复核）：
> - **C17**（G2 对棱-棱接触失明）：经过两轮独立复核——第一轮 VERIFIED，g4 组合并（b1bbd27）前的第二轮结论是 NO_TEETH（"无牙"），
>   这一组是带着 NO_TEETH 合并的。补牙的 6f157ac 是合并之后直接提交到 main 的，**没有经过独立复核**，
>   只由补牙者本人和本次文档核对用同一变异确认会红（变异与结果见"审查外发现"）。
> - **端到端门**：b26d7f5 是四组合并之后直接提交到 main 的，不属于任何一组；8376ec2（把它的破坏模式断言改成读对偶面不变量、
>   对角推补上 μ = √2、新增 LP"答对或抛错"契约门）同样直接进 main。两者都**没有经过任何独立验证者复核**。下表跨层行即此项。
> - **77600c9**：直接进 main、未经复核，只重新生成 `reports/bb52_g1_g0.json` 与 `reports/tia_sensitivity.json` 两份机读报告。
> - **094861c**：直接进 main、未经复核，只改 `src/eab/limit.py` 的模块文档（诚实条款："是否转动"不是对偶最优面的一般不变量，
>   门的指向改到 `test_failure_mode_is_read_off_invariants_of_the_dual_face`），不改代码与测试。
> - 合起来，b1bbd27 之后主干上 6f157ac、b26d7f5、77600c9、8376ec2、094861c 五件都没有经过独立验证者（`git log --oneline --no-merges b1bbd27..094861c`）。
>   **订正（2026-10-10）**：这是 09-24 写时的口径；此后 G6 第一轮（09-24，`reports/g6_20260924.json`）、第二轮、第三轮的镜头都读过这几件涉及的
>   代码与门并报出缺陷（见各轮报告），"没有经过任何独立验证者"保留作历史，不再是现状。

## 现状（2026-10-10）

**E5a 验收订正（WO-E5a2，2026-10-12）**：所有者明确系统临时目录不属于姊妹仓库/其他工作树保护红线，撤销“整单作废”的判断，将 E5a 按部分完成提交为 `5b09ea3`（所有者独立复跑 7907 passed / 1829 s）。旧报告保留作历史证据，不删除旧临时文件。本单在该提交上续作；具体修改、实测和未达项以 `reports/codex/E5a2_report.md` 为准，未过 G6。

全套 **6717** 个测试全绿（2026-10-10，G6 第三轮全部修复后的工作树 9e88720；09-24 时为 1209，M0.2/M0.3/M1 的不变性元门与分辨率门把数目抬到这里；
`python -X utf8 -m pytest -q -p no:cacheprovider`）。
**复核覆盖（2026-10-10，第四轮 claims-vs-code 镜头核对后逐文件如实列）**：下表里写着"未经复核·待 G6"的行，按两份报告的 coverage_notes
实查——**有逐行读的记录**：`tests/test_margin.py`（g6b theory-fidelity，"most of"）、`tests/test_frozen_lowdim.py`（同上）、
`tests/test_interlock_sensitivity.py`（只有陡折门）、`tests/test_end_to_end_cb2.py`（g6b gate-quality；g6c 只执行）；
**只有执行 / 变异子集的记录、无人逐行读**：`tests/test_dual.py`（L4）、`tests/test_interlock_escape.py`（L5 TIA）、
`tests/test_covers3_membership.py`（L1 三维票一/票三）、`tests/test_geom3_merge.py`、`tests/test_geom3_face_polygon.py`（L0）。
第三轮盲区 gaps[1] 只闭合了一部分；余下五个文件第四轮也没读到，**第五轮的 unread-files 镜头逐行读完**并各做了变异（`reports/g6e_20261010.md` 的覆盖说明）——由此新增的门：冻结 EE 朝向（`test_frozen_ee_sign.py`）、互锁候选集两半句契约（`test_interlock_candidates_contract.py`）。这些行的"未经复核"字样随第五轮处置更新，"✔"只在 M0 退出后升级。
**E2 变更范围（2026-10-11，WO-E2）**：二维凸构造、成员、法锥与 G0 三票改用精确判据；凸首入的选路、初态与射线裁剪也不再以浮点 gap 作分支。定向门为 `test_kernel2d_exact.py`、`test_kernel2d_report_band.py`、`test_kernel2d_convex_ray_exact.py` 及改写后的二维回归/不变性门；旧噪声带豁免改为逐点精确 oracle 对照，稳定区另验刚体运动不变性。变更后的全套结果、突变体及残余边界以 `reports/codex/E2_report.md` 为准。这里不是新一轮 G6 通过声明；上文历史复核不自动覆盖 E2 的新代码和新门。
**E3E4 复核边界（2026-10-12）**：本单逐条重放第五轮指定的 14 条旧版本发现，并执行二维/极限分析新门与 10 项一次性源码突变；处置、红断言、旧门改写和全套耗时见 `reports/codex/E3E4_report.md`。这不是 50 条发现全部关闭，也不是六路独立 G6；用户禁止新建 worktree，本单仅本树验证，历史复核不自动覆盖新代码。
表里每个 ✔ 后面的括号给出看护它的测试（纪律 C：写不出测试的不打 ✔）。文件名省略 `tests/` 前缀。

| 层 | 状态 |
|---|---|
| L0 | 二维已有精确谓词门（见 E2/E3 报告）。**三维 E5a 部分实现，有门、未过 G6**：输入顶点精确凸包、仅精确共面归并、orient3d 保守过滤；显式 `exact_*` 三角表面成员/交点原语（`test_geom3_e5a.py`、`test_hull_robustness.py`、`test_geom3_merge.py`、`test_filtered_predicates.py`）。**E5a2 已将旧一般三入口接入精确三角化表面路径**（`test_e5a2_surface.py`）：仅对有效、定向朝外、闭合、嵌入的表面；非平面环确定性耳切，不自动凸化。一般重叠用有理平面分区及内部见证，涵盖共面分支；非法/自交表面不在证明范围。一般表面与显式凸包是不同模型，见 `docs/exact_3d_design.md`。实测与未达项见 `reports/codex/E5a2_report.md`，不是 G6 退出 |
| L1 二维 | G1 复现 legacy bb52 顶点-边 53/53 ✔（`test_bb52_g1.py::test_g1_tier1_all_legacy_ve_reproduced`）。**E2 凸路径（2026-10-11，已实现并配定向门，待 G6）**：只接受精确凸输入，允许平直顶点，微凹/折回/绕圈/零长边清晰拒收；仅精确平行同向边合并 FF。成员对给定坐标和精确平移判定；显式 `tol` 无舍入地板，凸报告带用精确欧氏边界距离，非凸回退用精确相交加保守四轴边界见证、报告带不保证完备（`test_kernel2d_exact.py`、`test_kernel2d_report_band.py`）。凸 G0 三票零容差、不跳样本，边界探针参与计分；票二对独立全顶点支撑集核对严格/边界标签，票三只数严格凸顶点（`test_kernel2d_g0.py::test_g0_random_convex_pairs`、`test_kernel2d_exact.py::test_g0_flat_chains_use_exact_support_sets_without_ambiguity_exemptions`）。**凹块 G0** 使用独立 `kernel2d/g0_oracle.py` 的有理区间裁剪、段距离与事件检查检验距离/出口完备性（不调用生产 `polygons_overlap`），历史 bb52 1260 次平移为 603/603、657/657（`test_bb52_g1.py::test_g0_distance_completeness_real_concave_geometry` / `::test_g0_exit_completeness_real_concave_geometry`）；精确一般多边形相交回退已有闭式门，但**基于盖裁剪的凹块全局 E 仍未实现**（M3）。**E3 二维收尾（WO-E3E4，有定向门、待 G6）**：凸/凹首入初态与判定均对给定数据精确；凹 VE/EV 仿射根、各自时刻段内和前事件漏候选自校验在 Fraction 上完成，t_max 不被容差放宽。`tied_labels` 只报精确同时，接近项另报 `near_labels`；`shortest_exit` 精确比较在程负间隙的平方距离（局部最浅盖，不声称一般凹对全局最小分离；`test_kernel2d_entrance_e3.py`）。局部 VE/EV/VV 默认精确，显式长度/角度域窗口只放宽、不抬舍入地板，严格性与窗口活跃分开（`test_kernel2d_covers_e3.py`）；二维 `convex_hull` 返回精确极点，tol 不再隐式删点。bb52 的 53 条 legacy 窗口盖对账保留；运动首入门对精确微贯入另核局部出口，不把 FIT 内贯入当接触（`test_kernel2d_entrance.py::test_every_legacy_vertex_edge_contact_of_bb52_is_a_first_entrance_along_its_edge_normal`）。旧静态 `first_entrance_for_vertex` 仍不是一般凹块的运动首入。全套、突变、调用点分类见 `reports/codex/E3E4_report.md`，不等于 G6 退出 |
| L1 三维 | **E5a 凸路径已有精确门、未过 G6**：凸成员对原始坐标有理 SAT；局部 facet 与独立精确差点凸包标签全量双向核对；票三仅比较极点。G0 强制 E 顶点/棱中点/面重心，零跳样、零 ambiguous/low_e 豁免（`test_g03_e5a.py`、`test_covers3_g0_vote2.py`）。凸模型的标签属于 canonical view，源面非共面时不能直接解释成原 face 编号。E5a2 枚举窗口从原坐标精确比较距离平方，正 tol 凸成员带为完整欧氏边界距离（`test_e5a2_covers.py`），不读构造 gap 作这些分支。一般非平面源环单盖仅为 Newell 向量/首顶点锚平面/源拓扑描述符，不是折面实体完整法锥；反例门固定见证不在折面上、环起点改变描述平面及标签域分离。凹块 G0 仍只有既有分离侧距离完备性。**G2 对 3-b-dda 手写期望清单** ✔（不是对检测器：3-b-dda 的入口是 `cases.py` 手写的 4 个，G6 盲区 1；三维 legacy 检测器至今未对过），范围窄：三个夹具（cb2_locked / cb2_sliding / cb_bond）各 4 个 np 入口 ↔ 4 个 VF 盖（`test_g2_bdda3d.py::test_g2_isomorphism_against_bdda3d`）；只对账 np↔VF/FV，窗口 `G2_WINDOW=1e-6`（原来硬写 1.0）；legacy 的 ee 入口、窗口内的 EE/VE3/EV3/VV3 盖现在会让门变红，**但还没有对账通道**（带内牙 6f157ac 未经独立复核，见状态声明）；只有一种几何（轴对齐方块叠放）；不是凸包角点的输入顶点，重复点登记别名、T 形点直接报错（`::test_g2_duplicate_vertices_are_aliased_and_reconcile` / `::test_g2_non_corner_vertex_is_a_clear_error`）；legacy 侧自 2026-09-24 起受哈希看护（`test_fixture_provenance.py::test_bdda3d_gate_has_teeth`），但姊妹仓库的版本没有记录；入口是算例预置的手写列表，**不是** detect.py 的产出（G6 盲区 1 已核实）。**M2 第一版（2026-10-10，`kernel3d/entrance3.py`，有门·未经复核）**：沿运动方向的三维首入（命题 7：候选集来自 facet 型盖、按给定数据精确谓词裁决（E5b 后继门见开头）、集值点如实报并列集、已侵入取最短出口）与退化族合并（FF / FE，`members` 保留展开视图）；门 `test_entrance3.py`（闭式、24 对随机凸对对不经盖的 oracle、刚体运动 1e3–1e6、漏候选必抛错）、`test_entrance3_concave.py`（台阶 / 微台阶 / V 槽 / 倒方台）、`test_entrance3_g2.py`（三份 bdda3d 夹具上首入 FF 的成员逐条还原 legacy 的 4 个 np 入口）；13 个突变体里 10 个被抓，3 个如实记（"平面已在身后"筛选与"t* 处谓词须相触"核验互为冗余、同时撤回才红；平面簇容差 ×1e6 在当时几何上不改变输出；E5b 已改精确共面并加微台阶牙，历史 13 项不代表现状）。EEP 没有自己的合并规则（由 VF/FV 边界态表达）。**未做**：凹块全局 E 构造（M3） |
| L2 | 裕度层四条自拟"定理"：二、四有门 ✔（`test_margin.py`：构型-工作空间距离恒等 `test_config_space_distance_equals_body_distance`、C^{1,1} 正则化的 Lipschitz 双边门 `test_inflated_normal_is_lipschitz` + `test_lipschitz_gate_has_teeth`）；定理一（膨胀恒等式）的门 `test_inflated_membership_tracks_the_margin` 与实现共用同一个 `body_distance`，**不是独立门**；定理三只有前半（margin_gap ≤ 0 即广义接触闭合）有门（`test_margin_contacts_are_generalized_contacts`），后半（KKT 乘子 = 虚拟接触力）无实现无门。审查指出的"贯入时答安全"（fail-unsafe）已修：贯入返回哨兵、裕度判违约（`test_margin_penetration.py`）；这道守卫依赖暴力谓词 `polyhedra_overlap`。**与正本的对照**（原审查盲区 4）：`docs/canon_map.md` 在历史 HEAD `094861c` 尚不存在；随后已经过 G6 第二至第五轮独立重审，正本对代码 GAP3 的处置见 `reports/g6d_20261010.md`、`reports/g6e_20261010.md`。定理一到四是本仓库自拟编号，正本没有同号定理；内容出处和模型边界按 canon_map 的逐项映射读取，历史文档核验不等于当前全部实现通过 G6，更不等于 M0 已退出。本行只采纳往弱里改的部分：定理一的门不独立、定理三后半无实现无门 |
| L3 | 极限分析（下限 LP + 对偶机构，自带上下限自校验）✔（`test_limit.py::test_lower_and_upper_bounds_coincide`）；Patton 剪胀律 ✔（`test_limit.py::test_interlock_with_friction_reproduces_pattons_law`，含曾被判假不可行的 (0.2, 0.1)、(0.3, 0.1)；全格扫描见 `test_limit_scale.py`）。审查指出的"部分格子静默报 infeasible"已在 M0 修复，M0.2 起 LP 改为**对给定数据精确**（浮点只给候选、有理数核验三种证书；力矩列、荷载平移、黏聚上限精确给出；`test_lp_certificates.py`、`test_limit_scale.py::test_interlock_is_never_falsely_infeasible_on_the_audited_cells`、`test_lp_scale.py`），可分辨性筛查与刀刃输入的诚实边界见 `limit.py` 模块文档，**待 G6 重审**。**E4 自校验（WO-E3E4，有定向门、待 G6）**：静力平衡、对偶间隙、互补与机构容许性在同一精确模型上用有理数核验，tol 不再决定通过；LP 保留精确解见证，浮点视图用于展示。Fraction 的 10⁻³ 至 10⁻¹⁰⁰ 相对 α 错误、低摩擦/低黏聚、远体与细高体注入由 `test_limit_exact_selfcheck.py` 看护；既有反作用和静力手改门保留。多体可分辨性按各体自身接触形心与臂长，不借无关远体扩大尺度。筛查只写 `resolvability` / `resolvability_statuses`，不再用邻域不可行覆盖原问题 status/alpha，也不因邻域敏感抛错；原答案由独立精确 LP 门核对（`test_lp_certificates.py`、`test_limit_multi.py`）。`contact_forces`/`active` 仍是按 tol 截断的展示，静力证书是 lambdas；输入可分辨性仍非误差界，详见模块文档与工单报告。三维摩擦锥采用经逐射线精确认证的内接模型，误差**不随 k 单调**。理想正 k 棱锥在固定几何、荷载和相同黏聚模型下，仅由集合包含得到 `C(μ·cos(π/k)) ≤ C_k(μ) ≤ C(μ)`；一般不能把左端换成 `cos(π/k)·C(μ)`，因为容量 C 对 μ 非线性。实际 binary64 生成元独立认证单边性和圆锥内接，必要时向内调整；这不自动保留理想内切圆半径。旧 `test_limit.py::test_three_d_cone_linearisation_is_conservative_within_the_inradius_bound` 仅在固定 amp=0.25、μ=0.2 网格断言相对界；同几何 μ=1.8 的反例门 `test_r14_cone.py::test_nonlinear_capacity_has_no_universal_cosine_relative_error_bound` 禁止将其推广。基架对齐/不单调门仍为 `test_limit.py::test_three_d_cone_error_depends_on_frame_alignment_not_monotone_in_k`。接触点取动体一侧 `point_a`，倾覆承载与间隙无关（`test_limit_contacts.py::test_toppling_capacity_is_independent_of_the_gap`）。本构 = 库仑 + 黏聚，可插；关联流动。**多体（M1，2026-10-10）：有门·未经独立复核·待 G6**——`limit_multi.py` 把各体平衡并进同一 LP、接触在两体间成对出现，单体是特例（`test_limit_multi.py`：单体退化与 `limit_load` 相同、两块叠放 min(μW₂, W₂, (W₁+W₂)/h) 逐点相等、成排块传力、三维叠放、注入错解与"忘记反作用"的变异都抛错；`test_limit_arch.py`：五/七块半圆薄拱的 α 与**独立枚举的四铰机构上限**在 1e-9 内相等（历史枚举记录为五块 480 种铰位里 10 个容许、七块 2240 种里 28 个；当前门核容量/容许性，不把这四个计数逐一断死），低摩擦取滑动机构、更低自重不平衡，厚拱在关联流动下无界——如实报出，不硬凑；`test_limit_flat_arch.py`：刚性竖直台肩之间的三块平拱自锁（μ > 0 报 unbounded、μ = 0 报 infeasible），附不经 LP 的运动学论证——此前 README 把它记在 test_limit_arch.py 名下，那里并没有这道门，G6 第五轮补）。多体下接触力分布不唯一、α 唯一。 |
| 跨层 | **端到端：有门·未经任何复核·待 G6**（`test_end_to_end_cb2.py`，115 例；b26d7f5 新增、8376ec2 修订，两次提交都是直接进 main 的）。补的是审查盲区 6 的三维半段，**按闭式改写，计划原定的判决没做**：计划要"sliding 例的机构是平动、locked 例承载更高"，但 cb2_locked 与 cb2_sliding 在 step 0 的导出除 `case` 名外逐字段相同（顶点相同，入口节理参数也相同：fa = 35°、coh = 0、tens = 0；本次对 `fixtures/bdda3d/*.json` 三份 JSON 逐字段比较）；cb_bond 只多了 coh = 20、tens = 3（连带 m0_0/m0init 不同）；导出里没有荷载/驱动，所以读不出 locked 与 sliding 的区别，而"平动"又不是对偶最优面上的不变量（见"审查外发现"）。端到端门**只取夹具几何**：μ 由测试参数化给出，接触不带黏聚力，不读夹具的 fa/coh（fa = 35° 即 tan 35° ≈ 0.70 与 cb_bond 的 coh = 20 都没用上）。现在的门是 bdda3d 真夹具 → 几何重建 → 盖枚举 → 接触 → 极限分析，对纸笔闭式核对承载力（绝对误差 ≤ 1e-9，尺度格相对误差 ≤ 1e-9；不是逐位相等，例如 μ = 0.3 时 α = 3.0000000000000018）——滑动 μW、沿轴推的倾覆 W、沿对角推的倾覆 √2·W，μ = 1 与 μ = √2 两个分界本身都取到（`::test_axial_push_slides_or_topples_exactly_as_closed_form`、`::test_diagonal_push_uses_the_sqrt2_tipping_line`），另有几何 ×1e-3/×1e3 与荷载 ×1e-2 至 ×1e4、三种接触点取法、非对称力矩参考点；破坏模式只读对偶面上的不变量（`::test_failure_mode_is_read_off_invariants_of_the_dual_face`，见"审查外发现"）。**L3 承载比 == L5 剪胀比**（`test_limit.py::test_frictionless_interlock_capacity_equals_the_dilatancy_ratio`）仍是唯一经住审查的跨层交叉验证。两条路径的求解部分（静力 LP `limit_load` 与冻结盖逃逸高度 `escape_height_covers`）互不共用，但共用块体生成（`tools/osteomorphic.py`）与盖枚举 `enumerate_covers3`（`kernel3d/interlock.py` 的 `escape_candidates` 也调它），盖层出错会两边一起错；两者各自对闭式 2·amp 核对，这一点才是它的硬度所在。审查报告（`reports/audit_20260921.md` 第 12、129 行）与 `reports/l3_limit_analysis.md` 的"零共用代码"、该测试 docstring 的"毫无共用代码"都说过了头，已于 09-27 / M0.2 订正 |
| L4 | 对偶内核 ✔（`test_dual.py`；`float(Dual)` 现在直接报 TypeError，不再静默丢导数：`::test_implicit_float_conversion_of_a_dual_is_a_type_error`）。冻结盖片内可微 ✔（G3 曾测得收敛阶 1.9995；当前门断言阶数在 2±0.1 内：`test_interlock_sensitivity.py::test_g3_gradient_vs_central_difference_with_convergence_order`，门限 2 ± 0.1）；冻结路径补上了 VE3/EV3，400 次一般位置随机抽样中的分离样本（本 HEAD 上 387 个，门只要求多于 350 个）全部走得通（`test_frozen_lowdim.py::test_every_body_distance_label_enters_the_frozen_path_convex_400`）。TIA 首枪的 ∂h/∂phase 在 phase = 0 处**不可微**（h 关于 phase 是偶函数），工具现在把它标出来，不再报一个单侧导数冒充导数（`test_interlock_sensitivity.py::test_phase_derivative_at_phase_zero_is_flagged_on_every_default_row`） |
| L5 | DDA 读取器 ✔（只读）：tf.cpp 路径有了执行门，三份夹具共 6716 条接触、100% n-p，经读取器重算并与零共用 oracle 逐行对账（`test_tf_reader.py::test_tf_census_recomputed_through_the_readers` / `::test_tf_readers_agree_row_by_row_with_a_zero_shared_oracle`）；TF_MODE 的状态 4/5/6 改标 UNVERIFIED，不再断言成 SLIDING/LOCKED（`::test_tf_mode_states_4_5_6_are_unverified_not_asserted`）；`canonical_key` 能分辨到哪一级要看来源——bdda3d 逐步唯一；bdda_df（带 verts.csv）仅旧夹具逐步唯一，M4a 的 v01/v02 四例有 9 条额外主特征键重复，必须保留 multiplicity/第二参考，不能无声去重；tf 探针只到块对一级（`test_readers_roundtrip.py`、`test_m4_bdda_shadow.py::test_duplicate_primary_reference_second_row_metrics_are_not_skipped`）。TIA 互锁首枪 ✔（逃逸剖面 / 剪胀比 / 解析灵敏度；`test_interlock_sensitivity.py`），逃逸候选集在非对称块 nx = 5 上 25 个随机偏移零失配（`test_interlock_escape.py::test_escape_height_covers_is_complete_off_axis_on_asymmetric_blocks`） |

**夹具溯源（2026-09-24 订正）**：10 个 Phase 0 夹具当初在 `core.autocrlf=true` 下被规范成 LF 入库，而 `fixtures/PROVENANCE.json`
记的是 CRLF 原件的哈希——从 GitHub 克隆下来，本仓库自己的溯源门是红的；09-21 的六路审查全在主树里跑，所以没发现。
cc5d7cf 按原字节重新入库，`.gitattributes` 设 `* -text`，本仓库本地 `core.autocrlf=false`。由此立一条规矩：
**新鲜 worktree / 克隆的基线必须全绿**（本次核对：在继承系统 `autocrlf=true` 的新鲜克隆里，77600c9 全套 1174 passed，8376ec2 全套 1209 passed，094861c 全套 1209 passed）。
附带记录：Git for Windows 的系统配置默认 `autocrlf=true`；b-DDA 与 3DDA（真仓库在 `C:\3DDA\3d-DDA-work`，`C:\3DDA` 根下的 `.git` 是空壳）
本地早已是 `false`，3-b-dda 已由用户设为 `false`（三处本地配置本次都读过确认：`git -C <仓库> config --local core.autocrlf`）。
**订正（2026-09-24）**：cc5d7cf 的提交说明称"3DDA 与 3-b-dda 仍继承系统的 true"。对 3DDA 这句是错的——它查的是 `C:\3DDA` 根下的空壳 `.git`；
真仓库 `3d-DDA-work` 的本地配置自 09-18 起就是 `false`（`.git/config` 修改时间 2026-09-18，早于 cc5d7cf）。对 3-b-dda 这句当时属实，之后由用户改为 `false`。
提交说明已推送，不改，在此订正。

**审查外发现（M0 期间修复者自己查出并修掉的；G6 应当复看）**：
- LP 在纪律 B 的尺度格子上还有毛病（2026-09-24 订正：此处原写"~3e-10 的主元、~1e3 的残差"，这两个数没人复核过，删去）。复核得到的是：M0 前的原始链路（cc5d7cf 的 `limit.py` + `lp.py`）在三维扁块四角黏聚（μ = 0.2、各 cA = 1.5·s）、荷载 ×1e4 时**报 `optimal` 却给错值**：k = 16 时承载力是解析上界的 2.12 倍（169757 vs 夹逼 [78463, 80000]），**k = 5 时承载力为负**（−492664 vs 夹逼 [64721, 80000]）；荷载不放大（s = 1）时同一算例正确（7.919 ∈ [6.472, 8]）。复现：`git archive cc5d7cf src` 解到临时目录，跑 `tests/test_lp_fail_loud.py` 里 `_cohesive_block(1e4, 1.0)` 同款算例（2026-09-24 实跑）。
  另外两个：列放大 1e2/1e4 时假不可行；一阶段舍入噪声造成的"无界"被报成不可行。修法是 2 的幂行列均衡、右端归一化、残差守卫；
  数值崩溃时现在抛错，不再返回一个错的最优（`test_lp_scale.py::test_column_scaling_does_not_change_the_answer`、
  `::test_phase_one_rounding_noise_is_not_reported_as_infeasible`、`::test_numerical_breakdown_cannot_change_the_answer`；
  荷载 ×1e4 加黏聚力的格子在 `test_limit_duality.py`）。（2026-09-27 注：下面描述的是 M0 时的契约；M0.2 起 LP 的契约改为
  "答案对给定数据精确"，这些格子现在一律答对，见 AGENTS.md §3。）"要么答对、要么抛 RuntimeError、绝不静默给错"这条契约由 8376ec2 新增的
  `test_lp_fail_loud.py` 钉住（lp_tol 取默认/1e-9/1e-12/1e-14 × 4 种荷载与几何尺度 × k = 5/16，共 32 格）：全部 32 格中有 6 格抛 RuntimeError，全都落在显式传 1e-12 / 1e-14 的 16 格里
  （不只 ×1e4：lp_tol = 1e-12 时是 (s,g,k) = (1e4,1,16)、(1e4,1e-3,16)；1e-14 时是 (1,1,16)、(1e4,1,16)、(1e4,1e-3,16)、(1e-3,1e3,5)，
  其中有未放大的黏聚块），契约允许；默认容差与 1e-9 下 16 格全部答出，审查那个算例默认容差下必须答出来（`::test_default_tolerance_answers_the_audited_case`）。这一条同样未经独立复核。
- 三维 G0 票三原来数的是凸包三角网格的顶点，退化输入上会把共面的非极点也数进去（四面体/方块 19 对 13，方块/方块 26 对 8），
  之前被票一的崩溃挡住，没人看见（`test_covers3_membership.py::test_g0_vote3_counts_only_extreme_points_on_degenerate_input`）。
- 上面"夹具溯源"那一条。
- C17 修完后，第二轮复核发现 G2 的带内检测只在"枚举之后追加的假盖"上测过：把 `compare()` 的枚举窗口改回去，全套照样绿。
  6f157ac 加了一颗穿过枚举器的牙——在内核里打一个真缺陷（顶点法锥判据恒返回"边界"）。本次核对在 8376ec2 上用同一变异
  （只把 `compare()` 里 `enumerate_covers3` 的实参改回 `window`，记下的 `enumerated_window` 不动）重跑 `test_g2_bdda3d.py`：3 红 55 绿，红的正是新加的
  `::test_g2_band_catches_a_real_kernel_defect_through_enumeration` 三例；若连 `ewin = max(window, band)` 这一行一起改回，
  6f157ac 同时加的 `enumerated_window >= band` 断言也会响，22 红 36 绿。C17 这颗牙没有经过第三轮独立复核（见状态声明）。
- 写端到端门时查出两件事。一是**对偶机构不唯一**：对偶最优面不是一个点，返回哪个机构取决于单纯形的选主元顺序。
  推力恰好落在八边形内接锥的一条棱上时切向速度可以在 ±π/k 内任取（实测沿 +x 推、μ = 0.3 时返回 (1, −0.414, 0.3, 0, 0, 0)，偏 −22.5°），承载力照样精确；而且**滑动例的最优面里还有带转动的机构**——
  μ = 0.4 时 (1, 0, 0.4, 0.117, 0, −0.293)（精确值 ω = (μc, 0, −c)，c = 1 − 1/√2）在原问题上同样容许、上限同样等于 α = 4.0
  （用门里的 `_power` 核算：最差接触功率 0、上限 4.0；μ = 0.95 时同形机构上限 9.5）。所以"滑动无转动"**不是**不变量。
  b26d7f5 的门曾在滑动分支断言"角速度为零"，那是一条靠选主元顺序才成立的脆断言；8376ec2 把它换成
  `test_end_to_end_cb2.py::test_failure_mode_is_read_off_invariants_of_the_dual_face`，用一个不调用 `eab.limit.wrench` 的独立刚体虚功率核算检查：
  返回的机构确是最优对偶；滑动时"平动 + 关联剪胀" T = (1,0,μ,0,0,0) 也是最优对偶；倾覆时绕前缘转动 R = (0,0,1,0,1,0) 是最优对偶，
  且任何纯平动的上限 ≥ μW > α——所以"带转动"只在倾覆时是真不变量；μ = 1 两者并列最优。
  二是 cb2 的四个接触点**关于原点中心对称**，"接触列力矩写反""接触列忘了减参考点"这类缺陷在原点取对称中心时看不见；
  于是加了参考点不变性门（`::test_capacity_is_independent_of_the_moment_reference_point`，原点取 (5,−3,2) 与 (−0.7,0.4,−11)）。
  本次核对（在 8376ec2 上，两种变异分别打在 `limit._build_columns` 的接触列上）：每种变异下都只有这道门红（4 例），文件里其余 111 例全绿。
  **订正（2026-09-24）**：b26d7f5 的提交说明称"力矩反号变异下本文件其余测试全绿"，在 b26d7f5 上不对——参考点取在对称中心时，
  那个变异只是把接触列重排（同一个 LP），当时被它弄红的是上面那条"角速度为零"的脆断言（在 b26d7f5 上重放：滑动的 μ = 0.4、0.95 两例红，
  加上参考点门 4 例，共 6 红 107 绿），不是抓到了缺陷。提交说明已推送，不改，在此订正。

**已知的层次违规**（2026-09-24 仍在）：
- `kernel3d/interlock.py` 是 L5 的东西，却放在内核目录下，第二个域进来之前（M6）要搬走。
  冻结盖的解析表达式已于 2026-09-20 从它里面搬进 `kernel3d/frozen.py`——这一步算完成，`frozen.py` 本身是 L4 的内容，留在内核里没问题。
- `contact_record.py` 里的各引擎映射表（状态码 `BDDA_MODE` / `BDDA3D_MODE` / `TF_MODE`，盖类 `BDDA_COVER` / `BDDA3D_COVER` / `TF_COVER`）
  仍是适配器的内容寄居在契约层，同样要在 M6 之前搬出。

报告见 `reports/`（审查全文 `reports/audit_20260921.md`）。

<details>
<summary>2026-09-21 版的状态声明与现状表（已被上文取代，原样保留，逐条标了订正）</summary>

> **⚠ 2026-09-21 独立审查后的状态声明**：`reports/audit_20260921.md` 确认 2 critical + 15 major + 14 minor 缺陷与 6 处审查盲区，
> 下表若干 ✔ **暂不可信**——三维 G0 只有两票、二维凹几何 G0 的 oracle 已证伪、首入三维未实现、裕度层贯入时 fail-unsafe、
> 极限分析求解器在部分参数格子静默报 infeasible。修复计划见 `docs/plan_20260921.md`（M0）；M0 以**重审 0 critical / 0 major** 为退出判据，
> 在此之前本表按审查报告的"对既有声称的订正"一节阅读。
>
> **订正（2026-09-24）**：三维 G0 现在是真三票；二维凹几何 G0 已改为暴力真值 + ∂E 完备性（分离侧距离完备性 603/603、相交侧出口完备性 657/657），
> 凹块成员谓词仍无门（M3）；三维首入仍未实现，已从"已交付"里撤掉、列入 M2；裕度层贯入时 fail-unsafe 已修；
> 求解器假不可行已修（相对阈值 + 2 的幂均衡 + 残差守卫）。以上都待 G6 重审。

旧现状表（2026-09-21）：

| 层 | 状态（原文） | 订正（2026-09-24） |
|---|---|---|
| L0 | 二维/三维多边形与多面体、暴力谓词（独立 oracle）✔；**只做平移** | "独立"当时不成立：暴力谓词与盖层共用扇形三角化与半平面核，非凸面上一起错。现统一为 `point_in_face_polygon`，并对闭式 oracle 设门 |
| L1 | 二维 ✔（复现 legacy bb52 53/53）；三维 ✔（G0 自证 + **G2 对 3-b-dda 手写期望清单零差异**）；共面归并 ✔；**退化盖未合并**；**凹块无全局 E 构造** | 53/53 仍成立；它背后的凹块 G0 "1186/1186" **撤回**——那次拿 sign(min gap) 当成员规则，1186 次里有 621 次是相交样本，靠一条假规则"通过"（`test_bb52_g1.py::test_g0_rerun_replays_the_original_1186_translations` 可重放）。三维 G0 当时只有两票，且在平行面退化对上崩溃或误判。"G2 零差异"只覆盖 np↔VF、一种几何，legacy 侧当时也无哈希看护，而且对的是手写清单、不是检测器 |
| L2 | ✔ 裕度层落地（膨胀恒等式 / 构型-工作空间距离恒等 / 裕度即接触 / C^{1,1} 正则化），四条定理各有门 | 当时贯入时答"安全"（fail-unsafe），Lipschitz 门无牙，可微路径对约一半分离位形崩溃；均已修 |
| L3 | ✔ 极限分析（下限 LP + 对偶机构，自带上下限自校验）；本构=库仑+黏聚，可插；**只做单体、关联流动** | 求解器在相邻参数格子静默报 infeasible；有黏聚力时 `check_duality` 全错；"随 k 单调收敛"不成立。前两条已修，第三条措辞已撤回 |
| L4 | 对偶内核 ✔ + 冻结盖片内可微 ✔（G3 收敛阶 1.9995） | 1.9995 复核仍成立。补充：`float(Dual)` 当时会静默丢导数；TIA 在 phase = 0 处报出的导数其实不存在 |
| L5 | DDA 读取器 ✔（只读）；TIA 互锁 ✔ 首枪（逃逸剖面/剪胀比/解析灵敏度） | tf 读取路径当时从未被执行攻击，TF_MODE 4/5/6 的折叠没有依据；逃逸候选集在非对称块上不完备 |

旧表下面那段原文：

> 268 测试全绿。报告见 `reports/`。**已知的层次违规**：`kernel3d/interlock.py` 是 L5 的东西
> 却放在内核目录下，第二个域进来之前要搬走（**冻结盖的解析表达式已于 2026-09-20 搬入 `kernel3d/frozen.py`**）；`contact_record.py` 里的三家状态码映射表
> 是适配器内容寄居在契约层。

**订正（2026-09-24）**："268 测试全绿"当时属实，但上面这些缺陷一条都没被那 268 个测试抓到（原因见审查报告"为什么 268 个绿灯没抓到"）。
层次违规一句漏了一半：`contact_record.py` 里的盖类映射表 `BDDA_COVER` / `BDDA3D_COVER` / `TF_COVER` 同属此类，旧文只列了状态码
（`BDDA_MODE` / `BDDA3D_MODE` / `TF_MODE`）；上文"已知的层次违规"已按六张表写。

</details>

## 路线

以 `docs/plan_20260921.md` 的 M0–M7 为计划背景；当前实现以本文现态表、canon_map 和最新修复报告为准。

<details>
<summary>历史路线快照（094861c 时期）</summary>

下列为历史计划及当时未完成项，不是当前实现状态；首入 API 和 canon 后续核验已在上文订正。
历史核验不能代替本轮修改的独立 G6，M0 退出仍由下一轮复审决定。

- **M0 止血**：31 条缺陷已修复并合并；审查盲区 1、3、5 已堵，盲区 2（首入）按计划从文档撤回、实现挪到 M2；
  盲区 6 做了三维半段（上面的端到端门，按闭式改写，未经独立复核）；盲区 4 的"正本对代码"对照表 `docs/canon_map.md` 已写、与本文同批提交，未经 G6。
  **剩余：G6 独立重审**（退出判据是 0 critical、0 major，不是测试全绿）。另有几项计划列在 M0 里、截至 094861c 没有做到，重审前要么补上、要么明确挪期：
  - 盲区 6 的二维半段（bb52 几何 → kernel2d → 二维极限分析）：这条路径还不存在。
  - 计划对三维端到端要求的判决"sliding 例的机构是平动、locked 例承载更高"**没有做，也无法从现有夹具做**：cb2_locked 与 cb2_sliding
    的导出除 `case` 名外逐字段相同（顶点与入口节理参数 fa = 35°、coh = 0、tens = 0 都相同），导出里也没有荷载/驱动，读不出二者的区别；
    "平动"又不是对偶最优面上的不变量。门已改为对纸笔闭式核对承载力（绝对误差 ≤ 1e-9，见跨层行）。
    这一判决**挪到 M1**（计划 M1 节"cb2 夹具的 sliding/locked 判决"即此项），前提是新的、带荷载/状态差异的夹具。
  - **G6 通过后待写**（只列条目名，不是声称）：L3 行"黏聚力下的上下限自校验"；L2 行"定理一、二、四的内容在正本有出处"
    （`docs/canon_map.md` 对审查 GAP3 的订正，未经 G6）。
- **M1** 多体极限分析 → **M2** 三维首入 + 退化盖合并 → **M3** 凹块全局入口块构造 → **M4** b-DDA 接缝 `BDDA_DETECT=legacy|eab` 影子运行
  → **M5** SE(2)/SE(3)（不承诺周期）→ **M6** 第二个域适配器（进来之前先搬两处层次违规）→ **M7** C++20 `eab2`（只在撞到性能墙时做）。

</details>

<details>
<summary>2026-09-21 前的旧路线（已由计划取代，原样保留）</summary>

**近期（让重写安全）**：G2 三维同构对账（bdda3d 侧只对了手写期望清单、**三维 legacy 检测器至今未对过**；**tf.cpp 侧阻塞于缺顶点导出**，请求已提交）→ 退化盖合并。
**订正（2026-09-24）**："bdda3d 侧已通过"只指 np↔VF 一类、一种几何；tf.cpp 侧的阻塞状况本次未核实。退化盖合并挪到 M2。

**中期（让重写有意义）**：~~L3 互补层 + 本构插口~~（极限分析已落地，**跑出 Patton 剪胀律**）→ 多体机构 → b-DDA 接缝 `BDDA_DETECT=legacy|eab` 影子运行
→ 同构门通过后由所有者决定切换。
**订正（2026-09-24）**：Patton 律仍成立，但当时求解器在相邻格子会静默报不可行（已修）。多体机构 = M1，接缝 = M4，且 M4 的前提加了"M0 全过、M2 首入落地"。

**远期（出岩石）**：位形空间从平移升到 SE(3)（**E 不再是 Minkowski 差，边界变曲面——真正的理论前沿**）
→ 第二个域适配器（护面块体或 caging）→ C++20 `eab2` 移植（复用 bdda2 的 `Scalar`/`Dual<W>`）。

</details>

**六份旧实现没有一份被就地重写**：它们变成参考实现与夹具源。b-DDA 的力学层（L3）留着，
只把它的检测层换掉——重写是真的，但必须走在门后面，因为 b-DDA 已经论文就绪且逐位锁定，
大爆炸式重写会把那份资产作废。

## 运行

```bash
python -X utf8 -m pytest -q -p no:cacheprovider     # 全套 6717（2026-10-10）；夹具已入库，不需要先导入
python -X utf8 tools/tia_sensitivity.py
```

**订正（2026-09-24）**：旧版这里把 `python tools/ingest_fixtures.py`、`python tools/ingest_bdda3d.py` 放在跑测试之前。
夹具早已入库并受 `test_fixture_provenance.py` 哈希看护，跑测试用不着它们；这两个脚本是**从姊妹仓库重新导出**用的，
会改写 `fixtures/` 与 `fixtures/PROVENANCE.json`，只在确实要换夹具版本时跑，跑完的差异要单独审。


## WO-E5a2 退出状态：PARTIAL（2026-10-12）

本单指定底层门与整数化对拍通过，但完整测试未全绿，不构成里程碑退出。严格表面语义揭示旧 interlock 近竖直事件被噪声政策丢弃：原80个竖墙输入中7格存在独立认证的更低分离高度，当前返回约1.2不是最小逃逸。不能把原最小逃逸门改成只检查安全上界。另有旧并列窗口突变牙失效；加强草案只在证据中，未应用。完整失败清单、实测耗时、独立反证及 WO-E5b 交接以 `reports/codex/E5a2_report.md` 为准；竖墙证书见 `reports/codex/E5a2_evidence/a1/walls_handoff.md`。没有宣称全套≤900秒、正式G6、新worktree或全链精确化通过。
