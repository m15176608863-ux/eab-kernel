# WO-M3c 三维几何补门分项记录（1 / 5 / 7）

## 范围与方法

仅修改测试，未改生产几何源码。主 oracle 为 `tests/m3c_oracle3d.py`，只导入 `fractions.Fraction` 与 `itertools.product`：手工声明原实体的凸盒分解，独立计算差集盒、全部盒支撑平面事件、闭并集占用、射线闭区间端点、Cartesian 网格暴露矩形及距离。没有调用被测 BSP / SAT / hull / clip / normal / distance，也不读取 `B.planes` 或生产凸片输出作为期望值。

五格是 L 凹棱柱、窄缝 U 槽、紧配 U 槽、闭空腔、全三维有理旋转加单位放大 2 倍及 10^6 量级平移的窄缝 U 槽；这是结构化样本覆盖，不是随机实体穷尽证明。合计核验 3006 个侧点、132 条固定种子的随机方向直线、336 个独立边界端点，全部零失配。每格还核验独立最短出口平方及全部并列最优点；五格实际 `polygon/side_points` 产物互异。

## 内部变异与准确红点

1. `explicit_boundary` 中把 `_sides` 的全部支撑面参数改为仅来源凸片对支撑面：窄缝格暴露片从 220 降为 205。三个独立子检查分别报：
   - `independent adjacent-open-cell side probe crossed a support event`
   - `independent ray boundary point has an exposed polygon`
   - `independent Cartesian-union shortest closed exit`
2. `_edge_closed` 两个 `>= 0` 改成 `> 0`：正交交叉细长盒的外露顶/底面中心仅能由 EE 覆盖，EE 法向处于闭锥边缘。报 `T3L closed-only EE covers the independent exposed-face interior`。三种单位/旋转/平移格均查完整局部盖并覆盖，实际裁剪产物互异。
3. `clip_local_covers` 删除非共面拒绝分支：实际产生 864 个片，其中 576 个为空。审计先作顶点数、非零面积、共面性断言，准确报 `clipped local cover must be a nondegenerate planar polygon`，不再由后续形心计算抛 `ZeroDivisionError`。

所有变异均在真实函数体中以独立 namespace 执行源码替换，不改磁盘源文件，不在返回结果后添加假数据；这些语义检查不调用源码哈希类门。三项均先绿、变异语义红、恢复再绿。根代理另运行未捕获异常子进程，保存真实非零退出红日志。

## 验证

最终测试结构：5 个 pytest 节点（其中两节点内部执行 5 格 / 3 格并断言实际产物互异）。定向运行原样末行：`5 passed in 4.68s`。

此前尚未合并族参数节点时，旧 M3b 三维边界门与新门一起运行：`21 passed in 9.60s`；此记录仅是此前回归证据，不充当最终全套结果。最终四片全套、静态门与新增耗时比由根代理汇总。

独立代理 interval_gates 只读复核未发现 critical / major；未新增 oracle 准入或豁免。每格计数、完整 import 清单、红点和恢复记录见 `geometry_agent.json`。
