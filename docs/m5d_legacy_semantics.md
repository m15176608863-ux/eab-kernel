# M5d B：19/68 的结构、legacy 表语义与编号订正

## 1. 口径先行

本文只订正可由冻结导出逐行复核的命题，不把观察扩写成几何定理。R3 证书正确性由专门的独立几何 oracle 验证；本审计不重算 R3。
`tools/m5d_wording_audit.py` 的 imports 为 `argparse / collections / fractions / gzip / hashlib / json / pathlib`；不 import `src/eab`、任何回放生产模块或姊妹代码。
它从不可变 endpoint/legacy 分片，独立重建周期编号、逐类三元组和命中；只把冻结的首特征及认证位当作输入观察。近乎平行描述用有理数叉积/点积，不与生产几何共用原语。

## 2. 19 个获证项不代表一般接触

19 个认证**步—块对**全部是两行 `mtype=0` 的边—边近平行构型。对两支承边的 `sin²(angle)` 精确计算后最大约 `0.000194987734`；描述门使用 `sin²<1/300`，这个界只描述子集，绝不是 R3 的新认证容差。
68 个名义候选中，12 个含 VV 行的块对、6 个超过两行的拥挤块对都在未证部分；两类可重叠，不能相加当分母。

构型去重采用 **`(算例, 无序块对, 规范化首特征集合)`，忽略步号、不跨算例合并**。结果为 **17 个特征构型身份**：bb05 的第 3、11、20 步 `(2,3), VE(18,{11,12})` 合并，其余各一项。
这是可复跑的拓扑特征去重，不声称不同步的精确几何相等，也不声称 17 个统计独立样本；跨算例可能仍有相似构型，不能凭 17 扩大适用域。

具名门：`test_certified_nineteen_are_two_row_near_parallel_ve_not_vv_or_crowded`、`test_case_pair_first_feature_dedup_has_seventeen_not_nineteen_identities`。

## 3. legacy 命中分列

以下各列是块对级“至少一个命中”，不是行数；VV 与共边列不与主参考列互斥。

| 子集 / 阶段 | 主参考 | VV 第二参考单列 | 共边槽单列 | 主 + VV | 全槽 | 无该块对记录 |
|---|---:|---:|---:|---:|---:|---:|
| 已认证 19 / raw_df05 | 7 | 0 | 12 | 7 | 19 | 0 |
| 已认证 19 / post_df06 | 19 | 0 | 0 | 19 | 19 | 0 |
| **未认证，纯名义 49** / raw_df05 | 31 | 9 | 8 | 40 | 48 | 0 |
| **未认证，纯名义 49** / post_df06 | 38 | 9 | 1 | 47 | 48 | 0 |

49 对的名义数只为定位差异，不是稳健命中率，不证明模型敏感或漏检结论。它们每阶段有 135 条主参考、12 条 VV 二参、32 条共边槽；19 对每阶段有 38 条主参考、0 条 VV 二参、25 条共边槽。

唯一名义全槽未命中是 **bb51 第 2 步 `(3,9)`，名义首特征 `VE(93,{149,153})`**。两阶段均有该块对的两行记录，并非 missing-pair：

- raw 主：`VE(92,{149,153})`、`VE(149,{93,94})`；VV 第二参考与共边槽都是 `VE(149,{92,93})`。
- post 主：`VE(149,{92,93})`、`VE(149,{93,94})`；VV 第二参考 `VE(149,{92,93})`，共边槽 `VE(92,{149,153})`。

具名门：`test_unproved_49_remain_nominal_including_bb51_step2_pair3_9_all_slot_miss`。

## 4. post_df06 主参考 19/19 的准确含义

在此窄子集，首盖总在 legacy 已保留的角候选中：要么原主三元组命中，要么在相应行的主/共边两组三元组候选中，由 `df06` 换半将共边候选放到主参考。raw 的 12 对主参考未命中正是后一类。
**post_df06 不是无关的报告表，它正是随后 df07 和弹簧装配消费的接触表。** 不应再含混地说“也不等于求解器使用了它”：准确说法是“共边槽本身不作为独立弹簧参考直接装配；其换半后的主参考进入求解表，并且共边槽还影响接触长度”。是否真正激活弹簧仍由开闭状态决定，19/19 不是 19 次实际载荷贡献的断言。

只读核验位置（全文 SHA256 与带行号摘录在证据 JSON）：

| 语义 | df.c | bdda2 |
|---|---|---|
| 邻边近平行转 VE / 共边两半 | 1619–1649 | `detect/classify.hpp` 66–86 |
| VV 的完整第二三元组 | 1660–1681 | `detect/classify.hpp` 88–106 |
| df06 换主/共边三元组 | 1832–1853 | `stepper/transfer.hpp` 118–125，137–144 输出 `out[i].t7=m[i]` |
| post 表接着进入 df07/接触结构 | 1880–1903、1935–1949 | `driver/run.hpp` 414–430 冻结位置；438–460 消费 `rows` 并调 `df07_o5` |
| 共边槽参与接触长度 | 1935–1949 | `stepper/transfer.hpp` 148–174：`m6>0` 时对 m5、m6 累计投影 |
| VE 不另装配共边第二弹簧；VV 可用第二参考 | 3215–3238：`jj<=m[i][0]` | `stepper/step_system.hpp` 167–209：第二参考由 `LOCK_SECOND` 门控，其余用 P；`driver/run.hpp` 459–460 仅 VV 有两半 |

具名门：`test_post_df06_primary_hit_means_promotion_of_retained_angular_candidate`。该门逐行确认换半关系，不以文本哈希冒充语义。

## 5. raw ID 0 与规范化 ID 0 不能混用

原“VV 的 m5/m6 可以是实际顶点 ID 0”理由错误，撤回。raw 实顶点编号从 1 开始；0 是首块首顶点之前的**垫位/末顶点副本**，不是 raw 实顶点。
`df.c` 894–902 与 `bdda2/io/case_data.hpp` 97–105、113–118 直接给出读入从 1 起以及 `i1-1 <- i2` 复制。

冻结入口保留从前垫位开始的环，再删除尾端两重复别名，因此规范化 ID 0 可以是合法的边端。比如 raw 正 ID `4,5` 经周期映射成为规范化 `0,1`；不能因此发明 raw VV 的 m5=0 约定。
旧测试已改为正 raw ID 的真实别名路径；生产条件和行为未变，仅注释订正。
具名门：`test_positive_raw_vv_edge_ids_normalize_to_legal_canonical_zero`。

## 6. 复跑、元门与边界

```powershell
$env:TEMP="$PWD/reports/codex/M5d_evidence/tmp"; $env:TMP=$env:TEMP
python -X utf8 tools/m5d_wording_audit.py --source-review
python -m pytest -q -p no:cacheprovider --basetemp reports/codex/M5d_evidence/tmp/b_unit_r2 tests/test_m5d_wording.py tests/test_m5c_accounting_review.py
```

`--source-review` 仅用于人工源码证据刷新，pytest 不读取姊妹树、不运行其程序。几何描述元门 `test_near_parallel_description_is_invariant_under_rigid_motion_and_units` 用非轴有理转动、|t|=1e6 与 1e-3/1e5 单位变化；全部几何判据用 Fraction，float 只显示无量纲结果。无新生产数值准入项。

证据：[逐对审计](file:///D:/eab-wt/cx-e2/reports/codex/M5d_evidence/b_wording_audit.json)、[姊妹源码只读行号与哈希](file:///D:/eab-wt/cx-e2/reports/codex/M5d_evidence/b_legacy_source_review.json)。
