# M5d 主报告 B5/B6/B7 片段

本片段的计数已由不可变 endpoint/legacy 输入独立重建。最终冻结已真实重算并发布（7 个产品，64,010 条观察重合并、68 个首接触候选重解）；随后已备份旧 B 产物并重新执行 `tools/m5d_wording_audit.py`（未启用 `--source-review`），逐个核验全部 92 个当前输入绑定。新旧 B 审计字节完全相同，19/49/17 及全部名义命中计数不变；这不是只改哈希。B/accounting 局部门亦真实重跑，最后一行 `22 passed in 1.95s`。**最终四片及逐站审计见主报告后节；不宣称所有者 G6 完成。**

## B5：19/68 子集结构与 49 对名义对照

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

## B6：post_df06 主参考 19/19 的准确含义

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

## B7：raw 编号与规范化编号分开

撤回“VV 的 m5/m6 可以是实际顶点 ID 0”的理由：**raw 实顶点编号 ≥1，0 是首块前垫位，即末顶点副本，不是 raw 实顶点。** 证据为 `df.c` 894–902，`bdda2/io/case_data.hpp` 97–105、113–118。

冻结环从前垫位起保留一个周期并去掉尾部两重复别名，故**规范化 ID 0 可以是合法边端**。例如正 raw ID `4,5` 可映射到规范化 `0,1`。旧测试中不存在的 raw VV `m5=0` 约定已改成正 raw 别名路径；生产解码条件不改，只订正注释与解释。

具名门：`test_positive_raw_vv_edge_ids_normalize_to_legal_canonical_zero`。另有 `test_all_68_reference_slots_match_independent_literal_oracle` 将全部 68 对、两阶段所有槽与独立周期模运算 oracle 对账，零失配；近乎平行描述另有非轴旋转、大平移及单位元门。

## 历史 M5c 订正边界与证据

已同步订正历史 `M5c_report.md` 及其生成器 `tools/m5c_report.py`，避免再次生成错误 raw-ID 理由和含混的“求解器不一定使用该表”措辞；同时补明 19 对的结构、17 类规则、49 对名义观察。`tools/m5b_robust_replay.py` 仅修改说明性注释，触及其冻结闭包的真实重算及发布已由主代理完成，发布记录为 `frozen_refresh.json`，不是仅刷新哈希。

**不追改历史里程碑能力边界**：M5c 的 C 部分仍是当时未实现状态。M5c combined 摘要里的初态出口认证 0，指该历史首盖回放产品没有做 C1；M5d 新 C1 结果另列新证据，不把两种产品、认证子集或分母混在一起。最终四片及逐站审计见主报告后节；所有者 G6 不由本片段代签。

独立 B 审计 imports 仅为 `argparse / collections / fractions / gzip / hashlib / json / pathlib`；不导入生产几何或姊妹模块。冻结首特征与认证标志是输入观察，不冒充独立 R3 几何 oracle。

证据：[逐对 B 审计](file:///D:/eab-wt/cx-e2/reports/codex/M5d_evidence/b_wording_audit.json)、[只读源码行号与哈希](file:///D:/eab-wt/cx-e2/reports/codex/M5d_evidence/b_legacy_source_review.json)、[B 局部门记录](file:///D:/eab-wt/cx-e2/reports/codex/M5d_evidence/b_tests.json)、[发布后 B 实算与绑定核验](file:///D:/eab-wt/cx-e2/reports/codex/M5d_evidence/b_post_refresh_verification.json)、[完整订正文档](file:///D:/eab-wt/cx-e2/docs/m5d_legacy_semantics.md)。旧 B 审计及局部门记录分别保存在同目录的 `b_wording_audit_before_frozen_refresh.json`、`b_tests_before_frozen_refresh.json`、`b_tests_before_frozen_refresh.txt`；这些均为小文件备份。
