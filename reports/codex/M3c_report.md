# WO-M3c：M3b 验收遗留补门

执行目录：`D:/eab-wt/cx-m4`。只读核验起点：`m4-seam @ 5f87ebd14ca5fa780350f4e07b3ebb5ea516ad9c`，初始工作树干净。

> **M3c 必做项 1–8 已完成。** 最终新鲜字节副本 13221 节点四片全绿、收集=执行、0 skip；静态 0 违例；19 组真实内部变异红在指定语义断言，恢复后绿；M4c 450 帧已真实重算。机器收口审计 GREEN。本单不合并 M5a，不替代 Claude 的独立验收或六路 G6；可选 9/10 未实施。

## 1. 逐条处置

| 工单 | 实施与语义门 | 结果/边界 |
|---|---|---|
| 1 三维侧点、暴露、覆盖、最短出口 | `test_independent_3d_all_support_adjacency_ray_boundary_and_shortest_exit`；测试自有笛卡尔凸盒并，精确反变换后检查全部支撑事件；独立网格矩形边界求最短出口及全部并列点 | L、窄 U 槽、紧配、空腔、旋转/大平移 5 格；3006 侧点、132 seeded 随机方向线、336 独立 ∂E 端点零失配；5 个实际边界产物互异 |
| 2 闭区间合并、紧配缝 | `test_closed_E_merges_internal_contact_seams_in_line_sections`、`test_g03_closed_E_exit_crosses_internal_contact_seams` | 紧配 pin/U、恰填空腔、分离双 slab 三族；接触起点和严格相交起点都穿过内缝；闭 E 合并而开 O 保留缝，不把非贯入时刻误称出口 |
| 3 非轴向等号切触 | `test_nonaxial_singleton_tangency_is_closed_at_three_scales_and_translations` | 三个尺度/平移格，一般方向 `(1,1,1)` 及缩放方向；闭截面恰为单点，O 为空；实际参数产物互异 |
| 4 g03 接触起点 | `test_g03_boundary_face_edge_vertex_start_uses_closed_zero_membership` | 正侧面/棱/顶点沿向外方向出口为 0；另测负侧面沿向内方向的非零出口，以同时守住闭区间左端点 |
| 5 EE 闭有效 | `test_t3l_coverage_requires_closed_but_not_strict_ee_family` | 交叉细长条的暴露面内部不能由 VF/FV 覆盖，必须保留 EE；独立源面叉积证明法向在闭锥边缘；三组旋转/尺度/平移裁剪产物互异；每个暴露片另作完整原子覆盖 |
| 6 公开输出确定性 | `test_compact_public_output_fields_are_independent_of_call_order`、`test_determinism_scale_parameters_have_distinct_public_probe_products` | compact 的 `side_probes()` 首次调用先构造最终 subdivision；cold/warm 两种顺序逐字段核 `side_probes` 与全部 `clipped_covers`；默认非 compact 路径不变 |
| 7 退化裁剪审计 | `assert_clipped_polygons_nondegenerate`，`test_noncoplanar_clip_mutant_dies_at_explicit_degenerate_polygon_assertion` | 在求重心之前检查至少 3 点、非零面积及共面；移除真实共面过滤后红在明确几何契约，不再以空片除零冒充语义门 |
| 8 文档订正 | T3L 共面覆盖引理、VF 必要条件/候选超集；T2/T2b；r3 作废；23 条旧审查溯源 | 全部完成，详见第 5 节 |
| 9 可选局部化 | **未实施** | 未在本单证明“仅选相交凸胞平面”后包括安排片、侧点等公开构造量逐值不变；不作未经证明的裁剪/性能优化，保留全部平面路径 |
| 10 可选理想化几何 | **未实施** | 未增加任何 Xbloc 风格模型或厂商几何声称；维持厂商实体不可认证的既有边界 |

新语义门位于 [三维门](file:///D:/eab-wt/cx-m4/tests/test_m3c_boundary3d.py)、[区间与 g03 门](file:///D:/eab-wt/cx-m4/tests/test_m3c_sections.py)、[确定性门](file:///D:/eab-wt/cx-m4/tests/test_m3c_determinism.py)。34 个新增 pytest 节点，严格核验无原节点删除，见 [最终机器审计](file:///D:/eab-wt/cx-m4/reports/codex/M3c_evidence/final_audit.json)。

**本单实际生产行为改动只有 compact 侧点求值顺序的 4 行**；`boundary.py` 另仅订正 docstring。未因补门改变当前正确的三维几何算法。

## 2. 独立 oracle 与覆盖口径

| 检查 | 独立原语/输入 | 与被测实现的隔离 |
|---|---|---|
| 三维邻胞、闭占据、随机射线端点 | `tests/m3c_oracle3d.py`，仅 `fractions.Fraction`、`itertools.product`；手工给定笛卡尔凸盒并；自持点积、闭盒成员与精确参数交 | 不读取 `B.planes`、生产凸分解、SAT、BSP、hull、clip 或生产距离来生成期望 |
| 最短闭集出口及全并列点 | 独立全部坐标事件网格；两侧占据 XOR 得完整暴露矩形；各轴钳位得到精确距离与见证 | 不调用生产 `shortest_exit`、`_in_polygon` 或投影公式产生期望 |
| EE 必需且闭有效 | 原始独立长条输入、源面叉积和共线判断；原子覆盖用既有测试自持二维行列式/线性插值 | 生产 `Polyhedron` 仅作输入容器，生产候选/裁剪仅为被测输出 |
| 紧配区间、切触、接触起点 | 手算盒差、闭并与参数端点；g03 另有原表面绕数/射线 oracle | 不共用被测区间合并、包围盒剪枝、凸分解或 SAT |
| 调用顺序 | 两个相同输入的新对象采用不同公开访问顺序，直接比较 dataclass 全字段 | 这是公开 API 确定性合同，不冒称几何真值 oracle |

[逐文件 import、行号和 SHA256 清单](file:///D:/eab-wt/cx-m4/reports/codex/M3c_evidence/oracle_import_inventory.json)。mutation helper 位于 `tools/m3c_mutation_support.py`，只做测试反射/编译，不计算几何；独立数值 oracle 仍在静态扫描域。未将几何 oracle 改名成测试驱动规避扫描。

三维邻胞声明针对**独立笛卡尔凸分解的全部支撑平面**，不是穷尽生产冗余 SAT 人工平面的声称。旋转格使用精确 SO(3)、尺度 2、平移 `(10^6,-3,7)`；射线 seed=3103，每个查询点取 12 个全非零分量方向。5 格共 1503 个安排片、1036 个暴露片；11 个内点/接触内缝查询逐值核最短出口及全并列点。它们是结构化有限回归样本，不是任意凹实体或任意退化族的普遍证明。[逐格计数](file:///D:/eab-wt/cx-m4/reports/codex/M3c_evidence/geometry_agent.json)

## 3. 真实内部变异：先绿、语义红、恢复绿

[完整 19 组子进程记录及逐条最后异常](file:///D:/eab-wt/cx-m4/reports/codex/M3c_evidence/mutations/summary.json)。每组运行三个独立子进程，原版和恢复版正常退出；变异版非零退出且**最后一行必须是指定 `AssertionError`**。只直接执行新语义门，源码哈希、静态审查和冻结摘要绊线明确不执行。生产磁盘文件未改；变异编译/替换真正的被测函数内部，不在结果之后追加假数据。

| 内部变异 | 独立语义红断言 | 组数 |
|---|---|---:|
| `explicit_boundary` 的 `_sides` 只用来源凸片对支撑平面 | `independent adjacent-open-cell side probe crossed a support event` | 1 |
| 同一来源平面变异，单独执行覆盖门 | `independent ray boundary point has an exposed polygon` | 1 |
| 同一来源平面变异，单独执行最短出口门 | `independent Cartesian-union shortest closed exit` | 1 |
| `_merge` 闭分支 `<=` 改 `<`，三族 `line_sections` | `closed-E contact seam is not an interval endpoint` | 3 |
| 同一合并变异，三族 × 接触/严格相交起点的 g03 | `g03 closed-E exit must cross the internal contact seam` | 6 |
| `_line_candidate` 将 `lower > upper` 改 `>=` | `nonaxial singleton tangency survives closed AABB pruning` | 1 |
| g03 的 `lo <= 0 <= hi` 分别改开左/开右 | `g03 boundary-start zero belongs to the closed interval` | 2 |
| `_edge_closed` 两个 `>= 0` 改 `> 0` | `T3L closed-only EE covers the independent exposed-face interior` | 1 |
| `side_probes` 去掉 compact 首次构造分支，分别检查两个公开输出 | `compact side_probes fields depend on public call order` / `compact clipped_covers fields depend on public call order` | 2 |
| `clip_local_covers` 去掉真实共面过滤 | `clipped local cover must be a nondegenerate planar polygon` | 1 |

来源平面变异使窄 U 槽暴露片从 220 片降为 205 片，确实漏掉真实边界；不是仅改变坐标约定。三条独立门分别报红，未靠单对盒坐标偶然阻拦。确定性修复前另执行原源码得到 6 条字段语义失败，见 [原版真实红日志](file:///D:/eab-wt/cx-m4/reports/codex/M3c_evidence/determinism_baseline_red.txt)。

## 4. 静态构造、450 帧与运行成本

- 全仓静态预检和最终副本均为：`exact construction AST gate: 0 violation(s)`，见 [最终静态输出](file:///D:/eab-wt/cx-m4/reports/codex/M3c_evidence/final_suite/exact_construction.txt)。
- **0 新豁免、0 新 import/member 准入**。仅 `M3b-L0004..0007` 四条因 `local_cover_candidates` docstring 订正续签；去掉该 docstring 后完整模块可执行 AST 与 HEAD 相等。保留旧 context、旧 review 路径与逐条理由：[本单静态续签](file:///D:/eab-wt/cx-m4/reports/codex/M3c_evidence/static_review.json)。辅助静态门不是任意 Python 数值正确性的证明。
- 定向 M3 新旧门合并：`86 passed in 15.82s`，[命令与末行](file:///D:/eab-wt/cx-m4/reports/codex/M3c_evidence/targeted_final.txt)。
- compact 修正命中 M4c import 闭包，已真实重算 15 案例 × 30 帧，`pd-edge-limit=0`。最终 r2 全部 450 帧完整 JSON 值与既有归档一致，同时复核每帧散列、输入、分类聚合和代码前后不变；expected.json 与全部 15 个原 normalized 夹具的前后哈希也一致。实际外层耗时 **171.7959 s**。未修改既有 expected/normalized 夹具，仅由新重算结果刷新 [冻结摘要](file:///D:/eab-wt/cx-m4/reports/codex/M4c_evidence/frozen_summary.json)。
- [450 帧实际重算认证](file:///D:/eab-wt/cx-m4/reports/codex/M3c_evidence/motion_refresh_r2_attestation.json)；[改前回滚摘要](file:///D:/eab-wt/cx-m4/reports/codex/M3c_evidence/motion_refresh_before.json)。第一轮也完成 450 帧，但同伴指出 `expected_fixture_unchanged` 缺少显式前后散列守卫；加入该守卫后**整批重算 r2**，最终只使用 r2，不拼接帧、不只刷新哈希。
- 新增 34 节点的 setup/call/teardown 总时长 **8.9592 s**；同轮旧节点累计 **3711.1922 s**，新增门直接占 **0.2414%**。整轮墙钟（含收集、四片及静态门）基线 **1545.4520 s** → 最终 **1600.5283 s**，观测增量 **3.5638%**，低于约 5% 目标。基线旧节点累计 **3506.2568 s**，与同轮旧节点也有波动；两套部分重叠运行、机器另有并发任务，因此墙钟和累计阶段时间都只是本次观测，不作稳定性能基准或精确因果归因。

## 5. 文档与历史证据订正

1. [T3L](file:///D:/eab-wt/cx-m4/docs/m3b_boundary3d_design.md)：补共面覆盖引理——有限非共面交线和共面零面积交集不能覆盖二维片的相对开层；共面正面积闭交集有限并包含稠密子集的闭包。VF 候选判据如实改为必要条件，候选为闭有效集超集；超集不漏正确盖，裁剪后不会加入 ∂E 外点，但不证明所有冗余标签的局部支撑充分性。
2. [T2/T2b](file:///D:/eab-wt/cx-m4/docs/m3_global_entrance_design.md)：T2 明写按全局凸胞边切分即可；T2b 改为每条相对开原子边标签恒定、各顶点各自取标签，不把端点与开边混为同一标签。
3. [作废 r3 标记](file:///D:/eab-wt/cx-m4/reports/codex/M3b_evidence/final_suite_r3/VOID.md)：旧目录保留，禁止用其残片拼接有效全套。
4. [M3b static_review.json](file:///D:/eab-wt/cx-m4/reports/codex/M3b_evidence/static_review.json)：23 条续签逐条补 `old_review_evidence`，与旧 context/旧审查记录对账。
5. 明确记录：**`src/eab/kernel3d/g03_surface_oracle.py` 原有 UTF-8 BOM 已在 M3b 去掉**；M3c 当前文件无 BOM，本单未再次改动该 oracle。不能将这项历史字节变化藏在“仅几何逻辑变更”里。[字节核验记录](file:///D:/eab-wt/cx-m4/reports/codex/M3c_evidence/determinism_agent.md)

## 6. 全套四片与边界

最终运行收集 **13221** 节点；基线 **13187**，新增 **34**、删除 **0**。独立重读原始执行记录确认 dispatch=collection=setup=call=teardown，每个节点每个阶段恰一次，所有阶段 passed，**0 skip**。

**最终四片最后一行原样：**

```text
3306 passed in 958.34s (0:15:58)
3305 passed in 585.68s (0:09:45)
3305 passed in 1442.05s (0:24:02)
3305 passed in 837.81s (0:13:57)
```

**基线四片最后一行原样：**

```text
3297 passed in 1363.54s (0:22:43)
3297 passed in 549.56s (0:09:09)
3297 passed in 909.70s (0:15:09)
3296 passed in 787.73s (0:13:07)
```

两轮末尾静态门均为 `exact construction AST gate: 0 violation(s)`。[最终四片摘要](file:///D:/eab-wt/cx-m4/reports/codex/M3c_evidence/final_suite/summary.json) · [基线摘要](file:///D:/eab-wt/cx-m4/reports/codex/M3c_evidence/baseline_suite/summary.json)

`tools/m3c_finalize_evidence.py` 不信任摘要布尔值而重读实际节点/阶段、变异日志和 450 帧；确认最终副本登记的 **308 个源码/测试/工具/配置/冻结摘要文件**与当前工作副本字节一致，输出：

```text
M3C_FINAL_AUDIT_GREEN 13221 nodes; 450 frames; 19 semantic reds; static 0
```

新增/改动交付文本均核 UTF-8 无 BOM，无 >1 MB 新交付文件；CRLF 保留场景以 `git -c core.whitespace=cr-at-eol diff --check` 检查通过，不为静音空白提示批量改行尾。[完整交付链接清单](file:///D:/eab-wt/cx-m4/reports/codex/M3c_evidence/delivery_index.md)

用户禁止 worktree/branch/checkout 等 Git 写操作，因此采用新建逐字节源副本，**不是新 Git checkout**。全部 pytest 均带 `-p no:cacheprovider` 与显式 `--basetemp`，TEMP/TMP 指向本单 ignored tmp 内；大日志、节点清单和完整执行记录留在 ignored tmp。长跑进度落盘，每轮使用新目录，不恢复/拼接中断运行。

只修改 cx-m4，未操作 cx-e2、其他工作树、b-DDA、bdda-wt 或 `D:/E(A, B)`；无 commit/push/reset/checkout/stash/worktree/branch，无安装第三方依赖。[同伴只读复核](file:///D:/eab-wt/cx-m4/reports/codex/M3c_evidence/peer_review.md) 范围内未发现 critical/major，但不是六路 G6，也不把本单有限回归扩称厂商几何认证或工程验证。

M3c_DONE
