# WO-C1E：eab2 C1 二维一般凹简单环实现与验证报告

## 结论与信任边界

**作者实现与自动验证：通过；里程碑验收：PARTIAL。** 尚需 Claude 指派的一路非作者对抗核查（0 critical / 0 major），以及所有者安排的新鲜 Git 工作树复现。作者自身三个内部缺陷注入不代替独立核查。H1 本次使用字节导出副本，不是新鲜 Git checkout。

- 工作树 `D:/eab-wt/cx-c0`，分支 `eab2-c1`，回滚/来源锚 `8269d1d5f4896e74b5186583f9784d700a189a2c`；本单没有 commit / push / reset / checkout / stash / worktree / branch，也没有安装/下载。交付是该基线上未提交的工作区修改，不把基线提交冒充这些新源码的产生提交。
- 设计 SHA-256 `6d174ecc4f1326d5bac21c56c8d333485fb50bbaef3a12150e94eaff14cb4dac`；最终测试 DLL SHA-256 `dd64762305f62b56b3aa985f1988b36bc619d1dbc367942ae6a9c40fca66dbf8`，构建产物忽略、不入库。
- 构建身份 `eab2-c1;compiler=MSVC-19.44.35227.0;toolset=14.44;isa=x64-SSE2;boost=1.86.0-et_off;fp=precise-contract_off;crt=MD;cxx=20`；实际 `cl /Bv`、13 条编译命令、Ninja 头依赖和 DLL 身份交叉审计，而非只读 CMake 声明。
- 未改 `src/eab`、设计正本、静态准入表、vendor 或姊妹源码。Python 是独立运行的生产裁判，不导入 DLL helper；差分不是独立数学定理证明。
- 开工**仅跑快档**，开工全档未执行；这是流程偏差，收尾四分片全绿不能倒写成开工全档已跑。本单未因文档整理重算冻结证据。

关键入口：[机器清单](C1E_evidence/verification_summary.json)、[交付文件清单](C1E_evidence/deliverables.md)、[完整哈希与只读边界审计](C1E_evidence/integrity.json)。

## 1. P0/P1/P2 对照

| 工单 | 实现 / 证据 | 状态 |
|---|---|---|
| P0-1 单无洞简单环、binary64 精确域、平直顶点与原 ID | Body 输入门；ABI 错误矩阵；657 例输入 bits/ID；`test_geometry2.cpp::validation_and_ids` | 已实现/作者门绿 |
| P0-2 凸分解→凸胞差→闭 E / 开 O，完整 T2b 与双三态 | geometry2；CONTACT 开段/端点/孤立点；active-halfspace 两侧占据导出 ∂E | 已实现/差分绿 |
| P0-3 exact 导出、Python 双方规范化、逐层双向查验 | `C1_DIFF selected=657 completed=657 mismatches=0 layer_queries=100086` | 0 失配 |
| P0-4 body / E / 查询 / exact result ABI | C++ ABI 764 断言；生产 DLL C 头测试；测试符号不泄露 | 绿 |
| P0-5 C0 小项 | UNDERFLOW_ZERO、实际构建身份、AVX guard、代际复用、工作预算 | 绿，详第4节 |
| P1-6 0 处局部胞/切锥/原始关联与排除证据 | 114 归档记录、605 对、7197 条 raw sources；逐项含端点/原 ID | 0 失配 |
| P1-7 至少10⁴合法近退化例 | 10000 个完成，全规范集合与局部证书差分 | PASS |
| P1-8 元门 | 17 项：flags0..7+循环/CW/交换/旋转/反射/尺度/平移 | 绿 |
| P2-9 正式及20×40规模 | 190 对精确 broad phase；31 边邻+24 对角VV=55；实测55对 | 只报告，不设性能门 |

## 2. Python → C++ 移植与具名守护

以下为实现者只读对照，不是独立核查结论。原始独立文件：[geometry_port_map.md](C1E_evidence/geometry_port_map.md)。

| Python 来源 / 合同 | C++ 对应 | 具名门及差分材料 | 对照边界 |
|---|---|---|---|
| `global_entrance._ring`；设计 §1.2 | `Body::Body`、`Body::from_bits` | `validation_and_ids`；harness `run_case` 核规范化环、原顶点/边 ID、全部输入 bits | 拒少于 3 点、零边、非相邻交会/触碰、回折、零面积及非有限 bits；CW 反向后保留原 ID；不删 Body 的平直顶点；`-0` bits 原样保留，几何值为 0 |
| `exact.signed_area2` | `signed_area2` | `validation_and_ids`；补充 `geometry_fastpath_probe.py` 逐项比较面积 | 有理精确坐标差后求和，不消费浮点面积 |
| `exact.convexity_violation` | `convexity_violation` | `validation_and_ids`、`convex_and_covers`；直接凸快路探针 | 正面积、零边、反射/回折及极角下降次数；未声称逐字相同错误文本 |
| `exact.entrance_block_exact` | `entrance_block_exact`、`ExactEntranceBlock/Facet` | `convex_and_covers`；补充探针 90 对逐项比较 ordered vertices、facets 的 label/start/direction、pairs | 完整保留凸快路 VE/EV/FF 与平直 facet；与一般凹入口的 cell hull 算法不是同一条执行路径 |
| `exact.membership_exact` | `membership_exact` | `convex_and_covers`；补充探针 1260 个顶点/边中点/内部/外部查询 | 凸入口专用 `-1/0/1`；不是全局 topology |
| `exact.vertex_side_exact / ve_side_exact / ev_side_exact` | 同名函数 | `convex_and_covers`；补充探针 2772 个 VE/EV 精确符号；零窗与显式窗口盖差分 | 平直法锥需额外同向条件；反射顶点不因隐藏容差接纳 |
| `exact.polygons_overlap_exact` | `polygons_overlap_exact` → `Entrance::membership` | `concavity_and_strata`；`run_case/compare_exports/verify_local` | **语义移植而非重写第二份 SAT oracle**：C++ wrapper 复用全局开胞并集。独立裁判仍是 Python，不得把此 C++ wrapper 当作独立 oracle |
| `exact.entrance_membership_exact` | `entrance_membership_exact` → `Entrance::topology` | `concavity_and_strata`、`tight_contacts`；双向所有层样本查询 | CONTACT 内缝/孤立点可同时是拓扑 INTERIOR |
| `covers.ve_cover / ev_cover` | 同名函数；`ve_window_side/angle_window2` | `convex_and_covers`；`compare_cover_rows` | gap、投影、法向以精确 recipe 表示；显式长度/角窗仅扩大接受集，不把扩窗态提升为 strict |
| `covers.vv_cover` | `vv_cover` | `convex_and_covers` 的严格/扩窗/重合分支；`compare_cover_rows` | 重合 VV 法向为 null；非重合保留精确方向与平方距离；`strict` 和 `window_active` 分开 |
| `covers.enumerate_covers` | `enumerate_covers`、`covers_exact_json` | 全语料 2530 个零窗盖；26 个 `covers_e3/*` 算例各 4 组窗口，共 104 组显式窗口检查 | 核 label、strict、window_active、param、两见证点、gap²/sign、法向同向；不是只比较盖数量 |
| `global_entrance._triangulate / _merge_convex_parts / _hull` | `triangulate / merge_parts / hull`；`Entrance` 构造 | `concavity_and_strata`；`determinism_and_exact_transforms`；657 对全局差分 | 耳切只在工作副本移除平直点；凸合并要求共享边端点和精确等面积 hull 证明；一般凹域绝不整体凸包替代 |
| `global_entrance()/GlobalEntrance2.membership` | `Entrance`、`membership`、闭 AABB + `cell_state` | 独立矩形并集 oracle `concavity_and_strata`；所有层样本双向差分 | 不同 E 对象不共享未物化几何；浮点不提名/过滤；OUTSIDE/CONTACT/OVERLAP 与 topology 分开 |
| `GlobalEntrance2.topology` | `topology/directional_state` | `tight_contacts`；harness `layer_samples`；局部扇区复核 | 精确活动半平面及射线扇区覆盖，不把 O 当作 int E |
| `GlobalEntrance2.cell_edges` | `cell_edges` | `concavity_and_strata`；导出凸胞/下游细分与样本核验 | 规范化无向胞边集合；分解和人工缝可与 Python 不逐条相同 |
| `GlobalEntrance2._contact_subdivision`（T2b） | `raw_segments/build_skeleton/contact_segments/contact_points` | `tight_contacts`；`canonical` 核 CONTACT 段、全部来源标签、必要端点及孤立点 | 全部原始 VE/EV 先排布，不用有效盖法锥预筛；CONTACT 开段及零维点均保留 |
| `GlobalEntrance2.subdivision`（T1/T2/T2b） | `subdivision`，compact 开/关 | `concavity_and_strata` 的 Euler 与逐层状态；flags 0–7 元门；`face_regions` | 允许不同竖直分片；比较规范物理集合，不比较内部剖分枚举序 |
| `GlobalEntrance2.clipped_covers`（T2a） | `clipped_covers` | `compare_covers` 的标签共线开段集合与逐片邻侧复核 | 不导出 Python `side_points` 的特定有限采样坐标；导出精确无穷小邻侧三态及 exposed，见 §4 |
| `GlobalEntrance2.boundary` | `boundary` ← T2b 联系段两侧占据 | `concavity_and_strata`；小语料对 Python 原 `boundary`；正式语料对 Python CONTACT 段 topology | **没有移植**产品 `side_probes` 慢路线；CONTACT 段两侧恰一侧属于 E 才为边界 |
| T1a `lock._local_data/_contact_sources/_distance_squared` 所需几何 | `local_origin`、`segment_distance_squared_to_origin`、`local_directional_state`、`local_origin_exact` | `boundary_and_original_ids`、`seam_isolated_outside_overlap`；`verify_local`；`contact_sources_final.json` | 提供局部胞/切锥、原始来源和排除证据；不移植 C3 锁定状态签发、接触力学约束或 LP |

一般凹全局构造不调用独立凸快路，故657例不能冒充对快路facets的直接覆盖。另以[临时只读调用探针](C1E_evidence/geometry_fastpath_probe.py)直接核90个非对称/平直/尺度凸对；[快路报告](C1E_evidence/convex_fastpath_final_r1.json)末行：

```text
C1_CONVEX_FASTPATH cases=90 facets=540 membership=1260 side_predicates=2772 mismatches=0 original_unchanged=1
```

## 3. exact 导出、规范集合比较与局部查询

### 3.1 比较口径

详见[比较方法与订正](C1E_evidence/harness_method.md)，实现为 `tools/eab2_diff_c1.py` / `eab2_c1_exact.py`。没有 DLL 参数硬失败；缺失路径也失败，不进入默认 pytest 收集。负入口证据见 [harness_negative_cli.json](C1E_evidence/harness_negative_cli.json)。

双方分别导出精确 n/d 坐标与状态，**同一个纯 Python Fraction 规范器分别处理双方**：直线 gcd/符号归一；合并极大相对开共线 E\O 段；另外保留来源标签改变的层、端点和孤立点；全部原始 VE/EV 来源段独立比较，未先用有效盖法锥删内缝。二维面按状态归组，精确再切分其有向边界并保留重数，让人工剖分线相消；不是仅比样本、面积或无序去重。有限外框的 OUTSIDE 面形状不作集合对象，但其状态样本仍复核。

C++ 全部层样本交 Python membership/topology，Python 全部层样本经仅测试用有理查询反向核验；主657例双向合计 **100086** 次（不含17元门、发布0点查询和10000例生成器）。小命名例另对 Python 慢 `boundary`；C++ 不移植 boundary/side_probes 慢路线。covers 的窗口/strict/来源及精确投影也核验，显示浮点不回灌为证书。

最终语料为 1763 次出现、657 个有序 bits 去重对（52 命名+605正式）；保留每条来源 alias。包含全部 M3 六族：thin_L / slot_wedge / interlock_section / tight_fit / pocket_hole / collinear，以及 M3b、M3c、E3、tia2d-2 正式 assembly。3 个原有理 `2^-400 + 大平移` 例 RN 后有零长边，明确列为域外，未计入合法通过数。其他非二进有理例比较双方**相同 RN binary64 输入**，不宣称原有理的共线关系保留。

### 3.2 0 处局部证据

`geometry2_local.cpp::local_origin` 与 `eab2_local_origin2_exact` 仅构造必要凸胞和局部数据，首次局部导出要求 `global_subdivision_materialized=false`。每个包含0的胞给活动边切锥；每个排除胞给含等号 AABB 与严格负的精确分离边；所有非关联闭边给精确距离平方界，以 `r=q/(1+q)` 构造严格邻域（r²<q）。该邻域保证局部扇区解释不会跨过另一条边。

`tools/eab2_c1_local.py::verify_local` 独立核所有界与来源，并用原始边扇区的严格邻域样本调用 Python `polygons_overlap_exact`，不使用 C++ 精确 helper。`eab2_c1_contact_sources.py` 再将 raw VE/EV、原始顶点ID、物理接触点及端点关联与归档 T1a ContactSet2逐项比较；OVERLAP 的非法力学分支保持归档拒收语义。

```
EAB2_C1_CONTACT_SOURCES records=114 pairs=605 raw_sources=7197 mismatches=0 status=PASS
```

### 3.3 门的敏感性

三个内部变异分别破坏闭E/开O、孤立接触保留、窗口与strict区别；编译真正被测 C++ 代码后由具名语义断言杀死，不是产出后追加假数据、源码哈希或编译失败。见[内部变异报告](C1E_evidence/mutations_final_r1.json)。这是作者测试敏感性检查，不是 Claude 指派核查。

## 4. ABI 增量与 C0 遗留处置

详见[ABI_CONTRACT](../../eab2/ABI_CONTRACT.md)、[ABI中文分报告](C1E_evidence/abi/C1E_ABI.md)。C0 已有结构不改布局；C1 通过新增结构/函数扩展。

| 族/合同 | 具体内容 | 守护 |
|---|---|---|
| body/E 生命周期 | `body2_create/destroy`、`entrance2_create/destroy`；owner/type/generation全校验，E保有body副本 | `test_abi.cpp::geometry2_matrix/child_context_reuse` |
| 双三态批量 | `query2_batch/membership2_batch/topology2_batch`；body OUTSIDE/CONTACT/OVERLAP 与 topology OUTSIDE/BOUNDARY/INTERIOR 分立；call_status≠mathematical_status | 同上，尺寸/步长/容量/溢出/逐项错误门 |
| exact 与 local | `result_export_exact/local_origin2_exact` 返回库拥有 UTF8 JSON+token；`result_destroy`，context销毁兜底释放 | 生命周期与坏句柄门 |
| 能力 | BODY2/ENTRANCE2/QUERY2/EXPORT_EXACT/LOCAL2/LIMITS2；测试 DLL 另有 TEST_EXACT2，未宣称LP/SE2/rho | `get_abi_info/get_c1_abi_info`、实际导出审计 |
| 资源 | 新 `context_limits2` 默认 work=50,000,000/elements=2,000,000/integer_bits=65,536；显式正数配置，有活子对象拒重配；对象冻结并导出限制 | `configurable_limits_and_transactions`、ABI限额矩阵 |
| cache | NO_MERGE=1/NO_COMPACT=2/NO_CACHE=4；NO_CACHE对每次全局/局部exact JSON导出建临时入口并销毁，不冒充关merge；query/covers不重建 | flags0..7精确元门 |

精确 JSON 采用约分、正分母 n/d；输入 binary64 bits 留存，包括负零。JSON 几何状态沿 Python -1/0/1，ABI 两个枚举各映射0/1/2，合同明确，不以 inside 布尔代替。

| C0 遗留 | 处理与验证 |
|---|---|
| 允许下溢单列显示 | `EAB2_DISPLAY_UNDERFLOW_ZERO=3`；精确零仍VALID；仅调整Python harness显示口径，不改Python数学实现；4483 cases/6003 bits复核 |
| 身份与ISA | 实际cl /Bv对compile_commands与DLL；受控入口 `#if defined(__AVX__) #error`；README明确STL运行时分派AVX2整数代码≠编译目标ISA |
| 槽复用 | 真实复用槽位、单调generation，旧context/body/E/result句柄拒收；代际耗尽映射RESOURCE_LIMIT |
| 文本工作量 | 每有理文本≤4096 bytes；batch values≤65536、bytes≤4194304、长度平方和≤67108864；超限RESOURCE_LIMIT |
| 资源失败恢复 | 算术前保守位长界+拥有结果检查；嵌套限制不得放宽；raw/skeleton/subdivision/export路径回滚本次新缓存，由具名低预算/重复调用恢复门核验，不泛称任意内存故障已穷尽 |

位长预算是算术与拥有值上界，不冒充 Boost 内部临时 limb 或进程物理内存峰值证明。

## 5. 固定种子近退化生成器

seed=20261022；尝试 **10079**，合法唯一有序 bits 输入 **10000**，完成 **10000**，失配 **0**。先构造合法环与已知原点标签，再做ULP、近共线、极窄边、极端指数、方向/旋转和分辨率扰动；拒收先由Python裁判完成，不拿C++筛选期望。拒收不计入10⁴。

| 生成族 | 合法且完成差分数 |
|---|---|
| collinear | 2019 |
| extreme_exponent | 199 |
| isolated_contact | 100 |
| narrow_edge | 1782 |
| near_parallel | 1800 |
| one_ulp_gap | 2000 |
| one_ulp_overlap | 2000 |
| tight_seam | 100 |

| 拒收原因 | 次数 |
|---|---|
| known_label_not_preserved_after_binary64_perturbation | 58 |
| polygon needs at least three vertices and no zero-length edge | 21 |

| 0 处 body_state | 数量 |
|---|---|
| OUTSIDE | 2000 |
| CONTACT | 4200 |
| OVERLAP | 3800 |

并非只查0：每例都走全规范集合、来源分层、正面积区域边界、双向层查询和局部证书。累计独立局部扇区样本 **87200**、来源 **13194**；两向层查询分别 **322334 / 322334**。耗时 420.716s（并发环境墙钟，不作性能门）。

输入分块、逐例journal、SHA256和重跑种子见[generated_final.json](C1E_evidence/generated_final.json)。大型journal仅在忽略的 evidence/tmp 保存，不入库；摘要含路径与哈希。有限随机/构造样本不证明全输入域正确。

## 6. P2 规模测量（只报告）

20块，每块恰40顶点，对齐4×5非凸简单环；共享二进有理锯齿接口。完整190对 broad phase，精确检测 **55 CONTACT / 135 OUTSIDE**，其中 **31边邻接+24对角VV**。没有把31当完整邻接；对全部55邻接冷构造与导出。未执行额外forced190全局构造，也未执行C3 Shi/锁定/多体LP分类。

| 范围 / 秒，中位 / 最大 | C++ 冷 body+E | C++ 全局导出 | Python 对应裁判工作量（见口径） |
|---|---|---|---|
| 正式去重块对 605 | 0.000612 / 0.017826 | 0.009530 / 0.260299 | 0.009411 / 0.361252 |
| 20×40 全部实际邻接 55 | 0.079874 / 0.086268 | 5.796427 / 6.128692 | 3.833166 / 4.119143 |

| 范围 | 原始段 min–max | 交点 min–max | 胞 min–max | 紧凑 V/E/F 最大 | 已存坐标整数最大 bits |
|---|---|---|---|---|---|
| 正式605对 | 32–648 | 9–255 | 1–64 | 68/119/52 | 17 |
| 合成55对 | 3200–3200 | 5789–6109 | 361–441 | 448/858/411 | 16 |

合成局部查询中位/最大 0.040769 / 0.047691s；C++错误记录 0。逐对数值见[正式605对 CSV](C1E_evidence/formal_pairs.csv)、[合成55对 CSV](C1E_evidence/scale_pairs.csv)、[完整测量 JSON](C1E_evidence/scale_final.json)。

口径：C++冷计时含ctypes/ABI，导出含序列化与Python JSON解析；正式diff Python列为GlobalEntrance2+python_export，含原始排布、来源、subdivision及逐层/边界topology，不含canonical比较、clipped_covers、局部verify或DLL反查；合成Python列才是E+subdivision。二者均不执行慢boundary，不能混作严格内核加速比。归档T1a整装LP/接触组装墙钟是不同工作量，不与这里的块对构造直接相除。单次冷测、未绑核，与其他验证存在并发，不是隔离基准；无性能门。硬件/解释器与并发说明见[测量环境](C1E_evidence/measurement_environment.json)。

交点计数包含闭段共享端点及共线重合端点；整数位长最大值仅指已存储精确坐标的分子/分母，不是所有算术临时峰值。浮点过滤器未启用，过滤/精确回退比为 **N/A**，不能把内部零计数写成0%失败率。

## 7. 验证原始末行与执行完整性

以下从最终完整日志读取，不拼接中断运行：

```text
EAB2_NUMERIC_TESTS checks=558 failed=0
ABI_TESTS: 764 assertions, 0 failures
C_HEADER_PRODUCTION_DLL checks=7 failures=0
C_HEADER_STATIC checks=7 failures=0
EAB2_GEOMETRY2_TESTS checks=700 failed=0
EAB2_LOCAL_TESTS checks=233 failed=0
EAB2_DIFF samples=4483 bits=6003 mismatches=0 status=PASS
C1_DIFF selected=657 completed=657 mismatches=0 layer_queries=100086
EAB2_C1_GENERATED attempts=10079 legal=10000 completed=10000 mismatches=0 status=PASS
EAB2_C1_CONTACT_SOURCES records=114 pairs=605 raw_sources=7197 mismatches=0 status=PASS

# Python 开工快档（不是开工全档）
8690 passed, 5976 deselected in 226.89s (0:03:46)

# Python 收尾快档
8690 passed in 239.80s (0:03:59)

# Python 收尾全档四分片（原样）
3667 passed in 879.39s (0:14:39)
3667 passed in 738.89s (0:12:18)
3666 passed in 1226.93s (0:20:26)
3666 passed in 695.84s (0:11:35)

# 静态构造门
exact construction AST gate: 0 violation(s)

# 定向纯度/大文件门
42 passed in 7.35s

# 实际构建身份/交付审计
EAB2_DELIVERY_AUDIT status=PASS findings=0 vendor_files=71 compiler_commands=13
```

- CTest：`100% tests passed, 0 tests failed out of 6`；见[CTest日志](C1E_evidence/abi/ctest_build06.log)。
- H1收尾快档 8690、全档 14666；每分片收集/分派/调用多重集合相等、0 skipped、0 failed；逐模块实际执行覆盖完整；导出副本及活树字节变化均空。见[快档摘要](C1E_evidence/c1e_fast/summary.json)、[全档摘要](C1E_evidence/c1e_final/summary.json)、[模块覆盖](C1E_evidence/c1e_final/module_coverage.json)。
- pytest均禁cacheprovider并显式basetemp，TEMP/TMP在本单 evidence/tmp；H1 Python3.12实际执行监测。字节副本验证不是新鲜Git树验证。
- 静态构造准入未增减；纯度、大文件门保持绿；最终未提交文件还由[完整性审计](C1E_evidence/integrity.json)逐项核UTF8/BOM/换行/大小与原始哈希边界。

## 8. 订正、设计差异与遗留

1. **harness策略订正**：tight_fit原始长CONTACT段上的Python有限side_probe可落到后续内缝，不能和紧邻开面标签等比。改为先由全部supporting-line事件限制严格邻域，再调用原Python membership；clipped比较相同闭E占据语义。未改Python生产代码，未忽略C++侧状态。首次失败保留，详harness_method。
2. **输入域订正**：3个非binary64原有理小尺度+大平移例RN坍缩，明确域外而非合法skip；非二进有理原输入只声称共同RN后的精确结果。
3. **构建环境修复**：build_05中文MSVC/showIncludes编码使旧local测试对象漏重编；CMake改显式受控头依赖，build_06实际重编全绿；audit逐对象核依赖。失败日志保留，build_05有6个捕获时替换字符且原始native流当时未存，不能伪造无损原始字节；成功build_06无该问题。
4. **C1接口适配**：新增C1工作ABI和独立limits结构，不改变冻结C0结构；局部0查询按需但仍先拥有凸分解/凸胞差，不强制全局T2b。仅测试有理/窗口桥接不进发布DLL。
5. **范围**：C3力学、Shi分类、LP、三维、事件/敏感性均不在本单，不据C1几何差分声称任何姊妹轨迹等价或工程验证。
6. **流程遗留**：开工全档未跑（仅开工快档）；末次全档已跑但不抹去这一偏差。Claude一路独立对抗核查及所有者新鲜工作树复现仍待安排；因此不标C1E_DONE、不宣称里程碑退出。

## 9. 重跑与交付

在当前工作树 PowerShell 中先令 TEMP/TMP 指向 `reports/codex/C1E_evidence/tmp`。下列输出名应换成未使用的新名，避免覆盖已封存运行；不需要Git写或姊妹exe。

```powershell
$env:TEMP = "$PWD/reports/codex/C1E_evidence/tmp"
$env:TMP = $env:TEMP
cmd /c eab2\build_eab2.bat
python -X utf8 tools/eab2_diff_c1.py --dll "$PWD/eab2/build/eab2_test.dll" --output reports/codex/C1E_evidence/diff_replay_NEW.json --metamorphic
python -X utf8 tools/eab2_c1_generate.py --dll "$PWD/eab2/build/eab2_test.dll" --count 10000 --seed 20261022 --output reports/codex/C1E_evidence/generated_replay_NEW.json
python -X utf8 tools/eab2_c1_contact_sources.py --dll "$PWD/eab2/build/eab2_test.dll" --output reports/codex/C1E_evidence/contact_replay_NEW.json
python -X utf8 tools/eab2_c1_measure.py --dll "$PWD/eab2/build/eab2_test.dll" --output reports/codex/C1E_evidence/scale_replay_NEW.json
python -X utf8 tools/h1_run_gates.py --name fast_replay_NEW --evidence-root reports/codex/C1E_evidence
python -X utf8 tools/h1_run_gates.py --name full_replay_NEW --runslow --evidence-root reports/codex/C1E_evidence
```

源码、接口、工具、所有小型证据和忽略的大型原始日志索引见[交付清单](C1E_evidence/deliverables.md)。回滚应由所有者以基线+差异清单审查后安排；本单不自动撤销工作树。

C1E_PARTIAL：待Claude一路非作者对抗核查、所有者新鲜Git工作树复现；开工全档基线未执行（已明确流程偏差）。
