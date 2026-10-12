# M4a · b-DDA 接缝地图（只读调查）

## 0. 口径与边界

本文件对应 WO-M4a 的第 1、7 项；依据当前可读源文件逐行核对，**没有在 `D:/b-DDA` 运行程序、导入模块、修改文件或执行 git**。外部路径下文均以 `D:/b-DDA/` 为前缀；行号对应本次读取的工作副本，不是假定某个提交的永久行号。命令入口只登记，不表示本次运行过姊妹工具。M4a 本轮运行与计数以 [报告](../reports/codex/M4a_report.md)、[差异台账](m4_difference_ledger.md) 为准。

重要订正：`bdda2/` 本身是 **C++20 二代引擎**；Python 参考内核是 `src/bdda/`，Python 工作台启动桥是 `studio/engine2.py`，原生 Qt 工作台是 `bdda2/studio/`。不可把“Python 工作台使用 bdda2”写成“Python 版 bdda2 检测内核”。依据：`bdda2/driver/main.cpp:1-10`、`studio/engine2.py:29-33,172-195`、`src/bdda/detect.py:1-6`。

设计背景已经对照：本树 `docs/plan_20260921.md` M4 节；`docs/canon_map.md` 的“八、设计正本 07 对代码”节；`docs/sibling_observations.md` 的 b-DDA / DDA4.x 项；现有 G1、二维首入与 G4 工具。M4a 是**离线检测影子对账**，不等于原生检测切换、开闭迭代同构或位移级 T1 全覆盖。

## 1. `BDDA_SOLVER` 先例：在哪里读、在哪里分派

| 线 / 接缝 | 已核实位置（`路径:行号`） | 实际语义 |
|---|---|---|
| C++20 CLI 读环境 | `bdda2/driver/main.cpp:21-30` | `BDDA_SOLVER=fast` / `auto` 改写 `driver::Options::solver`；其他字符串和未设值均保留默认 Faithful。只在薄 CLI 读进程环境，不在库内探测。 |
| 类型化配置默认值 | `bdda2/driver/run.hpp:55-69` | `SolverMode {Faithful, Fast, Auto}`；默认 Faithful，Auto 阈值 `fast_threshold_blocks=32`。 |
| 求解器分派 | `bdda2/driver/run.hpp:355-356,503-528` | `Fast` 或 `Auto && n>32` 走 Skyline；遇 `SingularSystem` 计回退次数后用 Faithful 稠密系统。两路调用同一个 `open_close_iterate`，不是两套检测器。 |
| Python 工作台桥 | `studio/engine2.py:172-195` | `run_forward(..., solver='faithful')` 启动 `bdda2_solver.exe`，通过 `_env({'BDDA_SOLVER': solver})` 传参；不是 Python 读取环境后自行求解。 |
| Python 验收隔离 | `studio/engine2.py:338-343` | T0 调用主动移除 `BDDA_SOLVER`，防止外部环境把逐字节 Faithful 门偷偷切到 Fast。 |
| 原生 Qt 正演桥 | `bdda2/studio/engine_bridge.cpp:190-208,214-218` | `runForward` 根据传入的 `QString solver` 直接设置 `Options` 并在进程内调用 `driver::run<double>`，**不经 CLI 环境变量**。 |
| 原生 Qt 子进程验收桥 | `bdda2/studio/engine_bridge.cpp:38-45,486-498` | `pinnedEnv()` 固定屏幕参数，并移除 `BDDA_SOLVER` / `BDDA_STATE_DUMP`；T0 子进程从默认 Faithful 起跑。 |
| Python 参考内核 | `src/bdda/detect.py:23-117`；`src/bdda/multistep.py:464`；`tools/bdda/audit_refkernel_nstep.py:335-339,387` | 直接函数调用检测 / 开闭迭代；**未找到 Python 参考内核自己的 `BDDA_SOLVER` 分派**。搜索过 `src/bdda/**/*.py`、`tools/**/*.py`、`studio/**/*.py`，命中仅启动桥及验收/打包脚本。 |

## 2. 每一步的检测与消费链

### 2.1 legacy `df.c` 原链

| 阶段 | 已核实位置 | 输入 → 输出 / 下游 |
|---|---|---|
| 步循环 | `df/df.c:6003-6039` | `df03 → df04 → df05 → df06 → df07 → df08/di08 → df09…df17 → (df18 → solve → df22)`。检测在本步位移求解之前；本步求解并不作为 `df04/05` 输入。 |
| 候选枚举 `df04` | `df/df.c:1346-1377,1380-1510` | `d[][]` 块顶点、`k0` 顶点范围、`u[][2]` 顶点内角、`d0/h5` → `k/k1` 候选；先保存/修正上一步接触状态，再用包围盒、顶点距离和有限边投影筛选。`k<0` 是 v-e，`k>0` 是 v-v。 |
| 距离窗口 | `df/df.c:1430-1460,1484-1504` | 顶点对距离平方 `≤d0²`；否则 v-e 要求投影在线段内，并且内法向距离在 `[-d0,h5*d0]`。这是**不对称域窗口**，不能等同 `abs(gap)≤d0` 的完整 legacy 定义。 |
| 静态角度分类 `df05` | `df/df.c:1527-1617` | 候选、相邻边方向角 `u[][1]`、`h1` → `m[][0..6]`；角度覆盖剔除，v-e 共边标志写入 `m4/m5`。 |
| v-v / 共边参考边选择 | `df/df.c:1619-1694` | 近似平行相邻边降为一条或两条 v-e；一般 v-v 保存两组三点参考，使用静态角度及 `abs(sin(angle))` 比较决定先后次序。 |
| 状态转移与拓扑改写 `df06` | `df/df.c:1705-1877`；对应 Python 逐条解释 `src/bdda/multistep.py:668-701` | 上一步有序末表 + 新检测表 → 转移 `o* / m0*`；共边记录可能**两半互换**。因而 post-df07 CSV 不等于 raw-df05 表；集合差异必须区分检测与转移重写。 |
| 步初锁态 / dump `df07` | `df/df.c:1960-1996` | 首步几何间隙与 `f1*d0` 决定近贴合开闭；v-v 闭合时选两参考中较短间隙，`m0_2` 为 1 或 3。在末尾写 contacts CSV。 |
| 弹簧装配 `df18` | `df/df.c:3155-3210,3312-3323` | 消费 `m[][] / m0[][] / o[][]`；由锁态选择主参考法/切向弹簧或第二参考法向弹簧，向系统装配。`df18` CSV 是装配侧诊断，不能与检测步初状态混成一个时间面。 |
| 开闭迭代 | `df/df.c:6028-6055`；`df/df.c:4090-4109` | 求解后 `df22` 判开闭，必要时迭代、削步或重启；`df24` 算位移，`df25` 最后推进顶点。检测并不在每次开闭迭代重新枚举。 |

### 2.2 Python 与 C++20 对应位置

| 功能 | Python 参考线 | C++20 二代线 |
|---|---|---|
| 顶点角 | `src/bdda/detect.py:23-53` | `bdda2/detect/angles.hpp`，调用 `bdda2/driver/run.hpp:386` |
| 候选枚举 | `src/bdda/detect.py:55-107` | `bdda2/detect/candidates.hpp:27-85`；调用 `bdda2/driver/run.hpp:387` |
| 角度分类 | `src/bdda/detect.py:110-195` | `bdda2/detect/classify.hpp:24-109`；调用 `bdda2/driver/run.hpp:388` |
| 步驱动 | `tools/bdda/audit_refkernel_nstep.py:325-339,387` | `bdda2/driver/run.hpp:366-391`；先用上一拍六分量位移更新几何，再检测 |
| 转移 / 接触建表 | `src/bdda/multistep.py:668-701` | `bdda2/driver/run.hpp:390-412`；`df06_rewire_and_transfer → ContactStore` |
| 接触存储 | `src/bdda/multistep.py:18-24` 的字典结构 | `bdda2/core/contacts.hpp:17-18,49-64,68-115` 的 SoA：顶点号、两套坐标/块号、转移态、当前态分列 |
| 开闭与装配 | `src/bdda/multistep.py:464` | `bdda2/stepper/open_close.hpp:148-195`：`assemble_static → add_contact_terms → solve → judge_step → judged_locks`；弹簧装配 `bdda2/stepper/step_system.hpp:162-205` |

### 2.3 参数与数据时间面

| 数据 | 源码位置 | 对适配器的要求 |
|---|---|---|
| 参数初始化 | `df/df.c:4903-4930`；`src/bdda/caseio.py:97-134`；`bdda2/io/det_params.hpp:20-26,40-60` | `h1=3°`，`f0=1e-7`，`f1=1e-4`；`d0=2.5*w0*g2` 后受 `f2=4e-4` 下限调整，`h5` 从 0.3 调整。应优先读取实际逐步 dump，不把这些量放进 eab 精确谓词。 |
| 屏幕依赖 | `df/df.c:924-931,5683-5684,5937-5938`；`bdda2/io/det_params.hpp:3-9,28-35` | legacy 的 `w0` 含显示纵横比，源码仍读 `GetSystemMetrics`；C++20 二代才显式注入屏幕值。不能仅设置 `BDDA_MAXX/MAXY` 就声称复制的 legacy exe 已固定屏幕；本轮应以 dump 实际 `w0/d0` 为准。 |
| detparams CSV | `df/df.c:576-578,1512-1519` | 列为 `step,d0,h1,h5,f1,f0,w0,hh,g0`；每步 df04 末写。具备直接窗口输入，不必将 bb52 的 `1e-6` 误当各算例搜索距离。 |
| verts CSV | `df/df.c:555-558,4335-4345` | 列为 `step,block,vidx,x,y`；**df25 更新前**的本步初始几何，每块包含两端回绕垫点。剥别名后恢复多边形，特征号也必须同步规范化。 |
| contacts CSV | `df/df.c:559-562,1989-1996` | 列为 `step,contact,mtype,p1,p2,p3,m4,m5,m6,m0_0,m0_2,o2,o3,o4,o5`；post-df06/post-df07 拓扑 + 转移状态，不是本步收敛状态。 |
| 求解位移 CSV | `df/df.c:502-504,3876-3884` | `zsto2` 是存储行号上的六分量解，需 `k2step` 映射；默认只捕获第一次 `m9==1`，后续削步重试可能继续改变解，不能无条件当“本步最终运动”。 |
| 状态时间面 | 本树 `src/eab/readers/bdda_df.py` 的模块头、`last_oc_judgments` 与 `load_records` | 读取器把 contacts 的 `m0_2/o3/o4` 放入初态/参考字段；当前 `mode/gap/shear` 来自 df22，缺 df22 则 UNKNOWN/空，不允许伪造本步状态。M4a 静态几何 gap 应独立计算并标注。 |

`p1` 是主参考顶点，`p2-p3` 是有向参考边；`m4..m6` 在 v-v 是第二组三点，在共边 v-e 也可携带换半信息。`mtype=0/1` 分别是 v-e/v-v；不能把 `m0_2=3` 当新盖类型。`o2` 是锁定投影参数，`o3/o4` 分别是法/切向状态量，`o5` 是接触长度。对应定义见 `bdda2/detect/classify.hpp:24-25`、`bdda2/core/contacts.hpp:17-18,103-115` 与本树读取器模块头。

## 3. 是否存在“按本步位移方向选边”的首入规则？

**检测层未找到。** 已逐段检查 `df/df.c:1346-1999`、`src/bdda/detect.py`、`bdda2/detect/{angles,candidates,classify}.hpp`，并检查调用时序 `df/df.c:6003-6039`、`bdda2/driver/run.hpp:366-391`。输入只有步初几何、角度、物理窗口；所谓 `entrance` 参考边通过静态角度、全局 y 方向的 `abs(sin)` 平局规则，以及 df07 首步的最短 gap 规则选出，不读取本步求解位移方向。

此结论限定于“候选枚举 / 两参考构造”。**开闭判定当然消费求解位移**，v-v 的当前活动参考会随法向间隙与状态改变；这不等于沿给定刚体相对平移方向求首次进入 `E(A,B)`。

相邻 verts 帧可恢复上一拍逐顶点增量，但 DDA 的运动含平移、转动、应变（`df/df.c:4145-4163`、`bdda2/driver/run.hpp:367-377`），不是一个可直接喂给二维平移首入 API 的块对方向；第一步没有前帧，末步没有后帧。`zsto2` 也有上述时间面限制。因此当前离线接缝可以明确采用**静态“窗口内有效盖”**，不得把从某条 legacy 边人为构造的法向方向写成“本步实际运动”。

本树旧首入门 `tests/test_kernel2d_entrance.py:243-297` 检验的是 53 条 legacy v-e 沿各自边法向逼近可获得相应首入/最浅盖，并非已导入 legacy 真实本步运动；这一区别保留。

## 4. “15 例家族”的准确清单

权威的**可执行清单**是 `tools/bdda/verify_cpp.py:31-42` 的 `FAMILY`，原生 Qt 同一清单为 `bdda2/studio/engine_bridge.cpp:450-455` 的 `t0primeFamily()`。`verify_cpp.py` 文件头仍写“九案例”，相邻注释仍写“13 案例”，但当前列表实际为 **13 个 golden 输入配对 + F038 / S038 = 15**；以列表而非陈旧注释为准。

下表全部输入文件已读取核对存在；`db` 原视界 N5 是第二个 token（读取协议 `tools/bdda/verify_cpp.py:53-55`），不是本次 M4a 承诺跑满的步数。

| 序号 | 算例键 | bb 文件 | db 文件 | 来源目录 | 原 N5 |
|---:|---|---|---|---|---:|
| 1 | 52 | bb52 | db52 | `df/` | 50 |
| 2 | 12 | bb12 | db12 | `df/` | 100 |
| 3 | 50 | bb50 | db50 | `df/` | 50 |
| 4 | 51 | bb51 | db51 | `df/` | 50 |
| 5 | 03 | bb03 | db03 | `df/` | 100 |
| 6 | 05 | bb05 | db05 | `df/` | 100 |
| 7 | 06 | bb06 | db06 | `df/` | 100 |
| 8 | 09 | bb09 | db09 | `df/` | 100 |
| 9 | 10 | bb10 | db10 | `df/` | 100 |
| 10 | v01 | bbv01 | dbv01 | `df/` | 100 |
| 11 | v01/v01a | bbv01 | dbv01a | `df/` | 400 |
| 12 | v02 | bbv02 | dbv02 | `df/` | 100 |
| 13 | v02/v02a | bbv02 | dbv02a | `df/` | 400 |
| 14 | F038 | bbF038 | dbF038 | `df/bench/` | 30 |
| 15 | S038 | bbS038 | dbS038 | `df/bench/` | 30 |

- 旧运行入口：`python tools/bdda/verify_cpp.py --family --engine gen2 [--steps N]`；解析和循环在 `tools/bdda/verify_cpp.py:120-142`。它同时跑求解器和插桩内核，不适合作为本工单直接运行的脚本，因为本工单要求把 exe 也复制到本树沙箱。
- M4a 只用本树 `tools/run_bdda_kernel.py` 协议：复制 `D:/b-DDA/build/kernel/df_rebuilt.exe` 和原始 bb/db，以 `ff.c` 两行命名、`BDDA_KERNEL_MODE=1 BDDA_DF17_DEBUG=1 BDDA_DUMP_STEPS=N` 在本树沙箱运行。变体必须按 **bb + db 配对**命名，不能让 `bbv01/dbv01` 与 `bbv01/dbv01a` 共用 `bbv01_N3` 目录。
- `golden` 是 `df/` 输入族标签，**不是同名快照与 bench 一一配对的关系**。Python 工作台扫描 `df/`、`df/inv/`、`df/bench/` 并独立补 a-变体（`studio/engine2.py:92-115`）；Qt 线同样扫描并补变体（`bdda2/studio/engine_bridge.cpp:107-130`）。
- bench 范围是 `F038,S038,B050,W025,W049,W100,W300`（`tools/bdda/verify_cpp.py:42`）；15 例族仅纳入前两个。Fast 门另含 W025/W049/W100/W300（`tools/bdda/verify_fast.py:32-36`），不能拿该 8 例 Fast 子集替代 15 例族。
- F038/S038 是 38° 摩擦角看护：打包说明 `tools/bdda/make_portable2.py:87`；T0 清单对 F038 的理由在 `tools/bdda/verify_t0.py:30-34`。**未找到专用 `df/bench/README.md` 或当前 bench 全集的独立 JSON manifest**（搜过 `df/bench/` 文件清单、`tools/bdda/*.py` 的 FAMILY/BENCH/CASES 定义）；当前以脚本清单与实际输入为依据。

## 5. 现有对账门究竟比较什么

| 门 | 源码位置 | 实际断言与限制 |
|---|---|---|
| T0：二代 Faithful vs C++ 一代 oracle | `tools/bdda/verify_t0.py:25-35,57-82,105-108`；原生 Qt `bdda2/studio/engine_bridge.cpp:486-499` | 位移 CSV 和完整状态 CSV **逐字节相同**。当前是 14 个配对（13 golden + F038），不是 15。本轮仅读代码，不重新宣称其运行全绿。 |
| T0′：求解器 vs `df_rebuilt` | `tools/bdda/verify_cpp.py:76-118,136-138` | 用 `k2step` 把物理块号映射到 zsto2 存储行，逐步逐块六分量解最大绝对差 `<1e-12`；不是检测集合 / 法向门，且源码按双方已有解的步范围比较。 |
| T1：Fast vs Faithful | `tools/bdda/verify_fast.py:61-120` | 按 `(step,idx)` 比 `lock_final/lock_solve`、`p1,p2,p3,m4,m5,m6`、`sign(o4)`，并比记录总数；位移用 `atol=1e-12, rtol=1e-10` 混合范数；比较 `hh_cur` 轨迹。**实码未单独比 `mtype`，也未实现文件头所称 w6 选中接触索引核对**；新接缝不可照抄这些遗漏。 |
| Python D1–D3 | `tests/test_d1d3_contact_detection.py:71-102` | bb52 前两步顶点角逐项相等、候选列表含顺序相等；首步七元组 54/54，第二步仅要求 ≥52 条同序相同及集合差各 ≤2。不是一般多例严格同构；文件头对历史差异的“纯角平局”解释也弱于后来的 df06 转移分析。 |
| Python 多步 | `tests/test_refkernel_nstep.py:41-63,93-122` | 检查求解残差 `<1e-12`、判定失配 0、转移未匹配 0，部分门检查几何误差与开闭收敛；不是直接验证 eab。 |
| 本树 G1 | `tests/test_bb52_g1.py:34-56` | 首步 53 条 legacy v-e 全匹配，贴合 gap `<1e-6`；额外盖多数在边端点，另核顶点-块集合。并未覆盖 15 例多步。 |
| 本树二维首入 | `tests/test_kernel2d_entrance.py:243-297` | 沿每条边法向构造首入，并对微贯入核最浅盖集合；不是 legacy 真运动回放。 |
| 本树 G4 | `tools/g4_multistep.py:1-12,78-89` | 步初几何/转移态/跨步 gap 趋势预测与 df22 末次状态对比；是活动集先验试验，不是完整接触拓扑同构门。 |

M4a 应称 **T1 型检测同构门**：规范化特征集合、类型、法向、几何 gap 及具名差异计数。没有 eab 弹簧装配、开闭求解和位移轨迹，就不能声称已满足原 T1 的锁态/滑动符号/位移三层契约。

### 5.1 本轮发现并修复：本树 VV 读取身份错误（不是 legacy 缺陷）

`df/df.c:1660-1681` 构造的两组三点参考，各自包含同一对真实候选角点；`:1689-1693` 还可能把两组三点互换。故真实 VV 身份是**规范化后的两组三点集合交集**，不是固定 `(p1,p2)`，也不能改成固定 `(p1,p3)`。

实物例：本轮 `bb52_N3` step 1 contact 47 的六列是 `(171,126,125,171,125,124)`；交集为 `{171,125}`，旧读取器却报 `{171,126}`，把参考边另一端当成接触角点。这个错误会把仍在搜索窗口内的真实 VV 误描成“legacy 在很远顶点间发射接触”，因此不能把它归入 legacy 差异。

修复在本树 `src/eab/readers/bdda_df.py::_vv_opposite_vertex`：alias 规范化后取交集，要求恰有两个点、包含 p1；有几何时同时核查两个角点分别属于当前接触的两块。异常引用抛 `ValueError`，不回退猜 p2。`ContactRecord` 契约模块头同步解释该身份。既有无块号数据仍保留 UNKNOWN，不补造身份。

证据：[新门](../tests/test_m4_bdda_vv_reader.py)、[修前红灯](../reports/codex/M4a_evidence/vv_reader_before_fix.txt)、[修后绿灯](../reports/codex/M4a_evidence/vv_reader_after_fix.txt)。新门包含四种参考分支、两半交换、alias、五种畸形输入与将旧 p2 映射重新注入读取路径的变异。当前全部 180 条 VV 的原始双参考拓扑可判；固定 p2 的反事实错 124 条，其中 sensor 第 2 步 1 条原本缺块号而不生成特征，实际可解析身份是 179 条。该测试文件本次 `24 passed in 0.31s`，不替代全套验收。

### 5.2 首步 df22 `o4` 残值的源代码路径

`df/df.c:3994` 在 v-v 或当前判开时直接跳到 `c212`，绕过 `:4028-4030` 的切向量重算，而 `:4072-4075` 对每条记录无条件导出 `o4`。首步此前未赋值的 `o4` 因而可能继续出现在 df22；后续步 `df04:1366-1367` 才对开态/v-v 清零。M4a 的重复运行差异应按实际行的 `mtype==1` 或 `m0_new==0` 跳过条件核对，而不是把所有 `o4` 或“小量”统统豁免。实测次数、列级清单与哈希以 fixture 生成证据为准。

## 6. 只建议：所有者批准后 `BDDA_DETECT` 的最小接缝方案

**本节没有执行；全部姊妹修改均须所有者另行批准。** 第一阶段应沿用本轮已冻结的数据契约，先添加只读影子输出，再考虑替换。无需为影子阶段重写 C++ 几何内核，也不应让 eab `src/eab` import 姊妹代码。

### 6.1 开关语义

| 设置 | 建议行为 |
|---|---|
| 未设 / `BDDA_DETECT=legacy` | 原始 `vertex_angles → detect_candidates → classify_contacts → df06` 路径不变；不开 eab、不分配影子表、不写额外文件。默认物理及 legacy 产物逐字节不变须由门证明。 |
| `BDDA_DETECT=shadow` | 同一份**只读步初几何和显式参数**给两路；实际求解永远消费 legacy 的原表/顺序/状态，eab 只生成旁路 ContactRecord 与对账文件。不将差异修正反馈给 legacy。 |
| `BDDA_DETECT=eab` | 仅在所有者明确批准切换后允许，将 eab 输出经单独映射层转换为下游 Tuple7 / ContactStore；现阶段应拒绝并给出“尚未批准/接缝未验证”的明确错误，不能静默等价 shadow 或 fallback。 |
| 非法值 | 显式报错；不要照搬 `BDDA_SOLVER` 未知值静默回退的行为。 |

若所有者坚持只允许 `legacy|eab` 两值，可用独立 `BDDA_DETECT_SHADOW=1` 表示只读旁路；不要让 `eab` 一词同时指“求解仍用 legacy”和“已替换检测”。

### 6.2 最小改动文件与职责

1. **`bdda2/driver/run.hpp`**：在 `Options` 旁加类型化 `DetectMode` 与可选只读 snapshot hook；在当前 :386-388 检测接缝采集步初几何、参数、raw Tuple7；在 :391 转移后另采集实际 legacy 表。legacy 分支保留原调用及顺序，不移动数值运算，不复用 M/C 缓冲给影子线程写入。
2. **`bdda2/driver/main.cpp`**：仿 :26-30 仅在 CLI 解析 `BDDA_DETECT`，将显式模式注入库；影子输出用独立文件名/目录，原 `z/state/force/geom` 格式与字节不变。记录 exe/hash、输入哈希、窗口、步号、detector version、模式和错误，禁止把运行环境隐含在几何谓词里。
3. **建议新增 `bdda2/io/detect_snapshot.hpp`**：稳定、版本化地序列化只读步初 geometry + detparams + 两个时间面（raw-df05 / post-df06）的 Tuple7。借用文件协议而非让 C++ 数值库 import Python；这是建议新增文件，不是现存实现。
4. **`studio/engine2.py`**：`run_forward` 增显式 detect 配置，只在 shadow 开启时调用独立 eab 离线/子进程对账工具；argv 必须列表传递，不拼 shell。T0 路径与 `_env` 清理 `BDDA_DETECT/BDDA_DETECT_SHADOW`，避免宿主环境污染。
5. **`bdda2/studio/engine_bridge.hpp/.cpp`**：因为正演在进程内调用，必须把 detect 设置传到 `Options`，不能只设环境；`pinnedEnv()` 同时清理新环境变量。可先仅暴露 legacy/shadow，再加 UI 控件；不必改 `contact/judge.hpp`、装配或 solver。
6. **本树 `tools/` 离线对账入口及 L5 适配器**：消费 versioned snapshot，在独立输出目录写每步两路规范化记录、类别、汇总与输入哈希。C++ 影子钩子只落盘，运行结束后旁路 eab 回放即可实现“同一路径输入，两路都跑”，无需在热循环启动每步 Python 进程。
7. **Python 参考内核若也要接缝**：另在 `tools/bdda/audit_refkernel_nstep.py:335-339` 的组合层注入 detector，而不改 `src/bdda/detect.py` 的 legacy 函数。它不是 C++20 正演 UI 的必改项。

### 6.3 必须随建议一并批准的验收门

- 对同一 exe / 同一输入 / 显式屏幕参数，`unset == legacy == shadow` 的**原有可复现产物逐字节一致**；非复现字段预先列入清单，不能因为差异才临时豁免。原有 T0 14 配对继续保留，并新增 shadow 开/关参数化；三种设置必须在日志中可辨，防止开关根本没走。
- 15 例逐步双路检测侧：集合/类型/法向/gap 对账，所有差异有可跑判据，未知类别立即红；补打破对称、缩放/平移/旋转和窗口边界的小算例，不能仅依赖 golden 轴对齐族。
- shadow 故障隔离：eab 超时、崩溃、记录缺失都显式标红该次 shadow 审计；不改变 legacy 物理进程，不把失败报告成“无差异”。
- 真正 `eab` 切换前，需单独验证 tuple 映射、两参考选择、df06 顺序继承、滑动符号、锁态轨迹与位移，并由所有者批准。M4a 的静态离线检测门不能替代这些门。

## 7. 可复核方式与未找到项

本次从 `D:/eab-wt/cx-m4` 执行只读 `rg -n` 与 `python -X utf8` 文本读取。常用搜索词：`BDDA_SOLVER`、`FAMILY/CASES/BENCH`、`detect_candidates/classify_contacts`、`bdda_debug_contacts/bdda_debug_verts/bdda_debug_detparams`、`df04/df05/df06/df18/df22`。未运行姊妹的测试或工具，所以本文只报告**源代码契约与输入清单**，不把其注释里的历史通过数当本轮验证结果。

- **未找到 Python 版 bdda2 内核**：搜索 `src/`、`bdda2/`、`studio/` 中模块与入口；实际为 Python 参考 bdda + 两套工作台桥 + C++20 bdda2。
- **未找到检测层按本步位移方向的首入**：搜索范围见第 3 节；发现的是静态 entrance 参考与求解后的活动参考判定，二者不混称。
- **未找到 legacy df.c 的 BDDA_MAXX/MAXY 环境读取**：全文搜索这两个名称无命中；发现屏幕 API 读取，不能把二代的环境隔离约定转嫁给旧 exe。
- **未找到 bench 独立清单文档**：`df/bench/README.md` 不存在；当前 15 例依据两个相互对应的可执行列表，不把某一目录所有文件都算作同一家族。
- **未找到既有 eab 与 15 例的完整在线 T1**：本树已有 bb52/G4 与姊妹 T0/T1 均有上述范围；本轮仍是第一步离线接缝。
