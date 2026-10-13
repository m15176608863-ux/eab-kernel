# M4b 独立审查 R3：回放输入、路径与失败隔离

审查日期：2026-10-13。审查者：bdda_switch 子代理（未实现 eab 回放）。
范围仅为 WO-M4b 的 `tools/m4_shadow_replay.py` 与对应门，不冒充全库 G6。

## 结论

历史发现 **1 major、1 minor**；修复后独立复核，**剩余 0 critical、0 major、0 minor**。
本结论不是仅引用作者“已修复”，而是在修复后对真实文件读写入口重新执行原反例。

## R3-M1：输出硬链接能够破坏只读快照（major，已关闭）

原 `main()` 只比较 `Path.resolve()`；不同路径的硬链接共享同一文件却不被识别。
在系统临时目录复制 bb52 的冻结快照再造硬链接，得到：

| 反例 | 修复前 | 修复后独立重测 |
|---|---|---|
| `snapshot` ↔ `normalized.jsonl.gz` | 退出 2、输入已被截断 | 退出 2，全部既存字节不变 |
| `snapshot` ↔ `audit.json` | 退出 0 / GREEN，输入被审计 JSON 覆盖 | 退出 2，全部既存字节不变 |
| 两个输出互为硬链接 | 潜在规范化记录覆盖；一并列入修复门 | 退出 2，全部既存字节不变 |

当前 `_same_file()` 同时核对解析路径与 `samefile()`；写前核三对关系；异常写审计路径
亦受 `outputs_safe` 保护。无法安全落审计文件时向 stderr 输出 RED，不为写 RED 报告再破坏输入。
本次反例只处理临时副本，仓库原夹具及 legacy 求解产物没有修改。

证据：[修复前](review_R3_counterexamples.json)、[独立复核](review_R3_counterexamples_recheck.json)。
永久门：`test_hardlinked_outputs_fail_without_mutating_source_or_existing_files`。

## R3-m1：schema 整数类型检查不严（minor，已关闭）

原 `version == 1` 接受 `True`，屏幕尺寸有限性检查接受非整数。
当前版本号与屏幕尺寸都走严格 `_integer()`；独立重测 `version=True` 与
`screen.max_x=2560.5` 均被拒绝。证据：[类型复核](review_R3_schema_recheck.json)。

## 其余检查

- header / step / end 字段闭集、几何与 Tuple7 列序及长度、有限数、连续步号、
  明确请求/完成步数、生产端成功状态均有拒绝路径；不凭接触条数推测缺步。
- 几何别名只准坐标精确相等；不能靠重复点容差悄悄改动输入。保留原顶点号，
  VE 核邻接关系、VV 采用 M4a 修正后的共享角点身份，不伪造当前求解状态。
- 外部进程的回放失败只有 RED 审计结果，不存在向 b-DDA 求解表写回的接口。
- 损坏输入、未分类、非有限数、缺列/错位/跳步、内部枚举缺陷及文件硬链接门定向重跑：
  `21 passed, 15 deselected in 0.61s`，见 [原始日志](review_R3_R4_targeted_pytest.log)。

边界：本次验证不承诺在另一个进程恶意并发改换路径/硬链接时提供事务隔离；
正常离线单写者工作流已核。全套与新鲜导出验证由主报告汇总。
