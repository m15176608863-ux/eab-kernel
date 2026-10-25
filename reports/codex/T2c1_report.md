# WO-T2c1：更强的笼/逃逸提议器与刚体临界公差括号

**一句话：10 例的已证括号都缩小了，凸耳两例达到目标宽度；燕尾八例仍偏宽，不能把它们说成临界公差已经算准。**

科学结果、固定回放与端点诊断已完成；收尾快档及全档四分片均通过。tools 整文件静态要求尚未闭合，因此本单为 **PARTIAL**，不是全部验收完成。

## 1. 范围、基线与信任边界

- 工作树 `D:/eab-wt/cx-e2`，分支 `codex-work`，干净起点 `cfa3e90b8fcca2117021bb12df188322199f3cfe`；Python 3.12.10，`core.autocrlf=false`。
- 只写本工作树及 `D:/eab-evidence/reports/codex/T2c1_evidence/`；没有 Git 写操作、姊妹修改、C++ 修改，未结束其他人的进程。生产核验器、独立核验器/oracle/实例生成器、v5 引理、三个分析器及 policy 均保持开工字节；旧测试只作 §6 获准的路径引用/复制根机械改动，不泛称整个独立侧所有文件未变。
- [工作合同](file:///D:/eab-evidence/reports/codex/T2c1_evidence/work_contract.json)、[2674 文件回退 ZIP](file:///D:/eab-evidence/reports/codex/T2c1_evidence/baseline_anchor/source.zip)、[逐文件 SHA](file:///D:/eab-evidence/reports/codex/T2c1_evidence/baseline_anchor/manifest.json)。回退须先逐文件比较并保护所有者后续修改，不能直接覆盖工作树。
- 单块、固定邻居，归属沿用 WO-T2a D1；不作新颖性/实现序数宣传。笼结论只来自生产文本与独立 `load_json` 双接受；失败提议仅 `UNPROVED`。不报告 δ*_SE2 的确切值，括号外均为“未证”。
- 逃逸沿用已验收 T2b 的核验范围：`verify_se2_escape` 检查完整原路径及无限射线，独立 oracle 检查所有有限 SE(2) 段与尾射线前缀。保留 `independent.infinite_ray_verified=false`；没有新增独立无限尾证明，也不修改核验器来制造一致。
- 所有长跑保留各自源码、参数与完整结果；合并表只是已接受端点选择，不拼接中断运行。字节导出不是新鲜 Git worktree；所有者的新鲜树验证及一路独立对抗验收不由本代理自签。

## 2. 提议器改进与具名门

实现：[笼](file:///D:/eab-wt/cx-e2/tools/t2c_cage_proposer.py)、[逃逸](file:///D:/eab-wt/cx-e2/tools/t2c_escape_proposer.py)、[交替扫描](file:///D:/eab-wt/cx-e2/tools/t2c_science.py)。这些都是不可信工具，浮点不决定接受。

|项目|本单实际实现|具名验证及限制|
|---|---|---|
|非原点、多阶段封口|在 Γ 内枚举片重心/扇形重心等，按有理平方内余量排序；局部耳收缩生成中间折线，每条同伦带仍需四点严格见证|`test_low_room_has_mixed_kernels_distinct_loops_and_nonorigin_caps`；`test_nonstar_shaped_cap_contracts_in_multiple_stages_without_origin` 用平移 U 形及独立盒不等式核四点。不是一般三角剖分完备算法|
|整周闭链|在双图区间 `[-1,3]` 搜索，含首尾接缝；`modes=('closed',), mixed=False` 可完全移除不变圆，仅用转动收缩片|`test_rotation_only_full_circle_is_dual_verified_with_no_caps_or_disk`，小真值双核验；不声称十例最终证书用了此模式|
|不同 Γ 的连接|每区间单独提议 Γ；稳定几何锚点、单调边索引对应、重复顶点补齐，仍逐四点核验|`test_monotone_alignment_retains_edges_and_pads_repeated_vertices`；`test_alignment_uses_stable_geometric_anchor_not_lexicographic_jump`|
|自适应细分|优先拆失败区间；否则用 V1 所需收缩平方/片重心到边余量平方作调度评分；按端点缓存区间|`test_adaptive_split_uses_failure_interval_without_changing_other_knots`。余量是调度代理，不是 Γ 上最优可用收缩的证明|
|组合内核|同一区间可同时携带不变圆和转动收缩片，沿用既有 exact/disk/left/right 见证合同|低房间门逐区间检查两种片。T2b 已有组合基础，本单接入新搜索，不宣传为首次实现|
|资源出口|秒数、区间、片对、顶点、同伦步数、目标数、局部扫描数、自适应步数及每角域子预算可配置|`test_limits_never_return_escape_or_a_certificate` 五参数；`test_final_observed_overrun_discards_an_already_verified_candidate`；协作式限时并非硬抢占，已观察超限即丢弃候选|
|更细逃逸/更长路径|沿旧精确路径建稀疏管道，增加管道宽度及尾部高度，路径节点上限 200000；实际运行 `1/400`，凸耳补充 `1/800`|`test_sparse_grid_really_uses_one_over_400_and_exact_source` 实跑千余节点；`test_proposal_resource_limits_are_unproved`、`test_overdue_candidate_is_discarded`|
|界与搜索失败分离|失败只更新经验搜索前沿，不修改已证 lower/upper；显式选择 T2b 逃逸范围后才采纳双通过路径|`tests/test_t2c1_science.py` 与 `test_failure_bisection_never_raises_cage_lower_or_changes_upper`、`test_finite_verified_candidate_is_not_silently_promoted`|

[实现复核及已知局限](file:///D:/eab-evidence/reports/codex/T2c1_evidence/cage_implementation_review.md)明确：各角区间的旧屏障搜索仍绕平移原点；本单**没有**任意漂移自由分量的拓扑跟踪。换封口点不能消灭 Γ 内真实自由点；耳收缩、线性连接和有限角域表都可能停滞。

[最终功能使用审计](file:///D:/eab-evidence/reports/codex/T2c1_evidence/feature_usage_final_02/report.md)：十例中 7 例有不同 Γ、非原点多步封口及混合片；但屏障见证没有一例同时使用两类内核。d06/k01/k02 是纯圆整周闭链；**0 例最终科学证书是含转动片的整周闭链**。纯转动整周能力由上述小真值门守护，不能冒称已解决凸耳科学例的转动闭链瓶颈。

## 3. 科学表 v2

下表的 δ_disk 是旧方法已有网格值，不是其全域最优值。宽度及相对宽度为精确有理数；目标为相对宽度 ≤1/256。

|ID|δ_disk|旧δ_cage|新δ_cage|旧δ_esc|新δ_esc|δ*_T|宽度|相对宽度|N|封口|整周|目标≤1/256|
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
|d01|23/128|23/128|257/1024|3/10|1211/4096|1/3|183/4096|549/4096|12|是|否|否|
|d02|63/256|63/256|81/256|1851/5120|1451/4096|1/2|155/4096|155/2048|8|是|否|否|
|d03|63/256|1/4|597/2048|21/50|843/2048|3/7|123/1024|287/1024|8|是|否|否|
|d04|13/128|13/128|573/4096|1/5|397/2048|3/14|221/4096|1547/6144|8|是|否|否|
|d05|63/256|63/256|687/2048|2043/5120|1595/4096|24/41|221/4096|9061/98304|8|是|否|否|
|d06|93/256|93/256|747/2048|5393/10240|1037/2048|24/41|145/1024|5945/24576|2|否|是|否|
|d07|13/64|13/64|1019/4096|849/2560|1293/4096|24/65|137/2048|8905/49152|12|是|否|否|
|d08|25/256|13/128|325/2048|11377/51200|55/256|12/49|115/2048|5635/24576|15|是|否|否|
|k01|75/256|75/256|301/1024|3923/12800|1209/4096|1/3|5/4096|15/4096|2|否|是|是|
|k02|93/256|93/256|747/2048|977/2560|375/1024|12/29|3/2048|29/8192|2|否|是|是|

主扫 `joint_01` 共 164 查询，δ 用 `2^-12` 网格，笼每查询提议预算 30 秒/128 区间、角域子预算 3 秒；逃逸每查询提议预算 45 秒（不含随后精确核验）、实际网格 `1/400`、两级管道、200 万网格单元及 20 万路径节点上限。两侧**经验搜索前沿**均网格结束，不意味着真实括号窄到 `2^-12`。八例燕尾的证书间隙远大于网格，因此不以 `2^-16` 继续小数细化冒充消除未证区。

完整补充运行单列：

- [d01 高预算](file:///D:/eab-evidence/reports/codex/T2c1_evidence/high_budget_d01_01/summary.json)：两点，`257/1024` 经双核验，提高主扫下界一个 `2^-12` tick；`1119/4096` 180 秒仍未证。原同点 30 秒失败说明资源/调度会影响提议，不能把失败当作不可行。
- [凸耳闭链专项](file:///D:/eab-evidence/reports/codex/T2c1_evidence/closed_chain_high_budget_01/summary.json)：每点 180 秒、初始 32 区间、最多 1024 区间；k01/k02 达到 N273/N376，仍在 V4 屏障图搜索失败。局部极细分时 rho 停在旧有理平方根上包络的 `1/1000000`，只记录现象，不改合同、不据此证明无笼。
- [细网格初探](file:///D:/eab-evidence/reports/codex/T2c1_evidence/fine_escape_01/summary.json)：`1/800`、管宽 2/6/12，在更低两点无路径，不更新任何界。
- [细网格终版](file:///D:/eab-evidence/reports/codex/T2c1_evidence/fine_escape_03/summary.json)：k01=`1209/4096`、k02=`375/1024` 均接受，使两凸耳达标。`fine_escape_02` 因读取仍在写的主汇总而 JSONDecodeError，**整轮作废**；03 在主扫完整结束后从头重跑两点，未采用02的部分成功或拼接日志。见[作废原件与 SHA](file:///D:/eab-evidence/reports/codex/T2c1_evidence/logs_lf_fine_invalid02/invalid_run_manifest.json)。

端点观察另在d07=`1019/4096`得到双接受笼，比原选择下界再提高一个tick；[增量重核](file:///D:/eab-evidence/reports/codex/T2c1_evidence/final_selection_02/d07_recheck.json)只核这一新输入，原joint、选择01和观察源不改。选择02只改d07，全部上界及其他九行原样；不追加任何新探针。

[最终选择与来源](file:///D:/eab-evidence/reports/codex/T2c1_evidence/final_selection_02/summary.json) · [机器表](file:///D:/eab-evidence/reports/codex/T2c1_evidence/science_summary_02/table_v2.json)。限时探索受机器负载影响，不声称这些值是该提议器的确定性最优值；可信对象是冻结的证书及其回放。

## 4. 双核验、实例与一致性

[一致性机器审计](file:///D:/eab-evidence/reports/codex/T2c1_evidence/science_summary_02/consistency.json)：1917 项检查通过（继承01的1841项及其SHA，另做76项增量），0 失败。原主扫与预算补充来源的170查询（164+6）计数不改，另列完整端点诊断20查询/1新笼，不把 pilot、细网格初探或作废运行拼成同一轮。

- 主查询41个新笼成功，加端点诊断1个及10个旧下界复核，共52条笼接受记录；生产/独立屏障段计数均3146。所有笼都经生产 JSON 文本与独立 `load_json` 入口核验，每个接受 δ 的 T1b 平移判定均为 `TRAPPED_TRANSLATION`。
- 42 个新逃逸成功查询，加 10 个旧上界复核，共 52 条接受记录；生产有限段对 14829，独立有限检查含尾前缀为 14985。计数差来自范围，不伪称二者检查对象数相同。
- 原科学来源158次、端点诊断16次及新d07重核1次燕尾实例比对全部等于独立 `canonical_instance(dovetail_instance(...))`；不把凸耳说成使用了燕尾独立生成器。
- 10/10 下界提高，10/10 上界下降，始终 `旧lower ≤ 新lower < 新upper ≤ 旧upper ≤ δ*_T`。两例达宽度目标，八例未达。
- canonical 几何+δ 身份审计含上述104接受记录及4条另存pilot，共108；无同输入笼/逃逸碰撞。另核 case+δ 不对应不同几何。归一范围为独立 canonical_instance 的简单环冗余点/方向/循环起点合同，障碍顺序保留；不声称任意几何编码等价判定。

### 4.1 有限 oracle 分歧必须停下

集成审阅发现工具将潜在有限分歧并为 `UNPROVED` 而继续的流程缺口，未发现实际数学矛盾。主扫及所有补充源冻结结束后，才最小修改 `audit_proposal`：生产接受而独立有限拒绝，或生产有限段已非 FREE 而独立接受，立即抛出带双方完整结果的异常。只因无限尾/输入连续性拒收且有限 oracle 接受，不冒称同范围矛盾。

[修补、原新源码及差异](file:///D:/eab-evidence/reports/codex/T2c1_evidence/guard_install_01/report.md)：原科学 52 份审计、14829 生产有限对均未触达新守护；原元数据/源码 ZIP/个体记录 SHA 前后不变。只改原运行未触达的失败分支，没有重写旧来源 SHA。`tests/test_t2c1_audit_guard.py` 含两方向、异范围对照和内部守护删除变异；与计数门、既有逃逸门合跑原样 `19 passed in 1.09s`。这不是所有者独立对抗验收。

### 4.2 固定回放与数值输入边界

[固定数据](file:///D:/eab-wt/cx-e2/tests/data/t2c1/index.json)与[回放门](file:///D:/eab-wt/cx-e2/tests/test_t2c1_replay.py)保存十例最终笼及十条最终新上界各一份，比较生产/独立完整返回、所有状态、精确时间和计数，不只比较 valid，不钉当前源码。独立侧有 `load_json` 调用 spy；燕尾16个端点独立实例、10个平移困住同时重核。耗时较长项标 slow，全档实际执行。

首轮构建与安装文件合计180196字节，单文件最大28022字节；[构建摘要](file:///D:/eab-evidence/reports/codex/T2c1_evidence/replay_build/build_summary.json)与[实际安装清单](file:///D:/eab-evidence/reports/codex/T2c1_evidence/replay_verify_01/installation.json)分开保存。[规范交付证书目录](file:///D:/eab-evidence/reports/codex/T2c1_evidence/certificates/final_01/)有30份最终输入的原字节副本，[manifest](file:///D:/eab-evidence/reports/codex/T2c1_evidence/certificates/final_01/manifest.json)逐对核原run/副本SHA；原独立run位置不改。

[数值边界审计](file:///D:/eab-evidence/reports/codex/T2c1_evidence/replay_build/numeric_boundary_audit.json)：30份最终输入真正参与核验的几何/segments/ray字段无float JSON数值、NaN或Infinity，可精确载入；36处内部输入注入被拒绝，删除审计守护的内部变异被语义断言杀死。该有限数据审计**不等于 tools 静态闭子集已通过**。

首轮完整回放（含slow）原样末行 `31 passed in 220.27s (0:03:40)`，见[完整日志/命令](file:///D:/eab-evidence/reports/codex/T2c1_evidence/replay_verify_01/summary.json)。随后端点诊断为d07产生一份更强新笼，最终选择02仅替换此下界；其余9例及全部逃逸输入不动，原31项结果不改写。新d07的局部回放及收尾全档另列，不为文档重算全部扫描。

[d07最小更新](file:///D:/eab-evidence/reports/codex/T2c1_evidence/replay_update_02/report.md)仅改变d07压缩payload及index对应行/来源字段，最终fixtures+回放测试合计181570字节。其他9个gzip、d07全部逃逸原文及完整预期子树逐项不变，0次逃逸oracle重跑；新笼双文本核验、实例/平移及metadata定向末行 `3 passed in 0.25s`。最终30副本在[final_02](file:///D:/eab-evidence/reports/codex/T2c1_evidence/certificates/final_02/manifest.json)，总1757143字节，相对01恰2文件改变、28原样；[新数值边界审计](file:///D:/eab-evidence/reports/codex/T2c1_evidence/replay_update_02/numeric_boundary_audit.json)再次通过。审计模板 `nonclaim` 中的375是历史扫描数，保留原件不改；本单最终工具扫描以 §7 的376为准。

## 5. 卡在哪一侧、区间/段/盖标签

|ID|侧|δ|最后完整几何尝试|区间|段|标签范围|资源结束|
|---|---|---:|---|---|---|---|---|
|d01|笼|1029/4096|V4_no_winding_barrier|['-1', '-511/512']|N/A_no_Gamma|proposer candidate piece-pair set, not an identified limiting cover|是|
|d01|逃逸|605/2048|no_tube_path_found_not_a_trapping_conclusion|None|N/A_no_path|label_not_recorded|否|
|d02|笼|1297/4096|V4_no_winding_barrier|['-1', '-31/32']|N/A_no_Gamma|proposer candidate piece-pair set, not an identified limiting cover|是|
|d02|逃逸|725/2048|no_tube_path_found_not_a_trapping_conclusion|None|N/A_no_path|label_not_recorded|否|
|d03|笼|1195/4096|V4_no_winding_barrier|['0', '1']|N/A_no_Gamma|proposer candidate piece-pair set, not an identified limiting cover|是|
|d03|逃逸|1685/4096|no_tube_path_found_not_a_trapping_conclusion|None|N/A_no_path|label_not_recorded|否|
|d04|笼|287/2048|V4_no_winding_barrier|['-1/4', '0']|N/A_no_Gamma|proposer candidate piece-pair set, not an identified limiting cover|是|
|d04|逃逸|793/4096|no_tube_path_found_not_a_trapping_conclusion|None|N/A_no_path|label_not_recorded|否|
|d05|笼|1375/4096|V4_no_winding_barrier|['-1', '-31/32']|N/A_no_Gamma|proposer candidate piece-pair set, not an identified limiting cover|是|
|d05|逃逸|797/2048|no_tube_path_found_not_a_trapping_conclusion|None|N/A_no_path|label_not_recorded|否|
|d06|笼|1495/4096|V4_no_winding_barrier|['0', '1/2']|N/A_no_Gamma|proposer candidate piece-pair set, not an identified limiting cover|是|
|d06|逃逸|2073/4096|no_tube_path_found_not_a_trapping_conclusion|None|N/A_no_path|label_not_recorded|否|
|d07|笼|255/1024|V4_no_winding_barrier|['-1', '-127/128']|N/A_no_Gamma|proposer candidate piece-pair set, not an identified limiting cover|是|
|d07|逃逸|323/1024|no_tube_path_found_not_a_trapping_conclusion|None|N/A_no_path|label_not_recorded|否|
|d08|笼|651/4096|V4_no_winding_barrier|['-1', '-1023/1024']|N/A_no_Gamma|proposer candidate piece-pair set, not an identified limiting cover|是|
|d08|逃逸|879/4096|no_tube_path_found_not_a_trapping_conclusion|None|N/A_no_path|label_not_recorded|否|
|k01|笼|1205/4096|V4_no_winding_barrier|['-1/4', '0']|N/A_no_Gamma|proposer candidate piece-pair set, not an identified limiting cover|是|
|k01|逃逸|603/2048|no_tube_path_found_not_a_trapping_conclusion|None|N/A_no_path|label_not_recorded|否|
|k02|笼|1495/4096|V4_no_winding_barrier|['-61/256', '-121/512']|N/A_no_Gamma|proposer candidate piece-pair set, not an identified limiting cover|是|
|k02|逃逸|1497/4096|no_tube_path_found_not_a_trapping_conclusion|None|N/A_no_path|label_not_recorded|否|

上表是在上述完整最终选择来源内、括号内最近失败提议，不是已接受端点失败。`V4_no_winding_barrier` 没有生成 Γ，因此线段号必须填 N/A；原 `candidate_labels` 是全候选片对集合，不是唯一肇因盖。逃逸无路径时原扫描未保存失败格点/盖标签，不能虚构标签。资源结束只说明调度未完成，不构成“不存在笼”或“可逃”的判定。

### 5.1 最终两端的指定反向尝试

[完整20点观察](file:///D:/eab-evidence/reports/codex/T2c1_evidence/observer_endpoints_01/diagnostic_report.md)记录了真实调用中的四点失败与浮点最近盖；包装原 `_cells/_witness`，每次原函数调用一次且原返回对象不变，不改核验器。每例含当时近下界一处和精确最终upper一处，19个UNPROVED、1个d07新笼。十个最终upper处均未提议出笼，未发现与已核验逃逸的矛盾；这不是不存在笼的证明。最后几何失败和较早的有段号中间失败采样分列，不能把采样盖标签硬贴成V4唯一肇因。

精确lower处，把最终upper的同一运动参数序列重新作用于lower实例，不重跑网格：[首轮十例诊断](file:///D:/eab-evidence/reports/codex/T2c1_evidence/endpoint_failure_diagnostics_01/compact.md)均被生产与独立有限oracle拒收，4026个独立有限对；首失败段d01/d02/d04–d08为0、d03为2、k01为10、k02为4。d07后来下界提高，须用下述单例增量替代首轮d07。精确标签与浮点近邻VE/EV候选分列；只否决指定路径，不证明所有逃逸路径失败。

[成功upper路径浮诊](file:///D:/eab-evidence/reports/codex/T2c1_evidence/endpoint_diagnostics_01/summary.json)另保留17点采样+旧工具局部细化，不把它当失败或连续最小余量证明，不含尾部采样。

[新d07 lower增量](file:///D:/eab-evidence/reports/codex/T2c1_evidence/endpoint_failure_d07_final_02/summary.json)只重定向新lower=`1019/4096`：双拒收、首失败段0，障碍1/2均PENETRATES，精确特征为VE(1,0)/VE(0,2)，独立351对，无有限分歧；其他九例原记录不变。两端诊断均已有具体尝试与标签边界，不以某一条路径失败代替全部路径判定。

## 6. 长路径隐患

`tests/data/t2b_forgeries/acceptance_20261026/F_<长描述>` 改为 `tests/data/t2b_forgeries/acc/<ID>`，27 个目录/54 个 JSON 原字节 SHA 全同，manifest 仅改 directory 映射，测试及三处文档同步。为使其他既有长测试数据也适配，两个指定复制测试内部的复制根字面量改为 `repo`；断言/核验逻辑不变。

150 字符 basetemp 的两指定测试正式末行：`2 passed in 559.02s (0:09:19)`，实际最长复制路径 252 字符；27 个伪造回放末行 `27 passed in 2.74s`。前两次输入/路径失败单列，第三次从头完整运行，不拼接。

[修复报告](file:///D:/eab-evidence/reports/codex/T2c1_evidence/path_repair/report.md) · [移动及 SHA 映射](file:///D:/eab-evidence/reports/codex/T2c1_evidence/path_repair/move_map.json) · [150 字符正式日志](file:///D:/eab-evidence/reports/codex/T2c1_evidence/path_repair/long_150_run03.log) · [复跑脚本](file:///D:/eab-evidence/reports/codex/T2c1_evidence/path_repair/rerun_long_paths.ps1)。

## 7. 静态门与准入：未闭合事项不能隐藏

三个分析器与CRLF policy字节不变；本单新准入清单为 **空列表 `[]`（0项）**，新增浮点汇点准入0。`tests/test_t2c1_static.py`直接计数本单 tools/tests policy 条目=0，并以两个内部parser输入植入确认断言有牙。不是把不允许的诊断写入豁免。

[显式整文件 raw 扫描](file:///D:/eab-evidence/reports/codex/T2c1_evidence/static_final_01/summary.json)与现有仓门须分开：

|范围|raw诊断|其中允许考虑的证明缺口规则|非证明缺口|
|---|---:|---:|---:|
|tools/t2c_cage_proposer.py|67|48|19|
|tools/t2c_escape_proposer.py|133|91|42|
|tools/t2c_science.py|176|147|29|
|六个新增tests/test_t2c1_*.py|0|0|0|
|合计|376|286|90|

286只是规则分类的原始诊断数，**不是已审准入站点数**，一项也未准入。90项非证明缺口含计时/浮点选择、I/O及跨调用传播等，不能人工改称全部无害，更不能按proof-gap规则准入。显式扫描源前后无变化。

现有全仓入口只扫描src/tests；其0违例不覆盖上述tools整文件结果。工单同时允许不可信 tools 使用浮点/numpy，却要求 tools 按闭子集且浮点汇点0处理；已向所有者提出范围问题，未获新裁定。**因此本项尚未闭合，最终保留PARTIAL，不以数值输入审计或仓门绿替代。**

[静态缺口只读复核](file:///D:/eab-evidence/reports/codex/T2c1_evidence/static_feasibility_01.md)将90条非证明缺口逐类列出。少数有局部闭子集改写机会，但真实 NumPy SAT 搜索、计时/异构数据传播及编排协议不能机械清零；286条中至少99条当前函数范围含 math/NumPy/float，不能按规则名批量准入。后续须选择严格整文件重构，或由所有者明确浮点提议层与精确接收边界的适用范围；本单没有自行豁免。

## 8. 收尾快档、全档四分片及来源

全程 pytest 禁 cacheprovider，显式 basetemp；`PYTHONDONTWRITEBYTECODE=1`。外部运行器将 TEMP/TMP 设为本单 `tmp/<run>`，不写仓外其他目录；测试不依赖其具体路径。Python 3.12 H1 保留收集/分派/实际调用多重集合及逐模块执行覆盖检查。

[运行器](file:///D:/eab-evidence/reports/codex/T2c1_evidence/run_gates.py)仅把已知超 1800 秒的快档墙钟预算改为 7200 秒，全档 10800 秒及 900 秒停滞守卫不变，仓内运行器一字不改。日常约5分钟目标并未实现，不能把延长超时说成成本达标。

开工全档 `t2c1_baseline_20261026`：16415 节点，GREEN；四片原样末行：

```text
4104 passed in 1943.36s (0:32:23)
4104 passed in 2604.72s (0:43:24)
4104 passed in 1733.13s (0:28:53)
4103 passed in 2135.70s (0:35:35)
exact construction AST gate: 0 violation(s)
```

[基线汇总](file:///D:/eab-evidence/reports/codex/T2c1_evidence/t2c1_baseline_20261026/summary.json) · [2674 成员源 ZIP 审计](file:///D:/eab-evidence/reports/codex/T2c1_evidence/t2c1_baseline_20261026/source_archive_audit.json)。

收尾快档 `t2c1_final_fast_20261026`：10375项，原样末行：

```text
10375 passed in 1854.21s (0:30:54)
```

收尾全档 `t2c1_final_full_20261026`：固定四分片共16491项，包含全部快/慢档；原样末行依次：

```text
4123 passed in 2013.64s (0:33:33)
4123 passed in 2654.32s (0:44:14)
4123 passed in 1740.33s (0:29:00)
4122 passed in 2201.02s (0:36:41)
exact construction AST gate: 0 violation(s)
```

[快档完整摘要](file:///D:/eab-evidence/reports/codex/T2c1_evidence/t2c1_final_fast_20261026/summary.json) · [全档完整摘要](file:///D:/eab-evidence/reports/codex/T2c1_evidence/t2c1_final_full_20261026/summary.json) · [双轮归档审计](file:///D:/eab-evidence/reports/codex/T2c1_evidence/final_pair_01/audit.json)。两轮0 failed、0 skip；收集、分派、插件收集与实际call节点多重集合相同，70个src/eab模块均实际执行。相对开工全档新增76个节点（其中10项slow）；最终d07及其余固定回放均在全档实际执行。

两轮2695成员源码清单逐字节相同；两个受测源ZIP均为 SHA256 `1cde35038f3628568bb83ccdec98b800972f96bd56871501e000620eccfbb89c`，全部成员的尺寸/SHA/集合复核，原摘要与源清单未改。两轮结束后仅回填报告及交付元数据，1552个非reports成员仍与受测字节相同。日志原字节及UTF-8/LF展示分别登记于[快档映射](file:///D:/eab-evidence/reports/codex/T2c1_evidence/logs_lf_t2c1_final_fast_20261026/mapping.json)、[全档映射](file:///D:/eab-evidence/reports/codex/T2c1_evidence/logs_lf_t2c1_final_full_20261026/mapping.json)。全档静态0只针对其既有src/tests入口，**不覆盖 §7 的工具缺口**。快档墙钟1871.027秒，全档2853.693秒；不声称达到日常约5分钟成本目标。

重跑须用新run名（下列不在本次收尾后再执行）；实际子命令、显式basetemp及禁cache参数都在摘要中：

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONIOENCODING='utf-8'
$env:TEMP=$env:TMP='D:/eab-evidence/reports/codex/T2c1_evidence/tmp'
$stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
python -X utf8 D:/eab-evidence/reports/codex/T2c1_evidence/run_gates.py --name "t2c1_recheck_fast_$stamp"
python -X utf8 D:/eab-evidence/reports/codex/T2c1_evidence/run_gates.py --name "t2c1_recheck_full_$stamp" --runslow
```


## 9. 交付、回退与遗留

[逐项交付核查](file:///D:/eab-evidence/reports/codex/T2c1_evidence/requirements.json)区分完成项、未达科学目标、T2b逃逸核验范围和静态缺口。证书及大证据放仓外；[H1 归档登记](file:///D:/eab-wt/cx-e2/reports/EVIDENCE_ARCHIVE.md)、[逐文件清单](file:///D:/eab-evidence/reports/codex/T2c1_evidence/delivery_final_01/artifact_manifest.json)、[范围/净增/编码审计](file:///D:/eab-evidence/reports/codex/T2c1_evidence/delivery_final_01/delivery_audit.json)。清单排除可重建 tmp 及自身，原始运行器日志保留字节 ZIP 并另给 UTF-8 无 BOM/LF 视图，不以规范化重写冻结 parser 输入或旧源 SHA。

- 八例燕尾仍有未证间隙；漂移自由分量、封口局部同伦、V4 图搜索/连接与资源上限仍是后续问题。维持 D4，不放开按转角精确的墙函数。
- P1 的燕尾36组合+凸耳4组合扩展未开展，不将现有10例冒称全组合，不据此画区域结论；按工单此项不单独造成 PARTIAL。
- tools 整文件静态要求仍待闭合/所有者裁定；没有用准入隐藏浮点汇点。
- 本地测试/内部多代理审阅不是所有者新鲜树和独立对抗验收，也不是全输入域证明。

T2C1_PARTIAL：tools 整文件静态要求未闭合（376条诊断、0新增准入）；八例燕尾未达目标宽度。
