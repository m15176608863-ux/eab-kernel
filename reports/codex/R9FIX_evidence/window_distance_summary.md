# R9FIX 全套集成暴露的窗口距离构造同类问题

## 失败分类与根因

首轮全套的 68 格 `test_margin_labels_are_identical_under_rigid_motion` 失败不是实体法锥补修引起的标签错误；标签集合与数量均正确。独立 oracle 已迁移为精确见证坐标相减后只构造最终范数，但 `contact_window` 显式旧报告路径仍把已经舍入的全局 `point_a/point_b` 相减求范数，并将该诊断显示距离当最终答案。这是 G6I-03/04 同根的“先分量舍入再构造最终标量”。

典型原格：sep_ve3 / q4 / t=1000 / s=0.001，标签 VE3(vertex3,edge2,3)。生产输出 0.00026700749058721407，独立精确输出 0.00026700749058706575；差 1.48318857196017e-16，大于原断言 4 ULP 上限 2.168404344971009e-19。生产自身 exact_distance_squared 也无法为旧输出提供 Fraction 中点证书。

## 最小修复，不削弱旧门

只改 `src/eab/margin.py` 最终构造：window `body_distance` 与 `margin_contacts` 返回的距离也一律从已计算的精确 d² 经统一 sqrt 构造。默认精确排序不变；调用方显式窗口的历史并列报告策略保留。

不能直接把 `cover_witness` 的诊断距离换成证书距离：那会掩盖真实见证点坐标错误，令既有自检失牙。因此保留该显示距离与全部自检，将文档明确为“显示见证构造误差诊断”，不再把它当最终源特征距离。

既有测试未修改、未放松、未缩网格。

## 红绿、证书与变异

- [新中点证书门](file:///D:/eab-wt/cx-e2/tests/test_r9fix_window_distance.py)：3 个原失败位姿分别核 window contact 与 body 最终距离；独立 Gram/triangle oracle 构造精确平方，Fraction 相邻中点直接认证最终 float；另 1 格真实内部变异。
- [修前红](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/window_distance_red.log)：`3 failed, 1 deselected in 0.32s`，目标 `window-distance-exact-midpoint` 断言。
- [修后绿](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/window_distance_green.log)：全部原 label 网格与新增门，`166 passed, 414 deselected in 21.52s`，原 68 个失败全部消除。
- [旧自检牙](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/window_distance_old_teeth.log)：`6 passed, 61 deselected in 0.27s`，含真实点误差、相对 ppm 误差、50/2 舍入单位阈值，不仅是新门绿色。
- [真实内部变异脚本](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/run_window_distance_mutation.py) / [变异红](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/window_distance_mutation.log)：编译真实 margin_contacts 函数，仅恢复旧 contact_window 条件，让该路径绕过最终精确根构造；`3 failed, 1 deselected in 0.27s`，全部命中 `window-distance-exact-midpoint`。

另跑 margin_resolution + R7geom3 时有 102 通过、2 个 EE 参数下溢失败；后者路径在 covers3.scalar_rational(s)，由 root 的 exact_params 显示证书补修负责，与此次窗口修法无关。原日志保存为 [window_distance_selfcheck.log](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/window_distance_selfcheck.log)，不冒充全绿。

完整原模块重跑已完成：`576 passed in 180.19s (0:03:00)`，结果见 [window_distance_module.log](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/window_distance_module.log)；总报告以 root 最终冻结全套为准。
