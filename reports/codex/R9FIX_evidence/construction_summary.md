# R9FIX 构造子任务报告：G6I-03 / G6I-04

## 1. 范围、当前状态与证据边界

本子任务修复两个构造发现，建立生产与独立参考两组统一精确构造接口，迁移指派的 oracle/helper，并完成定向验证。仅写当前工作树，未写姊妹仓库，未执行 Git 写操作。

主代理负责全仓调用迁移、AST 静态门、完整测试、文档同步和最终交付；本报告不把定向绿灯宣称为独立 G6 或 M0 退出。

生产与参考构造实现不共用：生产使用整数平方根与精确中点；独立参考使用 binary64 位模式二分与 Fraction 中点。参考实现放在 `src/eab/oracle_construction.py`，仅为源 G0 oracle 与 tests 共用独立参考组，不供被测内核构造使用。`tests/construction_oracle.py` 提供测试侧入口。

**公共法锥当前边界**：公共 API 已由其他代理统一到声明的三角化实体；只有明确命名的私有 source 路径保留源环 descriptor。此前本子任务曾补写局部 descriptor 说明，随后已由更强的公共实体实现取代，不能再把公共法锥描述为 descriptor 豁免。

## 2. G6I-03：最近点先舍入，丢失可表达的次正规锥裕度

### 根因与修前红

`cone_intersection_margin` 原先将精确最近点 `p` 先传给 `_float_vector`，再求 norm。对 `p=(-d/3,-d/3,-d/3)`，各分量可能先舍零或舍成错误组合，而最终范数仍是可表达的非零次正规数。

新增 `test_g6i03_cone_margin_rounds_exact_norm_not_nearest_point` 保留审查方 24 个 multiplier。独立 oracle 证明 `p` 是三个极点的平均、每个极点与 `p` 的点积均等于 `|p|²`，即完整投影 KKT 证书；预期 binary64 再由 Fraction 中点平方确定，不用浮点平方开方。

修前 24 格中 10 格失败。m=1 的目标断言为 `G6I-03 exact cone margin`，实际 `0.0`，预期 `5e-324`；m=2 实际 `1e-323`，预期 `5e-324`。记录见 [修前日志](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/construction_red.log)。

### 修法、修后绿与变异

直接对精确 `p` 调用 `norm_rational`：先精确平方求和，再对最终标量一次正确舍入。输出真正越界时响亮失败，不静默清零。

24 格修后全部绿。变异编译进入真实函数体，把关键 return 恢复为 `norm(_float_vector(p))`；m=1 在目标断言确实报红，输出 `assert 0.0 == 5e-324`，不是在枚举后伪造记录。见 [定向绿灯及变异日志](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/construction_green.log)。

## 3. G6I-04：独立距离 oracle 先舍入平方

### 根因与修前红

`e5b_margin_oracle.check_exact_margin` 的两处 `sqrt(float(d2))` 在 `s=2^-600` 时把非零平方舍零；另一侧也可能平方溢出而最终根仍可表达。`test_near_parallel_edges.exact_seg_seg` 的显示出口存在相同缺陷。

新增尺度网格 `{-600,-540,-500,0,600}`：-600/-540 在 `default-exact distance construction` 失败，600 在平方转浮点时溢出；近平行线段的 `1e-200` 间隙显示为零。正式修前合计：

```text
14 failed, 16 passed in 0.70s
```

大尺度输入使用 x 半宽 s、y/z 半宽 `min(s,1)` 的长盒，独立区间真距离仍为 `2s`。这样避免全等大盒的真实面积本身超出 binary64，把测试隔离到“平方越界、最终距离可表达”。首次新测试曾误用全等大盒，先在真实面积越界处失败；修正该新增输入后重新取得上面的正式修前红日志，不涉及任何历史门放松。

### 修法、修后绿与变异

e5b helper 不再构造 expected root，而是直接对返回距离检查上下相邻 binary64 中点的 Fraction 平方证书，含 ties-to-even。原四 ULP 构造断言加强为唯一正确舍入值；全部标签、窗口、closed 状态及相邻 delta 探针保留。相邻探针使用已通过证书的返回值，不与被测实现共用 root 构造。

`exact_seg_seg` 仅将最终显示出口改为独立 `sqrt_exact`；有理候选枚举及 `squared=True` 出口不变。

五个尺度和微小线段间隙修后全部绿。分别 AST 改写真实 `body_distance` 与 `margin_contacts` 内的开方调用，恢复平方先舍入；保留精确 d2、标签与自校验。前者在 `default-exact distance construction` 报红，后者在 `default-exact cover distance` 报红。两次均穿过真实内部构造路径。

## 4. 结构性构造边界与逐值证书

生产组接口：`scalar_rational`、`ratio_rational`、`vector_rational`、`sqrt_rational`、`norm_rational`、`unit_rational`。参考组提供对应六个 `*_exact`，不 import 生产构造或几何原语。

生产 sqrt 不再借助 `sqrt(float(...))` 找候选：精确确定二进制指数，在最终 ULP 单位下算 `isqrt(floor(n/d))`，用 `4n` 与 `d(2k+1)^2` 比较中点，奇偶判断 ties-to-even；最后 `ldexp` 的 significand 是精确可表达的整数。次正规、普通尺度和最大有限值的上溢中点走同一构造路径。

`test_r9fix_construction_rounding.py` 包括：

- 48 个标量/根位置：中点上下、恰好中点、最小次正规、正规与次正规交界、`2^±600`、最大有限值及上溢中点。
- 对生产与参考 scalar、ratio、sqrt 的每个有限返回值，独立核验 Fraction 舍入单元。
- 24 个非完全平方的次正规例子。
- 8 组 norm/unit 向量，含未单位化范数溢出但单位分量仍可表达的输入。
- 非零下溢、真正上溢、负数开方与零向量单位化的显式错误政策。

参考 `scalar_exact` 对 finite binary64 输入采用 identity 快路径：输入本来就是可表达值，不需要二分；NaN/Inf 拒收，Fraction 仍走参考位模式二分。该快路径另有门。

额外确定性 5000 个有理平方逐值验证：4830 个 finite，其中 201 个在显式允许下舍零；170 个 overflow 均满足精确上溢界。见 [额外压力日志](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/construction_stress.log)。

## 5. 同类扫描与测试改写台账

| 文件或 helper | 改动 | 历史门保持情况 |
|---|---|---|
| `covers3` 最终点和参数显示 | 点显示走 `vector_rational`；有限参数走 `scalar_rational`；不得把显示点当作 norm/unit 的中间输入 | inf 常量不变；未删历史门 |
| `e5b_margin_oracle` | 两处四 ULP root 比较加强为 RN-even Fraction 中点证书 | 标签、状态、窗口、邻界探针不删 |
| `test_near_parallel_edges` | 最终 root 显示改独立 `sqrt_exact` | 精确候选、squared 出口及所有断言不变 |
| `test_frozen_ee_sign._ee_exact` | 对精确 direction 调用 `unit_exact` | 原网格和阈值保留 |
| `_line_parameters_and_gap` | 先精确求点积，再构造带符号的 `sqrt(numerator²/normal²)` | 不再先单位化和舍入差向量；原门保留 |
| `test_invariance_2d` 三个支撑/夹角 helper | 完整有理平方比一次最终开方 | 原参数、标签与阈值保留 |
| `test_invariance_geom._support_gap_oracle` | 精确有符号平方比，去掉先舍分量再 norm | 原误差界不放宽 |
| `test_geom3_e5a` 薄面法向 expected | 改 `unit_exact(n)` | 原 `rel=1e-15, abs=0` 保留 |
| `test_hull_robustness` | 主代理已改完整平方比 `sqrt_exact`，本代理复核后无需额外改动 | 原网格保留 |
| `test_interlock_e5a` reporting noise expected | 保留原 reporting noise 输入，把最终商合并成有理平方比开方 | 原 `2e-15` 阈值及内部变异保留 |

未增加 skip/xfail，未删除历史参数格或放松断言。全仓 AST 门和白名单的最终状态由主代理汇总，本报告不冒称全仓人工形式证明。

## 6. 追加同类门及牙

`test_r9fix_construction_helpers.py` 共 12 格：2D/3D 支撑在 `2^±600` 上的最终距离；EE signed line gap 在切向 `2^600`、法向 `2^-600` 下的精确相消；参考 scalar finite identity 路径。

两个 helper 内部变异也命中目标断言：

1. 真正的 support helper 恢复先舍投影，`triangle strict support margin` 报红。
2. 真正的 line-gap helper 恢复先舍单位向量再点积，错误值为 **+8192**，独立真间隙是微小负值；`line gap sign survives exact cancellation` 报红。

见 [追加 helper 门及变异](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/construction_helper_stress.log)。

## 7. 已运行的验证

| 验证 | 最后一行原样 | 日志 |
|---|---|---|
| 正式修前红 | `14 failed, 16 passed in 0.70s` | [red](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/construction_red.log) |
| 构造证书、定向回归和三次主变异 | `241 passed in 3.21s` | [green](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/construction_green.log) |
| R9/R6/near_parallel/e5a2_covers/kernel3d_covers/perf_covers 扩大回归 | `320 passed in 9.44s` | [wide](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/construction_wide.log) |
| 六个 helper 相关完整历史网格及 rounding | `3724 passed in 270.48s (0:04:30)` | [helper migration](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/construction_helper_migration.log) |
| 新同类门及两次 helper 变异 | `12 passed in 0.17s` | [helper stress](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/construction_helper_stress.log) |

完整 helper 网格命令（环境 `PYTHONDONTWRITEBYTECODE=1`）：

```text
python -X utf8 -m pytest tests/test_frozen_ee_sign.py tests/test_invariance_2d.py tests/test_invariance_geom.py tests/test_geom3_e5a.py tests/test_hull_robustness.py tests/test_interlock_e5a.py tests/test_r9fix_construction_rounding.py -q -p no:cacheprovider --basetemp=reports/codex/R9FIX_evidence/tmp/construction/helper_migration
```

一次扩大验证命令误写不存在的 `test_r7fix_construction.py`，属输入错误，无测试执行；查目录后修正并取得上述 320 绿，不把该失败计为通过。额外独立脚本首次未设 src 导入路径而失败，随后显式指定本树 src/tests，取得 5000 例证书结果。

本报告初次通过 PowerShell 管道写入时中文曾被替换为问号；现已仅重写本报告为真正 UTF-8 中文并回读核验。原日志采用 PowerShell UTF-16 输出，读取应使用 BOM/UTF-16，不应误按 UTF-8 解码；日志本体未改写。

## 8. 遗留与交接

本子任务未发现 G6I-03/04 的已知剩余缺陷。全套、最终静态门、canon 指针与最终文档必须由主代理在集成完成后验证；不能以本报告的定向绿灯代替独立复审。

## 主执行者收尾订正

最终参考构造增加仅候选的 float/Decimal 快路，每值必须过 Fraction RN-even 证书，不通过仍位二分；不改变与生产实现独立的边界。identity 仅接受原生 float。Cover3 的 EE/VE3/EV3 params 次正规以下可显示零但附 exact_params 证书，extent 仍精确。原严格参数说明已由此更完整契约取代。

[最终主报告](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_report.md)。
