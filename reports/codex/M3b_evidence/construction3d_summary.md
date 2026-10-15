# M3b 三维构造/输入认证/性能子任务汇总

## 逐项结果

1. **数值审计补齐有限族逐值代数证书**：两侧 `parts_a/parts_b`、凸盒所有有序 face 三元组、内点，
   以及一般 BSP 和一般斜切两侧新 Steiner 点，在 `2^-400 / 1 / 2^400` 上逐值对独立参考。
   一般 BSP 每档 4 胞、21 条顶点记录、20 条面记录、5 个不同新 Steiner 点；三档零数值失配。
   坐标参考为独立 Cramer/源半空间，不 import 生产剪裁/BSP/SAT；每胞所有半空间极点必须出现，
   每个输出坐标精确属于源平面独立解，所有面每条边×全部顶点的有向行列式非负且至少一次严格正。
   **限定**：这是逐值独立代数证书，不是第二份独立确定性 BSP 分支/合并顺序实现；语义覆盖仍由原表面 oracle 审核。
2. **输入认证扩展**：完整三角交集（含共面交）、顶点 link 多重圆、边反向双 incidence、逐壳零体积/
   奇偶嵌套定向。穿插、共面重叠、共享一顶点非流形、反向面/隐藏反向壳、零体积例均精确拒绝；
   非对称有理旋转、大平移与三尺度拒绝门通过。无浮点阈值。
   面引用定义几何：未引用顶点 buffer 入口剔除/重映射，不进 bbox；这不是零体积已引用片的豁免。
3. **性能部分完成**：任意方向精确 AABB 参数区间剪枝、不可变凸胞 hash 缓存、原始表面 exact 线段缓存。
   热查询明显提速；新增完整输入认证抵消冷启动收益，**整逃逸没有实测提速，保留 PARTIAL**。

## 精确回放及性能

采用既有 `reports/codex/M3_evidence/three_d_scan.py replay` 的全部 392 输入，完整重跑，不拼接。
基线为修改前冻结 `global_entrance.py/interlock.py`。**正式最终证据现为 `construction3d_frozen_r4_replay.json`**：
二维 compact 侧探针事件遗漏修复稳定后，从当前源码重新 byte-freeze 到本树 `tmp/construction3d_frozen_r4_export`，
复制前后当前字节与冻结字节完全一致；全新进程一次运行未改的历史 392 driver，**298 个 src/test/tool/driver 文件 before/post SHA256 全相同**。
该轮起止 UTC、实际命令、TEMP/TMP、次数=1、无 resume/splice、wrapper 前后 hash 与完整结果 hash 见
`construction3d_frozen_r4_replay_attestation.json`。同一次 child 结束记录实际 import 的 **29 个本仓库模块及 driver**，
不是事后根据调用链猜测；记录见 `construction3d_frozen_r4_actual_imports.json`。
45 个全部生产 src、29 个实际 import 模块和 driver 共 30 条路径，与最终 `final_suite_r4_export` 和当前工作树均逐字节相同，
见 `construction3d_frozen_r4_equivalence.json`。生产冻结后 3 个未 import 的测试/二维扫描/最终审计脚本仍有修改，亦在该文件逐名披露。
旧 `construction3d_frozen_replay.json`、其 attestation 与 r2 equivalence 保持原字节作为 **superseded 历史**：
它们绑定二维修复前的生产版本，不再作为当前源的正式认证，没有只更新旧 hash 或拼接旧回放。
对 `input_sha256 / exact_height / exact_offset / state` 共 **1568 字段完全相等**，最终暴力谓词调用 **0**。
另对提供的 pre-M3 历史 392 行冻结数据核同四字段，也全等。

| 冷/热测量 | 修改前 | 修改后 | 解释 |
|---|---:|---:|---|
| 最终 r4 完整 392 新冻结回放（带源码 pre/post + 实际 import） | 677.498 s | 687.658 s | 约 1.50% 慢；并发争用下不能据此宣称稳定整流程加速 |
| 修复前旧完整 392 冻结回放（superseded 历史） | 677.498 s | 649.483 s | 保留原计时/原 hash，不用于当前源认证 |
| 先前完整 392 过渡轮（无启动源码 hash） | 677.498 s | 679.415 s | 此轮约 0.28% 慢；保留说明测时波动，不用于正式源版本认证 |
| box 冷完整逃逸，中位数 | 0.017498 s | 0.030834 s | 加入完整认证后约 1.76 倍耗时 |
| wall 冷完整逃逸，中位数 | 1.609613 s | 1.623101 s | 约同速 |
| TIA 冷完整逃逸，中位数 | 0.163881 s | 0.316236 s | 加入完整认证后约 1.93 倍耗时 |
| box 热 exact 状态查询 | 84.264 μs | 2.460 μs | 34.25 倍加速 |
| wall 热 exact 状态查询 | 705.915 μs | 4.247 μs | 166.21 倍加速 |
| TIA 热 exact 状态查询 | 260.152 μs | 3.546 μs | 73.36 倍加速 |

冷热基准每族独立 5 次；冷次清空所有模型/事件缓存，热次每轮 100 个不同参数状态查询。
不能把热查询倍数说成完整逃逸倍数。

## 变异牙与门

三条均在独立子进程先检查基线，再替换实际被测函数；不执行哈希门；无捕获 AssertionError 真红。

| 变异 | 预期语义红 | 说明 |
|---|---|---|
| `_validate_embedded` 内将三角交集错误置空 | overlapping coplanar shells must be rejected before decomposition | 非邻接共面重叠共享体积为零，变异后实际错误接受为 2 parts，非偶然总量护栏红 |
| `_line_candidate` 漏上方凸片 | all exact box candidates are retained | 精确双区间闭式预期缺一段 |
| `_merge_parts` 真实全共面邻接候选分支绕过凸性守卫，错合成外包盒 | full-facet nonconvex merge filled independently excluded region | 两四面体真共面，探针整体违反双方独立半空间，错合后却贯入；不是最终返回值替换 |

最新新门（强化真实邻接分支变异后）：`25 passed in 1.68s`。
最新新门 + 原 M3 三维 + 原 merged interlocking 回归：`48 passed in 14.82s`。
全套四片及静态门由主任务最终跑数提供，本子任务不先宣称 G6 或里程碑退出。

## 可重跑入口与清单

- `tests/test_m3b_construction3d.py`：25 项新门。
- `tools/m3b_construction3d_evidence.py --mutations`：三条真红；`--microbench` / `--baseline-folder ...`：冷热基准；
  `--compare OLD NEW OUTPUT`：完整 392 对账。
- `construction3d_notes.md`：输入域、完整交集论证、缓存失效边界和数值审计范围。
- `construction3d_numerical_audit.json`：三档记录及 oracle import 清单。
- `construction3d_replay_comparison.json`、`construction3d_prem3_comparison.json`：字段对账、调用数、输入哈希。
- **最终正式源认证对账**：`construction3d_frozen_r4_comparison.json`、`construction3d_frozen_r4_prem3_comparison.json`，
  及 `construction3d_frozen_r4_replay_attestation.json` / `construction3d_frozen_r4_actual_imports.json` /
  `construction3d_frozen_r4_equivalence.json`。
- `construction3d_frozen_r4_replay.py`：新鲜 byte-freeze 后一次性运行全部回放、记录前后源码 hash 与实际 import 的标准库包装脚本；
  `construction3d_frozen_r4_equivalence.py`：重核当前源及最终 r4 全套导出字节。
- 旧 `construction3d_frozen_replay.py` 及旧 frozen comparison/attestation/r2-equivalence 原样保留，仅历史证据。
- `construction3d_micro_summary.json`：冷热数据；`construction3d_mutations.json`：三条对应真实红日志。
- `construction_peer_review.md`：独立边界/出口定向审阅；发现 unused-buffer oracle 缺陷已交 boundary 子任务处理。

## inventory 交接

没有新增公开浮点 API。更新既有 `GlobalEntrance3D.parts_a/parts_b`、`ConvexPart3D.vertices/faces/interior` 的
数值门条目；内部 `_bounds` 为已核 Fraction 坐标极值选择，`_line_candidate` 仅布尔，hash 缓存不是几何构造量。
新增源码只 import 标准库 cached_property；测试的 pytest/inspect/textwrap 为既有门和真实故障注入脚手架。
所有源文件 UTF-8 无 BOM，所有定向命令 TEMP/TMP 和 pytest basetemp 限于本树 evidence/tmp。

子任务遗留：完整逃逸冷启动/总回放提速未达到；一般 BSP 拓扑顺序不以数值候选证书冒称独立完整副本；
任意深层 monkeypatch 必须清既有外层 `_exact_escape_cached`，新增直接层 key 不提供全局动态失效保证。

## 一般位置独立补例（与原 6733 探针不混合）

`gp_boundary_probe.py` 以自持 Fraction 差/叉/点积核 2 项满维、16 项跨体面/面非平行、
48 项双向棱/面非零点积、36 项跨体棱/棱非平行，共 **102/102** 条充分 GP 条件；
完整 audit 为 V11/E22/F13/两侧26，共 **72** 探针，另 13 个 local atomic 片，0 mismatch、0 skip。
二维 production 修复后已真实重跑，耗时 0.331327 s，49 个源码/脚本 hash 前后不变；
最新 `gp_boundary_probe.json` 绑定修复后源，旧字节留 `gp_boundary_probe_superseded_pre2dfix.json`。
这是新有限 GP 族，不把原一般四面体误称 GP，也不以有限数值例替代 T3L 的条件证明或 G6。
