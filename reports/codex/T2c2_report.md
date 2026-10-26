# WO-T2c2：8 弦凸耳刚体临界公差的精确核验与证书佐证

**一句话：对本单指定的 8 弦凸耳、墙不腐蚀和两种容差元，精确核验支持所有者定理——允许转动后临界公差恰好下降 √5/2−1，约 11.8%；方形与八边形的相对降幅相同。**

当前交付状态为 **PARTIAL，仅差验收口径确认**：有限证书采用“有向有理代理双核验＋精确包含转移”，不是不可修改的原核验器直接接收无理实例；已向所有者询问这一口径，尚待确认。收尾快档10428项、全档16550项及静态门已全绿。未发现定理反例，未修改定理稿。

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

实现为 [标准库 Q(√5) 辅助模块](file:///D:/eab-wt/cx-e2/tests/t2c2_knob_exact.py)及 [24 个定理测试](file:///D:/eab-wt/cx-e2/tests/test_t2c2_knob_theorem.py)。系数为 Fraction，符号只比较有理平方，拒绝浮点转换；除法使用共轭与有理范数。主 oracle 是手写支撑、水平截面及仿射分区，不调用生产腐蚀、SE(2) 路径或两侧笼核验器。

下表测试名均位于上述定理测试文件；反向门修改辅助模型内部的常数、顶点或阈值函数，并匹配目标数学断言，非修改已产出的真假结果。

|义务|精确结果|正向门|具名反向门后缀/变异|
|---|---|---|---|
|Q(√5) 四则、符号|共轭、乘除逆、异号平方比较；零除与非精确输入拒收|`test_q5_exact_field_arithmetic_sign_and_order`、`test_q5_rejects_nonexact_inputs_zero_division_and_float_conversion`|拒收门不将浮点转为 Fraction 后悄悄接收|
|A：g(0)>0|3²>8，且3>0|`test_lemma_a_zero_critical_slack_and_exact_main_chord`|`test_lemma_a_zero_rejects_internal_secondary_bound_mutation`：3→2|
|A：g(δ°)>0|先核正残量，再核残量²−10r²>0；方形为 −1/6+4√5/9，八边形为 95/3364+205√5/841|同上|`test_lemma_a_critical_slack_rejects_internal_bound_mutation`：3→5/2|
|A：主弦取等|r(δ°)=1/2，r√5/2+δ°h=1，四侧支撑一致|同上|`test_lemma_a_main_rejects_internal_support_mutation`：h+1/1000；`test_lemma_a_equality_rejects_internal_critical_delta_shift`：δ°+2^-20|
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
2. 取 `cos=2/√5, sin=−1/√5`，核 `cos²+sin²=1`；两个腐蚀环的水平投影均**恰为** `[-1/2,1/2]`，不是近似小于颈宽。
3. 转后最低点严格高于 `1/6`；闭条带 `[-1/2,1/2]×[1/6,∞)` 内无墙或地板内部。所有非负竖直位移保留这个条带，故整段上移及无限尾自由。边界接触允许。

## 4. 有限证书：有理接口差异不隐藏

现有生产与独立接口只接收 int/Fraction/有理字符串，不能原样接收 `δ°±2^-k` 的 Q(√5) 坐标。未改核验器，也未把近似值冒充目标值。

取 `D=2^48`、`s0=floor(√(5D²))/D`、`s1=s0+1/D`，由整数平方严格证明 `s0<√5<s1`。设

```text
d_lo=(4−s1)/(4h) < δ° < d_hi=(4−s0)/(4h)
cage verified_delta = d_hi−2^-k > target_delta = δ°−2^-k
escape verified_delta = d_lo+2^-k < target_delta = δ°+2^-k
```

笼直接核验更小的移动体，困住性转移到更大的目标；逃逸直接核验更大的移动体，路径转移到更小的目标。墙保持不变。每份元数据分列目标 `(a,b)`、实际代理、严格方向、整数夹逼证据及 `direct_algebraic_instance_verification=false`。这是**代理双核验＋精确包含转移**，仍待所有者确认可作为本单原字面义务的交付口径。

[正式52份清单与逐文件SHA](file:///D:/eab-evidence/reports/codex/T2c2_evidence/certificates/run_01/manifest.json) · [全部52行证书表](file:///D:/eab-evidence/reports/codex/T2c2_evidence/certificates_audit_01/README.md) · [完整状态/计数/时刻对拍](file:///D:/eab-evidence/reports/codex/T2c2_evidence/certificates_audit_01/summary.json)。正式运行207.08秒；pilot仅估时，不拼接入正式数据。

|K|笼目标|笼数|D边数，按k=6…12|逃逸目标|逃逸数|结果|
|---|---|---:|---|---|---:|---|
|方形|δ°−2^-k，k=6…12|7|16,32,32,64,64,128,128|δ°+2^-k，k=6…24|19|所有代理双接受|
|八边形|δ°−2^-k，k=6…12|7|16,32,32,64,64,128,128|δ°+2^-k，k=6…24|19|所有代理双接受|

- 每个笼均为**只含不变圆片**的两个角区间闭链，无 caps、无转动收缩片。D 的点为有理圆周点，外半径及每边到原点距离平方精确核验，内切半径严格大于1/2。生产与独立各核280个屏障段，生产核280个连接四边形，独立总检查166941项。
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

P1的e=1、segments=8/16括号未开展，不因此计PARTIAL。路径守卫只做了只读预查：在现有复制前缀38下，150字符basetemp＋最长实际Python312缓存相对路径72=260，已经不能满足严格<260；按约30字符缓存余量计为265。未擅改只读复制测试或偷偷缩小基准路径使其假绿，也未新增必失败快档门。此项留给所有者安排缩名/支持预算裁定。

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

两轮收尾源清单2711成员完全相同；全程源快照与运行中的工作树均无漂移。报告及归档条目仅在两轮完成后回填，最终受测代码与当前代码逐字节一致。[双轮独立机械审计](file:///D:/eab-evidence/reports/codex/T2c2_evidence/delivery_final_01/gate_pair_audit.json)与[受测源码ZIP](file:///D:/eab-evidence/reports/codex/T2c2_evidence/t2c2_final_full_20261026/tested_source.zip)保存成员核对及SHA。基线、快档、全档总墙钟分别2410.895、1764.922、2683.659秒；串行调度，未叠加多轮全仓运行，不声称达到日常约5分钟目标。
<!-- T2C2_GATE_RESULTS_END -->

完成的新run输出先保存原字节ZIP，再仅作UTF-8/LF展示规范化；映射保留原SHA及LF SHA，不改变状态、计数、源码快照或证书输入，不拼接中断运行。

## 8. 交付、回退与遗留

机器证据入口见 [正式证书目录](file:///D:/eab-evidence/reports/codex/T2c2_evidence/certificates/run_01/)；[仓内改动SHA](file:///D:/eab-evidence/reports/codex/T2c2_evidence/delivery_final_01/repository_manifest.json)、[净增/只读/编码审计](file:///D:/eab-evidence/reports/codex/T2c2_evidence/delivery_final_01/delivery_audit.json)、[全部外置成果SHA清单](file:///D:/eab-evidence/reports/codex/T2c2_evidence/delivery_final_01/artifact_manifest.json)、[逐项需求交付表](file:///D:/eab-evidence/reports/codex/T2c2_evidence/requirements.json)。只新增15个仓内文件，既有文件只追加归档登记；净增严格小于3MB、每个新文件小于1MB。所有新交付的源/文档均UTF-8无BOM/LF，保留只读policy原CRLF；大型证据在指定外置目录，不写仓库根。

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

遗留仅为本单“有理代理双核验＋精确包含转移”替代直接无理实例双核验的所有者口径确认；未擅自扩大不可修改核验器的数域。所有者安排的新鲜树和独立对抗验收亦不由本代理自签。P1未做不作为PARTIAL原因。本地归档不是远程备份。

T2C2_PARTIAL：现有核验器只接收有理实例，已交付有向有理代理双核验与精确包含转移；该替代口径待所有者确认。
