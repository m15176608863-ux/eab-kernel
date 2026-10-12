# WO-R6FIX 子报告：G6F-04 / G6F-05 与二维同类扫描

## 范围与结果

- 工作树：`D:/eab-wt/cx-e2`；不执行 git 写操作，不改 fixtures，不触碰姊妹仓库。
- 本分工修改：`kernel2d/g0.py`、`kernel2d/geom.py`、`kernel3d/g03.py`；新增两个互相独立于生产几何的 oracle 模块 `kernel2d/g0_oracle.py`、`kernel3d/g03_surface_oracle.py`；新增 `tests/test_r6fix_g0.py`，加强 `test_invariance_2d.py` 与 `test_kernel2d_entrance.py` 的相关旧断言。
- 最新新增门：**70 passed in 0.15s**，完整日志 [green.log](green.log)。四项内部变异均由目标看护断言报红。
- 本报告不是全仓最终验收；全仓运行、canon 指针与正本文档同步由主执行者负责。

## G6F-04：隐式带跳过严格样本

### 修前真实红

先新增最小复现测试，尚未修改 G0 源码时运行，完整日志 [red.log](red.log)：

- 二维严格微分离与微贯入 `2^-44`，在实际盖枚举内将 `_ve_side` 置为拒绝、`vv_cover` 置为空；原门都 `samples=0, touching=1, passed=True`。
- 三维严格微分离 `2^-44`，实际法锥 `_qvertex_contains` / `_qedge_contains` 置为拒绝；原门 `samples=0, skipped_intersecting=1, passed=True`。
- 报红断言均是 `assert rep.samples == 1`，不是后置伪数据或偶然浮点值断言。

### 根因和治根修复

- 旧二维 `polygons_overlap(..., 1e-12*L)`、三维 `polyhedra_overlap(..., 1e-12*L)` 将严格样本改成边界，导致完备性命题未执行。
- 二维新 oracle：有理平移、公共分母整数提升、精确边交/绕数；区分严格内部、边界、严格分离，不共享生产几何原语。
- 三维新 oracle：只读原始顶点/面环，独立整数平面、齐次面环绕数、边面交、泛化射线奇偶；分离时独立有理顶面/棱棱平方距。所有组件各有包含性代表点，不能因第一个组件在外而漏掉另一个被包含组件。非共面面环按独立实现的约定投影耳切插值，不能把它们悄悄压到首三点平面。
- oracle 新缓存只接受内容 tuple 作键，缓存值全是不可变 tuple/整数；不持有可变 Polyhedron 的别名。
- 三维采样平移本身也先有理化 `base + radius*v`，不会让 Fraction 的微基准被 `+ float(0)` 抹掉。
- 旧相对/舍入阈值只审计**浮点盖见证构造误差**；不再决定成员真值、事件真值或样本去留。

### 修后与变异

- 三个最小反例现在各 `samples=1`，盖内缺陷导致 `passed=False` 且真实缺少见证的距离为 `inf`。
- [mutant_classification2d.log](mutant_classification2d.log)：把独立分类内部恢复成正噪声带分类，`samples==1` 两格重新红；`2 failed, 68 deselected in 0.12s`。
- [mutant_classification3d.log](mutant_classification3d.log)：在 G0 调用的 oracle 分类内部恢复微正距豁免，`samples==1` 红；`1 failed, 69 deselected in 0.11s`。
- 两个变异都发生在门的真实分类路径，不在盖输出之后追加假数据。

## G6F-05：出口和距离 oracle 自身错误

### 修前真实红

同一份 [red.log](red.log)：

- `1-2^-39` 的方块、方向 `(1,0)`，应返回 `Fraction(1, 549755813888)`，原结果 `0.0`，看护断言 `got == expected and got > 0` 红。
- `s=2^-600` 错位方块真距 `s/2 = 1.204959932551442e-181`，原 oracle 返回 `1.7040706787304193e-181`；正确内核被门假红。
- 顺带扩展同类上溢格 `s=2^600`：真距可表示，原 oracle 返回 `inf`。
- 修前总体 `6 failed, 1 passed in 0.11s`，其中三项属 G6F-04，另三项属 G6F-05。

### 根因和治根修复

- 首出口：所有顶点/边射线事件用 Fraction 完成（包括共线行进的端点事件）；相邻事件区间用独立精确成员分类，不加带、不放宽区间参数。返回精确 Fraction 事件参数；G0 保持有理平移一直到盖枚举输入，不把精确事件先舍入成另一组几何。
- 距离：全端点/闭线段对的投影、夹紧、平方距、最小值比较都在有理数中完成，最后才用独立高精 Decimal 开方生成浮点显示，不先将平方变成 float。
- oracle 与生产原语零共用；新三维距离 oracle 也去掉旧 `brute_feature_distance` / `point_in_face_polygon` 共享路径。

### 修后与变异

- 原微贯入以及 `2^-600 / 1 / 2^600` 距离格全绿；正确微尺度盖不再被假红。
- [mutant_exit_midpoint.log](mutant_exit_midpoint.log)：仅把事件区间成员恢复噪声带，首出口断言重新得到 `0` 而红；`1 failed, 69 deselected in 0.11s`。
- [mutant_distance_square.log](mutant_distance_square.log)：仅删开方前保精确平方的关键步骤，恢复 `sqrt(float(square))`，微尺度断言因 `0` 红，大尺度因平方溢出红；`2 failed, 1 passed, 67 deselected in 0.12s`。
- 全部变异进程隔离、无源码覆盖；可重跑 [mutate.py](mutate.py) 的四种模式。

## 全仓同类扫描中本分工处理项

|位置|同类根因|处理及新门|修前证据|
|---|---|---|---|
|`geom.reflex_vertices / is_convex`|默认/tol=0仍抬 `turn_floor`，吞掉真实微凹|默认精确转角；正 tol 是显式 sin/cos 扇区，之后有理行列式比较|[scan_red.log](scan_red.log)|
|`point_in_polygon / polygons_overlap / segments_properly_cross`|默认或小正 tol仍抬坐标舍入地板；距离平方可下溢|去隐式地板；给定坐标转有理后判绕数、闭线段平方距、相交和三角 SAT；显式正窗口不随坐标放大|微几何新门同时覆盖严格内/外、贯入/分离、真横截|
|`signed_area / is_ccw / centroid`|中间面积下溢变0或上溢变inf，符号分支及质心错误|面积符号精确；面积显示无法表示时响亮失败；有理面积矩先相除后最终舍入|[centroid_red.log](centroid_red.log)：tiny误判非CCW、大尺度centroid=(nan,nan)|
|`interior_point`|择最远点用浮点叉积，tiny时排序全成0；Fraction工程坐标平均用了浮点除法|输入与择支量有理化，内点平均保持Fraction；tiny凹槽和far微三角均严格内部|[interior_red.log](interior_red.log)：旧结果分别在外/边界|
|`outward_normal`|混合float/Fraction相减先丢短边|先F差，有理归一化分量再稳健开方输出|[normal_red.log](normal_red.log)：原先误抛zero-length edge|
|G0的可变缓存/隐藏带扫描|新增缓存必须防别名；默认采样不能空过|不可变内容键缓存；新增49格L形独立单元并分类、三尺度×两平移的三维区间积距离、双组件包含门|新增文件70格全绿|

保留但重新明确用途：`round_floor / angle_floor / turn_floor` 是浮点见证误差/表示误差报告，不用于上述精确谓词的真值。`g0` 的 `tol` 兼容参数和构造审计容差不再给 oracle 制造噪声带。

## 测试改写台账：不删除、不缩网格、不放宽阈值

1. `test_invariance_2d.py` 距离/出口计数：原断言要求**浮点旋转再舍入**后的精确接触仍恒为接触，数学上不成立。新门保留全部原输入、种子和尺度；原浮点样本逐个与另一份测试侧独立 Fraction oracle 对照；额外用同一参数的**精确有理仿射**重做原来的计数不变性。每个门仍要求通过，原距离阈值完全不变。
2. 同文件 `polygons_overlap`：保留全部原格；原浮点像双向用零容差与独立精确成员 oracle 比对（更严格），另在精确仿射像上保留原显式正 tol 的接触/分离/重叠不变断言。
3. 同文件平直点/BB52凸性：保留原网格/块数；对原浮点像逐点用独立有理转角 oracle 对照，并新增精确仿射下与原计数相同的断言。不能以理想平直为由把给定数据的微凹改答为凸。
4. `test_kernel2d_entrance.py` 30个原随机种子：不改 bt误差 `5e-9` 和 gap门 `1e-9`。原 `polygons_overlap(translate(A,e.x),B)>=0` 使用了已舍入的显示点，14格真实变成微分离。现用 `e.t_exact` 和原 `x0,d` 有理重建真实位形，要求独立 oracle **恰等于0**；显示点生成的实际几何另与独立 oracle 零容差逐格对账。
5. `test_kernel2d_review.py` 旧 `outward_normal` 反号变异因主执行者重写精确 `facet_gap` 后不再穿过被测路径，已通知主执行者改为新路径内部反号；本分工未修改该文件。

## 验证命令和运行记录

统一前缀 `$env:PYTHONDONTWRITEBYTECODE='1'; python -X utf8 -m pytest -q -p no:cacheprovider`；临时目录均在本树证据目录。

- 新增门：`tests/test_r6fix_g0.py --basetemp reports/codex/R6FIX_evidence/tmp/g0_green70` → `70 passed in 0.15s`。
- 加强后的 G0 / 凸性 / overlap 元门：`tests/test_r6fix_g0.py tests/test_invariance_2d.py -k 'r6fix or polygons_overlap or convexity or distance_completeness or exit_completeness'` → [geom_invariance.log](geom_invariance.log)，当时 `267 passed, 653 deselected in 14.68s`（后续又追加了法向1格）。
- 入口文件最终单跑 → [entrance_green.log](entrance_green.log)，`47 passed in 9.50s`。
- 最广关联运行（全部 `test_kernel2d*.py`、invariance_2d、interlocking、新增门）→ [final_related.log](final_related.log)，`14 failed, 1766 passed in 208.44s (0:03:28)`；此进程启动时已加载修前入口断言，14失败仅为上面列出的显示点14格，之后入口文件全47格单跑绿。其余1766格没有失败。
- 更早一次关联运行的7个 tmp fixture ERROR 是环境输入错误：`--basetemp` 父目录未创建；已显式建立本树父目录，最广关联运行中全部消失。没有 skip/xfail 或删除测试掩盖。

最终全仓最后一行与总耗时由主执行者在汇总报告记录；不把部分绿冒充全仓绿。

## 首轮全套复核追加

BB52 稀疏VE门的旧“584/603”必须作用于历史逐顶点浮点坐标像，不可与现行有理仿射输入混同。已在不改原参数网格、原变异、原出口/距离/退役投票守护的前提下增加原1260格浮点像控制与变异审计，19条真实缺盖完整保留。详见 [bb52_followup.md](bb52_followup.md)。整个 `tests/test_bb52_g1.py` 最终 `17 passed in 225.39s (0:03:45)`；单步输入形成变异在新增距离守护准确报红。
