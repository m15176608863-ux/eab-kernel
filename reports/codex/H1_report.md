# WO-H1 返修报告（2026-10-19）

基线 `codex-work @ 476c5d6`；本轮修订 Claude 的 5 个 major 与指定 minor，不提交。原报告逐字节保留为 [H1_report_v1.md](file:///D:/eab-wt/cx-e2/reports/codex/H1_report_v1.md)。本报告更正 v1 中退役数量、冻结门作用域及 P3 覆盖的过宽声称。

## M1–M5 处置与变异验收

| 项 | 修订 | 原版 / 指定内部变异 |
|---|---|---|
| M1 | 恢复 6 个运行内 guard 节点和 1 个 M4c 闭包节点；直接调用守卫，穿越用 `(bad,bad)`，无当前哈希自比 | 7 passed；提前 return + runtime/REPLAY_SOURCE_FILES 丢 numeric_domain：7 failed，7/7 红在目标断言 |
| M2 | 快档晋升 M5a 首块 15、旋转 3、M5b 五例 1、M4c bb52 首帧 1 | 默认快档收集并执行 20 节点，20 passed in 5.35s；其余 14 个 M4c 家族仍在全档 |
| M3 | A10 改引 2D tight-fit 与 3D zero-clearance 生产门；A28 明写无门、两纯算术测试标算例 | 原版 24 passed；毒化相关生产路径后 22 failed、2 算例 passed，二者不再冒充生产门 |
| M4 | A14 主门改为 exact clipped-cover 双向/独立 ray-exit 门，原门注明只守包含方向 | 原版 15 passed；exposed=True 后主门 6 failed、包含门 9 passed，6 红均为 clipping exposure mismatch |
| M5 | 位移形式逐点对独立 oracle；加凹口/凹缝、membership=0/topology=1 紧配缝、顺逆时针环；元门明确 test-of-test | P3 原版 29 passed；G4/G5/G8/G9 各 24 failed、5 passed，红在成员/拓扑/CW 合同断言 |

证据：[M1/M2 与冻结修订](file:///D:/eab-wt/cx-e2/reports/codex/H1_evidence/fix_verification/REPORT.md) · [当前退役清单](file:///D:/eab-wt/cx-e2/reports/codex/H1_evidence/hash_retirement.json) · [M3/M4](file:///D:/eab-wt/cx-e2/reports/codex/H1_evidence/fix_docs/verification.json) · [M5 与 C1 镜像](file:///D:/eab-wt/cx-e2/reports/codex/H1_evidence/fix_p3/verification.json)。所有变异只在受控副本/内部替换中进行，未改现场生产数学。

## minor 逐项处置

| 编号 | 处置 |
|---|---|
| m1 | README 13 行与归属表具名门集合逐项对齐；补 A20、A25、A30、A31–33、A16、A04；27 个具名门共 96 节点原版全绿 |
| m2 | A36 标为已有标准结果，二维特例引 Shi 2015 §6.3–6.4 / 2021 §5.3，不再列仓库新结果 |
| m3 | canon_map §六标题/§七历史指针、m3_global 原文核查/归档指针、旧 plan 首入措辞均订正 |
| m4 | 归档说明明列 theory_audit 勘误全文及唯一 +197 B 例外；Git 真值 523,273,912 B，归档现场跟踪字节 523,274,109 B |
| m5 | A39 与测试只声称位移反射形式逐点检验，不把 a0+b0 的内部抵消算额外覆盖 |
| m6 | AGENTS 恢复 F 门指针/纯度门、阈值先测后钉、通用 basetemp、-m slow 须配 --runslow；README 已证明栏不得收无门命题 |
| m7 | 2728 / 26+18 明列封存、未验收 WIP 5e3ba68 来源及独立近似校验；写作“26 次标签改变 + 18 次离开严格穿透” |
| m8 | BFS 加自身父包；contact_record 注入 adapter 后 40/40 内核模块报出；删除父包 BFS 的工具内部变异在覆盖集合断言报红 |
| m9 | 扩禁词、保留字母数字、复数/拼接缩写、bytes/模块路径/匹配模式字段；各类真实源码注入有牙，纯度共 35 节点 |
| m10 | contact_record/numeric_decode/eab.__init__ 纳入词法扫描，共 43 模块；joint_material 与 dataclass slots 仅有具理由的站点白名单 |
| m11 | 三个适配器恢复原映射表来源/状态图例/盲区/码型注释 |
| m12 | affine_motion、geom 等说明与空行修正；geom 原有 8 处混合 CRLF 统一 LF；可执行 AST/归一化上下文不变 |
| m13 | 19 死键（13 imports、6 members）在对应表标退役，策略条目总数不变 |
| m14 | 可选包循环整理未做：不影响当前导入，避免扩大搬家范围；本轮不声称已消除 |
| m15 | R3 门调用 examples.verify；名称明确在冻结标签和区间上重执行两张证书及 legacy 计数，不声称重求首入标签/时间 |
| m16 | PROVENANCE 显式检查 unknown；两门定性为数据完整性检查，而非语义替代 |
| m17 | 补 test_int1_semantics 插桩重钉的精确导入行差异；对应表 114 旧重键 + 19 退役说明 + 1 插桩说明；另列本轮 1 个 docstring-only 上下文审查 |
| m18 | 恢复 source_hashes==source_hashes_end、schema-id、闭包 >4、inherited_hashes；继承流哈希只核摘要内记录，不声称重读外档大流 |
| m19 | 慢函数清单 220 条、死条目 0，fast_nodes 20；恢复的 7 守卫都在快档 |
| m20 | 可选提高执行见证门槛未做：现有 55/55 只是逐模块实际执行见证，不声称函数/分支全覆盖 |
| m21 | 当前文档和工具的历史路径映射已说明：先 fixtures/frozen，后只读外档；可选死链枚举测试未加，旧全量 CLI 不自动恢复 |
| m22 | 表头改“已归档跟踪文件”；补转入 fixture 列：表内 134 搬迁 + 根级 2 搬迁 + 1 复制 = 137 |
| m23 | 紧配缝拓扑对独立角扇区外部判据比；G8 在 24 格报红，不再仅做正反互比 |
| m24 | 每格含 A/B 四种顺逆环组合；G9 在 24 格报红 |
| m25 | 新增 A 环凸性应使用 ra 的镜像门；C1e 变异 1 failed / 28 passed，目标断言报红 |
| m26 | 参数格互异门单列 test-of-test，计数保留但不冒充生产语义门 |

分项文件/核对：[文档与归档修订](file:///D:/eab-wt/cx-e2/reports/codex/H1_evidence/fix_docs/README.md) · [纯度与静态说明](file:///D:/eab-wt/cx-e2/reports/codex/H1_evidence/fix_purity/README.md) · [冻结证据作用域](file:///D:/eab-wt/cx-e2/docs/frozen_evidence.md)。

## 数学、策略与归档边界

- `src/eab` 55/55 模块去真实 docstring 后的完整可执行 AST 与 476c5d6 相同；48 文件原字节不变，另 7 文件只改说明/注释/换行。[逐模块证明](file:///D:/eab-wt/cx-e2/reports/codex/H1_evidence/fix_production_integrity.json)。
- 准入仍为 3522、imports 648、members 432、renewals 106。唯一 R12b-L0008 的 docstring 上下文改动先证同一 AST 站点和可执行 AST，再机械改 1 字段；142 映射数不变，反向投影后的完整策略仍等于 1ce9a91，不是为过门单改哈希。[机械脚本](file:///D:/eab-wt/cx-e2/reports/codex/H1_evidence/fix_policy_context.py) · [上下文证明](file:///D:/eab-wt/cx-e2/reports/codex/H1_evidence/fix_purity/context_update.json) · [重键/退役/插桩表](file:///D:/eab-wt/cx-e2/reports/codex/H1_evidence/policy_rekey.csv)。
- `D:/eab-evidence` **零写入**；43 份清单 SHA 未变，6047 个归档跟踪项的 Git 字节统计已订正；137 fixture 完整性通过。没有重算冻结证据或全量回放。[归档映射与例外](file:///D:/eab-wt/cx-e2/reports/EVIDENCE_ARCHIVE.md)。

## 本轮快档与两次全档（最后一行原样）

快档单进程：
```text
8004 passed in 274.83s (0:04:34)
```
运行器总耗时 295.266s；8004 快 + 5940 慢 = 13944。逐模块执行 55/55，含新增快档 20 个冻结族语义节点；共享主机耗时不作内核性能结论。

开工原样 476c5d6 全档四片：
```text
3477 passed in 778.30s (0:12:58)
3477 passed in 1772.97s (0:29:32)
3477 passed in 814.21s (0:13:34)
3476 passed in 1181.76s (0:19:41)
```
收尾全档四片：
```text
3486 passed in 1459.34s (0:24:19)
3486 passed in 905.04s (0:15:05)
3486 passed in 2203.52s (0:36:43)
3486 passed in 1210.93s (0:20:10)
```
三次均收集=派发=实际执行、多重集合相等，0 failed、0 skip；两次全档静态均 `exact construction AST gate: 0 violation(s)`。副本与其核对源均未漂移。[本轮基线](file:///D:/eab-wt/cx-e2/reports/codex/H1_evidence/fix_baseline/summary.json) · [快档](file:///D:/eab-wt/cx-e2/reports/codex/H1_evidence/fix_fast/summary.json) · [收尾全档](file:///D:/eab-wt/cx-e2/reports/codex/H1_evidence/fix_final/summary.json)。

## 节点差异与遗留

- 原 H1 基线：**13877 − 5 + 72 = 13944**，11 对等量改名；删除不再误计为 12。新增 72 分栏含 2 个完整性检查与 1 个 test-of-test，不全称语义门。
- 本轮：**13907 + 7 恢复守卫 + 29 纯度 + 1 C1 镜像 = 13944**，26 对等量改名（对称 24、元测试 1、R3 1）；无未知增删。[原基线逐节点账](file:///D:/eab-wt/cx-e2/reports/codex/H1_evidence/node_delta.md) · [返修逐节点账](file:///D:/eab-wt/cx-e2/reports/codex/H1_evidence/fix_node_delta.md)。
- 137 项真实生产提交/工具版本仍 unknown，不能补造；旧全量 CLI 历史输入需按映射准备。可选 m14/m20/死链枚举未实施，未扩大承诺。
- 本轮为受控字节副本验证，**不是新鲜 Git worktree/克隆**；开工快照来自只读 git archive，收尾来自冻结工作树。未 commit/push/切分支，未改姊妹仓库或正本。Claude 的新鲜树结果与一路独立对抗复验仍由所有者确认，本地修复证据不冒充其验收结论。
- 完整文件链接见 [本轮交付清单](file:///D:/eab-wt/cx-e2/reports/codex/H1_evidence/DELIVERABLES.md)；v1 报告原字节留存，不把本轮修复倒写为初版已做到。

H1_DONE
