# R13FIXb 子任务：Dual / margin / limit / limit_multi

## 数字与边界

- R13FIX 原未确认项：21；本轮关闭 19；保留 2 个 API 缺口：`eab.dual.Dual.__pow__` 的一般非整数分支，以及 `eab.dual.convergence_order` 的一般对数收敛阶误差界。
- `coverage.json` 逐 API 记录 50 项，包括原已覆盖项、访问器以及本轮发现原分类过宽的自校验数值报告。
- 整数/半整数幂已有三档独立有理/平方根逐值门；**不能据此把整个 `__pow__` 标成完结**。一般非整数 primal 仍是 libm 幂，导数系数仍是 Decimal 80 位近似，没有充分证明误差界；一般指数转换与 Decimal 错误类型也未全面收口。
- `inflated_membership` 的公开返回仅有三个离散整数标签，按“无数值构造返回”处置；其内部仍调用数值见证自检，本记录**不证明**所有域外输入都能避开下游构造异常。
- legacy 容差/差分/收敛阶函数是明确的**诊断模型**，不是任意回调的解析导数或真实收敛阶保证。
- 主审订正：`convergence_order` 的 errors / valley 逐值对拍与幂二测试不能证明一般数学对数收敛阶误差界；把 libm 返回重命名为系数模型不足以满足所有者契约，因此整 API 降为 gap，保留已有修复和门，不把近似说成已认证。

## 生产实现位置与静态 scope 审查理由

### `src/eab/dual.py`

- `Dual.const` / `seed`：原 `float(v)` 可能静默清零；改集中 `scalar_rational` 范围边界。`lift` / `seeded` 由此获得同样检查。
- `Dual._pair`：原先把标量 int / Fraction 先转 float，普通量级 `(-1)+(1+2^-54)` 错为零；保留精确标量直至完整表达式。
- `__add__` / `__sub__` / `__mul__` / `__truediv__` / `__rtruediv__`：完整有理 primal 末端舍入；不会把域外非零 primal 静默显示为零。
- `_product_derivative` / `_ratio_derivative`：移除会早舍入的浮点二乘积路径，统一完成有理导数表达式。独立 oracle 为 raw Fraction 多项式与测试自己的 binary64 舍入单元参考。
- `_derivative_float`：集中范围错误转换为带 `Dual derivative` 量名的 `ConstructionDomainError`。
- `__pow__`：整数 primal 用有理幂，半整数 primal 用精确平方根；统一既有 primal 下溢/上溢异常类型。**一般非整数分支仍保留上述缺口**；没有用文档掩盖近似。
- `val` / `is_exact_zero` / 比较方法：移除判据入口的 float 强转，任意小 Fraction 不再错判零或平局。这些返回访问值或布尔结果，不新增数值近似。
- `central_difference`：输入 theta / h 集中检查非零 `[2^-400,2^400]`；对实际回调采样值构造完整有理差商；非有限回调结果明确量名。
- `convergence_order`：逐 h 误差有理相减；两个有限误差之比可能超过 binary64，改为超长比值的整数对数之差。log 仍是所声明的 libm 诊断系数模型。

### `src/eab/margin.py`

- `cover_witness`：先把原始点转有理向量再相减；不把显示点混合算术的早舍入当成原始几何。
- `rounding_floor` / `effective_geom_tol` / `boundary_band` / `contact_resolution`：对文档指定的已报告长度/度量值构造完整有理表达式，仅末端舍入；不改变默认精确判据。
- 完整有理构造保留原全域能力，只在必须报告的非零有限 binary64 量不可表示时响亮失败，不加 ±400 人工截断。
- `_witnesses`：公共裸 `cover_witness` 仍对不可表示的非零距离抛专门异常；私有成员判定通道不能因此丢失全域精确判定。仅在独立有理平方距离 `0 < d² <= 2^-2150`（binary64 RN-zero 胞的精确平方边界）时恢复私有零显示，并保留原盖及后续 `exact_distance_squared` 证书。这是显式证书展示例外，不是无证据零距离，更不是放宽接触判定。旧 `test_closed_is_exact_when_the_display_gap_underflows_to_zero` 原断言未改且复测通过。

### `src/eab/limit.py` / `limit_multi.py`

- `LimitContact.__post_init__`：对 int / Fraction 不再让 `math.isfinite` 隐式 float 强转溢出；float 仍明确检查有限性，法向归一化仍走完整有理构造。
- `contacts_from_covers` / multi 适配器代码原已正确；本轮补每个返回字段、a/b/mid 三分支及域外 midpoint 专门异常门。
- 两模块补支持域正本引用；`limit_multi.py` 没有算法变更。

## 域内真错与新门

1. 混合 Fraction / float 的 Dual 标量在 `_pair` 早舍入，普通尺度可把非零差值抹成零。
2. Dual 两乘积导数与商导数的普通浮点快捷路径并不保证完整表达式的正确舍入；本轮用内核内替换确认错误由导数逐值断言捕获。
3. `contact_resolution` 的早乘法舍入：两盒尺度比 1132，普通尺度原值 `0x1.0022a70772d6cp-26`，完整模型正确值 `0x1.0022a70772d6dp-26`，相差 1 ulp。门在低/普/高三档均绑定完整表达式。
4. `convergence_order` 即使 theta / h 均普通，有限误差 `2^800` 与 `2^-800` 的中间比值也会上溢；新门给独立真实对数比 1600。
5. `val` / `is_exact_zero` 对 `Fraction(2)^-2000` 的零判和比较曾因 float 转换失真；现保持给定精确值。

## 旧门契约迁移（不是删格或放宽）

`tests/test_r6fix_dual_lp.py` 保留全部参数：

- `test_r6fix07_quotient_with_two_active_inputs_matches_fraction[1e-300-1e+300-1e+300-1e+300]`
- `test_r6fix07_related_product_derivative_avoids_intermediate_range_loss[2.409919865102884e-181-2.409919865102884e-181-1.0250665447337477e-143-1.0250665447337477e-143]`

两格原先只关心可表示导数而隐含允许非零 primal 显示成零。新所有者契约禁止这种返回，所以用独立 Fraction 判定精确 primal 落入 RN-zero 胞时，公共操作必须抛 `ConstructionDomainError`；**旧导数逐值断言继续直接执行内部导数核**。其他输入的原断言不变，无 skip / xfail。

`tests/test_r10_dual_construction.py` 两个变异 harness 随实现迁移：

- atan2 旧快捷分支已消失，注入改为在有理化位置恢复 float；原“atan2 derivative exact rational final rounding”断言保持。
- 整数幂新增第二道正确范围边界，恢复旧 silent-zero 缺陷时必须同时移除旧 if 与新 scalar 边界；原“不再抛异常”的断言保持。

`tests/test_r7fix_dual.py` 原早浮点幂变异插入点移到新的 `try/except` 之后，避免把注入插在 `try` 体外造成语法错误；仍在 `__pow__` 内恢复同一个旧快捷路径，原 `nonzero derivative must not become signed zero` 数值断言不变。

## 变异表

全部注入到被测函数内部，不篡改输出后的假数据。

| 类别 | 注入 | 必须红的断言 |
|---|---|---|
| Dual 导数 | `_product_derivative` 恢复浮点二乘积 | `Dual derivative exact expression` |
| 数值差商 | 回调值先转 float 再相减 | `sample callback exact quotient` |
| 距离见证 | 点坐标先转 float 再相减 | `witness cancellation retained` |
| 适配器点 | midpoint 恢复 raw 混合相加 | `adapter cancellation retained` |
| 容差报告 | diag 项先乘浮点系数再与 floor 合成 | `resolution final complete expression` |
| 输入域 | 移除 `central_difference.theta` 的集中检查 | 原域外断言 `DID NOT RAISE` |

低/普/高参数化另有 `test_scale_grid_produces_distinct_constructed_outputs`，禁止用相同产物假称尺度覆盖。

## 验证

- 初轮：Dual / R6 / R13 mechanics / R13 frozen margin / 新门：`314 passed in 0.62s`。
- 新门 + R10 + R6：`250 passed in 0.32s`。
- 四处回归修复后小门：旧 margin RN-zero 谓词门 + R7 + R10 + 新门：`1015 passed in 0.79s`。
- 第一次完整相关组合的 4 个失败和全量日志保留 `focused_initial_failures.log` / `focused_initial_run.json`，未覆盖销毁。两个 R10 failure 属于运行进程已加载旧 harness 的陈旧执行；R7 注入语法和私有 margin 证书显示问题如上修复。
- 最终完整相关旧门组合：`2456 passed in 89.79s (0:01:29)`。
- 完整相关旧门组合执行、耗时与原样最后一行写 `focused_run.json` / `focused_pytest.log`；这只是子任务相关组合，不代替 root 的全套四分片门。

## 全套发现的次正规内部阈值回归与修复

首轮全套在原封不动的 `test_escape_reporting_does_not_construct_an_unrepresentable_intermediate_face_area[subnormal]` 发现真实回归：严格构造 `REL_GEOM_TOL * characteristic_length` 的非零 binary64 显示会下溢，即使最终逃逸高度仍可表达。只延后这个 base 不够，下一层 `rounding_floor` 也同样过小。

这里 gtol / r 是 nominal 候选与并列**分支窗口**，不是必须公开显示的量，也不是精确 escape root 的判据。恢复 `allow_underflow=True` 输出零会改变窗口，所以没有采用。

最小修复：

- `margin._rounding_floor_exact` / `_effective_geom_tol_exact` 返回完整 Fraction 内部窗口；公共 `rounding_floor` / `effective_geom_tol` 仍对完整最终量严格调用集中构造边界。max 先比较再构造，避免被较大可表达操作数遮住的小操作数先触发下溢。`boundary_band` 同型修正。
- `kernel3d/interlock.py` 两个公开 escape 入口和 `_candidates_uncached` 使用私有精确窗口。候选高度比较和 `_escape_solution` 的并列不等式两侧都完成 Fraction 表达式，防止 Fraction 与 float 混算重新清零。
- `_candidates` 缓存 implementation identity 纳入新的 `_rounding_floor_exact` 实际 callable。`_effective_geom_tol_exact` 的实际返回值与类型进入既有 extent_tol 内容键。
- 原 escape root、最终高度构造和旧测试不改。新涉及的 interlock 源码修改前备份为 `before/interlock.py`。
- 新门直接 spy 实际 `_candidates` 路径收到的 gtol / r：在几何尺度 `2^-1070` 下都是严格非零 Fraction；独立轴盒根 `47*s/4` 正确且可表示。调用公共裸诊断仍必须以量名抛 `ConstructionDomainError`，没有悄悄返回零。
- 两个新变异在私有 helper **内部**恢复 `float` 早舍入；精确根仍正确，但分别命中 `internal gtol must not round to zero` / `internal rounding floor must not round to zero`，没有借其他脆断言报红。
- 初步回归：原三尺度 escape 门 + 新门 + 候选契约与缓存：`199 passed in 8.10s`。另一路独立只读复核旧 event 全文件 / 缓存 / margin exact 得到 142 绿，并独立核验四档有理阈值与暖缓存变异。
- 扩大相关组合因 root 已启动最终 11998 节点四分片而按要求终止，状态 **`TERMINATED_FOR_FINAL_FULL_SUITE`**，不记绿。仅中断受控 exec session 46684；随后按完整唯一命令行精确查询确认其子进程已不存在，没有枚举或终止其他 Python 进程。记录为 `threshold_repair_terminated.json`。
- 扩大组合 stdout 在子进程完成前由父进程缓冲，终止时没有已发布输出；其 monotonic 起点未预先落盘，因此精确耗时不可恢复。基于源冻结文件时间的保守上界为 481.906 秒，不冒称 pytest 实测时间。最终验收以 root 的 verified 四分片为准。

R13FIXb_PARTIAL：Dual.__pow__ 一般非整数分支误差界及完整专门异常审查；convergence_order 一般数学对数收敛阶误差界
