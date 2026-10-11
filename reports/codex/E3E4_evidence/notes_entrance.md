# E3 B1 入口子任务说明

## 改动与证据

- `src/eab/kernel2d/entrance.py`：凹路径从原始 A/B 坐标计算 Fraction 仿射 gap 分子、沿速度斜率与段内投影；不先浮点平移。零间隙根为 `-g/slope`，共线平移同时枚举到达线段端点的事件。
- 原局部盖枚举接口保留，内部不传历史 `ctol`、不放宽法锥；候选标签之后额外用 exact side 核验。浮点输出 gap/normal 不参与任何分支。
- 凹初态、候选时刻的相交裁决与自校验均走 `polygons_overlap_exact(A,B,X)`，X 为 Fraction。
- 自校验覆盖**所有候选之前的原始顶点-边接触事件**，并查紧邻候选之前的事件中点。无候选时同样核全部原始事件，包含无限射线；不再以有限粗探替代。U 形门证明删掉先碰后离的左壁候选时，即使右壁前一步分离也必须报错。
- `shortest_exit` 仅在精确有效、精确段内、非正 gap 候选中比较 `gap_num²/edge_len²`，取最浅盖（最小平方距离，即最大非正 gap）。**不主张一般凹对全局最小分离，也不主张该一次位移清除全部接触。**
- 凸/凹/出口 `tied_labels` 都只收精确同时/同距离；`near_labels` 是独立可分辨性报告，不参与判定。`t_exact` 保留精确首入时刻证据；原 t/x/法向/点对仍为浮点构造输出。
- 删除 `_cover_at`、旧带宽 `_in_segment`；`first_entrance_brute` 的扫描与二分均在 Fraction 平移上作精确判定，终止只控制 float 输出分辨率。

## 新门与独立性

`tests/test_kernel2d_entrance_e3.py` 当前 93 格：

1. 尺度 `{2^-10,1,2^10}` × 坐标 `{0,1e3,1e6}`，低于坐标舍入量级的平移、极小速度及精确 `t_max` 截断；闭式 t=32。
2. 精确微侵入必须 exit；初始恰接触即使背离仍 t=0；非二进有理首入时刻不能先舍入；精确并列与近邻报告分离。
3. 最浅出口不能由浮点平移吞掉负间隙；brute 不得把 t=32 吞为0。
4. 72 格随机旋转 × 大平移 × 单位尺度：预先已知的 STEP 四三角片只用原始顶点，测试内联 Fraction 投影 SAT 得各凸片首入，取最小时刻；与生产法锥、Minkowski、耳切、相交原语零共用。
5. 候选删竖板、U 形删左壁两道真实路径注入；后者补上旧“前一步”跨过窄接触区间的漏洞。

`first_entrance_brute` 与生产共用 exact overlap，模块文档明确它是**佐证而非纪律 A 主 oracle**；主门为闭式与测试内独立 SAT。

## 旧门改写（无删除输入、无跳样）

唯一旧门改写：`tests/test_kernel2d_entrance.py::test_every_legacy_vertex_edge_contact_of_bb52_is_a_first_entrance_along_its_edge_normal`。

- 旧：53 条 legacy 盖在 `sin3°/FIT=1e-6` 窗口验证；`polygons_overlap(...,FIT)==1` 的输入跳过；其余要求首入与 legacy 在窗口内同一。
- 新：原 53 条及窗口盖断言、`n==53`、旧窗口侵入计数 `n_pen<=20` 全保留；**不再跳过任何侵入输入**。测试内独立 Fraction 边交+winding 判精确初态；侵入必须 exit，并核独立代数枚举出的最浅盖完整集合；未侵入必须 entrance、精确时刻处独立 oracle 为边界，初始边界必须 t=0，然后保留 legacy 窗口等价比较。
- 不是削弱：消除了历史噪声带把真实微侵入当相触的错误前提，同时为原来跳过的格子增设确定的独立真值检查；不是允许旧错解通过。
- 原实现语义改变后有 3 条旧断言红：`(ba,bb,p1)=(4,1,108),(9,1,152),(1,9,40)`，均为精确微侵入返回 exit 而旧窗口谓词未判侵入。原失败保留 `entrance_targeted.log`。
- 独立出口 oracle 仅为本单指定“局部最浅盖”规则，不把它冒充全局分離。

## 修前红与当前绿

- 工作树修改入口之前的新增 18 格：`15 failed, 3 passed in 0.18s`，日志 `entrance_baseline.log`。典型红断言：`assert got == 32.` 得0；`assert got.kind == 'exit' and got.gap == -2.**-45` 得非精确初态；最浅出口 gap 被舍入为0；精确首入被吞或漏。
- 增补后93格另外用子进程加载**冻结旧入口文件**（不覆盖工作源码）复跑：`90 failed, 3 passed in 0.95s`，`entrance_frozen_baseline_all_new.log`。此轮共用当时已改 covers，且72格中含 `t_exact` 新字段缺失，所以**不得声称90个旧正确性缺陷**；仅作接口/契约回退佐证。环境首试缺 src 路径是输入错误，已修 sys.path 后成功运行，非测试缺陷。
- 当前三文件定向最终：`180 passed in 7.65s`，日志 `entrance_targeted_final.log`；此结果不是全套/G6退出。

## 突变准备（尚未由本子任务执行）

`run_entrance_mutations.py` 为父任务串行执行脚本；每项记录源码原/变异/恢复 SHA、JUnit 抓中断言与日志，并在 finally 按原字节恢复。

| 项 | 一次性源变异 | 目标语义门 |
|---|---|---|
| D1 | 凹判定闭包变回 float translate + `polygons_overlap(...,ctol)` | 低于舍入尺度平移仍 t=32、不能虚报提前相触 |
| D2 | 仿射根变 `Fraction(-float(g)/float(slope))` | 非二进有理候选和72格独立精确射线时刻 |
| D3 | 删除候选前精确自校验整段 | 竖板漏候选/U形先碰后离必须 RuntimeError |
| D4 | 出口平方距离 min 改 max（等价取最小负 gap） | 出口法向与最浅负 gap |

## 调用点归类及边界

- `first_entrance -> _first_entrance_convex/_concave` 的 tol：仅 near_labels 长度报告窗，无域放宽；原 `_floor` 只用于报告。
- `_candidate_labels -> enumerate_covers`：不显式给 tol、cone_tol、seg_tol；数学默认精确，无域窗口。`window=inf` 是不裁候选的搜索域。
- `_candidate_labels -> ve_side_exact/ev_side_exact`：数学有效性精确。
- `first_entrance -> shortest_exit`：tol 同上，仅报告；`first_entrance_brute` 保留 tol 兼容参数但不影响扫描判定。
- bb52 测试 `ve_cover(...,FIT,cone_tol=sin3°)`：真实 legacy 显式域窗口，保留。
- brute 仍是离散扫描，扫描步长须短于接触区间；孤立切触可以漏采，不是完备首入算法。生产全事件自检不受该限制。
- 浮点输出仍可能下溢或舍入（例如极小距离平方转 float），不把该构造量用于决策；本任务未主张任意指数范围的浮点输出准确性。
