# WO-M4a 中文交付报告：b-DDA 离线影子检测与逐条对账

## 1. 当前结论与日期口径

**报告执行日期：2026-10-12。** 工单指定记载的所有者 M0 退出决定日期为 **2026-10-17**；两者不是同一天。本报告按用户要求记录该决定，不将未来日期冒充本次运行时间。

本轮完成 15 个输入配对各 3 步、共 45 帧的冻结捕获、L5 静态域窗口适配、逐条具名差异门和三处真实路径变异。**未知类别为 0，全套 10923 passed；工单状态 DONE。两路检测集合并非完全相等，也不声称物理轨迹等价或 M4 通过独立 G6。**

- 2538 条 legacy 原始记录，2529 个去重主特征键，2633 个 eab 局部盖。
- VE 同构 `MATCH=1939`；VV 身份相同但法向合同不同 `58`；其余逐条归入五个有可执行判据的类别。
- 修复本树读取器的真实缺陷：VV 不能固定用 `(p1,p2)`。180 条已有原始 VV 中，旧映射反事实错 124 条；不是 legacy “远距离发射接触”。
- 15 例全部有真实逐步 d0/h1 等参数，无 bb52 参数 fallback。3 步覆盖初始化与两次跨步转移，不覆盖原有 30–400 步全时程。
- 家族是 **14 份不同几何时序**：F038/S038 前 3 步几何相同；不能把它们当两份不同几何覆盖。
- legacy 可直接核对的检测度量仅 **782 条首步 VE**（含重复行）；其余 **1756 条**只核重构几何，其中包含 156 条 VV。没有拿 df22 求解后 gap 充当检测前 gap。

主要交付：

1. [接缝地图及仅建议的开关方案](file:///D:/eab-wt/cx-m4/docs/m4_bdda_seam_map.md)
2. [差异台账 G5 第一批](file:///D:/eab-wt/cx-m4/docs/m4_difference_ledger.md)
3. [45 帧逐条对账 JSON](file:///D:/eab-wt/cx-m4/reports/codex/M4a_evidence/shadow_results.json) / [逐帧汇总 CSV](file:///D:/eab-wt/cx-m4/reports/codex/M4a_evidence/per_step_summary.csv)
4. [15 例捕获与逐格双跑清单](file:///D:/eab-wt/cx-m4/reports/codex/M4a_evidence/family_manifest.json)
5. [三处变异验证 JSON](file:///D:/eab-wt/cx-m4/reports/codex/M4a_evidence/verification.json)
6. [L5 适配器](file:///D:/eab-wt/cx-m4/src/eab/adapters/bdda2d.py)
7. [逐条分类与计数门](file:///D:/eab-wt/cx-m4/tests/test_m4_bdda_shadow.py) / [冻结期望](file:///D:/eab-wt/cx-m4/tests/m4_shadow_expected.json)
8. [全套运行日志](file:///D:/eab-wt/cx-m4/reports/codex/M4a_evidence/full_pytest.txt) / [全部交付索引](file:///D:/eab-wt/cx-m4/reports/codex/M4a_evidence/DELIVERY_INDEX.md)

## 2. 范围、回滚与 M0 决定

本轮只改 `D:/eab-wt/cx-m4`。开始时分支为 `m4-seam`、HEAD 为 `0e9ef93`、工作副本状态为空；[原文件回滚副本](file:///D:/eab-wt/cx-m4/reports/codex/M4a_evidence/rollback/) 已留存。没有 commit/push/reset/checkout/stash/worktree 操作，没有修改姊妹仓库，也没有接触 `cx-e2/g6*` 复审工作树。

仅从 b-DDA 只读复制 exe 和算例输入到[本树沙箱](file:///D:/eab-wt/cx-m4/reports/codex/M4a_evidence/sandbox/)运行；回归只消费冻结夹具，不 import 姊妹源码，不依赖姊妹 exe。

按工单指定，M0 以“**连续四轮独立复审无 critical**”口径退出并转入 M4。第六至十轮计数（critical/major/minor）依次为 **1/7/4、0/9/2、0/6/0、0/4/2、0/4/1**；剩余 major 仍在另一复审线上处理。这是所有者对 M0 的指定退出口径，**不是宣称 major 清零，也不是 M4 已过 G6**。该记录与进展同步到[计划](file:///D:/eab-wt/cx-m4/docs/plan_20260921.md)和[README](file:///D:/eab-wt/cx-m4/README.md)。

## 3. 接缝地图摘要

以下为只读源码确认；逐项路径与行号见[完整地图](file:///D:/eab-wt/cx-m4/docs/m4_bdda_seam_map.md)。

1. **不要混淆 Python 与 bdda2。** Python 参考实现位于 `src/bdda`；`bdda2` 本身是 C++20；`studio/engine2.py` 是 Python 启动桥，`bdda2/studio` 是 Qt 原生桥。
2. **开关先例**：C++ CLI 在 `bdda2/driver/main.cpp:26-30` 读 `BDDA_SOLVER`，注入 `Options::solver`；`driver/run.hpp` 分派 Faithful/Fast/Auto。Python 工作台用环境传参；Qt 正演在进程内设置 Options，因此新 detector 开关不能只改 CLI 环境读取。
3. **检测链**：步初几何 → `df04` 距离候选 → `df05` 角度分类与双参考构造 → `df06` 历史转移/共边换半 → `df07` 初态与 contacts dump → `df18` 弹簧装配 → 求解与 `df22` 开闭迭代。
4. **没有找到检测层按本步位移方向的首入。** legacy 用静态距离、h1 角域、全局 y 方向的 sin 平局及首步最短 gap 规则；求解后开闭/锁点更新不等同沿给定刚体相对方向首次进入 E(A,B)。
5. **15 例正本清单**：`tools/bdda/verify_cpp.py:33-37` 的 FAMILY，以及 Qt `t0primeFamily`；前 13 配对在 df，F038/S038 在 df/bench。文件头旧“九例/十三例”文字不覆盖实际 15 项列表。
6. **现有 T1 比本单范围更宽**：Fast/Faithful 原门比较锁态、参考拓扑、滑动符号、位移混合误差及 hh；本轮没有 eab 求解路径，只能称“T1 型检测同构门”。原 T1 实码未单独比较 mtype，未实现其文件头声称的 w6 选中索引核对，本单不复制这些遗漏。

## 4. 捕获协议、15 例清单及溯源

捕获时间：`2026-10-12T18:05:46.120129`（本地时间）。内核 SHA-256：

`26abf3ee24dc28ead32b97f6500490cf6087ee20ffc3712412dddd8f6d5a5606`

每例均将 exe + 原 bb/db 复制到两个独立沙箱分别运行；`ff.c` 两行分别命名 bb/db，环境为 `BDDA_KERNEL_MODE=1`、`BDDA_DF17_DEBUG=1`、`BDDA_DUMP_STEPS=3`。输入配对不同的 v01/v01a、v02/v02a 使用独立夹具目录，没有同 bb 覆盖另一 db。

每例入库 6 类原始 CSV：contacts、verts、detparams、df18、df22、cand，加 2 个原始输入；合计 **120 文件、1,436,984 B**。**没有裁列、改值或去重**。其余 debug、exe、运行 wall_clock 留沙箱，不占回归夹具体积。[捕获核验](file:///D:/eab-wt/cx-m4/reports/codex/M4a_evidence/capture_verify.json)确认 15 例/45 帧；每文件内核哈希、输入哈希、不可复现列记录在[PROVENANCE](file:///D:/eab-wt/cx-m4/fixtures/PROVENANCE.json)。

| 算例 | bb / db 配对 | 来源 | 步数 | 夹具目录 |
|---|---|---|---:|---|
| 52 | `bb52 / db52` | golden | 3 | [bb52_N3](file:///D:/eab-wt/cx-m4/fixtures/bdda_df/bb52_N3/) |
| 12 | `bb12 / db12` | golden | 3 | [bb12_N3](file:///D:/eab-wt/cx-m4/fixtures/bdda_df/bb12_N3/) |
| 50 | `bb50 / db50` | golden | 3 | [bb50_N3](file:///D:/eab-wt/cx-m4/fixtures/bdda_df/bb50_N3/) |
| 51 | `bb51 / db51` | golden | 3 | [bb51_N3](file:///D:/eab-wt/cx-m4/fixtures/bdda_df/bb51_N3/) |
| 03 | `bb03 / db03` | golden | 3 | [bb03_N3](file:///D:/eab-wt/cx-m4/fixtures/bdda_df/bb03_N3/) |
| 05 | `bb05 / db05` | golden | 3 | [bb05_N3](file:///D:/eab-wt/cx-m4/fixtures/bdda_df/bb05_N3/) |
| 06 | `bb06 / db06` | golden | 3 | [bb06_N3](file:///D:/eab-wt/cx-m4/fixtures/bdda_df/bb06_N3/) |
| 09 | `bb09 / db09` | golden | 3 | [bb09_N3](file:///D:/eab-wt/cx-m4/fixtures/bdda_df/bb09_N3/) |
| 10 | `bb10 / db10` | golden | 3 | [bb10_N3](file:///D:/eab-wt/cx-m4/fixtures/bdda_df/bb10_N3/) |
| v01 | `bbv01 / dbv01` | golden | 3 | [bbv01_N3](file:///D:/eab-wt/cx-m4/fixtures/bdda_df/bbv01_N3/) |
| v01/v01a | `bbv01 / dbv01a` | golden | 3 | [bbv01_dbv01a_N3](file:///D:/eab-wt/cx-m4/fixtures/bdda_df/bbv01_dbv01a_N3/) |
| v02 | `bbv02 / dbv02` | golden | 3 | [bbv02_N3](file:///D:/eab-wt/cx-m4/fixtures/bdda_df/bbv02_N3/) |
| v02/v02a | `bbv02 / dbv02a` | golden | 3 | [bbv02_dbv02a_N3](file:///D:/eab-wt/cx-m4/fixtures/bdda_df/bbv02_dbv02a_N3/) |
| F038 | `bbF038 / dbF038` | bench | 3 | [bbF038_N3](file:///D:/eab-wt/cx-m4/fixtures/bdda_df/bbF038_N3/) |
| S038 | `bbS038 / dbS038` | bench | 3 | [bbS038_N3](file:///D:/eab-wt/cx-m4/fixtures/bdda_df/bbS038_N3/) |

双跑不是原文件逐字节全部相同：contacts 首步 o3/o4 有 **975 格**不同，df18 首步 o3/o4 有 **967 格**不同，df22 首步 o4 有 **570 格**不同。df22 差异逐格符合 `mtype==1 or m0_new==0` 跳过重算条件；首步未初始化状态残值不进入检测几何对账。其余所有保留 CSV 单元格一致，逐格 first/repeat 原值仍在 manifest，未按“小数足够小”清洗。

legacy `w0` 仍依赖 `GetSystemMetrics`；本次没有宣称固定屏幕跨机重现。固定的是已捕获几何、原始输入与各步实际 detparams。新增观察见[姊妹观察台账](file:///D:/eab-wt/cx-m4/docs/sibling_observations.md)，没有代修 legacy。

## 5. L5 适配与可独立复核的比较合同

[适配器](file:///D:/eab-wt/cx-m4/src/eab/adapters/bdda2d.py)从各步 vertices 重建 CCW 块多边形并规范化回绕别名，消费二维精确盖内核，输出 ContactRecord；`source/observable` 明确为静态检测口径。相邻 verts 是上一拍逐顶点运动，包含转动/应变；zsto2 首次解也可能被后续重试改变，所以没有伪造本步单一平移方向来调用首入。

**域窗口只在 L5 显式声明**：搜索长度 d0、角窗 sin(h1) 来自各例各步；有限边端外长度窗 `seg_tol=1e-9`、度量贴合精度 `fit_tol=1e-6` 延续已验证 bb52 口径。fit_tol 只比较显示度量，不参与枚举；h5/f0/f1/w0 保留在 raw_parameters，不假称已复刻全部 df05/df06 语义，也不把这些物理窗口变成内核容差。

[比较器](file:///D:/eab-wt/cx-m4/tools/m4_bdda_shadow.py)独立用 Fraction 邻边向量、内积/行列式、平方距离与公共开放锥可行性判定，不调用生产 cover/cone/normal/project 原语；它证明给定 binary64 数据上的局部几何性质，不判定 legacy 物理选边是否合理。

对于 VE，逐条比较规范化顶点-边身份、类型、法向方向、单位长与 gap；同向/角残差限 1e-12，gap 差不超过 fit_tol。**1939 条 MATCH 并不全有 legacy 直接度量**：实际 df18 导出的 `cs1/s1/s2` 只覆盖首步 VE 共 782 条；1756 条其他记录仅有重构几何。VV 保留两参考语义，不把 eab 径向或重合集值法向冒充 legacy 两参考弹簧法向。

门同时检查非空、45 帧完整覆盖、重复/缺失步骤、闭集类别、重复输出、逐帧计数和逐条类别摘要哈希；未分类差异或“legacy 几何有效而 eab 漏掉”立即红。参数化额外包含边界、非对称、旋转、大平移及单位缩放，见[适配器元门](file:///D:/eab-wt/cx-m4/tests/test_m4_bdda_adapter.py)。

## 6. 45 帧完整对账表

列缩写：`M`=VE MATCH；`V`=VV 身份相同但双参考法向合同；`E`=严格角域有效而 legacy 未选的局部盖；`A`=只在显式角窗放宽后有效的额外盖；`S`=legacy 主参考投影在有限边窗外；`D`=legacy VV 点间方向不属开放公共锥活跃方向；`R`=legacy 重复主参考额外行；`U`=未分类。

原始条数保留重复；legacy_unique 只用于集合计数，重复行另记 R，不静默删除。以下表由最终 shadow_results.json 逐帧生成。

| 算例 | 步 | legacy 原始 | legacy_unique | eab | M | V | E | A | S | D | R | U |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 52 | 1 | 54 | 54 | 85 | 53 | 0 | 26 | 6 | 0 | 1 | 0 | 0 |
| 52 | 2 | 54 | 54 | 48 | 42 | 0 | 1 | 5 | 11 | 1 | 0 | 0 |
| 52 | 3 | 54 | 54 | 48 | 43 | 0 | 1 | 4 | 10 | 1 | 0 | 0 |
| 12 | 1 | 54 | 54 | 74 | 54 | 0 | 17 | 3 | 0 | 0 | 0 | 0 |
| 12 | 2 | 54 | 54 | 48 | 47 | 0 | 0 | 1 | 7 | 0 | 0 | 0 |
| 12 | 3 | 54 | 54 | 48 | 46 | 0 | 1 | 1 | 8 | 0 | 0 | 0 |
| 50 | 1 | 2 | 2 | 4 | 2 | 0 | 2 | 0 | 0 | 0 | 0 | 0 |
| 50 | 2 | 2 | 2 | 2 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 50 | 3 | 2 | 2 | 2 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 51 | 1 | 54 | 54 | 85 | 52 | 0 | 27 | 6 | 0 | 2 | 0 | 0 |
| 51 | 2 | 54 | 54 | 48 | 38 | 0 | 6 | 4 | 14 | 2 | 0 | 0 |
| 51 | 3 | 54 | 54 | 48 | 38 | 0 | 6 | 4 | 14 | 2 | 0 | 0 |
| 03 | 1 | 40 | 40 | 63 | 40 | 0 | 21 | 2 | 0 | 0 | 0 | 0 |
| 03 | 2 | 40 | 40 | 38 | 38 | 0 | 0 | 0 | 2 | 0 | 0 | 0 |
| 03 | 3 | 40 | 40 | 38 | 38 | 0 | 0 | 0 | 2 | 0 | 0 | 0 |
| 05 | 1 | 10 | 10 | 14 | 10 | 0 | 3 | 1 | 0 | 0 | 0 | 0 |
| 05 | 2 | 10 | 10 | 10 | 10 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 05 | 3 | 10 | 10 | 10 | 10 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 06 | 1 | 10 | 10 | 14 | 10 | 0 | 3 | 1 | 0 | 0 | 0 | 0 |
| 06 | 2 | 10 | 10 | 10 | 10 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 06 | 3 | 10 | 10 | 10 | 10 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 09 | 1 | 58 | 58 | 142 | 44 | 14 | 84 | 0 | 0 | 0 | 0 | 0 |
| 09 | 2 | 58 | 58 | 68 | 44 | 0 | 15 | 9 | 0 | 14 | 0 | 0 |
| 09 | 3 | 58 | 58 | 68 | 44 | 0 | 15 | 9 | 0 | 14 | 0 | 0 |
| 10 | 1 | 74 | 74 | 156 | 60 | 14 | 82 | 0 | 0 | 0 | 0 | 0 |
| 10 | 2 | 74 | 74 | 78 | 53 | 5 | 13 | 7 | 7 | 9 | 0 | 0 |
| 10 | 3 | 74 | 74 | 78 | 53 | 5 | 13 | 7 | 7 | 9 | 0 | 0 |
| v01 | 1 | 156 | 153 | 195 | 144 | 3 | 33 | 15 | 3 | 3 | 3 | 0 |
| v01 | 2 | 156 | 156 | 129 | 105 | 1 | 9 | 14 | 45 | 5 | 0 | 0 |
| v01 | 3 | 156 | 156 | 122 | 102 | 1 | 6 | 13 | 48 | 5 | 0 | 0 |
| v01/v01a | 1 | 154 | 152 | 195 | 144 | 3 | 33 | 15 | 3 | 2 | 2 | 0 |
| v01/v01a | 2 | 154 | 154 | 100 | 91 | 1 | 2 | 6 | 58 | 4 | 0 | 0 |
| v01/v01a | 3 | 154 | 154 | 100 | 90 | 1 | 2 | 7 | 59 | 4 | 0 | 0 |
| v02 | 1 | 88 | 86 | 107 | 78 | 3 | 19 | 7 | 3 | 2 | 2 | 0 |
| v02 | 2 | 88 | 88 | 60 | 51 | 1 | 4 | 4 | 32 | 4 | 0 | 0 |
| v02 | 3 | 88 | 88 | 57 | 51 | 1 | 2 | 3 | 32 | 4 | 0 | 0 |
| v02/v02a | 1 | 88 | 86 | 107 | 78 | 3 | 19 | 7 | 3 | 2 | 2 | 0 |
| v02/v02a | 2 | 88 | 88 | 56 | 50 | 1 | 2 | 3 | 33 | 4 | 0 | 0 |
| v02/v02a | 3 | 88 | 88 | 56 | 50 | 1 | 2 | 3 | 33 | 4 | 0 | 0 |
| F038 | 1 | 2 | 2 | 2 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| F038 | 2 | 2 | 2 | 2 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| F038 | 3 | 2 | 2 | 2 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| S038 | 1 | 2 | 2 | 2 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| S038 | 2 | 2 | 2 | 2 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| S038 | 3 | 2 | 2 | 2 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **TOTAL** | **45** | **2538** | **2529** | **2633** | **1939** | **58** | **469** | **167** | **434** | **98** | **9** | **0** |

总计守恒：`2538 = 2529 + 9`；`2633 = 1939 + 58 + 469 + 167`；`2529 = 1939 + 58 + 434 + 98`。类别总计 3174 是两集合并集加重复行的分类条数，不等于 legacy 原始条数，也不是“错误条数”。

## 7. 差异台账摘要与判定边界

| 类别 | 计数 | 可复跑判据 | 裁决边界 |
|---|---:|---|---|
| MATCH | 1939 | 两路 VE 规范身份相同；独立度量核验通过 | 检测几何层一致，不推演力/锁态/位移 |
| VV_IDENTITY_MATCH_TWO_REFERENCE_NORMAL | 58 | 同一对真实 VV 角点；两路法向表示合同分开记录 | 只确认身份，不宣称径向等于双弹簧法向 |
| EXACT_LOCAL_COVER_NOT_SELECTED | 469 | eab-only，在零角窗下仍满足独立局部锥、距离及边端窗口 | 局部盖有效；legacy 未选是否物理错误无法判定 |
| ANGULAR_WINDOW_COVER_NOT_SELECTED | 167 | eab-only，sin(h1) 下有效，零角窗下无效 | 显式域放宽，不是严格盖，不回流内核容差 |
| LEGACY_OUTSIDE_FINITE_EDGE_WINDOW | 434 | legacy-only，距离窗通过，投影超有限边端窗 | 几何窗外确定；历史转移参考的物理意义无法判定 |
| LEGACY_VV_DIRECTION_OUTSIDE_OPEN_CONE | 98 | 真实 VV 距离在 d0 内、公共开放锥存在，但点间方向不满足严格或 h1 活跃规则 | 活跃性差异确定；不能用径向合同宣判 legacy 双参考错 |
| LEGACY_DUPLICATE_PRIMARY_REFERENCE | 9 | 主 p1/p2/p3 相同、第二参考不同；9 组二重的第二条独立记账 | 不唯一是事实；禁止静默去重，不改 legacy |
| 未分类 | 0 | 所有未知类别、有效盖漏检、空/缺帧直接红 | 这是闭集分类通过，不是完全等价或零物理缺陷 |

完整定义、优先序、方程与实例见[差异台账](file:///D:/eab-wt/cx-m4/docs/m4_difference_ledger.md)。当前三个已注册的其他拒绝原因计数均为 0（距离窗外、局部角窗外、VV 无公共开放锥）；不是豁免池，任何未来新增类别/计数仍由冻结门报红。

## 8. 本树发现与修复

### 8.1 VV 身份映射缺陷

bb52 第 1 步 contact 47 的两参考为 `(171,126,125)` 和 `(171,125,124)`。真实两角点是交集 `{171,125}`，旧 reader 却给 `{171,126}`。修复前现场红灯明确发生在 `VV_CORNER_IDENTITY`，不是无关断言。

[读取器修复](file:///D:/eab-wt/cx-m4/src/eab/readers/bdda_df.py)在 alias 后求两组三点交集，要求恰两点、包含 p1、有几何时跨正确两块；畸形引用 ValueError，不猜 p2。全旧/新夹具 180 条 VV 中，旧固定 p2 映射反事实错 124 条；实际有块号可解析 179 条，sensor 第 2 步 1 条继续 UNKNOWN。修复后本轮所有虚假的“距离窗外”类别消失。

[专项门](file:///D:/eab-wt/cx-m4/tests/test_m4_bdda_vv_reader.py)覆盖四种构造分支 × 两半交换 × alias、五种畸形引用、全夹具普查及在读取器内部重引入旧映射。[修前日志](file:///D:/eab-wt/cx-m4/reports/codex/M4a_evidence/vv_reader_before_fix.txt)与[修后日志](file:///D:/eab-wt/cx-m4/reports/codex/M4a_evidence/vv_reader_after_fix.txt)保留；单文件结果 `24 passed in 0.31s`。没有修改几何内核判定。

### 8.2 比较器在工单内交叉检查中暴露的问题

缺几何步曾静默少审、未知类别名字曾缺少闭集校验、重复主参考及已导出的 legacy 度量曾漏校；均已增加真实路径反例与目标断言，并复测修复。记录见[捕获侧复核](file:///D:/eab-wt/cx-m4/reports/codex/M4a_evidence/review_capture_comparator.md)和[适配器侧复核](file:///D:/eab-wt/cx-m4/reports/codex/M4a_evidence/review_adapter_comparator.md)。这是工单内交叉检查，**不是独立六路 G6**。

## 9. 三处必需变异：红在哪、为什么红

三处均注入被测执行路径内部，不在枚举结果后追加假数据；每次先跑基线、注入并确认目标断言红、撤销后再确认基线通过。机器结果见[verification.json](file:///D:/eab-wt/cx-m4/reports/codex/M4a_evidence/verification.json)。

| 变异 | 注入路径 | 目标红灯 | 恢复 |
|---|---|---|---|
| 丢掉显式角域窗口 | `eab.kernel2d.covers.enumerate_covers` 的实际调用置 cone_tol=0 | 三步分别出现 11/19/20 个 `UNCLASSIFIED_EAB_MISSING_VALID_COVER`，未知差异门红 | PASS |
| 严格额外盖误归角窗额外盖 | `m4_bdda_shadow.classify_extra` | bb52/步1 从 E=26,A=6 错成 E=0,A=32，`pinned shadow tally` 红 | PASS |
| legacy 读入错位一列 | `eab.readers.bdda_df._read_csv` 将 p1 误读为 p2 | `legacy p1 column misread` 红 | PASS |

原样红日志：[域窗口](file:///D:/eab-wt/cx-m4/reports/codex/M4a_evidence/mutation_drop_domain_window_red.txt)、[误分类](file:///D:/eab-wt/cx-m4/reports/codex/M4a_evidence/mutation_misclassify_difference_red.txt)、[错列](file:///D:/eab-wt/cx-m4/reports/codex/M4a_evidence/mutation_legacy_column_shift_red.txt)。本轮还保留 VV 旧缺陷注入门及缺步/错误度量/未知类别等负例，不以“三处够数”替代针对性断言。

## 10. 给所有者的下一步建议（未执行）

推荐下一单先批准 **legacy 默认 + shadow 只读旁路**，不要立即批准真实替换。完整文件级方案见[接缝地图第 6 节](file:///D:/eab-wt/cx-m4/docs/m4_bdda_seam_map.md)。

- `bdda2/driver/run.hpp` 增 `DetectMode`/只读快照 hook；保留原 legacy 调用、顺序和缓冲区，不触碰接触装配或求解语义。
- `bdda2/driver/main.cpp` 仅解析开关、显式注入 Options；建议新增独立 snapshot 序列化文件，输出步初几何、域窗、raw-df05 与 post-df06 两时间面。
- Python `studio/engine2.py` 和原生 Qt `engine_bridge.hpp/.cpp` 分别传递模式；Qt 直接设置 Options。验收入口清除宿主的 detector 环境污染。
- `unset/legacy` 不启 eab、不写影子文件；`shadow` 两路都运行、legacy 原表仍唯一进入求解；`eab` 在真正批准切换前明确拒绝，不悄悄回退或混称 shadow。
- 首批可以运行结束后由独立 Python 进程回放所有快照，避免每步启动子进程。旁路写规范化记录、逐条分类、计数、哈希与异常；shadow 失败必须审计红，但不更改 legacy 物理结果。
- 必须证明 unset/legacy/shadow 原有**可复现产物逐字节一致**；之后再对真实替换增加 df06 继承、双参考选择、锁态、滑动符号与位移门。静态 M4a 不足以授权切换。

## 11. 验证结果与可复跑命令

### 11.1 已完成的验证

| 检查 | 原样结果 / 状态 | 证据 |
|---|---|---|
| 捕获核验 | `{"cases": 15, "steps": 45, "fixture_bytes": 1436984, "status": "verified"}` | [capture_verify](file:///D:/eab-wt/cx-m4/reports/codex/M4a_evidence/capture_verify.json) |
| 溯源专项 | `188 passed in 0.22s` | [日志](file:///D:/eab-wt/cx-m4/reports/codex/M4a_evidence/fixture_provenance_pytest.txt) |
| 聚焦回归 | `236 passed in 9.42s` | [日志](file:///D:/eab-wt/cx-m4/reports/codex/M4a_evidence/focused_pytest.txt) |
| shadow 门单独运行 | `29 passed in 6.63s` | [日志](file:///D:/eab-wt/cx-m4/reports/codex/M4a_evidence/shadow_pytest.txt) |
| 精确构造 AST 门 | `exact construction AST gate: 0 violation(s)` | [日志](file:///D:/eab-wt/cx-m4/reports/codex/M4a_evidence/exact_construction.txt) |
| canon 指针修复工具 | `0 rewritten; 0 kept`；`applied` | [日志](file:///D:/eab-wt/cx-m4/reports/codex/M4a_evidence/canon_ptrs.txt) |
| 三处内部变异 | 3 KILLED，3 restored_baseline PASS，未分类 0 | [JSON](file:///D:/eab-wt/cx-m4/reports/codex/M4a_evidence/verification.json) |

### 11.2 全套最终结果

**状态：全套通过，exit code 0。** 最后一行原样：

```text
10923 passed in 1191.84s (0:19:51)
```

- pytest 报告耗时：1191.84 s；PowerShell 外层 Stopwatch 总 wall time：1200.8655036 s。
- 证据：[原始 UTF-16 日志](file:///D:/eab-wt/cx-m4/reports/codex/M4a_evidence/full_pytest.txt)、[命令/耗时/退出码](file:///D:/eab-wt/cx-m4/reports/codex/M4a_evidence/full_pytest_run.json)。
- 收尾再读构造门仍为 `exact construction AST gate: 0 violation(s)`；canon 工具 `0 rewritten; 0 kept`。
- [最终捕获审计](file:///D:/eab-wt/cx-m4/reports/codex/M4a_evidence/final_capture_audit.json)：原 61 条溯源对象未改，新 120 条及全部 181 个夹具哈希/字节数通过；禁用姊妹/沙箱读取、子进程与网络后，`--verify-only` 仍通过。
- [几何别名审计](file:///D:/eab-wt/cx-m4/reports/codex/M4a_evidence/geometry_alias_audit.json)：696 个别名坐标完全相等，非零距离合并 0。既有 reader 的去重点窗口未在本批改变几何；不外推任意工程坐标读取精度。
- `git -c core.whitespace=cr-at-eol diff --check` 通过；CRLF 是溯源写法，未擅自将原件转成 LF。分支/HEAD 仍为 `m4-seam` / `0e9ef93`，未提交。

### 11.3 从本树复跑（不运行姊妹 exe）

```powershell
Set-Location -LiteralPath 'D:/eab-wt/cx-m4'
$env:PYTHONDONTWRITEBYTECODE='1'
python -X utf8 tools/m4_capture_family.py --verify-only
python -X utf8 tools/m4_verify_evidence.py
python -X utf8 -m pytest -q -p no:cacheprovider tests/test_m4_bdda_adapter.py tests/test_m4_bdda_shadow.py tests/test_m4_bdda_vv_reader.py --basetemp reports/codex/M4a_evidence/tmp/recheck_m4
python -X utf8 tools/check_exact_construction.py
python -X utf8 tools/fix_canon_ptrs.py --apply
python -X utf8 -m pytest -q -p no:cacheprovider --basetemp reports/codex/M4a_evidence/tmp/recheck_full
```

`m4_verify_evidence.py` 会重算/覆盖本轮 evidence JSON、CSV 与三份变异日志，但不改 fixtures、冻结期望或执行 exe。`--verify-only` 只校验捕获；不要为了回归误跑重新捕获。重新捕获须另做明确证据更新，原始输入/内核/窗口漂移单独审查。

## 12. 遗留与验收矩阵

| 工单要求 | 当前交付 | 状态 |
|---|---|---|
| 只读接缝地图、15 例准确清单 | 路径行号、时序、开关位置、现有门范围已落盘 | 完成 |
| 15 例影子数据、哈希及不可复现列 | 每例 3 步 × 两套沙箱，120 文件，完整原始列 | 完成 |
| L5 域窗口适配、ContactRecord | 静态窗口有效盖；窗口来源与首入限制显式 | 完成 |
| 逐帧逐条同构与闭集差异门 | 45 帧，7 个非零类别，未知 0，计数与逐条摘要冻结 | 完成 |
| 差异台账、缺陷修复、legacy 只记录 | VV 读取修复；重复主参考/状态残值登记 | 完成 |
| M0 决定与 M4 文档同步 | 指定日期/口径与剩余 major 并行线边界 | 已记录 |
| BDDA_DETECT | 只给最小建议，未改姊妹 | 符合本单边界 |
| 三处必需内部变异 | 目标断言红，撤销后绿 | 完成 |
| 静态构造、canon 指针 | 0 违例；工具已执行 | 完成 |
| 全套 pytest 最后一行与耗时 | 10923 passed；1191.84 s；外层 1200.8655036 s；exit 0 | 完成 |
| 新鲜工作树与独立 G6 | 本单禁止 worktree；没有六路独立退出审查 | **未执行，不宣称通过** |

残余风险明确保留：后续步 legacy 原生检测法向/gap 缺导出；VV 双参考不等于径向法向；局部盖不是凹块全局入口边界；3 步不是全时程；屏幕依赖未消除；M4a 没有力学装配/锁态/滑动方向/位移等价，也没有授权任何真实开关切换。以上为本单声明的边界与下一单建议，不冒充完整 M4 或独立 G6 退出。

M4a_DONE
