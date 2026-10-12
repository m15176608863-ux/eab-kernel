# R9FIX 设计同步（2026-10-12）

本文件只更新本工作树的实现契约。外部正本 `D:/E(A, B)/07 程序设计·统一接触内核方案.md`
按工单保持只读；本地偏离/补充由本文及 canon_map 登记。本单不是独立 G6，不宣称 M0 退出。

## 1. 二维首入：支撑平面不等于有限源特征

凸射线裁剪先合并同向共线支撑，仍保留源标签集合。候选、精确并列与 nominal near
在输出前均核验 VE/EV 的闭段投影或 FF 的真实闭段交叠。源标签的 witness 不用 clamp
修饰错误归属；共线链的实际接触子段决定回映标签。

门：`test_r9fix_entrance_domain.py`；原有凹路径的精确参数域门保留。这里没有实现一般凹块全局 E。

## 2. 声明三角表面与源单盖描述符分层

- `Polyhedron.is_convex/reflex_edges/dihedral_turn` 使用声明三角化的真实面邻接；非平面环的
  内部对角可以成为凹棱。二面角使用实际邻接三角片，而非合成 Newell 平面。
- 公共 `vertex_cone_contains/edge_arc_contains/cone_constraints` 及公共锥交接口同样使用
  `exact_surface`，不把原环拓扑假冒成实体法锥；不调用凸化视图。
- **源单盖描述符仍不是折面实体完整法锥**。旧 local cover 的源标签/源 Newell 平面语义
  保留在显式 `_source_*`/`_q*` 内部路径；公共实体 API 与这一窄描述符域分开。
  `exact_surface` 保留输入顶点索引，三角面标签携带源面及子三角信息。
- `manifold_issues` 对边连通壳分别核方向，按壳嵌套深度交替要求正/负有向体积。
  严格分离的内向壳不再被大外向壳总量掩盖；相触/交叉分量提示嵌套不明。
  此诊断没有新增单壳自交完备认证，空列表不证明任意输入嵌入无自交。

门：`test_r9fix_topology.py`、`test_r9fix_solid_cones.py`，含内部拓扑步骤撤回变异。

## 3. 精确量到最终浮点的统一边界

生产组 `eab.construction`：`scalar_rational/ratio_rational/vector_rational`、
`sqrt_rational/norm_rational/unit_rational`、`normalized_difference_rational`。

- 有理比值先完成除法再舍入；norm 先精确求平方和；unit 各分量以精确平方比开方。
- sqrt 用整数 `isqrt`、有效位整数和精确中点做 RN-even，不能先把平方或向量舍成浮点。
- radical-minus-offset 先完成精确比较再最终构造，保留抵消；上溢边缘包括最大有限值到
  overflow midpoint 的有限舍入区间，不能把所有大于 max 的精确值一概拒绝。
- 最终结果不可表示为非零 finite 时默认响亮失败。少数附带精确见证的显示或保守候选
  显式指定 `allow_underflow=True`；它不改变精确几何分支。角度齐次输入可舍掉不可表达
  的非主分量，但现有最终非零角变零的错误检查保留；不声称 libm atan2 全域正确舍入。
- LP 候选/带证书显示仍允许受控饱和 inf，精确状态和证书不读它作最终证明。

独立参考组 `eab.oracle_construction`（由 `tests/construction_oracle.py` 导出）使用有序
binary64 位模式二分和 Fraction 中点，不 import 生产构造或几何。G0 与测试 oracle 共享
此参考组，**不与被测生产构造共用实现**。对返回值可直接用中点证书检验，无需 expected sqrt。
候选快路只用 float/Decimal 提议一个值，逐值通过 Fraction 两侧 RN-even 中点证书后才返回，
否则仍回退独立位二分。强制污染候选须回退，撤掉认证须报红。identity 快路只接受原生
`type(value) is float`，不意外保留 float 子类的额外精确见证。

门：`test_r9fix_construction.py`、`test_r9fix_construction_rounding.py`、
`test_r9fix_compound_construction.py`、`test_r9fix_construction_helpers.py`、
`test_r9fix_oracle_helpers.py`、`test_r9fix_oracle_candidate.py`。覆盖次正规、halfway-even、正常值、上溢边缘、整体向量
可表示但分量先舍入失真、见证大坐标相消及 escape 精确高度比。

### 集成补充

- 窗口仅保留 legacy tie/report 策略；返回 distance 亦从精确 d² 正确舍入，不从已舍入
  的全局见证相减。display witnesses 仍保留独立的构造自检和真实点误差注入牙。
- EE/VE3/EV3 的显示 params 可在次正规以下舍零，但必须附带 `Cover3.exact_params`；
  extent 始终读取精确量。没有证书的普通标量接口仍拒绝非零下溢。
- G03 对每个候选先检查显示见证有限性，非有限候选明确记 construction failure，
  不能被另一个正常候选的最小距离遮蔽。
- 力学 `_tangents` 在精确投影后单位化；`dual.sqrt` 的有限标量路径统一构造。

门：`test_r9fix_window_distance.py`、`test_r9fix_cover_parameters.py`、
`test_r9fix_g03_construction.py`、`test_r9fix_mechanics_construction.py`。

统一复合构造在入口同时有理化 c、nn、offset；nn 必须为正，不能依赖调用方预先转
Fraction。门 `test_r9fix_normalized_input.py` 覆盖相同 binary64/Fraction 输入及内部撤回变异。

## 4. 静态防回归与边界

`tools/check_exact_construction.py` 扫描整个 src/tests AST：禁止未经批准的直接 float 转换，
sqrt(float)、hypot(map(float))、先分量舍入再 norm/unit，以及先舍两个操作数再相减。
追踪 import/赋值别名、普通/注解赋值、海象表达式、局部容器以及捕获的转换值。
统一构造名字之间的串接（如 sqrt_rational(scalar_rational(q))、unit(ratio(...))）同样不允许
提前舍入，不能因为函数名“checked”就漏检。白名单按文件、具名函数、规则逐条写理由：仅输入解析/Number 输入协议、保守过滤、
统一构造内部的精确转换和故意的真实路径变异；没有整文件豁免。

门：`test_r9fix_construction_static.py`，植入禁用源码和六种语法绕过均必须被拒绝。
这是针对已知错误族的结构门，不是任意动态 Python 的跨过程类型/数值正确性形式证明；
反射、任意用户函数隐藏的转换仍需代码审查和数值证书。完整 src/tests 搜索及修改台账
见本单 evidence，不能用 AST 绿替代独立复核。

## 5. 验证及退出口径

全部旧测试格子保留，构造 oracle 改用独立 RN-even 证书（旧四 ULP 条件未被放宽）。
README 中 canon 的历史二至五轮核验不再被写成“从未 G6”；命题 7 已有 API 不意味着
命题 8 或完整首入控制已实现；二维旧 19 格不再是现行 oracle 豁免。

完整回归、修改边界和未完成项以 `reports/codex/R9FIX_report.md` 为准。
本单禁止 Git 写操作/新 worktree，故仅当前树和只读基线快照证据；M0 仍须下一轮独立 G6。
