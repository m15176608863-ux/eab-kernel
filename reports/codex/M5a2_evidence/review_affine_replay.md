# M5a2 独立对抗审查：仿射研究与回放语义

## 结论

审查对象不是本审查者实现的模块：R1 为仿射拟合、轨迹、理论及 B7 统计来源；R2 为 A1 独立回放门及重新冻结后的内部变异。

**首次发现：0 critical、1 major、2 minor；修复并独立复测后：0 critical、0 major、0 minor。** 三个发现的原失败结果与修后拒绝结果均保存在 JSON，不把首次发现从结论中抹去。本报告只覆盖这两路，不宣称整仓 G6 或 B8–B10 完成。

本审查完成时的定向检查最后一行：`63 passed in 1.47s`，0 skip。独立运行的回放变异为 9/9 语义击杀。这些是分项原始证据，不是整单最终四分片计数；整单只采用全新 `final_suite_r3` 的完整结果，`final_suite_r1`（审查中断）与 `final_suite_r2`（换行保真修正）均已作废。本报告不预判最终四分片结果。

## R1-001：输入绑定竞态（major，已关闭）

**原缺陷。** 早版 `m5a2_affine_replay.replay_case` 在开头验证旧输入，末尾重新计算 input_hashes，却没有和同一组初始哈希比较。已经读取的计算数据与末尾记录的输入字节可能不是同一份。

**真实复现。** 复制 bbv01_dbv01a 的 snapshot/terminal 到本单 scratch，仅重定向 INPUTS；在生产 `fit_affine` 的第一次调用时，将已经读取完的 snapshot 首步所有 x 加 1000，再执行原拟合。旧程序仍返回 `complete=true, steps=400`：

- 开始 snapshot SHA256：`7b5f3d42157054639f6cf86a0dce950e367396c4aba02e4f95b7bc8c72a26bca`；
- 修改后与最终错误绑定的 SHA256：`340ad470153ab0ca483c508c28a74a2dff22d8b484fc467df294b3a16461e2da`。

没有修改原始快照或姊妹文件，复现只写当前工作树的 ignored tmp 副本。

**修复与独立复验。** 实现者固定 snapshot、terminal、M5a normalized、M5a audit 四文件的初始哈希，在 batch/worker 入口、读取后、worker/batch 出口核对同一闭包，只发布初始哈希。审查者用原注入再次运行，得到 `AssertionError: affine replay input changed during run: discard and rerun`，没有发布完成摘要。四类文件变动的正常回归门也已加入。

## R1-002：最小例引用旧摘要（minor，已关闭）

初次检查时，`affine_minimal_examples.json.full_summary_sha256` 仍对应 r4 之前的摘要，默认 verify 却不核对该字段；三个数值例仍通过，说明是证据绑定缺口，不是数值反例。

实现者重新冻结到最终 r4，并加入默认验证的强哈希断言。审查者重新运行三个顶点数据自包含的例子全绿；默认验证还读取冻结总摘要并核对其哈希，但不依赖 ignored 全时程原件。另将 scratch 最小例的摘要哈希改成 64 个零，默认验证明确拒绝：`minimal examples must bind the current complete full summary`。

## R1 数学、数值和统计复核

1. 只读核对 b-DDA `moments.hpp::update_block_vertices`：理想实数更新确实是 `c+d+[R(θ)+E](x-c)`，有限转动与常应变相加，而非相乘。正文明确说明拟合 u 不恢复内部角度、补偿矩阵未必对称、时间律不等价，未发现夸大物理一致性。
2. 复核中心化精确最小二乘、端点闭合、u=0 与零应变退化、事件多项式次数≤8、Neumann 非反转充分条件，以及指定校正轨迹的 `sδ` 偏差界。正文将这些和未知物理轨迹、一般首盖稳定证书分开，证明边界正确。
3. 审查者独立生成 120 组精确拟合及 120 组轨迹例：拟合 oracle 为未中心化 3×3 Gauss–Jordan 消元，轨迹 oracle 为复数 Cayley 连乘；另有 100 组矩形最近间隙闭式。固定 seed=5101502，含极小尺度、10⁶ 平移和微小非仿射扰动，**0 失配**。没有调用生产拟合、旋转或距离原语计算期望。
4. 对最终 `affine_full_r4` 的 **15220 条逐块原始行、1810 步、15 算例**独立重聚合：各算例及全局 8 类精确分位数（无正间隙的算例为 6 类）、零残差/块对计数、原始行哈希、每算例四文件输入闭包及当前源码哈希全部一致，0 失配。
5. 933/4 是“伴随端点状态翻转”的描述性分层，不是已证明的因果分解。正文明确保留一般八次首入、δ>0 首盖稳定性、全三模型四问题对账为 PARTIAL，未把舍入量级残差冒充认证。

## R2-001：聚合统计未进入独立期待（minor，已关闭）

**原缺口。** 原 A1 新门逐字段核对 selected pair 与 legacy 记录，但没有独立期待完整 focused frame 的 blocks/stats/phase 聚合。

**真实内部变异。** 审查者从生产 `frame_result` 函数体编译变体，将 `separated_chord_same` 与 `separated_chord_different` 桶交换，先屏蔽源码哈希。四个原 A1 帧守门全部通过；bb05/4/(1,4) 实际 `same_chord_status_and_cover=false`，统计却记 `separated_chord_same=1`。

**修复与独立复验。** 新增 `assert_frame_semantics`，对完整 focused frame 的 schema、blocks、独立残差显示、stats、各阶段 counts/secondary_counts/transitions 建立独立期待。原变异现红在 `M5a2 frame independent stats`。另增加 block center 错位与阶段计数误用弦分类两种真实内部变异，均命中对应新语义断言。

## R2 冻结变异审计

独立重新执行 `tools/m5a2_replay_mutations.py --name replay_review_independent_r2`：**9/9** 的 control=0、mutant=1，红在记录的语义断言，源码快照前后一致。

- 三个原账本变异（模型对调、弦无接触错误旁路、分类误用弦）先重新计算 bb05 全部 30 个真实前缀帧，调用真实生产 `freeze()`，通过新 frame/file/code hash 检查，再被读回数据的独立语义断言击杀。没有先生成正确结果再追加假行。
- 新增的三个 frame 元数据/统计变异检查的是完整 **focused 两块帧**，不把 focused 统计与全 bb05 统计混用；其证据不声称额外执行了全 bb05 freeze。
- 另三个变异覆盖 9/5 扫掠系数、无理时刻错误分支和忽略多项式。
- A1 的期望几何直接来自生产 SE2/M4c 内核，但绕过回放接线、拟合、特征编号映射及分类 helpers；这是回放语义 oracle，不冒称另一个独立几何 oracle。分类表和全局 ID 映射在测试内独立构造，真实帧包含相同及不同结论。

## 限制

- 本审查没有独立重写一般仿射首入算法；该算法本单尚未提供。
- 数值随机检查和小角度包含采样不替代相应连续数学证明。
- 聚合复核证明冻结数字可从该运行原始行复现，不证明真实 b-DDA 连续路径或因果归因。
- 本审查者先前实现的 A2/A4/部分 A6 不属于本次“独立”审查对象。

## 证据

- [机器可读完整审查与可复现程序](file:///D:/eab-wt/cx-e2/reports/codex/M5a2_evidence/review_affine_replay.json)
- [独立重新运行的 9 项回放变异](file:///D:/eab-wt/cx-e2/reports/codex/M5a2_evidence/replay_review_independent_r2/summary.json)
- [最终仿射全时程摘要](file:///D:/eab-wt/cx-e2/reports/codex/M5a2_evidence/affine_full_summary.json)
- [顶点数据自包含最小例（验证另需冻结总摘要）](file:///D:/eab-wt/cx-e2/reports/codex/M5a2_evidence/affine_minimal_examples.json)

REVIEW_AFFINE_REPLAY_COMPLETE: 0 critical, 0 major, 0 minor remaining; 1 major and 2 minor found, fixed, independently retested.
