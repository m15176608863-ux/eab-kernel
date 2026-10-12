# R6FIX 子任务报告：G6F-07 / 11 / 12 与同类冻结构造扫描

## 范围与验证锚点

- 修改：`src/eab/dual.py`、`src/eab/lp.py`、追加授权的 `src/eab/kernel3d/frozen.py`。
- 新门：`tests/test_r6fix_dual_lp.py`（114 格）、`tests/test_r6fix_frozen_construction.py`（13 格）。未改动任何既有测试。
- 只在本工作树写入；未执行任何 Git 写操作。基线来自主代理预存的 `../baseline_tracked.zip`，变异仅在独立 Python 进程内重编译/替换被测函数，不写回源码。
- 所有执行都设置 `PYTHONDONTWRITEBYTECODE=1`，以 `python -X utf8` 运行，pytest 使用 `-p no:cacheprovider` 和本树 `--basetemp`。

## G6F-07：Dual 除法与 atan2 的中间量量程丢失

### 修前红

新测试先在未修复的 `dual.py/lp.py` 上运行。`before.log` 最后一行：

```text
43 failed, 56 passed in 0.29s
```

其中直接商、反向商覆盖指数 `-1074,-1000,-665,-300,0,300,665,1000,1023`；两输入同时带导数的商覆盖邻浮点数消去和两端极端尺度；atan2 覆盖 `1e±200`、跨 600 个十进制指数和最小次正规数。原结果含 `inf`、`nan`、零导数和 `ZeroDivisionError`，而独立 Fraction 公式给有限非零值。

### 根因与修法

1. 商先算 `1/v`，继而算 `(a*v-u*b)*inv*inv`；atan2 先形成 `x*x+y*y`，即使最终结果可表达，中间乘积/平方也已溢出或下溢。
2. primal 商改为直接 `/`，不先构造倒数；导数共用 `_ratio_derivative`。普通、安全指数区且没有明显消去时保留浮点快路，否则按精确 2 的幂规整 primal 对，用有理算术算完导数后仅舍入一次。
3. `_ordinary` 的指数区间、消去检测仅选择快慢算术实现，不是几何谓词、容差带或零判据。不能表达的非零导数抛出异常，不返回 0/inf 冒充有限导数。
4. oracle 直接写原始 Fraction 闭式，不调用任何生产规整/导数辅助函数。

### 同类扫描与追加修复

- **反向除法**：同一平方/倒数序列，已与正向商统一处理。
- **乘法导数**：`a*v+u*b` 的两项各自溢出后相消为 nan；或两项各下溢但和是最小次正规数。极端/消去路径先有理求和；新增三格，修前均红。
- **整数负幂**：`p*v**(p-1)` 系数先溢出，乘 seed 后的导数却有限；极端输入使用精确整数幂和有理导数，最终一次舍入。
- **分数负幂**：例如 `v=2^-1000, seed=v, p=-0.5`，正确导数为 `-2^499`，旧系数先溢出；反向尺度系数先下溢。仅极端路径用 80 位十进制、独立指数表示保留系数直至乘 seed；普通路径保持原式。新增四格修前 `4 failed, 110 deselected in 0.09s`。这些是实数构造，不参与精确分支判定；半整数/2 的幂门有独立有理参考。
- `sqrt/sin/cos` 导数系数没有上述两个巨大乘积相消或平方分母机制；LP 的浮点估计仍只是候选，精确证书路径未改。
- 零跳过只对导数表达式的两个源通道均为精确零时返回零；未通过 primal 为零而跳过导数。冻结门明确包含 `Dual(0, (scale,))`。

追加的乘法/整数幂修前日志 `scan_before.log`：

```text
5 failed, 99 deselected in 0.10s
```

### 真实内部变异

`run_mutations.py` 从基线 zip 取原函数体，换入当前模块后运行当前看护测试，非输出后追加假数据。

| 变异 | 真正红的看护位置/原因 | 日志 |
|---|---|---|
| 恢复旧 `__truediv__` | `assert direct.e == (1,-1,0)`：得到 `(inf,-inf,0)`，primal 仍为 1 | `mutation_07_div.log` |
| 恢复旧 atan2 | `assert got.e == (float(q),)`：得到 `-0.0`，参考 `-5e-201` | `mutation_07_atan2.log` |
| 恢复旧 `__mul__` | `assert r.e == (expected,)`：两个无限中间项相消，非精确零结果 | `mutation_07_mul.log` |
| 恢复旧 `__pow__` | 合法有限导数构造处抛 OverflowError，未能抵达有理参考相等断言 | `mutation_07_pow.log` |

每个独立进程均退出 1、末行为 `1 failed ...`；常驻 pytest 内还保留一项真实旧商的 mutation-catching 门。

## G6F-11：零次幂

- 根因：先求 `0**-1`，后乘指数 0，常数函数的边界分支缺失。
- 修复：拒绝 Dual 指数之后，`p == 0` 直接返回值 1、原通道宽度的全零导数。覆盖正负零、正负底数、`1e±300`、宽度 0/1/3、整型/浮点正负零指数；仍保留负底非整数幂等所有旧错误门。
- 修前：`before.log` 中零底的 18 格均因 ZeroDivisionError 红；非零底基准格仍绿。
- 修后：全部通过。
- 变异：从当前 `__pow__` 内删掉 `p == 0` 分支；`test_r6fix11_zero_power_is_constant_one_with_same_width` 在合法 `Dual(0,()) ** 0` 计算处重现 ZeroDivisionError。这里红的是**合法边界必须有返回值**的看护，不是无关顶点/顺序断言。`mutation_11.log` 为 `1 failed in 0.07s`，常驻对应 mutation-catching 门通过。

## G6F-12：空约束 LP 的精确最优见证

- 根因：`solve` 的 `m == 0` optimal 返回分支没有填写见证字段；普通精确认证路径已经填写，`maximize` 已正确转接。
- 修复：该 optimal 分支补 `exact_x=(Fraction(0),)*n`、`exact_y=()`；不改状态、目标或迭代算法。
- 修前：`before.log` 中 8 格空约束路径在 `assert r.exact_x is not None, "optimal result must carry exact_x"` 红。
- 扫描：枚举 `LPResult(...)` 和 `OPTIMAL` 返回位置，只有这个出口缺字段；`_Exact.certify` 和 `maximize` 保留现状。
- 新门对 min/max、普通候选/强制精确兜底、零变量、零约束、冗余行、非整数精确解全部核验：字段类型/维数、原始非负可行、对偶可行、精确强对偶等式。并非只检查字段不为 None。
- 变异：在被测 `solve` 函数内部恢复 `exact_x=None, exact_y=None`，第一格恰在上述见证断言红；`mutation_12.log` 为 `1 failed in 0.06s`。常驻 mutation-catching 门通过。

## 追加授权：冻结解析路径同类构造量扫描

`frozen_before.log`：`9 failed, 3 passed in 0.18s`；追加 `_unit_jet` 案例的 `frozen_unit_before.log`：`1 failed, 12 deselected in 0.09s`。

确认并修复：

1. VV3 单位向量、VE3/EV3 点线投影先形成浮点平方范数，`2^±600` 时溢出/下溢。现在像已有 VF/EE jet 一样先从原数据提取独立有理 primal 和所有导数通道；相对向量与投影/投影导数全部有理计算，末端交给 `_unit_jet`。精确投影不再需要两遍浮点 Gram–Schmidt。
2. `A + x - B` 先进行全局浮点平移，`T=1e8, s=1e-9` 的 Fraction 微特征在等价浮点零平移下丢失；现在先有理化再做仿射量。VV/VE/EV 的位置与 `frozen_gap` 共用 `_affine_point_jets`，没有回读舍入后的全局点。
3. gap 的相对向量/点积中间溢出导致 nan，改为有理完整仿射点积后一次转换；所有 six cover kinds 的参考顶点规则不变。
4. `_unit_jet` 的切向导数归一项可以先超过 binary64 上限，再除以 `[1,sqrt(3)]` 内的归一长度回到有限范围。现在保留该有理项直到除完长度再舍入，例子从 OverflowError 改为有限正确导数。

验证：现有 `test_frozen_exact_jets.py`、`test_frozen_lowdim.py`、`test_frozen_surface_diagonal.py`、`test_frozen_ee_sign.py`、`test_covers3_strict_lowdim.py` 全保留。新门的 oracle 是 1:2:2 向量和轴线投影的闭式，以及手写正交投影导数，不复用生产几何原语。全通道保留门包含零 primal、非零 derivative。

新增两项内部真实变异：基线 frozen gap 在当前单位法向输入上恢复 `nan != 0.5291502622129182`；基线 `_unit_jet` 在正确最终导数有限时恢复中间 float 转换 OverflowError。分别见 `mutation_frozen_gap.log`、`mutation_frozen_unit.log`，均 `1 failed`。

跨文件扫描线索已交接：`kernel2d/geom.py` 的 `point_on_segment` 分母平方和 centroid 面积构造由 g0 代理负责；本子任务不越过其文件所有权。

## 测试改写台账

- **既有测试：零改写、零删除、零缩网格、零 skip/xfail。**
- 自己新建的“不可表达导数应报错”一格初写 seed=1，使导数为可表达的 `1e300`，属于测试输入错误；更正 seed 为 `1e300`，导数才是 `1e600`，不是放宽生产门。
- 自己新建的 frozen dot-product 扫描格最初用大模长给定法向；随后加强为单位长度法向和原坐标相减超量程的输入，当前基线变异仍在目标相等断言红。

## 运行结果与命令

1. G6F 主门及 LP 相关旧门：

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -X utf8 -m pytest -q -p no:cacheprovider tests/test_r6fix_dual_lp.py tests/test_dual.py tests/test_lp.py tests/test_lp_scale.py tests/test_lp_fail_loud.py tests/test_lp_certificates.py tests/test_interlock_sensitivity.py --basetemp reports/codex/R6FIX_evidence/tmp/dual_lp
```

当时末行：`581 passed in 64.43s (0:01:04)`，见 `after.log`。随后仅 Dual/frozen 同类补强，LP 没再编辑。

2. 冻结与对偶最终相关门：

```powershell
python -X utf8 -m pytest -q -p no:cacheprovider tests/test_r6fix_frozen_construction.py tests/test_frozen_exact_jets.py tests/test_frozen_lowdim.py tests/test_frozen_surface_diagonal.py tests/test_frozen_ee_sign.py tests/test_covers3_strict_lowdim.py tests/test_r6fix_dual_lp.py tests/test_dual.py tests/test_interlock_sensitivity.py --basetemp reports/codex/R6FIX_evidence/tmp/dual_lp
```

最终末行原样：

```text
388 passed in 113.99s (0:01:53)
```

见 `frozen_final.log`。此时其他代理相关运行并行，不能拿该子集耗时代替整仓耗时。

3. 变异复跑：`python -X utf8 reports/codex/R6FIX_evidence/dual_lp/run_mutations.py`；结果 `mutations.json` 的 8 项全部 `exit_code=1`、末行含 `1 failed`，runner 自身成功退出 0。
4. `git diff --check -- src/eab/dual.py src/eab/lp.py src/eab/kernel3d/frozen.py` 无输出，成功退出。

## 交接与边界

- 本子任务源码/测试已冻结，交主代理运行全套与 `tools/fix_canon_ptrs.py --apply`、文档同步。
- 本报告没有声称通过新的独立 G6 审查或替代全仓验收；不运行/不改姊妹仓库。
- G6F-07/11/12 与本子任务确认的同类问题无已知未修条目；最终全仓结果以总报告为准。
