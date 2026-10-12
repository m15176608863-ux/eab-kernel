# G6J-J04 修复与同类扫描

## 改动与回滚

仅修改 `src/eab/dual.py`，新增 `tests/test_r10_dual_construction.py`；未改 construction.py、旧测试、fixtures、姊妹树。修前锚点由父任务保存于 `baseline/`；没有 git 写操作。逐字节核对：baseline dual.py 为 LF（301 行），现文件仍为 LF（342 行）；新文件 UTF-8/LF。

## 修前红 → 修后绿

- 主门先写测试、后修改源代码。[初次红日志](file:///D:/eab-wt/cx-e2/reports/codex/R10FIX_evidence/J04_red.log)：`26 failed, 6 passed, 3 deselected in 0.23s`，其中16个 sqrt 舍入格、4个 sqrt 范围格、4个 trig 下溢格、2个 pow primal 下溢格。
- v=nextafter(1,+inf), seed=3u, u=2^-1074，修前导数 `1e-323`，正确值 `5e-324`。目标断言：`complete sqrt derivative final rounding`；正负 seed 及尺度 2^600 均报红。
- 根因：先把 sqrt(v) 舍入成1，再算 (0.5/s)*seed，造成可表达次正规导数错舍。修法：精确构造 `seed²/(4v)`，统一 `sqrt_rational` 最终舍入后施符号；导数不再使用已舍入 primal。范围外响亮 ArithmeticError / OverflowError，不回0/inf。零 primal 的导数继续明确 ZeroDivisionError。
- Oracle：主门直接用 Fraction 邻浮点中点的平方比较，不调用生产开根或几何原语；另加六格完整 cell 检查（一般位置、精确tie、最小次正规、巨大primal），使用独立 construction_oracle。

## 同类扫描与修复

| 对象 | 发现及处理 | 门 |
|---|---|---|
| sin / cos | 非零 coefficient*seed 可静默下溢0；改为 Fraction(libm coefficient)*Fraction(seed)，送统一标量构造，正负都覆盖 | `test_r10_trigonometric_nonzero_derivative_cannot_underflow_silently` |
| 整数 pow 导数 | 已走 Fraction 完整导数，无新故障；保留历史门 | R6 / R7 全格 |
| 半整数 pow 导数 | 新确认 Decimal80 把精确4.5u扰成5u：v=2^-716, p=1.5, seed=0x1.8p-715。改为完整导数平方 `(p*seed)²*v^(2p-2)` 有理构造后开根；五组输入正负共10格 | `test_r10_half_integer_power_derivative_keeps_exact_subnormal_ties` |
| 其他非整数 pow | 保持既有80位 Decimal 系数近似；去除与seed相乘时第二次Decimal截断：Fraction(p)*Fraction(c)*Fraction(seed) 最后统一构造；不声称一般超越正确舍入 | 源码明确契约 |
| pow primal | 新确认 v=2^-600, p=2或2.5, zero seed 返回primal=0；现在非零输入的零结果 FloatingPointError，非有限结果 OverflowError | `test_r10_power_primal_underflow_without_an_exact_channel_fails_loudly` |
| atan2 导数 | 新确认ordinary快径可差1ULP。angular=True不走该快径，完整有理比值最后构造；一般非对称输入和2^±100共3格 | `test_r10_atan2_derivative_uses_one_final_rational_rounding` |
| frozen.py | 原始Fraction jet / 完整normalized construction没有复用舍入primal根，本轮未改 | 既有R6 / R8门由主套复核 |

[追加红日志](file:///D:/eab-wt/cx-e2/reports/codex/R10FIX_evidence/J04_scan_red.log)：`13 failed, 35 deselected in 0.17s`；10个 half-power tie 格、3个 atan2 格均在目标断言报红。

## 源内变异的牙

[变异脚本](file:///D:/eab-wt/cx-e2/reports/codex/R10FIX_evidence/J04_mutation_runner.py)、[日志](file:///D:/eab-wt/cx-e2/reports/codex/R10FIX_evidence/J04_mutations.log)。只在内存编译真实函数源，自动恢复，无工作文件变异残留；六项均另有持久pytest门。

1. sqrt 恢复 `(0.5/s)*a`：`complete sqrt derivative final rounding` 红。
2. sin 撤统一标量构造：对应范围门 `DID NOT RAISE` 红。
3. cos 撤统一标量构造：对应范围门 `DID NOT RAISE` 红。
4. pow 撤半整数分支落回Decimal80：`half-integer derivative exact tie must round to even` 红（-716格）。
5. atan2 恢复ordinary快径：`atan2 derivative exact rational final rounding` 红。
6. pow 撤primal范围检查：p=2下溢门 `DID NOT RAISE` 红。

## 验证与测试台账

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -X utf8 -m pytest -q tests/test_r10_dual_construction.py tests/test_dual.py tests/test_r6fix_dual_lp.py tests/test_r7fix_dual.py tests/test_r9fix_mechanics_construction.py --basetemp reports/codex/R10FIX_evidence/tmp/j04_green_final
```

[绿日志](file:///D:/eab-wt/cx-e2/reports/codex/R10FIX_evidence/J04_green.log)最后一行：`1099 passed in 0.66s`，含R7全部876格，无缩网格、skip、xfail。新文件57格。

旧测试改写：无。新测试最初用float(Fraction)输出独立oracle值；按增强静态门改用独立construction_oracle.scalar_exact，未改生产边界或弱化期望。

残余边界：sin/cos primal及系数仍为libm近似；一般非整数且非半整数power系数仍为80位Decimal近似，不宣称严格正确舍入。这些不用于几何分支判定。基本加减乘除既有快径保留，不将其冒充初等函数严格最终舍入。全仓全套及独立G6退出由父任务统一执行。
