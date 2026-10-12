# WO-G6K：G6 第十一轮独立正确性复审

## 0. 结论、基线与操作边界

**已确认：0 critical / 2 major / 0 minor。按本工单的 `0 critical / 0 major` 标准，不能确认 M0 退出。**
用户所述“连续四轮无 critical”的行政退出口径不等于本单要求的正确性退出门；本报告不修改历史状态，只作当前 HEAD 的审查判断。

- 对象：新鲜 detached 树 `D:/eab-wt/g6k`，HEAD `5591702b8c8216350a47982c4b22b4c8a43d0ca4`。
- 身份：独立审查方；没有实现方会话上下文。主审及三个独立分路只审、不修；历史修复报告不是正确性证明替代品。
- 自跑全套：**10813 passed in 1190.63s (0:19:50)，exit 0**；包装进程总耗时1199.51秒。启动时即运行串行 pytest；未用 xdist。审查脚本同时运行，因此耗时不是独占机器性能基准。
- 用户示例的“g6f 内 tmp”与“其他树只读”相冲突，采用本树 `review/tmp_fullsuite`。Python 禁止 bytecode，pytest 禁 cacheprovider。
- tracked 原字节核验：**2736个 tracked 文件 SHA-256 全部与审前一致，漂移0；HEAD未变，tracked git status为空**。所有脚本、日志、报告只保存在本树 review；源内变异在内存或 review/copies 的隔离副本里，副本变异恢复按 SHA-256 验证。没有 Git 写操作、没有运行姊妹 exe、没有修改姊妹源码或外部理论正本。

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONIOENCODING='utf-8'
python -X utf8 -m pytest -q -p no:cacheprovider tests --basetemp=D:\eab-wt\g6k\review\tmp_fullsuite
```

证据：[完整串行日志](file:///D:/eab-wt/g6k/review/logs/fullsuite.log)、[运行元数据](file:///D:/eab-wt/g6k/review/logs/fullsuite_result.json)、[审前字节锚点](file:///D:/eab-wt/g6k/review/tracked_sha256_before.json)、[最终核验](file:///D:/eab-wt/g6k/review/logs/final_verification.json)。

## 1. 已确认发现

| ID | 严重度 | file:line | 一句话结论 |
|---|---|---|---|
| G6K-K01 | major | `tools/check_exact_construction.py:297-326` | 循环只合流 rounded 集，不合流 callable aliases/bindings；零次循环能让真实错误构造逃过静态门。 |
| G6K-K02 | major | `src/eab/kernel2d/geom.py:279-290;369-370` | orient2d 过滤只识别 Fraction，混合大整数/float 的转换误差未入界；可判反号，并把非退化三角形三角化为空。 |

分级与去重：K01 是门无牙，不是 pristine 内核当前已返回该错误，也不是全部动态数学门无牙。K02 是窄域数值类型/坐标组合的真实错误，按工单“错误答案但范围窄”记 major；不夸大到已经先 Fraction 化的相交/成员入口。三种循环语法及102个错格均按各自根因合并计数。

### G6K-K01：零次循环中的构造函数别名漏检

- **具体输入**：`u=2^-1074`；四面体顶点为 `(0,0,0),(1,-1,u),(u,1,-1),(-1,u,1)`，另一体为其反射体，调用真实 `cone_intersection_margin` 核两体顶点0的法锥。其最小范数点 `p=(-u/3,-u/3,-u/3)`；独立 Fraction KKT 核该点，平方与相邻浮点中点比较证实最终范数 RN-even 应为 `u`。
- **内部缺陷注入**：在真实函数的 final norm 前放 `root=norm_rational; for _ in (): root=abs`，随后调用 `root(vector_rational(p, allow_underflow=True))`。循环实际不执行，运行时 root 仍是 norm_rational；scanner 却保留遍历循环体后的 abs 别名，漏掉“向量先舍入再求范数”。`range(0)` 与 `while False` 同根因。
- **错误输出与门**：pristine `5e-324`，mutant `0.0`，对整个真实 covers3.py 的 `scan_text` 为 `[]`。这是被测代码内部的错误算术，不是在产出后拼假数据。当前动态 R9/R10 中点门能抓这个数值错误；本发现仅证明指定静态门的新语法漏牙。
- **建议修法（未实施）**：循环的 may-state 同时合流 rounded、aliases、bindings，并保留零次执行路径；新增三种真实构造路径的内部变异门，不以未知跨过程/反射豁免此局部语法。
- **复跑（PowerShell，本树根目录）**：`$env:PYTHONDONTWRITEBYTECODE='1'; python -X utf8 review/repro/g6k_static_zero_loop_alias.py`。

[脚本](file:///D:/eab-wt/g6k/review/repro/g6k_static_zero_loop_alias.py)、[主审亲自复跑输出](file:///D:/eab-wt/g6k/review/logs/root_confirm_g6k_static_zero_loop_alias.log)。运行 exit 0 表示缺陷已被证明：

```text
for_empty_tuple: expected=5e-324, baseline=5e-324, mutant=0.0, gate_issues=[]
for_range_zero:  expected=5e-324, baseline=5e-324, mutant=0.0, gate_issues=[]
while_false:    expected=5e-324, baseline=5e-324, mutant=0.0, gate_issues=[]
confirmed=true; tracked_source_unchanged=true
```

### G6K-K02：混合大整数输入让二维定向过滤给错答案

- **具体输入一**：`N=2**53`，`a=(N+3,3.0)`，`b=(N+5,4.0)`，`c=(float(N),0.0)`。全部是有限、可精确有理化的 Python 数；精确行列式 `3*4-3*5=-3`，故应为右转 `-1`。当前快路先把整数端点隐式转成 float，所得 det 为正并远超相对过滤界，直接返回 `+1`。
- **具体输入二（真实传播）**：`P=[(N+2,7.0),(N+3,11.0),(float(N),0.0)]` 是面积 `1/2` 的合法非退化三角形。当前 `triangulate(P)==[]`；逐坐标先转 Fraction 后为 `[(0,1,2)]`。不是理想几何 vs 舍入数据的比较：两次输入数学值相同，仅数值表示不同。
- **范围**：3072个混合格中102个错，82个真反号、20个精确共线却报非零。另做39000个 float/Fraction 双线性及三维定向符号独立对拍，未发现错误。`polygons_overlap`、`interior_point` 等已先 Fraction 化，未证明本例在它们内部传播。
- **合同依据**：orient2d 文档承诺精确符号；triangulate 承诺精确谓词和非退化耳切。它们未拒收 int；同仓一般数值入口将 int/Fraction 当精确输入处理。把调用方已给出的整数预先舍为 float 是算法新增的信息损失，不是输入原有舍入。
- **建议修法（未实施）**：只有全部坐标均为普通 binary64 float 才走现有 float-only 过滤；其他类型先精确求值，或采用包含输入转换误差的保守界。补混合类型的定向/三角化独立门及过滤绕过变异。
- **复跑（PowerShell，本树根目录）**：`$env:PYTHONDONTWRITEBYTECODE='1'; python -X utf8 review/repro/orient2d_mixed_integer.py`。

[脚本](file:///D:/eab-wt/g6k/review/repro/orient2d_mixed_integer.py)、[全部102个错格](file:///D:/eab-wt/g6k/review/logs/orient2d_mixed_integer_results.json)、[主审输出](file:///D:/eab-wt/g6k/review/logs/root_confirm_orient2d_mixed_integer.log)。

```text
mixed inputs (9007199254740995, 3.0) (9007199254740996, 4.0)
             (9007199254740992.0, 0.0): got 1, exact (0, '0')
Fraction inputs 0
sign reversal: got 1, exact (-1, '-3')
wrong 102
sign reversals 82; exact-zero errors 20
nondegenerate triangle area2=1: raw [] exact-input [(0, 1, 2)]
```

## 2. 第十轮五条回归重放（先原复现，再正向检查）

从只读 g6j/review/repro 复制六脚本到本树 `review/repro/r10/`，只改本树路径。原缺陷断言全部退出1，报红的是“旧错误应存在”的断言，非环境错误；正向复现六脚本全部退出0。没有把仅“不再复现”当作已修证明。

| 第十轮 | 判定 | 当前正向结果 / 边界 |
|---|---|---|
| J01 静态门关键字/伪去污/局部累加 | 已修（原反例） | 七原型全部有指定 rounded-root / rounded-vector / subtract-rounded 违例；真实 cone keyword 变异被抓。**同类新漏网另记 K01**，不据此把原七原型说成未修。 |
| J02 三维普通边界初态闭集首入 | 已修 | 原三姿态×四方向/窗口格均为 entrance、exact_t=0；进入、背离、切向和零 t_max 保留。 |
| J03 微反射法锥反向误 strict | 已修 | 三姿态反向都为 -1，同向显式微反射窗口为0。 |
| J04 Dual.sqrt 完整导数先舍入 | 已修 | 原四导数为1/3/5/7u；范围外 ArithmeticError / OverflowError，不静默0/Inf。 |
| J05 无界结果 NaN uncertainty 标 resolved | 已修 | 原例当前 uncertainty=8.881784197001252e-16、finite；resolved 是允许结果，不要求这个低 U 输入必须 unresolved。另有四个 NaN/Inf 注入均 unresolved。 |

当前五个新增 R10 测试文件由主审最终定向自跑 **209 passed in 1.44s**，见[日志](file:///D:/eab-wt/g6k/review/logs/root_r10_targeted_final.log)；该子集不代替全套或退出门。

[原重放元数据/输出](file:///D:/eab-wt/g6k/review/r10_replay_raw.json)、[六个正向脚本完整输出](file:///D:/eab-wt/g6k/review/r10_replay_positive.json)、[复现目录](file:///D:/eab-wt/g6k/review/repro/r10/)。

## 3. 九镜头覆盖与同类漏网检查

### 镜头1：精确性声称、浮点分支

全 `src/eab` 35个模块做 AST 库存：1298个条件行、1600个 Compare（31个模块含比较）。筛出140个带 tol/noise/gap/bound 等显式候选逐家族追数据流；补 Return 中的比较，避免只数 If。库存的模块分桶是阅读索引，**不是 Python 类型/可达性形式化证明**。

| 类别 | 当前判断 / 证据 |
|---|---|
| predicates cross2/dot2/orient3d；geom2 orient2d | 保守过滤须退 Fraction。39000格独立原始 Fraction 算式对拍未错；混合整数转换的 orient2d 漏网为 K02。 |
| LP price/ratio/reinvert 等浮点阈值 | 仅给候选；三类精确证书失败后有理数兜底。600个独立 BFS/ray 小 LP 和9个说谎浮点候选确认兜底不是文档空话。 |
| covers / membership / exact_sweep | tol/window 是显式域窗，主要比较已是有理平方/未归一化符号；枚举不得消费显示 gap。独立几何与历史反例核验。 |
| margin | 默认关系/闭合由精确原数据决定；输出见证误差与 rounding 比较仅是构造自检，不能替代精确 minimum2==truth2。显式窗口另外列镜头6。 |
| limit / limit_multi | α/status 的证书精确；U阈值、邻域解、active/contact_forces 截断仅是已明示的诊断/显示。切向基架的有限多边形模型与近乎平行 tangent 拒收已声明，不能冒充精确圆锥。 |
| interlock nominal roots/ties | 旧 nz=1e-12、噪声、浮点簇只决定名义标签/微分兼容报告；权威 exact_height/offset 由完整事件精确核，不以 nominal 过滤接受贯入根。 |
| geom3 私有旧 contact-cone helpers | `_active_normals/_gordan_direction/_min_norm_on_simplex/_contact_cone_witness` 仍有绝对浮点阈值；全仓调用检索表明当前公开 overlap 已转 exact_surface，旧 helper 群无当前入口调用。不当作当前噪声带错答。 |
| readers / ContactRecord | 结构、有限性及 legacy 数据清理。bdda_geom 的 duplicate floor 是公开声明的 df 适配预处理，不是精确几何 API；不能将其 dup_tol=0 当作当前内核零噪声合同的反例。见第5节边界。 |
| Dual | ordinary 四则快路不声称全域最终 RN-even；sqrt/半整数幂/atan2 导数有完整有理式；sin/cos libm 系数近似已声明。原导数修复正向核验与冻结有理 jet 压测，未确认新缺陷。 |

[条件库存](file:///D:/eab-wt/g6k/review/branch_inventory.json)、[候选列表](file:///D:/eab-wt/g6k/review/branch_candidates.txt)、[含 Return 的比较库存](file:///D:/eab-wt/g6k/review/comparison_inventory.json)。

### 镜头2：过滤、缓存、构造等价性

- 39000个 independent Fraction 符号：cross2 12000、dot2 12000、orient2d float族8000、orient3d float/Fraction族7000，含次正规、下溢、溢出、中点/近平面、混合尺度，0错；不掩盖 K02 的另一类型族。
- 7360个构造检查：sqrt1560、norm1200、unit分量3600、复合归一化相减1000。oracle 用相邻浮点的精确平方中点/有符号根比较，不调用生产 oracle_construction；0错，真正范围外异常不计缺陷。
- 79个缓存检查：源顶点/面内容修改与 fresh对象对拍、拓扑返回列表污染、非self凸视图隔离、margin内部记录污染与 `_resolve` 无缓存对拍、事件重复读取，0错。与全套已有 cache-vs-uncached/内部缺键变异合读；未声称覆盖任意外部数值子类。
- LP reduced_sign 再做12000个极端指数与精确相消对拍，0错。过滤界上溢必须走精确回退，不把 NaN bound 当接受条件。

[过滤压力](file:///D:/eab-wt/g6k/review/logs/root_predicate_pressure.json)、[构造压力](file:///D:/eab-wt/g6k/review/logs/root_construction_pressure.json)、[缓存压力](file:///D:/eab-wt/g6k/review/logs/root_cache_pressure.json)、[LP过滤结果](file:///D:/eab-wt/g6k/review/agents/lp_filter_result.json)。

### 镜头3：oracle 独立性

E2–PERF 报告台账、生产 G0 oracle 依赖及测试 oracle helper 对账。二维 support/hull、一般凹二维 g0_oracle、三维 g03_exact / g03_surface_oracle 不调用被测几何原语；独立构造边界与 production construction 分离。借用数学数据模型、原输入坐标及理论恒等式不等于共享被测几何 helper。模型三角化必须一致，但两边独立实现不能证明模型设计自身没有共同误解。

已明示共用项不升级为主 oracle：escape_height_brute 调 covers/exact predicate；旧 inflated_membership/body_distance 的交叉门共用距离；生产自校验重建同一力学模型也不是模型独立验证。独立 box/矩形并、Fraction jet、LP BFS/ray 补强，不把这些共享路径的两边一致当数学真值。

[oracle import库存](file:///D:/eab-wt/g6k/review/agents/oracle_import_inventory.json)、[oracle/门/文档分报告](file:///D:/eab-wt/g6k/review/agents/gates_docs.md)。

### 镜头4：旧门迁移强度与内部变异

检查 `git diff b6126cf..HEAD -- tests` 和报告改写台账，建立逐函数 AST清单；R10只新增五文件，既有148文件未因本轮修复放松。边界豁免迁为“核实际坐标精确真值”，不是跳过边界。

对四个高风险族，在 b6126cf 与当前代码隔离副本实跑旧/新门，副本修改后恢复原字节：

| 内部变异 | 旧门 | 当前门 | 红的语义断言 |
|---|---|---|---|
| 凸成员边界0改1 | 1 passed | 1 failed | 实际边界(-1,-1) `1 != 0`，当前加强 |
| 删除最近 VV | 1 failed / 4 passed | 同左 | vertex_vertex_diagonal 的 `rep.passed` |
| 出口枚举 return[] | 4 failed | 4 failed | `rep.passed`，缺见证为 inf |
| 真实凸最近点返回坐标×0.99 | 3 failed | 3 failed | `abs(d_config-d_body)<1e-9`，首格误差0.0066669 |

这些证明不支持“每个旧断言对每一种可能变异均不弱”；未确认新的迁移变弱。另有13个定向文件776 passed /41.49s。K01 是本轮静态门实际新增盲区，单独计数。

[逐函数台账](file:///D:/eab-wt/g6k/review/agents/gates_test_migrations.json)、[可重跑旧/新变异](file:///D:/eab-wt/g6k/review/repro/g6k_migration_mutations.py)、[实际红断言/哈希恢复](file:///D:/eab-wt/g6k/review/logs/gates_migrations/results.json)。

### 镜头5：几何压力与反例搜索

主审实际再次运行三份独立脚本：80个 Fraction 凸盒（自有 SAT/射线裁剪/出口平方/窗口），120个 L/U prism（自有矩形并 overlap/距离/首入/逃逸），600个二维 L/U×矩形（自有区间并 E 拓扑、四象限局部 germs、物理相交和精确闭射线根）。合计800格，0错；包含1e-15/1e-9/1/1e8尺度、1e8平移、有理旋转、初态接触/贯入与截断窗口。不是用生产 overlap 给自己当 oracle。

凹体的 shortest_exit/shortest_exit3 仅是局部盖出口，文档已经撤回任意凹体全局最短分离承诺；没有用全局 PD 标准误判这个有限合同。G0 全套门、旧漏特征/假极点回放及实际删除 VV/出口变异补检查；不是任意高亏格实体的穷举证明。

[凸盒脚本](file:///D:/eab-wt/g6k/review/repro/independent_box_pressure.py)、[三维凹并脚本](file:///D:/eab-wt/g6k/review/repro/independent_nonconvex_pressure.py)、[二维凹并脚本](file:///D:/eab-wt/g6k/review/repro/independent_2d_union_pressure.py)。完整结果分为[凸盒80格](file:///D:/eab-wt/g6k/review/independent_box_pressure.json)、[三维凹并120格](file:///D:/eab-wt/g6k/review/independent_nonconvex_pressure.json)、[二维凹并600格](file:///D:/eab-wt/g6k/review/independent_2d_union_pressure.json)，共800格。

### 镜头6：局部贯入厚度窗口

按当前准确定义核两条析取，而非泛化为正本闭集 PD：六轴证书证明 `rho<=w`；星核收缩证书证明每个严格重叠区在该体径向厚度<=w的壳内。星核须在每个声明朝外三角面严格内侧，L1半径上界保守；六轴及 L1壳的坐标依赖已经在文档和反例门明示。

独立矩形并/盒族分别计算六轴与壳模型，不共用被测星核/SAT。现有 PERF 内部 w→2w、删唯一方向的语义牙在全套/定向集重跑；未确认违反当前可靠性命题的反例。封闭空腔 `rho=1/8`、`PD_closed=19/8` 是合同限制，不重复计缺陷。报告“相触”不能当原实体严格不贯入证明。

### 镜头7：极限分析/精确自校验

- 独立 Fraction BFS/ray oracle 的600个小 LP：220 optimal、211 unbounded、169 infeasible，0错；exact_x/y 原始/对偶可行、float视图与精确值转换一致。
- 9个 `_float_solve` 说谎状态/候选均被证书或有理数兜底纠正。
- 六组单/多体二维/三维、荷载2^-300/1/2^300：48个 `alpha*(1-2^-k)`（k至1000）全拒绝；另2个小于float一ULP的 exact_x/y 错候选被 limit 自校验拒绝；4个NaN/Inf报告注入均 unresolved。总54针。
- 模型构造与自校验使用同一锥方向定义，不能据此认证精确圆摩擦锥、最优面全部敏感性或工程稳定性。resolved 仍仅为已声明筛查；这不是新缺陷。

[独立LP脚本](file:///D:/eab-wt/g6k/review/repro/g6k_lp_independent.py)、[54针自校验脚本](file:///D:/eab-wt/g6k/review/repro/g6k_limit_selfcheck_independent.py)、[机读LP结果](file:///D:/eab-wt/g6k/review/agents/lp_independent_result.json)、[自校验结果](file:///D:/eab-wt/g6k/review/agents/limit_selfcheck_result.json)。

### 镜头8：文档、代码与只读理论正本

必读 README、AGENTS、exact_predicates_plan、exact_3d_design、canon_map、E2–PERF 六报告、R10FIX及HEAD说明；只读 00/01/03/07，重点核闭集/内部不交、局部盖/全局E、凸/声明折面、静态/运动首入、ContactRecord/G0–G5 与 canon第八节映射。核心契约和命名门定位/定向运行，未确认另一条核心承诺误述。

历史E5a作废/E5a2失败、旧速度、未经G6状态均有后来更新标记，不能按截断旧段误记新缺陷。canon已明示读取器6→3、G2手写清单非检测器、G5未开、G4缩水、缺一般凹全局E、源单盖非完整实体法锥；本单未把这些明示缺口包装成已交付。K01虽不是当前数值错，却反证R10的本地循环扫描强度仍不足。

完整性界限：未重验所有历史性能数字、所有论文外部陈述；词法 test-name 库存含行内标签/短名/测试引用等，不能将未解析字符串自动定性为不存在的门。详细覆盖与未读文件以分报告/第7节为准。

### 镜头9：第五轮50条中的24条原/等价重放

原JSON数组1-based编号为 `7,9,11,20,21,22,24,25,26,27,28,29,30,31,34,36,37,38,40,41,42,43,44,45`。实际执行24脚本，全部最终有效 exit0；包含源码内变异牙、旧错α/机构输入及精确模型重查，不仅跑实现方现有测试。脚本提取引号错误/旧宽容凸性assert已订正，原日志保留；不把审查脚本错误算生产发现。

特别处理三类旧边界口径：
- #24 原80个舍入 Motion 输入不再全应“接触”。独立整数 SAT 按声明面 first-ear 三角化和自有形心四面体并逐格给72贯入/8分离，当前完全一致；另用Fraction刚体变换核接触0。
- #34 原抖动墙在生产 covers/brute 上一致仅算佐证；补有理U槽两个独立解析根1/5。没有冒称原所有抖动墙已做独立事件穷举。
- #36 浮点边界标签随数据变不算不变性失败；精确有理旋转/平移另核18标签保留。

[24条逐项输入/输出/判定](file:///D:/eab-wt/g6k/review/agents/legacy_replay_results.json)、[原反例重跑器](file:///D:/eab-wt/g6k/review/repro/g6k_run_legacy_replays.py)、[#24独立80格](file:///D:/eab-wt/g6k/review/repro/g6k_legacy_geometry_equiv.py)、[LP/回归分报告](file:///D:/eab-wt/g6k/review/agents/legacy_lp.md)。

## 4. 新代码与第六至十轮同类扫描

实际审查 `git diff 0e9ef93..HEAD -- src tests tools`：5个生产模块（dual、2D covers、3D entrance、limit、limit_multi）、1个scanner、5个新增测试；1150 insertions/70 deletions。逐条原修复正向核，新代码内部源变异及差分阅读，不把全套绿当答案。

| 历轮问题类 | 本轮处置/覆盖 |
|---|---|
| 可变缓存/别名 | 源内容与fresh对拍、返回污染、cache-vs-uncached；未确认新数值串用。静态 callable alias 不同问题，计K01。 |
| 隐式噪声带 | AST全仓库存、实际类型/可达性追踪；core默认未确认新窗口吞真值；legacy预处理另界定。 |
| 构造先舍入/快路只查输入 | 精确中点7360检查、Dual R10原反例；定向过滤39000及LP12000。混合类型过滤遗漏计K02。 |
| oracle只查中点 | 读取完整事件分区/前区间核验与独立区间射线oracle；未把共享brute当主证。 |
| 尺度上溢让门失效 | 极端LP、float符号上下溢、构造范围检查；无穷显示不替代exact证书。 |
| 暴力真值漏特征 | 原 #31 距离、#40–44 G0/支持集回放，VV/出口真实删除牙。孤立点域问题未确认。 |
| 冻结闭式相消 | 自有Fraction jet/平方中点和已声明原始法向证书；不反减显示见证。 |
| 首入/出口/逃逸边界初态 | R10十二格与800格独立闭射线/并集，区分普通边界与紧配内部缝。 |
| 标签有限域 | R10原初态及历史平直链/声明三角事件回放；未据源环描述符宣称实体完整法锥。 |
| 声明三角化凸性 | 实体/凸模型分开；独立声明first-ear oracle与原 #42 谓词/G0回放。 |
| 微反射法锥 | 原三姿态反向/同向窗口均正确；未确认新同类。 |
| Dual初等函数导数 | sqrt/half-power/atan2精确完整表达式及sin/cos已明示libm近似；未确认新同类。 |
| 静态门语法覆盖 | 关键字/Fraction伪去污原七原型已抓；零次循环alias漏检计K01。 |

## 5. 未确认与不计数项

1. **未引用孤立顶点**：沿用g6j已记录的域问题。加入未被face引用的点可让距离oracle与实际面表面不一致，margin响亮抛exact mismatch；尚未证明这类存储属于受保障的有效闭合嵌入2-manifold输入。manifold_issues的空列表明确不是全部合法性认证，不升级计数。
2. **legacy duplicate floor**：`strip_duplicate_vertices(...,dup_tol=0)`在1e6坐标会删1e-9真短边；它是文档明示的df适配清理规则，非精确kernel合同。未证明真实df导出特征因此被错误alias且G1假一致，不另算缺陷。不能把该预处理用于任意精确几何的零窗去重。
3. **仅显示的巨大/极小构造**：非零结果确实超binary64范围时的响亮异常不记critical；事件有exact根不代表所有nominal面积/法向显示都可表达。
4. **未知动态Python/外部数值子类**：未证明scanner对反射/跨过程完备，也未据此计数；K01只用明确本地语法，不能被这个边界豁免。

## 6. 审查错误与证据质量控制

- 二维压力脚本初版字段名 exact_t→t_exact、旧脚本提取引号、宽容凸性前提等是审查脚本问题；纠正后重跑，未计生产发现。
- PowerShell默认ASCII管道曾把部分审查中文草稿变问号；用UTF-8重新写入、读回核中文，数学脚本/结果未因此改变。交付校验再核中文报告、JSON必填字段、链接存在与计数。
- 新发现由主审在当前HEAD亲自再次执行；每条 machine JSON 保存完整 verified_output。全部几何/LP主压力也由主审复跑保存，不以子审结论替代实测。

## 7. 完整性批评

- 九镜头均有独立工作与证据，但不是形式化正确性证明。全35个src模块有词法库存和分路覆盖；主要变更/精确核全文读，未逐行新读所有未变更 tools、全部 tests/helper 或所有历史报告正文。未改且第十轮已覆盖的读取器/静态适配路径以diff与旧覆盖为依据略写，主审补读ContactRecord和三个读取器。
- 明确未完整逐行重读的生产文件/段落：`kernel2d/exact.py`、`kernel2d/g0_oracle.py` 的全部旧分支；`kernel3d/covers3.py` 的全部单盖/LP近凸包；`kernel3d/geom3.py` 的全部凸包/manifold/merge；`kernel3d/exact_geom.py` 的全部平面分区/star-tetra SAT/triangle-distance。这些文件已读相关函数、diff或oracle路径，不能冒称全文数学审计。全部35个文件均有库存，词法扫描不等于阅读。没有重新阅读外部 `o3/o3t`、`solver_profile`、导师DDA4.x所有源码；其状态只核canon现行边界。
- 旧测试迁移有逐函数清单及四个高风险家族真实旧/新变异；**没有为每一个旧断言穷举所有可想到的错误实现**。不能把该证据冒称全迁移强度证明。
- 文档核心现行承诺/07映射已核，历史“已完成/已验证”全部句子的逐字穷举与所有历史数值重新实测未完成。命名门存在/通过也不自动证明其断言涵盖完整声明域。
- 第五轮仅24/50条原/等价重放；原#34的共享brute仍仅佐证。其余26条未本轮逐条重放，不能据报告宣称50条全部独立关闭。
- 独立几何oracle限凸盒、矩形并L/U、若干已知声明三角族、有限随机/指数格；未穷尽任意高亏格、复杂折面耳切、极端退化拓扑或一般凹体全局E。未重跑姊妹导出器/求解器，无工程验证或部署证明。
- 缓存/过滤覆盖普通float/Fraction/int与既有Dual契约；未穷尽第三方数值子类、恶意直接修改内部缓存字段、所有浮点误差界的形式推导。K02提示“输入数值类型”本身也应进入过滤合同。
- 当前2条major应交实现方修复、补真实路径牙，再在新鲜只读树复审；审查方没有修复它们。0 critical不抵销major退出阻塞。

## 8. 交付与重跑入口

- [机读发现](file:///D:/eab-wt/g6k/review/G6K_findings.json)
- [主审实跑命令、脚本哈希、完整输出](file:///D:/eab-wt/g6k/review/logs/root_confirmations.json)
- [几何/回归分报告](file:///D:/eab-wt/g6k/review/agents/replay_geometry.md)
- [oracle/门/文档分报告](file:///D:/eab-wt/g6k/review/agents/gates_docs.md)
- [旧50条回放/LP分报告](file:///D:/eab-wt/g6k/review/agents/legacy_lp.md)
- [证据清单](file:///D:/eab-wt/g6k/review/EVIDENCE_INDEX.md)
- [最终机器核验](file:///D:/eab-wt/g6k/review/logs/final_verification.json)

G6K_DONE critical=0 major=2 minor=0
