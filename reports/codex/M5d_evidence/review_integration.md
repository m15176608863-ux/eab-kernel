# M5d 集成与冻结发布独立团队复核

范围：`m5d_refresh_frozen / m5d_run_gates / m5d_finalize_evidence / m5d_audit_admissions`。
本记录是独立团队交叉复核，不是所有者 G6；没有代替主代理重跑长全量，也没有在真实冻结目标上试发布。

## 结论与首轮发现

**发现并修复 1 个 major；当前 0 critical / 0 major 未关闭。** 不应把此轮写成“从未发现问题”。

首版发布器在前段与联合重建时核验 source/input，但后续几个子进程结束到目标发布之间只检查候选及目标文件哈希。我们在隔离 tmp 沙箱运行真实 `main()`，以已完成的小合成子进程产物代替长回放，在最后一个子进程完成后改动一份被绑定源文件：发布器仍输出 `M5D_FROZEN_REFRESH_GREEN 7` 并写 `complete=true`，而发布摘要的源哈希已经过时。原始项目源和冻结文件均未修改。

首版脚本 SHA256：`815c878433c738aa321a81fe3f773410d481e2bf7d1d78b86c55c05d54bf4a74`。
旧探针的 `publication_rejected=false / final_marker_exists=true` 与不一致源哈希已保留到机器复核记录。

主代理修复：统一封印所有候选声明的 source/input/inherited 哈希，以及发布器自身、候选、备份字节；每项写入前后及全部写完后重新核验；原子替换单文件；异常时只恢复仍为本次产物字节的已写目标。增加 `--stage / --backup`，失败后的候选与备份用新目录，不自动删除或续接。另修复 `research_diagnostics.json` 是 list 而非元数据 dict 的封印兼容问题。

对修复后真实 `main()` 重新跑两种隔离探针：同样闭包漂移现在被拒绝、没有最终 complete 标记；未漂移例正常完成。不是只检查修复源码或更新哈希。

## 固化门与真实内部变异

新门 `[tests/test_m5d_frozen_publication.py](file:///D:/eab-wt/cx-e2/tests/test_m5d_frozen_publication.py)`：

- source、input、inherited 三类依赖分别在发布前、第一项后、末项后、最后一次逐项检查后改变，全部被拒绝，三个目标全部恢复原字节，无半旧半新；备份保持原字节。
- 正常依赖下全部发布新字节；纯 list 诊断产物也被纳入封印。
- 真正移除 `publish_sealed` 函数体最后的 `verify_seal(bindings)`。在最后逐项检查刚结束后改变源，使剩余的最终检查成为必需；变异红在具名语义断言 **`M5d changed closure must be refused`**，不是检查源码哈希是否与某快照一致。
- 16 个节点通过；新增文件单独运行 AST 静态扫描 **0 违例**，没有新增准入。

预期答案只是沙箱中事先保存的原/新字节，无几何 oracle。`mutation_support` 仅负责真实函数体变异。门不会修改任何生产源码文件。

## 四组件核查结果

### 冻结刷新

- 新鲜 `python -c` 子进程只导入需要的 replay/helper，避免编排器污染运行时闭包；每个完整长批次有起止源绑定与进度状态。
- robust 逐算例 counts/references 与旧数值对照；combined 发布器逐条核对 64010 个精确 P1/P2 观察并连接全部 68 个重算候选，而非只检查汇总计数。
- minimal、research minimal、initial witnesses 均调用真实求值函数；比较 examples/rows/counts 后才进入候选发布列表。代码中没有把旧结果复制后只修改源哈希的分支。
- 目标原字节备份先行、所有候选比较先于目标写入；最终统一闭包验证补上了本轮发现的窗口。
- `--adopt-complete` 是明确采纳完整批次，不拼接行流；失败批次须新目录。研究摘要使用历史候选流筛选，但候选实际重解，再由全新 robust 流逐条联合校验，口径准确。

### 四片与最终审计

- `m5d_run_gates` 只将已有 runner 的 EVIDENCE 精确设置为 M5d；源码导出、临时目录、日志和 pytest basetemp 均留在本树 M5d tmp。pytest 使用 `-p no:cacheprovider`。
- `m5d_finalize_evidence` 对既有严格审计器设置同一 EVIDENCE；它独立检查四片 setup/call/teardown 全过、收集=执行、0 skip、节点唯一、最后行与原日志一致、导出文件集合及字节不变，再检查当前可执行文件与真正执行的导出一致。
- 没有用“摘要 GREEN”取代原始节点/阶段审计；新鲜字节导出明确不是新 Git checkout。最终是否全绿以最终四片证据为准，本复核不抢先宣布完成。

### 逐站准入

- wrapper 让旧 counterfactual 扫描器使用 M5d OUT，并顺序检查基线与当前树；没有修改 policy 或加入 waiver。
- 口径仍是关闭准入前后实际 emitted diagnostic 的 `(path,function,rule,line,AST column)` 差集，并单列 shared marginal；不是仅数 policy JSON 行或 context 命中。
- 当前 HEAD 已只读确认 `5b73cc8dfc1ad4f257412392111927d5a7171640`，与 wrapper 的基线标记相同。真实逐站净增结果由主代理长审计交付，本复核不虚报其已完成。

## 保留的运行边界

1. 七个文件不是跨文件原子事务。进程/主机被强制终止可能来不及执行 Python 回滚；此时 complete 标记缺失，必须作废批次并核对备份，不能声称强杀后自动恢复。
2. 外部同时修改目标或备份时，安全回滚拒绝覆盖未知字节；需要人工核验。我们的“全部恢复”门针对闭包漂移但目标/备份无人外改的明确场景。
3. 最终长回放、四片、静态全仓及逐站准入结果仍由主代理完成；本审查只读加小合成校验，未修改被审脚本。

证据：[机器复核与前后反例](file:///D:/eab-wt/cx-e2/reports/codex/M5d_evidence/review_integration.json)、[16 节点原始输出](file:///D:/eab-wt/cx-e2/reports/codex/M5d_evidence/review_integration_tests.txt)。
