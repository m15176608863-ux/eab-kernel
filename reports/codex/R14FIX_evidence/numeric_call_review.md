# R14FIX 数值调用候选人工交叉复核

**角色边界：这是实施者的交叉检查，不是独立 G6，也不是全部公开 API 的数值证明。** 我同时实现了 Dual 和部分工具修复，不能把自己的复核称为独立审查。

## 清单与方法

- 起始清单有 247 个候选；实施期间主线刷新过索引，本次输出绑定 `numeric_call_review.json` 中记录的清单 SHA256，初版人工逐项覆盖 246 个调用位点；先完成 250 位点中间版；首次全仓失败修复后，再按最终冻结源码增量核对 **251 个最终调用位点（58 模块、571 个签名）**。246、250 版证据和 SHA 保留，未用最后数字覆盖历史。
- 每个位点都有文件、函数作用域、原调用文本、处置族和理由。原行号可能因修复移位，以作用域/源码片段及文件 SHA256 识别。
- 全部显式 float/初等函数/JSON 候选均按实际调用上下文核对，不把 `float(...)` 次数直接计作缺陷数。
- 同时检查了词法清单看不见的 CHILD 源码字符串和部分隐式混合算术。确实因此找到了 M4 字符串 gap、G4 角参数、工具 schema 身份字段和 showcase 荷载构造问题；分别实际复现后修复。

## 分族处置

| 族 | 数量 | 具体位置与判据 |
|---|---:|---|
| 显式 checked 边界 | 114 | `construction.scalar_rational` 的调用、`binary64_argument`、`check_mu`。边界有范围/输入认证；**不因此推断其传入表达式必然未提前舍入**。逐函数名单在 JSON |
| 非物理哨兵 | 48 | `covers._feature_in_gap_window`、`entrance.first_entrance`、`geom3.brute_feature_distance`、`lp._Exact.certify`、`limit_load`、`margin._resolve` 等 literal inf/nan；表示无候选、无界/不可行或报表状态，不是把用户数转换成它 |
| 已先检查的读取字段 | 35 | `readers.bdda_df.read_contacts_csv/read_df22_csv/read_verts_csv/load_records`：`_read_csv` 或 df18 明确字段循环先检查；`readers.tf_probe.read_pair_stage/load_records`：`_rows` 先检查。ID 列另走整数解析 |
| 有认证的最终转换 | 3 | `construction.scalar_rational`、`construction.sqrt_rational`（已限宽的整数 significand）、`numeric_domain.binary64_argument`（转换前检查） |
| 保守过滤后精确回退 | 2 | `kernel3d.exact_geom._iv` 为外包区间；`predicates._float_value` 仅供误差有界过滤，未获可靠符号则精确 Fraction 路径 |
| 独立 oracle 候选 | 2 | `oracle_construction._candidate_positive` 的 float/Decimal 只给候选；`_candidate_is_certified` 精确中点单元验收，否则 binary64 位模式二分 |
| 附精确见证的显示视图 | 1 | `limit._rational` 对 `_ExactFloat` 的 float() 仅核显示值与其见证相符，然后读取 exact，不拿显示值替代证书 |
| 无损超越参数 | 7 | `dual.sin/cos/atan2`、`kernel2d.geom.reflex_vertices`：进入 libm 前的 `binary64_argument` 检查；不是把 int/Fraction 裸转 binary64 |
| 精确同次缩放后的角构造 | 4 | `covers.cone_width`、`geom.turn_angle`、`geom3.angle_between`、`Polyhedron.dihedral_turn`：先精确 cross/dot/平方，再共同缩放；近 π/2 的不重要分量允许显示零，最终非零小角不可表达仍拒绝。这不是全域正确舍入的超越证明 |
| 有明确范围的 legacy 角模型 | 4 | `Bdda2DWindow.cone_tol`、`g4_multistep.analyze` 的 sin/radians；G4 本次补原 h1 文本 `check_input`，要求零或至少 2^-400，且 0≤h1<90 度 |
| 内部有限角网格 | 10 | `limit.friction_generators/_cohesion_directions`、`geom3._ray_directions`、`bb52_g0.g0_exit_directions` 及固定 H1；参数来自圆周网格/固定示例，不是有损巨大 caller 相位。摩擦生成元另有独立精确锥认证 |
| 展示内部角及模型 | 14 | `showcase.arch_problem`、`fig_entrance3.rot_xy`、`_rot`、固定 bb52 角。私有图库旋转只用于固定示例；公开 arch 的半径/密度/鞋带式面积和荷载本轮另行补域与完整表达式构造 |
| 精确 JSON 入口 | 1 | `numeric_decode.loads` 的 parse_float 保留精确值、parse_constant 拒绝非标准非有限词；**还必须按字段 schema 决定 integer/continuous**，本轮已抓住一刀切 decode_tree 丢身份的返修问题 |
| 非物理 policy/manifest JSON | 5 | `exact_construction_subset._read_policy`、`ingest_fixtures.upsert_provenance/main`、`m4_capture_family.verify_manifest/capture`；读取策略/溯源/捕获元数据，物理摘要由 checked 源文件重算 |
| phase/形参/坐标已分别守门的构造器 | 1 | `osteomorphic_block`：phase 无损检查；主代理已补 `_shape_parameters` 的 D400/正长度、`_shape_value` 的精确提升和 `_shape_coordinate` 的最终边界。generic 保留 Dual 通道，见末轮增量证据 |

## 真实漏点与修复台账

### 1. M4 字符串检测间隙 cs1

本树临时复制 `bb52_N3` 的 CSV，只把 step=1/contact=1 的 df18.cs1 改成 `1e-400`。读取器正确保留原始字符串，但 `m4_bdda_shadow.compare_step` 裸 float 将其变为零，并无异常返回 53 个已观察 VE metric。现实际消费处换为具名 checked scalar；没有让字符串 passthrough API 替下游虚构二进制表示。

### 2. G4 度参数下溢

同一真实夹具副本仅把第一步 h1 改为 `5e-324`。原 `analyze` 读得非零最小次正规数，`radians` 却静默给零。现在读取原文本处先检查与 M4 适配器同口径的角参数域，再转换。

两项先红证据：`cross_review_red.log` 的 `2 failed, 41 deselected in 1.34s`；闭合后包含完整旧 M4 文件门的 `cross_review_green.log` 为 `77 passed in 10.13s`。两项撤销内部检查均由原拒绝断言报 `DID NOT RAISE`。

### 3. 初次工具补修引入的 schema 身份回归

这是**本轮自己的补修回归，不是遗留代码发现**：给 G2/ingest 加 exact JSON 后，后接一刀切 `decode_tree` 仍会把 `step:18014398509481985.0` 这类数学整数 Fraction 舍成 float，丢 1。新 `tools/bdda3d_document.py` 共用 schema 明确区分：step、bi/bj、refs、owner、nsign、m0init/m0_0 精确整数；顶点、滑移及已知实数字段 checked continuous；未知 metadata 保持已有树模型，不发明其物理单位。G2 读入和 ingest 写出回读均有门，恢复旧 generic tree 即命中 `decimal step must remain exact integer`。

### 4. Showcase 演示模型

`arch_problem(rho=Fraction(2)**-2000)` 原来直接返回五块全零荷载；域内半径/密度组合还会让面积×密度吞零，普通尺度的裸鞋带式也不等于完整表达式一次舍入。现只对该演示模型声明 n∈[2,4096]、0<r_in<r_out、半径及非零密度在 D400、密度非负、μ 使用公共界；顶点 libm 模型构造后，鞋带式面积/形心/重力力矩在 Fraction 中完成，到 `wrench` 统一最后构造。不得把该演示域宣传为任意薄拱工程求解器认证。

schema + showcase 先红：`final_same_family_red.log` 为 `7 failed, 45 deselected in 0.29s`；含常驻变异的闭合日志 `final_same_family_green.log` 为 `56 passed in 1.64s`。真实测试只抽取 arch 函数 AST，不初始化绘图库、不运行整个 gallery。

### 5. 主代理已闭合：osteomorphic 的长度

`osteomorphic_block(nx=1,ny=1,lx=Fraction(2)**-2000)` 在 phase 已检查的代码中仍无异常返回八个 x=0 顶点。主代理现已完成：几何形参 D400/正长度检查，regular 采用完整 Fraction 坐标，generic 保留 Dual 通道；本文作者只读回源码及证据，没有修改该文件。`shape_green.log` 末行 `139 passed in 87.47s (0:01:27)`，`domain_final.log` 末行 `32 passed in 0.07s`；`domain_mutations.log` 中撤去 `_shape_value` 的 Fraction 提升，由 `test_shape_raw_exact_coordinate_cancellation_cannot_be_silently_zero` 的目标断言报红。

## 额外复核与证据

- 巨大整数幂额外实测：`Dual(-1,(Fraction(2)**-2000,)) ** (2**2000+1)` 得到 primal=-1、导数=1，最终可表达的结果没有因指数巨大而被提前 float 或全局拒绝；证据 `numeric_call_review_probes.json`。
- 非整数幂底数/指数、raw exact sin/cos/atan2 参数按现有无损域拒绝；整数及半整数保留独立代数分支；非平凡底数的精确物化资源界具名拒绝，0/±1 豁免。
- `final_same_family_mutations.py/.log` 保存 M4、G4、schema、showcase 密度、showcase 鞋带式共五条真实内部变异的原始失败栈和 `VERIFIED_RED`。未在产出之后追加伪造数据。
- 工具整数列：现有CSV已知ID/state列使用直接 int 文本解析，不会经过 float；非法小数字符串会响亮失败，不静默截断。JSON 已知身份字段使用精确 integer，decimal token 与整数 token 一致保真。

## 明确保留的限制

没有对最终 571 个签名的所有用户定义 scalar 协议、所有隐式运算、所有超越值和所有文档定量陈述做形式化证明。不是因为候选已逐项分类，就能声称全仓不可能再有缺陷。这里交付的是位点级可复核处置和已确认问题的红绿闭合；全套结果、静态台账以及独立 G6 身份由各自的门判定。


## 中间版冻结索引增量：246 → 250

这不是将旧计数直接改成新计数。以文件/函数/调用名/原调用文本逐项对账：

- **243 个位点原位延续**。
- **3 个位点迁移而非新增机制**：`numeric_decode.decode_tree` 的 checked scalar 调用移入新 `numeric_decode.scalar`（加保留 signed zero 的薄层）；showcase 中两条 cos/sin 调用从 `arch_problem` 的 lambda 作用域移到 `arch_problem.pt`。
- **4 个真正新增的显式边界**：`osteomorphic._shape_coordinate` 的最终 scalar；`showcase.arch_problem` 的 μ 界；`showcase.arch_problem.pt` 的 x、y 两个完整乘积 scalar。
- 因为作用域属于位点键，原始集合表现为 **新增 7、旧位置退役 3，净增 4**。JSON 保留全部增量明细及 prior_site_id，不把迁移重复统计为新修复。
- 新 `tools/bdda3d_document.py::loads` 已纳入最终 58 模块哈希。其 `integer/scalar/loads_exact` 别名调用不都被原词法过滤器计数，但本次已另按明确字段 schema 人工核对；词法少计不等于该模块未复核。

### 250 位点中间版 SHA256 绑定（保留历史）

- 当时索引 `numeric_surface_audit.json`：`013f373ae1a1ee94637e63c9fdbb6461543d175fd731be896bd159dd43764022`。
- 当时 58 模块路径→字节 SHA256 映射的规范 JSON 摘要：`b481f6e70a41dc60236037c4ea14b529560977c7208d619d2b2aefcff97347b0`（各文件哈希现保存在 `numeric_call_review_250.json` 的 `source_sha256_at_review`）。
- 当时 `numeric_call_review.json`（现原字节归档 `numeric_call_review_250.json`）：`66bc3c2031d8d14f3ba48d949cf98facdb0d90e528b5149ffda9589e55e387ea`。
- 此增量仅更新 reports 文件；冻结源代码和 tests 未修改。

## 首轮全仓后增量：250 → 251

第一轮全仓并非全绿，原样结尾是：

```text
R14FIX_FULL_SUITE FAIL: 12402 calls; wall=660.926s; failures_or_skips=6; source_drift=0
```

其中二维近自锁两格的精度退步导致此轮重新设计邻点路径；adapter 异常量名、旧变异路径与 canon 头部定位另行修正。不能以先前定向通过覆盖这次失败。最终全仓重跑结论由主报告填写，本复核不预告全绿。

- 原 **250 个调用文本/作用域均延续**；新增仅一条 `limit._certified_friction_direction` 内的 `scalar_rational(v, quantity="friction generator")`。无退役位点。
- 变化的生产模块仅 `src/eab/limit.py` 和 `src/eab/adapters/bdda2d.py`；最终逐模块字节哈希已重绑。源/tests 本次仍只读。
- 二维调用方先对完整 `n ± μt` 做一次 RN，认证函数的初值及最近距离都以该 RN 候选为基准；测试的独立表达式亦如此，并非一个相对于 exact 候选、另一个相对于 RN 候选。
- 初值安全直接返回；否则逐分量本值与相邻两个 binary64，最多九组合。显式排除非有限、原非零分量变零或反号，再以 Fraction 的正法向功及物理圆锥不等式筛选，最后按有理距离平方取最近者。没有安全邻点才走原有限步内缩，仍不安全就具名异常。未变更三维路径，也未放大 uncertainty。
- 新门独立使用二维行列式 `det(n,g)² ≤ μ²(n·g)²` 与给定浮点数据完整表达式，不复用生产 dot/norm 证书；读取 `two_d_neighbor_red.log` 的 `6 failed, 18 passed, 98 deselected in 0.16s` 与 `two_d_neighbor_green.log` 的 `356 passed in 22.32s`。
- 删除邻点分支的真实变异仍红在原近自锁断言 `abs(r.alpha - exact) <= (r.uncertainty + 1e-9) * exact`，不是意外状态差异；日志 `1 failed in 0.12s`。
- adapter 量名同步后 h1 仍在构造和属性两层按同一 `bdda2d.cone_tol.h1_degrees` 检查；域未变：`0 ≤ h1 < 90` 度且零或 D400。读取器补充门 `549 passed in 15.49s`；删除两层角域检查由原拒绝断言报 `DID NOT RAISE ConstructionDomainError`。

完整 250 位点报告另存 [`numeric_call_review_250.md`](numeric_call_review_250.md) / [`numeric_call_review_250.json`](numeric_call_review_250.json)，初始 246 元数据与 246→250 增量仍保留在最终 JSON 内。

### 最终 251 位点 SHA256 绑定

- 最终索引 `numeric_surface_audit.json`：`ff06b68d74ba42a886f808c0e85e5bfb30fecea101a02e6105af2442404630db`。
- 最终 58 模块路径→字节 SHA256 映射的规范 JSON 摘要：`738beb1442b99804fe9b1cae158a7b70451353762289436eb0d004c4b218e3ea`（`sort_keys=True,separators=(",",":")`；各模块哈希在 JSON）。
- 最终 `numeric_call_review.json`：`d01923ce76a6947bc58cad92e01085f1ad7c68d54835a8a6c4b29090d468b1d2`。
- 251 候选是词法覆盖加人工处置，不是全部 571 签名的形式证明，也不是独立 G6。
