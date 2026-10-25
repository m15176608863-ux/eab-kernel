# WO-C3L4-fix-close 收尾续单报告（64b499f）

日期：2026-10-24；执行：Codex；数学合同、所有者新鲜树、对手核查及最终接受：Claude。

## 0. 目标、范围与回退锚点

开工 HEAD `64b499f8bf2d5e889d0ac0c65a3eab37ef743629`，工作树干净。只修改 tools/tests/docs 和收尾证据；成功标准是定向/静态/四变异门绿、minor 有直接语义门、分片打包不漏不重、ABI 不变、真实净增 ≤ 2,000,000 B。回退锚点为该提交，以及 [本轮基线与旧报告备份](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_fix_evidence/tmp/close_64b499f/)。

未执行 Git 写操作；未改生产源码、公共头、设计正本、冻结输入。未访问或修改所有者新鲜树；只读用户指定的 `c3l4fix5_fresh_out` 输出目录。未安装/下载/结束他人进程；未启动 Python 全档四分片，也未把有限测试说成全域数学证明。

## 1. 定向复测与静态复核

统一复测覆盖 errata、分片打包、仓库大小、独立核验器、threshold branch、C++ JSON oracle、L4 harness/asymmetric/meta，以及原先五个 KeyError 参数与 readback 接线；不重算全族冻结证据；6 项慢测按默认规则 deselected，非全档。运行器持续写进度，TEMP/TMP 与显式 pytest basetemp 均在本轮目录，禁用 cacheprovider。

```text
python -X utf8 reports/codex/C3L4_fix_evidence/tmp/close_64b499f/run_checks.py
253 passed, 6 deselected in 600.14s (0:10:00)
python -X utf8 tools/check_exact_construction.py
exact construction AST gate: 0 violation(s)
C3L4_CLOSE_CHECKS head=64b499f status=PASS
```

[实测命令/退出码/耗时/日志哈希](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_fix_evidence/close_checks_64b499f.json)；[定向日志](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_fix_evidence/tmp/close_64b499f/directed.log)；[静态日志](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_fix_evidence/tmp/close_64b499f/static.log)。另一次 minor 集合实测末行 `57 passed in 122.50s (0:02:02)`。新增域门初次 fixture 默认 orientation 与探测 helper 不同，2 项失败；修正测试输入为 unreversed 后重跑通过，未改生产、未放宽断言。旧轮失败保留在历史记录，不重写为绿。

## 2. 第二轮 minor：独立核验及探测门

- `.certificates.jsonl` 记录新增调用方原始请求的 `mu_max_binary64`，差分双方、meta、readback 均从原始 query 传入；独立 `verify_record` 要求它与 `search_domain` 相等。F4a/F4b 同步伪造自洽返回域仍被核验器自身拒绝，而非仅依赖差分。旧 archive 缺调用方字段明确拒绝，不从返回域倒填。
- certified 的 lower/upper 为 null，及上端 point/ray 为 null，均经 `need` 给明确 AssertionError，不再 TypeError。
- `_rational_roots` 门覆盖 `v²(v−7/128)` 重根；探测域门在 `mu_hi < mu_max` 时记录真实 LP 查询，核始终在调用方原域内、不误用缩窄隔离区间。
- Python 直接构造 K 正、有限探测点负的同一复用基，并内部绕过 `_probe_consistent` 证实门会红。C++ 新工具原样提取当前生产复用片段，记录片段 hash/字节一致性，两个探测点由独立 Fraction 算术核 JSON；内部删除 probe guard 变异触发同一语义断言。

```text
python tools/eab2_branch_probe_reuse.py --core eab2/build/close_mut_core_64b499f/eab2_core.lib --output eab2/build/tmp/close_probe_reuse_64b499f
C3L4_PROBE_REUSE_CPP_OK baseline=1 killed=1 survived=0 json_records=4
```

[核验器](file:///D:/eab-wt/cx-c0/tools/eab2_branch_verify.py)、[直接拒伪门](file:///D:/eab-wt/cx-c0/tests/test_eab2_branch_verify.py)、[Python 门](file:///D:/eab-wt/cx-c0/tests/test_threshold_branch.py)、[C++ 白盒工具](file:///D:/eab-wt/cx-c0/tools/eab2_branch_probe_reuse.py)、[实测摘要](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_fix_evidence/close_probe_reuse_64b499f.json)。C++ 此项是生产原片段白盒单测，不冒充端到端完整求解器测试；额外 1 个被杀不混入下列四门 22 个。

## 3. 四个内部变异门

自己的 `eab2/build/close_mut_core_64b499f` 从当前源码构建；PowerShell 直接运行绝对路径 ASCII cmd，构建退出 0，末行 `[14/15] Linking CXX shared library eab2.dll`。core/DLL/ABI object 与各变异产物时间戳均晚于相应启动。未动顶层已有 build 产物。

```text
python tools/eab2_c3l4_mutations.py --core eab2/build/close_mut_core_64b499f/eab2_core.lib --output eab2/build/tmp/close_mut_l4_64b499f
C3L4_MUTATIONS_OK baseline=2 rejected=5 semantic_failures=5
python tools/eab2_branch_mutations.py --core eab2/build/close_mut_core_64b499f/eab2_core.lib --output eab2/build/tmp/close_mut_branch_64b499f
C3L4FIX_BRANCH_AND_STABLE_MUTATIONS_OK baseline=3 rejected=7 branch_semantic=4 derivative_comparison=2 backend_certificate_rejection=1
python tools/eab2_c3l4_meta_mutations.py --build eab2/build/close_mut_core_64b499f --output eab2/build/tmp/close_mut_meta_64b499f_r2
C3L4_META_MUTATIONS_OK baseline=2 rejected=2 semantic_failures=2
python tools/eab2_c3l4_certificate_mutations.py --output eab2/build/tmp/close_mut_certificate_64b499f
C3L4_CERTIFICATE_MUTATIONS_OK baseline=2 rejected=8 semantic_failures=9
C3L4_CLOSE_MUTATIONS_OK baseline=9 killed=22 survived=0
```

全部退出 0；**9 基线、22 被杀、0 幸存**。certificate 前后各 11 项绿（79.66s / 80.99s）；仅随 caller μ 参数更新工具注入锚点及 watched 清单，不改缺陷语义。meta 在 minor 冻结后用新 `_r2` 目录完整重跑。最初 cmd 相对路径启动失败日志保留，改绝对路径后完整构建，不计为语义被杀，不拼接日志。29 个四门生成批处理纯 ASCII；源码/产物互异与恢复验证见 [被杀/幸存清单](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_fix_evidence/owner_run_fa481ba/mutations.md)、[机器证据](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_fix_evidence/owner_run_fa481ba/mutations.json)。

## 4. 分片所有者包与 errata 交接

目录已改为 [owner_run_fa481ba](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_fix_evidence/owner_run_fa481ba/)，引用同步；旧结果不只改提交号冒充新跑。工具兼容原 monolithic，也支持 `l4_formal/t1b/thickness/branch` 和 `l4_asym0..5` 十片；逐文件提取末行/计数/mismatches/errata/证书统计，保存 log/err 的 SHA-256 与字节数、summary 与 DLL hash，不复制大文件。

当前源码清单共 **342 cases**：formal 114、t1b 36、thickness 25、branch 5、asymmetric 162。校验重复 case、重复查询键、遗漏/未知/错族、计数与 DLL 一致性，完整后合并送原 errata 语义。只读取实际稳定快照；部分片保持 pending。完整 JSON 与退出码分别判定：完整十片可生成台账，未知退出码仍为 null/process pending、整体 partial，不捏造 0；明确失败退出阻断完整绿。具名合成回归见 [打包测试](file:///D:/eab-wt/cx-c0/tests/test_eab2_owner_run_pack.py)。

```text
python tools/eab2_owner_run_pack.py OWNER_OUTPUT_DIR --output reports/codex/C3L4_fix_evidence/owner_run_fa481ba --source-commit 64b499f8bf2d5e889d0ac0c65a3eab37ef743629
OWNER_RUN_PACK status=failed layers=21 pending=13 failed=8 errata=pending
```

OWNER_OUTPUT_DIR 的完整只读路径见 [manifest](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_fix_evidence/owner_run_fa481ba/owner_run_manifest.json.gz)，[一页索引](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_fix_evidence/owner_run_fa481ba/owner_run_manifest.md)。本次部分结果试跑退出 1：源 summary 有明确失败，L4 JSON 未到；不是打包工具自称 PASS。部分 L4 err 明示 `--dll requires existing absolute path`；根因处理、新鲜树重跑均留给所有者，不改该目录。缺 L4 不生成伪台账。Claude 后续原命令重跑即可；最好另记录真实命名退出行如 `L4_FORMAL_EXIT 0`，不可按无映射 PID 顺序猜配片名。

## 5. 文档对账与发布 ABI

README、澄清提案、cpp_interface_audit 已对齐定向顶点（每次 point/ray 调用最多 8 个负分量）、形状不变量与 `_probe_consistent`。筛选 ε=`2^-24` / η=`2^-8`、固定探测 ε=`2^-24` 与 56 次二分、4×4 提升网格、RETRY_LIMIT=6 均核对；不恢复 seed scale 或 trace 环境变量。`--branch-sweep`、`asym_limit_dead_live`、能力位 581501 仍一致。ABI_CONTRACT 仅补诊断/工具档案文字，冻结表不变；abi_minor_results 保留历史并加当前入口，不冒充本轮实测。

```text
python -X utf8 tools/eab2_release_abi.py --dll eab2/build/eab2.dll --output reports/codex/C3L4_fix_evidence/close_release_abi.json
EAB2_RELEASE_ABI status=PASS exports=31 structures=28 findings=0
```

退出 0；既有 DLL hash/mtime 未变，不声称与所有者 DLL 字节相同。[接口对账](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_fix_evidence/cpp_interface_audit.md)、[ABI JSON](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_fix_evidence/close_release_abi.json)、[原始末行](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_fix_evidence/close_release_abi.log)。两份主报告整文件保持开工字节，`{FRESH}` / `{ADV2}` 与 `C3L4FIX_PENDING_OWNER_ACCEPTANCE` 均由 Claude 后续填写。

## 6. 真实净增、卫生与遗留

```text
python tools/eab2_fix_close_audit.py --baseline reports/codex/C3L4_fix_evidence/tmp/close_64b499f/baseline.json --output reports/codex/C3L4_fix_evidence/close_hygiene.json
git diff --check
C3L4_CLOSE_HYGIENE status=PASS net=1990241 limit=2000000 findings=0
```

真实净增 = 当前仍存在的 tracked + 未忽略 untracked 去重总字节 − b34c966 全部 blob 字节；不是只加正差。基点 **53,878,592 B**；候选 **55868833 B**；净增 **1990241 B**。ignored 构建和原始长日志不属入库包；所有者紧凑包 **53149 B**，≤ 300,000 B。

本轮曾实测净增 2,042,553 B，按授权压缩旧 C3L4_evidence 的三个 module_coverage、abi_static_repair、checks/mutations、pack_manifest、clarification/history_mapping、checks/harness_static_equivalence 共八份 JSON：100,295 → 19,896 B，省 80,399 B，gzip mtime=0。逐份解压与 HEAD 原 blob 字节/hash 一致；不修改冻结输入。源/gzip hash、路径与回退映射见 [historical_compaction.json](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_fix_evidence/historical_compaction.json)，入口见 [EVIDENCE_ARCHIVE](file:///D:/eab-wt/cx-c0/reports/EVIDENCE_ARCHIVE.md)。

661 个保护路径及 30 个原顶层 build 文件 hash/mtime 不变；设计 SHA 保持 `6d174ecc4f1326d5bac21c56c8d333485fb50bbaef3a12150e94eaff14cb4dac`。新增/修改交付无 >1 MB、无 BOM、无编译产物；基点既有的 3,670,335 B 冻结准入政策及 10 个 BOM 文件原字节保留，不扩大豁免。全部改动/迁移/压缩文件和可点击链接见 [卫生结果及逐文件清单](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_fix_evidence/close_hygiene.json)。

本续单要求的定向/静态复测、四变异门、minor 修补、分片工具试跑、文档/ABI 与净增卫生均完成。本单无待做项；所有者输出快照的 8 层失败、L4/其他缺层、新鲜树全档和对手最终接受仍由 Claude 接管。此 DONE 仅指收尾执行，不是 C3-L4 总验收通过。

C3L4CLOSE_DONE
