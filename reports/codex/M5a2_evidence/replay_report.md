# M5a2 A1 / A3 / A6 same_time 分项交付

## 范围与边界

- 本分项只新增 `tests/test_m5a2_replay.py`、`tools/m5a2_replay_mutations.py` 和本目录 `replay_*` 证据；未修改原生产源码或正式夹具。
- A1 是回放接线、序列化、分类的独立语义门，不是另一个几何 oracle：期望几何直接来自生产 SE2 与 M4c 内核；拟合、全局特征编号映射及分类在测试内独立重建，禁用回放的 fit/result/classifier/时间比较 helpers。
- 独立期望不读取 code_hashes；原始冻结记录与当前回放路径各自逐字段核对。数学等价时刻按精确代数数比较，不要求不同合法隔离区间逐字节相等。

## A1 真实转动帧

| 算例 / 步 / 块对 | SE2 / 弦 | 完整盖集合相同 | 覆盖 |
|---|---|---|---|
| bb05 / 4 / 1,4 | contact / no_contact | 否 | 弦无接触不能旁路 SE2；legacy FIRST_COVER_MATCH 与 OTHER_FEATURE_FIRST |
| bb05 / 4 / 2,4 | no_contact / no_contact | 是 | 真正相同无接触；扫掠排除路径 |
| bb10 / 7 / 5,6 | contact / contact | 否 | 同为接触但首盖不同，且两时刻不同 |
| bb12 / 2 / 2,9 | contact / contact | 是 | 相同首盖但不同无理时刻 |

逐字段范围：pair、initial_state、rigid/chord/translation 的 status/time/time_display/features/incidences、残差及认证、path、所有比较布尔值、pd、M4c 子集标记；每条两阶段 legacy 行的 index、tuple7、pair、两条 reference 与四种 category。index 和原始 reference 从快照原行独立恢复。

## A3 小转角扫掠界

- u = ±10^-1 … ±10^-6；非对称瘦四边形使 9/5 系数不足在小角度区间真实暴露。
- 每档 3 个尺度/平移组合（尺度 10^-6、1、10^5；平移 0、10^3、10^6）× 3 个旋转（恒等、3-4-5、固定种子随机有理旋转）× 11 时刻 × 4 顶点，直接展开坐标检查 `_swept_bounds` 包含。
- 每档 9 组扫掠产物互异。独立公式不调用 rotate_rational/at/endpoint/多项式/扫掠原语。

## A6 same_time 无理分支

- 多项式 t²−t+1/8 的两个无理根，各自正确 branch 必须相等、反 branch 不等。
- t²−t+1/16 的无理根不得只因在同一 branch 半区就认作相同；另保留 None 分支。

## 真实内部变异与重新冻结

`tools/m5a2_replay_mutations.py --name <新目录>` 每个控制/变异独立子进程，60 秒硬超时；中断目录不可复用。先把生产 code_hashes 钉到原冻结哈希，再从真实函数源码用唯一锚点替换、compile 成函数并注入；绝不追加假行。

三个账本变异在 tmp 中重新执行 bb05 全部 30 帧，调用真实生产 `freeze()`，仅将 CASES 缩为 bb05、ROOT 与 ingest.FIX 重定向到临时沙箱。新 normalized/hash/provenance 全部来自 mutant 产物；所有 fresh hash 门通过后，冻结数据读回被新语义断言击穿。正式 fixtures/PROVENANCE 未触碰。默认 pytest 仅做单目标微冻结；30 帧生产 freeze 仅在证据脚本执行。

| 变异 | 结果 | 语义击杀断言 |
|---|---|---|
| swapped_models | 控制绿、变异红 | `M5a2 ledger rigid status` |
| chord_no_contact_shortcut | 控制绿、变异红 | `M5a2 ledger rigid status` |
| classifier_uses_chord | 控制绿、变异红 | `M5a2 ledger independently classified category` |
| sweep_nine_fifths | 控制绿、变异红 | `M5a2 small-angle swept bounds contain path` |
| same_time_wrong_branch | 控制绿、变异红 | `M5a2 same_time irrational matching branch` |
| same_time_ignores_polynomial | 控制绿、变异红 | `M5a2 same_time rejects different irrational polynomial` |

最终证据：`replay_mutations_r5/summary.json`；9/9 semantic_kill，source_snapshot_unchanged_during_run=true。r1/r2 为前期微冻结验证，r3 为首次生产冻结验证，最终以 r5 为准。

## 运行与 import 清单

- 最终定向：`31 passed in 0.98s`；收集 31；0 skip。`replay_verification.json` 包含完整命令、节点、源码 SHA256。
- Oracle 标准库：fractions.Fraction、math.isqrt、random.Random、gzip、json、pathlib.Path、functools.lru_cache、types.SimpleNamespace；工具胶水另用 sys。pytest 为测试框架。
- A1 被测依赖：生产 se2.se2_first_entrance、motion.motion_first_entrance 与 RealAlgebraic；仅作为回放语义的参考内核，非独立几何 oracle。快照解析由已有 reader 提供数据，未使用其分类器。
- 静态准入与全套四片由主代理统一处理；本分项不修改 inventory/policy。

## 附加独立复核

- A5 的 15 种 adversarial callable 写法全部拒绝，记录见 `replay_independent_static_review.json`；包括直接参数、属性、namespace、import alias、默认参数、tuple/attribute 流、factory、partial、kwargs、stars、条件 alias、闭包、`__call__` 和模块级 lambda。
- 主代理新增静态/runner 定向门独立执行：`11 passed in 1.02s`。未发现 A5 或 renewal 的关键绕过。
- 运行器后续审查发现的非有限 timeout、遗漏新增源文件、仿射输出参数边界三个 minor 已修复并复测关闭；详见 `review_static_runner.md`。

## 限制

- 本分项不重新认证 M5a 全部 1810 步；它建立稳定、低成本、具有真实反例牙齿的回放语义回归门。
- `_swept_bounds` 抽样门不是连续包络证明的替代；原系数 2 的解析证明仍是数学依据，小角度门专门防止该系数退化。
## A1 第二轮：完整 focused frame 聚合门

独立对照现在覆盖完整单块对生产帧的顶层 schema、step/endpoint_step、输入/基线摘要、blocks 全记录、stats，以及每阶段 counts/secondary_counts/transitions。

- `independent_frame_expected` 直接从独立 pair 模型结果及独立 reference 分类表构造计数；不复用生产计数器。
- 每块运动与精确残差仍由测试内拟合重建；delta_display 使用独立 `eab.oracle_construction.scalar_exact`（回放生产出口是 `scalar_rational`）。
- `baseline_frame_sha256` 针对实际输入的 focused baseline，不能与未裁剪的历史全帧 baseline 摘要混为一谈。
- 新增内部变异：same/different 统计桶互换 → `M5a2 frame independent stats`；`RigidFit.record` 把 center 串成 translation → `M5a2 frame independent blocks`；phase counts 使用 chord 类别 → `M5a2 frame independent phase counts`。
- 新三变异走完整 focused frame 语义门；原三账本变异仍执行 bb05 全 30 帧生产 freeze 后验证目标块对。两种门的统计域严格分开。
- 默认全文件从 24 项增加至 31 项，实测 0.85～0.98 秒，追加门耗时约 0.23～0.36 秒。最新证据以 `replay_verification.json`、`replay_mutations_r5/summary.json` 为准。