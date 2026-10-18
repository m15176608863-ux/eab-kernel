# H1 P1 / P3 / 机械重键路径核对

**这是实施代理的最终代码路径核对，不是 Claude 安排的一路独立对抗核查，也不是里程碑退出判据。**

## 结论

- 对 `1ce9a91` 的全部 52 个 `src/eab` 模块逐定义比对：迁移后 55 个模块，1074/1074 个类、函数及嵌套定义 AST 一一对应；没有新增或漏配的生产定义。6 张状态/盖映射表 AST 完全相同。
- 唯一白名单归一化是 `geom3.Polyhedron.edge_dir` 的零长边错误提示：删除域专用 reader 示例；异常类型、条件、数学分支不变。模块归属、`__module__`/导入路径和根包域映射导出按工单有意变化，不能宣称旧 import API 仍兼容。
- `bdda2d_affine` 从核心导入原 `AffineFit/fit_affine` 对象，使 INT1 仅改顶层 import，全部 10 个函数原文保持不变。这是 adapter → core 的合法组合，不是在内核放转发。
- 三个封存语义门仅摘 `5e3ba68:tests/test_m5e_revision_semantics.py` 中指定函数及其最小局部有理数 helper；保留原断言与反例。没有摘取变异框架、台账或充分性门。原码 3/3 通过，指定内部缺陷分别由对应语义断言报红。
- 二维对称元门是独立 winding/相交 oracle 加位形互换，不仅比较两次相同生产算法；24 个非凸/旋转/平移/尺度格子与 1 个产物互异门通过。P3 合计 `28 passed in 0.24s`。三维可选门未做。

## 机械重键证明边界

- `tools/h1_rekey_policy.py` 已先调用 `verify_relocation(root, baseline)`：全定义 AST 验证封住了“删除所有定义再比较模块”的漏洞。
- 常规准入行保持函数源码 pin、规则和 AST 站点；仅 `R12b-L0008`（contact_record）与 `M5B-S0038`（dda_motion）是 `<module>` 上下文例外，分别对应映射表移出、模块导入路径/定义搬家。例外不是新数学函数准入。
- 现证据为 3522 → 3522 项；114 个变更行 = 112 个普通重键 + 2 个模块上下文例外。648 个 import 项只机械映射其中 10 个，前后 648 个唯一项，无键碰撞；waiver ID 集合不变。
- 原先任意剥离 import 的证明边界已收紧为显式导入绑定映射检查。直接将 INT1 的绑定改成不相关模块，检查会报 `unrecognized import rebinding`。当前实际 diff 无导入重排或额外作用；所有函数源码 pin 保持原样。
- `test_m5a2_replay.real_inputs` 的函数字节不变；仅顶部 `gzip` 换成 `frozen_gzip as gzip`。该只读输入适配器做归档路径解析后原样调用标准库 gzip，不属于生产几何/数学路径。
- 已不存在的历史 instrumentation scope 保持不活动，没有借重键复活。源码比较只用于本次搬家证明，不新增常驻源码哈希绊线。

## 牙与证据

- 去域化门：源文件副本中追加 adapter import 或 `mtype`，真实 CLI 均以退出码 1 报对应违规；相对导入、父包初始化与传递导入另有具名门。
- 搬家验算器：副本中把 `model_robustness._scale` 的 `k*x` 改成 `k+x`，精确由 `_scale` 的 AST 对应断言报红，没有改真实源码。
- 数学与门证据：`p1_p3_peer_check.json`、`p3_verification.json`、`p1_function_relocation.json`、`policy_rekey.json`/`.csv`。
- 当前引用补扫 399 个文本文件，机械更新文档 1 文件 1 处，完整旧路径剩余 0；两处历史计划裸文件名保留，见 `p1_current_path_references.json`。特别核对 M5b 两份合同文档没有旧模块路径，M4c 工具的 live source list 已指向存在的 `src/eab/numeric_decode.py`。
- 本核对没有跑全档；8 格 instrumentation 门及收尾全档由主代理/验证代理统一执行，避免重复长跑。

## 可重跑命令

```powershell
python tools/h1_verify_relocation.py --baseline-ref 1ce9a91
python tools/h1_kernel_purity.py
python tools/h1_rekey_policy.py --baseline reports/codex/H1_evidence/tmp/baseline_export --output reports/codex/H1_evidence/tmp/peer_rekey
$env:TEMP = "$PWD/reports/codex/H1_evidence/tmp"; $env:TMP = $env:TEMP
python -m pytest -q -p no:cacheprovider --basetemp reports/codex/H1_evidence/tmp/peer_p3 tests/test_h1_adopted_semantics.py tests/test_h1_entrance_symmetry.py tests/test_kernel_purity.py
```

重键复跑命令故意不带 `--apply`。历史量化数 4283/4280/102/2728/44 仅修正文案；本单没有全量回放，不声称重新验证这些计数。
