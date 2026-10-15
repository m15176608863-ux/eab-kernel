# M5a 影子回放结果（中文证据摘要）

## 范围与认证边界

一个完整新批次覆盖 15 例、1810 个区间、64010 个步—无序块对。未分类为红，未分类数为 0。
仅对本单选定的两条有理 SE(2) 插值轨迹计算；不声称恢复 b-DDA 步内真实轨迹。δ=0 仅认证拟合端点兼容该刚体模型；δ>0 一律未认证。
M4c 的弦模型结果、相同初态特征及冻结 PD_closed 作为逐文件/逐帧哈希绑定的历史数据复用，不冒充本批次重算。旧 M4c 另有完整 450 帧新鲜重算，详见 m4c_frozen_revalidation.json。

## 问题 1：68 对中的 20 对

M4c 弦模型新接触 68 对，其中平移替身状态或首盖改变 20 对。这 20 对中，刚体模型与弦模型的状态及完整首盖集合一致 7 对，不同 13 对。
完整 68 对群组中：完整首盖集合一致 51 对，仍接触但首盖集合改变 2 对，降为窗口无接触 15 对；精确时刻相等 0 对。
刚体模型全时程共给出 973 个新接触步—块对。不能把这个数解释为精度提高：端点应变/舍入被替换，全部认证标签必须另看 δ。逐对记录见 three_answers.json。

在同一 17603 个初态分离候选对分母下，SE(2) 与弦模型的状态/首盖差异为 937，平移替身与弦模型差异为 790。不能从“加入转动”推出一定更接近弦模型；刚体拟合同时移除了应变，且所有真实拟合 δ>0。两者都不因此成为物理错误判定。

20 对逐对转移（弦模型均为 contact，全部 δ>0 未认证）：

| 例 | 步 | 块对 | 平移替身 | SE(2) | SE(2)/弦完整首盖集合 |
|---|---:|---|---|---|---|
| bb52 | 1 | 2,6 | no_contact | no_contact | 异 |
| bb52 | 1 | 2,7 | no_contact | no_contact | 异 |
| bb12 | 55 | 9,10 | no_contact | no_contact | 异 |
| bb51 | 5 | 6,11 | no_contact | contact | 同 |
| bb51 | 7 | 2,6 | no_contact | contact | 同 |
| bb03 | 1 | 10,11 | no_contact | no_contact | 异 |
| bb03 | 15 | 8,11 | no_contact | contact | 同 |
| bb03 | 26 | 5,6 | no_contact | no_contact | 异 |
| bb05 | 3 | 2,3 | no_contact | no_contact | 异 |
| bb05 | 3 | 3,4 | no_contact | no_contact | 异 |
| bb05 | 8 | 3,4 | no_contact | contact | 同 |
| bb05 | 20 | 2,3 | no_contact | contact | 同 |
| bb06 | 3 | 3,4 | no_contact | no_contact | 异 |
| bb06 | 4 | 2,3 | no_contact | contact | 同 |
| bb10 | 7 | 5,6 | contact | contact | 异 |
| bbv01_dbv01a | 54 | 2,4 | no_contact | no_contact | 异 |
| bbv01_dbv01a | 85 | 1,4 | no_contact | no_contact | 异 |
| bbv01_dbv01a | 150 | 2,8 | no_contact | no_contact | 异 |
| bbv01_dbv01a | 190 | 8,9 | no_contact | contact | 同 |
| bbv02_dbv02a | 196 | 5,6 | no_contact | no_contact | 异 |

## 问题 2：legacy 参考是否为刚体模型首盖

| 类别 | raw_df05 | post_df06 |
|---|---:|---:|
| FIRST_COVER_MATCH | 406 | 716 |
| INITIAL_OVERLAP_PD_MATCH | 14197 | 16190 |
| INITIAL_OVERLAP_PD_OTHER_FEATURE | 67012 | 65019 |
| INITIAL_TOUCH_COVER_MATCH | 661 | 661 |
| INITIAL_TOUCH_INCIDENCE_NOT_COVER | 8 | 8 |
| INITIAL_TOUCH_OTHER_FEATURE | 53 | 53 |
| NO_CONTACT_IN_STEP | 57710 | 57710 |
| OTHER_FEATURE_FIRST | 1547 | 1237 |

仅 FIRST_COVER_MATCH 回答分离初态下的首盖成员关系。初始相触和初始贯入另列；后者比较步初冻结 PD_closed，不伪造首入时刻。VV 双参考分别计数，完整次参考及相对 M4c 的类别转移见 three_answers.json。

上表计数单位是参考行，不是块对。下面按无序步—块对去重；首盖命中包含主参考或 VV 次参考的并集，三个分区“命中 / 有参考但不命中 / legacy 无该对”之和等于该群组对数。

| 群组 | 阶段 | 对数 | 任一参考首盖命中 | 有参考但不命中 | legacy 无该对 | 其中次参考命中 |
|---|---|---:|---:|---:|---:|---:|
| rigid_new_contacts | raw_df05 | 973 | 645 | 328 | 0 | 244 |
| rigid_new_contacts | post_df06 | 973 | 955 | 18 | 0 | 244 |
| chord_new_contacts | raw_df05 | 68 | 39 | 29 | 0 | 9 |
| chord_new_contacts | post_df06 | 68 | 51 | 17 | 0 | 9 |
| m4c_20_subset | raw_df05 | 20 | 4 | 16 | 0 | 1 |
| m4c_20_subset | post_df06 | 20 | 7 | 13 | 0 | 1 |

## 问题 3：残差与认证计数

逐块拟合 15220 次：δ=0 有 0 次，δ>0 有 15220 次。认证步—块对 0，未认证 64010。
残差为端点最大 L∞ 顶点误差，精确有理值随结果保留；包含应变、拟合近似与快照舍入的合效应，不能单凭该值分解三者。

| 分位 | 显示值（精确值见 JSON） |
|---|---:|
| min | 6.9013464368991147e-16 |
| median | 0.0022171352173461093 |
| p95 | 0.034415493885976714 |
| max | 0.18454965299659865 |

## 最小复现与冻结门

三个问题分别有独立小例，保存原始两端顶点、持久编号、拟合及参考比较。minimal_examples_reproduced.json 已通过实际 SE(2) 路径再执行。
```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:TEMP='D:/eab-wt/cx-e2/reports/codex/M5a_evidence/tmp/replay'
$env:TMP=$env:TEMP
python -X utf8 tools/m5a_se2_replay.py reproduce --examples D:/eab-wt/cx-e2/reports/codex/M5a_evidence/minimal_examples.json --out D:/eab-wt/cx-e2/reports/codex/M5a_evidence/tmp/replay/example_fresh.json
```

冻结来自同一完整批次的 15×30 前缀，不拼接中断运行。pytest 检查全部 450 帧证书、分区闭合、保守剔除守恒、残差认证与 15 个真实拟合，并重算 3 个真实非零转角事件对；不声称 pytest 重算了全部 450 帧根隔离。

## 运行纪律与遗留

全时程大记录位于被忽略的 tmp/replay/full_r1，不纳入提交；永久摘要及每个冻结文件均小于 1 MB。
revalidate-m4c 子命令使用绝对 --out 路径。第一次用相对路径的完整计算在发布元数据时失败，已整批作废并从头重跑 r2；未拼接、未改旧夹具。
PARTIAL：一般 δ>0 首盖稳定性证书未实现；真实 DDA 连续运动未恢复；单环和单步每块≤90° 的模型域不泛化到材料多环、近π大转角或SE(3)。
