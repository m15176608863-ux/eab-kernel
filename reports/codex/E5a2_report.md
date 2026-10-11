# WO-E5a2：一般精确表面收尾与全套提速

执行日期：2026-10-12。工作位置 `D:\eab-wt\cx-e2`，分支 `codex-work`，回滚锚 `5b09ea399a5277f359f833312638c9bb86f09192`。**未提交、未推送。**

<!-- FINAL_RESULT_START -->
**最终全套尝试（未全绿）：`49 failed, 7953 passed in 1566.87s (0:26:06)`**

- 包装器墙钟 **1578.67 s**；pytest 自报 **1566.87 s**。≤900 s目标：**未达到**；≤600 s理想：**未达到**。
- 原 7907 个节点全部保留，当前 **8002**，新增 95；运行期间及结束后源哈希一致。通过7953、失败49、跳过0。**D全绿要求未满足，不得合并成已通过里程碑。**
- A1/A3指定底层接线与独立门已实现，但旧调用层集成收尾仍未完成；A2按允许的有限语义说明方案交付。留树供审查，**不建议按全绿成果合并**，不是G6或新worktree退出。
- 发现失败后并行进行了短诊断，故该墙钟是完整失败运行实测，**不是干净独占提速成绩**；未证明900秒达标。
- [完整全套日志](file:///D:/eab-wt/cx-e2/reports/codex/E5a2_evidence/final.log) · [命令/源哈希/墙钟](file:///D:/eab-wt/cx-e2/reports/codex/E5a2_evidence/final.json) · [失败明细](file:///D:/eab-wt/cx-e2/reports/codex/E5a2_evidence/full_failures.json)
<!-- FINAL_RESULT_END -->

## 1. 验收口径与操作边界

- 接受所有者对 E5a 的订正：系统临时目录不算保护红线越界，E5a 按部分完成接续。历史报告保留；未删除或移动旧 `%TEMP%` 文件。
- 只在本工作树写入。本单没有对姊妹库/其它工作树写文件或执行 Git 写操作；没有 commit/push/reset/checkout/stash/worktree。所有 pytest 基准临时目录在本单证据树；Python 使用 `PYTHONDONTWRITEBYTECODE=1` 与 `-X utf8`。
- 用户本单禁止新 worktree，故**不能声称通过新 worktree 门或正式六路 G6**。两份交叉审查是开发质量检查，不是里程碑退出证书。
- [执行契约](file:///D:/eab-wt/cx-e2/reports/codex/E5a2_evidence/contract.md)、[证据索引](file:///D:/eab-wt/cx-e2/reports/codex/E5a2_evidence/INDEX.md)、[交付审计](file:///D:/eab-wt/cx-e2/reports/codex/E5a2_evidence/delivery_audit.json)。

## 2. A 项逐项处置

| 项 | 处置 | 主门与证据 |
|---|---|---|
| A1 三个旧入口 | `point_in_polyhedron`、`segment_crosses_face`、`polyhedra_overlap` 接精确有理三角化表面路径；一般路径不偷偷凸化 | `test_e5a2_surface.py`；[A1 证明、门和迁移明细](file:///D:/eab-wt/cx-e2/reports/codex/E5a2_evidence/a1/report.md) |
| A1 内部重叠 | 精确 AABB 排除；经源三角支持证书才走凸 SAT；一般情况切分三角面开二维单元，构造并核验双方严格内部的有理证人。共面和共同棱附近重叠均纳入 | 独立矩形并集、星形体四面体并集整数 SAT；删除真实共面内部证人分支后 9 个目标断言失败 |
| A2 一般单盖 | 采用工单允许的**如实限定语义**方案，不声称完成一般折面实体法锥 | 源环 Newell 方向、首顶点锚平面、投影绕数和源拓扑描述符；两项反例门固定见证不在任何对应三角面上、环起点依赖及标签域不同 |
| A3 精确窗口 | 六类盖从原坐标重建精确距离平方比较窗口；不读浮点 gap 或舍入见证作窗口分支 | 所有六类完整候选集合独立 Gram 对拍；真实 gap 下溢到 0 的内部突变牙 |
| A3 欧氏报告带 | 凸成员零 tol 精确三态；正 tol 为到完整 E 边界的欧氏距离。外部平面距只作下界，剩余用精确最近凸组合 | 盒体闭式、独立有理 Gram 子集 oracle；改回支撑平面带后 6 个目标格失败 |

### 模型边界不可省略

A1 的前提是**有效、向外一致定向、闭合、嵌入的有界表面**。不自动修复开口、自交、非流形或错误朝向。非平面 face-ring 按确定性投影耳切表示折面；显式凸 API 则表示原顶点精确凸包，二者不是同一个模型。

点查询的正 tol 是到实际三角表面的欧氏带；实体相交的正 tol **只在分离侧**把近带报告为 0，真实内部始终为 1。零 tol 分支严格针对给定浮点数的有理值，不针对舍入前的理想几何。独立星形 oracle 必须先证明核点严格在每个三角内侧，不能证明便拒收；非星形 U 形补查使用另一闭式，并未暗中凸化。

A2 保留源编号；不能把一般源环描述符当作完整折面接触盖，不能把 canonical convex-view 标签与源标签混用。[A2/A3 详细说明](file:///D:/eab-wt/cx-e2/reports/codex/E5a2_evidence/a3/notes.md)。

## 3. 集成时发现的 interlock 问题及最小桥接

新谓词揭示：相邻浮点候选高度可能一个真正贯入、另一个已分离，旧循环却按舍入簇共用贯入状态，导致 `candidate set incomplete`；浮点闭式根本身也可能向下舍入。没有通过改旧逃逸门或把微贯入吞成接触来消除失败。

修复分两层，必须分开理解：

1. **功能接线**：不同 nominal float 高度分别验收；一簇全部失败时，在既有法向舍入报告带内构造一次上探，再对**实际返回 height 对应的原对象平移坐标**做精确非贯入核验。不能验收高探针却返回未验收的低高度。winner/tied_labels 仍为 nominal 簇的旧报告标签；不是全链精确最早根、精确并列或任意折面法锥证明。
2. **严格等价优化**：这些调用只消费 `state == 1`，而相交接口正 tol 只改变分离侧 -1/0，因此传零 tol 与正 tol 的贯入布尔完全相同，避免每次二分求无关的欧氏报告带距离。独立剖面 oracle 检查返回实际位形；另有正/零 tol 对拍及内部上探突变。

原 `test_interlock_escape.py` / 候选合同 / 灵敏度 / 不变性门未删改。新增桥接门保留尺度、工程坐标、原出错偏移、零初态和微贯入检查。`entrance3.py`、`frozen.py` 没有修改生产逻辑；`margin.py` 只订正文档，去除 docstring 后的 AST 与 HEAD 相同。

## 4. B：先 profile，再做等价优化

六个指定文件均对编辑前的 HEAD 字节副本完整 cProfile；最后采用的六次均返回 0。不是抽样参数网格。**cProfile 时间不是裸跑性能**；有并行 profiler，累计调用树百分比重叠，不能相加。

| 文件 | 基线 cProfile wall / s | 主要核心热点（累计占比） |
|---|---:|---|
| invariance_interlock | 1277.295 | enumerate_covers3 50.18%；escape_height_covers 36.43%；ee_cover 35.97% |
| invariance_geom | 690.946 | enumerate_covers3 39.26%；margin._resolve 37.53%；_witnesses 27.11% |
| interlocking | 526.781 | 见完整前20表；距离完备性验证及盖枚举 |
| interlock_sensitivity | 432.321 | escape/一般相交、点包含、盖枚举 |
| covers3_g0_vote2 | 307.313 | 独立 SAT overlap 62.8%；凸成员 26.2%；几何 dot 16.8% |
| bb52_g1 | 269.881 | enumerate_covers 85.75%；二维局部盖及符号算术 |

**每文件前 20 名、调用次数、累计时间、自身时间与占比**完整列于[性能报告](file:///D:/eab-wt/cx-e2/reports/codex/E5a2_evidence/performance_review.md)；[机读汇总](file:///D:/eab-wt/cx-e2/reports/codex/E5a2_evidence/profile_summary.json)及六份原始 `.prof` 在证据目录，可由 pstats 复核。

### 逐项优化前后与对拍

下表是同一小工作负载的微基准，不能作为全套达标证明；有其它 profiler 活动时记录，2D 行为进程 CPU 中位数，其余为 wall 中位数。

| 等价优化 | 前 → 后 / s | 不改变答案的理由 / 对拍 |
|---|---:|---|
| 3D Fraction dot/cross 公分母整数化 | 0.030513 → 0.015727 | 同一有理多项式，只在最终结果规范化；随机/退化/工程/次正规/大指数逐值相等，真实调用接线 spy 门 |
| 独立 SAT 查询用整数区间行 | 0.158552 → 0.012520 | 同一完整轴集，1800 平移对拍；独立 oracle 不 import 被测几何算术 |
| EE 先核锥、后构造最近直线参数 | 0.104673 → 0.058312 | 3136 棱对与原 eager 调度逐项相等，输出/次序不变 |
| 凸成员支持平面整数行 | 0.061067 → 0.008820 | 同一平面与同一闭边界关系；tol=0 平移循环逐项对纯 Fraction |
| 角域平方比较整数化 | 0.013595 → 0.004232 | 正分母交叉相乘，同一严格/闭边界；2999 组及边界门 |
| 2D Fraction cross2/dot2 符号 | 0.187500 / 0.171875 → 各 0.046875 | 直接比较精确分子；每轮52320对，2616不同输入对；浮点转换陷阱与两项内部符号突变 |
| 点成员同次查询复用平面/包围盒 | 0.076898 → 0.050260 | 192点诊断；180点 fresh/prepared 与独立 L 形真值对拍；并发期间还改过算术，不能单独归因此比例 |
| interlock 仅求贯入时传零报告带 | 9.816589 → 1.911130 | 同40次二分输入、布尔序列及返回高度完全相同；通用状态对拍另在新桥接门 |

[五项微基准](file:///D:/eab-wt/cx-e2/reports/codex/E5a2_evidence/optimization_benchmarks.json)、[二维微基准](file:///D:/eab-wt/cx-e2/reports/codex/E5a2_evidence/bilinear_benchmark.json)、[二分序列逐项比较](file:///D:/eab-wt/cx-e2/reports/codex/E5a2_evidence/brute_zero_tol_diagnostic.json)。浮点/混合/Dual 保持原表达式顺序；交叉审查对每个几何模块另作410次位模式/全部导数通道比较，没有只比 primal。

**没有新增浮点过滤或缓存层。** 扩展的是既有内容寻址缓存的整数 payload，键仍带完整顶点/面环/标签及必要实现身份；同值不同对象可以安全复用，不是仅用部分值的全局缓存。A1 prepared 数据仅在本次调用中传递。新增内容串用门不等于所有上游缓存都可变安全，见第8节明确限制。

<!-- TIMING_TABLE_START -->
### 最终无 profiler 全套中的六文件耗时

| 文件 | E5a JUnit / s | E5a2 JUnit / s | 后/前 | 原格→现格 |
|---|---:|---:|---:|---:|
| test_invariance_interlock | 456.857 | 412.465 | 0.903 | 515→515 |
| test_invariance_geom | 277.182 | 235.908 | 0.851 | 2406→2406 |
| test_interlocking | 176.497 | 174.946 | 0.991 | 17→17 |
| test_interlock_sensitivity | 129.449 | 82.759 | 0.639 | 41→41 |
| test_covers3_g0_vote2 | 102.824 | 15.526 | 0.151 | 95→95 |
| test_bb52_g1 | 89.634 | 76.015 | 0.848 | 17→17 |

E5a每文件基线来自历史完整JUnit汇总，不与cProfile时间混用；所有者提供的整套基线为1829秒。当前是失败运行，途中有短诊断并发，不计算净提速率。测试数由7907增至8002且一般表面语义与独立oracle工作量增加，不能把整套差额归因到单个算术优化。

### 当前剩余慢门（最终 JUnit 前15）

| 文件 | 格数 | 秒 |
|---|---:|---:|
| tests.test_invariance_interlock | 515 | 412.465 |
| tests.test_invariance_geom | 2406 | 235.908 |
| tests.test_interlocking | 17 | 174.946 |
| tests.test_entrance3 | 37 | 92.110 |
| tests.test_interlock_sensitivity | 41 | 82.759 |
| tests.test_bb52_g1 | 17 | 76.015 |
| tests.test_frozen_ee_sign | 98 | 43.090 |
| tests.test_interlock_escape | 19 | 39.118 |
| tests.test_frozen_lowdim | 15 | 38.126 |
| tests.test_invariance_2d | 851 | 28.304 |
| tests.test_limit | 67 | 26.478 |
| tests.test_g4_multistep | 7 | 26.449 |
| tests.test_kernel2d_predicates | 151 | 20.907 |
| tests.test_geom3_overlap_witness | 120 | 19.974 |
| tests.test_kernel2d_g0 | 115 | 18.520 |

[完整分文件对比](file:///D:/eab-wt/cx-e2/reports/codex/E5a2_evidence/performance_breakdown.json)。
<!-- TIMING_TABLE_END -->

## 5. 测试改写台账：原格逐个保留

不是要求舍入后对象仍保持理想接触，而是要求**原浮点输入的精确答案**，同时另核理想有理仿射位形和原有稳定区性质。完整台账含旧/新函数全文、理由、函数哈希、参数装饰器及逐节点格数：[test_rewrites.json](file:///D:/eab-wt/cx-e2/reports/codex/E5a2_evidence/test_rewrites.json)。

- A1 的7项迁移：刚体变换下叠块接触/逃逸，原死 helper 的突变接活路径，source-ring投影与真实三角路径分离，两个凹体边界族，4档真实微贯入，工程坐标薄体正确分离。
- root 的3项几何不变性门及3项 margin 门：全部原参数/调用保留；边界格用独立原表面 oracle，真正内部要求唯一贯入哨兵；原 delta/depth 网格不缩小。两个 margin 牙改在实际 `_resolve` 内注入，不篡改返回产物。
- 首入2项：24原seed、每格800步 brute、原时间精度/gap/normal等断言保留；独立整数 SAT 求连续精确首入区间，核对原实际舍入终点完整三态，并另在精确有理首入平移要求0。V槽原1.15确为微贯入，保留原输入并增加精确接触轨。
- G2 的原27格、完整字段及adapter分组全部保留，只把独立辅助枚举窗从舍入gap改为Gram精确距离平方。
- 没有新增 skip/xfail，没有删除测试。库存审计不替代断言强度审查：[逐节点库存](file:///D:/eab-wt/cx-e2/reports/codex/E5a2_evidence/collection_audit.json)、[交叉复核](file:///D:/eab-wt/cx-e2/reports/codex/E5a2_evidence/cross_review_a1_root.md)。

## 6. C：真实被测路径的突变表

| 突变 | 目标结果 / 红因 |
|---|---|
| A1 共面内部证人分支 `elif loc == 0` 禁用 | 9格在 `polyhedra_overlap(a,a)==1` 失败；不是后处理假产物 |
| A3 外部报告带退回支撑平面距离 | 6格精确外角距²=1/8、tol²=1/16，错误0被真值-1抓住 |
| A3 窗口退回 `abs(c.gap)<=window` | 实际下溢为0的gap误收VV3，完整空集断言失败 |
| 整数dot第三项反号 | 纯Fraction逐值对拍失败 |
| SAT严格区间改闭/开边界 | 整数SAT边界状态与原Fraction不一致 |
| 支持平面偏移反号 | 原始坐标成员对拍失败 |
| 角带 `>` 改 `>=` | 精确闭边界格失败 |
| 真正dot/cross整数快路断开 | 调用接线spy断言失败，避免微基准快但生产没接上 |
| 2D cross/dot符号内部反号 | 各自纯Fraction符号门失败 |
| margin内部删除分离带钳位 / 删除内部状态 | 分别命中 `separated-report-band` / `exact-penetration` 目标断言 |
| 内部折棱横截守卫删除 | 屋脊纯切向不应算穿面断言失败 |
| interlock上探构造禁用 | 原剖面反例无法给出合格安全返回；具体内部突变原因随桥接证据记录 |
| 新过滤误差界缩小10倍 | **不适用：本单没有新增过滤或改已有误差界**，不伪造这一项已执行 |
| 新缓存键去对象身份 | **不适用：本单没有新增缓存层**；既有完整内容键本来不依赖对象id，删不存在的id不是有效突变。已有payload的串用及变更门另核，不能冒称任意可变源缓存安全 |

[A1 突变绑定](file:///D:/eab-wt/cx-e2/reports/codex/E5a2_evidence/a1/mutation_coplanar.json)、[整数内部突变绑定](file:///D:/eab-wt/cx-e2/reports/codex/E5a2_evidence/integer_mutations.json)、A3两份mutation与目标日志见证据索引。注入通过真实函数源码编译到独立进程或pytest monkeypatch，不在枚举之后添假盖，不永久污染生产源。

## 7. D：验证过程、失败分类与复跑

最终命令：

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -X utf8 reports/codex/E5a2_evidence/verify_run.py run final -- -m pytest -q -p no:cacheprovider tests --basetemp=reports/codex/E5a2_evidence/tmp/final_pytest --tb=short --durations=30 --junitxml=reports/codex/E5a2_evidence/final.xml
```

运行器保存命令、环境、开始/结束、墙钟、日志哈希、所有src/tests/tools Python源的前后SHA256。本轮开始时所有其它profiling/测试已停；发现5个失败后，为定位是否应迁移旧门而并行作了短诊断，生产源和测试继续冻结。**故这次完整失败运行的耗时不是干净独占提速成绩**，也不能把后续正确性未满足的运行当900秒验收。

`python -X utf8 tools/fix_canon_ptrs.py --apply` 已随定义行移动重跑，最终文档指针门在全套内验收。README三维行、canon_map、exact_predicates_plan、exact_3d_design均区分已验证模型、有限描述符和待E5b事项；旧E5a报告不改历史。

中间失败没有藏起来：

- **编排/输入错误**：profile runner路径层级错误；bb52快照少两份引用JSON；初版快照缺fixtures时仅收集7724节点。补齐原始输入后完整收集7907、六profile全部绿。详见性能报告，不把失败profile算有效基线。
- **验证/契约错误**：旧理想边界断言被实际精确微贯入/微分离证伪；保持原格改为独立精确核验，逐项台账。A3 G2旧helper仍按gap舍入判窗，迁移后恢复。
- **集成错误**：interlock候选簇复用状态暴露；修复实际返回的验收，不回退谓词。一次注释编辑误删dataclass字段，由新增门立即捕获并恢复，失败日志保留。
- **过期诊断**：首轮 `full_diagnostic` 与源码编辑重叠、哈希变化且仍跑旧interlock正tol路径，在668.79秒处停止。它不是完成的全套，不作为性能成绩或全绿证据；保存了准确被停PID/命令与日志。

<!-- FINAL_VERIFICATION_START -->
**最终日志最后一行（原样）**：

```text
49 failed, 7953 passed in 1566.87s (0:26:06)
```

墙钟 `1578.669441 s`；时间 `2026-10-11T20:46:37Z` → `2026-10-11T21:12:57Z`；退出码1；src/tests/tools前后哈希相同，结束后再次读回一致。JUnit共8002条，通过7953、failure/error 49、skipped 0。原7907节点无缺失，15个改写旧测试的装饰器不变，18项函数/辅助台账保存全文。62个fixtures文件与初始字节副本全部相同；HEAD仍为`5b09ea3`。

当前doc指针以 `fix_canon_final2.log` 和全套 `test_doc_pointers.py` 为证；追加PARTIAL说明后又运行 `fix_canon_postreport.log` 与 `doc_final.log`，1 passed。其余编排失败日志仅作过程审计，不计入最终成绩。

附加样式审计：`git diff --check` 仅报 `test_geom3_overlap_witness.py:389` 末尾多一个空行；为保持冻结测试字节未再编辑，见 `final_delivery_qa.json`。这不是测试通过声明。


### 完整失败分组（由最终JUnit生成）

| 测试 | 失败格数 |
|---|---:|
| `tests.test_interlock_sensitivity::test_steep_gate_has_teeth_vertical_tie_window` | 1 |
| `tests.test_interlock_walls::test_vertical_walls_do_not_hijack_the_escape_height` | 4 |
| `tests.test_invariance_interlock::test_brute_oracle_is_exact_zero_at_rest_and_scales` | 3 |
| `tests.test_invariance_interlock::test_margin_reference_cases_are_what_they_claim` | 1 |
| `tests.test_invariance_interlock::test_margin_layer_is_rigid_motion_and_unit_invariant` | 40 |
<!-- FINAL_VERIFICATION_END -->

## 8. 遗留、风险与 WO-E5b 交接

### 必须先处理的退出阻塞：不是改容差或放宽断言能解决

**竖墙最早逃逸存在生产缺口。** 保留原 `test_interlock_walls.py` 四组、每组20个seed，另外诊断完整80格。原0.2高度是在舍入前理想几何上的真值；四组seed0在0.200001均有独立有理双内点，证明原始扰动数据的侧向微贯入真实存在，不能继续硬套0.2。

更重要的是，**7格当前候选路径返回约1.2，但更低高度已严格分离**。每格全部336对源三角形有独立整数严格分离轴证书，再用独立Fraction射线排除包含；不使用生产几何原语，也不把U形体假装为星形。其共享生产谓词的brute结果只作佐证，主反证是独立严格分离证书。因此，把旧门改为“返回高度安全”会丢掉原最早逃逸要求，本单明确不这样做。

[竖墙80格结果、7格严格反证及E5b建议](file:///D:/eab-wt/cx-e2/reports/codex/E5a2_evidence/a1/walls_handoff.md)。E5b应迁移真实近竖直特征事件/最早根与冻结标签，不把近竖直真实事件一律当法向噪声去掉。这个问题也限制第3节桥接：它给出的只是安全构造高度，不是合格的全局最小逃逸答案。

**旧 steep 突变牙失效，仍原样保留为失败。** 新精确验收不再选择略贯入的错误低支，旧 vertical-window 突变虽然漏报带内另一支，却不再触发原“可微但给另一支斜率”断言；故旧牙 DID NOT RAISE。独立草案用精确双特征在程与法向报告带充分条件，保留72个原格和全部旧断言，新增“带内漏支”断言；纯内存验证可杀死同一生产内部突变，但**未应用到工作树测试**，不冒称该门已修复。[草案与验证](file:///D:/eab-wt/cx-e2/reports/codex/E5a2_evidence/a3/steep_tooth_proposal.md)。

**另外44格旧不变性门尚未迁移，仍计失败。** 完整运行结束后逐项独立核验：

- 3格 brute 沿原无起伏方向滑动后，逐顶点舍入产生真实微贯入；每格都有不在任何源三角平面上的严格共同内部有理点，所以不能要求实际输入必有高度0。此证书不把 brute 当独立 oracle，也不证明其输出是精确最小根。[3格诊断与证书](file:///D:/eab-wt/cx-e2/reports/codex/E5a2_evidence/a1/invariance_brute_slide_handoff.md)。
- 41格 margin（14个 touch 运动格、26个 subtol 运动格及1个 subtol 参考）全部由独立严格星核/四面体并集整数SAT证实真实内部相交；生产零tol为1，唯一贯入哨兵、delta=0/.01s的gap与INSIDE字段均正确。这里是旧“理想相触/亚容差贯入无哨兵”断言与新契约冲突，不是这41格新生产缺陷；但测试尚未按“不弱于原门”完成迁移，因此不能计绿。[41格逐项审计](file:///D:/eab-wt/cx-e2/reports/codex/E5a2_evidence/a3/margin_failed_exact_audit.md)。

最终49失败完整归类为：**4个竖墙参数组（含真实最早根缺口）+1个失效旧突变牙+3个未迁移brute零高度门+41个未迁移margin门**。95个新增格均通过，不能据此掩盖49个旧门失败。

### 其它边界和下一单范围

1. **一般折面法锥未完整迁移**：A2按允许方案交付语义边界，后续需三角化局部特征、来源映射、真实接触见证与完整法锥独立门。凹块全局E构造也不在本单。
2. **margin**：除文档外未动；实际微贯入现在按精确入口走哨兵，但其余构造距离、报告状态与窗口仍需E5b逐分支审查。不要把底层精确等同于整个margin精确。
3. **entrance3**：候选/根/聚类/时间/后继构造分支未全部精确；返回浮点时刻逐顶点舍入后可为微分离，原24格最大精确时刻误差 `6.709306307797114e-16`。这是已量化限制，不是exact endpoint证书。
4. **interlock / frozen**：本单桥接确保实际返回位形非贯入，保留旧nominal标签政策，不保证任意折面体全局最小根、精确tied集合或所有导数正确。零高度raw簇未作完整extent验收；不要把其标签提升为返回点的真实接触见证。冻结公式仍应独立审查微叉积、方向和分母。
5. **既有非 canonical 可变对象缓存缺陷**：HEAD已存在 `_convex_view` 缓存失效缺失。先升高box顶点使view成为另一个对象，缓存后原地平移源verts，旧源membership可答1而同坐标新对象答-1。不是本单整数payload引入，但明确未修；目前应视对象为不变，修改后重建。后续需源verts/faces内容签名及失效门。[复现与限制](file:///D:/eab-wt/cx-e2/reports/codex/E5a2_evidence/cross_review_performance.md)。
6. **性能后续**：从最终文件耗时与当前表面profile继续，优先减少非凸临界表面的重复精确三角相交/成员构造，再考虑完整误差界过滤或明确不可变缓存。已有两个仅在scratch验证的算法草案：精确布尔三角相交（1300对逐值对拍）与横截严格内部正证书；**未部署、未计入已实现优化**，局部6倍不等于全套速度。[下一步性能证据](file:///D:/eab-wt/cx-e2/reports/codex/E5a2_evidence/next_performance.md)。不得回退tol吞微贯入，不得减网格。新缓存应先定义可变性契约；上述既有失效问题未解决前不能泛加缓存。
7. **验收边界**：只有本工作树代码/测试证据；没有正式G6、新worktree绿、姊妹求解器切换或工程验证。本单未写姊妹观察表，因为发现的是本库问题，非姊妹缺陷。

<!-- OUTCOME -->
E5a2_PARTIAL：全套49失败（竖墙最早逃逸、旧门语义迁移及突变牙）；≤900s未达，实测墙钟1578.67s
