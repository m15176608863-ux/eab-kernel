# WO-E5b 首入 / 冻结 / 退化族子任务

## 实现契约

- 首入几何使用 `exact_surface` 的确定性三角面；非共面输入环不再用 Newell 拟合平面代替。
- 根、时刻排序、t_max、并列及平方深度比较全部用 Fraction。`exact_t` 为精确时刻；`t/x/normal/witness` 是浮点构造。
- 完整 `surface_events` 给出时间分区；首事件和紧邻前区间有理中点均精确自检，能发现遗漏的早接触（包括先接触、再次分离后再进入）。
- 兼容 `label/members` 仍用源特征编号；精确三角限定存在 `surface_label/surface_members`，面描述为 `('face',fi,'triangle',i,j,k)`。冻结单盖使用 surface_label；FF/FE 合并标签须从 surface_members 选原始 VF/FV/EE 代表成员。旧源整面 label 对非共面环不能冒充精确冻结几何。
- `shortest_exit3` 精确比较局部 facet 的最小平方深度；不是任意凹体全局最短逃逸保证。
- 退化合并只允许精确同向、精确共面；无隐含角度/长度分辨带。四种台阶高度 1/2、1/1000、1e-12、2^-80 均返回两组 FF，各 2 成员。
- 冻结 EE 和凸 facet 共用 `_oriented_ee_normal` 双侧精确锥规则；一般源面视图与 canonical convex 标签不能混号，同视图且同显式角窗才保证同向。facet_normal3 用零角窗；一般 margin 选盖角窗 1e-9 时冻结须带同一选择口径。
- Newell/EE 的值和全部 Dual 导数先计算精确多项式 jet，然后仅在 sqrt/归一化输出时转浮点。门钉住浮点叉积为 0、精确叉积为 2^-54 的值和两个导数通道。

## 第五轮处置

- entrance3.py:234 major：原 h=.5/.05/.02/.005、旋转 0/7/11、平移 0/1e3 的 24 格全部对独立星核四面体并集、整数 SAT 射线区间的精确首端点，零错。已删除旧两把尺步长。
- test_entrance3_concave.py:75：原审查标签 major，复核纠正为 minor。已纠正“0.5 台阶杀 ×1e6”错误 docstring；新增微台阶真牙杀死共面容差回退。
- g03/geom3/covers3 其余项由主代理汇总。本任务仅改 covers3 的共享方向辅助，不声称独立 G6 通过。

## 测试改写台账

机读 test_ledger.json。无删除测试、缩网格、新增 skip/xfail 或放宽误差。
唯一行为断言迁移：旧 t_max=.3，而给定 binary64 底面 .8 减 .5 严格大于 binary64 .3。原输入新增 none 和精确边界断言；在有理恰边界的同构数据上逐字保留旧 entrance 断言。其余旧首入/冻结断言全保留。

## 突变

机读 mutations.json，原始 mutation_*.log。三项真路径均杀：浮点前步导致假“更早已触”；容差合并把两组 FF 各二成员变成一组四成员；浮点中点把相邻有理事件区间压到端点。目标断言已逐条核对。前两次临时源改动 finally 按原字节恢复；第三次仅隔离进程 compile/exec，不修改生产文件。

## 验证

- 局部完整入口/冻结套：185 passed in 146.44s (0:02:26)。
- 随后追加第五轮原 24 格、先接触再分离门和相邻有理区间门，并细化同一角窗的方向规则。
- 最新源码局部门：74 passed, 24 deselected in 7.87s；24 个未再跑的是前一完整套已绿、未改写的随机凸对 800 步佐证门。
- 全套最后结果和耗时由主代理冻结全队修改后记录；本文件不声称全套/G6已通过。

## 追加闭合：非共面源环的三角化对角 EE

margin 同事提供折面脊岭 / 四面体实际标签 EE(0,1)×(5,7)。B 原面环拓扑不存在 (5,7)，旧冻结锥判据将空邻面错误降为 fallback。原姿态恰巧正确；镜像 x 且反转面环时保留起始顶点（确保同一确定性三角对角），body_distance=+0.2、冻结却为 -0.2，已复现真实缺陷。

现仅在请求棱不属于源拓扑时，用 exact_surface 找到真实相邻三角，再执行同一精确方向规则；既有源棱保持原来选盖窗口/源环契约。新增 2 个镜像 × 3 个有理刚体/单位/大坐标格，主 oracle 是已知平行平面距离且两脊棱交点达到该下界。6 格全部对签名距离和已知法向；内部编译变异恢复“返回原源拓扑”，目标“diagonal EE frozen signed distance”断言确实捕获反号。未物理修改源文件做突变。

目标门：10 passed（7 个新对角门 + 3 个精确jet门），兼容门另4 passed。日志 frozen_diagonal.log / frozen_diagonal_compat.log。

## 首次集成全套发现的旧冻结门 oracle 域遗漏（已闭合）

全套诊断出现的 3 格失败均在 `label in independent.cover_labels(P,Q)`，不是冻结正负号失败。默认裕度路径已采用实际折面三角，原 oracle 却仍采用源环 Newell：其中两格胜出棱是原环没有的对角棱，一格原棱的相邻真实三角法锥与源环不同。独立复算三格冻结间隙均为正确正号。因此没有把生产默认答案改回旧源标签。

`test_near_parallel_crossing_edges_stay_in_extent_in_engineering_coordinates` 的原 6 格、原输入、原所有断言逐字保留，仅旧调用显式给 `contact_window=contact_resolution(P,Q)`。同一输入另加默认全 `(label, strict)` 集合对拍，以及独立精确全表面最小平方距、冻结间隙正号、EE 方向/在程断言。测试专用 `e5b_frozen_oracle.py` 用独立投影耳切与 Fraction Gram/点三角距离，未调用生产 triangulate/normal/cover/距离谓词。断言逐字保留证据见 `frozen_migration_assertions.json`。

新增内部突变把 `_witnesses` 中实际折面展开分支关闭（仅 compile namespace + monkeypatch），由 `complete exact-surface cover set` 断言捕获。原文件全部 98 节点加新牙 1 节点，`frozen_migration_full.log` 原样最后一行：`99 passed in 21.58s`。这一轮没有修改生产文件。
