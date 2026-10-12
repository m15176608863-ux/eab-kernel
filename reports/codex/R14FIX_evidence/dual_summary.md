# R14FIX：Dual 分项修复证据

## 范围与验证

- 修复 `G6N-N01`、`G6N-N02`，并扫描同模块的幂底数、非整数指数和角度输出边界。
- 修前新增门：`dual_red.log`，原样末行 `33 failed, 12 passed, 2 deselected in 0.21s`。
- 修后定向包含旧 Dual、R6/R7/R10/R13 门及新门：`dual_green.log`，原样末行 `1216 passed in 1.03s`。
- 旧参数网格没有删减；R7 的全部 876 格保持。
- 本报告不声称全仓退出；全仓套件与文档总账由主代理汇总。

## N01：精确整数指数的奇偶性

根因：`p = float(p)` 在精确整数分支之前舍去大整数最低位。修前 `Dual(-1,(1,)) ** (2**54+1)` 的 primal 为 `+1` 而非 `-1`；导数符号也反向。

修法：`exact_input` 先保留完整 Fraction，按精确分母分派；分母为 1 时直接完整有理数幂和导数，分母为 2 时保持完整半整数平方根表达式，最后构造 binary64。大整数和半整数不再经过有损转换。

门：`test_r14_integer_power_keeps_exact_parity`，覆盖 int/Fraction、正负大奇数及 `2**400+1`。主断言 `exact odd exponent must retain negative primal`；另独立断言完整导数符号。半整数门保留巨大 Fraction 指数的精确系数。

变异：在真实 `Dual.__pow__` 中将精确解析恢复为 `Fraction(float(p))`；上述 primal 目标断言变红，具体 traceback 见 `dual_mutations.log`。没有在产出后伪造数据。

## N02：sin/cos/atan2 先检查精确参数

根因：libm 隐式将 int/Fraction 转成 float，宏观相位误差或 tiny/tiny 的两个参数同时归零。

分项支持域：

1. `sin/cos` 的角度、`atan2` 的两个坐标分量，以及一般非整数幂的指数和底数，必须**可无损表示为有限 binary64**。这不是 D400；包括所有有限 binary64 次正规数。
2. 判断发生在转换前：有理数约分后分母须为 2 的幂；去除分子尾部二进制零后有效位数不超过 53；最低有效位指数不小于 -1074，最高有效位指数不大于 1023。通过后才允许 `float(q)`。
3. 中央实现是 `numeric_domain.binary64_argument`；`dual._lossless_libm_input` 仅为薄包装及内部变异接缝。
4. 超越函数仍声明 libm 近似系数模型，不宣称全域正确舍入；禁止的变化是**调用 libm 之前擅自改变用户给定的精确参数**。
5. 整数/半整数的代数分支不受该 libm 参数界约束。其余代数 jet 和精确谓词也没有被 D400 限制。

新门同时覆盖 sin/cos、标量/Dual、`2**54+1`、`2**54+1/3`、`2**-1075`、`2**-2000`；atan2 增加 Fraction(1,3) 和全部同量级 tiny/tiny 格。所有支持域外格要求具名 `ConstructionDomainError`，没有用容差放过错误输出。

变异：在实际调用链内将薄包装改为裸 `float(value)`，参数拒绝断言 `DID NOT RAISE` 变红；同一缺陷在一般幂指数路径也被独立抓住。

## 同类扫描新增修复

### 一般非整数幂底数

即使指数保真，原来 `self.v ** p` 仍会提前丢失 Fraction 底数。因此在进入一般非整数 libm 分支前，底数也执行同样的无损检查；整数与半整数的精确代数底数域保持不变。

### atan2 的非零结果不能静默下溢

标量及 Dual 的 `atan2(minsubnormal,2)` 在本机 libm 返回 minsubnormal。独立数学界却给出 `0 < atan(u/2) < u/2`，正确 RN 输出应为零，而此项目要求非零不可表达时响亮拒绝。

因此不仅检查 libm 是否返回零，还在调用前精确检查正 x 的 `2*abs(y) <= x*u`。再对 libm 的非零角输出零加防线。回归门 `test_r14_atan2_nonzero_output_underflow_is_named`；去掉前置精确 RN-zero 单元检查，标量格拒绝断言变红。sin/cos 同样增加不允许非零理论值静默归零的输出检查。

### 巨大幂资源界

为防止 `2 ** (2**54+1)` 等路径尝试分配天文大小的精确整数，非 0/±1 底数增加具名资源支持域：物化的 numerator+denominator 位数保守估计乘幂次数不得超过 `2**20`。这是资源边界，不是几何容差或奇偶近似；超过时 `ConstructionDomainError`。0/±1 底数豁免，仍支持 `2**400+1` 等准确奇偶与可表达导数。最终输出自身的下溢/溢出检查照旧。

## 测试改写台账

| 文件/门 | 改写 | 不弱于原门的原因 |
|---|---|---|
| `tests/test_r6fix_dual_lp.py::test_r6fix07_atan2_matches_independent_fraction_derivative` | 原 y=1e-300,x=1e300 格断言 primal 等于 libm 的 0；现改为公开入口具名拒绝，并继续直接核完整有理导数与原独立 Fraction 真值 | 全部输入格保留；不再接受无声零；原导数信息断言保留 |
| `tests/test_r7fix_dual.py::test_g6g07_input_only_fast_path_mutation_is_caught` | 将原有损系数快路变异从一般幂输出检查前移至新的真实整数幂分支内部 | 同一非零导数吞零缺陷、同一回归输入、同一句 `nonzero derivative must not become signed zero` 断言；避免变异绕开被测路径 |

## 证据及回滚边界

- `dual_red.log`：修前真实生产代码红。
- `dual_green.log`：定向所有旧门和新门绿。
- `dual_mutations.py`：可重跑的内存编译生产源码变异脚本；`dual_mutations.log` 保存每个具体目标失败。
- 变异结束核 `src/eab/dual.py` 字节 SHA256 不变，脚本从未写生产代码；修改本身保留在未提交工作树。
- 所有 Python 执行使用 `PYTHONDONTWRITEBYTECODE=1 python -X utf8`，pytest 禁用 cacheprovider，basetemp 在本树证据目录。
