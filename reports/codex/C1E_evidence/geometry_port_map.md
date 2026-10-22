# WO-C1E 几何函数移植对照与作者自查

本文件是实现作者的只读复核与补充测试记录，**不是 Claude 安排的独立对抗核查**，也不替代所有者安排的新鲜树复现。有限测试不构成全输入域证明。除本文件、同目录补充探针脚本及 `tmp/` 探针产物外，本轮复核未修改源码、最终 DLL 或构建产物。

设计正本 SHA-256 已实读核对：`6d174ecc4f1326d5bac21c56c8d333485fb50bbaef3a12150e94eaff14cb4dac`。本对照使用 build_06 的测试 DLL，SHA-256 为 `dd64762305f62b56b3aa985f1988b36bc619d1dbc367942ae6a9c40fca66dbf8`；不引用较早 `abi/verification.json` 对应的旧 DLL 当作最终证据。

## 1. 文件索引

- [几何接口](file:///D:/eab-wt/cx-c0/eab2/src/geometry2.hpp)、[几何实现](file:///D:/eab-wt/cx-c0/eab2/src/geometry2.cpp)、[局部查询实现](file:///D:/eab-wt/cx-c0/eab2/src/geometry2_local.cpp)。
- [几何单测](file:///D:/eab-wt/cx-c0/eab2/tests/test_geometry2.cpp)、[局部单测](file:///D:/eab-wt/cx-c0/eab2/tests/test_geometry2_local.cpp)、[ABI 单测](file:///D:/eab-wt/cx-c0/eab2/tests/test_abi.cpp)。
- [差分入口](file:///D:/eab-wt/cx-c0/tools/eab2_diff_c1.py)、[Python 规范集合计算](file:///D:/eab-wt/cx-c0/tools/eab2_c1_exact.py)、[局部证据复核](file:///D:/eab-wt/cx-c0/tools/eab2_c1_local.py)。
- [最终全语料差分](file:///D:/eab-wt/cx-c0/reports/codex/C1E_evidence/diff_final.json)、[接触来源逐项复核](file:///D:/eab-wt/cx-c0/reports/codex/C1E_evidence/contact_sources_final.json)、[build_06 日志](file:///D:/eab-wt/cx-c0/reports/codex/C1E_evidence/abi/build_06.log)。

下表的 C++ 门名均是具名测试函数，不是独立 CTest 条目：几何函数统一由 `geometry2_static` 的 `main()` 执行，局部函数由 `geometry2_local_static` 执行。

## 2. Python 函数 → C++ 实现 → 实际守护

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

## 3. C1 规范骨架与直接快路补验

### 3.1 规范计算确实位于 Python harness

`python_export` 读取 Python 裁判，C++ 仅导出原始精确数据。`canonical` 对**双方**输出进行相同规范化：合并最大共线 CONTACT 开段、按完整来源标签再分层、保留来源转变/分支端点和孤立点；逐点验证标签来自哪些原始 VE/EV 段。`face_regions` 对逐面有向边切分并抵消内部竖直缝，同时保留非零重数，防止把重复整面吞掉。没有把 C++ 的内部 subdivision 字节或序号当作规范真值。

还逐一用 Python `membership/topology` 复查 C++ 的全部 0/1/2 维层样本，反向将 Python 层样本送入测试专用有理批查询。C++ 没有参与 Python 分数运算、谓词或舍入。小例使用原 Python `boundary` 慢路线交叉核验；正式 assembly 大语料避免重复慢边界计算，使用 Python CONTACT 段的 topology 判定。

已完成证据末行：

```text
C1_DIFF selected=657 completed=657 mismatches=0 layer_queries=100086
```

657 是 1763 个命名/正式块对出现记录按有序 binary64 输入去重后的数量，不是 1763 个不同几何。3 个历史纯有理极小尺度加大平移例在 RN 为 binary64 后出现零边，明确登记 Python-only，不伪装为合法 C++ 输入或 0 skip 的成功算例。非二进有理数据经过 RN 后只比较给定 binary64 数学问题，不声称旧精确接触关系仍保留。

### 3.2 凸快路的单独直接差分补齐

复核发现：一般凹 `Entrance` 构造使用凸片两两差点的 hull，不执行 `entrance_block_exact` 的双边序归并。因此不能把上述 657 对全局差分写成 `ExactFacet.label/pairs` 的直接逐项覆盖。

为补这个验证缺口，本轮新增了[可重跑探针](file:///D:/eab-wt/cx-c0/reports/codex/C1E_evidence/geometry_fastpath_probe.py)，仅在 evidence/tmp 编译调用既有 `eab2_core.lib` 的临时程序，不改发布 ABI、最终 DLL 或源文件。5 个基形覆盖非对称一般位置、平直顶点、平行不等长边、1 ULP 斜率；分别改变循环起点，取二进缩放指数 -400/0/400、0°/90° 旋转及可精确表示的不同体平移，共 90 对。所有坐标先确认 binary64 能精确表示。

直接对比 Python `kernel2d.exact` 的 ordered vertices、每条 facet 的 label/start/direction、顶点源 pairs、面积、VE/EV 侧判及成员查询。结果见[快路差分汇总](file:///D:/eab-wt/cx-c0/reports/codex/C1E_evidence/convex_fastpath_final_r1.json)：

```text
C1_CONVEX_FASTPATH cases=90 facets=540 membership=1260 side_predicates=2772 mismatches=0 original_unchanged=1
```

运行命令：`python reports/codex/C1E_evidence/geometry_fastpath_probe.py --name <新的名字>`。本证据仍是作者差分，不是独立核查。

## 4. 刻意不同的表示、局限与未声称事项

1. **盖的显示层**：C++ 导出未归一化法向、gap²/sign、精确投影参数与两见证点，而不是复刻 Python `Cover.normal/gap/point` 的浮点显示对象。它们定义同一精确 recipe；C0 显示合同独立守护。本单未新增浮点几何裁决。
2. **显式窗口**：零窗及有限 `tol/cone_tol/seg_tol` 已移植精确平方比较；`window=null` 在测试桥表示正无穷窗口。无限端点窗口的同集合操作由 `require_in_segment=false` 表达；没有另造 `seg_tol="inf"` 文本。非法/非有限参数不是合法 binary64 几何结论。
3. **邻侧点不逐坐标复制**：Python finite side probe 可能落到远处内缝/端点；C++ `directional_state` 报接触段中点处的无穷小两侧三态。harness 用精确最近 supporting-line 事件界限取样并复核；对 Python 原 clipped_cover 对比的是两侧闭 E 占据和 exposed，并另外核 C++ 无穷小 body 三态。此差异有方法说明，不是放松 E/O 判定。
4. **细分语义而非枚举协议**：compact 开/关均为完整分层表示，允许竖直辅助切分不同；没有保留 Python 全局 `lru_cache` 的容量/逐对象复用行为。C ABI `NO_CACHE` 用临时 E 重建；缓存门只证明观察集合/状态一致，不承诺运行时间一致。
5. **局部只是不建全局骨架**：E 创建时仍构造全体凸胞；局部查询不会强制物化 raw arrangement/subdivision，但不是完全不建 E 凸胞的惰性分解算法。返回全部未含零胞的精确 AABB/严格分离边、全部非 incident 胞边距离及正有理 r。它不签发 LockCertificate、不判组装一阶可动性、不装配机械法向约束。
6. **资源限制不是数学否定**：配置 work/elements/integer_bits，C++ 几何入口/ABI 整批嵌套共享计数，整数算术有保守前置位长预算和 owning 结果核验；超限 RESOURCE_LIMIT。固定 4096 顶点保护仍存在。`configurable_limits_and_transactions` 核失败后的预算恢复及无半缓存/渐进缓存绕过。这里不承诺精确 RAM 峰值或 Boost 私有临时 limb 的逐对象统计。
7. **统计定义**：`max_integer_bits` 只观测已存储几何坐标分子/分母（导出已附 scope），不是所有整数临时峰值；`intersection_points` 包含共享端点与共线重叠端点；`exact_work_units` 是计费循环单位，不是完整算术指令数/bit complexity；`exact_fallbacks=0` 因纯精确且没有浮点过滤器，不可解释为“几何无需精确运算”。性能不设通过阈值。
8. **工单完成度边界**：本作者复核不认证 10000 生成器最终完成、P2 全规模测量、Python 最终快/全档四分片、独立核查或新鲜树复现；这些应由主报告引用各自最终证据。不能从此处 700 个几何断言推出其余交付已完成。

## 5. §5.4 ABI 与 §1.5 局部事项核对

body/E 创建销毁、双三态批查询、全局/局部 exact JSON 与库侧释放均已落到 C ABI；有理查询和非零窗盖仅测试 DLL 提供。`get_abi_info/get_c1_abi_info` 如实公布能力/尺寸。句柄 context/type/generation 校验与槽位复用拒旧 token、尺寸/步长/容量/溢出拒收、call_status 与 mathematical_status 分离由 `geometry2_matrix/child_context_reuse/limits2_matrix` 守护。详细协议以[ABI 分报告](file:///D:/eab-wt/cx-c0/reports/codex/C1E_evidence/abi/C1E_ABI.md)和[ABI_CONTRACT](file:///D:/eab-wt/cx-c0/eab2/ABI_CONTRACT.md)为准，不从几何函数自行推断 ABI 安全。

正式 contact_set 原始来源复核记录：605 个不同有序块对、1201 个状态记录（OUTSIDE 749 / CONTACT 451 / OVERLAP 1）、7197 项来源，165 个冻结 fixture 片段已核验；`contact_sources_final.json` 为 PASS。只核原始关联/端点/物理点/原 ID，不将此计数宣传为 C3 约束/LP 对账。

## 6. 已观察的定向门末行

```text
EAB2_GEOMETRY2_TESTS checks=700 failed=0
EAB2_LOCAL_TESTS checks=233 failed=0
ABI_TESTS: 764 assertions, 0 failures
C1_GEOMETRY_MUTATIONS mutants=3 semantic_kills=3 original_unchanged=1
```

3 个内部缺陷是把 closed E 当 O、移除孤立接触、把显式 cone 扩窗误提升 strict。均由目标语义断言报红，不是源码哈希/编译失败杀死；见[注入证据](file:///D:/eab-wt/cx-c0/reports/codex/C1E_evidence/mutations_final_r1.json)。

结论：本次作者复核未发现仍开放的 C1 几何数学缺陷；发现的凸快路直接验证覆盖缺口已用独立调用探针补充。以上结论仅针对所列实现和有限证据，不自行宣布 WO-C1E 验收退出。
