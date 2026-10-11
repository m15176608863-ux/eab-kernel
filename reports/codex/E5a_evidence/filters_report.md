# WO-E5a 精确过滤与二维提速子报告

## 改动

- `src/eab/predicates.py`：新增 `orient3d` / `orient3d_fraction`，正号统一为 `det[b-a,c-a,p-a] > 0`；新增 `cross2_sign` / `dot2_sign`。Fraction 输入是精确数据，不因浮点视图改变答案。
- `src/eab/kernel2d/covers.py`：VE/EV 的纯方向判据使用有界 LRU 缓存（32768 项）；默认严格符号用新过滤器，显式角/长度窗口仍用既有 Fraction 平方比较。VV 开锥符号使用过滤器；不改窗口/盖/构造语义。
- `tests/test_filtered_predicates.py`：新增 6 道门，7301 个方向分类样本（另有两类快路检查）和 4904 个双线性符号，包含随机、精确退化、近平面、工程坐标、次正规、中间上溢和任意 Fraction 派生输入。独立 oracle 以内联 Fraction 算术关于 a 展开；被测实现关于 p 展开，不共用几何原语。
- `tests/test_kernel2d_predicates.py`：只把独立支持线 oracle 中反复计算的 Fraction 坐标与点对差分前置；3000 个点集、全部有序点对/支持点和两条断言完全保留。详见 `filters_test_ledger.json`。
- LP 没有改动。既有 `lp._Exact.reduced_sign` 已有包含下溢放大的过滤界和精确证书，未为追求速度盲改证书逻辑。

## 过滤界（不是几何容差）

设 u=2^-53、eta=2^-1074。任何快路只有在 `abs(det) > bound` 时返回符号；不能证明时逐个退 Fraction，上溢/NaN 中间量不通过快路。

1. 纯 binary64 orient3d 使用现有 Shewchuk 形式 `(7+56u)u * permanent`，绝对项改成 `16 eta (1+|az|+|bz|+|cz|)`。浮点数差落入次正规区时仍是 eta 的整数倍，减法不产生不精确下溢；六个二次乘积的绝对误差会再乘 z，故必须把 z 的量级纳入，而不能只加与坐标无关的 `2^-1000`。后续乘加的绝对误差由常数项覆盖。
2. Fraction 输入转 float 的误差包含相对与绝对项。令差分的 M 为两端浮点绝对值之和，转换加差分的误差由 `4u M + 4eta` 包住。六个三次单项式展开后，64u 倍 M-permanent 给出保守相对界（含界自身的求值误差），`128 eta (1+sa+sb+sc+sa*sb+sa*sc+sb*sc)` 计入微小输入误差被两项大坐标放大。保守性使近平面时常退精确路径，但不会放过不确定符号。
3. 二维双线性符号：两次有理数转换乘积再加减的误差小于 8u 的乘积 permanent；实现用 16u 并加 `8 eta (1+sum|operand|)`，含界求值舍入与下溢。

## 实测

- 强对拍：`6 passed in 0.61s`（`filters_comparison.xml`）。
- 二维与过滤广回归：`1717 passed in 233.05s (0:03:53)`（全部 `test_kernel2d*.py`、`test_invariance_2d.py`、`test_bb52_g1.py`、`test_filtered_predicates.py`，`filters_2d_regression.xml`）。该进程已加载旧支持线 oracle，故其机械提速另以上述定向门验证。
- 另做 30000 个逐项过滤版/纯 Fraction 版性能对拍，零差：20000 个一般浮点 0.516641 s → 0.0362733 s，14.243 倍；5000 个近平面 0.1320704 s → 0.1365367 s，0.967 倍，4924 次回退；5000 个一般 Fraction 0.1351900 s → 0.1020899 s，1.324 倍。该微基准不是整套速度承诺，详见 `filters_benchmark.json`。
- bb52 指定慢门同机器独立进程配对：`test_g0_distance_completeness_has_teeth[no_VV_covers]` 原版 `1 passed in 19.31s`，改后该格 JUnit 10.204 s；改后连同 30 道 covers E3 门为 `31 passed in 10.58s`。前/后 XML 分别为 `filters_bb52_before.xml`、`filters_bb52_after.xml`。
- 支持线 oracle 机械提速后 `1 passed in 9.61s`（`filters_hull_oracle_after.xml`）；上一单整套中同门25.187 s仅作历史参照，不冒充本次配对基准。

## 突变 F01

用实际生产 `predicates.py` 的隔离副本，把 orient3d 的相对过滤常数除以10。测试使用固定真实四面体，纯 Fraction 答 +1，而缩水过滤界放行错误的 -1；定向门在 `assert pred.orient3d(...) == 1` 处得到 `assert -1 == 1`。原样末行为 `1 failed in 0.20s`。

突变在生产函数内部，不是往输出追加假数据；只改副本，运行前后在线源码 SHA256 相同。可复跑 `PYTHONDONTWRITEBYTECODE=1 python -X utf8 reports/codex/E5a_evidence/run_filter_mutation.py`。机读 `filters_mutation.json`，失败全文 `filters_mutation.log` / `filters_mutation.xml`。第一次隔离运行曾因 pytest 的 Windows 反斜杠 pythonpath 被解析失败而未收集到测试；已改用 POSIX 路径，那个收集错误不计作杀死突变。

## 边界

- 缓存只缓存精确输入的纯函数结果，不缓存浮点不确定性；生产输入变动会改变 key。源码突变/纯 Fraction 对拍必须使用新进程或主动清空缓存，不能借旧缓存冒充变异执行。
- 尚未以本子任务单独声称整套 ≤600 s，也不声称 G6 独立退出。整套实测与三维调用方整合由总报告给出。
