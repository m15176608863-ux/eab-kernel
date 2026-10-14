# M4c 运动首入差异台账

## 1. 观测量、分母与闭集

这是事后端点弦运动审计，不是 DDA 连续圆弧运动、检测替换、动力学正确性或漏检物理危害判定。
定义与条件见 [理论设计](m4c_motion_entrance_design.md)。程序入口为
[m4c_motion_replay.py](../tools/m4c_motion_replay.py)。下面类别都是互斥的**每条 primary 参考三元组**类别；
raw-df05 / post-df06 分表，原有重复行不去重。VV 的第二参考三元组另有 `secondary_category` 和
`secondary_counts`，不把 VV 的点点身份吻合冒充两条参考边都吻合。

按块号排序后，A 为较小块号。运动 API 的 VE/EV 统一映射成
`("VE", 顶点全局号, min(边端全局号), max(边端全局号))`，VV 保存为排序后的两顶点号。
闭段 incidence 与法锥有效 cover 分开：边端点闭段相交不自动构成有效首盖。

| 类别 | 独立精确判据 |
|---|---|
| `FIRST_COVER_MATCH` | 初态实体分离；本步存在首接触；参考键属于完整有效首盖集合。 |
| `FIRST_INCIDENCE_NOT_COVER` | 初态分离；参考键属于首时刻闭段关联，但不满足该顶点局部法锥。 |
| `OTHER_FEATURE_FIRST` | 初态分离；本步存在首接触；该参考键不属于首时刻关联集合。 |
| `NO_CONTACT_IN_STEP` | 初态分离；全 [0,1] 窗口没有闭集接触。 |
| `INITIAL_TOUCH_COVER_MATCH` | 初态实体相触；参考键属于 s=0 有效盖。 |
| `INITIAL_TOUCH_INCIDENCE_NOT_COVER` | 初态相触；参考键仅属于 s=0 关联。 |
| `INITIAL_TOUCH_OTHER_FEATURE` | 初态相触；参考键不属于 s=0 关联。 |
| `INITIAL_OVERLAP_PD_MATCH` | 初态严格贯入；参考键属于冻结步初全局 PD_closed 全部并列最优出口点的有效盖并集。 |
| `INITIAL_OVERLAP_PD_OTHER_FEATURE` | 初态严格贯入；PD 已计算；参考键不在上述并集。 |
| `INITIAL_OVERLAP_PD_NOT_EVALUATED_RESOURCE` | 初态严格贯入；显式确定性资源上限阻止 PD 计算。不能进入 PD 一致/不一致分母。 |

整步域约束是保守拒答：首入之后才出现的环退化也会使整步报域外；域外不等于首入不存在，
不能混入 `NO_CONTACT_IN_STEP`。1810 步的逐块复核及步—块对数见 [域审计](../reports/codex/M4c_evidence/fix_domain_audit.json)：1810 步、15220 个步—块、64010 个步—无序块对，整步域外步—块对为 **0**；其中“首入后才退化”的保守拒答也为 **0**。

未知名字不是新豁免，一律 RED。分类顺序首先依据初态实体三态，再看首时刻/PD 集合。
`MATCH` 不是一个可任意回退到的总类别；任何合并必须改变冻结摘要且命中专门的内部变异门。
上述初态相触包括紧配内缝，不能据此宣称该点在 E 的真外边界。

## 2. 独立 Fraction 判据

初态由 `g0_oracle.overlap` 的整数公共分母提升、绕数、严格边横交和同向共线边判据获得；
生产运动模块使用另一套多边形重叠实现，分类 oracle 不 import 生产事件枚举、求根、法锥、三角剖分。

对线性顶点 p(s) 与线性边 [a(s), b(s)]，比较工具独立构造
`f(s)=cross(b-a,p-a)` 与 `g(s)=dot(p-a,p-b)` 的三个 Fraction 系数。
闭段关联当且仅当 `f(tau)=0` 且 `g(tau)<=0`。顶点前后边向量 u、v 的局部凸角检验为
`cross(u,v)>=0`，并要求 `cross(e,u)>=0, cross(v,e)>=0`；平角还要求
`dot(u,v)>0, dot(e,u)<0`。VV 要求两个坐标差均精确为零。
因此零端点、共线退化与并列集合不经过浮点容差。

二次时刻给定最小多项式 `t²+b t+c=0` 与根支，任意二次判据先独立约化到 `u+v t`，
再用有理平方与有符号根支判断正负。不是调用生产 `sign_polynomial` 再宣称独立。
每个返回接触时刻重新枚举所有关联及有效盖，逐集核对生产结果；没有只检返回盖、漏掉未返回并列项。
首时刻“没有更早事件”的完备性另由运动内核独立闭式/平移退化门看护；本台账不把事后成员检查称为完整独立求根 oracle。

PD 使用 [motion_exit.py](../src/eab/kernel2d/motion_exit.py) 的精确 cell 外侧覆盖算法，返回 M3 `Distance2`。
“真外边界”是完整 ∂E（含洞壁），不是只取最外连通分量；排除的是内部凸胞剖分缝。
每个 PD 最优点另由独立实体相触及局部外部扇区判据核对确为 E 真外边界；平方距离与所有最优点以有理字符串保存。
例行 CLI 默认资源 cap 可显式调节；批量全时程和冻结调用 `--pd-edge-limit 0`，即无预设工作量剪裁。

## 3. 三类不能混在一致率里的量

1. **漏检块对**：仅初态分离且在本步发生新接触，且 raw/post 两张表中该块对都不存在。
   扫掠 AABB 只用于证明不接触，不用 legacy 候选限制运动枚举。
   初态已有相触/贯入而两表缺席另计 `initial_contact_pairs_absent_both_tables`，不混进“本步新发生”的分母。
   末态深度字段是“顶点在对块内部的最大边界净空证人”（长度平方），既非全局 PD，也非步内最大穿透。
   没有严格内部顶点时标记 `squared=null, has_strict_vertex_witness=false`；十字横交可严格贯入但没有该证人，故不可写成深度零。
2. **平移替身**：每块以顶点平均位移平移；`delta_linf` 是两块最大残余 L∞ 位移之和，Fraction 精确。
   仅 delta=0 记 `CERTIFIED_IDENTICAL_TRAJECTORY`；非零统一 `UNCERTIFIED_NONTRANSLATION`，不能计认证一致或不一致。
   另保存两条轨迹都精确求解后的 `same_first_cover_set` / `same_time` 描述性结果。该比例只描述模型敏感性，不是替代可认证率。
3. **事前预测**：从第2步起只用上一段已发生的顶点位移作同量外推，和真实本步首盖对比。
   第1步缺前帧明确 unavailable；预测轨迹离开简单环域也单独 unavailable，不拿实际下一帧修补预测。
   不把上一段位移当步初速度，不把 hh 当 dt，不宣称 online 替换。

替身/预测描述性统计的条件分母仅是：初态分离，且任一 legacy 表记录过该块对，或**真实运动**扫掠 AABB 相交。
真实运动扫掠盒严格分离且两 legacy 表均无记录的远块对，只计“证明真实窗口无接触”，不求其替身/预测。
因此本报告**不是全体块对的预测漏报/误报率**；预测可能对被上述真实候选域排除的块对报接触，
这类 false positive 未统计。限定域统计不宣称具备在线预测检测器的全召回验收。

## 4. 输入、末帧与证据完整性

完整 source 的 N 个 snapshot 步初帧必须与同 run `geom.csv` 的 step0..step(N-1) 逐顶点精确同值，
且 step0=initial、stepN=final、顶点全集稳定，然后才允许 stepN 补末端。
因此 1810 个步初帧可以得到 1810 个运动区间，而不是静默丢掉15个末步。
冻结前30步用 [endpoints.json](../fixtures/m4c_motion/endpoints.json) 绑定各原快照哈希、步初几何哈希及第30步末端几何；
端点来源先经过完整源核对，不是把第30步初重复当作静止末帧。

少列、列错位、步号跳跃/回退、未知 attempt 字段、重复身份、终端缺失、末端错配均 fail-closed。
本单只认证已审计生产者无回退的现有路径；不声称可处理任意回退快照协议。
每步输出规范化记录并 flush，progress 保存当前完成步数及输入/运动回放本仓 import 闭包文件哈希（POSIX 路径键）。
只有 final audit `complete=true`、全输入/代码末态哈希不变的批次可作为完成证据；中断目录保留但不得拼接成结果。

## 5. 门与复跑

具名门见 [test_m4c_replay.py](../tests/test_m4c_replay.py)：
- `test_synthetic_two_time_surfaces_have_exact_first_cover_categories`；
- `test_classifier_match_folding_mutation_hits_its_own_guard`，内部分类并 MATCH 红在专用类别断言；
- `test_pairing_one_step_shift_mutation_hits_alignment_guard`，内部错一帧红在独立 endpoint 几何绑定；
- `test_malformed_snapshot_is_audit_red`，少列/错位/跳步/回退等；
- `test_truncated_gzip_cli_persists_red_and_preserves_source`，真实 gzip 截断 EOFError 也持久化 RED；
- `test_batch_child_failure_always_writes_red_incomplete_summary`，子进程失败、缺/坏 audit 不得使批次只留下无 summary 的异常；
- `test_translation_nonzero_residual_is_uncertified_not_mismatch`；
- `test_swept_contact_pair_is_detected_with_both_legacy_tables_empty`；
- `test_frozen_all_thirty_frames_are_hashed_classified_and_conservative`，全部450规范化帧哈希/类别守恒；
- `test_real_first_frame_per_family_recomputes_the_frozen_classification`，15例各1帧实际生产计算。
- `test_frozen_full_computation_is_bound_to_current_production_sources`，450帧完整重算证据绑定当前回放 import 闭包源哈希（23 文件，见 `REPLAY_SOURCE_FILES` 与新增 AST 闭包门）；
  生产源变化即红，必须显式重新执行全450帧审计，不允许旧结果加几帧采样冒充新代码已全量通过。

为控制常规全套增量，pytest **不是重新计算全部450帧**。450帧完整重算是显式证据脚本：

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:TEMP=(Resolve-Path reports/codex/M4c_evidence/tmp).Path
$env:TMP=$env:TEMP
python -X utf8 tools/m4c_run_replays.py freeze-endpoints
python -X utf8 tools/m4c_run_replays.py frozen --out reports/codex/M4c_evidence/frozen_replay_rerun --jobs 4
python -X utf8 tools/m4c_run_replays.py full --out reports/codex/M4c_evidence/full_replay_rerun --jobs 4
```

批量入口还核对计数的类型（非 bool、非负整数）、闭集类别、有限非负耗时、输入/代码/规范化记录哈希，
再逐帧重算 primary/secondary 行数守恒和汇总；不允许字符串计数被 `Counter` 当作可累加的合法值。
完成批次的只读复验命令如下；输出必须是新文件，原始 summary 不覆写，不把不同中断批次的子例拼接：

```powershell
python -X utf8 tools/m4c_run_replays.py verify-batch --batch reports/codex/M4c_evidence/fix_frozen_replay --out reports/codex/M4c_evidence/fix_frozen_revalidation_rerun.json
```

旧 `full_replay_r4` / `frozen_replay_r2` 的复验 JSON 是原源码绑定下的历史证据；当前 23 文件绑定会拒绝其旧 46 文件哈希映射，不能直接用当前 CLI 冒称重审通过。
现行冻结为 `fix_frozen_replay`；本单 1810 步域审计和 VV 新旧规则逐行差分不冒充完整 PD 重跑。

必须使用新输出目录；不能覆盖已有证据。批次计数、每例摘要、各类最小复现端点与耗时以
[M4c报告](../reports/codex/M4c_report.md) 指向的最终 complete 批次为准；本台账不把未完成的 pilot 计数当结果。
