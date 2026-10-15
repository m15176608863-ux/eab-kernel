# INT1 第 4 条：数值、几何与回放语义门

## 结论与范围

新增 `tests/test_int1_semantics.py`，29 个 pytest 节点；13 个真实内部变异全部由预先指定的语义断言杀死。
没有修改任何生产算法，也未改写冻结夹具。待补项是**看护门缺口**，本树原有正确实现已经具备二次式区间筛选、保守 L1 扫掠半径、模素数适用条件、精确细化与闭区间端点处理。

统一调用 `tests/mutation_support.py`，不在新测试中复制 `inspect / exec / compile / vars` 脚手架。
控制组与变异组运行**之前**，均将两个 replay 模块的 `code_hashes`、`file_hash` 回调屏蔽；输入的几何摘要仍正常核对。
变异在实际函数体内部、执行之前注入，退出作用域后恢复；不追加伪产物。

## 门与确切变异

| 条目 | 独立语义与夹具 | 注入缺陷 | 结果 |
|---|---|---|---|
| 二次式分支区间（major） | 顶点 `(-1,7)` 到直线 `y=5`，事件 `2−2s−12s²=0`，根为 `−1/2,1/3`；完整 `se2_first_entrance` 应输出 `1/3` | `as_rational` 二次式区间条件改成 `True` | 控制正确；变异输出 `−1/2`，首入时刻断言红 |
| 非形心旋转中心（major） | 围绕任意全局中心旋转、但局部顶点集中 `(1,1)` 的薄三角形；三个小角、三种尺度及大平移；独立有理旋转展开验证包含 | `_swept_bounds` 的 `abs(x)+abs(y)` 改为 `max(abs(x),abs(y))` | 控制为真实接触；变异误报 `no_contact`，端到端接触断言红 |
| 模素数前提 | `(p x−1)(p x²+1)`，`p∈{2,3,5}`，根 `1/p`，模 `p` 为常数 `−1` | 删除“素数整除首项系数则跳过”分支 | 有理根恢复断言红 |
| 细化宽度 | 两个大分母；区间中点位于 Farey 中界之外 **gap/8**，绝非平局 | `1/(2B²)` 改为 `1/(2B)`；另改为 `2/B²` | 两变异均错误返回 `None`，指定有理根恢复断言红 |
| 闭上端点 | `(3x−1)(x−2)` 在 `[0,1/3]` 的唯一根；同时核对退化区间、细化、符号及双根区间拒绝 | 构造器上端点收缩方向反转 | 上端点值语义断言红 |
| `δ_aff` 范数 | 方形上棋盘残差 `(±s,±2s)` 与 `1,x,y` 正交；精确拟合恒等，`δ∞=2s`；三尺度 | 坐标最大值改为逐残差向量 L1 最大值 | `δ_aff=2s` 断言红，不能被单坐标噪声遮蔽 |
| 省略块对 stats | 真实 `bb03 step 1 pair (1,3)`，历史基线无该块对；全帧聚合应有 `all_pairs=1`、非刚性证书 1、省略 1 | 内部分支计数 `+=1` 改为 `+=2` | 完整 stats 字典断言红 |
| 初始接触复用 stats | 真实 `bb05 step 1 pair (2,3)`；初始接触 | 内部 `stats[path]` 对初始状态不累计 | 完整 stats 字典断言红 |
| 初始压入复用 stats | 真实 `bb05 step 1 pair (1,2)`；初始压入，另核对冻结 PD 复用 | 同上；独立参数格 | 完整 stats 字典断言红 |
| 仿射拟合交叉项 | 复用原 M5a2 独立 Cramer 法线方程 oracle | 拟合矩阵第一分子的减号改加号 | 精确端点 oracle 断言红 |
| 正残差假认证 | 复用极小、精确正残差夹具 | `delta==0` 改为 `delta<=2⁻⁵²` | 正残差不得标端点精确的断言红 |
| 残差校正符号 | 复用独立逐顶点闭合门 | `value+s*residual` 改成减号 | 原始快照端点闭合断言红 |

三项仿射历史 evidence 脚本变异现纳入普通 pytest：
`test_internal_int1_mutants_fail_the_designated_semantic_assertion` 的
`affine_fit_cross_sign`、`positive_affine_residual_certified`、`residual_correction_sign` 参数。

## 验证证据与耗时

- [机器证据](file:///D:/eab-wt/cx-m4/reports/codex/INT1_evidence/semantic_work.json)：逐项控制/变异、指定断言、耗时、源码摘要、完整命令。
- [新门日志](file:///D:/eab-wt/cx-m4/reports/codex/INT1_evidence/semantic_pytest_r3.txt)：29 个节点全绿；此前开发轮为 `29 passed in 0.34s`。
- [相邻回归日志](file:///D:/eab-wt/cx-m4/reports/codex/INT1_evidence/semantic_regression_r2.txt)：合跑 `test_int1_semantics.py` 与三个 `test_m5a2_*` 语义文件，共 116 节点全绿。
- [进度记录](file:///D:/eab-wt/cx-m4/reports/codex/INT1_evidence/semantic_progress.json)：完整运行已结束；中断不拼接。
- [测试文件](file:///D:/eab-wt/cx-m4/tests/test_int1_semantics.py)。

所有 pytest 均包含 `-p no:cacheprovider` 与独立显式 `--basetemp`；`TEMP/TMP` 均指向 `INT1_evidence/tmp`。
本分报告不是最终四片集成验收，也不以约 0.4 秒局部门耗时替代全套 5% 增量核算；最终分片身份与增量以总报告为准。

## 重启后的完整复验

原 `semantic_work.json` 为完整 GREEN，恢复时其六项源码绑定均与当前字节一致。按续单仍以全新目录从头重跑13项控制/变异和两份 pytest 专项，未拼接旧输出：

- [恢复后机器认证](file:///D:/eab-wt/cx-m4/reports/codex/INT1_evidence/semantic_work_resume_r1.json)
- [恢复后29节点日志](file:///D:/eab-wt/cx-m4/reports/codex/INT1_evidence/semantic_pytest_resume_r1.txt)
- [恢复后116节点相邻回归日志](file:///D:/eab-wt/cx-m4/reports/codex/INT1_evidence/semantic_regression_resume_r1.txt)

全部重新通过，恢复期间未修改任何被测生产代码。
