# R9FIX 收尾：R8 普通裕度差变异门补强

## 根因与修前证据

第二轮全套唯一失败是 `test_migrated_margin_gate_catches_real_pre_subtraction_rounding[old_subtraction-ordinary_1ulp]` 的 `pytest.raises` 未捕获错误，不是生产计算出错。R9 把窗口距离从“分别舍入的全局见证点相减”更正为最终精确平方距离开方后，旧普通姿态的 `RN(d)-delta` 恰好与 `RN(d-delta)` 相等；旧注释依赖已经移除的另一项构造缺陷。

[修前单模块日志](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/gap_gate_red.log)：`1 failed, 17 passed in 0.57s`。原文件保存为 [gap_gate_before.py](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/gap_gate_before.py)。

[数学探针日志](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/gap_gate_math_probe.log) 列出了旧普通输入变换后 4 条及基准 4 条接触的十六进制结果：全部 `RN(d)-delta == margin_gap`，并逐值通过独立 Fraction 中点检查。因此不能要求这个原单格继续区分已经数值等价的变异，也不能删掉该格或放松 `pytest.raises`。

## 只加强，不删改旧断言

唯一测试文件改动：[test_r8fix_margin_gap_gate.py](file:///D:/eab-wt/cx-e2/tests/test_r8fix_margin_gap_gate.py)。原 `_ordinary_gap_gate` 中 `invariance.test_margin_layer_is_invariant("box_box_face", 7, 0., .001)` 原样保留；其所有距离、标签、精确平方距离和差值断言未动。原普通/大消去两格 × 四种变异的 8 格参数网格完整保留；所有 `pytest.raises` 及匹配文案未变。

在原普通门之后增接一个全部输入顶点坐标可由 binary64 精确表示的普通盒格：

- A 的 x 区间 `[1,2]`，B 的 x 区间 `[-1,-2^-53]`，y/z 区间重叠。
- 独立区间真值 `d=1+2^-53`，`delta=1/4`，精确平方量 `(1+2^-53)^2`。
- `d` 恰为 1 与其下一浮点数的中点，1 的有效尾数为偶数，故 `RN(d)=1`。
- `d-delta=3/4+2^-53` 本身可表达：正确 `gap=0x1.8000000000001p-1`。
- 旧式 `RN(d)-delta=3/4=0x1.8000000000000p-1`，恰错一个普通量级 ULP。

新门先用 Fraction 证明上述中点及可表达性，再核生产返回的精确平方距离、舍入距离、每条最近接触的独立中点差值证书和 closed 状态。没有调用生产构造函数生成预期值；没有在生产输出后植入假数据。

## 绿门与真实内部变异

- [修后单模块日志](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/gap_gate_green.log)：`18 passed in 0.59s`，包括全部原 8 个真实内部变异格。
- [变异脚本](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/run_gap_gate_mutations.py) 复用原内部源码表达式替换，只改实际 `margin_contacts` 内 gap 构造为 `w-delta`、`w`、`w+delta` 或 `2*w-delta`；对两个完整 gate 分别直接调用。
- [变异断言日志](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/gap_gate_mutations.log) 逐格记录 8 条目标红 `exact margin-gap midpoint`，而非导入失败、其它粗距离断言或后处理输出失败。
- 补强后重跑 `python -X utf8 tools/check_exact_construction.py`：`exact construction AST gate: 0 violation(s)`。

本项没有改 `src/eab/margin.py` 或其它生产代码，没有缩网格、删断言、skip 或 xfail；仅去掉过时注释并补充独立普通中点反例。最终冻结全套由 root 重跑，本定向记录不代替独立 G6。
