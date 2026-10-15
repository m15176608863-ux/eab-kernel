# WO-M5b §2 子任务：P2、六次根与全时程位置误差界

## 已交付与边界

- [核心实现](../../../..//src/eab/kernel2d/dda_motion.py)：面积形心、对称常应变、含严格误差界的有理半角近似、P2 坐标/坐标多项式、精确六次首入、P2/P3 全窗位置上界、保守投影包围。
- [理论](../../../../docs/m5b_motion_theory.md) / [数值合同](../../../../docs/m5b_numeric_inventory.md)：T1–T6 定义、证明、支持域与具名门。次数扩展只改 `algebraic.py` 的输入上限，Sturm/gcd/精确符号机制不变。7 次依旧明确拒绝。
- [30 个新增门](../../../../tests/test_m5b_motion.py)、[独立 oracle](../../../../tests/m5b_independent_oracle.py)：不导入生产几何/旋转/事件生成/代数根原语。全首入差分含双体六次事件和凹环；六次根包括一个六无理实根多项式的完整分支。
- 研究支持域：单简单环；每块精确首入要求 `2||E||∞<1`，这是充分条件；`|u1|<=1`；由 theta 构造时 `|theta|<=1` 弧度。不支持域响亮拒绝，不以未证当无接触。
- 未实现 P3 超越首根求解，仅给出规定 P3 相对于 P2 的解析全窗误差界；不恢复未知 DDA 物理路径。P1 退化逐值相等指 P2 自身精确端点的弦，不偷换成已舍入实测末帧的弦。

## 数值原理摘要

`c` 用有向面积矩；`E12=gxy/2`。交错有理 Taylor 包住 sin/cos，给 `tan(theta/2)` 区间；有理网格取 `u1`，误差 `epsilon=max(|u1-l|,|u1-h|)`。因此不依赖 libm 舍入假设。

每坐标分子至多三次，分母 `D=1+u1²s²>0`。VE/EV 叉积及两个线段投影原始分子共有正因子 `D_B`；精确除法检查余数为零后次数至多 6（刚体至多 5），不增删实根或符号。首入使用同一一般路径，包括 theta=0、E=0、恒共线与闭窗端点。

全窗偏差为 `max_p ||p-c||1 * (|u1|³/2 + 2 epsilon)`：第一项来自 `2atan(su1)` 对端点线性转角的二阶插值余项，第二项来自 atan 的 1-Lipschitz 性。不把端点舍入误差藏在该界内，端点误差须额外累加。

## 语义变异

四项均由测试专属 `mutated_function` 重新编译**生产函数源码体**，不改磁盘、不向最终结果追加假数据。测试驱动显式期待相应语义 `AssertionError`；这些驱动不运行来源哈希断言，故哈希绊线不能代替语义门。

| 内部缺陷 | 被杀死的语义断言 | 门 |
|---|---|---|
| 丢弃真实非零六次事件项 | `sixth-term semantic first-root identity` | `test_losing_the_sixth_event_term_is_killed_by_the_first_root_semantic_assertion` |
| 非对角剪切系数翻倍 | `shear semantic coordinate identity` | `test_shear_mutation_is_killed_by_coordinate_semantics` |
| 面积形心错用顶点均值 | `area-lamina semantic centroid identity` | `test_area_centroid_mutation_is_killed_by_independent_lamina_moments` |
| 删除有理时间律与线性转角的差异项 | `time-law semantic all-time deviation bound` | `test_missing_time_law_bound_is_killed_by_independent_p3_interval` |

这不是独立隔离副本的全套变异运行；它是具名、源码体内插桩、已核对失败断言的局部门。主报告不得把局部门当 G6。

## 验证与协作审查

最新命令、最后一行、耗时、SHA256 在 [p2_work.json](p2_work.json)，逐行输出在 [p2_gates.log](p2_gates.log)。只跑 P2 的记录为 `30 passed in 0.98s`。M5a 代数/SE2/独立 oracle 作为兼容回归一并运行，最终结果以 JSON 和日志为准。

所有 pytest 使用 `-p no:cacheprovider`、显式 `--basetemp=reports/codex/M5b_evidence/tmp/...`，进程 TEMP/TMP 同在本树该目录。生产文件最终稳定后已通知主线程启动全时程真实重算；之后只补测试/理论/本证据，不改生产闭包。四片总耗时、静态逐站准入、冻结重算及总工单 PARTIAL 清单归主报告。

另外对主线程 `model_robustness.py` 与 `docs/m5b_robustness_theory.md` 做了只读协作审查：逐项核对双线性管误差、所有非邻顶点的严格凸性、一般分母商导数、两端符号和竞争事件排除，未发现可使假稳健通过的问题。此协作审查不是独立六路 G6。初始贯入的未证标签来自更宽扰动管的保守边界，不代表三种名义模型在 s=0 的位置不同。
