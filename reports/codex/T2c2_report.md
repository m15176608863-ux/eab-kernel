# WO-T2c2：8 弦凸耳刚体临界公差的精确核验与证书佐证

**一句话：对本单指定的 8 弦凸耳、墙不腐蚀和两种容差元，精确核验支持所有者定理——允许转动后临界公差恰好下降 √5/2−1，约 11.8%；方形与八边形的相对降幅相同。**

**T2C2_DONE。所有者 2026-10-26 确认**接受“有向有理代理双核验＋精确包含转移”作为 §5 第 3 项交付口径；这仍不是不可修改的原核验器直接接收无理实例。原交付已提交为 `1488914`，原收尾快档10428项、全档16550项及静态门全绿。此次10项验收返修已完成，50变异、定向67门、静态及新全仓快档10436门通过，见 §9；未发现定理反例，未修改定理稿。

## 1. 合同、基线与解释边界

- 工作树 `D:/eab-wt/cx-e2`，干净起点 `codex-work @ a0eb727b4a2c59561ff59b96b447bc61d4fa05e7`；Python 3.12.10，`core.autocrlf=false`。没有 Git 写操作、姊妹写入、C++ 改动或结束非本单进程。
- [工作合同](file:///D:/eab-evidence/reports/codex/T2c2_evidence/work_contract.json)、[2696 文件开工 ZIP](file:///D:/eab-evidence/reports/codex/T2c2_evidence/baseline_anchor/source.zip)、[逐文件回退清单](file:///D:/eab-evidence/reports/codex/T2c2_evidence/baseline_anchor/manifest.json)。回退只能比较后逐文件操作，不可覆盖所有者后续修改。字节导出不是新鲜 Git worktree。
- 定理与证明归属所有者的 [第 2 版定理稿](file:///D:/eab-wt/cx-e2/docs/t2c2_knob_theorem.md)，石根华入口块理论归属沿用 WO-T2a D1；本单不作新颖性或实现序数宣传。测试与证书是针对这一个有限多边形的核验，不是机械轨迹等价、工程验证或任意输入域的自动证明。
- 生产核验器、引理、定理稿、独立侧文件、既有数学合同、三个静态分析器和 policy 均不改。内部多代理实现复核不是 Claude 安排的独立对抗验收；新鲜树与最终所有者接收不由本代理自签。

## 2. 定理到具名门的对应

令 `c=(0,1)`、`h=h_K(1,1/2)`。方形 `h=3/2`，有理八边形 `h=29/24`：

```text
δ° = (4−√5)/(4h)
δ*_T = 1/(2h)
δ*_SE2 / δ*_T = 2−√5/2
```

“不取到”指困住侧的上确界不属于困住集合：`δ<δ°` 困住，`δ=δ°` 已能在允许接触的约定下逃逸。

实现为 [标准库 Q(√5) 辅助模块](file:///D:/eab-wt/cx-e2/tests/t2c2_knob_exact.py)及 [31 个定理测试](file:///D:/eab-wt/cx-e2/tests/test_t2c2_knob_theorem.py)。系数为 Fraction，符号只比较有理平方，拒绝浮点转换；除法使用共轭与有理范数。主 oracle 是手写支撑、水平截面及仿射分区，不调用生产腐蚀、SE(2) 路径或两侧笼核验器。

下表测试名均位于上述定理测试文件；反向门修改辅助模型内部的常数、顶点或阈值函数，并匹配目标数学断言，非修改已产出的真假结果。

|义务|精确结果|正向门|具名反向门后缀/变异|
|---|---|---|---|
|Q(√5) 四则、符号|共轭、乘除逆、异号平方比较；零除与非精确输入拒收|`test_q5_exact_field_arithmetic_sign_and_order`、`test_q5_rejects_nonexact_inputs_zero_division_and_float_conversion`|拒收门不将浮点转为 Fraction 后悄悄接收|
|A：g(0)>0|`lemma_a_metrics(element,0)` 实算平方余量恰为1，正残量为3|`test_lemma_a_zero_critical_slack_and_exact_main_chord`|`test_lemma_a_zero_rejects_internal_secondary_bound_mutation`：3→2及11/4|
|A：g(δ°)>0|先核正残量，再核残量²−10r²>0；方形为 −1/6+4√5/9，八边形为 95/3364+205√5/841|同上|`test_lemma_a_critical_slack_rejects_internal_bound_mutation`：3→5/2|
|A：主弦取等|r(δ°)=1/2，四侧支撑一致；已删对所有δ成立的半径定义恒等式|同上|`test_lemma_a_main_rejects_internal_support_mutation`：h+1/1000；`test_lemma_a_equality_rejects_internal_critical_delta_shift`：δ°+2^-20|
|符号腐蚀完整性|方形11点、八边形9点；凹角截线已纳入|`test_symbolic_erosion_exact_section_partition_and_rational_affine_crosscheck`|`test_symbolic_erosion_rejects_old_octagon_top_intercept_inside_model`：1/3→旧错误1/2|
|C：最远顶点与圆包含|两种最远点均为两个颈顶角；ρ²见 §3，均<4/5|`test_lemma_c_exact_farthest_vertices_and_all_eight_edge_distances`|`test_lemma_c_radius_rejects_internal_disk_bound_mutation`：4/5→2/5|
|C：Q 的8边距离平方|4边为4/5，4边为9/10|同上|`test_lemma_c_edge_distance_rejects_internal_q_vertex_mutation`：一个底点坐标+1/1000|
|D：11顶点条带|全部满足绝对值 abs(x+(y−1)/2)≤1，且两侧取等|`test_lemma_d_all_eleven_strip_projections`|`test_lemma_d_rejects_one_internal_vertex_coordinate_mutation`：最宽顶点x+1/1000|
|E：转后竖直范围|两种实际极值均在定理共同包络内|`test_lemma_e_vertical_extrema_and_piecewise_cavity_width`|`test_lemma_e_vertical_rejects_internal_rotation_number_mutation`：cos分子2→3|
|E：墙/地板条带|半宽各折点≥1/2，墙顶2、地板顶0；真实障碍与手写定义一致|同上|`test_lemma_e_strip_rejects_internal_neck_width_mutation`；`test_lemma_e_strip_rejects_internal_floor_top_mutation`|
|§3.1 平移阈值|方形1/3、八边形12/29；阈值及两侧横截面宽度精确核验|`test_translation_threshold_and_universal_relative_reduction`|`test_translation_threshold_rejects_internal_threshold_shift`：阈值+2^-20|
|δ° 精确逃逸|精确转动、水平投影等号、整个上移半射线条带|`test_exact_critical_escape_disk_turn_closed_strip_and_infinite_lift`|`test_exact_horizontal_projection_rejects_internal_rotation_mutation`；`test_exact_escape_rejects_internal_rotation_mutation_not_fake_output`|
|T2c1 兼容|两旧括号严格夹住定理值|`test_t2c1_knob_brackets_strictly_straddle_theorem_value`|不是把旧数值括号当新定理证明|

符号腐蚀不是由三个生产样本拟合推断：独立截面 oracle 枚举 K 纵向顶点及腔体折点穿越，分区内每个候选均为仿射函数。端点保证所有候选不低于声明边界，中点取等迫使某个候选在整格取等，故整格最小值等于声明边界。最低点以下由全局下锥排除，最高点以上由顶界排除。生产 `erode_polygon_exact` 在方形 `[29/100,3/10]`、八边形 `[9/25,37/100]` 的两端及中点仅作当前仿射分支的佐证，不据此声称生产函数对所有 δ 仿射。

## 3. δ° 处的精确逃逸

[完整 Q(√5) 顶点、转后顶点及指标](file:///D:/eab-evidence/reports/codex/T2c2_evidence/exact/exact_summary.json)保留每个数的有理系数；不调用 `se2_paths`。

|K|δ°|ρ²（精确最大值）|转后实际竖直范围|
|---|---|---|---|
|方形|(4−√5)/6|5/12+√5/18|[1/2−√5/25, 3/2+√5/10]|
|八边形|6(4−√5)/29|8509/30276+175√5/2523|[(69−3√5)/145, 3/2+√5/15]|

两种的实际竖直极值**不同**；定理 E 的“相同”是共同包络，非两种实际极值相同。

1. 精确核 `ρ²<4/5`、Q 的各边距及 `Q⊆A`。整个刚体在以 c 为心的严格内圆内，绕 c 的全部转动均不进入墙/地板内部。
2. 取 `cos=2/√5, sin=−1/√5`，从 `rotate_minus_phi` 对 c 及两个基向量的实际输出提取矩阵，核 `RᵀR=I`、`det R=1`，不只检查未必实际使用的两个常数；两个腐蚀环的水平投影均**恰为** `[-1/2,1/2]`，不是近似小于颈宽。
3. 转后最低点严格高于 `1/6`；闭条带 `[-1/2,1/2]×[1/6,∞)` 内无墙或地板内部。所有非负竖直位移保留这个条带，故整段上移及无限尾自由。边界接触允许。

## 4. 有限证书：有理接口差异不隐藏

现有生产与独立接口只接收 int/Fraction/有理字符串，不能原样接收 `δ°±2^-k` 的 Q(√5) 坐标。未改核验器，也未把近似值冒充目标值。

取 `D=2^48`、`s0=floor(√(5D²))/D`、`s1=s0+1/D`，由整数平方严格证明 `s0<√5<s1`。设

```text
d_lo=(4−s1)/(4h) < δ° < d_hi=(4−s0)/(4h)
cage verified_delta = d_hi−2^-k > target_delta = δ°−2^-k
escape verified_delta = d_lo+2^-k < target_delta = δ°+2^-k
```

笼直接核验更小的移动体，困住性转移到更大的目标；逃逸直接核验更大的移动体，路径转移到更小的目标。墙保持不变。每份元数据分列目标 `(a,b)`、实际代理、严格方向、整数夹逼证据及 `direct_algebraic_instance_verification=false`。这一**代理双核验＋精确包含转移**交付口径已获**所有者 2026-10-26 确认**。旧 JSON 的历史待定状态不改写，由 §9 出处附录注明后续裁定。

[正式52份清单与逐文件SHA](file:///D:/eab-evidence/reports/codex/T2c2_evidence/certificates/run_01/manifest.json) · [全部52行证书表](file:///D:/eab-evidence/reports/codex/T2c2_evidence/certificates_audit_01/README.md) · [完整状态/计数/时刻对拍](file:///D:/eab-evidence/reports/codex/T2c2_evidence/certificates_audit_01/summary.json)。正式运行207.08秒；pilot仅估时，不拼接入正式数据。

|K|笼目标|笼数|D边数，按k=6…12|逃逸目标|逃逸数|结果|
|---|---|---:|---|---|---:|---|
|方形|δ°−2^-k，k=6…12|7|16,32,32,64,64,128,128|δ°+2^-k，k=6…24|19|所有代理双接受|
|八边形|δ°−2^-k，k=6…12|7|16,32,32,64,64,128,128|δ°+2^-k，k=6…24|19|所有代理双接受|

- 每个笼均为**只含不变圆片**的两个角区间闭链，无 caps、无转动收缩片。D 的有理圆周点及逐边距离平方由生成器 `circle_polygon` 精确检查；**D 内切半径 > 1/2 由生成器保证，生产与独立通用核验器不检查这一特设颈宽条件**。核验器接受完整闭链证书；另由不变圆盘半径 `r>1/2` 与引理 B 给出定理几何理由，不混称。生产与独立各核280个屏障段，生产核280个连接四边形，独立总检查166941项。
- 笼生产走 JSON 文本入口，独立走 `load_json` 文本入口。14个代理处 T1b 均 `TRAPPED_TRANSLATION`；目标处另有包含转移与精确 `δ<δ*_T`。
- 每条逃逸只有绕 c 转到有理 Cayley 参数 `u=2−s0`、竖直上移4两个有限段，再接+y射线。生产有限刚体对228，独立含射线前缀有限对342；两者范围不同，不伪称计数应相等。
- 旧独立 oracle 的 `infinite_ray_verified=false` 原样保留。另用它独立构造的终点及精确竖直半平面证成全部38条无限尾；固定回放还核更强的“有限刚体段终点已经高于全部墙顶”。不把新补证改写为旧 oracle 自己核了无限尾。
- 38条同参数路径在相应下侧较小代理上均发生有限段碰撞，从而在更大的下侧目标上也碰撞；76个碰撞对的精确有理时刻、标签及状态一致。这只否决指定路径，不是以搜索失败证明所有路径失败。
- 90份数值输入审计共22978个Fraction、1022个整数、336个字符串，0浮点、0非有限数；时钟诊断不参与判定。源ZIP与commit/tool版本单列保存，不把现在的源码哈希当作数学回归条件。

## 5. 固定回放与一致性

[固定数据](file:///D:/eab-wt/cx-e2/tests/data/t2c2/index.json)选每种K的笼k=6/12、逃逸k=6/24，共8份gzip、44976字节；[回放门](file:///D:/eab-wt/cx-e2/tests/test_t2c2_replay.py)比较完整生产/独立返回，包括全部状态、计数、精确时间和标签，不只比较 valid。

- `test_t2c2_cage_replay_full_results_text_entry_and_translation` 实际观察独立 `load_json` 调用并重跑T1b。
- `test_t2c2_escape_replay_full_results_and_independent_unbounded_tail` 重跑两侧、保留旧有限scope，并独立核上方半平面无限尾。
- `test_t2c2_same_escape_motions_collide_on_paired_lower_instance` 先比较上下侧运动参数相同，再重放完整下侧碰撞结果。
- `test_t2c2_frozen_payload_integrity_and_exact_directed_transfer` 核历史数据SHA及目标/代理严格代数顺序；`test_t2c2_proxy_delta_labels_are_bound_to_exact_instance_geometry` 将δ标签绑定到独立符号移动体和手写墙，防止正确证书贴错实例标签。
- [52点一致性审计](file:///D:/eab-evidence/reports/codex/T2c2_evidence/replay_build/consistency.json)还核全部52份及38份lower的输入身份、目标和代理唯一性：同δ矛盾0，14平移困住，38下侧碰撞，38独立无限尾补证。此步复核冻结数据，不重算整轮证书。
- T2c1方形 `[301/1024,1209/4096]`、八边形 `[747/2048,375/1024]` 均严格夹住定理值；T1b阈值分别1/3、12/29。

新增全部定向门（含选定slow回放）[原始命令与完整日志](file:///D:/eab-evidence/reports/codex/T2c2_evidence/targeted_01/summary.json)末行：

```text
59 passed in 26.33s
```

## 6. 静态门、P1与成本

本单新增准入清单 **`[]`**，证明缺口准入0、浮点汇点准入0；policy原CRLF字节不变。三个分析器一字不改。[五个静态门](file:///D:/eab-wt/cx-e2/tests/test_t2c2_static.py)含实际辅助源内部浮点植入、内部policy解析器植入、源局部扫描和只读分析器字节核对；这些字节门不代替数学语义门。

`tools/` 为不可信提议层、可用浮点的范围沿用T2c1所有者验收补记；不重开已裁定的tools整文件静态缺口。[局部静态与路径预算](file:///D:/eab-evidence/reports/codex/T2c2_evidence/static/README.md)、[内部数学复核](file:///D:/eab-evidence/reports/codex/T2c2_evidence/static/mathematical_review.md)不是所有者独立验收。

P1的e=1、segments=8/16括号未开展，不因此计PARTIAL。原路径预查确实发现旧38字符复制前缀不满足预算；本次按验收返修第9项，在三个既有复制测试中仅把自动长测试名目录改为短 `tmp_path_factory.mktemp` 名称，测试体及复制范围不变。新增[快档路径守卫](file:///D:/eab-wt/cx-e2/tests/test_t2c2_paths.py)从实际 AST 取复制前缀，枚举真实复制范围 `src/tests/tools` 中所有文件，保持150字符basetemp及额外30字符缓存余量；最长相对路径64，三个预算为256、255、250，均严格<260。门内另注入过长前缀/文件名并要求报红，没有降低150基准或省掉缓存余量。

## 7. 开工全档与收尾快档/全档

pytest统一禁cacheprovider、显式basetemp，TEMP/TMP位于本单外置tmp，`PYTHONDONTWRITEBYTECODE=1`。[外置H1包装](file:///D:/eab-evidence/reports/codex/T2c2_evidence/run_gates.py)只调整证据根和已知过短的快档墙钟预算：1800→7200秒；全档10800秒、900秒停滞守卫、固定四分片及实际执行审计保留。没有把延长上限说成达到日常5分钟成本目标。

<!-- T2C2_GATE_RESULTS_BEGIN -->
开工全档 `t2c2_baseline_20261026`：16491项，四片原样末行：

```text
4123 passed in 1673.54s (0:27:53)
4123 passed in 2219.99s (0:36:59)
4123 passed in 1460.67s (0:24:20)
4122 passed in 1831.60s (0:30:31)
exact construction AST gate: 0 violation(s)
```

收尾快档 `t2c2_final_fast_20261026`：10428项，原样末行：

```text
10428 passed in 1747.95s (0:29:07)
```

收尾全档 `t2c2_final_full_20261026`：16550项，包含快慢全部节点，固定四片原样末行：

```text
4138 passed in 2087.05s (0:34:47)
4138 passed in 2468.41s (0:41:08)
4137 passed in 1692.56s (0:28:12)
4137 passed in 2395.52s (0:39:55)
exact construction AST gate: 0 violation(s)
```

[基线摘要](file:///D:/eab-evidence/reports/codex/T2c2_evidence/t2c2_baseline_20261026/summary.json) · [收尾快档摘要](file:///D:/eab-evidence/reports/codex/T2c2_evidence/t2c2_final_fast_20261026/summary.json) · [收尾全档摘要](file:///D:/eab-evidence/reports/codex/T2c2_evidence/t2c2_final_full_20261026/summary.json)。三轮均GREEN、0failed、0skip，收集/分派/插件收集/实际call节点多重集合相同，70个src/eab模块均实际执行。快档执行53个新增节点，全档执行59个新增节点。

原交付两轮收尾源清单2711成员完全相同；当时源快照与运行中的工作树均无漂移，报告及归档条目在两轮完成后回填。[双轮独立机械审计](file:///D:/eab-evidence/reports/codex/T2c2_evidence/delivery_final_01/gate_pair_audit.json)与[受测源码ZIP](file:///D:/eab-evidence/reports/codex/T2c2_evidence/t2c2_final_full_20261026/tested_source.zip)保存成员核对及SHA；这些是1488914交付的历史运行，不冒充此次返修后的受测源码。基线、快档、全档总墙钟分别2410.895、1764.922、2683.659秒；串行调度，未叠加多轮全仓运行，不声称达到日常约5分钟目标。
<!-- T2C2_GATE_RESULTS_END -->

完成的新run输出先保存原字节ZIP，再仅作UTF-8/LF展示规范化；映射保留原SHA及LF SHA，不改变状态、计数、源码快照或证书输入，不拼接中断运行。

## 8. 交付、回退与遗留

原交付机器证据入口见 [正式证书目录](file:///D:/eab-evidence/reports/codex/T2c2_evidence/certificates/run_01/)；[当时仓内改动SHA](file:///D:/eab-evidence/reports/codex/T2c2_evidence/delivery_final_01/repository_manifest.json)、[当时净增/只读/编码审计](file:///D:/eab-evidence/reports/codex/T2c2_evidence/delivery_final_01/delivery_audit.json)、[原外置成果SHA清单](file:///D:/eab-evidence/reports/codex/T2c2_evidence/delivery_final_01/artifact_manifest.json)、[历史逐项需求表](file:///D:/eab-evidence/reports/codex/T2c2_evidence/requirements.json)。原交付新增15个仓内文件、既有文件只追加归档登记；其中待定状态由本次附录取代，原JSON不改。此次返修的改动与累计净增另见§9，仍须严格小于3MB、每个新文件小于1MB；大型证据只在指定外置目录。

重跑科学证据或全仓门须使用新目录/run名，不覆盖本次冻结数据：

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONIOENCODING='utf-8'
$env:TEMP=$env:TMP='D:/eab-evidence/reports/codex/T2c2_evidence/tmp'
$stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
python -X utf8 tools/t2c2_certificates.py --output "D:/eab-evidence/reports/codex/T2c2_evidence/certificates/recheck_$stamp"
python -X utf8 D:/eab-evidence/reports/codex/T2c2_evidence/run_gates.py --name "t2c2_recheck_fast_$stamp"
python -X utf8 D:/eab-evidence/reports/codex/T2c2_evidence/run_gates.py --name "t2c2_recheck_full_$stamp" --runslow
```

“有理代理双核验＋精确包含转移”的原遗留已由所有者2026-10-26确认关闭，未扩大不可修改核验器的数域。所有者同时告知两路非作者核查通过；本代理不把自己的多代理审阅改称该独立验收。所有者的新鲜树全档正在另行执行，本轮按指令不重跑全档、不代签其结果。P1的e=1及细刻面预览未做，不作为PARTIAL原因；路径守卫已补。本地归档不是远程备份。

## 9. 验收返修（2026-10-26，基线1488914）

返修前2711文件干净字节锚见[快照清单](file:///D:/eab-evidence/reports/codex/T2c2_evidence/acceptance_repair_20261026/baseline_anchor/manifest.json)及[回退ZIP](file:///D:/eab-evidence/reports/codex/T2c2_evidence/acceptance_repair_20261026/baseline_anchor/source.zip)。本轮不commit，不改src、核验器、独立侧、定理稿、引理、三个静态分析器或policy；受测字节副本不是新鲜Git树。

### 9.1 精确检查与测试的牙

|验收项|返修后的具名门/证据|
|---|---|
|1：A/C/E及完整逃逸的直接正向检查|`test_lemma_a_zero_critical_slack_and_exact_main_chord` 直接调用 `verify_a_critical` 并比较两种精确平方余量；C门直接比较两种ρ²、两最远点及8边距；E门直接比较两种精确竖直范围与6折点宽度；完整逃逸门比较截面计数(8,15)/(12,23)、半径/最远点、水平及竖直投影。|
|组合调用不可悄悄脱开|`test_composite_proofs_execute_each_required_semantic_gate` 使用wraps运行真实检查并核调用，专门保护组合连线；它与直接精确值、几何负例分开，不把调用计数当数学证明。|
|2：截面分区完备|`test_symbolic_erosion_rejects_underreported_octagon_widest_pair_at_midpoint` 注入指定低报双点；`verify_section_partition` 枚举每个K高度事件，`test_symbolic_partition_rejects_one_missing_element_height_event` 删除一个非顶点事件后必须拒绝。|
|3：Q⊆A左右两侧|显式断言A、Q左链为已检查右链的镜像；`test_q_containment_rejects_outside_vertex_even_when_both_chains_mirror` 在两侧对称外移最宽点；另有仅左链破坏的负例。|
|4：实际转动矩阵|`test_rotate_minus_phi_actual_matrix_is_orthogonal_with_unit_determinant` 从函数实际输出构造两列并精确核单位长度、正交和det=1。|
|5：去掉恒等式、g(0)实算|删除半径定义的同义反复，保留临界半径=1/2；两K的 `lemma_a_metrics(element,0)` 实算余量=1。反例 `SECONDARY_BOUND=11/4` 的余量=−7/16，专门拒绝放宽一单位阈值。|
|6：非整数幂与Pell近零|额外AST审计拒绝所有指数非整数常量的 `**`（包括 `5 ** F(1,2)`、变量及bool）；带正负号整数字面量允许。算术门独立递推Pell整数，核n=14…32正反近零符号，不以浮点判符号。|
|7：Q5边角|新增 `__bool__`，断言 `Q5(1,1)!=Q5(1,0)`；12个左右比较方向均拒绝浮点。唯一故意生成的浮点是拒收边界输入，不进入Q5算术或几何判定，不新增浮点汇点准入。|
|9：路径预算|[预算记录](file:///D:/eab-evidence/reports/codex/T2c2_evidence/acceptance_repair_20261026/path_budget_01.json)保留实际前缀与最长文件；150+12+64+30=256<260，不用缩小basetemp造绿。|

### 9.2 出处附录，不改原清单

`manifest.source.source_commit=a0eb727` 只表示运行基线，实际运行来自**非干净工作树**；后续交付提交为 `148891476ce64f6731ec14d7d111a81f98667125`。原源ZIP的12个文件、总239008字节，与原源清单和该提交Git blob逐字节一致。这不是全部依赖闭包，也不是当时在干净提交上运行的声明。详见[出处附录](file:///D:/eab-evidence/reports/codex/T2c2_evidence/acceptance_repair_20261026/provenance/README.md)、[机器记录](file:///D:/eab-evidence/reports/codex/T2c2_evidence/acceptance_repair_20261026/provenance/provenance_addendum.json)及[可重跑脚本](file:///D:/eab-evidence/reports/codex/T2c2_evidence/acceptance_repair_20261026/provenance/audit_provenance.py)。

新附录的 `source_manifest_sha256` 唯一指原 `source_manifest.json` 的字节哈希，`certificate_manifest_sha256` 唯一指原 `manifest.json`，逐字段映射三个旧记录。旧证书审计中同名键实际指证书清单的歧义在附录明确更正；旧清单、旧JSON及其SHA不改。

```text
T2c2 provenance audit: 12/12 source files match delivery; 6 historical inputs unchanged; 3 hash-key mappings verified
```

### 9.3 50变异与收尾运行

正式 `mutation50_02` 从头完整执行两份核查方脚本的40+10项，653.0秒；**45项报红，5项为所有者允许的等价/冗余存活，0未施加、0收集/环境错误**。每项保留实际变异源、完整stdout/stderr、命令、返回码与源SHA；运行后2712文件副本恢复原字节。[完整结果](file:///D:/eab-evidence/reports/codex/T2c2_evidence/acceptance_repair_20261026/mutation50_02/summary.json)及[逐项分类](file:///D:/eab-evidence/reports/codex/T2c2_evidence/acceptance_repair_20261026/mutation50_02/classification.json)。

|存活项|理由与边界|
|---|---|
|M17|−φ变为+φ仍为刚体转动；本例左右镜像对称，另一方向同样给出等宽出口及相同极值。不是一般非对称物体的等价声明。|
|M21|只放宽函数内部水平投影断言；返回的实际极值没变，外层正向测试仍直接断言恰为±1/2。冗余守卫变弱，不表示容许3/5宽的逃逸。|
|M25|内部圆半径上界4/5放宽至1；返回的两种精确ρ²及外层ρ²<4/5仍直接核验，故对固定输入冗余。|
|M42|固定11顶点下锥界加9仍为真；仅是当前固定几何的较弱冗余断言，不声称对任意移动体等价。|
|M65|两种固定K的次弦支撑本来对称相等；改为≤h3+99不改变精确支撑、余量及逃逸结果，属于固定输入上的冗余放宽。|

49项保留原替换定义；唯一失效的旧字面量M28作[等价重键](file:///D:/eab-evidence/reports/codex/T2c2_evidence/acceptance_repair_20261026/mutation50_02/anchor_rekey.json)：`b²>8 → b²>7` 对应实算 `margin>0 → margin>−1`。新锚在g(0)及g(δ°)有两处，仍用原脚本的 `replace(...,1)`，实际变异落在g(0)；11/4反例将其杀死。没有把NOT_APPLIED算作杀死，也没有以源码哈希或语法错误当数学红灯。脚本仅另加日志、TEMP目录、LF及环境/收集错误整轮作废守卫，见[改编清单](file:///D:/eab-evidence/reports/codex/T2c2_evidence/acceptance_repair_20261026/mutation50_02/script_adaptations.json)和[守卫补记](file:///D:/eab-evidence/reports/codex/T2c2_evidence/acceptance_repair_20261026/mutation50_02/script_adaptations_addendum.json)。

M06同时由Pell n=14近零符号断言和新增AST幂门杀死；M18/M19由实际矩阵非正交杀死；M23/M27/M28由错误体/外点/负余量未被拒绝的具名反例杀死。M44/M53/M54/M55属于真实检查调用被删的**组合连线门**；M37属于目标竖直包络守卫被绕过、改由下游断言报错的**守卫身份门**，不夸称它产生被接受的假逃逸。其余逐项语义失败节点和断言见分类记录。

首轮 `mutation50_01` 因basetemp父目录缺失出现环境错误，已停止本代理启动的进程并[整轮作废](file:///D:/eab-evidence/reports/codex/T2c2_evidence/acceptance_repair_20261026/mutation50_01/state.json)；02从头重跑全部50，未拼接01结果。

本轮定向含慢测试与未改分析器的完整静态门，[命令、日志与摘要](file:///D:/eab-evidence/reports/codex/T2c2_evidence/acceptance_repair_20261026/targeted_01/summary.json)原样末行：

```text
67 passed in 34.19s
exact construction AST gate: 0 violation(s)
```

另外实际重跑三个改过临时目录的既有复制慢测，[完整日志](file:///D:/eab-evidence/reports/codex/T2c2_evidence/acceptance_repair_20261026/copy_tests_targeted_02.log)原样末行：

```text
3 passed in 786.98s (0:13:06)
```

新增准入清单仍为 **`[]`**，新增证明缺口准入0、浮点汇点准入0；原CRLF policy与三个分析器SHA不变。不是整个测试进程从不产生float的声明：拒收边界测试有一个故意的浮点样本，数学和证书判定不使用它。三个复制测试仅改临时目录创建，原lifecycle测试的整文件CRLF保持；其余本轮新/改源文档为UTF-8无BOM/LF。

收尾全仓快档新run `t2c2_acceptance_fast_01_20261026` 完整GREEN，[摘要](file:///D:/eab-evidence/reports/codex/T2c2_evidence/t2c2_acceptance_fast_01_20261026/summary.json)及[完整日志](file:///D:/eab-evidence/reports/codex/T2c2_evidence/t2c2_acceptance_fast_01_20261026/shard_1.txt)原样末行：

```text
10436 passed in 1953.99s (0:32:33)
```

10436个节点收集/分派/插件收集/实际call多重集合一致，0failed、0skip，70个src/eab模块实际执行；其中61个T2c2快档节点。运行器总墙钟1973.391699199914秒，不声称达到日常约5分钟目标。受测2712文件导出及运行时工作树均无漂移；本报告和归档登记仅在运行结束后回填，受测代码/数据未改。[受测源码ZIP](file:///D:/eab-evidence/reports/codex/T2c2_evidence/t2c2_acceptance_fast_01_20261026/tested_source.zip)按源清单逐成员核对。运行原字节ZIP与LF映射保留，不拼接结果。

### 9.4 最终交付与遗留边界

- [返修逐项闭合表](file:///D:/eab-evidence/reports/codex/T2c2_evidence/acceptance_repair_20261026/delivery/requirements.json)取代旧需求表的PENDING/PARTIAL状态；旧表不改写。
- [仓内文件SHA清单](file:///D:/eab-evidence/reports/codex/T2c2_evidence/acceptance_repair_20261026/delivery/repository_manifest.json)、[净增/只读/编码/受测源码审计](file:///D:/eab-evidence/reports/codex/T2c2_evidence/acceptance_repair_20261026/delivery/delivery_audit.json)、[外置逐文件H1归档清单](file:///D:/eab-evidence/reports/codex/T2c2_evidence/acceptance_repair_20261026/delivery/artifact_manifest.json)。返修只新增1个路径测试，修改9个既有测试/文档；累计本工单仓内净增仍<3MB，无删除。
- 569个旧外置成果逐件SHA保持不变；核查方输入原字节不改；原源清单和52份科学证书没有重跑或“刷新源码哈希”。三分析器与CRLF policy无变化、0新增准入，src/核验器/独立侧/定理/引理一字不改。
- 本轮不commit、不做任何Git写操作。所有者的新鲜树全档结果不由本代理代签；依指令未重跑全档。P1的e=1与细刻面预览未开展，不计PARTIAL；原路径遗留已关闭。没有尚未完成的本轮必修项。

T2C2_DONE
