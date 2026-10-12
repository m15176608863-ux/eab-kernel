# WO-R13FIX：事件字段绑定与构造量差分分报告

## 结论与范围

- G6M-02 已补牙：三维原 24 个随机输入一格未删，加入独立 earliest-time 与每个返回坐标的 Fraction midpoint RN-even 证书。
- 同类扫描发现二维迁移随机门也有相同脱钩；原 30 格一格未删，同样补齐。另给二维凹路径、三维凹路径、出口与逃逸字段加入显式绑定。
- 仅修改 `tests/test_entrance3.py`、`tests/test_kernel2d_entrance.py`；新增 `tests/r13_event_oracle.py` 与 `tests/test_r13fix_event_bindings.py`。本分任务未改生产代码、未进行 Git 写操作，变异只在内存编译的真实函数体内。
- 三尺度测试是具体、可重跑的覆盖，不是对任意几何或任意 Python 的安全证明；名义候选和中心差分剖面的近似合同不偷换成全域精确合同。

## G6M-02：修前复现 → 修后目标断言红

|阶段|真实内部变异|结果|解释|
|---|---|---|---|
|修前当前三维原门|返回 `exact_x` 换成 `x0`|24 passed / 0 failed|确认复审现象；时间、法向、自校验不改，错位置仍绿|
|先增加独立绑定探针，尚未改原门|同上|`AssertionError: event position midpoint binding`|seed 0 实际原起点不在正确事件位置的 RN-even 舍入胞内|
|修后三维原 24 格|同上|1 passed / 23 failed|唯一绿格为 none 分支；全部 23 红因均为目标位置绑定断言|
|二维修前等价门（内存撤掉本轮新增 5 行）|凸路径 `vector_rational(exact_x)` 换成 `vector_rational(x0)`|30 passed / 0 failed|确认同类问题，不靠推测记账|
|修后二维原 30 格|同上|1 passed / 29 failed|全部 29 红因均为目标位置绑定断言|

seed 0 三维错误输出仍为 `(-3.017738778724177, 3.152165214937428, 2.3413999174549023)`；独立 SAT 给出相同正确精确时间 `1004139483583575262962424459322025043832044118908/302512545848554957045687895979560504994722154541`，返回位置必须逐分量满足该时刻对应的精确坐标舍入胞，而不是只在自己所在位置与另一谓词互相印证。

证据：[修前 24 格](file:///D:/eab-wt/cx-e2/reports/codex/R13FIX_evidence/events/pre_fix_existing_mutant.json)、[补断言前红探针](file:///D:/eab-wt/cx-e2/reports/codex/R13FIX_evidence/events/new_binding_red.log)、[完整变异矩阵与 traceback](file:///D:/eab-wt/cx-e2/reports/codex/R13FIX_evidence/events/mutation_matrix.json)、[可重跑矩阵脚本](file:///D:/eab-wt/cx-e2/reports/codex/R13FIX_evidence/events/run_mutation_matrix.py)。

## 根因、修法、迁移台账

|门|原断言保留|新增不变量|是否放松|
|---|---|---|---|
|三维随机凸首入 24 格|800-step 佐证、时间近似、gap、输入支持面、返回浮点位形状态对拍、精确接触边界、法向方向|`exact_t == independent_interval[0]`；`t` 及每个 `x[i]` 精确 midpoint 证书|否；纯增 4 行及说明|
|二维随机凸首入 30 格|800-step 佐证、原精确接触状态、返回位形状态对拍、gap、法向方向|独立 Fraction 边法向 temporal SAT；none 分支同步核独立区间；`t_exact/t/x` 绑定|否；纯增 5 行|
|凹首入/出口/逃逸|不改已有门|新增独立台阶首入时刻、返回字段及三尺度差分门|新增，无替换|

参考实现独立性：二维 oracle 只做 Fraction 边法向投影与射线区间相交；三维原独立整数 SAT 不调用生产原语。坐标证书使用独立 `oracle_construction.assert_sqrt_rounding` 的 Fraction midpoint 检查，将有符号标量先核符号、再核平方值；没有调用 `eab.construction`、生产几何、事件或投影 helper 来产生预期值。`e.x` 本身是直接被断言对象。

## 本轮新增内部变异牙

|变异位置|删除/替换步骤|必须红的性质|
|---|---|---|
|`first_entrance3` 正事件返回|`exact_x → x0`|`event position midpoint binding`|
|二维 `_first_entrance_convex`|`vector_rational(exact_x) → vector_rational(x0)`|`event position midpoint binding`|
|二维 `_first_entrance_concave`|返回 `vector_rational(x) → vector_rational(x0)`|`event position midpoint binding`|
|`escape_height_covers`|删除 `nextafter` 向上舍入|`escape outward display binding`；root=1/3|
|`escape_height_covers`|`exact_offset[2]` 删除 `+root`|`escape exact offset binding`|

五颗牙均位于 [新增测试](file:///D:/eab-wt/cx-e2/tests/test_r13fix_event_bindings.py)，不是返回结果后篡改假数据。

## 公开事件构造 API 覆盖矩阵

主文件：`tests/test_r13fix_event_bindings.py`。`S` 为 `{2^-1070, 1, 2^1018}`；`A` 为 `{2^-1070, 1, 2^508}`（第三格使面面积靠近上溢边缘，避免要求不可表达的整个大体面积）。

|公开 API|新增门（函数后缀）|直接核对字段|尺度与边界|
|---|---|---|---|
|`kernel2d.entrance.first_entrance`|`test_public_2d_event_fields_have_independent_extreme_scale_references`|t、t_exact、x、normal、gap、point_a/b|S；精确有理闭式；保留二维原随机格|
|`kernel2d.entrance.shortest_exit`|同上|x0、normal、负 gap、两个 witness|S；非对称初始位移|
|`kernel3d.entrance3.first_entrance3`|`test_public_3d_entrance_fields_have_independent_extreme_scale_references`|t、exact_t、x、normal、gap、point_a/b|S；各向异性保持所有面积可表达|
|二维/三维首入时间|`test_public_entrance_times_are_rounded_once_at_extreme_scales`|时间 t 与 x|S，root=s/3，不只测常数 t=3.5|
|二维/三维凹首入|`test_concave_2d_and_3d_returns_stay_bound_to_the_analytic_riser_event`|kind、t、exact_t、x|普通尺度；独立台阶闭式 root=2/5|
|`kernel3d.entrance3.shortest_exit3`|`test_public_3d_exit_fields_have_independent_extreme_scale_references`|x0、normal、负 gap、两个 witness|A；非对称起点|
|`interlock.escape_height_covers`|`test_public_escape_height_offset_and_frozen_lift_match_independent_extreme_roots`|exact_height、exact_offset、height 的最小向上 binary64 胞|S × {3/4,1/3}|
|`interlock.escape_height_brute`|同上|height 的独立最小向上胞|S × {3/4,1/3}；该兼容入口生产上委托精确解，不作为独立 oracle|
|`interlock.escape_height_from_frozen_cover`|同上|完整有理 root|S × {3/4,1/3}；VF 平面固定标签|
|`interlock.escape_candidates`|`test_nominal_candidates_and_profile_have_valuewise_extreme_scale_references`|每个名义候选高度|S；公开 normal-noise 规则可抑制大纵横比下的标签，未声称完整精确事件表|
|`interlock.dilatancy_profile`|同上|每行 h、中间 tan_psi、端点 None|S；仅平剖面的零导数；一般非零导数仍不是此门覆盖|
|逃逸完整均匀缩放|`test_escape_reporting_does_not_construct_an_unrepresentable_intermediate_face_area`|root、height、非空候选、每个候选高度|A；关联几何代理修复 diagnostic face_noise 的不必要中间面积下溢|

未声称本分任务覆盖：三维 first_entrance_brute 是抽样/二分佐证，非 correctly-rounded 主输出；二维 first_entrance_brute 的扫描/邻浮点合同；非零一般剪胀中心差分误差全域；所有凹非流形/复杂退化的每个输出组合。无数字输出的 `merge_degenerate` 是标签算法，不纳入浮点构造矩阵。

## 同类扫描与额外发现

1. 对 21 个入口/逃逸/互锁测试文件的 127 个 test 函数作直接字段断言普查，逐条候选清单见 [扫描 JSON](file:///D:/eab-wt/cx-e2/reports/codex/R13FIX_evidence/events/event_gate_scan.json)。清单只作为人工审查入口，不把 AST 命中数冒充完备性证明。手读二维/三维随机迁移门、exact、concave、wall、escape 和 candidates contract；确认二维随机门是同类遗漏并已补。
2. `escape_height_covers` 的原 exact 系列主要绑定 `exact_height`，不足以看护独立的浮点 `height` 和返回 `exact_offset`；新增两颗真实内部变异牙补上，不删原精确区间证书门。
3. 均匀次正规块的真实 probe 最初在 `face_noise → face_area` 因面积下溢失败，虽然最终逃逸高度可表达。交由几何代理修复中间构造后，新增全路径门已绿。原 probe 保存在 [探索日志](file:///D:/eab-wt/cx-e2/reports/codex/R13FIX_evidence/events/probe_extremes.log)，不把失败藏掉。
4. 均匀 2^1018 体的盖面积真实不可表达而响亮抛 OverflowError，属于范围拒绝，不当作数学错；三维入口的极大距离改用各向异性几何，使所有被返回面积仍可表达。

## 验证

- 原门 + 新差分门最终一组：`114 passed in 20.14s`，见 [定向绿日志](file:///D:/eab-wt/cx-e2/reports/codex/R13FIX_evidence/events/focused_final.log)。随后仅加了兼容 `escape_height_brute` 的同 oracle 核对；最终全套以总报告为准。
- M4a 三文件：`109 passed in 7.81s`，见 [M4a 日志](file:///D:/eab-wt/cx-e2/reports/codex/R13FIX_evidence/events/m4a_after.log)。
- 本分任务四个测试/oracle 文件静态检查均 `[]`，未刷新任何 policy，见 [静态日志](file:///D:/eab-wt/cx-e2/reports/codex/R13FIX_evidence/events/static_check_final.log)。
- 根代理新增 mechanics/frozen-margin 测试与 friction_generators 修法已交叉阅读：未发现 oracle 复用或非法表面输入；建议补 3D 摩擦生成元全分量门、把 frozen 变异范围失败归为目标断言，根代理已落实。此为交叉阅读，不冒充六路独立 G6。

## 可重跑

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -X utf8 -m pytest -q -p no:cacheprovider tests/test_r13fix_event_bindings.py tests/test_entrance3.py tests/test_kernel2d_entrance.py --basetemp=reports/codex/R13FIX_evidence/tmp/events_rerun
python -X utf8 reports/codex/R13FIX_evidence/events/run_mutation_matrix.py
python -X utf8 -m pytest -q -p no:cacheprovider tests/test_m4_bdda_shadow.py tests/test_m4_bdda_adapter.py tests/test_m4_bdda_vv_reader.py --basetemp=reports/codex/R13FIX_evidence/tmp/m4a_rerun
```

EVENTS_G6M02_FIXED_WITH_RUNTIME_TEETH
