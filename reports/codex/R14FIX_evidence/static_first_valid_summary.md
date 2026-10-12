# R14FIX 静态辅助门审阅

本节只报告 `tools/check_exact_construction.py` 的保守辅助检查，**零诊断不是 Python 数值证明，也不是 G6 退出证明**。未修改分析器、闭集语法或数据流算法；原有遗留例外未冒充全部经过新数值证明。

## 审阅方法

- 保留初始 policy 原件 `static_policy_before.json`。
- 所有新增/续 pin 必须在 `static_review.py` 显式列出 `(path, function)` 的复核依据；未知函数、找不到原 AST 节点、过期 scope 不自动批准。
- 每条例外仍绑定**具体 AST 节点 + 最小包围源码 SHA256**；没有给函数、目录或任意相同函数名一概放行。
- `static_review.json` 逐项保存具体源码表达式、规则、用途和边界；后续 `static_changes.json` 按初始/最终 policy 的唯一 ID 对账新增、移除与续 pin。
- 审阅时发现“用现有 R14 条数生成新 ID”在移除中间节点后可能重号，已改为 `max(existing id)+1`，显式修复三处 ID 并加唯一性断言；详见 `static_id_repair.json`。这只修证据标识，不放宽任何规则。

## 例外分类与理由

1. **输入域检查**：mu 的精确比较、lossless binary64 参数的整数位宽检查、具名异常调用；没有先 float 再按舍入后的数决定域。
2. **checked 输出/读取协议**：JSON parse 回调保留 Fraction 到 schema 分派；离散整数不截断；连续值单次 checked scalar；signed-zero 保留已有零的符号；嵌套证据树只在明确的 dict/list/tuple 分支分派。
3. **声明的近似系数模型**：libm 三角/一般幂、80 位 Decimal 幂系数；这些仍不是精确超越函数证明。最终 cone 方向按独立精确物理不等式认证，黏聚投影保留有理系数。
4. **运行时测试/独立 oracle**：完整有理表达式最终转换为 expected binary64，或者实际/参考输出差值作为误差断言；不是生产构造的中间舍入。
5. **测试夹具与内部变异**：tmp_path 中的文本/CSV、局部 SimpleNamespace 桩、AST 提取真实工具函数、定向 inspect/compile/exec 变异；不授权生产路径进行任意动态代码执行，不启动姊妹程序。
6. **不变的下游调用节点**：旧 limit/M4/不变性测试因被调路径增加显式域检查而变成保守分析的“不知”；具体调用节点逐项标记为被测路径/夹具构造，不能用共用模型的自洽门冒充独立圆锥 oracle。

## 完整复核范围与限制

原分析器仓库扫描固定为 `src/**/*.py` 与 `tests/**/*.py`；**不包含全部 `tools/` 实现**。本轮工具数值边界依靠独立运行时测试及代码审查，不能从静态门零诊断推出全工具已证明。

`static_verify.py` 使用原命令重新扫描，并对扫描前后所有 src/tests 与 policy/分析器文件做 SHA256 对比；即使扫描零诊断，过程中有源码变更也判为非最终证据，不隐藏。在汇总前以 `static_final_status.json` 的 `exitcode == 0` 且 `source_policy_bytes_unchanged == true` 为最终有效条件。

最终计数、耗时、原样末行见 `static_final_status.json`；本说明不以中途扫描结果冒充最终成功。

## 最终有效结果

- 原样末行：`exact construction AST gate: 0 violation(s)`。
- 耗时：`87.8284064999898 s`；进程退出码：`0`；扫描前后源码/测试/policy/分析器 SHA256 全同。
- 初始 2674 条到最终 3029 条。按初始与最终活跃记录对账：新增 369、移除 14、原 pin 续审 42、新增 import 13；不是各次扫描累计条数。3029 个 ID 全部唯一，当前源码/AST pin 全部有效。
- 曾有一次零诊断扫描期间 `test_r14_domain` 发生变更，因此不作为最终证据；原始记录保留在 `static_interim_drift.log` / `static_interim_drift_status.json`。最终扫描是另一次无源码漂移的完整运行。
- `static_changes.json` / `static_review.json` 为 UTF-8 JSON；`static_pin_integrity.log` 记录 ID 唯一和全部 pin 当前有效。
