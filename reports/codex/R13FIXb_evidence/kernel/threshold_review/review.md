# 次正规逃逸阈值修复：独立只读复核

结论：本次修复范围内未发现阻塞问题。没有改动生产代码、测试、policy 或 docs；本目录仅保存复核脚本与证据。

## 检查内容

- `margin._rounding_floor_exact` / `_effective_geom_tol_exact` 返回 Fraction；不调用 ±400 输入域检查。该 exact 指以文档声明的已显示 characteristic_length 和精确 coordinate magnitude 为数据计算阈值，不声称对无理几何直径作未舍入代数根运算。
- `interlock` 的实际候选 extent/r 窗口，以及高度乘法、差值、并列比较均保持 Fraction；默认权威根仍由 `_exact_escape` 的有理事件与精确成员判定产生。
- public `rounding_floor`、`effective_geom_tol`、`boundary_band` 对最终非零不可表示阈值抛出 ConstructionDomainError，quantity 分别为对应 `... result`，没有把阈值静默抹成 0。
- 3-4-12 直方体独立几何参考（对角线 13），在 2^-1070、2^-400、1、2^396 下逐值核对 floor/tol；后三档属于工程包络，首档验证保留的扩展域行为。
- 精确成员 API 在 Fraction 2^-1200 / 2^1200 下分别核对重叠 / 相接 / 分离六项判定，未引入构造支持域限制。
- 暖候选缓存后，将真正内部 floor helper 改为早 float 的故障函数；同输入缓存 misses 从 1 增到 2，真实函数被调用，非零 Fraction 阈值断言红。缓存没有掩藏此变异。
- `tests/test_r13fix_event_bindings.py` 字节与 HEAD 相同，旧 subnormal 门未改。

## 执行证据

- `targeted.log`: `142 passed in 8.89s`（完整旧 event bindings、perf_interlock 缓存/变异门、margin_exact）。
- `new_gates.log`: `4 passed, 79 deselected in 0.27s`（新增次正规实际候选窗口门、public max 门、两个真正 helper 早舍入变异）。
- `independent_checks.log` / `.json`: 四档数值、六个超 binary64 有理判定、三类指定异常、暖缓存变异、旧文件不变全部 PASS，附源与测试 SHA256。
- `independent_checks.py`: 可用 `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python -X utf8 <该脚本>` 重跑（PowerShell 以环境变量语法赋值；TEMP/TMP 指向工单 evidence/tmp）。

## 边界与执行失误

- 这是本次局部补丁的独立复核，不是整个构造普查、全域形式证明或全套验收替代。私有 helper 仍消费 characteristic_length 的受控浮点显示；超其构造范围仍可响亮拒绝，精确 predicate 路径未因此收窄。
- 首次回归命令误写不存在的 test_interlock_cache.py（输入错误，未运行测试），纠正为 test_perf_interlock.py 后取得上述 142 绿；独立脚本首次缺 PYTHONPATH（环境错误），设置到本树 src 后通过。
