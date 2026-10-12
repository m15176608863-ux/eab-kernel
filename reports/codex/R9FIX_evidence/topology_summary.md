# R9FIX 拓扑与 oracle helper 分项证据

## 边界与文件

仅修改当前工作树；无 Git 写操作、无姊妹树操作。源文件仅 `src/eab/kernel3d/geom3.py`；新增 `tests/test_r9fix_topology.py`、`tests/test_r9fix_oracle_helpers.py`。后续按主执行者分工修改 5 个 test-owned helper：`e5a_cover_oracle.py`、`e5a_escape_oracle.py`、`e5a_g2_oracle.py`、`perf_cover_oracle_reference.py`、`perf_escape_oracle_reference.py`。统一构造库及独立构造参考库由其它执行者提供。

全部命令设置 `PYTHONDONTWRITEBYTECODE=1` 并使用 `python -X utf8`；pytest basetemp 均为本树 `reports/codex/R9FIX_evidence/tmp/topology` 或 `topology_oracle`。

## G6I-02：源环描述符冒充声明折面实体

- **根因**：`is_convex`、`reflex_edges`、`dihedral_turn` 只看输入源环与单个 Newell 向量，没有读取非平面面环的声明三角表面。真实内部凹对角棱 `(5,7)` 不在源环棱集中。
- **修前红**：`topology_before.log` 中独立屋顶方程 `0<=z<=1+h max(0,x+y-1)` 的 24 个参数格，`assert p.is_convex(0) is False, 'declared-roof-midpoint-concavity'` 均得 `True`；24 个凹棱格得到 `[]` 而不是 `[(5,7)]`；12 个二面角格得到 `1.3258176636680326` 而不是 `pi/2`。
- **修法**：三条公共实体入口先 `P = exact_surface(self)`，再在声明 surface view 上检验精确二面符号/构造角度。保留原顶点编号，使内部凹棱回映到 `(5,7)`。`is_convex` 同时拒绝多个闭壳分量（分离两凸体或带空腔实体都不是凸体），不再仅用逐棱局部凸性充当整体凸性。
- **变异牙**：对三个真实被测方法分别把内部 `P = exact_surface(self)` 改回 `P = self`；三条看护断言分别为 `declared-roof-midpoint-concavity`、`declared-folded-reflex-ridge`、`actual-surface-right-angle`。不是在输出端追加假数据。
- **加强格**：平屋顶分界 `h=0`、同一对象从折面改回平面后新鲜 surface 读取、微凹 `h=2^-80`、三尺度、旋转与大平移。oracle 仅用屋顶显式方程和已知正交平面，不调用生产三角化/法向/成员/凸性原语。

## G6I-05：总正体积掩盖独立内向分量

- **根因**：原诊断只对总有向体积做 `v>0`，未核分量朝向，也未区分空腔的合法内向壳。
- **修前红**：独立分量体积 `64` 与 `-8` 时 `manifold_issues(0)==[]`，`disconnected-inward-component` 断言报红。额外 `2^±600` 形状暴露诊断先构造浮点面积/体积导致范围异常；错误朝向的嵌套壳也未报告。
- **修法**：`_component_orientation_issues` 按面—棱连通分量取精确有理体积；先拒绝分量间接触/相交，再按精确成员核嵌套深度。偶数深度外壳须正体积、奇数深度空腔须负体积；体积零独立报告。不机械要求所有分量正体积。面积退化先看精确 Newell 非零，不让浮点面积范围决定诊断。
- **契约收窄**：空列表只表示列出的闭合/遍历/平面度/朝向检查通过，不宣传完整嵌入流形证书；单分量自交和顶点链完整认证仍不在本诊断内。相互不交的嵌入闭壳是嵌套方向判据前提。
- **变异牙**：将真实诊断内部 `_component_orientation_issues` 换回总有理体积正负检查，`disconnected-inward-component` 精确断言红。
- **加强格**：合法双壳空腔、非法同向空腔、三层壳奇偶朝向、反向外壳、合法分离实体、分量接触/相交、三数量级。

## 同类拓扑扫描

1. `entrance3.py` 的一般表面入口、`frozen.py` 的一般模型入口、表面距离棱集已经显式 `exact_surface`；未找到同类缺失。
2. **此处按最后同类补扫订正**：最初仅为 `covers3.py` 公共局部锥补充 source-ring descriptor 文案并不足够；团队补扫找到了真实折面法锥反例，现 `vertex_cone_contains`、`edge_arc_contains`、`cone_constraints` 等公共入口内部先取声明表面。只有单盖的显式 `_source_*` / `_q*` 内部路径保留 source-ring descriptor 契约，避免偷改源特征标签。最终修法、红绿与内部变异见 [solid_cones_summary.md](file:///D:/eab-wt/cx-e2/reports/codex/R9FIX_evidence/solid_cones_summary.md)。
3. `geom3.face_normal`、`vertex_edge_dirs`、`vertex_edges` 文档明确 source-ring 辅助含义；实体 `is_convex/reflex_edges/dihedral_turn` 不再使用该豁免。
4. `geom3.norm/unit/_checked_scalar/_exact_line_params/angle_between` 的精确输出统一走经过验证的 `eab.construction` API，保留原 wrapper 名以守住旧变异门。
5. `_contact_cone_witness` 等旧探针代码不是当前 `polyhedra_overlap` 判据路径；不能把其噪声窗口或 Newell 探针描述当现行精确判据。此次没有借机扩展/改写死路径拓扑策略。

## 额外同类问题：5 个 test-owned oracle/helper

### 修前证据

`topology_oracles_before.log`：**11 failed in 0.15s**，包括：

- 两个 cover oracle 在 `10^8` 坐标上先舍入见证点，再相减，把精确 `10^-9` 距离输出 `0.0`。
- 两个 escape oracle 在 `2^-600` 和 `2^600` 的范数先分量浮点平方，分别输出 `0.0` 和 `inf`。
- 两个 escape oracle 用舍入单位法向点乘大抵消位移 `(2^53,1-2^53,0)`，不满足精确 gap `sqrt(1/2)` 的 Fraction 中点证书。
- 三个单位化 helper（escape、perf escape、G2）在普通输入 `(7/5,2/3,1/7)` 就有分量舍入误差，逐值中点门报红。

`topology_oracle_height_before.log`：**2 failed, 4 passed, 11 deselected in 0.32s**。倾斜顶面 `z-(2/3)x-(1/5)y=1`、初始底点 `z=-3/11` 的精确首达高度是 `14/11`；先构造 gap 与 nz 再相除得到 `1.272727272727273`，正确 binary64 是 `1.2727272727272727`。

### 根因修法

- 全部改用独立 `construction_oracle` 的 `vector_exact/norm_exact/unit_exact/sqrt_exact/scalar_exact`，不共用生产几何或生产构造算法。
- 见证距离先 `exact=True` 求 Gram 见证，再精确相减和最后开方；perf 参考增加同等 exact 选项。旧标签、几何算法、参数格和比较断言全部保留。
- signed gap 从精确分子 `dot(n,d)`、平方和 `dot(n,n)` 构造一次，符号读精确分子。
- escape 的 facet 提供 `exact_coefficients`，候选高度先算精确 `-numerator/nz_exact`；归一化分量和 gap 窗口也用精确平方比较。原 legacy 分组/并列窗口政策未放松。
- 二次候选检验只消费有限接触域，新增 `extent_only` 走同一精确域路径，避免为不消费的中间 residual 构造不可表示 gap。
- direction noise 直接构造最终比值平方根，避免先构造会下溢的 sine。超范围的 **legacy 不确定性诊断** 显式饱和为 `inf`（拒绝候选，不是几何结果）；说明写入代码。
- unit 的 sub-binary64 分量仅作显式 display，源模型/锥/方向阈值分支均保留精确数据。candidate nz 门至少 `1e-12`；小到下溢的分量不能通过。gap 和 height 不允许这种显示降级。

### 牙与不弱化台账

- 新 `test_r9_oracle_witness_rounding_mutant_is_caught` 将真实 `witness_distance` 的 `exact=True` 改回 False，红在 `exact root midpoint certificate`。
- 新 `test_r9_oracle_rounded_gap_height_mutant_is_caught` 将真实 candidate height 改回“已开方 gap / 已单位化 nz”，红在 `oracle-exact-plane-height-ratio`。
- 未删除/放松任何旧测试、未 skip/xfail、未缩网格。5 helper 的参考输出语义由错误中间舍入加强为最终正确舍入；原 perf 快慢参考完整相等门仍原样成立，含 subnormal 格。新增总计 19 个 oracle helper 回归/变异测试。

## 验证结果与原样末行

1. `topology_before.log`：`66 failed, 2 passed, 4 deselected in 0.64s`（修前）。
2. `topology_after.log`：`200 passed in 0.97s`（R9 + R6/R7/R8 针对门）。
3. `topology_legacy_final.log`：`526 passed in 98.36s (0:01:38)`（拓扑、几何、hull、interlocking、cache、R6/R7/R8/R9 完整选组）。
4. `topology_oracles_legacy.log`：`72 passed in 6.07s`（5 helper 的性能等价、G2、margin、盖与新增门）。

第一次拓扑兼容组执行期间本执行者挪动了 geom3 定义行，旧进程中 `inspect.getsource` 依旧以加载时行号定位，误取邻近函数；该次为 `1 failed, 449 passed in 91.88s`，日志完整保留在 `topology_legacy.log`。这是验证环境失配，不是断言放宽：源停止修改后同一项 `1 passed in 0.10s`，完整组随后 `526 passed`。运行完整套件前须冻结源码行号。

## 交接状态

所负责代码与测试均已交接，未提交；完整仓库最终门、canon 指针修复、README/canon_map/设计文档同步由主执行者统一完成。此分项报告不声称独立 G6 退出通过，也不声称单分量自交流形已认证。

## 最后只读扫描发现并接管修复：力学切向与大整数根

静态 AST 模式检查不等于类型完备证明：`math.sqrt(x)` 的 `x` 可能是整数/Fraction，且没有显式 `float(...)`；`sum(v*v)**0.5` 也可能先把极端平方变成零或无穷。因此额外逐个检查剩余 sqrt/hypot/幂路径的实际调用域。

### 新发现与修前红

- `limit._tangents` 的显式方向 `(1e-200,0,0)` 和 `(1e200,0,0)` 都错误报“与 `(0,0,1)` 平行”，而方向 `(1,0,0)` 正常。3-4-5 方向在 `2^±600` 的 float/Fraction 格也失败；这是 `LimitContact` / `friction_generators` 的活路径，非死代码。
- `dual.Number` 明确允许 int，但 `dual.sqrt(2**1200)` 在 math.sqrt 的隐式 float 转换时溢出，尽管最终根 `2**600` 可表示。`2**2046` 同样错误；扩展检查的小 Fraction `2^-1200` 被先转 float 输出 0。
- 新门 `tests/test_r9fix_mechanics_construction.py` 修前日志：`mechanics_same_family_before.log`，原样末行 `9 failed, 9 passed, 2 deselected in 0.19s`。

### 最小修法

- `_tangents`：法向/显式 tangent 先保留 Fraction，精确投影；原有 `64eps * |tangent|` 可分辨窗口不删不放宽，而是等价的精确平方比较。之后 `unit_rational` 一次构造 t1；t2 契约仍是 `n × 返回的 t1`，各叉积分量精确相减后走 `scalar_rational`。不再需要第二遍浮点投影去消除首遍舍入垃圾。
- `dual.sqrt`：非 Dual 的有限 scalar 走 `sqrt_rational`；Dual 正常域求导公式原样保留；显式非有限 float 原行为保留。不让输入大整数先进入 float。
- 内部变异：把 `_tangents` 的单位化改回“先构造平方 float 再 sqrt”、把 `dual.sqrt` 有限 scalar 分支改回 `math.sqrt(x)`，分别红在 `tangent-scale-invariant-frame-construction`、`large-integer-final-root`。
- 旧 `tests/test_limit_tangent_noise.py` 的四个近乎平行拒绝格和三个合法正交格原样保留并全绿；新增门再守 `2^±600` 下近乎平行的相同相对拒绝。

### 验证与边界

`mechanics_same_family_after.log`：新增门 + 原 tangent-noise + Dual + R7 limit-construction，原样末行 `64 passed in 0.12s`。未改任何旧测试断言或网格。新增两个源文件改动为 `src/eab/limit.py`、`src/eab/dual.py`；已通知主执行者重新修 canon 行号。

其余剩余 sqrt/hypot 扫描项为普通浮点随机姿态生成、已限定的固定夹具/近似诊断、非有限报告处理或故意注入的变异。此次没有找到它们在现有 Fraction 活调用中的新可复现实例；这不是“AST 能证明所有数值数据流正确”的声称。生产代码几何分支与库构造边界、独立 oracle 的最终转换已按实际路径审查。

## 首轮全套后的 G03 非有限显示报告兼容修复

第一轮全套 `full_3.log` 的 G03 失败有两层，均已处理：

1. 自动统一构造时把旧测试的 `math.isnan(float(c.point_a[0]))` 改成了 `math.isnan(scalar_exact(c.point_a[0]))`，但被注入的值本来就是 binary64 NaN，不是等待构造的有理量。有限构造器应当拒绝 NaN，故测试在报告路径之前意外抛错。现改为 `math.isnan(c.point_a[0])` 直接读同一个注入值，保留原来的 `any(c.in_extent and ...)` 断言，不降低看护强度。
2. 正常入口的 `norm` 迁移到有限精确构造边界后，G03 报告器把坏显示候选传入 `norm` 会抛异常，不能履行“报告 construction failure”的契约；原代码还直接略过缺失坐标 `None`，允许其被其它正常候选掩盖。

`src/eab/kernel3d/g03.py` 新增 `_display_witness_distance`：先核 None/非有限，再对有效坐标精确相减后构造范数；不可表示的显示距离也明确记录为失败 sentinel。任何候选非法都会使本次报告距离为 `inf` 并写 construction failure，不改变精确 feature completeness。

新增 `tests/test_r9fix_g03_construction.py` 在枚举器内部注入 NaN、正/负 infinity、None，要求返回失败报告而非中断；精确完备性仍应通过。内部去除 `_display_witness_distance` 的验证门会使 `g03-invalid-display-recorded` 指定断言红。

- 修前：`g03_display_before.log`，`5 failed, 4 passed, 1 deselected in 0.36s`。
- 修后：`g03_display_after.log`，`10 passed in 0.20s`。
- 测试改写台账仅旧 NaN 探针检查去掉无意义转换；原看护条件及最终 `not report.passed` 完整保留。没有改 covers3/margin/oracle_construction 或静态门。
- 同轮 margin-underflow 失败定位为 `covers3.ee_cover` 在被有限域筛除前构造域外 `s=-2^-1075` 参数，此项已回报主执行者，由源文件所有者处理。
