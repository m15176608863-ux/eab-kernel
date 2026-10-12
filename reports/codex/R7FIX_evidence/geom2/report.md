# R7FIX 二维分报告（G6G-01 / 02 / 03）

## 范围与回滚

仅修改本工作树 `src/eab/kernel2d/{g0_oracle,g0,geom,covers}.py`，新增 `tests/test_r7fix_geom2.py`。
回滚锚点为主执行器冻结的 `reports/codex/R7FIX_evidence/baseline_tracked.zip`。不修改姊妹仓库，不执行 Git 写操作。
文件编辑使用 `newline=''`；`g0_oracle.py` 原为混合换行，依据 ZIP 用 unchanged-line 字节映射恢复原行终止符。

## 修前真实红

命令：

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -X utf8 -m pytest -q -p no:cacheprovider tests/test_r7fix_geom2.py --basetemp=reports/codex/R7FIX_evidence/tmp/geom2_red
```

原版源码上实跑：`11 failed, 1 passed in 0.17s`，完整断言在 `pre_fix_red.log`。这里包含 3 条发现及独立同类扫描的 unit/turn 门。

### G6G-01

- 修前：`assert brute_ray_exit(...) == Fraction(1,2)` 得到 `Fraction(2,1)`；在真正首次边界内部删除法锥候选，`assert not rep.passed` 红，旧门仍 `passed=True`。
- 根因：只检查射线事件间开区间，不检查事件本身；仅改成检查非内部重叠也不够，因为非凸紧配接缝可以在拓扑 `int E` 内。
- 修法：保留「拓扑 int E 的首出口」语义。精确事件和区间都检查；仅接触处用独立有理平移空间直线 arrangement 构造全部邻域开扇区见证，步长小于所有非过点直线的首次交叉距离，有外部扇区才是真正 ∂E。oracle 仅共用自己的 winding/inline rational primitives，零生产几何原语。
- 对照：L 反角首次为 `1/2`；U 形紧配通道中首次实体非重叠 `1/2` **不是**出口，真正首出口 `5/2`。再含 exact 3-4-5 旋转、共同平移 0/1e6、单位 2^-40/1/2^40 共 12 格。
- 变异：内存编译 `ray_exit`，去掉「事件本身检查」；同一 `==1/2` 断言红（实得 2），不是构造假输出。见 `mutation_G6G-01.log`。

### G6G-02

- 修前：minsubnormal 两分量给 normal `(1,1)`；有理 `(1.49q,.49q)` 给 gap=q，正确 2q；maxfinite 两分量未抛异常并返回 inf。
- 根因：先舍入相对向量，再用已经舍入的模长归一化；模长与方向需要独立构造。
- 修法：VV 保留 Fraction 差向量；`norm` 对精确平方最后开根；`unit` 各分量直接由精确 `v_i² / Σv²` 开根并保留符号；非零不可表达 gap 抛异常，非有限模长不再被拿来归一化。
- oracle：gap 使用独立有理平方中点不等式；方向使用独立 Decimal 100 位根，不调用 construction helper。
- 变异：只在 `vv_cover` 内把精确差分量提前 `float`；有理格 `gap==2q` 红（实得 q）。见 `mutation_G6G-02.log`。

### G6G-03

- 修前：全有限巨大 L 形、可表达真距 k，内部删掉全部候选后 `samples=1, worst_abs_error=inf, passed=True`；出口门同类也复现。
- 根因：`L=inf` 变成无限验收阈值，`inf>inf` 为 false。
- 修法：验收保留 bbox 对角线平方，先移除精确 roundoff，再用有理平方比较 `err > atol*max(L,truth)+roundoff`，从不构造 L 或巨大阈值；缺盖、NaN/inf 距离/误差独立拒绝，非有限候选不能藏在有限 minimum 后。
- `char_length` 若作为公开浮点显示调用且不可表达则 fail loud；G0 本身不依赖这个显示。
- 配套：盖枚举先在精确距离窗判定、后构造。distance G0 用真距向上一个 ULP 的窗（包含精确真距），exit 用精确零窗；不构造与本门无关且超范围的远盖。此操作收紧「最近盖/接触盖必须存在」而非放宽门。
- 变异：在 `_construction_error_exceeds` 内复原浮点 L / inf 阈值算法；`not rep.passed` 红，实得无 failures 的 passed=True。见 `mutation_G6G-03.log`。

## 同类扫描与改动

- `geom.norm/unit`：根除平方/模长早舍入，直接 API 的 subnormal/maxfinite 门。
- `geom.vertex_turn`：差与叉积精确构造，最终非零面积不可表达时拒绝，不默认为平直。
- `geom.turn_angle`：精确叉积/点积，先同尺度缩放再 atan2，不让 2^-600 / 2^600 平方下溢/溢出。最终角不可表达时 fail loud。
- `covers._facet_normal_own`：FF 长边选择改成精确平方比较，不调用可能不可表达的浮点边长。
- `covers.enumerate_covers`：距离窗筛选移到构造前，避免被窗外不可表达特征阻塞。
- `g0`：距离、出口两条验收路径同时处理；NaN/inf 候选顺序均拒绝。
- 已审阅 `covers` 的 VE/EV/facet_gap、`entrance` 的 gap 与投影、`geom` 的面积/形心：已经是 Fraction 最终构造，不重复改写。
- 报告-only `angle_floor/turn_floor/entrance._floor` 的极端缩放组合仍由主执行器统一决策；它们不参与精确分支，未在本组追加泛化改造。

## 测试改写台账

原测试零删除、零修改、零跳过、零缩网格。仅新增 28 格。

修后定向结果：`28 passed in 0.13s`，见 `post_fix_green.log`。
变异统一可重跑：`python -X utf8 reports/codex/R7FIX_evidence/geom2/run_mutation.py G6G-01`（02/03 同），每条内部 pytest 必须 exit=1 才视为变异成功。

旧二维回归包括 test_kernel2d*.py、test_r6fix_g0.py、test_bb52_g1.py、test_invariance_2d.py、test_perf_2d_directions.py，结果另见 regression.log。
首轮 7 个 fixture ERROR 为 --basetemp 父目录缺失（WinError3），不是数值失败；创建限定的 evidence/tmp 后这 7 条重跑 `7 passed, 34 deselected in 0.19s`，见 fixture_rerun.log。

全套/文档指针重排由主执行器统一完成；本报告不声称 G6 退出。

## 最后补充：已确认的报告地板同类漏洞及性能

主执行器要求不遗留已确认同类后，追加两个修前红门（`floor_scan_red.log`）：
`angle_floor(q,q)` 在 q=2^-1074 时先下溢为 0，最终正确值却是 64 eps；`entrance._floor` 的 Amax+xmax=2max 先溢出为 inf，而最终缩放报告界是有限 5.109351192408882e294。

已修复：angle_floor 先做完整 Fraction 比值；turn_floor 直接由精确邻边平方与坐标量级比开根。entrance._floor 保留内部有理保守上界，先缩放后构造唯一根式并向上舍入，根的精确平方给证书；near_labels 的 band2 也保持 Fraction 加法，不把这个上界提前隐式转 float。对 -1074/0/1023 三种方向尺度验证上界证书，不参与精确判定。

另给 norm/unit 精确 tuple 层增加 maxsize=4096 有界缓存，outward_normal 复用同一 exact unit 路径；输入 list 被改后重建 Fraction key，新增门验证 [3,4]→[4,3]→[1,0] 不串用结果，不使用 ordinary/range 猜测快路。

新增测试最终共 34 格；新门+现有入口E3/局部盖E3为 `157 passed in 1.16s`（floor_green.log）。旧大组已到 91%，无 F；早先 7 E 仅 basetemp 父目录缺失且已单独7绿。按照主执行器要求主动中止旧大组，避免与正式全套争 CPU；不能把这次中止称为全套/完整回归通过。最终全套以主报告正式运行结果为准。

最终额外改动：`src/eab/kernel2d/entrance.py`，其原有 CRLF 逐行保留。此前本报告提到 reporting floor 留主执行器决策的残项现已消除。

## 最后全仓同类扫描补项：LimitContact / limit._norm

主执行器指出的 float 法向 `(3,3,7q)`（q=2^-1074）已确认：`LimitContact.__post_init__` 的 `v/m/n` 给第3分量 q，独立精确中点夹逼要求 2q。负号同样出错。
同文件 `_norm` 对有理 `(1.49q,.49q)` 返回 q 而不是最终可表达的 2q；有限 maxfinite 向量模长溢出时原实现返回 inf；极端法向非零分量还会静默成为 0。新增 `tests/test_r7fix_limit_construction.py`，修前 `5 failed in 0.12s`（limit_scan_red.log）。

仅修改 `src/eab/limit.py` 的两处构造路径：法向每分量由精确 `v_i²/Σv²` 最终 sqrt_rational 并恢复符号；报告模长从精确平方最终开根。有限输入的不可表达结果 fail loud；调用方明确传入的非有限报告数保留 math.hypot 的显示语义。未引入 kernel3d 几何依赖，未改 LP 约束、证书、求解、自校验或承载力判定，零旧门修改。

新增 7 门（原5门+2内部变异）`7 passed in 0.06s`。分别复原 constructor 内部 v/m/n 与 `_norm` 内部先缩放的旧算法，原目标中点等式均重新红；日志 limit_mutation_normal.log / limit_mutation_norm.log，统一脚本 run_limit_mutation.py。
选择性旧LP回归：test_limit.py、test_limit_contacts.py、test_limit_selfcheck.py、test_limit_exact_selfcheck.py、test_invariance_limit.py 加最初5新门，`753 passed in 38.40s`（limit_scan_green.log）。正式全套仍由主执行器统一重启、以其结果为准。

## 报告阅读说明（最终审计）

本分报告按执行阶段累积保留，不覆盖早先真实结果：主体“28格/四文件”是首次二维交付阶段；后续“34格”增加 entrance 报告地板和缓存键门；最后力学补项另增 limit.py 与7格。最终范围/旧测试改写六文件总台账/全套结果统一以主报告为准。轻量一致性审计见 final_report_audit.md。
