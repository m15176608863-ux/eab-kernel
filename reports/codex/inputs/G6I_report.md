# WO-G6I：G6 第九轮独立正确性复审

## 1. 结论

被审新鲜 detached 工作树：`D:\eab-wt\g6i`，HEAD **`9f99025232450dc70b4e442b173badc3f9e55727`**。审查日期：2026-10-12。角色：**独立审查，不修代码**。

**确认：0 critical / 4 major / 2 minor。M0 不可以退出。** 四条 major 分别是二维有限盖域、三维折面凸性、次正规锥裕度构造、微尺度距离 oracle 漏检。每条已由主审 root 自己运行复现，去重后计数；没有把子审查的未复现意见直接入账。

第八轮 **6 条原发现均确认已修**，不将新同类实例回填为“原条未修”。全套自跑 **10100 passed，0 skipped / failure / error**，但全绿不能替代 G6 退出判据。本轮没有确认新的静默成员/LP承载结果 critical；这不是全输入正确性的形式证明。

- [机读发现及完整运行输出](file:///D:/eab-wt/g6i/review/G6I_findings.json)
- [证据与全部产物索引](file:///D:/eab-wt/g6i/review/INDEX.md)
- [全套运行配置与结果](file:///D:/eab-wt/g6i/review/full_suite.json)
- [31 条第五轮重放台账](file:///D:/eab-wt/g6i/review/G6E_replays.md)
- [收尾完整性核验](file:///D:/eab-wt/g6i/review/integrity.json)

### 审查约束

所有脚本、日志、报告、副本仅写 `review/`。被审 tracked 文件、姊妹仓库、其他工作树、理论正本只读；没有 Git 写操作、安装依赖或运行姊妹求解器。副本变异按原字节恢复并核 SHA；进程内变异恢复函数绑定且不写生产源码。开工和收尾逐 tracked 文件 SHA-256 核对，HEAD 未变，`git status --short` 只有 `?? review/`。

## 2. 全套自跑证据

设置 `PYTHONDONTWRITEBYTECODE=1`；Python 3.12，`python -X utf8 -m pytest -q -p no:cacheprovider`。没有安装 xdist：先完整收集 **10100 nodes**，再按**完整测试模块**分为四个独立进程，每个模块恰跑一次。`--basetemp` 位于本树 `review/tmp/full_0` 至 `full_3`，没有把其他工作树的 tmp 用作可写目标。

| 分片 | 实际结果 | 原样日志 / JUnit |
|---|---|---|
| 0 | 2526 passed in 186.91s | [log](file:///D:/eab-wt/g6i/review/logs/full_0.log) / [xml](file:///D:/eab-wt/g6i/review/logs/full_0.xml) |
| 1 | 2525 passed in 543.27s | [log](file:///D:/eab-wt/g6i/review/logs/full_1.log) / [xml](file:///D:/eab-wt/g6i/review/logs/full_1.xml) |
| 2 | 2525 passed in 301.50s | [log](file:///D:/eab-wt/g6i/review/logs/full_2.log) / [xml](file:///D:/eab-wt/g6i/review/logs/full_2.xml) |
| 3 | 2524 passed in 480.60s | [log](file:///D:/eab-wt/g6i/review/logs/full_3.log) / [xml](file:///D:/eab-wt/g6i/review/logs/full_3.xml) |

四片均 exit 0，JUnit 合计 10100，skip/error/failure 全为 0。记录的单调时钟总耗时 **557.04s**，含收集及收尾；不是作者的 xdist 性能复验，也不是串行 1643s 的复跑。四独立进程保留模块内次序，**没有验证单进程跨模块共享状态的相同顺序**。用户工单中的旧 `9851` 数不是本 HEAD 实际收集数。

复跑：`$env:PYTHONDONTWRITEBYTECODE='1'; python -X utf8 review/repro/run_full_suite.py`。该脚本会刷新其 suite 日志和开工 SHA 快照；本轮最终证据另保存在 integrity。 [脚本](file:///D:/eab-wt/g6i/review/repro/run_full_suite.py) / [收集日志](file:///D:/eab-wt/g6i/review/logs/full_collection.log)。

## 3. 第八轮六条回归重放

先保留原“缺陷应成立”脚本，仅调整可写副本/导入路径，在新 HEAD 重跑；然后用另外的正向断言跑完原输入。旧缺陷断言 exit 1 是**该反例不再成立**，不能单凭这点宣布修复，下面同时列正向输出。

| 原发现 | 判定 | root 的实际输出及证据 |
|---|---|---|
| G6H-01 紧配内缝初态 | **已修** | 物理态 0、拓扑 E 态 1；返回 `kind=exit,t_exact=0,gap=0`。不要求这里的局部出口成为一般凹体全局 PD。[原输出](file:///D:/eab-wt/g6i/review/logs/root_R8_01_original.log) / [正向](file:///D:/eab-wt/g6i/review/logs/root_R8_01_positive.log) |
| G6H-02 冻结相消与零 Dual | **已修** | 三格 gap 为 `1,1,1e-9`，切向导数全 0；plain lift=`5/8`，零种子 Dual primal=`0.625`、导数0。[原输出](file:///D:/eab-wt/g6i/review/logs/root_R8_02_original.log) / [正向](file:///D:/eab-wt/g6i/review/logs/root_R8_02_positive.log) |
| G6H-03 薄四面体转角 | **已修** | 六个 M 的角等于独立 `atan(1/(2M²))`；`M=1e8` 得 `5e-17`，不再为0。[原输出](file:///D:/eab-wt/g6i/review/logs/root_R8_03_original.log) / [正向](file:///D:/eab-wt/g6i/review/logs/root_R8_03_positive.log) |
| G6H-04 wrench 中间溢出 | **已修** | 2D/3D × `1e160/1e200`，原独立 Fraction 力矩0；实际所有力矩0、全有限，等于真值。[原输出](file:///D:/eab-wt/g6i/review/logs/root_G6H04_original.log) / [正向](file:///D:/eab-wt/g6i/review/logs/root_G6H04_positive.log) |
| G6H-05 共用 view oracle 无牙 | **已修** | 2格漏极点、3格面号错置：baseline新旧门均PASS；在真实 `exact_convex_view` 内变异，新门分别在“raw-coordinate…lost or reordered extreme vertices / changed source face numbering”红。[原漏点](file:///D:/eab-wt/g6i/review/logs/root_R8_05_dropvertex_original.log) / [原面号](file:///D:/eab-wt/g6i/review/logs/root_R8_05_faceperm_original.log) / [正向漏点](file:///D:/eab-wt/g6i/review/logs/root_R8_05_dropvertex.log) / [正向面号](file:///D:/eab-wt/g6i/review/logs/root_R8_05_faceperm.log) |
| G6H-06 工程坐标地板吞缺盖 | **已修** | 真间隙 `1.4901161193847656e-08`；真实内部拒z盖变异在平移0和1e8都触发 exact squared-distance selfcheck，G0=false、samples=1。SHA before=after。[原输出](file:///D:/eab-wt/g6i/review/logs/root_R8_06_original.log) / [正向](file:///D:/eab-wt/g6i/review/logs/root_R8_06_positive.log) |

这些变异穿过实际被测函数；没有在枚举完的记录后追加假数据。复现脚本见 [repro目录](file:///D:/eab-wt/g6i/review/repro/)；源脚本对应关系及子镜头逐输出见 [二维回放](file:///D:/eab-wt/g6i/review/geom2/replays.json)、[三维回放](file:///D:/eab-wt/g6i/review/geom3/g6h_replay.json)、[门回放](file:///D:/eab-wt/g6i/review/gates_docs/coverage.md)。

## 4. 确认发现表

| ID | 严重度 | 位置 | 一句话结论 | 独立复现 / root运行输出 |
|---|---|---|---|---|
| G6I-01 | major | kernel2d/entrance.py:146–175 | 精确支撑直线根不等于有限盖域，选中域外边、见证不相触。 | [script](file:///D:/eab-wt/g6i/review/repro/geom2_convex_flat_facet_domain.py) / [log](file:///D:/eab-wt/g6i/review/logs/root_confirm_G6I02d.log) |
| G6I-02 | major | kernel3d/geom3.py:464–480；324–325 | 真实折面凹对角线未进入“精确局部凸性”接口。 | [script](file:///D:/eab-wt/g6i/review/repro/geom3_folded_reflex_hidden.py) / [log](file:///D:/eab-wt/g6i/review/logs/root_confirm_G6I03d.log) |
| G6I-03 | major | kernel3d/covers3.py:399–408 | 先舍最近点分量再求norm，清零可表达锥裕度。 | [script](file:///D:/eab-wt/g6i/review/repro/geom3_cone_margin_subnormal.py) / [log](file:///D:/eab-wt/g6i/review/logs/root_confirm_cone_margin.log) |
| G6I-04 | major | tests/e5b_margin_oracle.py:83–84；90–91 | 平方先舍入的独立oracle错拒正确值、接受同类真实路径变异。 | [script](file:///D:/eab-wt/g6i/review/repro/docs_margin_oracle_range.py) / [log](file:///D:/eab-wt/g6i/review/logs/root_confirm_margin_oracle.log) |
| G6I-05 | minor | kernel3d/geom3.py:409–455 | 总正体积掩盖分离的朝内分量，空问题列表的外向认证不成立。 | [script](file:///D:/eab-wt/g6i/review/repro/geom3_manifold_component_orientation.py) / [log](file:///D:/eab-wt/g6i/review/logs/root_confirm_manifold.log) |
| G6I-06 | minor | canon_map:93；README:106；test_invariance_2d:17–22 | 三处现态说明仍说旧的未实现/未经审查/19格豁免口径。 | [script](file:///D:/eab-wt/g6i/review/repro/docs_stale_current_contracts.py) / [log](file:///D:/eab-wt/g6i/review/logs/root_confirm_stale_docs.log) |

### G6I-01：平直链有限域漏查

输入：`A=[(0,0),(1,1),(0,2)]`、`B=[(0,0),(3,0),(3,1),(1,1),(0,1)]`、`x0=(0.5,2), d=(0,-1)`。独立笛卡尔支持关系：t<1时A最低y>1；t=1仅A顶点0在 `(0.5,1)` 接触B边3（x∈[0,1]），边2的x范围[1,3]不能接触。

```text
expected t=1, label=('VE',0,3)
actual   t=1, label=('VE',0,2)
point_a=(0.5,1), point_b=(1,1), gap=0, separation=0.5
tied_labels=(('VE',0,2),('VE',0,3))
```

尺度1、1e-9、1e8及精确3-4-5旋转+平移1e8共四格均错。另平直链矩形合法初触格因错误FF标签抛 `convex entrance face witness has no segment overlap`，同根因去重。平直顶点是允许输入，不能以非法域排除。整体时刻/成员仍正确，按窄域major。

**建议**：获选及并列前精确核VE/EV/FF有限接触域，或正确合并共线支撑并回映真实源特征；不要用垂足clamp掩盖域外标签。加入标签有效、见证同点及尺度/姿态门。

### G6I-02：折面内部凹棱漏特征

单位盒只将顶点6抬至z=3/2，顶部源环(4,5,6,7)声明三角化为(7,4,5)+(5,6,7)。独立实体图是 `0<=z<=1+(1/2)max(0,x+y-1)`。顶点4、6在实体内/边界，而其中点 `(1/2,1/2,5/4)` 在外，直接违反凸性定义；对角(5,7)独立三重积=-1。

```text
P.is_convex(tol=0) = True          expected False
P.reflex_edges(tol=0) = []        expected contains (5,7)
exact_surface(P): False / [(5,7)]
source dihedral(4,5)=1.3258176636680326
actual adjacent-triangle angle=pi/2=1.5707963267948966
```

h=1/2、2^-80，三尺度、两平移、两精确正交帧共24格确认。独立oracle只用height graph与凸性定义，不共享生产triangulator/normal；`exact_surface`结果仅作佐证。

**域界限**：源环本身非平面，旧 `manifold_issues` 会提示；这里的合法性是**声明三角化后闭合、朝外、嵌入的实体**，不是“源面环都是合法平面”。设计明确允许非共面环作为折面；covers源描述符豁免没有限定 `is_convex/reflex_edges` 的“Exact local convexity”声称。二面角只作同根因佐证，不对任意非平面环宣称有单一数学角。显式conv(vertices) API不因此被认定错。

**建议**：实体凸性/凹棱使用声明三角面拓扑；若仅支持平面面环，须清晰拒收和同步契约，不能对已接受折面返回“精确凸”。

### G6I-03：次正规锥裕度提前舍入

d=`2^-1074`，`A=tetra(O,(1,-1,d),(d,1,-1),(-1,d,1))`，B为A反射，顶点索引均0。全部原坐标是有限binary64；行列式d(3+d²)>0。精确正缩放约束的独立投影为 `p=(-d/3,-d/3,-d/3)`：p是三顶点平均且对每个极点q都有p·q=|p|²，因此完整投影证书成立。

`d²/4 < d²/3 < 9d²/4` 以Fraction中点平方证明最终norm最近binary64是d，不是0。

```text
m=1: expected margin=5e-324, actual=0.0
m=2: expected margin=5e-324, actual=1e-323
24 cases, 10 wrong; Boolean cone feasible=True (correct)
```

函数doc承诺constraint hull距离，noise仅报告；范围虽不可分辨，不能把最终可表达标量先分量舍成零。布尔真值不受影响，按major窄构造而非critical。

**建议**：有理p上先求精确norm²，再构造最终标量；不能先 `_float_vector(p)`。补次正规中点证书，不以 `sqrt(float(d²))` 为oracle。

### G6I-04：独立oracle有相同数值缺陷

s=`2^-600`，A=[3s,5s]×[-s,s]²，B=[-s,s]³，独立区间积真距2s可表示。当前production答对；oracle用 `sqrt(float(nearest_squared))` 得0，反而错拒正确值。

变异编译进入真实 `body_distance` / `margin_contacts` 内部构造，保留其有理d²、状态和完整性证书，不伪造返回记录：

```text
baseline production distance=4.819839730205768e-181
baseline helper: AssertionError: default-exact distance construction
internal mutant distance=0.0, contact distances={0.0}
helper on mutant: PASS
old b6126cf scale gate: baseline PASS / mutant AssertionError
```

原旧函数源码只读抽取并在同一新增压力尺度运行，证明旧尺度断言与新helper存在区别；**2^-600不是被删除的历史实际网格**。没有运行该mutant下的全套，不声称10100门全放行。这条是独立真值/门失牙major，不是当前production距离已错。

**建议**：独立test-owned最终根构造或RN-even中点证书；补平方越界但最终根可表达的双侧格，真实路径恢复坏构造必须在目标距离断言红，不能共用生产sqrt。

**同类漏网补充（并入本条，不另计）**：`tests/test_near_parallel_edges.py:62` 的 `exact_seg_seg` 默认显示出口仍是 `sqrt(float(best))`。两单位平行线段间隙 `1e-200`，独立闭式距离与production都是 `1e-200`，该oracle却显示 `0.0`；新 `squared=True` 出口仍给正确精确平方。root亲跑 [复现](file:///D:/eab-wt/g6i/review/repro/geom3_near_parallel_oracle_display.py) / [输出](file:///D:/eab-wt/g6i/review/logs/root_near_parallel_oracle.log)。这是旧已有helper同类范围缺陷，不声称它的新平方证书失牙或另有整套变异逃逸。

### G6I-05 / 06：两条minor

**G6I-05**：两严格分离方体独立有向体积64、-8；整体总56，`manifold_issues(0)=[]`，小朝内分量单独报inward。问题是空列表宣称整个输入朝外。输入不满足核心外向域，故仅诊断minor；修复需考虑空腔嵌套语义，不能一概要求每分量正体积。

**G6I-06**：`canon_map:93`“命题7、8均未实现”与当前命题7门/API冲突；README的“canon未经G6”与同表二至五轮历史核验冲突；二维不变性模块doc仍说旧19格/隐式地板，而现门已逐格精确oracle。这三处同类旧口径合并一minor。砖二自身未实现仍是真的；建议历史状态显式标旧HEAD。静态复现同时检查原文及当前反证，不是仅凭主审意见。

## 5. 同类漏网全仓复查

分支/缓存导航覆盖src/eab全部34个模块，人工阅读公开API与live主路径，并将不确定/未全读范围列末节。名称式AST抽取123个候选决策，二维39、三维及margin71、root其余13条逐项分类，另有两几何组手补20处及root补录。**不是“只检索到123处，故其余没有浮点分支”的证明。** [总导航](file:///D:/eab-wt/g6i/review/branch_inventory.json) / [二维分类](file:///D:/eab-wt/g6i/review/geom2/branches.json) / [三维分类](file:///D:/eab-wt/g6i/review/geom3/branches.json) / [root分类](file:///D:/eab-wt/g6i/review/root_branches.json)。

| 第六至八轮问题类 | 本轮同类复查 / 结果 |
|---|---|
| 冻结闭式、解析jet大坐标/大跨度相消 | G6H02重放；R8 raw-normal/Gram/offset路径细读；Dual向量相消搜索及新冻结各模态门。原条已修，未确认新的jet错。 |
| 首入初态、紧配与仅中点oracle | 二维矩形并、三维区间并；25组全符号室用独立Fourier–Motzkin逐可行室对拍，两层局部步长细读。新G6I01是有限域标签漏检，不与初态修复重复。 |
| 迁移门失牙 | G6H05、G6E08/35/49真实内部变异；旧新AST114函数台账；新增G6I04揭示另一helper盲区。 |
| 可变缓存 / 别名 | 原容器内容signature、fresh view、immutable serialized covers、geometry/offset/window/implementation键；二维源list变更与返回Cover改写测试通过。未确认新串用；未穷举所有删键变异。 |
| 隐式噪声带、float oracle | 默认状态有理比较；显式窗口/nominal报告分开。G6I04确认float expected错。reader重复点地板是明示legacy规范化政策，不冒充raw保真内核。 |
| 构造先舍入 / 先平方再相减 | wrench、shift/twist、frozen offset、面积/质量历史复核；G6I03锥距离标量仍先舍点分量，G6I04oracle仍先舍平方。 |
| 快路只查输入不查派生 | 10000 orientation+10000 dot/cross、2250投影过滤、8000 LP约化成本随机指数格；不确定回落Fraction。未确认新的快路真值不等价。 |
| 特征尺度上溢使门失效 | G6H06精确平方门与工程坐标缺盖变异；polygon尺度2^-1074至2^1000；最终越界响亮错误与错误有限值分开。 |
| 暴力真值漏特征 | G6G04重放；本轮G6I02暴露同一折面内部对角在凸性API仍未使用。共享brute不作独立主oracle。 |
| 文档优先性主张 | 当前canon三层谱系、00相关条目与07偏离逐核；未确认新增priority major。外部只读03/07的陈旧主张已经在canon注册，不修改正本。G6I06是旧现态文案minor。 |

## 6. 新代码细审：30ee153..HEAD

**25文件、1788插入/149删除**。13个生产文件与12个测试文件全部新diff由分工逐行核验，不仅照抄R8FIX报告。[逐文件清单](file:///D:/eab-wt/g6i/review/newdiff_coverage.json)。

| 生产改动 | 审查与验证 |
|---|---|
| kernel2d covers/entrance/exact/geom（4） | 纯有理point-side、cone width同次缩放、triangle-pair切锥并分类与接线；独立多方格并压力。未确认R8初态新算法给错；凸有限域缺口仍在，G6I01。 |
| entrance3 / 新entrance_topology（2） | 精确接触局部平面超集、rank1/2/3球室、两层步长及成员核验；25组完整符号图独立对拍。 |
| frozen | raw jet / 原始normal证书、最终归一化差、offset延后、halfway二分与Dual lift；原G6H02和全部新frozen门。 |
| g03 / g03_surface_oracle（2） | 精确squared证书从辅助显示误差独立出来，漏盖真实路径红；完整表面oracle独立，内部共用校验仅佐证。 |
| geom3 | 新二面角同次构造修复G6H03；仍使用源环，折面对角拓扑遗漏G6I02；出口平方排序不反馈报告带。 |
| interlock / margin（2） | 首入/出口核的精确模型接线，raw frozen证书携带与逐根状态验收；nominal簇只作标签，未变成隐式实体噪声。 |
| limit | wrench、shift、twist、midpoint、mechanism power先精确相消再构造；G6H04正向、R8 wrench门及自写静力模型。 |

12测试文件逐处说明在 [测试新diff覆盖表](file:///D:/eab-wt/g6i/review/gates_docs/coverage.md)：两独立oracle、vote2、frozen EE、invariance geom、7个R8新增文件。没有确认R8新门被改弱；G6I04位于仍沿用的E5b expected helper。新/旧算法恢复变异也核红的是目标断言，不把脆弱面号/求解器任取顶点当牙。

## 7. 九镜头覆盖与证据

### 镜头1：精确性声称与浮点分支

live几何的符号/成员/严格cone/根/区间大多有理或整数；caller `tol/extent_tol/window/contact_window`是显式域政策，near/tied nominal与可分辨性U是报告。LP浮点阈值只给候选，三状态精确证书不过就有理走完。construction最终range guards不应称“答案噪声带”。死私有旧witness含阈值但public overlap不再调用，按无消费者链列账。

未确认新的“默认谓词因隐式float噪声带改变答案”实例；不因此外推全repo完全没有noise。G6I01/02是精确模型/特征域漏查，G6I03是数值构造，均不能靠谓词精确保证掩盖。

### 镜头2：过滤与缓存等价

- [root独立过滤/导数脚本](file:///D:/eab-wt/g6i/review/repro/root_current_filters_and_dual.py) / [输出](file:///D:/eab-wt/g6i/review/logs/root_filters_dual.log)：10000 orientation、10000 dot/cross与Fraction展开对拍；22285项mul/div/atan2 jet比较，精确零与符号检查，非零误差界为有限搜索用 `5e-13`，不宣称所有导数逐位正确舍入。
- [LP价格/顶点oracle](file:///D:/eab-wt/g6i/review/repro/root_lp_audit.py) / [输出](file:///D:/eab-wt/g6i/review/logs/root_LP.log)：8000价格符号，指数-1100至1100；180个有界2行LP独立列举所有基顶点，过滤版与纯有理价格版exact_x/y/objective一致；浮点视图用独立Fraction转换核对，不用生产 `_fl` 作expected。
- [三维polygon过滤压力](file:///D:/eab-wt/g6i/review/repro/geom3_polygon_filter_pressure.py) / [输出](file:///D:/eab-wt/g6i/review/logs/root_geom3_polygon.log)：2250格，次正规、超大尺度/平移、凹L面及显式带。

这些加上源码有限/正规派生量检查与exact fallback证明路径存在；不是每个IEEE操作误差界的全域形式验证。缓存读全部主要key/序列化/返回fresh路径，无新确认串用；主动篡改私有证书属性不计缓存别名。

### 镜头3：oracle独立性

E2–PERF主要test-owned helper的imports与expected形成路径逐类审查。独立Fraction SAT、support/hull、ear-cut/Gram、profile、扫掠与interval oracle不调被测几何原语；处在src的G0 oracle也需核被测路径未共用，不能只凭目录判断。内部brute selfcheck共享production表面，只作佐证；旧 `escape_height_brute`不独立已明示。

**共享模型锚的限界**：`tests/test_lp_certificates.py::_exact_limit_lp` 仍读取生产 `_build_columns` 的浮点摩擦射线，虽独立组装力矩、荷载移位及黏聚上限，也不能作为“摩擦射线模型本身零共用”的主oracle。root另以60格独立闭式静力与180个独立LP基顶点核验补强；没有声称它们覆盖任意三维摩擦锥构造。未找到该共享锚引起两边同错的当前具体输入，故不凭共用事实单独新增计数。

G6H05 raw view修复真实通过。但**零共用不等于真值正确**：G6I04完全独立却有先舍平方的同类数值bug。详见 [oracle审查](file:///D:/eab-wt/g6i/review/gates_docs/coverage.md)。

### 镜头4：旧门迁移

完整历史test diff生成 [114项迁移导航](file:///D:/eab-wt/g6i/review/gates_docs/changed_existing_tests.json) 与 [迁移核查表](file:///D:/eab-wt/g6i/review/gates_docs/migration_review_table.md)：**108同名修改＋6有承接者的语义改名，合计114，不是114再加6**；62项旧assert文本替换、8项decorator变化。收尾补验已逐项读完两版完整正文，并留下人工前提/断言裁决：[机器核对完整覆盖](file:///D:/eab-wt/g6i/review/migration_complete_review.json)，分工为 [root18](file:///D:/eab-wt/g6i/review/root_migration_final_pass.json)、[二维34](file:///D:/eab-wt/g6i/review/geom2/migration_final_pass.json)、[三维42](file:///D:/eab-wt/g6i/review/geom3/migration_final_pass.json)、[门/文档20](file:///D:/eab-wt/g6i/review/gates_docs/migration_final_pass.json)。断言数或全文阅读均不能证明所有可能变异等价。

实际内变异：G6H05五格；G6E08漏有限extent、35删nominal报告带；G6E49恢复 `_open_cone` 隐式扩窗；G6H06漏最近z盖；R8内置门及G6I04旧新对照。二维49目标“VV activity must match exact neighbor support”报 **12 failed/3 passed**，不是偶然脆断言。[变异脚本](file:///D:/eab-wt/g6i/review/repro/geom2_vv_gate_mutation.py) / [日志](file:///D:/eab-wt/g6i/review/geom2/g6e49_vv_mutation.log)。

**环境误导如实记**：第一次二维副本pytest找父层配置，误import主树而全绿；加副本独立pytest.ini确认被测copy后才得到有效红，不将第一次当门逃逸。

没有逐项亲造114项全部历史变异、没有所有变异矩阵；不以boundary态可变豁免代替实际数据逐格oracle。G6I04只证明新helper的新增小域弱点，不冒称历史原网格被删。

**确有局部敏感性损失，但不是全仓失牙**：`_facet_set` 的list→set会抹重复facet。真实 `convex_entrance_block` 函数体在坐标量级>100时重复一facet，在原有 `random/rot_s1_t1000` 格旧门红、新门绿（[root复现](file:///D:/eab-wt/g6i/review/repro/geom2_migration_duplicate_facet.py) / [输出](file:///D:/eab-wt/g6i/review/logs/root_migration_duplicate.log)）。继续在副本跑该API全部直接测试消费者及该不变性门，16个测试函数177格有 **94 failed / 83 passed**，命中的是FF数量/`len(eb.facets)==8-len(expected)`目标断言；root亲跑 [矩阵脚本](file:///D:/eab-wt/g6i/review/repro/geom2_duplicate_consumer_matrix.py) / [输出](file:///D:/eab-wt/g6i/review/logs/root_duplicate_matrix.log)。因此明确记录局部门变化，但不把已有其它牙抓住的同一个变异计作新的major/minor，也不宣称新set门本身仍守多重性。

### 镜头5：二维/三维独立几何压力

- [二维自写压力](file:///D:/eab-wt/g6i/review/repro/geom2_independent_stress.py) / [root输出](file:///D:/eab-wt/g6i/review/logs/root_geom2_pressure.log)：150对无孔polyomino并、精确正交运动、1e-9/1/1e8尺度与1e8平移；4320 E成员、2160 body、2137成功首入、1441距离完整性及2缓存比较。**另23格FF异常**单独列出，已并入G6I01，不说整组全绿。
- [三维interval-union](file:///D:/eab-wt/g6i/review/repro/geom3_interval_union_pressure.py) / [root输出](file:///D:/eab-wt/g6i/review/logs/root_geom3_union.log)：33格独立区间积/并集真值，物理态与E拓扑分开，紧配、离散组件、尺度1e-100/1e-9/1e8、工程平移和有理旋转。
- [球室完整符号搜索](file:///D:/eab-wt/g6i/review/repro/geom3_chamber_signs_pressure.py) / [root输出](file:///D:/eab-wt/g6i/review/logs/root_geom3_chamber.log)：25组全部2^m符号图，由独立Fraction Fourier–Motzkin证明可行；rank1/2/3及2^-200窄室。

零长/共线/微凹/近平行/微间隙及混合尺度另由旧原复现和全套门覆盖。不是任意genus、所有非正交凹体或所有退化三角化的穷举证明；局部shortest_exit不外推一般凹体全局最短出口。

### 镜头6：接触窗口的实际承诺

**重要口径**：当前docs不承诺一般 `PD_closed<=w`。六轴证书承诺 `rho=inf{||d||:int(A+d)∩int(B)=∅}<=w`；紧配封闭空腔中它与闭集完全分离的PD_closed不同。薄壳承诺每个重叠区落入径向厚度≤w壳，不等于整体PD子水平集；axis/L1证书不保旋转不变。这些是现文档明示边界，不能把正本PD命题直接当已有实现承诺。

手核六轴精确平移证书与star-core条件：星心位于所有真实三角内半空间；`alpha=min(w/R,1/2)`，R是最大顶点L1半径，连续凸组合半径≤R且L2≤L1；core与对方内部不交，因此全部重叠落在厚度≤alpha R≤w的壳。完整interval/正交帧oracle、六轴18格及壳增厚/漏+z内部变异已运行。 [175格三维定向日志](file:///D:/eab-wt/g6i/review/geom3/targeted.log) / [窗口核验详细边界](file:///D:/eab-wt/g6i/review/geom3/coverage.md)。未确认新的可靠性反例，不声称任意非star凹体连续区域全验证。

### 镜头7：极限分析与证书

root逐读lp、limit、limit_multi全部源码及相关背景；有理层验证optimal原/对偶、unbounded可行+射线、infeasible Farkas，浮点层失败仅“无候选”。精确派生力矩、荷载平移与黏聚上限保留原数据模型。

[独立静力/错误候选脚本](file:///D:/eab-wt/g6i/review/repro/root_limit_guard.py) / [root输出](file:///D:/eab-wt/g6i/review/logs/root_limit.log)：

```text
exact_closed_form_pairs=60
single_wrong_candidate_rejections=180
multi_wrong_candidate_rejections=180
limit_load_live_path_poison_rejections=4
all_equal=true
```

真值独立 `min(mu*W, W*s/h)`，W指数±600及短杠杆/非对称实际参考点；错误alpha/lambda/mechanism注入Fraction1e-100，单体/多体均拒。真实limit_load路径再污染浮点alpha、Fractionalpha、exact_x、exact_y，全部在selfcheck拒。LP180顶点oracle核浮点视图与exact_x/y一致。G6E11/20/21/22/45复验远处body/荷载不放宽证书、不吞小行、不改变局部U。未找到新漏检。

**模型边界**：摩擦方向是当前文档声明的浮点离散模型；巨大mu下该方向与理想Coulomb锥有差异，不能无视明示定义把它直接报当前精确LP错。精确答案保证不等于任意物理方向构造精确。

### 镜头8：文档与理论正本

阅读当前README/AGENTS/两精确设计/canon以及E2、E3E4、E5a、E5a2、E5b、PERF、R8FIX与g6f提交说明；外部01/07全文、03映射相关内容、00定义/§3.3/§4.6/谱系只读核对。

[声称→门语义表](file:///D:/eab-wt/g6i/review/gates_docs/claims_coverage.md) 拆每个当前✔/已完成/已验证；[174行自动索引](file:///D:/eab-wt/g6i/review/gates_docs/claims_inventory.json) 的159次显式测试引用均存在，全套通过。**“名字存在/全套绿”不是那句话全域证明**，索引已标仅自动核；实际断言/前提按表逐类读。

canon第八节对07的缩水和未实现项确已明记：原字节往返、读器规模、solver_profile、canonical_order_key、退化record零构造、G1锁态/滑动、G2手写清单、G3批量/零跳过、G4先定阈值与迭代收益、G5、Phase3/5/MLCP等。没有将已公开非目标再次报新major。理论的外部陈旧优先性句不等于当前repo主张；本轮现态旧口径见G6I06。

### 镜头9：第五轮至少20条重放

已由root运行 **31个原raw索引**：01/04/05/06/08/09/10/11/14/16/18/20/21/22/25/26/27/29/30/31/32/35/37/38/40/41/42/43/44/45/49。至少20项计算/门反例之外，还有文档/契约原事实复核；14/32原内容重复，不冒充两项独立数学证据。全输出与方法在 [机读](file:///D:/eab-wt/g6i/review/G6E_replays.json) / [逐项表](file:///D:/eab-wt/g6i/review/G6E_replays.md)。

09以正确响亮ValueError消解旧切向问题，其exit1不是当前失败；40旧私有调用先做float差点仍出现3个hull_anomaly，它不是现给定输入精确E模型；保留该原输出，并用Fraction(b)-Fraction(a)等价声明模型得到 `(0,6,0,0,[])`。不宣传逐字旧模型所有输出相同。

另三维专项重放G6G04/05/06/08全通过，为漏特征、面积、法向、质量同类扫描提供背景；root未将其额外复跑冒充本轮31项的个人证据。 [补充日志](file:///D:/eab-wt/g6i/review/geom3/g6g_replay.json)。

## 8. 未确认 / 不计数项

没有额外“疑似缺陷但复现不了”的项目被计入critical/major。下列边界/风险明确不计数：

1. 极大摩擦系数方向先浮点构造，与理想锥容量不同：已明示浮点方向模型，不是现精确LP证书的错误。
2. legacy reader的坐标相关重复点合并地板：公开规范化政策，不能称raw完全保真，但不把该政策本身当新默认精确谓词缺陷。
3. `_FrozenNormal`私有raw/jet属性被调用方主动改写：未确认跨对象缓存串用，不计别名漏洞。
4. 最终标量真正越binary64范围而响亮拒绝、共享brute扫描的有限步限制、局部出口非全局PD：与既有明示域一致，不能借不支持/近似佐证报静默计算critical。
5. G6E40旧float差点与当前精确差点是不同输入模型，保留原异常而按现合同等价重放，不藏原输出。
6. 显示facet的list→set局部敏感性损失已实际证实，但同一内部变异被其它现有消费者94格拒绝，详见镜头4；不计“全仓门无牙”。

## 9. 完整性批评

1. **源代码**：root全文读数值基础、Dual、predicates、construction、rational3、lp、limit、limit_multi、ContactRecord、全部readers；二维生产模块全文读；三维全部模块职责/API/live主路径及本轮新diff读。收尾另补读 `geom3:569-576,625-772` 旧witness链全部算术更新，并核无生产消费者；root将六helper禁用，凸/凹重叠、距离、首入仍成功，源码SHA一致（[脚本](file:///D:/eab-wt/g6i/review/repro/geom3_dead_witness_not_consumed.py) / [root输出](file:///D:/eab-wt/g6i/review/logs/root_dead_witness.log)）。这些旧浮点启发式不能因此复活为主oracle。没有把全文阅读写成每行形式证明。
2. **历史迁移**：114项（108同名＋6改名）两版完整正文均已逐项人工读完、裁决，清单集合严格匹配；没有每一旧门各自实施所有可能变异。全套10100节点均跑过，不代表未改动测试全部源文件逐行人工审读。G6I04的整套mutant存活情况未测；duplicate变异只跑全部直接消费者，未冒称整套变异矩阵。
3. **数学域**：有限独立Fraction压力、误差界源码审查不是全IEEE、任意genus、多空腔、任意非star/折面耳切退化的形式证明。一般凹体全局E边界/全局PD不是现实现保证。并行分片未复验单进程跨模块缓存/次序依赖。
4. **窗口**：核充分证书推导与明确命名门，没有枚举任意复杂凹体所有连续重叠区。完整PD_closed、窗口旋转不变不在当前承诺；不能以局部壳政策升级工程可靠性。
5. **文档**：174关键词行与159显式引用只是索引，语义核验按声称表说明。00只读相关章节，未全文逐句验证所有外部文献事实；原文论文、学术优先性网络普查未重做。03/07外部旧数字/优先性未修改。姊妹源码仅对指定历史导出前提只读核验，没有全面审查它们。
6. **独立性与去重**：所有入账脚本root亲跑exit0，同行额外反方复核三条major的域与数学反证；FF错/异常只算G6I01，折面凸/凹棱/源角只算G6I02，三处旧文案只算G6I06。没有把门中注入的生产错当当前production错。

## 10. 收尾与下一步

本工单交付完成，**实现未修、M0退出未通过**。实现方可按六项机读发现处置；四major确认修复后仍须新鲜工作树独立复审，不能仅增加测试后以10100绿宣告退出。全部成果位置与可运行命令见 [索引](file:///D:/eab-wt/g6i/review/INDEX.md)，文件/日志哈希及tracked零漂移见 [完整性证据](file:///D:/eab-wt/g6i/review/integrity.json)。

G6I_DONE critical=0 major=4 minor=2
