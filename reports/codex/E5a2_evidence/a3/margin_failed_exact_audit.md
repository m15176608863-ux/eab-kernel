# 最终失败全套：41 个 margin 节点的独立精确分类

## 结论

**41 / 41 个失败节点的实际输入都有严格实体内部重叠，独立精确状态均为 `1`。** 这些节点返回 `PENETRATING` 哨兵是正确行为；失败来自旧门仍将理想相触或亚容差真贯入强制当作非贯入边界。没有在这 41 格发现新的生产关系判定缺陷。

这是只读失败分类，不是已完成的测试迁移。source/tests 均未修改；最终全套 `49 failed, 7953 passed in 1566.87s` 的事实不变。本审计不处理余下 8 个失败，也不是 G6。

## 完整覆盖

从 `final.xml` 自动读取 `test_invariance_interlock` 下所有失败的 `test_margin_*` 节点，断言恰为 41 个，逐节点审计，无手工筛除。

| 失败组 | 节点数 | 实际精确状态 | 分类 |
|---|---:|---:|---|
| `test_margin_reference_cases_are_what_they_claim` 的 subtol 参考输入 | 1 | 1 | 原输入就是深度约 3e-10 的真贯入，正报告带不能吞掉内部 |
| `test_margin_layer_is_rigid_motion_and_unit_invariant[subtol-...]` | 26 | 1 | 全部所列失败变换格仍保留了真贯入 |
| 同门 `touch-q4-...` | 9 | 1 | 全部原 q4 旋转 × 3 平移 × 3 尺度的舍入后输入发生严格微贯入 |
| 同门 `touch-q6-...` | 5 | 1 | `t=1000,s∈{0.001,1000}`；`t=100000,s∈{0.001,1,1000}` 的舍入后输入发生严格微贯入 |

未失败的 touch/subtol 格不在本次 41 节点分类范围内；不从“未失败”反推其真实三态。

## 独立性、前提与证书

复用原测试 `MARGIN_CASES` 的 factory 和 `_rigid` **仅生成完全相同的 raw 坐标与源面环**；不复用生产法向、三角化、射线、SAT、距离、凸包或关系判断来决定真值。

真值使用 `tests/e5a2_surface_oracle.py` 的独立星形闭表面四面体并集法：

1. 明确核对每条源无向棱恰出现两次且方向相反；无重复面内顶点。
2. 独立投影检验这些 box 四边面环均严格凸，保证简单非退化环前提；tet 三角面亦非退化。
3. 每个实际舍入表面都找到严格星核点。对全部独立三角片验证核点位于朝内严格半空间，记录最小正有理平面余量。
4. 对从星核到三角片构成的四面体进行公共分母整数化，再以独立整数 SAT 分类四面体对。
5. 每节点保存第一对严格相交四面体索引、公共坐标分母、检查过的非零 SAT 轴数和所有 primitive 整数轴上的最小严格正投影交叠。由于四面体位于对应实体内，该严格相交证书足以证明实体内部重叠。

全部 41 个输入的上述前提和严格内部证书通过；没有以正容差、采样密度或浮点 epsilon 判内部。

## 生产返回的只读交叉核验

在独立真值确定后，另外读取生产返回，逐节点全部满足：

- `polyhedra_overlap(A,B,0) == 1`；
- `body_distance(A,B) == (0.0, ('PENETRATING',))`；
- 对 `delta ∈ {0, 0.01*s}`，`margin_contacts` 恰有一个 `PENETRATING` 哨兵，`closed=True`、`distance=0`、`margin_gap=-delta`；
- 两个 delta 的 `inflated_membership == INSIDE`。

这些交叉核验只是生产字段检查，不参与 oracle 真值构造。

## 后续迁移建议，未应用

- `subtol` 不再归入“必须非贯入的 contact”分组；是否真实贯入必须按该格原始浮点坐标的独立精确证书判断，不能按名称或变换前意图决定。
- `touch` 原全部旋转、平移、尺度格仍须保留；每格核自己的精确三态，不将理想运动前的相触强加给运动后的舍入实体。
- 对这里已证明 state=1 的格，保留距离恰零断言，并加强为唯一 closed 哨兵、`gap=-delta`、`INSIDE` 的完整字段门；不能删格、改参数、接受任意异常或仅放宽零距离阈值。
- 迁移其他仍为 state=0/-1 的格时，必须另做独立真值与报告带核验；不能用本审计覆盖未核的格，也不能把生产谓词当自己的 oracle。

## 证据与复跑

- `audit_margin_failures.py`：独立审计脚本，只写本 evidence 目录。
- `margin_failed_exact_audit.json`：41 个完整 node、raw 顶点 hex/面索引、输入 SHA256、严格星核及内部相交证书、生产字段和源文件哈希。
- `margin_failed_exact_audit.log`：汇总 `41` 个 state=1；subtol 共 27 节点（含参考格）、touch 14 节点。
- 独立审计耗时 `0.6738861000048928 s`，不是全套性能结果。

复跑：`PYTHONDONTWRITEBYTECODE=1 python -X utf8 reports/codex/E5a2_evidence/a3/audit_margin_failures.py`（PowerShell 应以环境变量赋值形式设置）。

本子任务已完成，无运行中的 CPU 任务。
