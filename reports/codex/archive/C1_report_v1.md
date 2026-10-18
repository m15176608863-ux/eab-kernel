# WO-C1 交付报告

2026-10-19｜`eab2-design @ 1ce9a91760e22cab7e471e76c39dcc2b786eb6ab`｜仅设计，未写产品代码。

## 文档与目录

[eab2 中文设计](file:///D:/eab-wt/cx-c2/docs/eab2_design.md)：§1 范围与版本；§2 数值；§3 编译；§4 可微；§5 API；§6 性能；§7 差分；§8 里程碑；§9 风险 / 决策；§10 来源与验收索引。

## 五条关键推荐

1. v0 一般凹二维 E/O、平移 / P1、PD/rho/平移锁定；v1 TIA LP 与敏感性；v2 五 / 六次事件。rho、锁定与完整界面装配须先补 Python 裁判。
2. Boost `cpp_int/cpp_rational` 私有封装；浮点过滤、精确回退，整数中点判定保证构造 RN-even，不自写大整数。
3. 精确标签 / 原值与 `Dual<W>` 连续导数分轨；LP 默认基点锚定连续模型，退化 / 并列显式报告，不混用不同 LP 的 x/y。
4. 受控 C++20 数值目标 + 稳定 C ABI / ctypes；独立实现 Dual，姊妹零代码依赖。TIA 多模态未解析不得强行叠加法向约束。
5. 主保证为 Python 差分与元门，不移植 AST 门、变异充分性框架、源码哈希绊线；单名预审不替代现行 G6。

## 微型测量与性能边界

只读盘点 15 例 × 30 帧：25,295 条 post_df06 行，每帧中位 54、最大 156；块数中位 10、最大 12。盘点约 0.192 s，**不是几何测速或 C++ 成绩**。建议目标：DDA 行级 P95≤10 ms；20×40 非凸 TIA 的 31 邻接 E + 20 固定邻体锁定≤5 s，均待实施实测。

[复跑脚本](file:///D:/eab-wt/cx-c2/scratch_eab2/inventory.py)｜[规模 JSON](file:///D:/eab-wt/cx-c2/scratch_eab2/replay_size.json)。scratch 全部不入库，关键数据已写入设计。

## 验证与待决

三路设计专项复核归并 4 项 major，修订后原核查员均确认闭合；不是产品 G6。UTF-8 无 BOM、目录 / 本地链接 / JSON 示例 / 改动范围审计通过。当前树全套 **13,877 passed，0 失败 / 0 跳过，收集=执行**；pytest 3799.51 s。未改 src/tests/tools，未对姊妹树写入或执行 Git 写操作；没有新建 worktree，不宣称新鲜 checkout 退出。[验证与复跑记录](file:///D:/eab-wt/cx-c2/scratch_eab2/README.md)

请决定：Python 前置工单、TIA 机械 profile 与梯度模型、Boost 分发、真实性能基准；完整 M5d 是否前移。DDA 主线接入仍需另行批准。详细 D1–D9 见设计 §9.2。

C1_DONE
