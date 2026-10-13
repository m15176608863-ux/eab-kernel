# R6：M4b 基线、捕获与计时协议独立审查

## 范围与结论

审查者：shadow_replay 子代理；被审文件为 b-DDA 专用工作树的 `tools/bdda/verify_m4b_shadow.py`，本轮没有编写或修改该文件。仅审查 WO-M4b 捕获协议，不是全仓库 G6。

最终代码复核：**critical 0，major 0，remaining minor 0**；历史复算入口 minor 已关闭（见末节）。基线与 45 次比较运行的当前磁盘证据吻合；最终计时已经补测并完成下述独立复核。其范围为代理无并行计算、但仍有正常桌面后台负载；不可把它称为绝对系统空载或零开销的单独证明。

## 已核对的实物与协议

- 改前 source_manifest 记录 HEAD `cbf3642e31a3d68790fb62446da185b55ee70e63`、git_status 为空。
- 独立打开 source_snapshot.zip 核对其中 **232 条** source hash；其余 **79 条**（主要为 df 输入、旧 exe/源文件）在 clean `baseline_head.zip` 逐条核对；合计 **311/311**，没有把源码快照和完整 HEAD 归档混称同一 ZIP。
- matrix 所记 source_manifest 与 source_snapshot 的文件 SHA256 均现场重算吻合；改前 baseline exe 与改后 exe 哈希也吻合。
- baseline_repeatability 为 30 次运行；modified 为 45 次运行。逐条检查运行目录、exe、bb/db 输入与四个 CSV 输出参数，全部局限 `D:/bdda-wt/shadow`；没有路径落在 `D:/b-DDA` 主工作树。
- `clean_env` 以不区分大小写的 BDDA_ 前缀移除宿主变量，再固定 2560/1355 屏幕；unset 不注入 BDDA_DETECT，legacy/shadow 显式注入。仅 shadow 给专用 path。
- `run_one` 创建全新目录，子进程 argv 为列表，不拼 shell；returncode 非零立即失败；out.csv 实际 step 集必须等于 1..N。四个求解 CSV 加 stdout/stderr 全部入 SHA256 比较，没有临时排除列。
- shadow 必須存在并逐步完备；非 shadow 若生成目录中含 shadow 名称的文件即失败。eab 的独立读取门进一步严格检查 header/schema/end、各行列宽与类型，而非只信捕获器的轻量包络检查。
- 计时协议顺序串行执行，每轮循环轮换 baseline/unset/legacy/shadow 的先后，第一轮暖机不入统计，保留全样本与中位数。所有计时包含独立进程启动及四类 CSV 输出；不是纯检测函数微基准。没有 `--quiet-machine-confirmed` 时拒绝计时。

机器证据：[review_R6_checks.json](review_R6_checks.json)。真实文件的 450 份产物哈希复核另见 R5。

## Minor R6-01：复跑不能直接使用已占用的固定 BASE

`BASE=bdda2/build/m4b` 与 `dest.mkdir(exist_ok=False)` 会使同一 baseline/compare/timing 原命令第二次运行因目录已存在而失败。这是保护旧证据的正确 fail-closed 行为，不应删旧目录或悄悄覆盖来“解决”。

建议在最终报告明确复跑布局：在同一授权工作树的 build 下另建带日期的新目录，先复制原 `baseline/` 的冻结源档、manifest 与 exe，再将捕获模块的 BASE 指到新目录，按 baseline → compare 运行；不要改 HEAD、不要覆盖旧证据。可在后续独立工单增加显式 `--out-dir`，本工单无需为便利性扩大接口。

## 剩余风险与待补

- quiet_machine_confirmed 是操作者确认，不是系统空闲监控证书。最终必须在其他编译、pytest、回放计算停止后执行；初审时 timing.json 不存在；现已按末节完成实测复核，保留历史阶段区分。
- exe 摘要按捕获阶段记录，而不是每次运行前后都复核。如果未来并行重编译同名 exe，必须重新建立安静/冻结条件；本次实际 exe 与矩阵摘要已吻合。
- 捕获器的 all_pass 便于编排，但退出结论还必须经 R5 的直接摘要对比及原始文件复核，不能只读取一个布尔值。
- 本审查不验证 contact force 的物理意义，也不批准 eab 真替换。

## R6 复核更新：复算入口已补齐

捕获器已增加 `--evidence-dir`，顶层目标 resolve 后必须位于当前工作树 `bdda2/build` 内。只复制已冻结的 source_manifest/source_snapshot 两个锚；若新目录里已有同名锚，必须逐字节相等，绝不覆盖不同锚。运行目录仍用 exist_ok=False，保护旧证据。

实际在 `bdda2/build/m4b/rerun_verification` 新目录重新跑完 **30 次 baseline + 45 次 modified**；审查者随后独立读取新目录的 **450 个产物和 15 个 shadow 快照**，重算长度/SHA256，并与原矩阵比较，全部相同。机器复核已加入 review_R6_checks.json。捕获代理另实测旧目录拒绝且旧 manifest 不变、build 外目标拒绝且外部目录未创建。

因此 R6-01 原“无显式复跑目录”minor 已关闭，不再要求调用者改模块全局变量。当前最小复跑命令为：

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -X utf8 tools/bdda/verify_m4b_shadow.py baseline --evidence-dir D:/bdda-wt/shadow/bdda2/build/m4b_rerun_NEW
python -X utf8 tools/bdda/verify_m4b_shadow.py compare --evidence-dir D:/bdda-wt/shadow/bdda2/build/m4b_rerun_NEW
```

必须从 b-DDA 授权专用工作树执行；NEW 换成尚不存在的名字，不删除旧证据。

## R6 最终复核：内部 junction 范围逃逸也已拒绝

新增参数初版只约束顶层 evidence-dir；审查提出其内部 baseline/运行子目录如被预置 junction，仍可能把后续创建路径重定向出授权 build。最终版本用 `inside_build` 对每个 anchor 目标、run_one 目标及 persist 文件的最终 resolve 路径再次校验，不只检查字符串前缀或顶层目录。

捕获代理实际构造指向系统临时空目录的 baseline junction，运行被拒绝（RC2），临时目录仍为空；运行子目录和 manifest 目标也会被拒绝。审查者独立读回该外部临时目录，确认为空。负门链接清理被工具策略拒绝，未绕过；空链接与空临时目录保留作证据，不涉及受保护主工作树。

最终 guard 版本又在 `rerun_verification_v2` 新目录完成 30+45 次运行；审查者再次独立重算 **450 个产物 + 15 个完整 shadow**，全部与原捕获相同。当前脚本 SHA256 为 `bc66898ea0372d59c33213bc92c9e60789d2142d05165f6679203ee33950e497`。机器记录在 review_R6_checks.json 的 evidence_dir_junction_guard_rerun 节。R6 代码范围内未剩 critical、major 或 minor；安静计时的最终实测复核见下一节。

## R6 最终计时实测复核（2026-10-13 16:08:17–16:08:29，UTC+08）

审查者只读核验 b-DDA 的 timing.json/timing_environment.json，及复制到 eab evidence 的两份文件；两侧逐字节相同。独立检查两算例 × 8 轮 × 4 模式，共 **64 次运行**：每个算例/模式有一条暖机和七条正式样本，正式样本总数 **56**。逐轮模式顺序确按轮号循环旋转；暖机只在第 0 轮并已从统计中剔除。审查者用排序取第 4 个样本独立重算每组中位数，核对原样本向量、相对基线比率，全部一致。

此外独立重算本轮 **384 个产物文件（64×6）及 16 个 shadow 快照** 的 SHA256/长度，全部与计时记录一致；每个算例的四种模式各次运行产物摘要完全相同。两种 executable 的现场哈希也与原 byte matrix 相同。

| 算例 / 时程 | baseline 中位数 ms | unset 中位数 ms | legacy 中位数 ms | shadow 中位数 ms | shadow 相对 legacy |
|---|---:|---:|---:|---:|---:|
| bb52 / 50 步 | 27.3127 | 26.7524 | 27.8039 | 42.4501 | +14.6462 ms / +52.6768% |
| W100 / 20 步 | 299.8645 | 293.2776 | 293.7185 | 329.3948 | +35.6763 ms / +12.1464% |

shadow 相对改前 baseline 分别为 +55.4226%、+9.8479%；比较分母不同，不应混写。

unset/legacy 相对 baseline 的中位数变化为约 −2.20% 到 +1.80%，样本范围重叠。它们没有在本轮显示明确、稳定的额外耗时，但七条有噪声的整进程样本**不能证明绝对 0 CPU 开销**；零影子分配/序列化/回调仍须依赖代码路径与相应变异门，而不是以计时替代路径证明。这里计时含新进程启动及四个 CSV 的写出，不是单独检测函数微基准，也未把后处理 eab 回放计入 C++ shadow 序列化开销。

采样前 root 声明并停止代理的编译、pytest、回放等计算；环境证据记录所有其他代理完成、无代理测试/构建并行。本次没有终止用户日常程序，ASUS InfoHub、ToDesk、msedgewebview2 在约 11.82 秒窗口内分别有 1.953125、1.390625、0.921875 CPU 秒增量。因此只能称“代理任务安静窗口”，**不能称绝对系统空载**。这些后台进程不是本任务违规的并行计算，但会构成测时噪声。

- timing.json SHA256：`2fd11e062a103c6b666012ded0c336700126014390936107215cf91dfa272abe`
- timing_environment.json SHA256：`540fe3c8307b660e89acd486c6cd2d94ccab1dde76b1d4fb27433c065fe7486b`
- 审查实算结果、样本范围和 hash 核验计数：[review_R6_checks.json](review_R6_checks.json) 的 final_timing_review。

本次只更新 R6 审查 Markdown/JSON，没有修改源码、测试、夹具或原计时文件。R6 最终状态保持 **0 critical、0 major、0 remaining minor**；上述正常宿主负载及计时解释范围保留为明确限制，不被隐去。
