# R7FIX 主代理：G6G-07 与跨模块同类扫描

## G6G-07

- 新门：`tests/test_r7fix_dual.py`。审查原 876 个“最终 primal 与 derivative 都非零且可表示”的指数格完整保留；另有最小复现与内部变异看护。独立真值只用 Fraction 与二的整数幂，不使用 Dual 算术。
- 修前：`red.log` 为 **28 failed, 850 passed in 0.69s**。其中 876 格有 27 格失败（原审查 13 个静默错 + 14 个响亮拒绝），最小复现另失败一次。
- 核心断言：`result.e == (expected, -expected, 0.0)`；实际 `(-0.0, 0.0, -0.0)`，期望首通道 `-4.666318092516094e-301`。
- 根因：`_ordinary` 限输入指数不等于限制 `v**(p-1)` 的派生指数。系数先下溢/溢出，后乘种子无法恢复。
- 修法：整数幂导数全程 Fraction；非整数导数用保留独立指数的 Decimal（80 位）直到乘完种子，再调用检查型最终转换。不再让任何幂导数走仅按输入范围判断的快路。非整数是浮点构造，不声称超越运算的有理精确性。
- 修后：连同原 Dual 与 R6 的 LP/导数门，`green.log` **1022 passed in 0.82s**。
- 变异：在生产 `Dual.__pow__` 内恢复 input-only 快路，不动输出。`run_mutation.py power` → `mutant_power.log` **1 failed in 0.10s**，红在上述非零导数断言；元数据见 `mutations.json`。
- 同类核查：乘法/除法/atan2 的 `_ordinary` 快路仅含有限次数的乘除，输入指数盒给出中间指数界，且消差回退 Fraction；没有幂的“派生指数任意倍增”漏洞。未改变这些路径。

## 同类新增：冻结法向与导数最后归一化前舍入

- 文件：`src/eab/kernel3d/frozen.py::_unit_jet`。
- 原值路径先 `float(c/scale)` 再除 norm；原导数路径也用已舍入的 norm 作分母，跨次正规中点时会改变最终一 ulp 的选择。
- 新门 `tests/test_r7fix_frozen.py`：独立精确平方与相邻中点比较。值构造 `(1,1,2.49q)` 的第三单位分量应为 `2q`，原返回 `q`；导数构造真值略低于 `1.5q`，原返回 `2q`，应为 `q`。
- 修前 `frozen_red.log` **5 failed in 0.15s**；修后 `frozen_green2.log` **18 passed in 0.12s**（含 R6 冻结构造门）。`frozen_lowdim` 在一次较早联跑中 14 门均绿；最终以全套为准。
- 修法：值和切向导数各自形成精确的 `c² / ||n||²`，最终一次开根、再保号；不先构造浮点 norm 或分量。
- 内部变异：`run_mutation.py frozen_value` → **4 failed in 0.08s**；`frozen_derivative` → **1 failed in 0.07s**。分别红在 `final normalized component was rounded twice` 与 `rounded norm changed derivative midpoint decision`。

### 原测试改写台账（本组一条；全单完整台账见主报告）

`tests/test_r6fix_frozen_construction.py::test_frozen_unit_jet_divides_before_rounding_an_overflowing_tangent_component` 原参考值先把 `sqrt(3)` 舍入，再作 Fraction 除法，实际固化了这轮消除的双舍入；修复后相差一 ulp。保留原输入、三通道、符号、网格，用原始输入精确平方 `seed²*k²/27` 严格落在返回浮点两侧舍入中点平方之间的断言取代旧等式。该判据唯一指定正确舍入浮点，没有加容差，没有删门，没有缩网格；不是放松失败。

## 同类新增：3D G0 非有限误差绕过

- 文档代理的只读独立扫描确认 `g03.g0_distance_completeness3` 与 G6G-03 同类：枚举器内部删除真实全部盖，有限 `atol=1e308` 的阈值先溢出，`inf > inf` 为假，门报绿；NaN/inf tolerance 也被接受。
- 新门 `tests/test_r7fix_g03.py` 在修前 **4 failed in 0.25s**（`g03_red.log`）。既有正常全盖控制组必须绿，然后在被测枚举内部把 `out.append(c)` 改 `pass`，要求门拒绝。
- 修法：入口拒绝非有限/负 atol；缺失或非有限候选、真值、误差独立拒绝；有限验收式用 Fraction 形成，不把有限大系数先乘成 infinity。
- 修后 **4 passed in 0.12s**（`g03_green.log`）。几何尺度本身不可表示时由几何 API 响亮报错，不以无穷阈值放行。

- 交叉复核追加：候选列表中有限最小值可藏住另一条 NaN 见证。生产枚举内部把真实第二候选点构造为 NaN，`g03_mixed_red.log` 在 `finite minimum must not hide an invalid constructed witness` 真红；修复为对**全部** cand 的有限性审计。新 G03 五格在最终集成中全部绿，不只核 got。

## 操作记录

一次修改脚本的文本锚未匹配，分类为输入/编辑脚本错误；没有写入源文件，随后用 ASCII 锚及 `newline=''` 完成，后续绿日志替代那次未成功的修后试跑。全部命令使用 `PYTHONDONTWRITEBYTECODE=1` 与 `python -X utf8`。变异均在独立 Python 进程的生产函数命名空间内执行，不更换工作树文件、不污染其他代理正在运行的测试。
