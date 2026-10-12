# WO-R13FIX 处置报告

日期：2026-10-13。工作树 `D:/eab-wt/cx-e2`；分支 `codex-work`；基线 `fabe303`。

## 结论

**PARTIAL：G6M-01～03 已处理，新增运行时差分门并修复同类真实构造错误；“全部公开构造 API 补齐极端尺度独立逐值门”未完成。**
仍有已复现的混合类型 raw 向量溢出、超长边导致最终可表达 `face_noise` 被中间长度拒绝，以及下列覆盖缺口。
不以静态零诊断或全套绿冒充这些遗留已解决。

输入报告/JSON 实际确认 **3 个唯一编号（0 critical / 1 major / 2 minor）**，不是工单措辞中的“6 条”。
以下按 **11 个验收工作项**交付；没有把同根因形态或附加门虚构为 11 条复审发现。
M0 的所有者退出决定不变；本轮不宣称独立 G6 或新鲜 worktree 门通过。

## 1. 范围、基线与验收

- 开始时只有 `reports/codex/inputs/G6M_*` 未跟踪，其余 tracked 工作树干净；原始输入不改。
- 仅写本工作树；无 Git commit/push/reset/checkout/stash/worktree 操作，无姊妹仓库写入，无 fixtures 改动。
- 回滚锚点：只读基线 `fabe303`、[静态工具修前副本](R13FIX_evidence/static/)、[政策修前字节](R13FIX_evidence/root/policy_before.json)。不执行任何回滚操作。
- Python 命令均设置 `PYTHONDONTWRITEBYTECODE=1`，使用 `python -X utf8`。临时测试目录在本树 `R13FIX_evidence/tmp/`。
- 成功要求：三发现红绿与真实内部变异、原断言/网格保留、API 逐项库存、差分门、文档同步、完整节点全套绿。
  其中“每个公开构造量完整差分覆盖”尚未达标，因此只能 PARTIAL。

## 2. 十一个验收工作项

### 01 · G6M-01（输入 major）：类生命周期及实例字段副作用

**根因**：初始化只看直接 `__init__`；方法调用归并返回值而没有完整 receiver 写回；dataclass 后初始化、继承初始化、setter 的字段修改未传到构造 sink。

**修前红**：[before_red.log](R13FIX_evidence/static/before_red.log)。审查三种新 helper 均 `approved_sites=0`，
`q=Fraction(1,2**1075)` 时返回 `0.0`，独立 Fraction 舍入胞要求 `5e-324`；目标是必须有 `closed-rounded-construction`，原 `issues=[]`。
setter 原仅有 `closed-decorator`，缺少数值副作用传播，新增目标断言同样红；这不能描述为 setter 原先零诊断绕过。

**修法**：有限 receiver 字段摘要/写回，记录方法、单继承初始化、dataclass `__post_init__`、继承生成初始化、显式 setter；
缓存签名纳入字段状态，避免已读字段沿旧摘要绕过写入；同时补字段隔离、builtin type guard、固定 tuple 等必要有限事实，避免整对象字段串扰。
精确 `*1` 控制不能误报成原 `*1.0` 缺陷。

**牙**：在真实被测 flow 内禁用普通方法写回、继承初始化、post-init、setter 调用，拒绝断言分别变红；不是篡改扫描输出。
详见 [永久门](../../tests/test_r13fix_static_lifecycle.py) 与 [静态分报告](R13FIX_evidence/static/static_summary.md)。
独立同任务交叉探针还覆盖初始化间接调用方法、关键字实参、继承方法和 getter 缓存后 setter，见
[交叉日志](R13FIX_evidence/events/cross_static_lifecycle.log)。这不是六路 G6。

**边界**：精确 property setter 仍可因 `closed-decorator` 被辅助子集拒绝；只声称数值副作用传播，不声称无例外准入。
元类、动态安装描述符/方法、任意别名、多继承 MRO、未知扩展及 monkeypatch 不获完全分析保证。

### 02 · G6M-02（minor）：三维首入的返回位置与事件脱钩

**修前复现**：内部返回 `exact_x -> x0`，现有原 24 格门 **24 绿**。生产基线正确，缺陷在测试牙，不虚报生产基线红。
先新增独立绑定探针后，同一变异红在 **`event position midpoint binding`**。
修后三维原网格 **23 红 / 1 none 分支绿**；全部失败都是目标位置断言。

**修法**：保留返回点实际状态的原核验，再由独立 Fraction SAT 求 earliest time；核精确时间、显示时间及每个返回坐标的 RN-even 中点胞。
不能再用“另算的正确端点相触”替代“实际返回端点正确”。

**同类修复**：二维原 30 格也存在脱钩；同一内部变异修前 **30 绿**，修后 **29 红 / 1 none 绿**。
原三维新增 4 行、二维新增 5 行，原断言与参数格零删除。
见 [变异矩阵及 traceback](R13FIX_evidence/events/mutation_matrix.json)、
[修前现门](R13FIX_evidence/events/pre_fix_existing_mutant.json)、[先红探针](R13FIX_evidence/events/new_binding_red.log)。

### 03 · G6M-03（minor）：canon 当前摘要过时

**修前**：[docs_before_red.log](R13FIX_evidence/root/docs_before_red.log) 为 `1 failed, 1 passed`，红在
`obsolete whole-repository pin in current canon summary`。
**修后**：顶部明确为 R12FIXb 局部 AST/最小封闭源码 SHA-256 和 int/Fraction 数据流；不再声称全库依赖冻结或纯整数字面量准入。
当前顶部同时同步 R13 的辅助定位。
**牙**：向文档读取路径重新植入旧摘要，目标“obsolete whole-repository pin”断言红；正常文档
[2 passed](R13FIX_evidence/root/docs_after_utf8.log)。

### 04 · 所有者定位调整

README、canon_map、本树三维设计、精确谓词计划、R12FIXb 同步页、[R13 设计补遗](../../docs/r13fix_design_sync.md) 与工具 docstring 均明确：
**静态工具/子集准入是辅助代码检查，不是安全保证；独立运行时构造差分是主保证要求。**
未来仅静态绕过、无生产错误实例的发现按 minor；保留本轮输入原 major，不篡改历史分级。
外部 `D:/E(A, B)` 正本按只读约束未写回，本树补遗是同步交付位置。

### 05 · 全公开 API 普查

AST 库存覆盖全部 `src/eab/**/*.py`，含私有对象用于审计边界；公开范围是源码暴露面，不仅 `__init__` 再导出。
目前 **915 个符号、333 个 public callable、249 个 public 字段**；**107 个 callable 有人工明确差分映射**；
**138 个 numeric/oracle/reader/混合 callable 尚未确认满足完整极尺度逐值门**。
这些数目不是“107 个已全域证明 / 138 个生产缺陷”；数据字段也不能因类型有测试就自动全部覆盖。

逐项已有门、新增门、缺口、尺度、限制和 nodeid 见
[API 清单](../../docs/r13fix_construction_inventory.md)、
[JSON](R13FIX_evidence/construction/public_api_inventory.json)、
[可重跑普查脚本](R13FIX_evidence/construction/inventory_public_construction.py)。
这是本单主工作量的未完成项，不能标 DONE。

### 06 · 同类真错：向量与坐标构造

- `s=2^-538`：二/三维点积或叉积应为最小次正规数 `5e-324`，原算成 `0.0`。
- `s=2^1020`：相消点积/叉积真值 0，原中间 `inf-inf` 变 `NaN`。
- 全 float 坐标相加超范围、minsub 乘半原静默为 inf/0。

**修法**：仅全 float 分支先以 Fraction 完成该积和/行列式/单项加减乘，再最终 checked scalar；
既有 Fraction/Dual/其他泛型路径不擅自转换为 float。translate/translated/box 复用检查后的坐标加减。
**红绿与牙**：[geometry_before.log](R13FIX_evidence/construction/geometry_before.log)、
[coordinate_before.log](R13FIX_evidence/construction/coordinate_before.log)、
[最终 59 格与变异打印](R13FIX_evidence/construction/geometry_final.log)。
真实内部恢复浮点积和、叉积、unchecked add，分别红在最终逐值断言或 `DID NOT RAISE` 范围断言。
混合 int/float raw 路径仍有实测残留，详见第 5 节。

### 07 · 同类真错：相对噪声先构造绝对量

`s=2^-1070` 盒体的 `edge_noise` 原先把 `64*eps*C` 舍入为零再除短棱，返回 0；独立有理比例应为 `7.105427357601002e-15`。
`face_noise` 原先构造不可表达面积，阻断最终可表达的相对报告及逃逸路径。

**修法**：相对报告保留原始向量平方/有理分子至最终比例开根；不把不可表达中间面积当必要输出。
face_noise 周长明确为“逐边最终舍入长度的精确和”，不冒充多根式精确和。
独立 absolute floor 最终非零不可表达则响亮拒绝。

[修前 6 failed, 1 passed](R13FIX_evidence/construction/noise_before.log)；恢复早舍入的真实 `edge_noise` 变异红在
`edge relative diagnostic exact ratio`。另外新增均匀小体逃逸全路径门，防止局部诊断又阻断正确高度。

### 08 · 同类真错：摩擦方向分量提前舍入

`normal=(0.6,0.8)`、`mu=nextafter(1,0)`：原 `normal[i]+mu*t[i]` 得 `-0.19999999999999996`，
完整有理表达式最终正确舍入为 `-0.19999999999999998`。
修前 [mechanics_first_probe.log](R13FIX_evidence/root/mechanics_first_probe.log) 红在
`friction complete component rational rounding`。

二/三维每个分量改成完整 Fraction 表达式后舍入；三维仍使用给定 libm 角度/系数，不声称理想圆锥精确化。
新门覆盖次正规/普通/上溢边缘 μ；三维非轴法向、显式正交切向、k=5/8 完整列表逐分量对拍。
内部恢复提前乘法，同一目标断言红；M4a 不改。

### 09 · 其他公开构造的运行时差分

- 几何：距离、单位方向、面法向/棱方向、二维面积/形心、三维面积/体积/形心、2D 三种及 3D 六种盖的数值字段。
  面积/体积使用对应量纲的极尺度网格；各向异性输入让巨大间隙和可表达面积共存，避免非法输入制造假红。
- frozen：六种盖的 gap/normal 及非零导数，face/EE 的独立非零法向 jet、普通与 Dual lift。
- margin：合法闭盒的距离/间隙/法向/见证点/精确平方，投影、凸入口距离和方向。
- 核心：vector 最终各分量及产物互异；wrench/power 的独立行列式；rational3 多项式；Dual atan2/sqrt 的逐值导数；
  sin/cos 按明示 libm 系数模型；LP 唯一原始/对偶解及所有显示字段；单/多体解析滑移承载。
- 事件：首入/出口字段、凹台阶、逃逸 exact_height/exact_offset/向上显示胞；名义候选与 flat profile。

这些新增门多数在修前正确生产代码上本来就绿，**不虚造生产修前红**。补牙通过真实函数内部缺陷注入：
face_area 先开根后除二、frozen 先舍入 raw normal、逃逸删除 nextafter 或 offset 的 `+root` 等。
原 R9/R10 构造胞和导数门继续保留。
根三测试定向 [106 passed in 0.35s](R13FIX_evidence/root/core_final.log)；事件详见
[分报告/覆盖矩阵](R13FIX_evidence/events/events_summary.md)。完整最终结果以下节为准。

### 10 · 同类扫描、测试改写与静态人工范围账

- 入口/出口/逃逸扫描覆盖 21 个测试文件、127 个测试函数的字段断言候选，并手读主要迁移门。
  [扫描 JSON](R13FIX_evidence/events/event_gate_scan.json) 不是全 127 函数逐变异证明。
- 已有测试只在三维/二维随机首入门加断言，不删、不放宽、不 skip/xfail、不减格。原 11508 nodeid 保留由全套运行器核验。
- 静态 receiver 传播也暴露既有**近似输入生成/诊断模型**和结构摘要未证明站点；不撤掉传播来保持旧零诊断。
  对明确已读作用域逐站点记录人工排除，不宣称它们不存在中间舍入。
- 政策账：**2365 − 删除 22 个失效旧站点 + 人工审阅 108 个局部站点 = 2451**。
  108 中包含 5 个泛型 dot 旧节点和 3 个 libm 角度旧节点续审；其余是新传播暴露的近似/结构范围。
  最后坐标补修另逐条续审原有 11 个 add/sub/mul 泛型回退节点，仅这四个已改作用域的局部 pin 更新，条数不变；混合类型真残留仍列 PARTIAL。
  [逐站点理由、类别、AST、源码 pin](R13FIX_evidence/root/manual_policy_review.json)，
  [删除清单](R13FIX_evidence/root/policy_removed_scopes.json)。
  没有整库 hash 刷新、没有给 G6M 三个植入文件加排除、没有“扫描到什么就默认放行”的运行时机制。
  **2451 条排除不是证明；静态零诊断必须连同此账阅读。**

### 11 · 文档、指针、M4a 与最终全套

文档同步见本报告 04 项。M4a 三组门曾定向 **109 passed in 7.81s**，
[日志](R13FIX_evidence/events/m4a_after.log)；最终全套再次包含，未改适配器或 fixtures。

<!-- R13_FINAL_VERIFICATION_START -->
最终完整集合 **11723 passed**，其中本轮新增 **215**；原 11508 节点全部保留。
采用四个标准 pytest 完整文件分片，不是单进程的伪造汇总输出：

|分片|pytest 最后一行原样|退出码|
|---|---|---|
|shard_1|`2013 passed in 536.79s (0:08:56)`|0|
|shard_2|`2225 passed in 427.05s (0:07:07)`|0|
|shard_3|`3423 passed in 449.23s (0:07:29)`|0|
|shard_4|`4062 passed in 463.84s (0:07:43)`|0|

完整运行器最后一行原样：

```text
R13FIX_FULL_SUITE PASS: 11723 calls; wall=541.682s; failures_or_skips=0; source_drift=0
```

- 全套执行墙钟 **541.682 s**；收集 3.037 s；合计约 544.719 s，达到尽量 ≤900 s 目标。
- 四进程墙钟之和 1899.274 s，不把此数当单进程耗时或 CPU 基准。
- 所有收集/执行 nodeid 并集相等且无重复；原 11508 节点均在；setup/call/teardown 无失败、skip/xfail；全部进程退出码 0。
- 源码、tests、tools、政策、项目配置及文档前后 SHA-256 一致：`source_policy_unchanged=true`，`code_drift=[]`。
- 静态辅助扫描最后一行：`exact construction AST gate: 0 violation(s)`，须与 2451 条明确人工排除一起阅读。
- 已执行 `tools/fix_canon_ptrs.py --apply`：5 处更新；再次只读核验 `0 rewritten; 0 kept`。
- `git -c core.whitespace=cr-at-eol diff --check` 无诊断（保留原 CRLF 合同，不为 diff 检查整文件改换行）。

证据：[全套 summary.json](R13FIX_evidence/full_suite_final/summary.json)、
[运行器完整日志](R13FIX_evidence/full_suite_runner.log)、
[前快照](R13FIX_evidence/full_suite_final/before_snapshot.json)、
[收集节点](R13FIX_evidence/full_suite_final/collection_nodes.json)、
[静态最终日志](R13FIX_evidence/root/static_final.log)、
[指针更新](R13FIX_evidence/root/canon_ptrs_apply.log) / [核验](R13FIX_evidence/root/canon_ptrs_verify.log)。
全套各分片的逐节点 JSONL 和原日志均在同目录；运行脚本不改选择集合。
Python 直接输出的分片日志为 UTF-8；PowerShell 重定向日志保留其 UTF-16 BOM，读取时须按 BOM 解码，不改原始证据。

<!-- R13_FINAL_VERIFICATION_END -->

## 3. 验证过程中保留的失败及分类

- 新几何测试首稿 3 个 VV 输入没有产生有效盖：**输入错误**，换为合法斜向错位 VV；未算生产修复成果。
- 根 mechanics 首稿把 minsub/2 导数误当可表达：**输入/期望错误**；保持同一参数格，改核独立精确非零下溢应抛错，未修改生产 Dual 来掩盖。
- 根 margin 首稿用没有 surface 的单点调用 body_distance：**前置条件错误**；改有效闭盒且保留全部尺度，单点仅用于允许凸包投影的 API。
- 文档写入初次 PowerShell 管道编码替换中文为问号：**环境错误**，文档门当场红；设 UTF-8 pipeline 重写后绿，原日志保留。
- 静态分项首次 basetemp 父目录不存在：**环境错误**；建本树目录后重跑。旧维护副本门在政策待收口时红，不能忽略，最终全套重新验。
- 所有日志留在 evidence；不把这些失败与真正数学红混算，也不删失败日志挑绿。

## 4. 可重跑入口

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -X utf8 tools/check_exact_construction.py
python -X utf8 reports/codex/R13FIX_evidence/construction/inventory_public_construction.py
python -X utf8 reports/codex/R13FIX_evidence/events/run_mutation_matrix.py
# 使用新名字，禁止覆盖已有运行证据
$env:R13_RUN_NAME='full_suite_rerun_01'
python -X utf8 reports/codex/R13FIX_evidence/run_full_suite.py
```

## 5. 必须保留的遗留

1. 全公开构造量差分门未补齐：138 个 numeric/oracle/reader/混合 callable 未确认完整要求；其他映射也只覆盖列明构造族，并非全域证明。
2. 混合 int/float raw 算术仍有 `geom3.add` 返回 inf 的真实复现；本轮未改变所有泛型/混合标量合同。
3. `face_noise` 对超 binary64 边长仍会在中间 norm 拒绝，即使最终相对报告可表达。
4. 普通 Dual 算术快路/一般幂、一般角度与多根式诊断、非零一般 dilatancy_profile、读取器/适配器全部数值字段、一般力学活跃集网格仍未闭合。
5. 2451 个静态人工排除仍需消化；辅助检查不提供任意 Python 安全保证。任意 alias/动态协议等仍可超出有限建模。
6. 工单禁止新 worktree；独立 G6 与外部只读设计正本写回由所有者后续安排，未代办。

实测残留与历史修前状态分别见 [最终 residual_probes.json](R13FIX_evidence/construction/residual_probes.json) 和
[后续坐标补修前版本](R13FIX_evidence/construction/residual_probes_before_coordinate_fix.json)。

R13FIX_PARTIAL：全部公开构造量极尺度差分门未补齐；混合类型 raw 算术范围与超长边 face_noise 遗留；静态人工排除及复杂动态协议未闭合
