# R7FIX 同组外只读复核：dual / frozen / g03

审阅范围：当前工作树 diff 的 `src/eab/dual.py`、`src/eab/kernel3d/frozen.py`、`src/eab/kernel3d/g03.py`，以及 `test_r7fix_dual.py`、`test_r7fix_frozen.py`、`test_r7fix_g03.py` 与唯一旧门改写 `test_r6fix_frozen_construction.py`。

- **Dual 幂**：整数指数的导数完整保留 Fraction 系数和种子乘积；非整数通过 Decimal 宽指数直到种子乘积后构造。删除仅检查输入范围的 unsafe 快路符合 G6G-07 根因。876 格网格保留，且显式最小复现加多通道正/负/零种子；内部源码恢复快路变异守的是“非零导数不能成为带符号零”的目标断言。
- **Frozen normal jet**：新公式对 n_i / sqrt(n·n) 与 `(dn_i − n_i(n·dn)/(n·n)) / sqrt(n·n)` 分别先完整平方比，最后 sqrt_rational，再恢复方向符号。解析值与导数均保留原数据，未使用显示点反差分。
- **旧 frozen 门改写**：原期望用 `Fraction(math.sqrt(3))`（先舍入√3）为分母，不是精确解析导数的正确舍入；该参考值会和本次要修的二次舍入互相认同。替换后的符号断言 + 严格邻浮点中点平方夹逼 `lo² < seed²*k²/27 < hi²` 在本输入无 tie 时唯一指定正确 nearest float，不带容差、不放宽，是更强的正确性门。
- **3D G0**：显式拒绝无穷验收参数、非有限 got/truth/error 并用 Fraction 阈值符合本轮同类要求。复核时额外提醒：必须检查 `cand` 全体非有限值，而不仅检查 min；有限首元素可以让后续 NaN 被 min 隐藏。主执行器已新增 `test_g03_a_finite_minimum_cannot_hide_a_nonfinite_candidate` 处理此条，最终绿以主执行器全套为准。

本复核是对本次差分和门逻辑的定向检查，不替代六路 G6，不声称穷尽所有数值输入。
