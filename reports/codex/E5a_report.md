# WO-E5a 执行报告

## 结论与信任边界

**工单作废／不可验收：已确认违反仅工作树写入红线。** 一次 G2 pytest 漏设 `--basetemp`，在 `C:\Users\m1517\AppData\Local\Temp\pytest-of-m1517\pytest-1058` 留下54文件、55目录（含根）。时间、测试名称和树内复跑字节一致性支持归因；这不是仅有风险，而是已确认写入。未删除或移动树外文件，补跑不能抵销违规。[完整路径、哈希与归因局限](file:///D:/eab-wt/cx-e2/reports/codex/E5a_evidence/scope_violation.json)。该审计也不能证明其它直调 pytest 没有树外临时写入，不能把已确认数量当作全部外部副作用上限。

以下仅是**留树技术状态和后续审查材料，不是有效工单交付**：精确凸路径、三维 G0 零豁免、若干一般表面精确原语、精确局部盖及保守过滤已落地；一般三角化实体的完整三态相交和旧入口接线尚未完成。新增 `exact_*` API 不能冒充旧 `polyhedra_overlap` 已精确，也不宣称 G6 通过。

源码、测试和文档编辑在 `D:\eab-wt\cx-e2`，分支 `codex-work`；但上述测试临时文件越界，不能声称“只修改本树”。起始 HEAD 为 `a47933682d9764b15e20d7200a6a37a1e8f14aee`，工作树起始干净。没有 commit / push / reset / checkout / stash / worktree；没有修改姊妹仓库或删除 fixtures。用户禁止 worktree，所以验证只适用于本工作树，不满足常驻纪律 D/G6 的里程碑退出条件。后续统一 runner 同时设 TEMP/TMP 与显式工作树内 `--basetemp`，仅用于防止再犯。

- [实现前设计](file:///D:/eab-wt/cx-e2/docs/exact_3d_design.md)
- [初始状态与回滚文件哈希](file:///D:/eab-wt/cx-e2/reports/codex/E5a_evidence/baseline.json)
- [初始字节备份](file:///D:/eab-wt/cx-e2/reports/codex/E5a_evidence/tmp/pre_e5a.zip)
- [完整证据索引](file:///D:/eab-wt/cx-e2/reports/codex/E5a_evidence/artifact_index.md)

## 1. 设计选择

### 1.1 凸块与一般表面是两个模型

显式凸 API 定义为 **conv(输入顶点集)**。输入面的角色是来源提示，而不是要求舍入后的四点仍然共面。精确微凹由凸包填平，精确微凸脊必须保留；仅精确共面的相邻面可合并。这一选择让凸 E 定理有确定对象，代价是它不再等同于任意输入 face-ring 表面。

一般 `Polyhedron` 不暗中凸化。新表面原语将非平面多边形确定性投影耳切成三角形；凹多边形不作错误扇形填充。但旧一般实体相交入口仍未完整接通，这部分属于本单未完成项，而不是“留给 E5b 就算 E5a 完成”。

### 1.2 标签不能跨模型混用

`exact_convex_view` 仅在原 faces 已恰好是全部精确支撑 facet 时保留原编号；否则产生确定性 canonical view，并记录 `source_vertices` / `source_faces`。新 facet 可能只覆盖原面的一部分，也可能不属于任何完整原面。凸成员、局部 facet 与 `facet_normal3` 解释的是 canonical 标签。

一般单盖和枚举仍解释原 face-ring 标签。局部 Newell 面向量及棱/锥分支已改精确，但这不是任意非平面折面实体的完整法锥语义。冻结适配的测试把源面 EE 与凸 facet EE 分别核对，禁止拿相同数字下标冒充同一特征。

### 1.3 三票比较同一个精确 E

差点必须是 `Fraction(b) - Fraction(a)`，不能先做浮点减法。G0 的独立 oracle 在调用被测凸化前保存原始顶点；其独立整数/有理数凸包、SAT、支撑维数不调用被测几何原语。

- 票一：随机样本以及 **E 的全部顶点、全部棱中点、全部 facet 重心**逐个检查内/外/边界，零跳样。
- 票二：局部严格 VF/FV/EE 标签与独立精确支撑集双向全量一致，退化支撑按仿射维数计数，重复标签也报错。
- 票三：精确锥相对内部相交产生的差点集合等于 E 的极点集；没有 low / low_e / ambiguous 豁免。

旧兼容计数字段保留，但必须为零，不能参与免责。单方凸化丢源顶点、票一跳过边界、票二漏标签、票三多报24个假极点均有实路径红门。

## 2. 实现摘要

| 区域 | 已实现 | 明确限制 |
|---|---|---|
| `predicates.py` | orient3d、二维点积/叉积符号的保守过滤与 Fraction 回退 | 不声称所有 Fraction 热点均已过滤 |
| `geom3.py` / `exact_geom.py` | 精确凸包、精确共面合并、canonical 来源映射、投影面内判定、显式精确成员/线段/三角相交/凸 SAT | 旧一般成员和实体相交入口仍有噪声/启发式 |
| `covers3.py` | 未归一化精确面向量/棱向量、局部锥、严格性、精确交点参数和在程、精确最小范数单形锥交、精确凸成员 | 一般非平面源面 Newell 语义；外层 gap 搜索窗仍读浮点构造 |
| `g03.py` / `g03_exact.py` | 独立精确 E 与三票；删除分辨带、细条、拟合平面和低高度豁免 | 限凸模型定理；不是凹块全局 E |
| `_seg_seg_distance` | 第五轮近平行耦合距离改有理平方距离；缩放开根避免可表示距离被平方下溢吃掉 | 普通浮点距离输出不声称精确实数构造 |
| `frozen.py` | EE primal 朝向及微叉积安全构造最小适配，正常非退化 Dual 值/导数兼容门 | 微交叉 Dual 构造仍留 E5b |
| `interlock.py` | `_normal_noise` 的浮点棱叉积为零时，用精确原始棱补算可分辨性报告，避免新微交叉 EE 导致除零；相关候选/逃逸定向34格保留原断言并通过 | 旧逃逸噪声政策不变，不宣称精确逃逸定理；另有 `test_invariance_interlock.py` 的舍入边界门迁移，见对应台账，不能说全部旧互锁门零改写 |
| G2 导入/对账工具 | 原始坐标精确凸包与精确回映；固定源顶点集合排序保留基础报告；不在精确 facet 上的 legacy 三角保留引用并报 violation | 运动后舍入造成的真实差异不被强行抹平；alias 导入噪声政策仍未迁移 |
| `margin.py` / `entrance3.py` / LP | 本次未改这些文件 | 它们的完整精确化仍未做；LP 既有精确证书未为提速降级 |

另修独立代理复核发现的两处实错：非平面 seed 面与共面面错误归并，以及精确平方转 float 后开根导致的上下溢。回归又暴露真实细条 facet 的浮点 Newell 向量抵消为零：构造侧增加精确回退，`face_area` 安全缩放；原 `test_entrance_block_scales` 全部断言未改，连同新门 **437 passed in 21.12s**。

## 3. 第五轮责任项处置

以下 raw 编号为 JSON **零起始下标**。起始 HEAD 的复现来自字节快照隔离副本，不把旧 b6126cf 报告直接当当前复现。

| raw / 旧位置 | 起始 HEAD 观察 | 本次处置 |
|---|---|---|
| 23 / geom3:604 | 原长梁/薄壁族仍有8/40与5/40旧贯入结果 | **未关闭**；新精确线段/三角原语有门，旧相交入口未迁移 |
| 30 / geom3:925 | 真值4.579391932681403e-9，旧 oracle 4.579515276060437e-9，margin 抛错 | 修复精确近平行距离，恢复旧分支突变报红 |
| 43 / covers3:247 | 原屋脊四对真极点被重心阈值删掉 | 精确纠正单形/KKT，四对保留；绝对重心阈值突变报红 |
| 28 / g03:148 | 四个尺寸比/偏航格报假 hull_anomaly | 删除噪声尺，四格零豁免通过 |
| 41 / g03:152 | 原 yaw=10^-8.75 屋脊输入假红 | 原输入精确支撑通过，无细条压平 |
| 42 / g03:82 | 原偏心四面体/微倒角在工程坐标产生假 facet | 删除非共面平面拟合；0/100/1e3/1e4/1e6 原格全核 |
| 39 / g03:275 | 默认 facet_vote3 抛 NameError(L) | 默认精确比较路径有独立门 |
| 38 / g03:441 | 每对顶点都声称极点仍 passed=True，豁免24项 | 同类实路径突变现在 mismatch=24、passed=False、豁免0 |
| 49 / g03:437 | 原格 loc2/glob0/amb3/drop2；宽度400倍在原四格子集逃逸 | 所有宽度删除；强制零跳样/零丢标签/零豁免 |
| 45 / hull test:271 | 旧185门在 fn×100 后照绿 | 噪声自检改精确全输入支撑证书，忽略真实2^-80凸出点的内部缺陷被抓 |

[机读处置与逐条证据](file:///D:/eab-wt/cx-e2/reports/codex/E5a_evidence/g6e_dispositions.json)。相邻 covers 旧缺陷随精确化改善，但没有逐项完整基线重放的，不另冒称“全50条已关闭”。

## 4. 测试改写，不用绿掩盖数据变了

旧门要求“舍入旋转后仍六面”“端点仍恰好在程”“允许丢两条看不清的 facet”等，与精确给定输入契约冲突。改写保留原参数格，以独立 Fraction 支撑集、Gram 解、极射线/绕数逐个分类，并保留原距离、体积、状态和稳定区缩放检查。

旧内部缺陷注入从不再驱动判定的浮点构造入口移到实际 raw-rational 判据入口；原红断言与几何输入不变。测试不删除、不新增 skip/xfail。库存审计检查起始快照的全部测试函数仍存在，并比较 skip/xfail 引用；它不替代人工逐条审核断言强度。

- [逐条机读旧/新/不减弱理由](file:///D:/eab-wt/cx-e2/reports/codex/E5a_evidence/test_rewrites.json)
- [测试库存审计](file:///D:/eab-wt/cx-e2/reports/codex/E5a_evidence/test_inventory_audit.json)

收尾只读复核实际发现两处初版门强度缺口，未用“全绿”掩盖：退化 facet 计数没有独立替代；三族凹几何把原 float 输入替换为 Fraction 输入而未双轨保留。为此中止了尚未完成的全套（413.268秒，不计通过），补门后才重新冻结：

- membership 原20格现逐项对比原坐标独立完整支撑集、strict/degenerate计数；另20格精确仿射输入保留旧7/3/13与0/6/8解析门。真实内部退化计数倍增会被目标断言抓住。冻结目标验证 **93 passed in 14.88s**。
- pinch/U端/U-L三角面归并的 **16/16 原浮点格逐bit恢复**，保留原终止/体积/流形门；独立 Fraction 平面、邻接、有向边界证书看护精确归并，并保留额外精确仿射解析门。漏并和近似误并两项内部牙命中归并边界断言。冻结目标验证 **53 passed in 0.87s**。

[只读审计及闭环](file:///D:/eab-wt/cx-e2/reports/codex/E5a_evidence/final_test_evidence_audit.md) · [计数补门说明](file:///D:/eab-wt/cx-e2/reports/codex/E5a_evidence/covers_membership_support_counts_notes.md) · [原输入逐bit审计](file:///D:/eab-wt/cx-e2/reports/codex/E5a_evidence/merge_rounded_input_audit.json)。这些补门不抵销范围违规，也不是独立 G6。

## 5. 过滤与性能

orient3d 纯 binary64 快路采用 `(7+56u)u·permanent`，另含随乘数传播的最小次正规绝对项；Fraction 快路额外涵盖原有理数据到浮点候选的转换误差。任何非有限或无法证明符号的候选退原值 Fraction。二维双线性过滤同样含转换、乘加和下溢绝对项。面内投影使用逐运算向外取整的区间必要条件，不能证明则回退有理数。

- 门内 **7301 orient3d + 4904 双线性**逐项对拍零差，另有 **10000 混合指数（−1074…1023）**压力对拍零差。
- 面内区间过滤 **972 格**与纯 Fraction 对拍，含边界、工程坐标、次正规。
- 30000 对性能样本零差：一般 float orient3d **14.24×**，一般 Fraction **1.324×**，近平面 **0.967×**（经常回退，不能假称加速）。
- bb52 指定 no-VV 慢门 **19.31s → 10.204s**；精确棱框纯缓存使单个 interlock 枚举冷进程 **2.3828s → 1.7282s**。这些不是整套≤600秒的证据。
- LP 既有过滤/精确证书不变；二维测试 oracle 只提前转换坐标/差分，同3000组、全部点对和断言保留。

[过滤界、对拍与基准详情](file:///D:/eab-wt/cx-e2/reports/codex/E5a_evidence/filters_report.md)。最终整套计时见第7节，不用子集或有其它本任务测试并行的计时冒充。

## 6. 指定突变

全部在被测函数内部打入，保存了失败断言；隔离副本或进程内恢复，不把假数据追加到输出算作完成。

| 突变 | 目标红断言 |
|---|---|
| orient3d 过滤相对界 ÷10 | 真 +1 被快路判 −1，过滤/Fraction 对拍直接错号 |
| 凸包保留共面非极点 | hull 顶点数必须8 |
| 精确共面改近似 | 真微脊必须留下7个面 |
| 棱弧严格 > 改 >= | 弧端点必须是边界而非严格 |
| 锥交恢复浮点1e-12阈值 | 原真极点必须保留 |
| 单形恢复绝对重心带 | 原点在单形外不得返回零最近点 |
| G0 票一跳过边界 | 全26个方块 E 边界探针必须检查 |
| G0 票二比对丢一个标签 | 完整标签对比差集必须为空 |
| segment 去掉面内条件 | 面外穿平面线段不得算穿面；新精确与旧入口均测试 |
| seg-seg 近平行恢复独立浮点参数 | 第五轮独立精确距离必须在2ulp内 |

共 **11 个内部突变结果**（segment 的新旧入口各一次），均命中目标断言。另有裕度枚举漏首个见证的内部缺陷，完整集合门点名缺失 VF 标签。
[机读突变表](file:///D:/eab-wt/cx-e2/reports/codex/E5a_evidence/mutations.json)。旧宽度突变逃逸原样保留在第五轮处置证据，不计作新门杀死。

其中五项几何突变又在最终生产源上重放，新增 [带源码与目标测试哈希的记录](file:///D:/eab-wt/cx-e2/reports/codex/E5a_evidence/geom_mutations_final.json)；旧无快照绑定的记录仍保留，不倒填成新证据。第4节三项收尾补牙为额外覆盖，不混充上表指定突变。

## 7. 最终全套

最后一次完整回归的 pytest 末行原样：

```text
7907 passed in 1838.73s (0:30:38)
```

独立进程 wall clock：**1855.871 秒**；运行前后全部 `src/`、`tests/`、`tools/` Python 文件 SHA256 无漂移，生成本结论前再次核对一致。完整命令、文件哈希、返回码见 [full_leave_tree_final.json](file:///D:/eab-wt/cx-e2/reports/codex/E5a_evidence/full_leave_tree_final.json)；[完整日志](file:///D:/eab-wt/cx-e2/reports/codex/E5a_evidence/full_leave_tree_final.log)、[JUnit](file:///D:/eab-wt/cx-e2/reports/codex/E5a_evidence/full_leave_tree_final.xml)。

命令为 `PYTHONDONTWRITEBYTECODE=1 python -X utf8 -m pytest -q -p no:cacheprovider tests --basetemp=reports/codex/E5a_evidence/tmp/full_leave_tree_final_pytest --tb=short --durations=20 --junitxml=reports/codex/E5a_evidence/full_leave_tree_final.xml`，另显式设 `TEMP/TMP` 到本树证据 tmp。此次完整测试期间没有其它本任务测试并行运行。

600秒目标：**未达到**。纯过滤微基准的加速不能覆盖精确三维几何、一般互锁枚举和新增完整独立 Fraction 候选 oracle 的成本；慢门逐项见日志。没有为达时限删格、skip/xfail 或减少边界探针。

JUnit 各测试文件耗时加总（非热点函数 profiler；包括测试与独立 oracle 成本）：

| 测试文件 | 格数 | 秒 |
|---|---:|---:|
| `tests.test_invariance_interlock` | 515 | 456.857 |
| `tests.test_invariance_geom` | 2406 | 277.182 |
| `tests.test_interlocking` | 17 | 176.497 |
| `tests.test_interlock_sensitivity` | 41 | 129.449 |
| `tests.test_covers3_g0_vote2` | 95 | 102.824 |
| `tests.test_bb52_g1` | 17 | 89.634 |
| `tests.test_interlock_escape` | 19 | 67.689 |
| `tests.test_frozen_lowdim` | 15 | 47.277 |

[全部文件计时](file:///D:/eab-wt/cx-e2/reports/codex/E5a_evidence/performance_breakdown.json)。未把测试耗时归因于某个未经 profile 的生产函数。

已执行 `python -X utf8 tools/fix_canon_ptrs.py --apply`，最后一次为 `0 rewritten; 0 kept`。全绿只表示当前留树回归通过，**不解除范围违规，不使工单重新有效，也不是新 worktree/G6 退出**。此前中止/失败的分组日志全部保留，不冒充最终结果。

## 8. 未完成清单与 E5b 交接

1. **本单仍未完成**：旧 `polyhedra_overlap` / `point_in_polyhedron` / `segment_crosses_face` 的一般三角化闭表面三态精确语义；尤其共面相交/共同棱附近的实体内部重叠证书。不能以新精确 API 的存在宣布接线完成。
2. **本单仍未完成**：一般非平面源 face-ring 的局部盖尚不是三角化折面实体法锥；原始面和 canonical convex 标签必须严格分开。
3. **精确窗口余项**：枚举外层仍比较构造 gap；`membership_convex3` 的正 tol 兼容窗是支撑平面距离带，而非完整欧氏偏移体。
4. **E5b 适配点**：margin/entrance3/interlock 的分支及理想边界并列不能继续混用旧噪声规则；`margin.entrance_block_convex` 仍先浮点构造差点。frozen 的 EE primal 已最小适配，微叉积 Dual 的值/导数稳定构造未做。
5. **验收边界**：所有本次新代码和重写门均待所有者审查及正式独立六路 G6；全绿不是理论全域证明或工程验证。600秒性能目标必须按第7节实测判定。

E5a_BLOCKED：测试临时文件已写入授权工作树之外，按用户规则整单作废；技术实现亦有明确未完成项。
