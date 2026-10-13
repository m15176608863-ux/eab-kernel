# M4b 独立复核 R2：快照拥有权、时间面与故障隔离

- 复核者：`baseline_gates`，没有实现被审查的 bdda 生产代码。
- 范围：M4b shadow 只读旁路，不代表 eab 替换或全仓库 G6。
- 结论：**critical = 0，major = 0，minor = 0；本范围通过。**

## 源码追踪

- `DetectSnapshot` (`bdda2/io/detect_snapshot.hpp:20`) 持有值类型的参数、几何和两组 `vector<array<int,7>>`，没有 solver 的指针、span 或 mutable buffer 引用。hook 接收 const 快照引用。
- `run.hpp:415–433`：legacy 的 df06 照原顺序执行；df06 的 `M` 入参是 const，并在 `transfer.hpp:53` 自己复制为局部 `m`，因此之后拷贝 `M` 仍是 raw-df05。`rows.t7` 是 df06 后、df07/ContactStore 构造前的实际表。影子未回写 `M/rows/C/vs`。
- 快照构造与所有几何 val 读取都在 `DetectMode::Shadow` 分支内。catch 只填写审计错误，不改变物理 Status；失败后停止后续影子回调，但求解继续。
- writer 开启流异常并 flush/close；中途/收尾失败有独立错误通道。文件有版本、列序、连续步号及 end 完成记录，不能把截断文件当完整捕获。
- `detect_snapshot.hpp:54–70` 在 truncation 前检查 canonical path 及 filesystem equivalence，覆盖相对路径、大小写和 hardlink。CLI 保护输入、可执行与四类既有输出；Qt 保护输入和自身 exe。未构造 writer 的 Legacy 不触碰任何 shadow_path。

## 独立证据

1. 遍历 15 例全部 **1810 帧**，将 shadow geometry 按 `vidx` 与已在 master 字节矩阵中验证的原 `geom.csv` 的 `step(s-1)` 比较：**188320 行完全相同**，未用距离容差。
2. **1648 帧 raw-df05 != post-df06**，证明两时间面不是重复拷贝同一表造成的假覆盖；源码 const-input/局部-copy 追踪说明两者来源。
3. 独立对 bb52 全 **50 步**将 shadow 路径故意指向目录：审计输出 `SHADOW_AUDIT_RED`，legacy RC 0，位移/状态/力/几何四 CSV 与修改前冻结版本逐字节相同。
4. 15 例 × 三模式的四 CSV、stdout、stderr，与基线两次各自逐字节一致；无非复现列豁免。
5. 新增自动门覆盖 bb/db/exe/四输出/hardlink alias 保护，以及库 callback 抛异常和缺 sink；post 全套 336 passed, 1 xfailed。

## 证据与边界

- [独立动态证据](independent_r1_r2_checks.json)
- [逐字节完整矩阵](file:///D:/bdda-wt/shadow/bdda2/build/m4b/byte_matrix.json)
- [生产开关门](file:///D:/bdda-wt/shadow/tests/test_m4b_detect_switch.py)
- 快照是检测几何与 Tuple7 拓扑，不冒充收敛接触状态或力；这些保持在原 state/force 产物中。
- bb/db/exe 的 SHA256 由验收矩阵和回放 provenance 绑定，JSONL 本体不重复嵌入这些哈希；独立转移文件时必须保留配套 manifest。
- 捕获是同步文件 I/O；本复核证明正常返回的 I/O/回调错误不改 legacy 结果，不承诺操作系统/磁盘无限挂起时的实时性隔离。
