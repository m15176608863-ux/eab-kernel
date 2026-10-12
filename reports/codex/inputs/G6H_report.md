# WO-G6H：G6 第八轮独立正确性复审

审查对象：新鲜 detached 工作树 `D:\eab-wt\g6h`，HEAD `30ee15336f64540141d9ba89f8656539dcc08e7c`。审查方不修代码；报告语言为中文。

## 1. 结论

**confirmed critical = 0 / major = 6 / minor = 0。M0 不可以退出。**

第七轮 11 条在其原始复现范围均已修：9 个数学/门/合同问题修复，2 个文案问题订正。不是把旧脚本异常退出当修复证据：另核正确值、全部原子格及具名新门。与此同时，本轮确认 **4 个窄域公开 API 错误、2 个看护门失牙**。6 条均由主审在当前树亲跑确认，原始运行输出保存在机读文件及逐项日志；没有将推测计入。

严重度边界：窄域紧配缝、强混合尺度、极薄二面角和超大中间乘积按工单的“错误答案但范围窄”记 major；两条变异发现按“门无牙使 critical 可能潜入”记 major。没有据此声称默认成员、普通距离、精确 LP 已存在广域静默错误，也没有把未改源码的变异结果当成未变异 HEAD 的 critical。

关键成果：[机读发现](file:///D:/eab-wt/g6h/review/G6H_findings.json) · [逐项回归台账](file:///D:/eab-wt/g6h/review/G6H_regression_replay.json) · [证据/脚本清单](file:///D:/eab-wt/g6h/review/README.md)。

## 2. 自跑全套、环境与只读纪律

实际使用**串行 pytest**：

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONIOENCODING='utf-8'
python -X utf8 -m pytest -q -p no:cacheprovider tests --basetemp=review/tmp/full_suite --junitxml=review/logs/full_suite.junit.xml
```

**9851 passed；0 failed / 0 error / 0 skipped，退出码0**。pytest实际摘要 `1614.33 s`；包装器墙钟 `1636.67 s`（二者计时范围不同）。[全套日志](file:///D:/eab-wt/g6h/review/logs/full_suite.log) · [JUnit逐例结果](file:///D:/eab-wt/g6h/review/logs/full_suite.junit.xml) · [命令/计时元数据](file:///D:/eab-wt/g6h/review/logs/full_suite.json)。

本轮未安装依赖，未创建/切换 worktree，未执行 commit/checkout/reset/stash/branch 等 Git 写操作。给定工作树的 fresh HEAD 是验收对象。`--basetemp` 位于本树 `review/tmp/full_suite`；没有向只读的 g6f 树写临时文件。测试命令从审查开始即启动，后续分镜核验与其并发；串行指 pytest 的测试执行方式，不把耗时当性能基准。

终态逐字节核对：**1910个已跟踪文件SHA-256全部不变，HEAD不变**；`git status --short` 仅 `?? review/`。

基线：[1910 项原始 SHA 清单](file:///D:/eab-wt/g6h/review/baseline.json)；终态：[完整性核对](file:///D:/eab-wt/g6h/review/notes/final_integrity.json)。变异在 `review/copies/` 副本，或仅替换独立子进程内的真实被测函数并 `finally` 恢复；每处写盘变异有原字节恢复 SHA，进程内变异有原树源码前后 SHA。所有报告、脚本、日志及临时产物仅在 `review/`。

## 3. 确认发现表

| ID | severity | file:line | 一句话结论 | 复现/主审日志 |
|---|---|---|---|---|
| G6H-01 | major | `src/eab/kernel2d/entrance.py:110` | 凹体紧配内缝位于 topological int(E)，却被首入 API 当成 t=0 的边界首入。 | [脚本](file:///D:/eab-wt/g6h/review/repro/geom2_tight_fit_initial_state.py) / [输出](file:///D:/eab-wt/g6h/review/logs/root_final_G6H-01.log) |
| G6H-02 | major | `src/eab/kernel3d/frozen.py:209-215; src/eab/kernel3d/interlock.py:352-370; src/eab/margin.py:571-572` | 冻结盖将已舍入的单位法向重新当精确数据，切向大杠杆污染 gap/导数，零种子 Dual 还能改变逃逸高度 primal。 | [脚本](file:///D:/eab-wt/g6h/review/repro/geom3_frozen_gap_tangent_cancellation.py) / [输出](file:///D:/eab-wt/g6h/review/logs/root_final_G6H-02.log) |
| G6H-03 | major | `src/eab/kernel3d/geom3.py:324-326` | dihedral_turn 先分别舍入面单位法向，将合法 binary64 四面体可表达的正转角清成0。 | [脚本](file:///D:/eab-wt/g6h/review/repro/geom3_dihedral_turn_rounding.py) / [输出](file:///D:/eab-wt/g6h/review/logs/root_final_G6H-03.log) |
| G6H-04 | major | `src/eab/limit.py:112-120` | 公开 wrench helper 对有限输入先算溢出乘积再相减，最终可表达的零力矩却静默返回NaN。 | [脚本](file:///D:/eab-wt/g6h/review/repro/root_wrench_intermediate_range.py) / [输出](file:///D:/eab-wt/g6h/review/logs/root_final_G6H-04.log) |
| G6H-05 | major | `tests/test_invariance_geom.py:325-329` | 迁移后的 facet 完整性 oracle 先调用被测 exact_convex_view，真实漏极点可让新门同错全绿，而旧断言报红。 | [脚本](file:///D:/eab-wt/g6h/review/repro/docs_canonical_oracle_dropvertex.py) / [输出](file:///D:/eab-wt/g6h/review/logs/root_final_G6H-05.log) |
| G6H-06 | major | `src/eab/kernel3d/g03.py:209-210; src/eab/margin.py:343-346` | 非凸距离完整性门在atol=0仍用坐标噪声地板验收，平移后可吞真实漏盖导致的10倍错误距离。 | [脚本](file:///D:/eab-wt/g6h/review/repro/geom3_g0_coordinate_noise_blind.py) / [输出](file:///D:/eab-wt/g6h/review/logs/root_final_G6H-06.log) |


### G6H-01 · major

**位置**：`src/eab/kernel2d/entrance.py:110`。

**具体输入 → 错误输出**：U=[(-1,-1),(2,-1),(2,2),(1,2),(1,0),(0,0),(0,2),(-1,2)]；A=[(0,1/2),(1,1/2),(1,3/2),(0,3/2)]；x0=(0,0),d=(0,1)。独立矩形并证明 E=[-2,2]×[-5/2,3/2]，x0 严格在 E 内；按模块初态合同应走 exit 策略，实际 entrance/t_exact=0。沿+y的真正边界为3/2。不是要求局部 shortest_exit 解一般凹体的全局 PD。

**可直接运行**：

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; python -X utf8 D:\eab-wt\g6h\review\repro\geom2_tight_fit_initial_state.py
```

**主审实跑输出关键字段整理（退出0）**：

```text
x0_in_topological_interior=true
actual.kind='entrance', actual.t_exact=0
independent first boundary along +y=3/2
```

完整原样stdout/stderr在 [日志](file:///D:/eab-wt/g6h/review/logs/root_final_G6H-01.log) 与机读 verified_output。

**建议修复（未实施）**：用可认证的局部补集/拓扑判定区分 E 真边界与仅两体内部不交的紧配缝；增加独立矩形并 oracle 的初态 kind 门。若此 API 不支持该类输入，应清晰拒收并同步合同，不能将内点标成 ∂E。

### G6H-02 · major

**位置**：`src/eab/kernel3d/frozen.py:209-215; src/eab/kernel3d/interlock.py:352-370; src/eab/margin.py:571-572`。

**具体输入 → 错误输出**：精确3-4-5旋转的两区间盒，切向跨度M=1e20，真实最近VF间隙1：body_distance=1，冻结裕度gap=6662.338147750939；互换3/5和4/5后gap=-6660.338147750939。切向种子(-8e19,6e19,0)真导数0，实得4440.892098500626。M=1e8,gap=1e-9实得7.66133814775094e-9。另斜面nz=4/5的已选最短出口VF，普通标量lift精确5/8，改零种子Dual offset后primal=-8326.047684688674。

**可直接运行**：

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; python -X utf8 D:\eab-wt\g6h\review\repro\geom3_frozen_gap_tangent_cancellation.py
```

**主审实跑输出关键字段整理（退出0）**：

```text
body_distance=1.0; frozen_gap=6662.338147750939
swap rotation components: frozen_gap=-6660.338147750939
tangent_derivative=4440.892098500626; expected=0
plain lift=5/8; zero-seed Dual primal=-8326.047684688674
```

完整原样stdout/stderr在 [日志](file:///D:/eab-wt/g6h/review/logs/root_final_G6H-02.log) 与机读 verified_output。

**建议修复（未实施）**：从原始特征的精确未归一化法向/相对向量构造 signed gap 及其 jet，最后才除范数/舍入；逃逸高度的标量与Dual走同一精确比值模型。增加大切向杠杆、符号交换及零Dual种子 primal 等价门。

### G6H-03 · major

**位置**：`src/eab/kernel3d/geom3.py:324-326`。

**具体输入 → 错误输出**：O=(0,0,0),Z=(0,0,1),C=(-M,M+1,0),D=(M-1,-M,0)，M=1e8。全部坐标是精确binary64整数、闭合外向四面体、volume=1/6、manifold_issues=[]。沿实际面遍历方向的精确三重积为1，dot=2M²，真角atan(1/(2M²))=5e-17；dihedral_turn((0,1))返回0。M=1e9、1e12、2^50同样丢正角。is_convex/reflex_edges另走精确符号，未据此声称其错误。

**可直接运行**：

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; python -X utf8 D:\eab-wt\g6h\review\repro\geom3_dihedral_turn_rounding.py
```

**主审实跑输出关键字段整理（退出0）**：

```text
M=100000000; expected_angle=5e-17; actual_angle=0.0
signed_volume=0.16666666666666666; convex=true; issues=[]
```

完整原样stdout/stderr在 [日志](file:///D:/eab-wt/g6h/review/logs/root_final_G6H-03.log) 与机读 verified_output。

**建议修复（未实施）**：用未归一化的精确法向和棱向量形成 atan2 的同次齐次参数，最终缩放/舍入；不可先舍入两单位法向再相减或叉积。增加薄但非退化四面体的正角与反向面符号门。

### G6H-04 · major

**位置**：`src/eab/limit.py:112-120`。

**具体输入 → 错误输出**：dim=2或3；force=point=(1e160,...),origin=0，另测1e200。每个输入有限binary64，独立Fraction叉积的每个力矩严格0，最终力/矩全可表达。实际返回[force...,nan...]且不抛异常。这里是公开构造helper的错误，不声称有理LP求解器吞NaN后静默给错承载比。

**可直接运行**：

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; python -X utf8 D:\eab-wt\g6h\review\repro\root_wrench_intermediate_range.py
```

**主审实跑输出关键字段整理（退出0）**：

```text
dim=2, scale=1e160: expected=[1e160,1e160,0]; actual=[1e160,1e160,nan]
dim=3, scale=1e200: expected moments=[0,0,0]; actual moments=[nan,nan,nan]
raised=false
```

完整原样stdout/stderr在 [日志](file:///D:/eab-wt/g6h/review/logs/root_final_G6H-04.log) 与机读 verified_output。

**建议修复（未实施）**：按给定输入精确形成力臂及叉积，最终只舍入可表达结果；至少必须对中间/最终非有限构造响亮拒绝，不能返回NaN。加力与力臂共线、乘积中间越界但最终抵消的2D/3D门。

### G6H-05 · major

**位置**：`tests/test_invariance_geom.py:325-329`。

**具体输入 → 错误输出**：tetra_box_vv/generic两格，rot=0,tmag=1000,s=1。正常新旧门都PASS；在 exact_convex_view 原编号保留分支内部对len>=8、|coord|>100的体删最后一个真实极点并缓存错误凸视图。当前迁移门两格仍PASS；从b6126cf取出的旧同名函数两格均在完整facet标签集合不变断言AssertionError。副本恢复SHA已核。另一仅错置源面编号的变异也为新门3绿、旧门3红。只声称该迁移门失牙，不声称9851门全逃逸。

**可直接运行**：

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; python -X utf8 D:\eab-wt\g6h\review\repro\docs_canonical_oracle_dropvertex.py
```

**主审实跑输出关键字段整理（退出0）**：

```text
BASELINE tetra_box_vv/generic: new_gate=PASS, old_gate=PASS
MUTANT tetra_box_vv/generic: new_gate=PASS, old_gate=AssertionError
old assertion: complete local facet label set invariance
copy source restored SHA256=cded18523b434090da3858ac3213d340f16b6d54570b0d8c69d65a1c585254e5
```

完整原样stdout/stderr在 [日志](file:///D:/eab-wt/g6h/review/logs/root_final_G6H-05.log) 与机读 verified_output。

**建议修复（未实施）**：oracle从保存的原始坐标独立构造凸包/支撑集合，不经过被测凸视图；另独立核源编号保留条件。稳定纯平移格保留旧完整标签断言，配删真实极点与源编号错置两类内部变异。

### G6H-06 · major

**位置**：`src/eab/kernel3d/g03.py:209-210; src/eab/margin.py:343-346`。

**具体输入 → 错误输出**：q=ulp(1e8)=1.4901161193847656e-8；A为center(T,T,T),half=q的盒；B为两个half=q盒的并，中心(T,T,T-3q)与(T+12q,T,T)。独立区间并距离严格q。只在真实 _outside_dot_band 内部注入拒绝z向盖；T=0时margin报missed nearest pair、G0红，T=1e8时margin返回10q且G0(radius=0,samples=1,tol=0,atol=0) passed=True,err=9q,failures=[]。样本实际核了，oracle正确，错距离不是见证显示舍入。源码仅进程内函数替换并finally复原，tracked字节SHA前后相同。

**可直接运行**：

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; python -X utf8 D:\eab-wt\g6h\review\repro\geom3_g0_coordinate_noise_blind.py
```

**主审实跑输出关键字段整理（退出0）**：

```text
T=0: mutant public_error="... missed the nearest pair"; G0 passed=false
T=1e8: truth=1.4901161193847656e-08; mutant distance=1.4901161193847656e-07
G0 samples=1, worst_abs_error=1.341104507446289e-07, passed=true, failures=[]
tracked SHA256 before=after=cf1158aac4906379c66efe1c15a676c61a3c1f254c2195032df3a8f0320ee9cb
```

完整原样stdout/stderr在 [日志](file:///D:/eab-wt/g6h/review/logs/root_final_G6H-06.log) 与机读 verified_output。

**建议修复（未实施）**：将精确盖平方距/最近特征完备性票与浮点见证构造误差票分开；前者不加global-coordinate噪声地板，后者保留清晰的显示误差口径。增加同一内部删盖缺陷在原点/工程坐标/短特征下都须红的门。


## 4. 第七轮 11 条：原脚本与正确值重放

原复现脚本均复制到本树 [repro 目录](file:///D:/eab-wt/g6h/review/repro/) 后运行；保留原“应出现缺陷”的断言，另存正确值增强版本，不篡改原缺陷证明使其假绿。10/11 原共用脚本先在已删 GAP3 旧句处退出，故另核优先性撤回及当前凹 G0 oracle，不能声称原脚本已逐句走到末尾。

| 原编号 | 现行实际输出/增强核验 | 处置 |
|---|---|---|
| G6G-01 | 首出口 `1/2`；baseline `samples=1,passed=True`；内部删除有效出口盖后 `samples=1,passed=False,worst_witness=inf` | 已修 |
| G6G-02 | minsubnormal VV normal=`(sqrt(.5),sqrt(.5))`, gap=q；Fraction 次正规差 normal=`(.9499506873676175,.31239989047659905)`, gap=2q；最终范围不可表达时响亮 OverflowError | 已修 |
| G6G-03 | 不可表达 char_length 响亮异常；巨大 L 的 distance/exit 正常通过，内部删盖两路均 `passed=False`，不再 `inf>inf` 漏检 | 已修 |
| G6G-04 | 源非平面面环、显式三角化同一表面、独立下界均为 `2.0`，不再 sqrt(6) | 已修 |
| G6G-05 | 精确面积 `29q/20` 最终报告 q；不可表达非零面积响亮拒绝；facet/support gap 的精确中点核验均 q | 已修 |
| G6G-06 | `gap=1e-9,translation=1e8` 虽 display 两点相同，normal仍 `(0,0,-1)`；精确3-4-5旋转 normal=`(-.8,0,-.6)`、distance=`2e-8` | 已修 |
| G6G-07 | 876 个幂导数格 `silent_wrong=0,loud_refusals=0`；2^200,p=-5,seed=x 的导数 `-4.666318092516094e-301`，与精确值同 hex | 已修 |
| G6G-08 | 极端长薄盒 volume=`1.9279358920823073e-180`、centroid=0；四面体循环移面环前后 volume=`4.0165331085048066e-182` | 已修 |
| G6G-09 | 空腔仍 `rho=1/8,PD_closed=19/8`；当前合同明确六轴仅证 rho≤w，不再承诺 PD_closed≤w | 已修（命题订正，非几何反例消失） |
| G6G-10 | 原脚本 StopIteration（旧坏句不存在）；具名当前门及禁用生产 polygons_overlap 的独立 G0 真运行通过 | 已修 |
| G6G-11 | 当前 README/AGENTS/canon 撤回“第一份/首次”优先性，07 旧句列为只读正本矛盾；具名门实际通过 | 已修 |

完整命令、原脚本退出码、正确值输出在 [回归台账](file:///D:/eab-wt/g6h/review/G6H_regression_replay.json)；主审再次运行全部增强核验的 [原样输出](file:///D:/eab-wt/g6h/review/notes/root_g6g_augmented_runs.json)。本轮新发现不是把上述同一原始格重报“未修”；它们是同类扫描漏网、不同构造或不同看护路径。

## 5. R7FIX“全仓同类扫描”的再审

| 历史问题类 | 当前检查与结论 |
|---|---|
| 可变缓存、别名 | 几何 cache 同步签名、tuple/Fraction 内容键、凸视图副本、法向/边表返回值、Dual内容检查；未确认新串用。测试有限输入不能代替所有对象生命周期证明 |
| 隐式噪声带/浮点 oracle | 默认精确成员及窗口分支已区分；**G6H-06** 的完备性验收仍被坐标地板吞错；**G6H-05** 的 expected 模型来自被测凸化 |
| 构造量先舍入、先平方再相减 | 原面积/体积/EE法向/二维VV格已修；**G6H-02/03/04** 分别仍先舍入法向、先舍入两法向、先溢出乘积 |
| 快路只查输入不查派生量 | 原 Dual 幂 876 格正确，当前整数导数走 Fraction；新过滤/AD 压力无失配。**G6H-04** 是另一个未保护派生中间量的公共 helper |
| oracle 只查区间中点 | R7 二维出口 oracle 事件本身已查，真 pinch 1/2 与假内缝3/2区分正确；但相同 topological int(E) 口径没扩散到首入初态，见 **G6H-01** |
| 特征尺度上溢使门失效 | 原二维 G0 缺盖/非有限格均红；本轮另找到 **G6H-06** 的大平移、短特征漏盖失牙，不是原 inf>inf 格复发 |
| 暴力真值漏特征 | 原三维源折面内部棱遗漏已修；新 oracle 的实际表面几何与源锚平面明确分开。未确认新的同类漏特征静默反例 |
| 文档优先性主张 | 本地正本谱系及当前文本核对后，未确认残留“本仓首个实现”的现行承诺；07只读旧句如实登记，不代改正本 |

## 6. 新代码细审：`d44dd78..HEAD -- src tests`

本轮 diff 含 **14 个 src 文件、14 个 tests 文件**。分镜与主审合计逐 hunk 阅读；没有只读修复报告就认定实现正确。[完整 diff](file:///D:/eab-wt/g6h/review/logs/r7_diff.patch) · [逐文件分工/结论](file:///D:/eab-wt/g6h/review/notes/r7_change_coverage.json)。

| 改动族 | 阅读与核验 |
|---|---|
| kernel2d covers/entrance/g0/g0_oracle/geom | 精确bbox平方、窗前拒绝、精确norm/unit、事件局部外扇区；原3条全部子格、639次独立配置障碍出口对拍；新增 tight-fit 初态遗漏在未改初态行 |
| kernel3d covers/geom3/frozen/g03 | 精确面积/质量矩、实际三角片棱、相对方向、最后舍入；原4条正确值重放；新增冻结、二面角构造与G0验收漏网 |
| exact_sweep/interlock/margin | rho/PD订正、raw比值、见证精确法向；窗口96格与原空腔；零Dual种子暴露 frozen 旧路径仍影响 lift |
| dual/limit | 幂整数导数 Fraction、norm最终开方；876旧幂格及22460新AD格；力学证书压力与公开wrench漏网 |
| 新8个 test_r7fix 文件 | 检查断言目标、原子格、非有限/内缺陷门及文档具名门，不把文件存在当牙 |
| e5a_cover_oracle / integer_arithmetic 等6个旧测试改写 | 数学模型与源面编号区别、完整标签/精确方向附加断言、冻结导数中点平方oracle、新旧 margin 内部漏盖牙；本轮R7小改未确认新弱化 |

**历史 E2–PERF 迁移门**另审 `b6126cf..HEAD -- tests`。确认 G6H-05 是“旧断言能抓而新门漏掉”的实例。其他已做真实内部变异：二维VV强制active、段内偷偷加带、facet gap反号、删除事件检测；多体unbounded screen关闭、对偶功率尺度宽放；均红在目标断言而非偶然顶点选择。不是对每种历史门做了所有可能变异，范围限制见第10节。

## 7. 九镜头覆盖及独立验证

### 7.1 精确性声称与浮点分支

全 `src/eab` 33个Python模块由分镜/主审逐文件读；AST关键词候选315项包含重复、字符串状态和非数值分支，**不冒称315项都是浮点答案裁决**。去重后逐项按显式域窗、显示/可分辨性、保守过滤+精确兜底、历史adapter正规化、精确谓词、缺陷分类。[原始候选](file:///D:/eab-wt/g6h/review/notes/whole_src_branches.json) · [合并分类](file:///D:/eab-wt/g6h/review/notes/branch_classification_all.json)。

LP浮点相、主元/比值/约简成本阈值仅给候选；`_Exact.certify` 验原始/对偶可行、Farkas或下降射线，未通过转有理单纯形。Dual普通指数快路取消不可靠抵消、退原始Fraction；几何orient/dot/cross过滤有原数据Fraction符号兜底。active及可分辨性阈值是显示，不代替完整lambda证书。legacy reader重复顶点正规化是明示adapter模型，不能拿它当纯精确几何oracle。

答案缺陷/门缺陷已逐项实例化（G6H-01至06），不存在仅凭 grep 出数字就报缺陷的条目。

### 7.2 过滤、范围、缓存

主审新种子8101226：10000个orient、10000个双线性符号、22460个可表达AD通道（指数含次正规、上溢派生范围、混合Fraction），独立Fraction对拍零错；不将普通fast AD数值近似误写成正确舍入定理。另重放1500 orient3d、4000混合二维过滤、1500 rational3公式及8000 LP pricing格。数学推导检查与有限格搜索结合，**没有形式验证所有binary64误差界**。[主审新压力](file:///D:/eab-wt/g6h/review/notes/root_current_filters_and_dual.json)。

三维缓存内容/返回别名、二维内容键已查；未确认新缓存串用。无缺陷结论仅限实际读取路径与样本；不意味着外部非法可变对象/并发用法均获证明。

### 7.3 oracle独立性

二维SAT/支撑/独立gift-wrap及g0_oracle的绕数/段距离/事件核；三维g03_exact、g03_surface_oracle及E5系列主oracle的Newell/Gram/Gordan/扫掠SAT核分别核查。共同原始坐标与Fraction不是共用几何。PERF reference直接复用生产几何的路径只作旧路径等价佐证，不能作为主真值。**G6H-05** 表明即使后段support_labels独立，前段模型来自被测凸化仍违反纪律A。

### 7.4 门的强度与迁移

严格区保持不变量，易变边界改为对各份实际数据独立精确核对，并另设精确仿射变换门；没有以“可能随舍入变”无条件放过实际状态。主审/分镜核过的内部变异详情在二维、三维、文档覆盖与 [LP门变异台账](file:///D:/eab-wt/g6h/review/notes/root_lp_gate_mutations.json)。确认两条漏检：共享凸化 expected、坐标噪声吞漏盖。未证明它们能逃过整个9851套，故只报实际被证明的门范围。

### 7.5 几何正确性压力

二维自写Fraction product-cell SAT、矩形配置障碍并、段投影：480成员+480一般重叠+413距离+413外首入+34距离G0+6出口G0，L/U、精确3-4-5旋转、平移0/1e8、尺度2^(-600,-30,0,30,600)，零错；另外639个拓扑出口对拍零错。新紧配缝只破坏首入初态，不破坏R7更新的独立 ray_exit oracle。

三维自写Fraction区间oracle **36/36通过**：3个精确正交姿态 × 尺度1e-9/1/1e9 × 平移0/1e3/1e6/1e8；最小真间隙1e-15。成员、距离、法向、delta三态、首入exact_t、出口及E成员均核；另95项定向门通过。这是预定构造族，不是任意凹闭表面穷举。[脚本](file:///D:/eab-wt/g6h/review/repro/geom3_independent_interval_pressure.py) · [输出](file:///D:/eab-wt/g6h/review/logs/geom3_independent_interval_pressure.log)。

### 7.6 接触窗口

按当前合同审，而不是沿用已撤回的PD命题：六个精确轴平移只证明 **rho≤w**（内部不交平移长度下确界）；星核证明每个重叠区在径向厚度≤w的壳内，不是整体PD_closed。独立区间积96格：63分离、7相触、26贯入，尺度2^-80/1/2^40、平移含1e8及非对称半宽，逐model核角点、同胚收缩、径向上界和public状态全绿。原薄壳倍窗/唯一证书删除内部牙及空腔rho/PD反例均运行。没有确认新的窗口可靠性反例；明确不保证旋转不变、斜向脱离完备或任意凹体全局E。

### 7.7 极限分析

180个小有界LP，以独立高斯消元/顶点目标oracle对拍，浮点候选与强制有理路径的exact_x/exact_y一致；浮点视图等于声明的最终转换，未找到NaN/错状态。8000定价符号格零错。

单/多体2D独立闭式容量60格，分界摩擦、非对称荷载/参考位置、几何与荷载分别缩放；180单体+180多体错误alpha/lambda/mechanism全部拒绝。4个真实调用LP候选污染（float_alpha、Fraction_alpha、exact_x、exact_y）全部拒绝。G6E23变异4个可分辨性格在目标resolved/nearby_infeasible断言红；G6E47变异在10^-9/10^-30/10^-100负功率的admissible断言红。可分辨性采用逐体/逐尺度报告，不将其当答案资格。

**G6H-04** 仅针对公开wrench构造helper；内部精确LP模型和候选自校验不能免除公共helper的NaN错误。[力学压力脚本](file:///D:/eab-wt/g6h/review/repro/root_limit_guard.py) · [LP独立对拍脚本](file:///D:/eab-wt/g6h/review/repro/root_lp_audit.py)。

### 7.8 文档/代码/正本

完整读README、AGENTS、exact_predicates_plan、exact_3d_design、canon_map，以及本地只读00/01/03/07。42处候选claim行逐行登记测试文件/判定；没有指向不存在的测试文件，但“文件存在”和“全套绿”不是全部子声称的证明。具名门的实际断言、已实跑/只静态核/历史陈述/未独立复算分别在 [claim清单](file:///D:/eab-wt/g6h/review/agents/docs_gates/claims_inventory.json)。G6H-01/03反驳当前API文字承诺；G6H-05/06反驳相应完整性门的强度。

canon第八节当前已如实列出：读取器并非六种，canonical_order_key序维护缺失，FF/FE标签不等于CoverType产出，G1未核锁态/滑动符号，G2手写清单而非检测器，G5未开，Phase0是JSON往返非原件逐字节，G4仅三份dump且无预注册阈值/迭代次数。只读外部DDA4.x源码再次核到逐闭合接触TSV导出；未执行外部solver。优先性只是按本地正本核当前措辞，未查外部出版物的新进展。

### 7.9 第五轮原始50条重放

去重重放 **37 / 50 条**，超过工单至少20条要求；另有DDA4.x只读原源码核验（不重复计编号1）。编号为原raw列表的1-based位置。数值原输入/等价复现与文档订正分别列出，不把“承诺缩小”写成“功能已实现”。

| 原编号 | 本轮处置 | 证据来源 |
|---|---|---|
| G6E-01 | 文档订正；DDA4.x读取器仍未实现 | [docs_gates](file:///D:/eab-wt/g6h/review/agents/docs_gates/g6e_replay.json) |
| G6E-04 | 文档订正；canonical_order_key和三维CoverType退化产出仍未实现 | [docs_gates](file:///D:/eab-wt/g6h/review/agents/docs_gates/g6e_replay.json) |
| G6E-05 | 文档订正且边界跳样已修；普遍±ε双侧构造仍未实现 | [docs_gates](file:///D:/eab-wt/g6h/review/agents/docs_gates/g6e_replay.json) |
| G6E-06 | 文档订正；正本03仍未回写新口径 | [docs_gates](file:///D:/eab-wt/g6h/review/agents/docs_gates/g6e_replay.json) |
| G6E-09 | 已修 | [root](file:///D:/eab-wt/g6h/review/notes/root_replay_runs.json) |
| G6E-10 | 已修 | [docs_gates](file:///D:/eab-wt/g6h/review/agents/docs_gates/g6e_replay.json) |
| G6E-11 | 已修 | [root](file:///D:/eab-wt/g6h/review/notes/root_replay_runs.json) |
| G6E-14 | 已修 | [docs_gates](file:///D:/eab-wt/g6h/review/agents/docs_gates/g6e_replay.json) |
| G6E-15 | 文档订正；未重跑历史提交整套 | [docs_gates](file:///D:/eab-wt/g6h/review/agents/docs_gates/g6e_replay.json) |
| G6E-16 | 文档订正；首入只称第一版，不称完整 | [docs_gates](file:///D:/eab-wt/g6h/review/agents/docs_gates/g6e_replay.json) |
| G6E-17 | 文档订正；Cover3/ContactRecord退化类型产出仍未实现 | [docs_gates](file:///D:/eab-wt/g6h/review/agents/docs_gates/g6e_replay.json) |
| G6E-18 | 文档订正；07规模/判据缺口仍未完成 | [docs_gates](file:///D:/eab-wt/g6h/review/agents/docs_gates/g6e_replay.json) |
| G6E-19 | 已修（现有溯源条目和4份差异文字）；未重新导出 | [docs_gates](file:///D:/eab-wt/g6h/review/agents/docs_gates/g6e_replay.json) |
| G6E-20 | 已修 | [root](file:///D:/eab-wt/g6h/review/notes/root_replay_runs.json) |
| G6E-21 | 已修 | [root](file:///D:/eab-wt/g6h/review/notes/root_replay_runs.json) |
| G6E-22 | 已修 | [root](file:///D:/eab-wt/g6h/review/notes/root_replay_runs.json) |
| G6E-23 | 已修（目标内部变异门有牙） | [root](file:///D:/eab-wt/g6h/review/notes/root_lp_gate_mutations.json) |
| G6E-25 | 已修 | [geom3](file:///D:/eab-wt/g6h/review/agents/geom3/g6e_replay.json) |
| G6E-26 | 已修 | [geom2](file:///D:/eab-wt/g6h/review/agents/geom2/g6e_replay.json) |
| G6E-27 | 已修 | [geom2](file:///D:/eab-wt/g6h/review/agents/geom2/g6e_replay.json) |
| G6E-29 | 已修 | [geom3](file:///D:/eab-wt/g6h/review/agents/geom3/g6e_replay.json) |
| G6E-30 | 已修 | [geom2](file:///D:/eab-wt/g6h/review/agents/geom2/g6e_replay.json) |
| G6E-31 | 已修 | [geom3](file:///D:/eab-wt/g6h/review/agents/geom3/g6e_replay.json) |
| G6E-32 | 已修 | [docs_gates](file:///D:/eab-wt/g6h/review/agents/docs_gates/g6e_replay.json) |
| G6E-33 | 已修（现有48条条目）；未重新导出 | [docs_gates](file:///D:/eab-wt/g6h/review/agents/docs_gates/g6e_replay.json) |
| G6E-36 | 已修旧隐式带机制；当前边界变动不按理想不变性计错 | [docs_gates](file:///D:/eab-wt/g6h/review/agents/docs_gates/g6e_replay.json) |
| G6E-37 | 已修 | [geom3](file:///D:/eab-wt/g6h/review/agents/geom3/g6e_replay.json) |
| G6E-38 | 已修 | [geom2](file:///D:/eab-wt/g6h/review/agents/geom2/g6e_replay.json) |
| G6E-40 | 已修 | [geom3](file:///D:/eab-wt/g6h/review/agents/geom3/g6e_replay.json) |
| G6E-41 | 已修 | [geom2](file:///D:/eab-wt/g6h/review/agents/geom2/g6e_replay.json) |
| G6E-42 | 已修 | [geom3](file:///D:/eab-wt/g6h/review/agents/geom3/g6e_replay.json) |
| G6E-43 | 已修 | [geom3](file:///D:/eab-wt/g6h/review/agents/geom3/g6e_replay.json) |
| G6E-44 | 已修 | [geom3](file:///D:/eab-wt/g6h/review/agents/geom3/g6e_replay.json) |
| G6E-45 | 已修 | [root](file:///D:/eab-wt/g6h/review/notes/root_replay_runs.json) |
| G6E-47 | 已修（目标内部变异门有牙） | [root](file:///D:/eab-wt/g6h/review/notes/root_lp_gate_mutations.json) |
| G6E-49 | 已修 | [geom2](file:///D:/eab-wt/g6h/review/agents/geom2/g6e_replay.json) |
| G6E-50 | 已修 | [docs_gates](file:///D:/eab-wt/g6h/review/agents/docs_gates/g6e_replay.json) |

未重放：G6E-02, G6E-03, G6E-07, G6E-08, G6E-12, G6E-13, G6E-24, G6E-28, G6E-34, G6E-35, G6E-39, G6E-46, G6E-48。每条具体输入、断言、状态依据、运行输出及限制在 [回归台账](file:///D:/eab-wt/g6h/review/G6H_regression_replay.json)。不以脚本exit0自动判修复；例如G6E40原先float差点的hull不是精确差点模型，已另核Fraction先作差的默认facet_vote严格结果 `(0,6,0,0,[])`。

## 8. 未确认（不计数）

- 测试独立overlap只查整边中点是否可漏局部内段：300000随机三角/方块独立SAT探索未复现，未证明一般凹体完备。
- 二维首入说明称查所有相邻区间中点，代码检查全部事件但只检查最后中点：尚无改变答案的反例，不能仅凭实现文字不同报数学缺陷。
- canon旧砖二行“7/8均未实现”与当前7第一版表述：有明确历史HEAD背景，留作残留说明；未证现行核心承诺错误，不计minor。
- 未确认新的cache/别名、float符号过滤、精确LP证书、rho/薄壳可靠性反例。这里是有限搜索结论，不是“不存在”的证明。

## 9. 可复跑证据入口

6条确认发现一次重放（每条0退出、每条日志分存）：

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONIOENCODING='utf-8'
python -X utf8 review/repro/root_finalize_findings.py
```

这是确认反例/门缺口的审查脚本，不是修复或验收通过脚本。[逐条脚本/日志/副本目录链接清单](file:///D:/eab-wt/g6h/review/README.md)。分镜覆盖：[二维](file:///D:/eab-wt/g6h/review/agents/geom2/coverage.md) · [三维](file:///D:/eab-wt/g6h/review/agents/geom3/coverage.md) · [文档/窗口/oracle](file:///D:/eab-wt/g6h/review/agents/docs_gates/coverage.md) · [三项交叉裁决](file:///D:/eab-wt/g6h/review/agents/geom2/adjudication.md)。

## 10. 完整性批评

1. **src模块没有团队层面的未读文件**：33个Python文件按分工全读；不是每个分镜都独立全文读全部文件。主审全读dual/LP/limit/limit_multi/构造/谓词/rational3/ContactRecord/readers；二维分镜全读kernel2d；三维分镜全读kernel3d与margin；文档分镜复核主oracle/窗口/理论。细节范围见分镜覆盖。
2. **没做全仓形式证明**，也未穷举全部binary64、一般凹多面体、所有退化组合。有效输入前提、不同API的凸包/表面/源锚平面模型不能互相替代。
3. 新R7的28个src/tests文件全部hunk已读；历史E2–PERF迁移仅对报告台账/相关文件做静态核及选定真实变异，**没有对每个旧门逐一穷尽变异**。未逐行重新阅读全部未改测试和所有PERF reference代数；主审跑全套不能补成形式独立性证明。
4. README/canon中的所有历史数字、G3全部收敛率与工程意义、外部solver行为、性能记录没有逐一独立复算；claim清单明确这些范围。不把test存在/全套运行冒称每句自然语言已证明。
5. G6E只重放本报告登记的原条目/等价条目，未重放余项，不把37项关闭外推为50项全关闭。文档订正只解除错误承诺，不证明未实现功能已补齐。
6. 只读正本及姊妹仓库未改、未运行姊妹exe；没有学术优先性/工程标定/生产可靠性认证。本次是数学软件审计，不是上述验证。
7. 6条发现的有限范围、内部注入位置、目标断言、主审实跑及恢复SHA均已给出；仍须实现方修复并进行下一轮独立确认。**9851项全绿不能解除本轮6条major。**

G6H_DONE critical=0 major=6 minor=0
