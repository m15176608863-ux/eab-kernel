# M5c A5 独立审查与 A7 闭包边界复核

## 结论

- 第一轮发现 **1 major**：把普通 VE 的锁长提示误计为第二三点参考；已修复，旧全程 r1 已明确作废、没有拼接复用，r2 已完整重新计算并发布，最终联合核验通过。
- 目前代码审查未决：**0 critical、0 major、0 minor**。这不是尚未完成的 r2 全程发布验收，也不是 G6 六路退出结论。
- 另一路审查者指出 A7 集合期望复用生产 scanner 的薄弱处，已用独立 import spec 枚举与真实内部遗漏变异补牙，仅修改测试，未触及冻结运行闭包。

## Major：m4>0 不等于第二参考

反例：`bb03 / step 1 / raw_df05` 的原始行 `[0, 2, 17, 23, 3, 0, 0]`。
旧实现会生成 `('VE', 3, 0, 0)`，既是退化边又不是对块参考。相同错误每阶段污染 **49218** 个额外参考计数。

只读核对姊妹文件 `D:/b-DDA/df/df.c`，SHA256 `a097a636990aee34cd0c2f856aa52a81c12e9ba9136f233004719be91158fcee`：

- 1605–1617：普通 VE 的 m4/m5 是锁长两侧点提示，m6=0，不是完整参考。
- 1626–1649：mtype=0 的共边入口候选填完整 m4–m6，m6>0。
- 1660–1681：mtype=1 的 VV 具有正式第二三点参考。
- 1832–1853：df06 可以交换完整的主/共边三点槽。

因此修后分开 `secondary`（正式 VV）与 `shared_edge`（有效共边槽），并验证点/边属于同一块对、点在对块、边同块相邻且非退化；完整但非法槽响亮失败。`FORMAL_ALL`=主参考+VV 二参；`ALL` 另含有效共边槽。**共边候选命中不冒称被主参考选中。** bb03 的首盖位于同一 raw 行的共边槽，保留这一事实；不能简单只保留 mtype=1。

独立 oracle 以连续 padded ID 的周期索引构造 alias，未调用生产几何或 alias helper；读取所有冻结 1810 帧、15220 块、两阶段 283188 行，逐行交叉核对修后生产解码，**0 失配**：

| 每阶段 | 数量 |
|---|---:|
| 主参考行 | 141594 |
| 正式 VV 二参 | 7768 |
| 完整 VE 共边槽 | 32075 |
| 两类有效额外槽合计 | 39843 |
| 旧 m4 判据误计锁长提示 | 49218 |

可重跑：`python tools/m5c_audit_legacy_slots.py --check-production`。输入与审查脚本 SHA256 冻结在 `a5_independent_legacy_audit.json`；该脚本不依赖姊妹源码或 exe，源码说明只是已核对的来源证据。

## 分母与初态交叉核对

代码路由相互排斥：`EXPLICIT_TRAJECTORY`、`CONSTRUCTED_INITIAL_CONTACT`、`CONSTRUCTED_INITIAL_OVERLAP`、`CERTIFICATE_DIRECT`。前两项都真实调用生产 P1/P2 并核对初态；贯入只由独立初态 oracle 构造状态，不能算生产交叉核对；直接证书不运行初态 oracle。

应有统计为 14079 / 213 / 16676 / 33042：生产初态交叉核对 14079+213=14292；独立初态评估 14292+16676=30968。14079 个真正轨迹比较内本步新接触 68。最终数字待完整 r2 输出再验证，未提前认定旧摘要已符合。

## A7 边界与证据链

- 干净解释器实际闭包：端点 29、稳健 21 文件。逐 AST 检查未发现动态 exec/import loader、`sys.modules` 卸载/改写；唯一 registry 使用是只读 snapshot。
- 现有几何 lazy imports 目标已在起始闭包；端点 midpoint 的 lazy imports 已预加载；`m5a_se2_replay` 中未执行的 ingest 分支不属于本次实际运行依赖。若实际计算新增普通 lazy import，结束集合不等会拒绝发布。
- 不主张防御任意第三方手工卸载模块或瞬间修改又恢复文件；合同是给定执行路径的首尾完整仓内源码快照。
- 独立 `module.__spec__.origin` 枚举不调用 production scanner。端点/稳健各把生产 dict comprehension 改为漏掉 `numeric_domain.py`，红在 `M5c independent import origins require every transitive source`，不靠冻结源码哈希绊线。
- 已完成的端点 r1 摘要真实发布、29 项起止闭包与当前源码一致，专项门 `1 passed in 0.22s`。
- 旧 robust r1 的作废记录明确 `valid_evidence=false`、`reused_results=false`。新 r2 仍在完整运行；必须等其结束、全量源/输入/行输出哈希通过、四片通过后才发布最终验收。
- robust 发布代码先备份目标旧字节，结束再次比较目标未被并发改变，仅全部算例允许 publish；各 worker 完成才累加。未发现复用中断片段的路径。

## 新测试及验证

`tests/test_m5c_accounting_review.py` 14 格覆盖锁长提示、VV 与共边区分、合法 0 号边端、wrap alias、非相邻/退化/同块/跨第三块非法槽、正式与全部参考区分、缺块对与未选首盖区分、重复行计数、ID 重编号与块顺序不变性。

与绑定门合跑：`30 passed, 2 deselected in 1.83s`；剔除的两条是依赖最终冻结摘要的门，不能充作全套收集=执行证据。新增/修改的两份测试生产静态扫描均 0 违例。

机器记录：`review_a5.json`。最终待办仅为 r2 完成后的证据核对与全套门；本审查未修改任何冻结生产闭包。

## 真实重算发布后的最终核验

完整 R2 已实际完成并发布（1810 步、15220 块帧、64010 对），15 个 worker 的 21 项源码首尾映射与父进程完全一致；旧 r1 作废且未拼接。冻结 publisher 实际执行成功并发布 `combined_summary.json`：逐对重核旧/新 64010 个 P1/P2 精确状态、特征、时间，68 个研究候选齐全，单首盖由 2 增至 19（净增 17）。所有绑定/联合及对应会计门含真实冻结产物全绿：`130 passed in 5.48s`，0 skip、0 deselect。

端点 29 项、稳健 21 项完整闭包门及最小例重算门均已执行，不再保留早期待发布剔除项。初态贯入 16676 对每阶段参考计数为主参考 81209、正式 VV 二参 2001、共边候选槽 19785；仍为 0 个出口排序证书，计数不代表出口命中结论。完整四分片收集=执行与静态总门由主代理最后发布。

可核验记录：`combined_publication_verification.json`、`combined_publisher_freeze.json`、`binding_combined_actual_r1.log`。
