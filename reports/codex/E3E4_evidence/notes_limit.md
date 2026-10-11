# E4 实施与证据

## 实现与可审计边界
- LPResult 新增 exact_x/exact_y 元组，仅保留证书见证，不改 LP 算法。
- alpha/lambdas/mechanism/row_duals 仍是 float 兼容视图，附不可变 exact Fraction。list/copy保留，算术、float()、JSON往返不保留；舍入显示值不得假称精确可行。修改项按新给定数核。
- 所有见证仍逐项在独立重建模型核；毒化原始/对偶见证、非有限、纯float手改、Fraction1e-100均有门。
- `_check_columns`只共用锥方向模型定义；力矩独立行列式重建，不调用LP `_exact_wrench`/`_exact_shift`；忘参考点/忘反作用牙仍绿。
- 静力、λ非负、黏聚行、α非负、功率、drive>=1、强对偶、每项互补均有理数精确。tol只兼容；*_rel只显示，不决定答案。contact_forces/active为截断展示，静力证书是lambdas。
- 删除无调用的_dot/_adot/_powers/_speed_scale/_scales；保留_norm供报告。
- 多体分辨性采用各体自己的接触形心与臂长；保留本体调用方原点构造荷载的噪声距离项，不计无关体跨度；局部扰动精确移回LP公共原点。

## 可分辨性不改答案
旧筛查曾用邻域infeasible替换原问题，或对精确有限答案抛“不认证”。与工单原则冲突，本单统一移除。
Result新增resolvability/statuses：resolved、nearby_infeasible、unresolved、not_applicable；原status/alpha始终保留精确LP答案。resolved只是单机构筛查未发现超阈变化，不是稳定性证明。
原测试输入全部保留，改成原问题精确闭式/独立有理数oracle与对应报告双重断言。tests/test_lp_certificates.py由入口代理另交台账。

## 八项发现
逐项见limit_dispositions.json，附原脚本、e1fbbd4输出、当前输出、新门和修前红断言。
limit.py:206已由aadc40e消解；其余本单修复/加强。tests:268基线关闭unbounded筛查仍53绿；同一内部源码突变在新两分支×body0/1门上4条报告断言红。

## 测试与突变交接
- 新门修前：43 failed, 4 passed in 0.51s（limit_new_gates_baseline.txt）。
- 首轮原有门8失败逐node登记limit_test_changes.json（7拱链oracle舍入；1三维sin/cos非精确单位）。
- 241 passed in 4.72s（limit_final_targeted.txt），之后按工单增加原selfcheck的任意k注入，单/多体原门109 passed in0.65s。
- 筛查新策略154 passed in7.26s（limit_report_strategy.txt）。
- limit_mutations.json给D8/D9/D10精确源码替换与目标门，主代理统一执行。D9可能良性逃逸：精确原/对偶可行+每项互补已经蕴含强对偶；不得为了造红削掉独立互补。

## 遗留
未经六路G6，不能声称里程碑退出通过。数据不确定性、几何非线性、离散锥误差不属精确算术保证。显示序列化后若需要复用证书，应显式保存exact有理数；普通JSON只保存float显示值。
