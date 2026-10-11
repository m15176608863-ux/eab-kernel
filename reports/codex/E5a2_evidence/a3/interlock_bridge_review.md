# E5a2：interlock 最小桥接只读复核

## 结论与范围

本复核只针对 A1 三态接入后必须处理的构造高度适配，不是 G6，也不替代 E5b 的 interlock 精确化。按“返回高度经精确非贯入核验；盖标签仍是旧 nominal 报告层”的有限契约，未发现阻碍本单的 critical / major。没有以测试全绿推导候选完备性或最早出口的精确性。

最终逻辑复核锚为 `interlock_bridge_audit.json` 中的 `interlock_sha256`；A1 随后仅调整说明和新门。此子任务没有修改任何生产代码、原测试或参数。

## 独立诊断

- 原四文件：`test_interlock_candidates_contract.py`、`test_interlock_e5a.py`、`test_frozen_ee_sign.py`、`test_frozen_lowdim.py`。
- 原样结果：`6 failed, 122 passed in 81.57s (0:01:21)`，见 `interlock_diagnostic.log`。
- 六失败均为 `test_public_candidates_keep_both_branches_inside_the_predicate_band` 的 `escape_height_covers` 候选耗尽异常，格子为 `(e, side) = (1e-11,+1), (1e-10,±1), (5e-10,±1), (1e-9,-1)`。其余三个文件全绿，不需要测试迁移。
- A3 有限窗口不是原因：`_candidates` 调用 `enumerate_covers3(window=inf)`；该窗口直接接受，不读取构造 gap。
- A1 桥接后不改门重跑 candidates 文件：`14 passed in 4.87s`，见 `interlock_candidates_reprobe.log`。

## 逐路径复核

1. **初始返回 0**：检查的 `A.translated(offset)` 与调用方随后用高度 0 构造的输入一致；只有精确内部不相交时才返回。
2. **原候选返回**：每个不同的浮点高度独立核验；不再把同一舍入簇内较低高度的贯入结论复用到较高高度。完全相同的高度去重安全。
3. **上构造返回**：一次 `nextafter(z + r/nz, +inf)` 只生成候选，不替代判据。被核验的是 `A.translated((offset.x, offset.y, offset.z + lifted))`，返回的也确实是 `lifted`，没有核验上点却返回未核验下点的漏洞。
4. **工程坐标**：先加 `offset.z + lifted` 再对每个原顶点平移，顺序与公开调用方一致。因此即使抬升值加回大坐标时再次舍入，该舍入后实体也已被核验；不能只凭高度的 `nextafter` 声称安全。
5. **零高度簇**：初始若确有微贯入，零簇只在正的上构造高度被核验为不贯入之后返回；否则继续，不能把微贯入重新标成边界。
6. **正 tol 改为 0 的消费方**：A1 的报告带仅能将分离侧 `-1` 报为 `0`，不会改变精确内部重叠状态 `1`；只消费 `== 1` 或 `!= 1` 的分支改用零 tol，布尔答案逐点等价，并避免无用的精确表面距离计算。

## 小额回放，不冒充独立 G0

`audit_interlock_bridge.py` 只复核真实返回构造，与生产路径共用关系判据，因此明确只作安全回放佐证。运行 9.9868 秒，完整参数与结果见 `interlock_bridge_audit.json`。

| 输入 | 初始状态 | 返回 height | 返回实体零带状态 | height 是原候选 |
|---|---:|---:|---:|---|
| 原失败陡坡正侧 `0.16+1e-11` | 1 | 0.02027523643405324 | -1 | 否 |
| `s=1e-3, t=1e5, Rz=0.7` 一般偏移 | 1 | 0.00018894045959350682 | -1 | 否 |
| 同工程坐标零偏移 | 0 | 0 | 0 | 是 |
| 原点零偏移 | 0 | 0 | 0 | 是 |

## 必须保留的界限 / E5b 交接

- winner / ties 仍按 nominal 高度和原报告带裁决；上构造 `height` 不是 winner 的精确零 gap 根，也未证明是最小可表示非贯入高度。冻结导数是 nominal 分支的导数，不能解释成上取构造操作本身的导数。
- 极小 `nz` 时 `r/nz` 可跨过后续名义高度簇；精确验收仍保证**所返回实体不贯入**，但不构成精确 earliest 的证明。E5b 应用有理射线事件排序 / 区间证书处理，不宜继续增加浮点容差补丁。
- `_candidates` 对 `z <= 0` 的 raw 候选不做 extent 过滤。新增零簇分支的标签只能沿用上述 nominal 报告层解释；本复核没有证明组首标签是返回构造处真实接触。若文档额外声称“每个返回标签必在返回 height 上精确零 gap 且在程”，该声称不成立，不能用此复核背书。
- 旧 docstring 中“比真值低的候选可因 geom_tol 而分不出贯入”的解释必须删除：现在内部重叠永远是精确状态 1。已通知 A1 修订，其桥接新门及突变证据由 A1 汇总。

以上限定已发送 root 与 A1；最终独占全套开始前，本代理已停止全部 CPU 任务。
