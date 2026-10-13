# WO-M4b 完成报告

日期：2026-10-13。执行范围：只批准 **legacy 默认 + shadow 只读旁路**；没有实现真正 eab 替换。两个工作树均保留未提交改动。

## 1. 结论与验收口径

- 15 例默认全视界共 **1810 步**，未设 / legacy / shadow 三模式的位移、状态、力、几何 CSV 及 stdout/stderr，全部与修改前同提交构建的两次独立基线运行逐字节相同；**零排除列、零排除文件**。
- b-DDA 原 C++ **156** 检查仍全过，新增 **32** 检查全过；全量 pytest 原 **319** 项保持，新增 **17** 项通过，原有 **1 xfail** 不变。Qt 编译及真实进程内开关 smoke 均过。
- 独立 Python 回放覆盖全 **1810 步 × 两时间面**，未分类 **0**、新增类别 **0**。M4a 前三步 **45/45 帧计数一致**，两条逐记录分类交换有输入末位差异与独立 oracle 解释。
- eab 最终无 Git 元数据的新鲜导出，四分片穷尽 **12662** 个 nodeid，全部通过；静态构造门 **0 违例**。原内核 `src/eab` 没有修改。
- 六路 **M4b 范围**交叉独立审查已完成，最终无未关闭 critical/major；不是全仓库里程碑 G6、不是合并批准、不是物理等价或工程标定。

主要证据：[字节矩阵](../../fixtures/m4b_shadow/byte_matrix.json)、[b-DDA 测试摘要](M4b_evidence/bdda_verification_summary.json)、[回放台账](../../docs/m4b_difference_ledger.md)、[全套摘要](M4b_evidence/full_suite_r2/summary.json)。

## 2. 操作边界、基线与回退锚

初始 eab HEAD `0810051ddebe07b39f7313e40517cbaf0988ad25`，b-DDA HEAD `cbf3642e31a3d68790fb62446da185b55ee70e63`，初始状态均干净。没有 commit/push/reset/checkout/stash/worktree/branch 操作，没有动 master 分支。b-DDA 的工作从 `D:/bdda-wt/shadow` 及其 build 内验证副本进行，构建产品均在该工作树 build；短寿命隔离测试另使用用户允许的系统临时目录。

`D:/b-DDA` 没有运行程序、写入或 Git 操作；为恢复已有测试缺少的历史数据，仅只读复制两个明确目录 `runs/golden_execute_all_20260608` 和 `runs/scan_sor_bb06_20260608`，共 705 文件 / 16,989,125 B，逐文件哈希见 [历史资料复制清单](file:///D:/bdda-wt/shadow/bdda2/build/m4b/historical_fixture_copy.json)。未接触两个用户研究笔记目录或其他受保护工作树。

改前二进制 SHA256：`d6593fad2d1ac4fdca8d13e81c48c7faf1a402b5cc8236780ecaea1eb13915c0`；改后：`75c178aed1b0a528e667d6bd0659483aefb405375640620bb96533c066d08650`。
修改前源码/二进制/构建日志保留于 [baseline](file:///D:/bdda-wt/shadow/bdda2/build/m4b/baseline/)；另有 [拟改源文件备份](file:///D:/bdda-wt/shadow/bdda2/build/m4b_source_before/)。回退锚保留，不执行自动回退。

用户禁止创建 worktree；因此采用工作树 build 内的新鲜文件导出补做洁净环境验证，不把它称为已提交后的新克隆。eab 导出每个文件的字节哈希见 [export manifest](M4b_evidence/full_suite_r2/export_manifest.json)。

## 3. b-DDA 逐文件修改

统计包含新增文件，不只看 `git diff --stat` 的已跟踪部分。完整两侧新文件/改动、行数与 SHA256 见 [change_inventory.json](M4b_evidence/change_inventory.json)。

| 文件（相对专用工作树） | 行数增/删 | 内容 |
|---|---:|---|
| `00_START_HERE.md` | +4/−0 | 注明本专用分支的只读 shadow 状态及证据入口，不改主树状态。 |
| `HANDOFF.md` | +5/−0 | 补充检测模式、只读快照、拒绝替换和验收边界。 |
| `bdda2/CMakeLists.txt` | +7/−0 | 新增独立 shadow 单元目标，不改原 core 检查集合。 |
| `bdda2/README.md` | +27/−0 | 说明 legacy 默认、shadow 旁路、eab 拒绝和复核入口。 |
| `bdda2/build.bat` | +2/−0 | 原 core 成功后执行新增单元；保持纯 ASCII。 |
| `bdda2/driver/main.cpp` | +30/−0 | 解析显式模式；shadow 专属 writer/路径保护/审计错误，不改原 CSV 输出。 |
| `bdda2/driver/run.hpp` | +46/−0 | 类型化 Options、拒绝未授权模式、owning const 快照 hook；legacy 计算次序保持。 |
| `bdda2/io/detect_snapshot.hpp` | +111/−0 | 版本化 JSONL、显式参数/原编号几何/双 Tuple7、flush/close 错误与文件别名保护。 |
| `bdda2/studio/engine_bridge.cpp` | +71/−2 | Qt 进程内设置 Options，独立审计结果，清理环境，真实桥 smoke。 |
| `bdda2/studio/engine_bridge.hpp` | +6/−1 | 桥函数显式 detect/shadowPath 参数及独立 shadow 结果。 |
| `bdda2/studio/main.cpp` | +1/−1 | --smoke 纳入检测开关与隔离检查。 |
| `bdda2/test/test_shadow.cpp` | +77/−0 | 默认不调 hook、快照拥有权、异常不影响物理与非法模式门。 |
| `docs/PROJECT_STATUS.md` | +4/−0 | 追加本分支验证事实；原主线研究/工作台定位保留。 |
| `studio/engine2.py` | +32/−3 | Python 桥显式传模式；宿主开关清理；捕获审计红不覆盖物理结果。 |
| `tests/test_m4b_detect_switch.py` | +132/−0 | 17 个新增集成门，覆盖模式、输出/输入别名、硬链接、失败隔离、Python/Qt。 |
| `tools/bdda/verify_cpp.py` | +4/−1 | 验收子进程清理检测开关，保留该门原判据。 |
| `tools/bdda/verify_fast.py` | +2/−0 | 验收子进程清理检测开关，保留该门原判据。 |
| `tools/bdda/verify_force.py` | +4/−1 | 验收子进程清理检测开关，保留该门原判据。 |
| `tools/bdda/verify_m4b_shadow.py` | +237/−0 | 冻结基线重复性、15×3 全产物字节矩阵、顺序轮换计时、新目录安全复算。 |
| `tools/bdda/verify_t0.py` | +2/−0 | 验收子进程清理检测开关，保留该门原判据。 |

eab 新增回放/冻结/字节摘要校验/新鲜导出工具、两份 M4b 测试、差异台账与证据；`fixtures/PROVENANCE.json` 只追加本批溯源。M4a 冻结结果和 eab 几何内核均未改。

## 4. 模式语义与只读设计

| 模式 | 实现 |
|---|---|
| 未设 / legacy | 原 `vertex_angles → detect_candidates → classify_contacts → df06 → ContactStore` 原顺序不变；不启动 eab、不构造/复制影子快照、不读写影子路径、不调用 hook。 |
| shadow | 求解唯一消费原 legacy 表；df06 的 const 输入 `M` 仍是 raw-df05，输出 `rows.t7` 是 post-df06，值拷贝到 owning 快照后同步落盘。 |
| eab | CLI/Python/Qt 显式“未获所有者批准”；库直接传 Eab 也返回拒绝状态，无 fallback。 |
| 其他值 | 显式错误，CLI 在打开原输出前拒绝。 |

库只读 Options，不读宿主环境。Python 桥显式传参；Qt 正演在进程内直接写 Options，**不是只设置 CLI 环境**。没有新增 GUI 下拉框：本单交付桥 API，不宣称每个界面按钮都能选 shadow。

验收入口清理 `BDDA_DETECT/BDDA_DETECT_SHADOW/BDDA_SHADOW_PATH`，固定屏幕 2560×1355。CLI 默认 shadow 路径为 `out.csv.shadow.jsonl`，可用显式路径改写；在截断前保护 bb/db/exe/全部原输出及硬链接别名。失败只产生 `SHADOW_AUDIT_RED` / 独立结果字段，legacy 物理状态、结果与退出码不因影子错误改变。

独立审查将全部 1810 帧的 **188320** 行几何与原 `geom.csv` 步初帧做精确数值核对；**1648** 帧 raw/post 实际不同，排除了“把同一表复制两遍”的假覆盖。详见 [R2](M4b_evidence/review_R2_snapshot_isolation.md)。快照只含检测几何与 Tuple7，不冒充 df22 收敛状态。

## 5. 逐字节矩阵

每格含四 CSV 的完整文件长度与 SHA256（不是抽样、不是浮点容差），另核 stdout/stderr。基线两遍先证明全部可复现，故没有事后豁免。每模式合计 1810 步；45 个修改版运行，30 个基线运行，总 450 个已冻结文件哈希另经独立重算。

| FAMILY | 默认步数 | 基线两遍相同 | 未设 = 基线 | legacy = 基线 | shadow = 基线 |
|---|---:|---|---|---|---|
| 52 | 50 | PASS | PASS | PASS | PASS |
| 12 | 100 | PASS | PASS | PASS | PASS |
| 50 | 50 | PASS | PASS | PASS | PASS |
| 51 | 50 | PASS | PASS | PASS | PASS |
| 03 | 100 | PASS | PASS | PASS | PASS |
| 05 | 100 | PASS | PASS | PASS | PASS |
| 06 | 100 | PASS | PASS | PASS | PASS |
| 09 | 100 | PASS | PASS | PASS | PASS |
| 10 | 100 | PASS | PASS | PASS | PASS |
| v01 | 100 | PASS | PASS | PASS | PASS |
| v01/v01a | 400 | PASS | PASS | PASS | PASS |
| v02 | 100 | PASS | PASS | PASS | PASS |
| v02/v02a | 400 | PASS | PASS | PASS | PASS |
| F038 | 30 | PASS | PASS | PASS | PASS |
| S038 | 30 | PASS | PASS | PASS | PASS |

门：`test_frozen_matrix_proves_all_fifteen_cases_three_modes_match_two_preedit_runs`。少模式/少案例/换输入/缩步/跳步/改 state 哈希均使摘要校验红；此门只证明冻结证据内一致性，不是重新执行 C++。真实文件的独立复核见 [R5](M4b_evidence/review_R5_byte_gate.md)。

## 6. b-DDA 自身测试与环境问题处理

| 门 | 修改前 | 修改后 |
|---|---|---|
| 原 C++ core | 156 检查 / 18 cases，0 失败 | 同 156 / 18，另加 shadow 32 / 3 |
| 全量 pytest | `319 passed, 1 xfailed in 118.68s (0:01:58)` | `336 passed, 1 xfailed in 119.05s (0:01:59)` |
| T0 双位面 | 14/14 | 14/14 |
| T0′ 对插桩内核 | 15/15，默认全视界 | 15/15，结果与基线同 |
| T-force | 6/6 | 6/6 |
| T1 Fast/Faithful | 8/8 | 8/8 |
| 分层 | 0 违例 | 0 违例 |
| 完整 BA / BA-multi / monitor | 6 / 5 / 4 checks 全过 | 6 / 5 / 4 checks 全过，布尔结果和值与基线一致 |
| AD / GN | 全套内 T2a、T2sweep、T2b（1980）、selftest/selftest-force；完整 BA 含 T2-abs | 同门通过 |
| Qt 编译 / --smoke | 成功 / SMOKE_OK | 成功 / SMOKE_SWITCH_OK + SMOKE_OK，原 7 页保留 |

第一次裸 worktree pytest 为 **25 failed, 292 passed, 2 skipped, 1 xfailed**：缺历史 runs、gen1 固定路径布局。不是把红删掉：保留 [原日志](file:///D:/bdda-wt/shadow/bdda2/build/m4b/baseline/pytest.log)，在 build 内导出原 HEAD 完整源码、放入同一冻结 binary、补只读复制的历史数据，然后全量重跑；post 采用同构布局，没有改门、跳门或在 cpp 根放构建产品。日志映射/哈希见 [验证摘要](M4b_evidence/bdda_verification_summary.json)。

Qt 初次增量链接因旧对象仍引用旧桥签名失败，完整 clean-first 重编后通过；未以跳过 Qt 验收规避。原 C++ 数值运算和编译浮点契约未变。

全量 336 passed 的 post-tree 冻结早于验收工具最后增加 `--evidence-dir`/junction 范围保护；此后生产代码、测试及二进制没有改变。最终工具版本另在新目录完成 75 次全视界复算并绑定工具 SHA256，见 [最终工具复算摘要](file:///D:/bdda-wt/shadow/bdda2/build/m4b/rerun_verification_v2_summary.json)，不把较早 post-tree 的工具哈希冒充最终版本。

## 7. 零影子工作与实际耗时

“零开销”严格解释为 **legacy 不执行影子构造、拷贝、回调、文件 I/O 或 eab 计算**。模式检查本身存在，不能声称总 CPU 耗时在数学上严格零差。陷阱 hook 在 legacy 调用数为 0；复制树中把内部 guard 改成允许 legacy 调用，目标 `calls == 0` 和 `shadow_error.empty()` 恰好报红，其余 case 绿，见 [变异证据](file:///D:/bdda-wt/shadow/bdda2/build/m4b/switch_mutation_evidence.json)。

计时在其他本轮计算停止后进行；每例 7 次有效样本，另有预热，baseline/未设/legacy/shadow 顺序轮换，独立进程、固定输入和四 CSV 导出。下表为 wall-clock 中位数，包含启动及原导出，不是纯检测微基准；未把并发验收阶段记录的时间拿来做性能结论。

计时均用默认 Faithful：bb52 运行 50 步；W100 运行 20 步。W100 是额外性能算例，不属于上述 15 例 FAMILY，不与其验收计数混算。

| 算例 | 修改前 ms | 未设 ms | legacy ms | shadow ms | shadow 相对修改前 |
|---|---:|---:|---:|---:|---:|
| 52 | 27.313 | 26.752 | 27.804 | 42.450 | +55.42% |
| W100 | 299.864 | 293.278 | 293.719 | 329.395 | +9.85% |

全样本及各模式相对基线比见 [timing.json](file:///D:/bdda-wt/shadow/bdda2/build/m4b/timing.json)。shadow 额外成本按实测值报告，文件 I/O 同步执行；普通 I/O 异常已隔离，但不承诺磁盘无限挂起时的实时性。

shadow 相对**修改后 legacy** 中位数分别增加 **52.68%（bb52）/ 12.15%（W100）**；未设/legacy 相对修改前中位数在 −2.20% 到 +1.80% 内，不能据此证明严格零秒。计时窗口 11.819 s，本轮编译、pytest、回放全部停止，但正常宿主后台仍累计使用 6.156 CPU-s（多核累计，主要 ASUS、ToDesk、WebView）；未停止用户进程，不称物理绝对空载。完整限制和进程快照见 [计时环境](M4b_evidence/timing_environment.json)。

## 8. eab 全时程回放与 M4a 对照

实际回放不是止于 30 步：15 例完整默认 **1810 步** 均独立进程读取快照、由 L5 检测、两个时间面分别规范化和分类。闭集沿用 M4a，未知 **0**，没有为长时程添加模糊豁免类别。

| 类别 | 完整 raw-df05 | 完整 post-df06 |
|---|---:|---:|
| `ANGULAR_WINDOW_COVER_NOT_SELECTED` | 12793 | 5674 |
| `EXACT_LOCAL_COVER_NOT_SELECTED` | 11983 | 4858 |
| `LEGACY_DUPLICATE_PRIMARY_REFERENCE` | 1502 | 18 |
| `LEGACY_OUTSIDE_FINITE_EDGE_WINDOW` | 55470 | 42710 |
| `LEGACY_VV_DIRECTION_OUTSIDE_OPEN_CONE` | 5193 | 5193 |
| `MATCH` | 76854 | 91098 |
| `VV_IDENTITY_MATCH_TWO_REFERENCE_NORMAL` | 2575 | 2575 |

完整逐条结果和规范化记录见 [full_replay](M4b_evidence/full_replay/)，摘要含每个审计文件和源快照哈希。eab 枚举不使用 legacy 候选作为过滤器；空 legacy 表仍检测。独立反例把实际 production broadphase 置空、gap 加 1、法向反号，分别击中缺有效盖、gap、法向断言；不是追加假接触。

与 M4a：45 帧分类计数全部相同；44 帧逐条分类完全同。bbv01 第 3 步 `VE(21;59,60)` 与 `VE(59;21,22)` 的 EXACT/ANGULAR 互换，参数及有序 legacy Tuple7 没变，相关几何 binary64 末位改变使严格零角窗边界翻转；显式角窗下两侧均有效。每个变化键有相关邻边坐标与独立精确判据，不凭其他无关坐标变化豁免整帧。详见 [差异台账](../../docs/m4b_difference_ledger.md)。

回归入库为各例前 30 步（450 帧），15 个确定性 gzip 共 **578345 B**，仅保留回放所需列；完整原快照 **15093485 B** 留 b-DDA build。前缀重封装显式注明原 header/end/hash，不冒充原 run 只做 30 步。完整回放报告另保留，不把 fixture 体积扩成全部求解输出。

## 9. eab 门、变异与独立审查

格式门覆盖少列、列错位、数据错位、步号跳跃、缺步/截尾、非有限数、参数缺失、重复顶点、生产者失败、未知分类、schema 类型及文件硬链接。真实 L5 内部去掉角窗必须红。回放失败返回非零并审计 RED；若 RED 文件本身与输入硬链接，不能安全落盘时只向 stderr 明确报红，原文件字节保持不变。

最终四分片最后一行原样如下（全 nodeid 清单证明无遗漏、无重复）：

```text
3166 passed in 505.39s (0:08:25)
3166 passed in 654.76s (0:10:54)
3165 passed in 529.74s (0:08:49)
3165 passed in 1202.62s (0:20:02)
```

静态门：`exact construction AST gate: 0 violation(s)`。证据：[节点覆盖](M4b_evidence/full_suite_r2/node_coverage.json)、[四片日志与命令](M4b_evidence/full_suite_r2/)。

第一轮 fresh runner 忘记创建 basetemp 的父 build 目录，造成 fixture setup 错误；单例复现后修 runner，并停止仅属于首轮的进程。首轮不算通过证据；第二轮是新导出全套，见 [环境错误记录](M4b_evidence/full_suite_r1/environment_error.md)。

六路审查：[R1 模式](M4b_evidence/review_R1_modes.md)、[R2 快照隔离](M4b_evidence/review_R2_snapshot_isolation.md)、[R3 回放输入](M4b_evidence/review_R3_replay_input.md)、[R4 几何台账](M4b_evidence/review_R4_geometry_ledger.md)、[R5 字节证据](M4b_evidence/review_R5_byte_gate.md)、[R6 采集协议](M4b_evidence/review_R6_capture_protocol.md)。各路由未实现被审代码的代理交叉审核。

实际发现并关闭：回放输出硬链接可破坏输入（major）、中文台账字面问号损坏（major）、schema bool/整数宽松（minor）。均保留修前证据和独立修后复核。R5 仍记录摘要校验器不认证基线采集独立性的 minor 边界：两次 run 的独立性由真实目录、源归档、450 文件独立重算补证，不把静态 JSON 自证宣传成现场执行证明。

## 10. 遗留与真正替换还缺什么（只列，不做）

当前功能验收无阻断；未提交、未推送、等待 Claude/所有者验收。工具仍是 research/workbench，不是 benchmark/calibration/engineering validation。同步捕获不提供进程恶意改换硬链接的事务保护，也不保证无限 I/O 挂起的实时隔离。

测试沙箱和原始证据全部保留，未自动递归清理；其中 build 内保留一个指向空系统临时目录的 junction 负门布局，见 R6 证据。`PROVENANCE.json` 保持仓库既有显式 CRLF 协议，默认 Git whitespace 检查会把新增行的 CR 报作尾空白；使用单次 `git -c core.whitespace=cr-at-eol diff --check` 为 0，不改 Git 配置或文件换行来制造干净。

如以后批准真正 eab 替换，仍须：
1. 新一轮明确所有者授权；独立定义 eab 模式，不借 shadow 名义启用。
2. EAB ContactRecord → Tuple7/ContactStore 的完整映射、VE/VV 两参考与共边换半选择。
3. df06 顺序与覆盖写历史、锁态继承、滑动符号、切向参考与开闭迭代等价。
4. 通过原 T1 的锁态/拓扑/步长/位移，并扩展装配列、接触力、锚力和参数梯度门；不能用静态局部盖计数代替。
5. 真运动首入与 DDA 仿射运动（平移/转动/应变）的明确定义；全局入口与局部盖边界不能混称。
6. 分界、非对称、实际参考点、旋转/大平移/单位缩放以及长时程触发分支；所有新门需真实内部变异报红。
7. 超时/资源预算、失败策略与回滚开关；独立六路里程碑 G6 及批准后的新鲜提交检验。

## 11. 复核与交付入口

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
# eab 内：不依赖姊妹 exe 的回归与证据摘要
python -X utf8 -m pytest -q -p no:cacheprovider tests/test_m4b_shadow_replay.py tests/test_m4b_byte_evidence.py
python -X utf8 tools/m4b_verify_byte_evidence.py fixtures/m4b_shadow/byte_matrix.json
python -X utf8 tools/m4_shadow_replay.py fixtures/m4b_shadow/bb52.jsonl.gz --out build/replay_check
# 新鲜全套（目录名必须新建，保留旧证据）
python -X utf8 tools/m4b_run_eab_gates.py --out reports/codex/M4b_evidence/rerun_suite --export build/m4b_fresh_rerun
# b-DDA shadow 工作树内；从保留的改前 exe 安全复算到新目录
python -X utf8 tools/bdda/verify_m4b_shadow.py baseline --evidence-dir bdda2/build/m4b_rerun
python -X utf8 tools/bdda/verify_m4b_shadow.py compare --evidence-dir bdda2/build/m4b_rerun
```

[完整交付清单](M4b_evidence/DELIVERY_INDEX.md)；[两侧变更哈希清单](M4b_evidence/change_inventory.json)；[b-DDA 原始构建/运行证据](file:///D:/bdda-wt/shadow/bdda2/build/m4b/)。

下一会话建议：请 Claude 按本报告与交付清单验收两个未提交工作树，再决定提交；真正 eab 替换仍未授权。

M4b_DONE
