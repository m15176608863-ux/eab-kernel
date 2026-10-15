# WO-M5b 中文交付报告

> M5c 勘误：本文为 M5b 历史记录；§5/§6 的分母、n=2/68 和 bb03 共边槽已订正。最新完整传递绑定、次参考/共边统计和扩大认证见 [M5c 报告](file:///D:/eab-wt/cx-e2/reports/codex/M5c_report.md)。链接中的端点/稳健摘要由 M5c 实际重算发布，不是改哈希。

## 0. 结论、范围与验收状态

**研究级 PARTIAL，不声明完整里程碑 G6 验收。** 基线 `df4f6f1950be09d6712afafc97ab312d30e03c57`，执行前干净；只修改本树，无 commit/push/reset/checkout/stash/worktree/branch 操作。姊妹目录只读，原始数据复制到本树 tmp。未改 DDA 求解器或其接触语义。

- 完成：15220 块帧端点重建与完整配对、自包含输入；DDA 面积形心锚定 P2、六次精确首入、P2/P3 严格全窗界；两类严格充分稳健证书；1810 步/64010 对 P1/P2 状态和首盖身份对账；INT1 指定小项；四片全套与受影响冻结闭包真实重算。
- 稳健子集 **38683/64010**：无接触 38681，单首盖 2（新接触稳健样本 n = 2/68，不可外推）。敏感或未证 25327，绝不把“未证”说成实证模型不同。
- 未完成：正扰动管下已贯入最短出口/参考边排序；legacy 次参考统计；敏感子集 P3 非代数首入及完整三模型差异率；外部 `2.8e-6` 与本次全数据中点口径的对齐。详情见第 10 节。

所有稳健结论只针对本文指定模型族与误差管，不是连续物理路径、标定、工程或生产验证。

## 1. 理论：定义、证明状态与退化边界

详细证明：[P2 与六次理论](file:///D:/eab-wt/cx-e2/docs/m5b_motion_theory.md)、[稳健认证理论](file:///D:/eab-wt/cx-e2/docs/m5b_robustness_theory.md)。

| 对象 | 定义/证明状态 | 具名门 |
|---|---|---|
| M_DDA | c 为精确面积形心，M=R_binary64(theta)+E，E12=gxy/2；有理映射精确计算，实际顶点末帧残差独立测量 | `test_endpoint_map_matches_independent_displacement_oracle` |
| P1 | 原快照同身份顶点端点弦，沿用 M4c | 原 M4c 门及 M5b 接线门 |
| P2 | c+s d+[R_rational(s u1)+s E](p-c)；u1 为 tan(theta/2) 的 dyadic 有理近似，有 Taylor 有理误差包围 | `test_p2_coordinates_match_independent_complex_product_oracle` |
| P3 | c+s d+[R_angle(s theta)+s E](p-c)，本单不求一般超越首根 | `test_p2_p3_uniform_bound_contains_independent_interval_trigonometry` |
| 六次上界 | D_B=1+u_B²s²>0；用 Q_B 的点积/叉积恒等式证明整除；逐次检查余数零；一般≤6，刚体≤5，u_B=0 单独计数 | `test_sixth_degree_events_match_independent_seven_sample_oracle` |
| 六次精确根 | 只把原始输入次数上限 5 改为 6；Sturm/gcd/闭根唯一性及精确符号算法不变，7 次可约也拒绝 | 六次独立因式/二分/六无理分支门 |
| 非反转 | 2||E||∞<1 的充分域，保证整个共同仿射变换正定向；域外拒绝不等于判倒置 | `test_unsupported_p2_domains_fail_loudly_before_event_enumeration` |
| 稳健无接触 | 分段精确 Bernstein 投影包络间隙下界 > εA+εB；P1、P2 各自通过 | `test_no_contact_requires_strict_margin_and_covers_whole_window` |
| 稳健单首盖 | 早期分离、凸性、名义严格横截、端点异号、边内投影及全部竞争事件余量均严格过误差界 | `test_single_cover_certificate_has_independent_closed_form_oracle` |

P2/P3 全窗位置界为 `r1*(|u1|³/2+2 epsilon_u)`，其中 r1=max||p-c||1。时间律项来自 f(s)=2atan(su1) 的二阶插值余项，参数项来自 atan 的 1-Lipschitz 性，**不是时间采样最大值**。

回放还收费 P3 自身端点闭合项：`epsilon = b + r2 + e`，b 为上述全窗界，r2=max|P2(1)-实测末帧|∞，e=r1*2epsilon_u。因此 P3 自身闭合残差 r3≤r2+e。P2、P3 及各自指定的 s*残差校正族均被此管包住。早版 r1 漏了这最后一项的直接三角界论证，整批中断作废，**只使用从头重跑 robust_full_r2**，没有拼接。

首盖证书仅证明单个 VE/EV **身份**不变，不保证精确时刻、扰动后导数或根唯一性不变。多盖/VV/凹环、零余量和其它未通过条件留未证。

退化：theta=0 时 P2 逐值等于**自身精确端点**的 P1 弦；有 binary64 末帧残差时，不能把此恒等式冒称与原快照弦逐值相同。E=0 时等于同中心的 M5a SE(2)。二者都走一般事件路径，有完整结果字段退化门。

## 2. 实现/API、数值合同与 oracle

- `src/eab/kernel2d/dda_motion.py`：`area_centroid`、`rational_half_angle`、`DDAAnchoredMotion`、`dda_motion_from_z`、`p2_p3_bound`、`dda_first_entrance`。
- `src/eab/kernel2d/algebraic.py`：实代数数和求根上限六次，未放宽任何判定。
- `src/eab/kernel2d/model_robustness.py`：有理坐标包络、`separation_certificate`、`single_cover_certificate`；返回 None 表示未证，不是接触或实际模型敏感。
- 回放与复现工具：`m5b_endpoint_replay.py`、`m5b_grouped_probe.py`、`m5b_robust_replay.py`、`m5b_minimal_examples.py`；无姊妹代码 import，仅标准库和本仓库代码。
- [数值 inventory](file:///D:/eab-wt/cx-e2/docs/m5b_numeric_inventory.md) 逐 API 登记入口、输出及判据边界。生产新几何量保持 Fraction，不添加 binary64 谓词出口。

| 主 oracle | import 清单/独立性 | 门与结果 |
|---|---|---|
| 端点/面积形心 | Fraction；独立扇形三角积分、位移展开；不复用生产形心/拟合 | 精确零失配；不变性含旋转、平移、尺度 |
| 三角区间/旧轨迹中点 | Fraction、factorial、Decimal100；独立 Lagrange 余项和未中心化 Cramer 正规方程 | 最坏中点例独立包围核对 |
| P2 六次/首入 | 测试专属多项式/Sturm、独立整数 winding G0；不导入生产事件/求根/法锥原语 | 七点精确插值、额外点自检、完整标签/凹环零失配 |
| 稳健证书 | Fraction、itertools.product、math.comb；菱形—墙首时刻 (1+db-da)/2 与独立 Bernstein 基展开 | 严格边界、竞争并列反例、旋转/大平移/单位缩放全绿 |
| 回放/历史/共享域 | 字面协议与 stdlib JSON/hash/AST；接线 oracle 不冒称独立几何 oracle | 原数据到 frozen 主参考 1810 步两阶段各 141594 条零失配 |

不变性范围、正/负角和六次不可约/可约边界详见 `p2_work.md`、`endpoint_work.md`。采样只检实现；全窗性质依赖已列解析证明。

## 3. 变异表：红在语义，不靠哈希绊线

新门使用编译后的被测函数内部缺陷；执行语义用例时不调用源码哈希门。涉及既有静态 pin 的审查先屏蔽哈希类绊线，数值变异不以 pin 失效当成功。新插桩不在产物末尾追加假数据。

| 内部缺陷 | 必须命中的语义断言 |
|---|---|
| 六次事件丢最高次项 | 独立完整首根/首盖身份不一致 |
| 工程剪切 gxy/2 丢 1/2 | DDA 位移独立展开不一致 |
| 端点更新/形心/区间界缺陷 | 独立面积积分、位移或真三角包围断言 |
| 间隙 > 改 >= | `strict tube gap required`，等余量不得认证 |
| 横截末端误差界反号 | crossing not guaranteed 不得认证 |
| 回放免收正管径 | same status is not a tube certificate |
| 少收 P3 自身端点参数项 | own endpoint closure 必须收费 |
| as_rational 模素数排除余数0 | 只在0有模根的真有理根仍应恢复 |
| 共享 helper 导入来源/同名 def/class 绑定遗漏 | 未审 helper 来源不能继承共享豁免 |
| 历史行/续审/共享记录改写 | 原前缀指纹不变且只追加 |

各组实际变异与具名测试见 [P2 证据](file:///D:/eab-wt/cx-e2/reports/codex/M5b_evidence/p2_work.md)、[端点证据](file:///D:/eab-wt/cx-e2/reports/codex/M5b_evidence/endpoint_work.md)、[INT1 处置](file:///D:/eab-wt/cx-e2/reports/codex/M5b_evidence/int1_work.md)。不把构造采样或哈希失败记作语义 kill。

## 4. 端点重建：15220 块帧、配对、舍入单位

`out.csv(step=k,block=b)` 的 z 对应 `geom.step(k-1) -> geom.step(k)`；snapshot k 是起点，不是终点。最后区间使用 geom.final。每个起点逐坐标与 snapshot 核对，步号/块号重复或缺失拒绝，%.17g 先还原 binary64，再转精确有理数；不把十进制字符串当真实精确坐标。环绕两尾别名与首两点逐值核对；块顶点身份保持。

**舍入单位 U** 定义为 `ulp(max|coordinate|)`，最大值取该块该步起终点全部坐标，U 是一个 spacing，不是半 ULP，也不是 `coordinate*2^-52`。零值取 2^-1074。该描述单位随工程坐标量级变化，不被用作几何容差。

| 全量量 | 实测/严格界 |
|---|---:|
| 块帧 | 15220 |
| binary64 cos/sin 锚定 M_DDA 最大坐标残差 | 2.257867693845113e-13 |
| 最大残差/U | 1.00442270480587 |
| 数学真 sin/cos 端点残差/U 的严格上界 | 1.278351617304262 |
| 本机 sin/cos 对数学值误差的全数据上界 | 6.125351005406442e-17 |
| 旧 M5a2 拟合族与 P3 中点 L∞ 差的全数据最大上界 | 9.626408698932884e-06 |

本机 `math.cos/sin` 候选转 Fraction，另由精确 Taylor 区间给出对数学值的误差界。未知历史 C++ CRT 的内部位模式不凭语言标准假定一致。按原物理 `lo..hi` 面积矩循环起点与 C++ 语句分组补充重放后，315760/315760 个坐标**精确数值一致**；Fraction 不保留符号零，因此不声称包括 ±0 的所有 bits 都已证明相同。原起点错位佐证仅314252匹配的记录保留，不抹去。

这独立复现了“约1.1舍入单位以内”的端点结论（本定义下实得约1.0044）。数学真三角端点的1.27835上界是不同对象，不可混用。

外部 `2.8e-6` 保留为验收历史；本次明确全15例旧拟合族/P3中点口径实得约 **9.6264087e-6**，最坏 bbv01_dbv01a 第56步块10；bb09 最大约2.8144e-6。独立 Cramer/Decimal/Taylor 最小例已复核，**尚未取得外部原程序以对齐口径，不将新值硬写成已复现2.8e-6**。`docs/m5a2_affine_theory.md` 已改为引用本单可复现证据并明确此遗留，而非推翻已确认的 DDA 端点公式。

[输入包](file:///D:/eab-wt/cx-e2/reports/codex/M5b_evidence/endpoint_inputs/manifest.json) · [全量摘要](file:///D:/eab-wt/cx-e2/reports/codex/M5b_evidence/endpoint_summary.json) · [分组佐证](file:///D:/eab-wt/cx-e2/reports/codex/M5b_evidence/endpoint_grouped_summary.json) · [端点最小例](file:///D:/eab-wt/cx-e2/reports/codex/M5b_evidence/endpoint_minimal_examples.json)。所有输入分片<1 MB，默认重算无需姊妹文件。

端点摘要的源码哈希表只绑定直接依赖，**不是完整传递闭包**：中点路径间接依赖的 M4c/SE2 文件未列入该表，且本轮未修改。当前最坏例有独立数值复核；完整传递闭包的启动/结束绑定及拒绝变异门仍待硬化。不要把下节全量模型回放的完整生产源码绑定反推为端点摘要已有此保证。

## 5. 全时程三模型分类：只对稳健子集作结论

有效批次 `robust_full_r2`，4873.892 秒，1810 步、15220 块帧、64010 对。P1/P2 相同判据仅为**窗口状态及首盖身份集合**，不比较精确时刻，也不把 initial_overlap 标签相同冒称 PD 排序已认证。严格扫掠证书可直接证明无接触而不做无谓求根；初态重叠按共享几何直接分类，其余走精确首入。

| 算例 | 步 | 对 | 稳健无接触 | 稳健单首盖 | 敏感或未证 | 已观察P1/P2不同 |
|---|---:|---:|---:|---:|---:|---:|
| bb03 | 100 | 5500 | 4080 | 1 | 1419 | 0 |
| bb05 | 100 | 600 | 204 | 0 | 396 | 0 |
| bb06 | 100 | 600 | 227 | 0 | 373 | 0 |
| bb09 | 100 | 6600 | 4384 | 0 | 2216 | 0 |
| bb10 | 100 | 6600 | 4651 | 0 | 1949 | 0 |
| bb12 | 100 | 5500 | 3501 | 1 | 1998 | 0 |
| bb50 | 50 | 50 | 49 | 0 | 1 | 0 |
| bb51 | 50 | 2750 | 1954 | 0 | 796 | 0 |
| bb52 | 50 | 2750 | 1765 | 0 | 985 | 0 |
| bbF038 | 30 | 30 | 0 | 0 | 30 | 0 |
| bbS038 | 30 | 30 | 0 | 0 | 30 | 0 |
| bbv01 | 100 | 4500 | 2198 | 0 | 2302 | 0 |
| bbv01_dbv01a | 400 | 18000 | 9853 | 0 | 8147 | 0 |
| bbv02 | 100 | 2100 | 998 | 0 | 1102 | 0 |
| bbv02_dbv02a | 400 | 8400 | 4817 | 0 | 3583 | 0 |
| 合计 | 1810 | 64010 | 38681 | 2 | 25327 | 0 |

未证分层：已贯入出口顺序未证 16676；其余无充分证书 8651；观察到 P1/P2 状态/首盖差异 0。独立初态 G0 求值 30968 对，其中 **14292 对与 P1/P2 生产结果交叉核对，零失配**；其余 16676 个初态贯入对由 G0 直接分类，未再调用生产初态谓词，不能计作交叉验证。P3 只在稳健子集由严格管证明结论不变，敏感部分没有完整超越根结果。

[冻结完整摘要](file:///D:/eab-wt/cx-e2/reports/codex/M5b_evidence/robust_summary.json) 绑定输入与完整生产源码；每5步进度落盘，开始/结束双核验。大逐对表在 ignored tmp，只冻结其SHA256。

## 6. 四个问题的直接回答与最小例

### 6.1 legacy 选的参考是不是首盖？

**本节历史稳健单首盖样本仅 n = 2/68**（68 个本步新接触块对中的 2 个），66 个未证，不可外推。历史表只统计主参考 primary（raw[1:4]），不把次参考算入。M5c 已另行统计全部参考（含 VV 第二参考），见 M5c 报告。对这 2 个已认证步—块对：

| 阶段 | 主参考首盖匹配条数 | 其它主参考条数 | 无该块对记录的步—块对 | 首盖未选作主参考的步—块对 | 稳健无接触窗口中的主参考条数 |
|---|---:|---:|---:|---:|---:|
| raw_df05 | 1 | 3 | 0 | 1 | 11443 |
| post_df06 | 2 | 2 | 0 | 0 | 11443 |

冻结字段 `ROBUST_FIRST_COVER_NOT_SELECTED` **仅解释为 PRIMARY_NOT_SELECTED**。独立审查确认每阶段还有7768条次参考；其结果未纳入本单结论。合成语义门固定该口径，避免次参考恰为首盖时误报“所有参考都漏了”。

最小真实反例：bb03 第15步 (8,11)，raw_df05 主参考非首盖，**首盖就在同一 raw 行的 m4–m6 共边候选槽（非 VV 正式第二参考）**，不是全部参考漏掉首盖；post_df06 有主参考首盖匹配；bb12 第6步 (10,11) 两阶段都有匹配与其它主参考。二者均通过 P1/P2 和 P3/舍入管身份认证。它们说明“主参考总是首盖”不成立；不据此直接归因为求解器缺陷。

### 6.2 漏检？

仅把稳健单首盖对在某阶段**完全没有该块对记录**计为窗口块对漏检，数量见表。主参考未命中不等于块对漏检；存在次参考时尤其不能混同。若计数为0，只能说这个已认证子集中未见，不能推到全部64010对。无接触子集只证明该窗口没有接触，不用于虚构漏检阴性样本。

### 6.3 已贯入时参考边与全局最短出口？

**未完成所要求的正扰动稳健排序。** 三种指定模型在 s=0 的名义几何完全相同，自己的 s*端点校正也在0为零；这是模型定义恒等，不等于任意正初态误差管下最近出口标签不变。本单保守均记 INITIAL_EXIT_ORDER_UNCERTIFIED，没有把历史 M4c PD 值重标成新稳健结论。自包含 bb03 第1步 (2,3) 是该遗留的最小真实输入；不提供伪造的稳健 PD 计数。

### 6.4 三种模型之间的差异比例？

P1/P2 实际轨迹比较 **14079 对（其中 68 对本步有新接触），差异 0/14079**。另有 **16889 对由共同初态构造必然相同（16676 贯入 + 213 接触）**，以及 **33042 对由双盒严格证书直接判定无接触**；三项合计 64010。后两项不是独立轨迹求根比较样本；全部口径均不含首时刻差异/PD 排序。在稳健子集三者身份/无接触结论差异为 **0/38683**，这是充分证书保证、并有选择偏倚，不能推断全集差异率。未证子集的 P3 差异未知，故**完整三模型差异比例仍 PARTIAL**。

最小例以同一真实输入同时重算三类认证所需量：bb03 第1步 (1,3) 为稳健无接触；bb03 第15步 (8,11) 为稳健单首盖；bb03 第1步 (1,2) 为未证而不擅称不同。没有观察到的差异不编造反例。

[五个真实最小例](file:///D:/eab-wt/cx-e2/reports/codex/M5b_evidence/robust_minimal_examples.json) 已**另外重新执行**，不是截取部分长跑输出当有效批次。`python -X utf8 tools/m5b_minimal_examples.py` 默认验证全部精确结果和证书，不会重冻结；默认pytest真实重算同五例。

## 7. INT1 小项、共享域与逐站准入

- as_rational 的模素数筛必须遍历余数0，新增只在0有模根的有理根门，内部 `range(prime)->range(1,prime)` 缺陷命中语义断言。
- semantic_guard/hash masking 移入 test-driver，不再算共享变异域。旧审查对象保持原值，新范围/来源绑定只追加记录。
- caller 导入来源纳入绑定；独立审查进一步找到同名 def/class 遮蔽漏洞，修复后整调用模块规范化文本 pin 与作用域 pin共同约束，并有 def/class 负向及去pin内部变异门。保留初始RED审查证据。
- 13种规则的 proof_domain 明确“反射得到 float”不在豁免保证内；共享源变异机制不声称数值 oracle 精确性。
- M3新增行、INT1-C行、续审记录、共享记录均加不可变前缀/只追加pytest门。旧历史不删除、不改写；新增记录有逐条理由。

**逐规则×AST occurrence（含行/列）口径**：原逐站 3558+共享 104=3662；当前逐站 3618+共享 77=3695；净增 **33**。档案行数 3522 不是站点数，active context行数 3416 也不是站点数；共享的一条审查更不能算一站。

新增生产/独立oracle有逐站审查理由；旧 algebraic pin 续审不算净新增。共享减少27处是迁入现有test-driver排除范围，**不冒称全仓豁免减少27**。4条历史context-only ghost pin 如实单列，保留旧档案但不计实际站点。未为凑净0而扩大共享域或把独立数值oracle移进driver。

[逐站机器清单](file:///D:/eab-wt/cx-e2/reports/codex/M5b_evidence/admission_rule_sites.json) · [逐条新增审查](file:///D:/eab-wt/cx-e2/reports/codex/M5b_evidence/new_admission_review.json) · [INT1专项报告](file:///D:/eab-wt/cx-e2/reports/codex/M5b_evidence/int1_work.md)。

## 8. 冻结绑定、四片最后一行与性能

algebraic 上限修改触及 M5a/M5a2 闭包。`m5b_refresh_replay.py --name se2_refresh_r1` 实际重算15×30=450个冻结前缀帧，逐叶语义和全部历史normalized哈希一致后才发布新revalidation/provenance。旧INT1来源链保留，先存原字节。**没有只改哈希。** M4c准确源码闭包未变，不虚称重跑不需要的M4c；其现行绑定由完整测试核验。

最终有效四片 `final_r1` 最后一行原样：

```text
3414 passed in 729.01s (0:12:09)
3414 passed in 1249.87s (0:20:49)
3414 passed in 735.89s (0:12:15)
3414 passed in 826.19s (0:13:46)
```

静态最后一行原样：

```text
exact construction AST gate: 0 violation(s)
```

总收集 = 实际call执行 = **13656**，唯一节点、四片无重叠；全部setup/call/teardown passed，0 skip。不是把派发清单当执行清单。新鲜字节副本执行前后无漂移，src/tests/tools/fixtures与当前树一致；用户禁止worktree，因此明确 `fresh_git_checkout=false`，不冒称满足新鲜Git检出条件。

基线call累计 3500.246s，新门call累计 2.945s，占基线 **0.0841%**，低于约5%预算。宿主并发审查/回放，`controlled_host=false`；不把整体时间比声称受控性能结论。全时程回放不塞入默认pytest。

[执行同一性](file:///D:/eab-wt/cx-e2/reports/codex/M5b_evidence/execution_audit.json) · [性能](file:///D:/eab-wt/cx-e2/reports/codex/M5b_evidence/performance.json) · [节点增量](file:///D:/eab-wt/cx-e2/reports/codex/M5b_evidence/suite_delta.json) · [真实冻结重算证明](file:///D:/eab-wt/cx-e2/reports/codex/M5b_evidence/se2_refresh_r1_attestation.json)。

## 9. 独立审查、复跑与回滚

六域复核：P2数值/理论、端点与外部口径、稳健证明、全量接线/legacy口径、INT1静态/历史绑定、最终执行证据。作者不以自己的专项测试替代独立审查。实际发现共享def/class遮蔽major已修复；primary-only和外部中点口径以明确范围和PARTIAL处理，未冒称完整G6退出。

独立审查文件：[P2](file:///D:/eab-wt/cx-e2/reports/codex/M5b_evidence/review_p2.md) · [端点](file:///D:/eab-wt/cx-e2/reports/codex/M5b_evidence/review_endpoint.md) · [稳健证书](file:///D:/eab-wt/cx-e2/reports/codex/M5b_evidence/review_robustness.md) · [回放接线](file:///D:/eab-wt/cx-e2/reports/codex/M5b_evidence/review_replay.md) · [INT1](file:///D:/eab-wt/cx-e2/reports/codex/M5b_evidence/review_int1.md) · [执行与发布](file:///D:/eab-wt/cx-e2/reports/codex/M5b_evidence/review_execution.md)。

另由非回放作者对有效全批逐对表完成[独立执行审计](file:///D:/eab-wt/cx-e2/reports/codex/M5b_evidence/review_model_execution.md)：15例集合完整、主参考守恒、52源码/91输入哈希一致；用独立扇形形心、阶乘 Taylor 和复乘构造重算全部15220块预算，38683个稳健对的半径和逐值一致、证书余量全为正。此审计不重复全部几何求根，不冒充总体G6退出。

本节审查链接和上节端点直接绑定边界为报告生成后的编辑性补充；没有改动已执行冻结的报告生成器或任何生产/测试/工具/夹具文件。

复跑先在PowerShell设置：

```powershell
$env:TEMP = "$PWD/reports/codex/M5b_evidence/tmp"
$env:TMP = $env:TEMP
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:PYTHONIOENCODING = 'utf-8'
python -X utf8 tools/m5b_minimal_examples.py
python -X utf8 tools/m5b_robust_replay.py --name <fresh_name>
python -X utf8 tools/m5b_run_gates.py --name <fresh_suite>
python -X utf8 tools/m5b_finalize_evidence.py <fresh_suite>
```

长回放必须新目录，中断整批作废。当前工具拒绝覆盖已冻结robust_summary，重跑可在新鲜字节副本独立执行，或先将旧摘要复制归档后由所有者明确发布新轮；不得只更新绑定值。端点工具命令见endpoint_work.md。pytest一律 `-p no:cacheprovider` 和显式 `--basetemp`；大日志、节点与逐对表只在ignored tmp；交付文本UTF-8无BOM。

回滚锚点：只读df4f6f1对象、`se2_refresh_r1_before.json`、历史policy前缀和原输入哈希；未执行任何破坏性恢复。按实际修改文件逐项回退，不得 broad reset/checkout。

## 10. 遗留（不以测试全绿冲销）

1. 已贯入时参考边与全局最短出口的正误差稳定排序尚未实现，不能给稳健PD结论。
2. legacy次参考未统计；主参考/缺失块对口径不可扩张为所有legacy盖。
3. P3敏感子集超越首入和完整三模型比例未知；未证并列/凹环不是判错。
4. 外部2.8e-6与本次全15例9.6264e-6中点最大值的原始验收程序口径未对齐。
5. 没有新鲜Git worktree及完整工单G6退出声明；本单使用明确披露的新鲜字节副本和分域独立复核。

M5b_PARTIAL：已贯入正扰动最短出口排序；legacy次参考；敏感子集P3首入与完整三模型比例；外部2.8e-6口径对齐；完整G6退出
