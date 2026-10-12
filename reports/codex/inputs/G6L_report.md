# WO-G6L：G6 第十二轮独立正确性复审

对象：新鲜 detached 工作树 `D:/eab-wt/g6l`，HEAD `0ce65a44c9c26d99411cee68d7300e7b5521bb40`。审查方只生成证据，不修实现。报告语言：中文。

## 1. 结论与信任边界

**确认：0 critical / 1 major / 0 minor。** 四种静态漏检形态具有同一根因，合并为 G6L-01。本轮没有确认当前未变异生产实现静默返回错误数学答案的 critical；这不等于已经证明任意输入正确。

**按本工单的“0 critical / 0 major”标准，M0 本轮不能获审查方退出认可。** 仓库记载的 2026-10-12 所有者退出决定采用另一口径；本报告不修改历史治理决定，也不把它写成原 G6 标准已经满足。

- R11 两条原问题已重放：原整数/浮点混合谓词反例消失，原零循环静态别名漏检被正确拒绝。
- M4a 在已冻结 15 配对、45 帧的离线检测合同内，没有新增确认发现。未分类 0 不代表与 legacy 完全等价，更不代表真实运动首入、锁态、滑动符号、位移或在线替换已经验证。
- 全套自跑：**11256 passed in 1460.86s (0:24:20)，exit 0；命令墙钟 1473.3085719 秒**。串行 pytest、没有 xdist；审查脚本同时使用机器，耗时不是独占性能基准。
- tracked 原字节完整性：**3375/3375 tracked 文件 SHA-256 完全相同，HEAD 未变，git status 没有 review/ 外变更**。全部审查产物位于 `review/`；未执行 git 写操作，未运行姊妹 exe，未改姊妹仓库或外部正本。

机读结论见 [G6L_findings.json](file:///D:/eab-wt/g6l/review/G6L_findings.json)，完整成果见 [证据索引](file:///D:/eab-wt/g6l/review/ARTIFACT_INDEX.md)。

## 2. 确认发现

| ID | severity | file:line | 一句话结论 |
|---|---|---|---|
| G6L-01 | major | `tools/check_exact_construction.py:356-387`，重点 `:376-380` | 已知 builtin `map / iter / list.pop` 丢失映射调用或元素 callable 来源，真实 cone 内先舍入再求范数仍被静态门判为零违例。 |

### G6L-01：已知局部高阶形态绕过构造门

**范围定性。** 这是静态防守门和核心局部数据流承诺的漏检，不是说当前生产 cone 已经错误。现有某些 cone 数值门能够发现本文特定见证；没有声称整个 pytest 都无牙。未知反射、任意用户函数跨过程返回及自定义对象协议已经被排除，本条不用这些逃逸域：只用标准 builtin、已知构造函数和局部容器。

**failure_scenario。** 令 `u=2^-1074`，四面体顶点为

```text
(0,0,0), (1,-1,u), (u,1,-1), (-1,u,1)
B=A.reflected(); ia=ib=0
```

独立 Fraction oracle 展开三个半空间法向 `(-1,1,-u),(-u,-1,1),(1,-u,-1)`。`p=(-u/3,-u/3,-u/3)` 是正凸组合，每个法向与 p 的内积均为 `||p||²=u²/3`，满足最小范数 KKT 条件。又有 `(u/2)² < u²/3 < (3u/2)²`，因此范数正确舍入为 `u=5e-324`，不是 0。oracle 不调用被测几何、向量或构造原语。

在真实 `cone_intersection_margin` 函数内部，将最后的 `return norm_rational(p), noise` 换成以下任一形态：

```python
return tuple(map(norm_rational,
                 [vector_rational(p, allow_underflow=True)]))[0], noise

return tuple(map(sqrt_rational,
                 [scalar_rational(sum(x*x for x in p), allow_underflow=True)]))[0], noise

root = next(iter([norm_rational]))
return root(vector_rational(p, allow_underflow=True)), noise

box = [norm_rational]
root = box.pop()
return root(vector_rational(p, allow_underflow=True)), noise
```

四个变异均从 **5e-324 错成 0.0**，而完整 `covers3.py` 源文本扫描返回 `[]`。另复制全部 195 个 src/tests Python 文件、仅改 map_norm 一处，`scan_repository(copy)` 仍为 **0 violation**。不是在输出后追加假数据。

**根因。** `:356-357` 只检查映射 float；`:358-362` 查的是外层调用名称，未将 mapped root/norm 应用于映射元素的舍入来源。`:376-380` 记录 lazy 来源并合并返回摘要，却没有核验这个真实映射调用。`iter`、本地 `list.pop` 在未知返回分支 `:387` 丢掉元素 callable 标签，后续 `root(...)` 不再被识别为范数。R11FIX 的分支/循环 may-state 修复是真实存在的，但不覆盖这些同类传播边。

**how_to_reproduce（在本树运行）。**

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -X utf8 review/repro/numeric_static_higher_order.py
python -X utf8 review/repro/numeric_static_repository_copy.py
```

脚本：[真实函数内四种复现](file:///D:/eab-wt/g6l/review/repro/numeric_static_higher_order.py)、[全仓副本门复现](file:///D:/eab-wt/g6l/review/repro/numeric_static_repository_copy.py)。根审查方亲自重跑的输出：[四种运行日志](file:///D:/eab-wt/g6l/review/logs/root_verify_numeric_static_higher_order.log)、[副本扫描日志](file:///D:/eab-wt/g6l/review/logs/root_verify_numeric_static_repository_copy.log)。

**verified_output 摘要：**

```text
map_norm:      baseline=5e-324 expected=5e-324 mutant=0.0 gate_issues=[]
map_sqrt:      baseline=5e-324 expected=5e-324 mutant=0.0 gate_issues=[]
iter_callable: baseline=5e-324 expected=5e-324 mutant=0.0 gate_issues=[]
pop_callable:  baseline=5e-324 expected=5e-324 mutant=0.0 gate_issues=[]
whole_repository_static_scan: python_file_count=195 gate_issues=[]
original_tracked_source_unchanged=true
```

被测原文件前后 SHA-256 同为 `23da74c34f963b5b12559bf9b3eba91687d6fd3f07334004e191200501b164dc`。数值变异只在内存重编译；磁盘变异只在 review 副本。

**suggested_fix（不在本单实施）。** 对已知 mapped root/norm 核验元素实参；让 builtin iter、局部容器 pop 保守保留元素的 rounding/callable provenance，或对已知但不支持的高阶形态响亮拒绝。增加四种穿过真实函数内部路径的变异门，指定必须红在目标舍入构造断言，而非碰巧的其他断言。

## 3. 工单优先项

### 3.1 第十一轮回归

[回放脚本](file:///D:/eab-wt/g6l/review/repro/numeric_r11_replay.py)、[完整输出](file:///D:/eab-wt/g6l/review/numeric/r11_replay.log)：

- 原 mixed integer/float 3072 格：0 错；精确两倍面积为 1 的三角不再被三角化为空。
- `for _ in ()`、`for _ in range(0)`、`while False` 三种真实 cone 内部变异：数值确实变成 0，但当前 scanner 均报 `rounded-vector`。故原 G6K-K01 已关闭；G6L-01 是新的传播形态，不重复计原缺陷。
- R9/R10/R11 静态与 R11 数值定向门：214 passed in 12.94s。

### 3.2 M4a 专审

详细证据见 [M4 子报告](file:///D:/eab-wt/g6l/review/m4/audit.md)、[独立深探针](file:///D:/eab-wt/g6l/review/repro/m4_deep_probe.py)、[变异复跑](file:///D:/eab-wt/g6l/review/repro/m4_mutation_replay.py)。

| 核查 | 实测与边界 |
|---|---|
| 台账可复跑、互斥、无兜底 | 45 帧逐条钉住分类和关键量。MATCH 1939；VV_IDENTITY_MATCH_TWO_REFERENCE_NORMAL 58；EXACT_LOCAL_COVER_NOT_SELECTED 469；ANGULAR_WINDOW_COVER_NOT_SELECTED 167；LEGACY_OUTSIDE_FINITE_EDGE_WINDOW 434；LEGACY_VV_DIRECTION_OUTSIDE_OPEN_CONE 98；LEGACY_DUPLICATE_PRIMARY_REFERENCE 9；UNCLASSIFIED 0。按明确谓词和优先级分配，未知项不被兜底吞掉。 |
| 未分类 0 有牙 | 真实角度窗口移除、严格额外盖错误归类、reader 的 p1 改读 p2 三种内部变异，都红在相关未分类/钉死计数/原始字段断言；恢复后绿。未知名称、缺失/重复帧等拒绝。补核保持所有 counts 不变而将 difference key 末特征号 +1，完整冻结门红在 pinned row-by-row classification；assert_classified 单独通过符合它只核闭集的职责。 |
| L5 只放宽、不回流 | detect_step 显式 window=d0、tol=0、cone_tol=sin(h1)、seg_tol；fit_tol 只核报告量。450 组域窗口包含性比较，尺度 1e-9/1/1e3、工程原点 1e8、精确有理旋转下 0 个缩窄。没有把 legacy 窗口写成内核默认噪声带。 |
| CSV / VV 身份 | 2538 条原始记录逐字段独立核；15228 身份值、17766 接触列值、10152 最终状态字段一致。本批 156 条 VV 由两组三点 alias 后交集核真实角点；参考半交换不改身份。 |
| alias 与 multiplicity | 696 个实际 alias 均为原 binary64 坐标完全相等，非零距离合并 0。原记录 2538、主身份唯一记录 2529，9 条额外重复仍保留，不因集合比较无声丢行。 |
| 源码接缝地图 | 只读抽查 df.c:555–578、1430–1460、1484–1519、1619–1694、1960–1996、4335–4345、6003–6055，以及 driver/main.cpp、run.hpp、Studio bridge、verify_cpp.py 指定片段。补核 df.c:3994 跳过 :4030、跳到 :4063，而 debug/dump 窗内 :4072–4075 仍逐 contact 导出 o4；冻结 570 个 df22 差异全满足指定分支。没有冒称读完 b-DDA 全仓。 |
| legacy 判断不越界 | 434 个有限边窗外、98 个开放公共锥外是精确几何事实，但原文明确不同检测/弹簧合同的物理正确性“无法判定”；9 个主参考重复不能据此判 legacy 物理错误。旧 VV 错位归本 reader，不转嫁 legacy。 |

[M4 补核](file:///D:/eab-wt/g6l/review/m4/addendum.md) 保留源码/冻结差异与同计数 key 变异的完整输出。M4 定向门 **109 passed in 7.14s**；冻结捕获核验为 `cases=15, steps=45, fixture_bytes=1436984, status=verified`。使用 verify-only，没有重新运行姊妹 exe 或覆盖夹具。初次 basetemp 父目录缺失导致 setup error，建审查目录后全数通过；属于审查环境错误，不计实现缺陷。

### 3.3 本轮新代码细审

检查 `git diff 5591702..HEAD -- src tests tools docs`（26 文件，3656 additions / 374 deletions）。M4 新 adapter/reader/三组 tests/台账工具由 M4 组逐段读取；数值类型修复和静态 scanner 由数值组读取；根方补读 contact_record、reader 往返门、plan、r11fix_design_sync、sibling_observations 和沙箱编排改动。保存 [根方差异补读](file:///D:/eab-wt/g6l/review/logs/root_new_code_diff_subset.txt)。新 fixture 全字节通过溯源核验，CSV 值通过独立解析；没有把自动读取所有字节等同逐行数学审查。

## 4. 九镜头覆盖

### 镜头 1：精确性声称与阈值分支

src/eab 共 37 Python 模块、11755 行，AST 语法清单含 1629 个 Compare，关键词候选 147 个。保留 [分支清单](file:///D:/eab-wt/g6l/review/all_comparisons.json)、[候选分类](file:///D:/eab-wt/g6l/review/threshold_classification.json)。**这个全仓语法枚举不是全仓数据流证明，也可能漏掉无 Compare 的隐式择支。**

手读分类：显式 tol/window/接触分辨率是调用方域/报告；predicates 的界只接受可认证快路，不确定则有理回退；LP 容差位于浮点候选层，答案须精确证书；limit contact_forces/active 是已说明的显示字段。geom3 旧私有见证链仍有绝对阈值，但公开 overlap 路由 exact_geom，未找到旧链入口，不把死辅助代码误报当前答案缺陷。manifold planarity 是诊断；first_entrance_brute 明示共享采样佐证及不漏穿越前提。没有确认新的答案噪声带反例；未证明所有 1629 个分支均可接受。

### 镜头 2：过滤与缓存

新独立 Fraction 压力：cross2/dot2 各 6000、orient2d/orient3d 各 3500、LP reduced_sign 3500、rational3 1000、平方根中点 1200、一行解析 LP 90；含次正规、下溢、上溢、巨整型、Fraction/float 混合及宽指数范围，确认错数 0。根方亲自重跑 [脚本](file:///D:/eab-wt/g6l/review/repro/numeric_exact_pressure.py)，输出见 [日志](file:///D:/eab-wt/g6l/review/logs/root_verify_numeric_exact_pressure.log)。

检查普通 float 严格类型门、转换误差界、有理兜底以及 `_float_value` 缓存的内建不可变输入。margin/interlock 几何缓存由内容快照定位，不以对象身份替代输入内容。有限探针没有确认缓存串用；没有穷尽任意自定义数值协议或可变对象的所有操作序列。追加全文手读 frozen/entrance_topology，二者无模块内缓存、未发现新状态噪声带；相关 tight-fit/narrow chamber 5 格和冻结 raw jet 18 格定向通过。

### 镜头 3：oracle 独立性

检查 E2 的整数 SAT/Jarvis、g03_exact、g03_surface_oracle、E5a cover/escape、E5a2 surface、E5b margin/frozen/wall 和构造 oracle 的数学 helper。主要 oracle 不调用对应被测 SAT、支撑锥、Newell/Gram/Gordan 等几何路径。construction reference 用 Decimal 初值加 Fraction 中点认证，不复用生产 significand/isqrt 算法。

六个 oracle poison/真实内部缺陷门 **6 passed in 0.38s**。本轮新扫描线、盒排列、四面体 oracle 自己展开 Fraction 几何，不使用生产成员/平面/三角化作真值。共享 polyhedra_overlap 的采样 brute 仅佐证；极限分析模型列序共享不被包装成零共用主 oracle。见 [几何子报告](file:///D:/eab-wt/g6l/review/geometry/audit.md)。

### 镜头 4：测试迁移强度

在 b6126cf 与当前 HEAD 的 review 副本中做四类内部变异、共 16 次 pytest：漏 VV、空出口集合、投影乘 0.99 旧门能抓、现门亦抓；吞掉 boundary 旧门绿、现门红。逐条保存红断言，不用 exit 1 替代因果解释；副本原字节 SHA-256 复原。见 [运行记录](file:///D:/eab-wt/g6l/review/geometry/gates_migrations/results.json)。

未对 E2–PERF 每一个迁移门逐个变异。AST 迁移清单只能定位删除/改写，不能证明强度。G6L-01 表明静态防守仍有局部语义漏网，因此不能凭现有静态 tests 全绿断言门完备。

### 镜头 5：二维/三维退化压力

新独立 oracle 共 **384 格**：二维精确扫描线 240、三维嵌套壳排列 48、微薄四面体 SAT/射线 96，均 errors=[]。覆盖精确有理旋转、平移 1e8、尺度 1e-9..1e8、间隙 1e-15、微薄特征到 1e-24，以及接触/分离/重叠和首入。二维 165 个分离格另外独立核有限特征距离平方完备性。输出见 [汇总](file:///D:/eab-wt/g6l/review/geometry/verification_summary.json)。

另对原 #24 的 80 个实际 float 姿态做独立整数 SAT，0 错；#36 精确有理刚体变换的 18 完整标签没有 lost/extra；#34 两个精确 U 墙的 exact_height=1/5。没有新写一般任意非凸互锁/最短出口完备 oracle，不以这些结构化家族代替它。

### 镜头 6：局部贯入窗口证书

根方新写 [Fraction 盒乘积证书脚本](file:///D:/eab-wt/g6l/review/repro/root_window_certificates.py)，108 格：两精确正交框架、三尺度、原点/1e8、三轴、三个贯入深度。独立核每个轴芯是相同位移且位移范数 ≤ w；每个壳芯具有同一中心、同一缩放，连续径向移除厚度由顶点最大值/凸性界 ≤ w；再以独立盒区间模型核精确 OR 与公共 membership，0 mismatch。证据见 [逐格 JSON](file:///D:/eab-wt/g6l/review/logs/root_window_certificates.json)。

PERF contact_window / doc pointers / R7 docs 定向门 **40 passed in 0.83s**。这里核的是证书结构与相触蕴含的薄层/位移限界，不偷换成任意 polyhedron 精确 PD 已实现。

### 镜头 7：极限分析

真实 `_float_solve` 注入五种错误状态/基候选后，solve 精确认证/有理回退返回正确解析最优；自校验 alpha/lambda/mechanism/row_dual 各注入 1e-100 污染均拒绝。90 个一行解析 LP 独立核原始可行、对偶可行、最优目标，以及 exact_x/exact_y/obj 的浮点视图一致性。相关四文件定向 **387 passed in 19.02s**，含真实调度和精确见证污染。静力独立力矩/荷载移位构造不调用 LP 原 wrench/shift helper。

可分辨性只报告，exact 模型状态和证书不依赖显示容差；活动列/接触力显示截断不当证书。没有确认新精确自校验漏检；没有穷尽任意维 LP。

### 镜头 8：文档、代码、正本

读 README 当前边界、AGENTS、两份精确设计及 canon_map 核心对照；读 E2–PERF 处置/迁移/边界和 R11/M4 报告；保存并阅读只读 g6f 的 b6126cf 之后提交说明。正本 01/03/07 全文，00 读理论内核、4.6 诚实分类和实现谱系相关段，未读完所有参考文献叙述。

抽取四份主文档 69 个声称行、101 个同句显式测试引用，0 个缺失引用；指针门通过。**存在引用不等于断言已证明整句话**，本轮逐项数学核查只覆盖上述新路径、窗口、精确分支和 M4 合同。canon_map §8 与 07 对照保留 G1 的锁态/滑动/位移、一般入口选择及更多表示仍未完成；M4a 是静态离线第一步，不冒充整个 07 接缝合同。G6L-01 是局部静态承诺的确认例外。

### 镜头 9：第五轮原问题重放

原始 50 条按原数组 1-based 编号。复制/重放 24 个原脚本：**7、9、11、20、21、22、24、25、26、27、28、29、30、31、34、36、37、38、40、41、42、43、44、45**。24 个均 exit 0，但不把“脚本运行完”说成每项所有原断言均成立；输出与处置见 [完整记录](file:///D:/eab-wt/g6l/review/geometry/legacy_replay_results.json)。

另数值组按原 file:line 对 9 项做等价输入/精确候选污染回放：9、11、20、21、22、23、38、45、47。与原脚本集合去重后 **26/50 项**有本轮重放或等价核验，超过要求的至少 20 项；不是 33 个不同问题，也不是全 50 项。八个 E4 等价项复用当前语义门的输入和注入，不伪称新独立 oracle。

旧 #24/#36 的 float 刚体构造会改变给定精确输入，不能机械沿用“不变”期待；追加独立 oracle / 精确有理刚体核验。#40 原脚本不再 NameError，但其先用 float 构造差点后的 `hull_anomaly` 仍打印，**没有完成该差异的独立数学归因，未宣称 #40 的全部 G0 断言已关闭**，列入未确认。

## 5. 未确认及非计数观察

1. **#40 hull_anomaly**：原脚本先浮点做差，与从原输入精确构造差点的数据模型可能不同；本轮确认了 NameError 不再出现，未独立证实仍打印的几何差异是现实现错误，不计 critical/major。
2. **mechanism_power 显示读数**：探针观察 `_ExactFloat` 机构见证的精确 power=0，而 helper 按 float 视图算约 2.808e-17。其签名/合同未承诺读取证书、普通运算会剥离精确见证；尚未确认违反合同。精确自校验读 `_rational`，没有将显示残差误报为证书失效。
3. late-lambda/reduce 等未知跨过程摘要探索未作为新条目；本轮确认发现严格限于已知 builtin 和局部容器。
4. legacy 几何 reader 公开近重复合并窗口，对任意合成极短棱可能合并真实点。本批 alias 全为同坐标；没有将已公开适配范围外推成任意精度读取保证或新 critical。
5. canon_map 旧 §8 状态表尚未补 M4a 列，README 旧键唯一性表须与最新 contact_record/M4 multiplicity 说明联读。建议维护消歧；没有把 dated 历史表的维护事项夸为核心数学承诺错误。

## 6. 完整性批评

- **不是全仓逐行审查。** 37 src 模块做了 AST 清单，但 exact_geom/geom3/covers3/entrance3/interlock 只重点读公共精确路由、构造、事件、窗口、缓存和相关退化段；其余辅助/历史函数没有逐行数学证明。包 initializer 未作独立数学审计。frozen/entrance_topology 已追加全文阅读。具体 full/partial/executed/machine-only 分级见三份子组 coverage 和根方 [范围记录](file:///D:/eab-wt/g6l/review/ROOT_scope_notes.md)。
- **不是所有测试都有新变异。** 没有对 E2–PERF 每个改写门逐个旧/新对照；本轮四类迁移变异、六个独立 oracle 毒化门和静态四种内核变异只是明确子集。
- **不是所有文档声称都被语义核完。** 69 行引用盘点只证明索引存在；没有对每条 ✔ 的整句性质独立证明。00 文献叙述和外部优先性论文未重新查验。
- **第五轮尚有 24/50 项没有本轮重放。** 已重放项中的 #40 仍有未确认差异；没有因 exit 0 隐去它。
- **几何反例搜索是有限家族。** 新扫描线限 x-monotone 分段多边形，三维限结构化壳/盒/四面体；没有穷尽任意凹体、非星形面、一般非凸互锁及最短出口，亦未将非法输入处理全部逐项列证。
- **M4a 只覆盖冻结三步离线证据。** 没有重新捕获 exe、覆盖长历程 30–400 步、核接触装配/继承/锁滑/位移同构或切换在线检测。源地图是指定片段抽查，不是 sibling 全仓审计。
- **数值有限压力不是形式证明。** 普通 float/Fraction/int、特定指数及解析 LP 家族没有覆盖所有用户自定义数值对象、所有 Dual 超越组合或任意维病态 LP。

以上遗漏不稀释已确认 G6L-01，也不被“全套绿”覆盖。

## 7. 全套自跑与完整性证据

开始时先检查干净 detached 状态并保存 3375 tracked 文件 SHA-256，随后首先启动全套，再进行并行审查。Python 3.12.10 / Windows 11。实际命令：

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONIOENCODING='utf-8'
$env:PYTHONUTF8='1'
python -X utf8 -m pytest -q -p no:cacheprovider tests `
  --basetemp=D:/eab-wt/g6l/review/tmp/fullsuite
```

按“写入只限 g6l/review”的更严格约束，basetemp 不写 g6f。没有合并定向测试计数冒充全套；不采信工单里互相冲突的历史测试数。

**最终结果：11256 passed in 1460.86s (0:24:20)，exit 0；命令墙钟 1473.3085719 秒**。

原始 PowerShell 日志为 UTF-16 BOM，另生成等内容 UTF-8 便于读取：[全套日志](file:///D:/eab-wt/g6l/review/logs/fullsuite_utf8.log)、[命令退出与墙钟耗时](file:///D:/eab-wt/g6l/review/logs/fullsuite_exit.txt)。

[写入范围核验](file:///D:/eab-wt/g6l/review/scope_verification.json)：3375/3375 tracked 文件 SHA-256 完全相同，HEAD 未变，git status 没有 review/ 外变更。

G6L_DONE critical=0 major=1 minor=0
