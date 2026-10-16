# A2 / A3 独立局部复核

范围：`tests/test_m5d_replay_semantics.py` 与 `docs/m5d_replay_teeth_theory.md`。本复核不是六路 G6 退出审查。

## 结论

本范围 **0 critical、0 major、0 minor**。当前字节版重新独立执行最后一行为 `10 passed in 0.68s`，10 收集 = 10 执行，0 skip。
另外逐个直接调用 6 个真函数体变异，均观察到预期具名 AssertionError；没有调用源码哈希或冻结摘要断言。
文件 SHA256、具体替换、实际红断言与独立重算有理值记录在 `review_replay_semantics.json`。

## 集成后真实重验

原绑定因 `_prepared` 的静态友好重构和理论补充而失效；本次已重新阅读实际代码与理论，不仅更新哈希。
输入适配改为逐顶点调用 `motion.coordinate_polynomials` 后，另以独立有理旋转和线性平移闭式，在 3 个顶点×3 个时刻×2 个运动族上共核对 18 个点—时刻产物，全部一致。
10 个 pytest 节点已重新执行，6 个真实内部变异也在当前源码上重新编译、逐一观察实际具名 AssertionError。
新增理论中的两个括区端点、P1/P2 半径阈值及平均半径均独立精确重算吻合：
`519929/1048576`、`528385/1048576`、`8198071/1048576000`、`4097/524288`、`16392071/2097152000`。
测试和理论的当前源码 SHA256 在重验首尾一致；没有修改生产、tests 或 tools。

## 数学及路径核验

1. **R1 只查 P1。** 独立有理转动公式复算中点为 `(16030/1601,1/3202)`；加允许的 1/100 横向位移后严格进入 B 矩形。P1 全管 x≤10.01，B 左边 10.02；名义 P2 顶点半径平方≤401/4，仍严格在矩形左侧。连续扰动 `4rs(1−s)` 的端点为零，且全程不超过 r。测试确实穿过 R1 证书分支而非双盒直判；变异仅去掉 P2 循环项，最终红在 `R1 both-path tube gate`。
2. **R2 温和缩短早期窗。** 以局部变量 τ 直接复算 `x=-47+296τ-600τ²+400τ³`、`y=-11+20τ`，在 τ=17/40 上方顶点为 `(33/32,-2)`，先碰 B 下边。此前全部 A 顶点严格在 y<-2；该首事件早于被提名的后续左边碰撞。两种 width 分别把它压进最后 1% 和最后 0.1% 的早期窗。内部改成 `hi=.99*lo` / `.999*lo` 后最终红在 `R2 mild early-window shortening`，不是构造预检查。
3. **R2 双路径与完整半径接线。** 独立 floor 算术复算回放 20 位括区；确有 `P2_margin < r < P1_margin` 且 `.99r < P2_margin`。允许的 P2 左移使首时刻 `(1+r)/2` 超出最大括区。`all→any`、只查 P1、只收 99% 半径三个内部变异均错误签发，最后红在 `R2 replay single-cover wiring`。

第 3 项仅反证证书的首时刻括区，并不反证该平移族的首标签不变。测试 docstring 已明确区分，没有用这条反例夸大标签改变。

## 独立性与复跑

数学 oracle 只用 Fraction 恒等式、矩形内部不等式、半径平方及整数 floor；`comb` 仅做输入多项式重参数化。生产路径适配器和证书 import 是被测对象，不被用于期望答案的几何计算。变异使用已有测试 instrumentation 编译实际源码函数体，不在返回产物之后追加数据。

```powershell
$env:TEMP = Join-Path $PWD 'reports/codex/M5d_evidence/tmp'
$env:TMP = $env:TEMP
python -m pytest -q -p no:cacheprovider --basetemp=reports/codex/M5d_evidence/tmp/review_replay_fresh tests/test_m5d_replay_semantics.py
```
