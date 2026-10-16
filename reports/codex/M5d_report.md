# WO-M5d 中文交付报告

## 结论与信任边界

A1–A4、B5–B7 已完成；C1 在已证明的严格凸、跨环非平行、唯一出口子域实现并完成全量回放。
16676 个初态贯入对认证 4280 个，未证 12396 个明确分列。未认证不等于真实不稳健，不向凹环或全时程运动外推。
本报告是工单实现与团队交叉复核交付，**不代替 Claude/所有者的六路 G6 独立退出验收**，不修改 README 声称。

初始基线为干净 `codex-work @ 5b73cc8dfc1ad4f257412392111927d5a7171640`。
仅写当前工作树；其他工作树及姊妹仓库只读，无 commit/push/reset/checkout/stash/worktree/branch 操作，无新依赖。
由于禁止 worktree，基线用只读 `git archive HEAD`，最终用全新字节导出；明确 `fresh_git_checkout=false`，不冒充新克隆。

关键索引：[数值合同与 imports](file:///D:/eab-wt/cx-e2/docs/m5d_numeric_inventory.md)、[交付清单](file:///D:/eab-wt/cx-e2/reports/codex/M5d_evidence/delivery_manifest.md)、[机器执行审计](file:///D:/eab-wt/cx-e2/reports/codex/M5d_evidence/execution_audit.json)。

## A 的变异总账与口径

本单数值主门合计 33 个真实内部变异：R3 21、R1/R2 回放 6、C1 6；另有冻结发布流程 1 个内部变异。
全部通过真实被测函数体编译替换执行，直接调用新具名语义门，未选择源码哈希和冻结摘要快照测试；不是枚举后追加假产物。
其中 R3 12 个是实际错误公共证书，2 个是公共充分条件合同、7 个是内部预算恒等式；C1 2 个穿过公共 API、4 个是内部排序合同。
回放 6 个均穿过实际回放或 R2 生产路径。不能将 33 个全称作已找到物理错误证书。
各变异的实际 AssertionError、输入及断言名分别在 `r3_semantic_evidence.json`、`replay_semantic_evidence.json`、`c1_mutations.json`。

| A1 子条件 | 真实内部改坏 | 具名门（`tests/test_m5d_r3_semantics.py`） |
|---|---|---|
| 早期全窗 | 跳过 / 缩短 / 只查后半段 | `test_r3_complete_early_window_rejects_prebracket_contact` |
| EV 竞争者 | 不枚举 EV | `test_r3_ev_competitor_precedes_nominated_ve` |
| 两侧边内投影 | 分别省略 g / h | `test_r3_both_projection_sides_reject_line_extensions` |
| 末段 | 省略最后子窗 | `test_r3_final_panel_rejects_departed_endpoint` |
| L1 对偶归一 | 用 L∞ 替代 L1 | `test_r3_linf_tube_requires_l1_dual_normalization` |
| 端点扣费 | 末端不扣误差 | `test_r3_endpoint_budget_prevents_actual_out_of_bracket_contact` |
| 边长预算 | 省略 dw·norm(U)，A / B 活动分别构造 | 同上及 `test_r3_bilinear_budgets_include_both_endpoints_and_all_terms` |
| 不等分母 | 错走等分母相减支路 | `test_r3_unequal_p2_denominators_reject_false_time_bracket` |

### A2：R1 必须认证两个名义路径的管

新 `test_replay_r1_requires_p2_tube_even_when_both_nominal_paths_are_separated` 构造 P1 与 P2 名义都不接触、
P1 管可分离而 P2 管有接触的实际回放输入；不靠双盒直判，也不是名义 P2 已接触的简单格子。
A 三角形为 `(10,-1/2),(-5,1),(-5,-1/2)`，P2 转动半角参数 1/20；B 的 x 范围为 `[501/50,401/40]`，y 为 ±1/1000。
ra=1/100，rb=0；P1 最大 x 加管宽只有 10.01。P2 名义顶点范数平方至多 401/4，仍在 B 左侧；
但 s=1/2 时 A 顶点为 `(16030/1601,1/3202)`，允许的端点为零的扰动 `dx(s)=4ra·s(1-s)` 将其送入 B。
把真实 `compare_pair` 的无接触证书接线改成只查 P1，红在 **R1 both-path tube gate**。

### A3：温和 R2 变体

`test_r2_mild_early_truncation_rejects_a_short_prior_penetration` 用窄时间窗轨迹，
真实早接触位于括区之前，省略最后 1% 或 0.1% 的早期窗口都会签错，而完整生产 R2 拒签。
`test_replay_single_cover_keeps_both_tubes_and_the_full_radius_at_the_threshold` 选 P1 速度 2.001、P2 速度 2，
公共括区 `(519929/1048576,528385/1048576)`，半径 `16392071/2097152000`：P1 可证、P2 不可证。
两条名义首标签相同不能掩盖 P2 管内首时刻越过上界。真实 `all→any`、只查 P1、半径乘 0.99 三种接线变异均红在具名语义断言。
这两组加 R1 共 10 节点 / 6 内部变异；独立期望为 Fraction 恒等式，不调用生产几何原语。

### A1 / A4：完整语义门和阈值对抗结果

#### 已验证默认门

- `41 passed in 28.71s`，0 skip；具名耗时见 `r3_pytest.log`。
- 21 个真实内部变异全部在新的具名语义 AssertionError 上判红：12 个实际几何错证反例、2 个公共证书预算合同拒签、7 个 helper 精确预算恒等式。源码哈希和冻结快照不参加判红，不能把 21 个都叫作实际错证。
- 八类主门分别是：早期全窗、EV 竞争者、两侧投影、末段、L1 对偶归一、端点扣费、边长误差预算、不等分母相对向量。
- 端点扣费与边长删项均有实际管内首时刻 `103/200 > 51/100` 的反例；边长另分 A 顶点活动和 B 边端点活动两个输入。
- 额外 `du||W||1` 和混合项仅为证明预算合同拒签，W/V 六个删项及 `ev=ew` 混用端点仅为精确预算恒等式；W/V 长度分别为 8 和 10，不计为已找到物理错签反例。
- 测试和独立 oracle 两个新文件的局部静态扫描均为 0 违例，未增加准入。
- R3 生产公式、旧 M5c R3 数值结果和共享策略未修改；整个工单另有注释订正触及回放闭包，真实重算与发布见主报告，不混称所有旧冻结文件字节未变。

#### 独立 oracle 与阈值

主 oracle 只导入 Fraction、lru_cache、comb；辅助平移 oracle 只导入 Fraction。没有生产几何原语导入。每条轨迹都先独立证明初态凸包严格分离，然后用独立多项式和 Sturm 根计数核闭边入射。

默认 P2 构型的两块均有转动、平移、非零对称应变；分母为 `1+s²/100` 与 `1+s²/25`。40 次二分得到保守 rlo，不确定宽度小于边缘偏移的 1/64；在 `rlo*(1-2^-24)` 与 `rlo/2` 检查非刚体逐顶点时变扰动的首标签和首时刻开括区。有限扰动不代替全管定理。

长 runner 已从头完成六个不同名义形状和相对位置，耗时 187.43 秒（不进入默认 pytest）。四个构型在阈值边缘与半阈值处通过，每个 64 条，共 256 条时变非刚体管内轨迹，首标签及首时刻开括区双检查零失配。两个构型连零半径充分条件都未通过，单列未证，不外推。

| 名义构型 | 结果 | 扰动数 | 限制 / 拒签子条件 |
|---|---|---:|---|
| diamond | CERTIFIED | 64 | 尖菱基准 |
| asymmetric_triangle | CERTIFIED | 64 | 非对称三角形 |
| near_corner | UNPROVED | 0 | 四个缩窄括区均 `early_separation` |
| concave_notched | CERTIFIED | 64 | 简单凹环，非凸域 |
| skew_wall | CERTIFIED | 64 | 不同墙体边长与形状 |
| near_tied_tips | UNPROVED | 0 | 宽括区 `competitor_VE`，缩窄后 `early_separation` |

所有认证构型均使用 40 次有理二分，宽度 `1/8796093022208`；每项 rlo、上下界、独立名义根区间、每条扰动根区间和源码摘要均在 JSON。脚本运行首尾摘要一致，完成后再次核当前文件摘要全匹配。证据 JSON 133621 字节，未生成超过 1 MB 的交付日志。

本轮增强 runner 补强并替代 M5c 旧 D=1 审计的“本轮阈值覆盖”角色，但不改写旧脚本或冻结证据，也不声称已把旧 90 个构型全部推进到阈值边缘。

#### 编码缺陷说明

原始中文草稿曾被 PowerShell 管道转成问号，独立复核发现后已重写本片段及理论文件为 UTF-8 无 BOM。理论合同在实现前已讨论并沿用既有 M5c 定理，但当前重写字节不声称先于实现。此缺陷不涉及 Python 数值源码或测试结论。

#### 文件

- `docs/m5d_r3_theory.md`
- `tests/test_m5d_r3_semantics.py`
- `tests/m5d_r3_oracle.py`
- `tools/m5d_r3_evidence.py`
- `reports/codex/M5d_evidence/r3_semantic_evidence.json`
- `reports/codex/M5d_evidence/r3_pytest.log`

重跑：`python tools/m5d_r3_evidence.py --count 32`。被中断则整次作废重跑，不拼接。
## B：措辞、19/68 子集与 legacy 槽语义

本片段的计数已由不可变 endpoint/legacy 输入独立重建。最终冻结已真实重算并发布（7 个产品，64,010 条观察重合并、68 个首接触候选重解）；随后已备份旧 B 产物并重新执行 `tools/m5d_wording_audit.py`（未启用 `--source-review`），逐个核验全部 92 个当前输入绑定。新旧 B 审计字节完全相同，19/49/17 及全部名义命中计数不变；这不是只改哈希。B/accounting 局部门亦真实重跑，最后一行 `22 passed in 1.95s`。**最终四片及逐站审计见主报告后节；不宣称所有者 G6 完成。**

### B5：19/68 子集结构与 49 对名义对照

**19 个认证步—块对全部是两行 `mtype=0` 的边—边近平行构型，并非一般接触构型的代表性抽样。** 两支承方向的精确 `sin²(angle)` 最大值约为 `0.000194987734`；描述门检查 `sin²<1/300`，这个界只用于描述子集，不是新增认证容差。68 个候选中，12 个含 VV 行的块对、6 个多于两行的拥挤块对，全部落在 49 个未证项中；两类可重叠。

去重规则为 **`(算例, 无序块对, 规范化首特征集合)`，忽略步号，不跨算例合并**，得到 **17 个特征构型身份**。唯一的本规则重复组为 bb05 第 3、11、20 步 `(2,3)`，首特征均为 `VE(18,{11,12})`。这个 17 是明确规则下的拓扑特征去重数，**不声称不同步的精确几何相同，不声称 17 个统计独立样本，也不排除跨算例仍有相似构型**。

下表均为块对级“至少一个命中”；三个单列可能重叠，不能任意相加。VV 二参是正式第二参考，共边槽单独列出。

| 子集与阶段 | 分母 | 主参考 | VV 第二参考 | 共边槽 | 主 + VV | 全槽 | 完全无该块对记录 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 已认证 / raw_df05 | 19 | 7 | 0 | 12 | 7 | 19 | 0 |
| 已认证 / post_df06 | 19 | 19 | 0 | 0 | 19 | 19 | 0 |
| **未认证，仅名义** / raw_df05 | 49 | 31 | 9 | 8 | 40 | 48 | 0 |
| **未认证，仅名义** / post_df06 | 49 | 38 | 9 | 1 | 47 | 48 | 0 |

为避免混淆“行数”与“块对数”，两阶段各自的记录规模如下：

| 子集 | 主参考行数 | VV 第二参考行数 | 共边槽数 |
|---|---:|---:|---:|
| 已认证 19 对 | 38 | 0 | 25 |
| 未认证 49 对 | 135 | 12 | 32 |

49 对的表格是**未认证名义观察，不作稳健命中、模型敏感或漏检结论**。唯一名义全槽未命中为 **bb51 第 2 步 `(3,9)`**，名义首特征 `VE(93,{149,153})`。两阶段各有该块对两行记录，所以这不是 missing-pair：

| 阶段 | 两个主参考 | VV 第二参考 | 共边槽 |
|---|---|---|---|
| raw_df05 | `VE(92,{149,153})`；`VE(149,{93,94})` | `VE(149,{92,93})` | `VE(149,{92,93})` |
| post_df06 | `VE(149,{92,93})`；`VE(149,{93,94})` | `VE(149,{92,93})` | `VE(92,{149,153})` |

具名门：`test_certified_nineteen_are_two_row_near_parallel_ve_not_vv_or_crowded`、`test_case_pair_first_feature_dedup_has_seventeen_not_nineteen_identities`、`test_unproved_49_remain_nominal_including_bb51_step2_pair3_9_all_slot_miss`。

### B6：post_df06 主参考 19/19 的准确含义

这 19 对的首盖总在 legacy 已保留的角候选中：原主参考已命中 7 对，其余 12 对的首盖位于相应行的主/共边两组三元组候选之中，`df06` 换半将其放到主参考。因此 post 主参考为 19/19。

**post_df06 正是随后 df07 / 弹簧装配消费的接触表，不是仅供报告的旁路表。** 共边槽本身不作为独立弹簧参考另行装配，但影响换半与接触长度；被换到主参考后便进入求解所用表。实际弹簧是否激活仍受开闭状态控制，19/19 不等于已证明 19 次非零弹簧载荷贡献。

只读源码核对位置：

| 语义 | df.c 行号 | bdda2 文件与行号 |
|---|---|---|
| 邻边近平行转 VE、保留共边两半 | 1619–1649 | `detect/classify.hpp` 66–86 |
| VV 完整第二三元组 | 1660–1681 | `detect/classify.hpp` 88–106 |
| df06 主/共边三元组换半 | 1832–1853 | `stepper/transfer.hpp` 118–125；137–144 将表写入 `out[i].t7` |
| post_df06 表进入后续求解 | 1880–1903、1935–1949 | `driver/run.hpp` 414–430 冻结该表，438–460 消费 `rows` 并调用 `df07_o5` |
| 共边槽影响接触长度 | 1935–1949 | `stepper/transfer.hpp` 148–174 |
| VE 不另装配第二弹簧；VV 可选第二参考 | 3215–3238，`jj<=m[i][0]` | `stepper/step_system.hpp` 167–209；`driver/run.hpp` 459–460 |

`df.c` SHA256 为 `a097a636990aee34cd0c2f856aa52a81c12e9ba9136f233004719be91158fcee`；其余文件完整哈希与带行号摘录见下方只读源证据。没有修改或运行姊妹源码。

具名门：`test_post_df06_primary_hit_means_promotion_of_retained_angular_candidate`，逐行检查原主/共边与换半后两槽的对应关系。

### B7：raw 编号与规范化编号分开

撤回“VV 的 m5/m6 可以是实际顶点 ID 0”的理由：**raw 实顶点编号 ≥1，0 是首块前垫位，即末顶点副本，不是 raw 实顶点。** 证据为 `df.c` 894–902，`bdda2/io/case_data.hpp` 97–105、113–118。

冻结环从前垫位起保留一个周期并去掉尾部两重复别名，故**规范化 ID 0 可以是合法边端**。例如正 raw ID `4,5` 可映射到规范化 `0,1`。旧测试中不存在的 raw VV `m5=0` 约定已改成正 raw 别名路径；生产解码条件不改，只订正注释与解释。

具名门：`test_positive_raw_vv_edge_ids_normalize_to_legal_canonical_zero`。另有 `test_all_68_reference_slots_match_independent_literal_oracle` 将全部 68 对、两阶段所有槽与独立周期模运算 oracle 对账，零失配；近乎平行描述另有非轴旋转、大平移及单位元门。

### 历史 M5c 订正边界与证据

已同步订正历史 `M5c_report.md` 及其生成器 `tools/m5c_report.py`，避免再次生成错误 raw-ID 理由和含混的“求解器不一定使用该表”措辞；同时补明 19 对的结构、17 类规则、49 对名义观察。`tools/m5b_robust_replay.py` 仅修改说明性注释，触及其冻结闭包的真实重算及发布已由主代理完成，发布记录为 `frozen_refresh.json`，不是仅刷新哈希。

**不追改历史里程碑能力边界**：M5c 的 C 部分仍是当时未实现状态。M5c combined 摘要里的初态出口认证 0，指该历史首盖回放产品没有做 C1；M5d 新 C1 结果另列新证据，不把两种产品、认证子集或分母混在一起。最终四片及逐站审计见主报告后节；所有者 G6 不由本片段代签。

独立 B 审计 imports 仅为 `argparse / collections / fractions / gzip / hashlib / json / pathlib`；不导入生产几何或姊妹模块。冻结首特征与认证标志是输入观察，不冒充独立 R3 几何 oracle。

证据：[逐对 B 审计](file:///D:/eab-wt/cx-e2/reports/codex/M5d_evidence/b_wording_audit.json)、[只读源码行号与哈希](file:///D:/eab-wt/cx-e2/reports/codex/M5d_evidence/b_legacy_source_review.json)、[B 局部门记录](file:///D:/eab-wt/cx-e2/reports/codex/M5d_evidence/b_tests.json)、[发布后 B 实算与绑定核验](file:///D:/eab-wt/cx-e2/reports/codex/M5d_evidence/b_post_refresh_verification.json)、[完整订正文档](file:///D:/eab-wt/cx-e2/docs/m5d_legacy_semantics.md)。旧 B 审计及局部门记录分别保存在同目录的 `b_wording_audit_before_frozen_refresh.json`、`b_tests_before_frozen_refresh.json`、`b_tests_before_frozen_refresh.txt`；这些均为小文件备份。
## C：C1 定理、实现、全量计数与最小例

### 结果与范围

先行证明 `docs/m5d_c1_theory.md` 已补全：全部边—非端点顶点叉积证明严格凸环存续；支撑面恒等式与跨环边非平行性给出 Minkowski 全部闭边的标签一一对应，排除遗漏、新暴露与拆分。随后才计算全边距离。

生产证书 `src/eab/kernel2d/m5d_exit_certificate.py` 使用精确 Fraction，严格检查 q > 2r²、对全部竞争边 h=qj−q−8r² > 0、h² > 32qr²；凹环、平行边、原并列均拒签。独立 oracle 不调用生产几何原语，仅 import fractions.Fraction，以全部顶点差的 monotone-chain 凸包及独立行列式距离公式对照。

C1 全量新算用时 68.055 秒；1810 步、15220 块帧、64010 步—块对中独立初态 oracle 检出 16676 贯入对；认证 **4280**，全部半径和严格大于零，名义独立 oracle **4280/4280、零失配**。未证 **12396**，不外推。

**口径限制：这是初态几何周围顶点 L∞ 盒内的出口排序证书，半径采用同 M5b 的 bound + residual + endpoint_parameter。不是把整个步的名义几何位移算入该初态小盒，也不声称全步出口标签持续不变。**

|算例|初态贯入|认证|严格凸失败|法向序失败|排序失败|
|---|---:|---:|---:|---:|---:|
|bb03|1145|370|775|0|0|
|bb05|327|325|0|2|0|
|bb06|299|297|0|2|0|
|bb09|1652|1649|0|0|3|
|bb10|1349|1141|208|0|0|
|bb12|1779|391|1386|2|0|
|bb50|0|0|0|0|0|
|bb51|613|0|613|0|0|
|bb52|869|49|820|0|0|
|bbF038|29|29|0|0|0|
|bbS038|29|29|0|0|0|
|bbv01|1584|0|1584|0|0|
|bbv01_dbv01a|4106|0|4106|0|0|
|bbv02|794|0|794|0|0|
|bbv02_dbv02a|2101|0|2101|0|0|

未证原因合计：RING_NOT_STRICTLY_CONVEX 12387；CROSS_NORMAL_ORDER_UNPROVED 6；EXIT_ORDER_UNPROVED 3。名义非严格凸的 API 拒绝域可包括凹环、共线等，不能仅从 reason 标签推断全是凹环。独立逐环全边—非端点顶点叉积细分（c1_nonconvex_audit.json）发现本数据 12387 对均至少有一个负支撑侧叉积；只有零叉积而没有负叉积的纯共线拒绝对为 0。它们直接失败在 C1 第 1 条，并未对遮盖边、新暴露边作没有依据的距离差认证。

### 4280 个认证对上的 legacy 参考（严格分槽）

|阶段|槽|总参考条数|属于唯一全局最短出口特征的条数|其余条数|命中步—块对|
|---|---|---:|---:|---:|---:|
|raw_df05|primary|8055|3226|4829|3226|
|raw_df05|secondary|424|349|75|349|
|raw_df05|shared_edge|4437|705|3732|705|
|post_df06|primary|8055|3931|4124|3931|
|post_df06|secondary|424|349|75|349|
|post_df06|shared_edge|4437|0|4437|0|

两个阶段的全部有效槽合计都命中 4280/4280 对，完全未命中 0。raw 主参考命中 3226，VV 第二参考另命中 349，共边槽另命中 705；post 主参考命中 3931，VV 第二参考 349，共边槽 0。**不是每条 legacy 参考都最短**；“其他条数”清楚说明了这一点。未证参考仅计数，保存在 c1_summary.json 的 unproved_references，不作出口命中结论。

### 对抗门与真内部变异

最后局部 pytest 真实末行：`21 passed in 0.13s`，包含新增的产物互异、非零查询、循环重编号和双块独立平移元门。固定种子中 3 构型×2 阈值半径×24 双块非刚体扰动 = 144 次独立 oracle 零错。另跑 `tools/m5d_c1_adversarial.py`：48 构型、40 次二分阈值括区、96 认证半径、6144 双块非刚体扰动，零反例。半径采用已认证下端 r_low 的 r_low·(1−2⁻²⁴) 与 r_low/2；不把二分下端冒称精确代数阈值。

`c1_mutations.json` 保存 6 个真实函数体变异及实际 AssertionError：去凸性门、去跨环法向门、内部性严格不等式改非严格、只查首竞争者、排序平方严格不等式改非严格、删除 h 正支约束。均未调用源码哈希绊线或冻结快照门；红在具名语义断言。前两项穿过公共 API；后四项是内部 _rank_guard 的精确标量合同门。尤其负 h 的 qj<q 反例在公共 q=min 路径不可达，不应把该辅助合同门夸大为公共 API 端到端错误证书反例。

不变性门包含有理旋转、工程坐标中 1e3/1e5/1e6 量级平移及极大/极小单位缩放；认证标签不变、平方距离按 s² 变化。旋转盒采用诱导 L∞ 范数扩张，不承诺边界附近的充分条件接受状态绝对相同。

### 最小构造与数值登记

三角形—三角形是顶点数最小的合法环构造：A=((0,0),(4,0),(0,3))，B=((1,1),(5,2),(2,5))，ra=rb=1/10。唯一出口 EV(1,0)，q=1；跨边余量 8/25，凸性余量 243/25、318/25。精确证书见 c1_minimal_example.json。

已在 `docs/m5d_numeric_inventory.md` 登记：exit_order_certificate 输入仅 int/Fraction，非负顶点 L∞ 半径，严格 CCW 凸环与跨环非平行是充分准入；输出 UNPROVED 不代表真实不稳健。_rank_guard 所有运算精确，根号通过正支平方消去；无 float、绝对容差、κ 膨胀或隐式转换。

独立审查/G6 由上游独立验收者执行，本片段不自行宣称通过 G6；凹环一般 C 证书仍未实现，但本单指定的保守严格凸 C1 子域已实现并全量运行。

静态审查触发的纯语法重构后已完整重算：新 c1_full_02 与 c1_adversarial_02 首尾闭包一致；此前的摘要保留为 c1_summary_before_static_refactor.json / c1_adversarial_before_static_refactor.json，不以修改哈希替代计算。

## 独立性、元门及数值合同登记

主 oracle import 清单和每个具名门见 `docs/m5d_numeric_inventory.md`；R3 主 oracle 只 import Fraction/lru_cache/comb，
平移辅助 oracle 仅 Fraction；C1 主 oracle 仅 Fraction；B 槽对照不 import 生产几何或姊妹模块。
输入适配器一致性不冒充 oracle。团队另用独立闭式旋转根 `4−2√3` 核 R3，用穷举支撑半平面第三路径核 C1，均零失配。
元门含非轴向有理旋转、工程坐标大平移、单位缩放及标签置换/产物互异；L∞ 盒旋转按诱导范数保守扩张，
不要求边缘处充分条件的最大认证半径旋转不变。所有新几何判据精确有理，无无关绝对阈值。

## 冻结绑定：真实重算而非改哈希

`tools/m5b_robust_replay.py` 的改动只是 raw ID 注释，但它位于冻结运行时闭包，仍按规则完整重算。
实际新 robust 批次 `robust_full_m5d_r1` 重新计算所有 64010 个步—块对；research 批次 `research_full_m5d_r1`
遍历同一全量、重解全部 68 个候选。联合发布逐项比较 64010 个 P1/P2 精确观察，连接全部 68 个研究结果。
最小例、研究最小例和 523 次初态见证试探都重新调用真实计算（3 对找到见证，65 对在八偏移内未找到），比较完数值产物才发布七个冻结文件；原字节保留备份。
原 M5c combined 的 C 未认证口径是其历史阶段，当前 C1 独立证据不偷偷改写旧阶段的含义。
发布器统一封印 source/input/inherited/candidate/backup，发布前后每阶段复核。
强制终止不是跨文件原子事务；外部编辑目标/备份时拒绝不安全覆盖，不保证强杀后自动恢复。中断批次作废，不拼接。

实际 robust 用时 5022.007s；research 用时 1465.091s。发布数 7，完整绑定与前后哈希见 `frozen_refresh.json`。

## 最终四分片、静态与准入

四片最后一行原样如下（不是计划执行数）：

```text
3470 passed in 895.95s (0:14:55)
3469 passed in 760.00s (0:12:40)
3469 passed in 1434.03s (0:23:54)
3469 passed in 688.12s (0:11:28)
```

收集 = 执行 = **13877**，0 skip；每个节点 setup/call/teardown 各一次且全部 passed。相对基线新增 96 节点、移除 0 节点。
静态末行原样：`exact construction AST gate: 0 violation(s)`。最终源码导出执行前后文件集合/字节均未变，当前可执行文件与执行导出零漂移。

逐站反事实准入：**3391 → 3391，净增 0**；policy 字节未改。口径是禁用准入后实际诊断的 `(path,function,rule,line,AST column)` 差集，不是 JSON 行数。

新节点 call 耗时 58.260s / 基线全部 call 3389.185s = **1.719%**，在约 5% 约束内。基线/最终墙钟 1516.143s / 1611.485s；有并行证据任务和静态门，不能把墙钟差冒称受控性能基准。长回放及大规模对抗不进 pytest。

## 审查发现闭环与遗留

团队交叉复核覆盖 R3、回放语义、C1、冻结/集成；完整过程见 `review_r3.md`、`review_replay_semantics.md`、`review_c1.md`、`review_integration.md`。
发现并关闭发布漂移窗口 1 major；另修复 W/V 同 L1 长度掩盖预算混用的弱门，以及 PowerShell 管道损坏中文理论草稿的问题。
R3 理论当前文件是编码修复后的重写字节，不冒称这份字节文件早于实现；理论合同沿用并核查了 M5c 定理。C1 边界存续证明先落盘后实现。
当前局部审查无未关闭 critical/major；此句话不是六路 G6 通过声明。

遗留/边界：凹环一般 C 证书、跨环平行拆分及原并列集合存续仍未证明，C1 拒签；12396 对不作稳健出口结论。
49 个未证新接触对只给名义对照。4280 个 C1 对仅在初态几何盒内认证，不认证整步名义轨迹出口恒定。
所有者 Claude 的独立验收仍需进行。上述拒签属于本单明确要求的保守边界，未以距离差勉强签发。

## 复跑与交付

所有命令先设 `TEMP=TMP=<本树>/reports/codex/M5d_evidence/tmp`，`PYTHONDONTWRITEBYTECODE=1`，UTF-8；pytest 必须带 `-p no:cacheprovider --basetemp <新目录>`。
关键脚本：`tools/m5d_r3_evidence.py --count 32`、`tools/m5d_replay_teeth_evidence.py`、`tools/m5d_c1_replay.py`、
`tools/m5d_c1_adversarial.py`、`tools/m5d_wording_audit.py`、`tools/m5d_refresh_frozen.py`、`tools/m5d_audit_admissions.py`。
全套采用 `tools/m5d_run_gates.py --name <新目录>` 后调用 `tools/m5d_finalize_evidence.py <同名目录>`；不得复用中断批次。
本报告可用 `python tools/m5d_report.py` 重建；最终清单用 `python tools/m5d_delivery_manifest.py` 重建，包含 SHA256、大小、可点击链接及编码/换行检查。
大日志和逐节点记录在 ignored tmp，待提交路径不含超过 1 MB 的本单文件。

M5d_DONE
