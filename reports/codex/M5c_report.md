# WO-M5c 中文交付报告

## 0. 结论与范围

**A1–A7 已完成；B 的严格充分条件与全时程扩证完成，稳健单首盖由 2/68 提高到 19/68；C 保持 PARTIAL。**

- 基线 `efb0dfe514a1f60c44e6341b69cce77ff5c9ec17`，初态工作树干净。只写本工作树，未执行 commit / push / reset / checkout / stash / worktree / branch。
- 新鲜字节导出四片 **13781 收集 = 13781 执行，0 skip，全绿**；静态 0 违例。反事实逐站准入 **3391 → 3391，净增 0**，policy JSON 原字节未改。
- 扩大后稳健无接触 38681，稳健单首盖 19，未证 25310，总计 64010。68 个新接触里仍有 49 个未证，不外推。
- 所有认证只针对规定的连续顶点 L∞ 管及 P1/P2/P3 指定族，不是未知真实物理路径、工程验证或求解器切换授权。
- C 未实现边界特征存续核验，16676 个初态贯入对的正半径出口排序仍全部未证；不伪造稳健 PD 子集结论。

关键证据：[交付总清单](file:///D:/eab-wt/cx-e2/reports/codex/M5c_evidence/DELIVERY_INDEX.md)、[完整联合摘要](file:///D:/eab-wt/cx-e2/reports/codex/M5c_evidence/combined_summary.json)、[逐对诊断](file:///D:/eab-wt/cx-e2/reports/codex/M5c_evidence/research_diagnostics.json)、[执行审计](file:///D:/eab-wt/cx-e2/reports/codex/M5c_evidence/execution_audit.json)。

## 1. 理论先行、oracle 与数值合同

先行文档：[A 补牙理论](file:///D:/eab-wt/cx-e2/docs/m5c_teeth_theory.md)、[R3/C1 定理与边界](file:///D:/eab-wt/cx-e2/docs/m5c_research_theory.md)、[数值合同 inventory](file:///D:/eab-wt/cx-e2/docs/m5c_numeric_inventory.md)。

R1/R2 原生产几何公式未改。A 主 oracle 只导入 `fractions.Fraction`，独立枚举刚体平移的线性入射方程、闭边投影与有理复数旋转；不导入生产几何/求根/区间原语。公式预算另用字面向量独立双线性展开。`pytest`、`mutation_support`、Path/JSON 属设施或被测接线，不冒充几何 oracle。

R3 主 oracle 是独立闭式凹环平移；对抗 oracle 使用 Fraction 的线性/二次事件与独立隔离、独立线段相交。随机仅用于构造输入，判定仍精确。主路径不使用 float 阈值；Decimal 只生成诊断显示。元门含非轴有理旋转、大平移至 1e6、极小/极大单位尺度，旋转管按诱导 L∞ 范数保守变换。

## 2. A 逐条完成情况与真实内部变异

| 工单 | 处置与具名门 | 变异结果 |
|---|---|---|
| A1 早期窗口 | `test_r2_complete_early_window_rejects_prior_penetration`：三次往返平移，早期真实首盖与晚期提名标签不同 | skip 与 half-window 均红在首盖语义拒绝断言 |
| A1 全竞争者 | `test_r2_ev_competitor_precedes_nominated_ve`：正确 EV 首时刻 0.3，错误 VE 为 0.5 | 只查 VE、不查 EV 必红 |
| A1 双边内投影 | `test_r2_both_edge_projection_sides_reject_line_extension`，上下两侧各一反例 | 各漏一侧均错误签发并被门杀死 |
| A1 全分段 | `test_r2_final_panel_rejects_departed_edge_endpoint`，真实整窗无接触 | 漏最后一段必红 |
| A2 r2 | `test_replay_endpoint_residual_r2_prevents_false_no_contact`，模型误差其他项为零但端点残差为 1 | 删除 r2 会错误签无接触；语义门红 |
| A3 L1 / 双盒 | `test_r1_linf_tube_uses_dual_l1_normalization`、`test_replay_p2_box_cannot_be_replaced_by_p1_box_only` | L1 改 L∞、只查 P1 两项均红 |
| A4 误差项 / 严格性 | `_event` 两预算各三项、凸性三项；竞争/凸性等号；近阈值接受格 | 九项删减与两项非严格化均由预算/拒绝语义断言杀死 |
| A4 真 oracle | 原恒真断言替换为 oracle 首标签/首时刻核对生产 label/bracket | 内部返回错误 label 与 bracket 均红 |
| A5 口径 | 比较来源四分列、G0 求值/生产交叉核对分列、稳健 reason 清理、主/次/共边槽分列 | 新计数门与真实 bb03/锁长反例门通过 |
| A6 审查域 | 代码固定 13 脚手架规则、4 个既有测试变异文件；活动 review 指纹单独 pin | 扩大规则/生产路径/任意测试路径/路径穿越的追加审查均拒绝；4 个内部 guard 变异均红 |
| A7 闭包 | endpoint 29 / robust 21 个实际运行时传递文件，首尾各采一次 | 每个文件 scratch 字节变异拒绝；独立 `__spec__.origin` 集合 oracle 另杀内部漏依赖变异 |

A1–A4 专项收集=执行=49，0 skip，**22 个真实内部变异全 kill**。仅运行具名语义驱动，源码哈希/冻结摘要绊线未被选入；没有在枚举产出后塞假数据。近阈值端点余量/误差为 `1/199999`。误差项门核对预算表达式，不冒称每次删项都已经构造实际错轨迹。

完整逐项记录：[22 项变异表](file:///D:/eab-wt/cx-e2/reports/codex/M5c_evidence/semantic_teeth.md)、[A6/A7 记录](file:///D:/eab-wt/cx-e2/reports/codex/M5c_evidence/binding_work.md)、[共享/闭包独立复核](file:///D:/eab-wt/cx-e2/reports/codex/M5c_evidence/review_binding.md)。

### 2.1 口径订正后的分母

- **实际 P1/P2 轨迹比较：14079 对，其中 68 对本步新接触，身份/状态差异 0/14079。**
- 构造上由共同初态必然相同：16889 对 = 16676 初态贯入 + 213 初态接触。
- 双盒严格证书直接判定无接触：33042 对。三项互斥相加为 64010，不再宣传“实测 0/64010”。
- 独立 G0 求值 30968 对，其中 **14292 对与两生产入口交叉核对、零失配**；另 16676 由 G0 直接分类，不冒充交叉验证。
- M5b 原 §6.1 已明确 **n=2/68，不可外推**；本次才扩到 19/68。
- bb03 第15步 (8,11)：raw 主参考不是首盖，但**同一 raw 行 m4–m6 共边槽就是首盖**，不能说全部可用槽漏掉首盖。

### 2.2 参考槽修复与真实重算

独立审查抓到本次初版把 `m4>0` 的普通 VE 锁长提示当第二参考的 major。`robust_full_m5c_r1` 整批作废并终止 worker，未发布、未拼接；修复后 `robust_full_m5c_r2` 从头真实运行。

- 正式 VV 二参：`mtype==1 && m4>0`；raw 实顶点编号 ≥1，0 为垫位；正 raw 编号经周期规范化后可以映射到合法边端 ID 0。原“raw 实顶点 ID 0”的理由撤回。
- VE 共边入口槽：`mtype==0 && m6>0`；普通 VE 的零尾锁长提示排除。
- 完整槽再检查：顶点在对块，边为同块相邻、非退化且属当前块对；坏完整槽响亮拒绝。
- 只读核对 `D:/b-DDA/df/df.c`（代码 hash/行号入证据），对全部两阶段 283188 行独立周期 ID oracle 零失配。每阶段主参考141594、VV二参7768、共边槽32075；先前各49218条锁长提示不再伪造二参。

[逐行独立审计](file:///D:/eab-wt/cx-e2/reports/codex/M5c_evidence/a5_independent_legacy_audit.json)；[首轮发现与修后复核](file:///D:/eab-wt/cx-e2/reports/codex/M5c_evidence/review_a5.md)。

## 3. B：诊断、收紧证书与扩大后的答案

### 3.1 为什么原来只有 2/68

68 对中 37 对两环名义严格凸，31 对至少一凹环。原 R2 的失败不只是半径太大：先对绝对顶点分别包络再相减会丢掉共同运动相关性；全局严格凸条件直接排除凹环；有限固定法向与固定粗窗口也会保守。

对原66个未证格，在最窄原候选窗口检查（子条件可重叠，不能相加）：早期分离64、严格凸性31、竞争EV5、起端符号5、终端符号1。全部三个 pad、P1/P2、每个块对的失败条件、扣误差余量和余量/误差比均存于 [68 行诊断表](file:///D:/eab-wt/cx-e2/reports/codex/M5c_evidence/research_diagnostics.json)。`margin_over_error` 是扣费前 margin/error，`surplus` 是扣费后严格余量；误差为0时比值记null，不伪装有限值。名义导数与混合单位简单环门不强造无量纲比。

另做523次独立 G0 管内初态反例查询，3对允许常量管内 s=0 已接触（bb03 step1 (10,11)、bbF038/ bbS038 step1 (1,2)）；19获证对子集无反例。这只反证宽常量管的统一保证，不是实际共享初态 P3 发生差异；65对没搜到反例也不证明稳健。[初态管诊断](file:///D:/eab-wt/cx-e2/reports/codex/M5c_evidence/research_initial_tube_witnesses.json)。

### 3.2 R3 定理与证明状态

1. 先在有理多项式环计算同时间相对向量 `(Np Dq-Nq Dp)/(Dp Dq)`，然后包络；共同平移相关项可精确消去。
2. 每个子窗的固定法向可取该窗中点边法向；所有顶点对投影差的严格下界扣 L1 对偶管预算后为正，证明整窗两凸包分离。中点只生成候选，不用采样代替证明。
3. 在接触括区逐窗证明边不退化、非邻边不交、邻边不倒折，保证任意管内配置为简单环，允许凹环。
4. 端点严格异号、两侧边内投影严格正、所有 VE/EV 竞争事件排除，推出首次接触只能是指定单标签。**不要求扰动可微，不认证唯一根或首时刻不变。**

这比 R2 更紧但仍只是充分条件。近切、VV、并列、零余量、自交、未知初态路径均不强行签发。`δF/m` 若只取根一点导数，没有整个移动走廊下界，就不是证明。

独立对抗：90个名义构造23获证；920条逐顶点常值扰动同时核首标签与括区，138条非刚体首末线性扰动仅核状态/首标签（未另核首时刻括区），均0错；80个简单环候选38获证、760次独立段相交核查，0错；6个结构反例均拒绝。90个名义轨迹的分母均为常量1，不能把这些数冒称非恒定分母P2的完整时刻扰动验证。测试通过是有限核查，连续管结论依据上述定理。[独立复核](file:///D:/eab-wt/cx-e2/reports/codex/M5c_evidence/review_r3.md)。

### 3.3 1810 步的两阶段完整覆盖

第一阶段：新 `robust_full_m5c_r2` 实际从头运行1810步/64010对，5014.223秒，完整21文件运行时闭包首尾一致。
第二阶段：研究 `research_recert_r4` 遍历全部1810步/64010对，重新求解全部68个新接触候选的 P1/P2 与 R2/R3，1471.718秒。**不是第二次全部块对 P2 求根**。
联合发布器按原始冻结 endpoint 每步块身份核验全组合覆盖，新旧64010对的状态/标签/精确时间逐项相同；新鲜68候选与研究 exact/compact 全连接，再逐对替换分类与参考计数。没有从历史只挑19个阳性来充当全集重跑。

| 算例 | 新接触候选 | 原R2 | R2∪R3 | 仍未证 |
|---|---:|---:|---:|---:|
| bb03 | 9 | 1 | 2 | 7 |
| bb05 | 8 | 0 | 3 | 5 |
| bb06 | 3 | 0 | 1 | 2 |
| bb09 | 9 | 0 | 3 | 6 |
| bb10 | 12 | 0 | 2 | 10 |
| bb12 | 10 | 1 | 6 | 4 |
| bb50 | 0 | 0 | 0 | 0 |
| bb51 | 6 | 0 | 1 | 5 |
| bb52 | 2 | 0 | 1 | 1 |
| bbF038 | 1 | 0 | 0 | 1 |
| bbS038 | 1 | 0 | 0 | 1 |
| bbv01 | 0 | 0 | 0 | 0 |
| bbv01_dbv01a | 5 | 0 | 0 | 5 |
| bbv02 | 0 | 0 | 0 | 0 |
| bbv02_dbv02a | 2 | 0 | 0 | 2 |
| 合计 | 68 | 2 | 19 | 49 |

### 3.4 重新回答 legacy 命中与漏检

分母均为**19个已认证步—块对**，不是参考行数：

| 阶段 | 主参考命中 | 主参考+正式VV二参命中 | 再含有效共边入口槽命中 | 完全无该块对记录 |
|---|---:|---:|---:|---:|
| raw_df05 | 7/19 | 7/19 | 19/19 | 0 |
| post_df06 | 19/19 | 19/19 | 19/19 | 0 |

这19对的正式 VV 二参为0；68候选全集有12条 VV 二参，均在未证格，不能据其推断稳健命中。19对子集每阶段38条主参考、25条共边槽：raw 主参考7条首盖/31条其他；post 主参考19条首盖/19条其他。raw 有12个块对未把首盖选作主参考，但其有效共边槽命中；**共边槽本身不另作独立弹簧参考；df06 换半后的主参考属于随后 df07 / 弹簧装配所用的表，共边槽还影响换半与接触长度，实际激活仍受开闭状态控制**。该子集0块对漏检，不能外推49个未证新接触或全集。


**M5d 结构与口径订正**：19 个认证步—块对全是两行边—边近平行构型；68 个候选中 12 个含 VV 的块对与 6 个拥挤（多于两行）块对都落在未证部分，两类可重叠。按“算例、无序块对、规范化首特征集合”去重并忽略步号，得到 **17 个特征构型身份**（bb05 第 3、11、20 步归一）；这不是 17 个统计独立样本，也不声称精确几何相等。首盖总在 legacy 保留角候选中，raw 的 12 对由 df06 主/共边换半升为 post 主参考。源码行号与具名门见 [M5d 订正文档](file:///D:/eab-wt/cx-e2/docs/m5d_legacy_semantics.md)。

**49 个未证项仅作名义对照，不作稳健结论**：raw 主 / VV 二参 / 共边单列命中为 31 / 9 / 8，主+VV 为 40，全槽为 48；post 对应 38 / 9 / 1、47、48。唯一名义全槽未命中是 bb51 第 2 步 (3,9)，名义首特征 VE(93;149,153)，两阶段仍各有该块对两条记录；不是 missing-pair。逐对清单与输入绑定见 [M5d B 审计摘要](file:///D:/eab-wt/cx-e2/reports/codex/M5d_evidence/b_wording_audit.json)。

新增最小例：bb05 第3步 (2,3)，首盖 `VE(vertex=18, edge=(11,12))`；raw 主参考不命中、同一行共边槽命中，post 主参考命中。输入、精确证书与真实重执行结果见 [新最小例](file:///D:/eab-wt/cx-e2/reports/codex/M5c_evidence/research_minimal_examples.json)。原 bb03 例仍见 [五例](file:///D:/eab-wt/cx-e2/reports/codex/M5b_evidence/robust_minimal_examples.json)。

## 4. C：已贯入全局最短出口——PARTIAL

C1 是严格但尚未实现的充分条件：两环管内严格凸，所有跨环边叉积严格离零以固定 Minkowski 边法向序/标签；对应端点差的 L∞ 误差为 `r=ra+rb`，故每条闭边的 Hausdorff 欧氏误差 ≤ `sqrt(2) r`。设原点到全部闭边的精确平方距离为 q_i，唯一最优 q 要求：

`q > 2r²`，且对所有竞争边，`h=q_j-q-8r² > 0`、`h² > 32qr²`。

后两式等价于严格距离差 `sqrt(q_j)-sqrt(q)>2sqrt(2)r`，配合边界标签存续给最近边不变；遍历全部闭边的严格间隙已排除端点邻边并列。平行边拆分、原并列集合、凹环遮盖边、新暴露边不得靠距离差单独认证。外部竞争者离并列组很远，只能证明新最优属于该组，不能证明原并列标签集合不变。

**未实现/未跑：** 跨边法向序、全局边界特征存续、距离扰动与并列等距保持的生产检查。因而16676对全部仍 `INITIAL_EXIT_ORDER_UNCERTIFIED`，稳健出口子集n=0，无法回答稳健出口命中率；不是0失配。

仅对这16676对原有记录计数（不是出口认证）：

| 阶段 | 主参考行 | VV二参行 | 有效共边槽 |
|---|---:|---:|---:|
| raw_df05 | 81209 | 2001 | 19785 |
| post_df06 | 81209 | 2001 | 19785 |

## 5. 冻结重算、四片与逐站审计

端点 `endpoint_full_m5c_r1` 真实重算15220块帧，121.192秒；全部精确极值与旧摘要相同。29文件运行时闭包替代4个直接文件，输入分片另绑定；旧摘要/最小例原字节在 `_before.json`。稳健全量、研究68、最小例均真实重算，不只改hash。未触及旧M5a/M5a2/M4c实际导入闭包，未无谓改其冻结绑定。

最终有效四片最后一行原样：

```text
3446 passed in 895.75s (0:14:55)
3445 passed in 738.35s (0:12:18)
3445 passed in 1295.12s (0:21:35)
3445 passed in 692.89s (0:11:32)
```

静态最后一行原样：

```text
exact construction AST gate: 0 violation(s)
```

所有setup/call/teardown passed；收集=执行=13781，唯一节点、分片无重叠、0skip。用户禁止worktree，以新鲜字节导出执行并前后核验，`fresh_git_checkout=false`，不冒称新Git检出。源码/测试/政策/fixture与最终实际执行副本一致。

基线call累计 3377.441s；新增节点call累计 10.817s，占基线 **0.3203%**。宿主有并行证据工作，不把墙钟比冒称受控性能测试；完整长回放未塞默认pytest。

准入按**实际反事实诊断集 × AST行/列站点**计数：关闭全部逐站/共享豁免前后差集，基线与当前均3314逐站或重叠贡献+77共享边际贡献=3391，净增0。M5b旧文3618+77是context匹配的AST站点口径，包含未实际释放诊断的项，不能直接当本单反事实分母。新增逐条准入清单为空，policy字节不变。[逐站机器证据](file:///D:/eab-wt/cx-e2/reports/codex/M5c_evidence/admission_rule_sites.json)。

独立交叉复核记录包括R1/R2补牙、A5接线、A6/A7绑定、R3证明/对抗、C1边界与联合发布。发现的锁长槽误计及联合参考总数守恒major已修复并保留首轮证据；不以“测试全绿”替代Claude最终独立验收。

## 6. 复跑、回滚与遗留

所有命令先令 TEMP/TMP 指向本树 `reports/codex/M5c_evidence/tmp`，Python UTF-8；pytest 一律无cacheprovider且显式basetemp。关键命令：

```text
python -X utf8 tools/m5c_mutation_evidence.py
python -X utf8 tools/m5c_independent_review.py
python -X utf8 tools/m5c_audit_legacy_slots.py --check-production
python -X utf8 tools/m5b_endpoint_replay.py --run-name <新目录>
python -X utf8 tools/m5b_robust_replay.py --name <新目录> --publish
python -X utf8 tools/m5c_diagnostics.py --name <新目录> --summary <完整摘要路径>
python -X utf8 tools/m5c_publish_combined.py --name <新目录> --output <新摘要路径>
python -X utf8 tools/m5c_run_gates.py --name <新目录>
```

联合发布器默认拒绝覆盖；历史产物先归档，新增完整批次才能发布。中断整批作废，研究r1–r3与稳健r1均未拼接成有效证据。大逐对流、详细节点及长日志留ignored tmp，公共摘要绑定hash；全部交付文件见清单。回滚依据原HEAD与字节备份；未自动执行Git回滚。

遗留：C1生产边界存续与出口排序尚未实现；49/68新接触仍未证，不把它们称为模型敏感；任意物理步内路径与完整P3超越首根不在本次保证内。Claude最终独立验收仍由所有者执行。

M5c_PARTIAL：C 的正误差管出口特征存续、排序实现及稳健子集命中结论未完成；49/68 新接触仍未证且不外推
