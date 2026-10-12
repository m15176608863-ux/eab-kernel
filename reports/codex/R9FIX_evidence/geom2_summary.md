# R9FIX 二维 G6I-01 证据小结

## 结论与改动

修复凸路径仅按无限支撑直线根选标签而漏有限源特征域的问题。`entrance.py`：精确同向共线支撑先分组裁剪，保留原始 facet 标签；到达精确时刻后，VE/EV 核投影位于源闭边，FF 核真实闭段投影重叠；获选、精确并列及 near 报告均只回映有效源标签。VE/EV 见证去掉 clamp。公开 `entrance_block_exact` 的分段、标签数量契约不变。`covers.py` 与 `entrance.py` 最终 exact→float 输出迁移到统一 `scalar_rational` / `vector_rational`。

## 修前红 → 修后绿

- 新增门：[test_r9fix_entrance_domain.py](file:///D:/eab-wt/cx-e2/tests/test_r9fix_entrance_domain.py)。独立 oracle 只用原坐标 Fraction 行列式与闭区间，不调用生产 Minkowski、法锥、段域或见证函数。
- 输入变体：VE 与交换后的 EV；接触横坐标 1/2、1、3/2，包含共线分界双标签；尺度 1、1e-9、1e8；精确 3-4-5 旋转与 1e8 平移；合法 FF 初态及不等长共线链。
- [修前日志](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/geom2_red.log)：`27 failed, 8 passed in 0.43s`。目标断言 `assert set(result.tied_labels) == expected`；实际 `{('VE',0,2), ('VE',0,3)}`，期望 `{('VE',0,3)}`，选中错误 `('VE',0,2)`。FF 输入在旧 witness 构造处报 `convex entrance face witness has no segment overlap`。
- [首轮绿日志](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/geom2_green.log)：`35 passed in 0.09s`。
- 加入真实路径变异门并迁移统一构造后，[定向总日志](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/geom2_targeted_final.log)：`1152 passed in 52.80s`。包括新 36 格与既有 entrance、E3、exact、invariance_2d 模块。

## 变异的牙

[可重跑脚本](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/run_geom2_mutation.py) 在进程内把生产 `_facet_in_domain` 设为恒真，从获选前内部检查处去掉修复，不修改返回记录、不追加假数据、不写生产文件。

[变异日志](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/geom2_mutation.log)：`16 failed, 8 passed, 12 deselected in 0.18s`。全部失败是 `finite source edge labels` 精确集合断言；域端点双标签 8 格仍绿，不是偶然 witness 或求解器选择断言。新常驻 `test_finite_domain_gate_has_teeth_inside_the_selected_feature_path` 也执行此路径并核命中目标 AssertionError。

## 同类扫描

| 路径 | 审查结果 |
|---|---|
| 凸 first_entrance 的 selected / tied / near | 本次修复，不再把共线支撑全体标签当有限接触标签 |
| 凹 first_entrance | 原有 Fraction gap=0 与 projection∈[0,length²]；selected、tied、near 均核域，未发现同类遗漏 |
| shortest_exit | 构造候选前已精确核 g≤0 与投影域，排序和 ties 从该候选表取 |
| covers.enumerate_covers / first_entrance_for_vertex | 已使用 `_in_segment_exact`；tol/seg_tol 为显式窗口；require_in_segment=False 是候选枚举显式模式，入口随后在实际位形复核 |
| local_facets / ambiguous_facets | 枚举平移无关的有效源盖，不声称当前配置接触，不应误加当前投影域 |
| membership / 报告带 | 支撑半空间判状态；非零带使用有限 E 边界闭段距离，不选接触标签 |

将审查方 150 对 polyomino 压力脚本复制到本树证据目录并加强：每个成功首入以独立有限域 oracle 核所有精确并列和选中标签、核两侧见证同点，原 FF 异常捕获最终要求为空。没有减少原网格。

- [加强脚本](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/geom2_independent_stress.py)
- [压力日志](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/geom2_stress.log)：150 对，4320 E 成员、2160 body 状态、2160 entrance、1441 distance、2 cache；`known_finite_facet_domain_errors=[]`。旧审查只有 2137 entrance、23 FF 异常，本次全部完成。

## 测试改写台账与边界

没有删除、放松或改写既有测试；只新增 36 格与加强证据脚本。统一构造迁移不更改分支判定。homogeneous atan2 的两个中间分量允许舍入下溢以保持可表达角（如 pi/2），但非零最终角为 0 仍 loud；未承诺超越平台 atan2 的超越函数正确舍入。

本小结不是全套结论；全套、文档指针更新与总报告由 root 汇总。未执行 commit、push、reset、checkout、stash、worktree，未修改其他工作树。下一轮独立 G6 退出仍待正式复审。
