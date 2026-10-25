# WO-C3L4-fix：ABI、consumer、元门与非对称输入补项

此记录是分工实施/定向验证记录，不代替根报告的完整验收。DLL 定向结果均基于修复中的 `eab2/build/fix_branch/eab2.dll`，不能冒充源冻结后的最终全量结果。所有者新鲜树与非作者核查仍待 Claude 验收。

## 实施范围与具名门

| 项目 | 已实施 | 对应门 / 边界 |
|---|---|---|
| 发布 ABI | 独立标准库 ReleaseHeader，冻结全部 64 整数常量及 31 返回类型；完整枚举 eab2_* 原型，缺 API、异返回类型、重复声明等拒收；移出陈旧 acceptance 字段 | tests/test_eab2_release_abi.py；python -I -S 在仓外 cwd 及同名毒化模块下可运行，release 不导入 consumer |
| consumer | derived_seed 与语料 seed 同为空当且仅当；非空仍逐项精确比 | 同文件正负门；仅标准库 ctypes 与发布 DLL，无生产 Python / harness 导入 |
| consumer 新阈值合同 | 数值、类别、quality、reason 仍严格比较；分支 tied_labels 检查 JSON 内部一致性、斜率及候选标签完整性，跨基不同明确登记 | **不是独立 K 核验**，完整独立几何/K 核验属于 L4 harness；消费脚本不冒称完成这一证明 |
| 条件勘误 | 仅 method=branch_certificate 阈值结果允许移除旧单基条件“临界证书基非奇异”“所列越零分量及方向保持有效”；其余条件仍严格比较 | 每条写 WO-C3L4-fix/20261023/branch-proof-v1 的 old/new condition_errata，不称原冻结语料逐字不变；这是 Claude 裁定，不是擅自放宽 |
| 元门 | 增 reflect_x、reflect_y、swap_xy 与 rotation-free-mid / y-free / regression_f 三源；反射力矩、接触切向/边向、摩擦列号及掩码依物理变换 | tests/test_eab2_c3l4_meta.py；64 模型 / 163 通道；局部约束有转动的源不得伪造 anchor gauge |
| b 边导数 | regression_f 共享原始顶点仿射种子，手算 3×5 dA；anchor 偏移核 dM′=dM−a×dF | 上述测试；该源原有限承载导数未认证，新增通道仅作 derived_seed 检查，不虚构 smooth |
| M5/M7 | 新 source-internal 变异 runner 编译独立 TU 并链接实际发布 ABI，基线成功后只认可具名 derived_seed 语义断言失败 | tools/eab2_c3l4_meta_mutations.py；最终执行结果由下节补充 |
| codec | dataclasses.replace 保留 _affine_path / _mu_seed，wire 仍滤私有字段；阈值 branch_certificate / tied_labels 采用独立证书核验规则 | tests/test_tia2d_cases.py 三个既有参数化导出实例由旧 implicit 方法断言改为 branch_certificate，独立用原始 binary64 几何重建 K 核验；没有改冻结数据 |
| 非对称族 | 每个精确阈值源 6 个确定种子：单面、单共享顶点、3 个 SHA 确定随机有理方向、恒/活载方向；至少两个方向含非零恒/活载 jet | tools/eab2_c3l4_asymmetric.py、tests/test_eab2_c3l4_asymmetric.py；正式精确阈值源清点 78，另含 T1b/厚度输入域内源 |
| 红旗检查 | 每侧 3 步 ±2^-18、±2^-22、±2^-26 实际重装配核同标签 skeleton；精确 critical 证书独立复核；保守 Richardson 诊断包络显式计入阈值括号误差 | 差商/包络不是 K 证明，不把原始差商 min/max 当导数括号；门覆盖从下逼近 1/2 而旧错误 0 必红 |

## 已执行定向结果（原样末行）

- 最新 release + meta + asymmetric 工具测试合跑：`99 passed in 3.04s`（禁 cacheprovider、显式 basetemp）。较早 release + meta：`90 passed in 2.21s`。
- consumer 奇异候选元数据补门后 release/consumer 全文件：`85 passed in 1.69s`；新增 7 个正负例核首阶/monic/精确根，不冒称原始几何独立证明。
- 正式全部精确阈值源的 6 通道实造清点：`ASYMMETRIC_FORMAL_INPUTS geometries=78 channels=468 errors=0`。
- 非对称输入与红旗包络测试：`9 passed in 0.48s`。
- 当前交付日志编码定向扫描：`DELIVERED_LOG_ENCODING files=13 findings=0`。
- 四个改动测试文件静态构造定向扫描：`ABI_META_CODEC_ASYMMETRIC_STATIC violations=0`，没有新增准入。
- 新 DLL 发布门：`EAB2_RELEASE_ABI status=PASS exports=31 structures=28 findings=0`。
- 新 DLL consumer：`EAB2_TIA_CONSUMER cases=6 sensitivity=18 mismatch=0`；4 条阈值单基条件 metadata 勘误明确记录，数值/类别/quality/reason 未豁免。
- 旧已冻结 DLL 上新增三个源的反射定向：`C3L4_META cases=9 channels=12 mismatch=0`，仅证明新增输入/变换接线，不能替代修后最终 DLL 元门。
- codec 全文件定向重跑：`55 passed in 24.99s`。此前 54 passed / 1 failed 的唯一失败是 `source changed during query generation; discard and rerun`（其他代理同时修改生产源），该次 **作废**；本次从头独立重跑，不拼日志。更早 ray 下标核验问题已由 root 修正。
- 非对称 g1_unreversed_t2 预跑：`C3L4_DIFF sensitivity=4 mismatch=3`（283.36 秒）；前 4 通道共 8 侧 K 核验及 24 个精确差商探测均 PASS，第 5 非零恒/活载通道触发证明能力 floor，第 6 随 case 异常未执行，另有 source_changed 使该次整体作废。不能称全族通过。隔离第 5：修复前 C++ 双侧 unresolved，Python one_sided exact_jet、R=5/128、L=−15/512。定位为 C++ 未对原侧 INFEASIBLE 探测另求 dual 可行点；定理(a)并不要求原侧最优。已移交 C++ 代理补路并复测，未豁免 floor。

诊断输出统一位于被忽略的 `tmp/abi_minor/`（不入库；保留的摘要与字节映射见 [abi_minor_history.json](abi_minor_history.json)），没有把重复运行大输出加入跟踪证据目录。最终完整运行以根报告记录为准。

## 历史证据卫生

- 原 tied_labels_forensics.log UTF-16LE BOM 原字节与旧 final_fast / final_full 共 19 成员已经 H1 追加归档、逐成员读回 SHA-256 核验。
- [外部归档 ZIP](file:///D:/eab-evidence/reports/codex/C3L4_fix_evidence/abi_minor_history_20261023/superseded_runs_and_utf16.zip)，SHA-256 `01cdba67d17b5af5c6c5819b2a78d7c71c3f22b37580ce7b48fb62d48adc5f68`。
- [逐文件映射](abi_minor_history.json) 保留原相对路径、字节、SHA；18 个已取代旧文件总计 56,181 字节，核归档后逐个安全移除，目录保留历史 README 指向归档。
- 取证日志仅转 UTF-8 无 BOM，解码内容与换行保持；tools/eab2_audit.py 新扫交付 .log，排除 ignored tmp/build。历史转码不升级旧结论。
- 真实净增须由 root 对当前候选全树总字节减 b34c966 全部 blob 总字节统一计算；本分工不把文件改动总和冒称净增。

## 文件清单

- tools/eab2_release_abi.py；tools/eab2_tia_consumer.py；tools/eab2_audit.py
- tools/eab2_c3l4_meta.py；tools/eab2_c3l4_meta_mutations.py
- tools/tia2d_cases.py；tools/eab2_c3l4_asymmetric.py
- tests/test_eab2_release_abi.py；tests/test_eab2_c3l4_meta.py；tests/test_tia2d_cases.py；tests/test_eab2_c3l4_asymmetric.py
- eab2/README.md；eab2/ABI_CONTRACT.md（机器冻结表仅新增常量/返回型与移除陈旧 metadata；旧公开布局、函数参数、能力值不变）
- reports/codex/C3L4_evidence/tied_labels_forensics.log；final_fast/README.md；final_full/README.md
- reports/codex/C3L4_fix_evidence/abi_minor_history.json；本记录；外部追加归档 ZIP

M5/M7 实际变异由 root 的 final_runner mutations stage 统一执行，本分工按指令不重复预跑。最终非对称族、完整元门和全部构建/快档/全档结果以根报告为准；本分工不把已作废的预跑或缺路定位冒称验收通过。

## WO-C3L4-fix-close 当前源码对账（47691cc，2026-10-24）

上文保留 5bdcf01 前的实施、失败与作废运行历史，不是 47691cc 的新结果。当前源码已增加齐次对偶见证、最近 6 基重试、筛选探测与探测几何阈值候选；非对称族对精确有限 limit 另追加 `asym_limit_dead_live`，因此历史“每源 6 通道”只指阈值通道，不是当前整族总数。差分证明能力退化现登记为该查询的 mismatch 后继续后续通道，不豁免 floor。

[当前 C++ / Python 接口与搜索预算对账](cpp_interface_audit.md)列明源码位置与具名门；当前发布 ABI 仍冻结 31 导出、28 结构、生产能力位 581501（其中 SENSITIVITY2=524288）。此处为静态对账，不新增构建或运行通过声明；本单实际 ABI 复核、所有者新鲜树及待验收状态见 [收尾报告](../C3L4_fix_close_report.md) 与 [修复轮报告](../C3L4_fix_report.md)。

## 64b499f 续单入口（2026-10-24）

上节仍是 47691cc 的历史对账；本轮定向顶点、形状不变量及工具档案请求绑定见 [接口审计](cpp_interface_audit.md)，实测结果与所有者待验收边界见 [收尾报告](../C3L4_fix_close_report.md)。
