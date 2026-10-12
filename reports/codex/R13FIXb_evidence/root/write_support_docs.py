"""Write the reviewed support contract without normalising existing newlines."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]

CONTRACT = r"""
<a id="r13fixb-numeric-domain"></a>
## R13FIXb：数值支持域契约（2026-10-13，所有者决定）

**判定不缩域；构造分层声明支持域。** 本节取代旧文把所有构造都一概要求全尺度正确的口径；
它是当前合同，不把尚未闭合的实现冒充合同已全部实现。逐项状态见
[138 项清单](r13fix_construction_inventory.md) 和 [R13FIXb 报告](../reports/codex/R13FIXb_report.md)。

### 1. 判定与三类构造

- 成员、相交、凸性、法锥、运动事件分支：在各 API 既有几何有效性与定义域前提下，对任意有限 binary64 / int / Fraction 的给定值精确。
  不把 `check_input` 装到这些分支或 Polyhedron 的数据容器上。数据精确不等于数据背后理想几何精确。
- **有理数输出/仅选择、搬运输入**：保留任意有限有理数域，不必装 ±400 限幅器。
- **最终一次舍入的代数构造**：保留更大的全有限输入域。中间 Fraction 可超出 binary64；只有最终输出
  需要 RN-even 有限，且精确非零值不得悄悄落到 0。标量、根、范数、单位分量、混合 raw 向量、reader 数值转换
  走 `eab.construction` 的最终边界；越界统一抛 `eab.numeric_domain.ConstructionDomainError`，信息含量名。
  `scalar_rational(..., quantity=...)` 可带调用方量名；异常继承 OverflowError，兼容既有 ArithmeticError 捕获。
- **近似构造/诊断模型**：基础工程输入域 `D400 = {0} ∪ {x: 2^-400 ≤ |x| ≤ 2^400}`，
  由 `numeric_domain.check_input/check_inputs` 用 Fraction 精确比较；每条路径还须声明输出/中间表达条件与误差模型。
  不是“输入过了盒子检查，所有算法就自动正确”。尚无全输入误差界或尚未接入检查的 API 必须留在缺口表。

门：`test_r13fixb_domain.py::test_engineering_input_envelope_is_exact`、
`test_outside_engineering_input_envelope_is_a_named_domain_error`、
`test_full_range_exact_constructions_are_not_artificially_narrowed`、
`test_predicates_keep_full_finite_int_fraction_domain`。

### 2. 为什么选 ±400，为什么不能只检坐标

非零输入的幅度约为 `[3.87e-121, 2.58e120]`，远宽于工程单位的通常范围。
两输入差的上界为 `2^401`；单个双线性项为 `2^800`（三维若干项相加仅增加常数个指数位），
在 binary64 指数上限 1024 以下有较大余量。但体积三次项可到 `2^1200`，而低端三次项可到 `2^-1200`；
因此 **±400 不能保证面积、体积、力矩、导数全部自动可表达**。即使坐标都在 D400，两 Fraction 可只差 `2^-2000`，
或除数可任意接近零；任何固定输入指数盒都不能排除相消、病态除法与非整数幂的困难。

所以支持域必须为“输入条件 **且** 对该 API 的最终量/声明中间量满足输出条件”，不是按坐标范围猜测成功。
代数路径直接算精确量并在最终边界验域，避免把可消去的中间上溢当域外。非代数路径要有另外的误差论证；
没有论证就列 PARTIAL，不用正好通过的三个尺度样本声称一般证明，也不用条件数膨胀阈值遮错。

默认非零输出范围用 **RN-even 舍入胞** 定义：正数须严格大于 `2^-1075`，并小于
`(max_binary64 + 2^1024)/2`；端点分别向 0 / infinity 舍入而拒绝，负数对称。
不是要求有理真值本身恰为一个浮点数。中间有理数没有 binary64 限制，内存/时间资源不作无界保证。

### 3. 明确误差模型与例外语义

- `Polyhedron.face_noise`：每条边长先构造 **53 位尾数、无限二进制指数** 的有理近似，再精确求和；
  Newell 模平方与最终根号内比值保留有理数（最终噪声通常是无理数）。令 `u=2^-53`，真实非退化面噪声为 R，正规输出误差
  `|Rhat-R| ≤ (2u+u²)|R|`；次正规输出可用同一界再加 `2^-1075`。推导：各正边长的相对误差 ≤u，
  正周长的相对误差仍 ≤u，精确比例不放大该相对误差，最终 RN 再贡献 ≤u；乘积界为 `(1+u)^2-1`。
  不承诺多根式之和正确舍入。门：`test_face_noise_non_axis_error_bound_is_independently_squared`；
  超长边回归：`test_face_noise_support_does_not_depend_on_intermediate_edge_range`。
- 既有 margin 容差报告的模型输入是已经构造的 L/C（不是理想几何精确 L）；完整有理报告表达式仅最终舍入。
  随机采样把 RNG 提供的 binary64 draw 视为给定系数，精确仿射后构造坐标；随机造型不是精确几何主 oracle。
- `interior_point` 的正确性是返回点确在内部，而不是返回唯一“标准点”。解析盒族另逐分量核参考候选的舍入界；
  一般凹体候选搜索并无本轮全覆盖声明。`first_entrance_brute` 的二分是佐证，不替代独立 exact event oracle。
- 一般非整数 `Dual.__pow__` 的 libm primal/Decimal80 导数系数、角度的通用 libm 误差证明仍按清单保留缺口。
  adapter 的三点 4ulp 门是平台测量，不是跨平台定理。不能用“系数模型”冒充理想超越函数已获正确舍入保证。
- 历史 `allow_underflow=True` 只用于带单独 exact 证书的显示字段，LP 的无界状态与 degenerate-face 的 infinity
  是已明确命名的状态/哨兵，不是可用来代替有限物理量的构造值。普通 Dual primal 非零下溢本轮改为专门异常；
  对应两格旧测试按新合同改测异常，原导数参考仍通过内部完整表达式核对。

### 4. 验收边界

每项记录低/普通/高三档逐值门或不产生构造量的具体证明；缺口数量以机读清单为准。
测试只证明所列输入族，源码数学论证才支持一般合同。静态门仍只是辅助检查；没有新增分析形态，
局部人工例外账随改动复核而非自动安全认证。本工作单禁止新 worktree，不宣称新鲜树或独立 G6 退出门通过。

"""

NOTICE = ("> **WO-R13FIXb 数值支持域（2026-10-13）**：判定继续对任意有限 binary64 / int / Fraction 精确；"
          "构造按声明域保证 RN-even 或所列误差界，超域须抛含量名的 `ConstructionDomainError`。"
          "基础近似输入域为非零 `[2^-400, 2^400]`，但仍需核输出范围；已有全域正确的代数构造不收窄。"
          "合同与推导见 [支持域定义](docs/exact_predicates_plan.md#r13fixb-numeric-domain)，"
          "实现未闭合项见 [138 项清单](docs/r13fix_construction_inventory.md) / "
          "[R13FIXb 报告](reports/codex/R13FIXb_report.md)；不能据此声称全 API 已满足该合同。\n\n")


def main():
    p = ROOT / "docs/exact_predicates_plan.md"
    with p.open(encoding="utf-8", newline="") as f:
        text = f.read()
    assert 'id="r13fixb-numeric-domain"' not in text
    end = text.index("\n") + 1
    text = text[:end] + CONTRACT + text[end:]
    with p.open("w", encoding="utf-8", newline="") as f:
        f.write(text)
    p = ROOT / "README.md"
    with p.open(encoding="utf-8", newline="") as f:
        text = f.read()
    assert "WO-R13FIXb 数值支持域" not in text
    end = text.index("\n") + 1
    with p.open("w", encoding="utf-8", newline="") as f:
        f.write(text[:end] + "\n" + NOTICE + text[end:])


if __name__ == "__main__":
    main()
