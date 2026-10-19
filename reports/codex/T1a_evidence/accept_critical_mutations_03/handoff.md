# 阈值 / 敏感性返修证据（本轮自产）

结论：C1、C2、C11、C10、S7、C9 六个生产源码内部缺陷均由新数学断言检出；既有 14 个正阈值敏感性结果没有丢失。

## 改动

- `CriticalParameter2.bisection_termination` 与 `threshold_proof_reason` 分开保存；`reason` 不再被证明结果覆盖。`ThresholdProof2.lower_signs/upper_signs` 的 `None` 表示无延续证明，空元组只用于退化区间。
- 阈值敏感性使用端基前检查延续证明以及临界点所有比值非负。缺基返回 `unresolved / critical_basis_unavailable`；域边界零阈值无跨越证明返回 `unresolved / threshold_on_domain_boundary_without_proof`，不增“认证零导数”分支。
- 处处不可行的域返回 `INFEASIBLE / infeasible_on_domain` 并附 Farkas；未解析接触传播 `contact_set_unresolved`。
- profile1 运动学冗余真 VV 不计静力，`true_vv_excluded_from_statics` 传播到 limit、critical、sensitivity；回归 c 在 μ_max=2 下有界。把该角点保留为两个摩擦半平面的诊断模型在 μ=2 无界，具名门同时核验两套结果及精确证书。
- 无斜率结果显示状态为 `NOT_APPLICABLE`；有斜率的三个成功路径显式 `EXACT`。条件串为 `L1接触骨架不变`。

## 验证

- 新文件 `tests/test_tia2d_critical_acceptance.py`：48 个小迭代预算阈值探针及延续、回收锥、原因串、D17 等具名门。
- 源码副本基线（3 个文件）：`113 passed in 10.78s`。日志 `baseline.log`。
- 真实源码副本变异：C1 `1 failed in 0.27s`；C2 `18 failed, 30 passed in 7.12s`；C11 `1 failed in 0.19s`；C10 `1 failed in 0.18s`；S7 `1 failed in 0.18s`；C9 `1 failed in 0.28s`。每项退出码为 1 且命中 `summary.json` 所列语义断言，不是哈希、导入或偶然异常。
- 14 个原正阈值导数逐项精确重算：全部 PASS；数据 `threshold_slopes.json`。三组未反转和单反转各自 dt=1、dh=0，细长反转 dt=15/16、dh=−17/32。
- 全现有 TIA 快档在当时工作树：`475 passed, 39 deselected in 58.23s`；此为返修中定向检查，不代替 root 的最终快档 / 全档四分片。
- 内核纯度 0；五个本任务修改的核心 / 测试文件静态构造定向扫描 0 诊断；没有新增准入。初次静态扫描暴露 `getattr`、`object.__setattr__`、测试关键字解包不在闭子集，均以显式字段 / 显式构造替换后复验。

## 复跑

`python -X utf8 tools/tia2d_critical_mutations.py --output reports/codex/T1a_evidence/<新的目录名>`

工具只修改其私有证据副本，不修改生产源码。源码前后 SHA 用于记录变异，不作为数学测试的判据。各次运行均独立，未拼接中断日志。全库最终静态、快档、全档与无 Git 副本由 root 集成执行。
