# M4c 汇总与最小复现审查

日期：2026-10-14。范围是 `tools/m4c_summarize_evidence.py` 的分母、案例选择和源文件绑定，不重新审查几何内核，也不把它称为全仓 G6。

## 1. 审查角色和当前结论

初始只读独立审查发现三项汇总风险；主执行者随后明确授权本审查者对汇总脚本及其测试作最小修补。因此应称为**独立发现 + 授权修复 + 独立算术/后验复数复核**，不能把修补后的汇总脚本说成仍由“从未参与实现者”独立退出验收。

代码层面已关闭 1 项 major、2 项 minor；9 个专门测试全部通过，原始输出为 `9 passed in 0.11s`，墙钟 0.700 秒，0 skip。测试 scaffold 的文件写入已留在测试函数、纯文本 helper 不再兼任数值返回和外部效应；`scan_text` 0 违例，豁免增量 0。最终 full_r4 的 **15 例 1810 行已用独立标准库脚本完整复数通过**，35 个最小例的角色/双源绑定/前帧可用性均过；耗时 1.406 秒，证据见 §6。此复数不重新证明几何算法。

## 2. 发现、修复与有牙门

| 编号 | 原风险 | 级别 | 修复与门 |
|---|---|---|---|
| SUM-01 | 只核 shadow hash，未核 geom.csv 的审计 terminal_source hash；同步改 stepN/final 能通过几何前缀校验，但最小例末端已脱离原 replay。 | major | `bound_terminal_geometry` 在读取前后及每例汇总结束绑定 terminal_source；真实 CSV 篡改门和内部去掉绑定的变异门均命中预期断言。 |
| SUM-02 | `other_first_given_contact` 将 OTHER_FEATURE_FIRST 与 FIRST_INCIDENCE_NOT_COVER 混成“另一特征先接触”，可能把首时刻已有 incidence 误表述为时间上更早的别边。 | minor | 拆成 `other_feature_first_given_contact`、`first_incidence_not_cover_given_contact`；总非首盖率另名 `nonfirst_cover_given_contact`。内部合并变异红在 `incidence is not an earlier other feature`。 |
| SUM-03 | VV secondary 有独立计数却没有对应类别最小例。 | minor | 增加 `phase:secondary:category` 键与 `reference_role`，完整 legacy 行继续保留双参考；内部丢 secondary 分支变异红在专用例身份断言。 |

测试：[test_m4c_summary.py](../../../tests/test_m4c_summary.py)。原始测试证据：[运行元数据](review_probes/summary_test_run.json)、[stdout](review_probes/summary_test_stdout.txt)。这些变异进入被测函数内部，不是向输出追加假行。

## 3. 分母复核

设初态分离参考行中 M=FIRST_COVER_MATCH，O=OTHER_FEATURE_FIRST，I=FIRST_INCIDENCE_NOT_COVER，N=NO_CONTACT_IN_STEP。

- 有实际首接触条件的分母是 M+O+I；M、O、I 分别报告，N **不**属于“另一特征更早”。
- 全部分离参考行分母是 M+O+I+N；另列 N 的比例，不将 N 静默排出全部分离行一致率。
- 初态相触的三类不入上述分母；PD 只以已实际求值的 `PD_MATCH + PD_OTHER_FEATURE` 为分母，资源未求值项不入分母。
- raw-df05 / post-df06 分开；primary / VV secondary 分开。`all_reference_rows` 在 secondary 桶内指 secondary 参考三元组数，不是另一份完整 legacy 行总数，更不能与 primary 相加冒充行一致率。
- 手工构造 M/O/I/N=2/3/5/7 的测试直接期望 1/5、3/10、1/2、7/17、2/17 等 Fraction 字符串；预期值不调用生产分类。未知类别、负数和 bool 计数一律红。

## 4. 漏检、深度、替身与证书

只读核查 replay 的生成路径：`missing_both_legacy_tables` 位于 `initial_state == -1` 分支，且 actual 为 contact、两张表均无块对；初态已有接触但缺席两表另记字段，不混为新发生漏检。汇总保存该限定集合。

`depth_witness` 的 observable 为 `largest_vertex_interior_clearance_at_step_end_not_global_PD`：末态严格内部顶点到对块边界的净空证人最大值，存长度平方；不是 PD_closed、不是步内峰值贯入。没有严格内部顶点时 squared=null；不能将 null 当深度零，也不能将长度平方直接标成长度。

替身描述性 `same_first_cover_set` 同时比较 status 与 features：两条 no_contact 路径可计描述性相同；一条 no_contact、一条 contact 必不同，即使误只看空集会相等也不能通过状态条件。输出分别报告：全部已评估候选分母、真实运动有接触条件分母、任一轨迹有接触条件分母。

这些候选只含初态分离且 legacy 有记录或**真实运动**扫掠 AABB 相交的块对；不声称遍历所有远块对的替身假阳性。证书 `delta=0` 的 CERTIFIED_IDENTICAL 与非零 delta 的 UNCERTIFIED 单独计数；精确算出两条轨迹相同并不能把后者升级为认证相同。最终后验复数脚本将逐行重新检查这些条件，不复用汇总函数。

## 5. 最小复现的准确含义

选择顺序为 `(两块总顶点数, case, step, blockA, blockB)`；这里“最小”指**现有已审计记录中按上述 rank 选出的例子**，不是经过顶点删减/参数约分搜索证明的全局最小反例。

每例保存原始 A0/A1/B0/B1、输入顶点号、完整 pair 结果与 legacy 行、primary/secondary 角色、shadow SHA256、terminal_source SHA256。按主执行者要求另存 A_previous/B_previous：首步为 null，其余来自严格前一帧，便于复算预测，不能用实际下一帧冒充先验。主执行者另提供几何 API 复算工具，本审查不将只看 JSON 的守恒检查称为几何复算。

## 6. 可重复的最终数据复数

[check_summary_artifacts.py](review_probes/check_summary_artifacts.py) 仅导入标准库，不 import replay/汇总函数，逐 normalized 行重数：

1. raw/post primary 与 secondary、每行与批次计数守恒；
2. 初始分离、实际首接触、两表缺席的漏检充要条件和深度字段口径；
3. 真实/替身 status+features、time、delta 证书，三种描述性分母；
4. 四问 JSON 的精确分子/分母；
5. 最小例角色、前帧可用性与双输入源哈希绑定。

运行形式：

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -X utf8 reports/codex/M4c_evidence/review_probes/check_summary_artifacts.py --full reports/codex/M4c_evidence/full_replay_r4 --summary <最终汇总目录> --out reports/codex/M4c_evidence/review_probes/summary_artifacts.json
```

最终运行已使用 full_r4 和持久化汇总根目录完成：[summary_artifacts.json](review_probes/summary_artifacts.json)，退出码 0、`complete=true`、1810 步、15 例、35 例子；所有 primary/secondary 计数、精确分子/分母与双源绑定检查均通过。对应 frozen 是整批重跑完成的 frozen_replay_r2（450 步），不是发布包装失败的旧冻结批次；本次独立逐 normalized 行复数的范围为 full_r4，冻结全量由其独立 batch revalidation/冻结门负责。

### 6.1 参考行与块对不能混用

实际新接触是 **68 个块对**，但两表各有 **173 条初态分离且实际发生接触的 primary 参考行**。独立复数得到：

| 量（分母都是 68 个新接触块对） | raw-df05 | post-df06 |
|---|---:|---:|
| 至少一条 primary 是首盖 | 38 | 57 |
| primary 或 VV secondary 至少一条是首盖 | 47 | 66 |
| 没有任何 primary/secondary 首盖 | 21 | 2 |
| 已有任一首盖、但另有非首盖 primary 行 | 45 | 64 |

所以 133/173、114/173 的 **primary 行非首盖率**不能写成块对的“选边错误率”。post 有 64 个块对已经记录某条首盖但仍保留额外非首盖行；必须保留这是多行/多参考候选记录的解释边界。

按 `(case,step,pair)` 词典序，无任何首盖行的最小身份是 raw：`bb03 / step15 / [2,6]`；post：`bb51 / step2 / [3,9]`。68 个块对的逐相位明细全部在上述 JSON 中。该身份最小序不声称几何最小化。

### 6.2 其他直接复核数

- 新接触漏检块对：0；因此本批没有漏检深度样本，不能据此报“深度为 0”。
- 替身描述性不同：790/17603；真实运动发生接触条件下为20/68；任一轨迹发生接触条件下为790/838。三种分母不同，不得互换。
- 17603 个被评估初态分离候选的非平移残差均非零，故全部 UNCERTIFIED，认证相同为0；描述性相同16813不能改写为16813个认证相同。
- 主执行者另提供的 [minimal_examples_reproduced.json](minimal_examples_reproduced.json) 为35例的生产 API 复算 GREEN；本审查已读其 complete/audit/source hash，仍将它和本节的独立 JSON 复数明确区分。

### 6.3 “首入不同”还包括精确时刻：不能仅比较盖集合

另增独立标准库 [timing_sensitivity.py](review_probes/timing_sensitivity.py)，在完整1810行中直接比较保存的 canonical 有理/二次代数时刻 certificate，而非 `time_display`；17603 次 `same_time` 均与该直接比较一致。[最终结果](review_probes/timing_sensitivity.json) `complete=true`，耗时1.005秒。

| 条件分母 | status/盖集合不同 | 精确时刻不同 | status/盖/时刻任一不同 |
|---|---:|---:|---:|
| 全部17603个已评估候选 | 790/17603 | 838/17603（4.760552%） | 838/17603 |
| 68个真实运动有接触 | 20/68 | 68/68（100%） | 68/68 |
| 838个任一轨迹有接触 | 790/838 | 838/838（100%） | 838/838 |

**48个块对的 status/盖集合相同，但精确时刻不同**；若把它们称为首入逐值一致就会错误。两条轨迹都无接触的16765个候选具有双 null 时刻，不计时刻差异；49个两条均接触、789个仅一条接触。后者时刻一空一非空，按定义不同。

同盖异时的最小身份见 `bb03 / step1 / [1,2]`，一方无接触的最小身份见 `bb03 / step1 / [10,11]`；上述 JSON 保存双方完整时刻证书与对应 normalized hash，可直接重现比较。身份取词典序，不声称几何最小化。

这里100%是对**保存的精确有理输入与其派生 canonical 代数时刻严格不等**的计数；并未度量差的工程大小，也不自动推出100%的物理/工程失效。本文先前的16813个“描述性相同”仅是 status/盖集合相同，联合逐值相同实际为16765个双无接触候选。证书仍独立：所有17603个候选均UNCERTIFIED。

本文件不把 full_r2/full_r3 或任何未完成批次当最终证据。最终审查状态与文件 SHA256 见 [review_summary.json](review_summary.json)。
