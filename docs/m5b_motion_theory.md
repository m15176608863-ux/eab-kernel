# M5b：DDA 锚定 P2、六次首入及 P2/P3 全时程偏差

状态：下述 T1–T6 已实现并有具名门；这是指定插值模型内的精确计算，**不是 DDA 求解器内部连续路径的恢复，也不是 G6 里程碑验收**。研究域外输入明确拒绝。

## T1．DDA 参数、面积形心与半角有理近似

输入单简单环顶点与 `z=(dx,dy,theta,ex,ey,gxy)` 均为 `int/Fraction`；binary64 数据须在读入边界先按其精确值转换，字符串十进制口径不得混用。定义

```text
c = sum_i (p_i+p_(i+1)) cross(p_i,p_(i+1)) / (3 sum_i cross(p_i,p_(i+1))),
d = (dx,dy),  E = [[ex,gxy/2],[gxy/2,ey]].
```

面积形心来自多边形面积矩，不是顶点均值。每条三角形有向面积对形心的加权求和即上式；整体平移、旋转、正单位缩放时随坐标协变，反转环顺序时分子分母同时反号。

`rational_half_angle(theta,bits=80)` 的明确支持域为 `|theta|<=1` 弧度、`8<=bits<=512`。这覆盖工单中的小转角数据，但不主张支持任意多圈角。对 `sin(theta), cos(theta)` 用交错 Taylor 级数：由于 `|theta|<=1`，项的绝对值递减；当前部分和与加下一项的和夹住真值。迭代到下一项不大于 `2^(-bits-4)`。对负角只翻转正弦区间。`cos(theta)>=1-theta²/2>=1/2`，故 `1+cos(theta)>0`。

对两个区间四个端点组合计算 `sin(theta)/(1+cos(theta))` 的有理包围 `[l,h]`，得到 `tan(theta/2)` 的包围。将中点按 `2^-bits` 网格精确舍入为 `u1`，并返回

```text
epsilon_u = max(|u1-l|,|u1-h|) >= |u1-tan(theta/2)|.
```

实现不调用 `math.sin/cos/tan`，不假设平台 libm 正确舍入。`HalfAngleApproximation` 的普通数据构造器只验证字段类型、顺序和角度域；**只有 `rational_half_angle` 计算出的包围带有上述来源保证**，用户自行构造字段不获得证明。`theta=0` 返回全零、误差严格为零。

门：`test_area_centroid_is_area_weighted_and_frame_covariant`（两个矩形层片的独立面积 oracle）；`test_dda_z_mapping_uses_area_centroid_and_engineering_shear`；`test_half_angle_has_independent_taylor_enclosure_and_zero_exactness`（阶乘显式 Taylor，与生产递推不同）。

## T2．P2 与退化

```text
R(v) = [[1-v²,-2v],[2v,1-v²]]/(1+v²),
P2(s,p) = c+s*d+[R(s*u1)+s*E](p-c), 0<=s<=1.
```

`DDAAnchoredMotion` 可显式指定中心；`dda_motion_from_z` 强制以上面积形心、对称应变及工程剪切约定。`|u1|<=1` 是有理旋转 chart 域。`at/endpoint` 均只返回精确有理坐标。

若 `u1=0`，旋转恒为 I，故 `P2(s,p)=(1-s)p+s*P2(1,p)`，逐有理时刻、逐坐标等于**其自身端点的 P1 弦**。`theta=0` 的构造保证 `u1=0`。若采用实测 binary64 末帧作 P1，则端点舍入残差另计，不能宣称二者逐值相同。若 `E=0`，同一 `c,d,u1` 下 P2 逐值等于 M5a SE(2)。事件求解器不为这两种退化设置旁路，保证门经过一般事件路径。

门：`test_p2_coordinates_match_independent_complex_product_oracle`；`test_coordinate_polynomial_identity`；`test_zero_angle_is_p1_and_zero_strain_is_same_center_se2`（包含完整首入结果字段）；`test_p2_initial_states_persistent_collinearity_and_closed_endpoint`。

## T3．非反转域和六次事件证明

### 3.1 非反转充分条件

令 `a=||E||_infinity`。旋转逆矩阵的 infinity 算子范数不大于 2；若 `2a<1`，则 `||s R(su)^(-1) E||_infinity<1`。Neumann 级数保证 `R(su)+sE` 全窗可逆；行列式连续且初始为 1，故全窗为正。这保持环的简单性、凸/凹顶点符号及方向。`dda_first_entrance` 在不满足这个**充分条件**时拒绝，拒绝只表示未支持，不表示环真的反转。坐标计算本身允许更大应变，但不得据此调用首入并跳过有效性证明。

门：`test_unsupported_p2_domains_fail_loudly_before_event_enumeration` 含严格分界 `2a=1`。

### 3.2 分子与正因子

令 `a_Ki=p_Ki-c_K`，`D_K=1+u_K²s²>0`，`Q_K=D_K R(su_K)`，并令

```text
V_Ki = Q_K a_Ki + s D_K E_K a_Ki,                 degree <= 3,
N_Ki = D_K(c_K+s*d_K)+V_Ki,                      degree <= 3,
U_Bj = V_B,j+1 - V_Bj,                          degree <= 3,
W = D_A[(c_A-c_B)+s(d_A-d_B)] + V_Ai.            degree <= 3.
```

`coordinate_polynomials(p)` 返回绝对坐标 `(N_x,N_y),D`；事件计算用中心相对表达式 W 以避免不必要的大系数，但所有运算仍精确。

对 `beta` 取二维叉积或点积，有 `Q_B^T Q_B=D_B² I`、`det(Q_B)=D_B²`。模 `D_B` 时 `U_Bj=Q_B(a_B,j+1-a_Bj)`、`V_Bj=Q_B a_Bj`，故 `beta(U_Bj,V_Bj)` 被 `D_B` 整除；同理 `dot(U_Bj,U_Bj)` 被 `D_B` 整除。于是线方向、投影下界、投影上界的精确分子为

```text
F = cross(U,W) - D_A * [cross(U,V_Bj)/D_B],
G = dot(U,W)   - D_A * [dot(U,V_Bj)/D_B],
H = D_A * [dot(U,U)/D_B] - G.
```

真实叉积/点积等于这些分子除以 `D_A D_B`。实现逐次做**精确多项式除法并检查余数为零**，不丢项，不以数值近零替代整除。

当 `u_B != 0` 时，第一项次数不超过 6；方括号次数不超过 4，再乘 `D_A` 不超过 6。当 `u_B=0`，`D_B=1` 且 `U_B,V_B` 次数不超过 1，直接计数不超过 4，不存在把常数分母硬减两次的漏洞。`E_A=E_B=0` 时 `U_B` 至多二次，相同计数得到刚体上限 5。除去的因子始终正，因此不增删实根、不翻转符号。

门：`test_sixth_degree_events_match_independent_seven_sample_oracle` 用七个精确样点和独立 Lagrange 插值核对全部系数，并在额外非整数样点自检；本算例确有非零六次系数。`test_losing_the_sixth_event_term_is_killed_by_the_first_root_semantic_assertion` 将缺陷注入生产事件路径，确实由独立首根身份断言杀死。

## T4．六次实代数数与首入完备性

`RealAlgebraic/roots_interval` 的输入上限由 5 扩到 6；仍在平方自由化**之前**检查上限，7 次即便可约也拒绝。Sturm 变号计数、平方自由 gcd、闭端点处理、隔离区间唯一根验证、gcd 相等与区间细化比较不依赖次数 5 这一特殊数值。因此其原证明逐字适用于 6；没有更改任何近似阈值，没有放宽根数/符号判定，没有 truncation。

连续的简单紧多边形由分离变为闭集接触，首次接触必发生于某个顶点—边闭线段关联（边交叉或平行边首次接触也包含这种关联）。对每个双向 VE/EV，解 `F=0,G>=0,H>=0`。若 `F` 恒零，关联的开闭只可能在 G/H 的零点及闭窗端点变化；这部分继续使用 M5a 的恒共线逻辑。取所有候选的精确最小值，重新检查**所有**关联并重建法锥及 VV 完整并列集。初始贯入单列为 `initial_overlap`，比较量 `pd_closed` 冻结在初始几何，不把它称作步内出口。

生产复用 M5a `_event_times/_features` 和 `SE2Entrance2` 结果协议。由于 T3.1 保证同一块公共仿射映射正定向，静态凸/凹转角符号不变；法锥的边方向来自当前 P2 分子，所以复用筛选条件有效。生产与 oracle 的复用边界不同：独立 oracle 不导入这些模块。

门：`test_sixth_degree_root_isolation_has_independent_factor_and_bisection_oracles`（六次单项式有理二分、六线性因子、重根、闭端点、拒绝七次和非法隔离）；`test_sixth_degree_six_irrational_branches_have_exact_independent_brackets`（六个不同无理实根，逐分支独立整数符号括区间）；`test_complete_first_contact_matches_independent_oracle`（双块转动/应变、完整实根分区、独立 G0 每区间检查、所有标签）；`test_concave_p2_first_contact_has_independent_complete_cover_oracle`（凹环完整标签）；原 M5a 代数门仍执行，旧拒绝域用例由六次移至七次，未删除检验。

## T5．P2 对 P3 的严格全窗上界

P3 定义为同一 `c,d,E` 下 `c+s*d+[R_angle(s*theta)+s*E](p-c)`。令 `alpha=2 atan(u1)`，`u*=tan(theta/2)`，`epsilon>=|u1-u*|`。由于 `atan` 是 1-Lipschitz 且支持角域没有分支歧义，`|alpha-theta|<=2 epsilon`。

令 `f(s)=2 atan(s*u1)`。它的端点线性插值为 `s*alpha`，且

```text
f''(s) = -4*s*u1³/(1+s²*u1²)²,
max_[0,1] |f''| <= 4|u1|³.
```

二阶插值余项给出 `|f(s)-s alpha| <= (max|f''|)*s(1-s)/2 <= |u1|³/2`。三角不等式因此对所有 `s∈[0,1]` 同时给出

```text
|2 atan(s*u1)-s theta| <= |u1|³/2 + 2 epsilon.
||P2(s,p)-P3(s,p)||_2
  <= ||p-c||_2 (|u1|³/2+2 epsilon)
  <= ||p-c||_1 (|u1|³/2+2 epsilon).
```

第一不等式使用 `||R(a)-R(b)||_2=2|sin((a-b)/2)|<=|a-b|`。对全部顶点取最大 L1 半径，即 `p2_p3_bound(...)["position"]`；边上同重心参数的点随凸组合服从同界。它也给坐标逐分量上界。

本界显式含**半角近似误差**及**时间律差**两项；不含 binary64 末帧误差，后者必须由端点重建证据另加。它只认证规定的 P3，不认证任何未知的物理路径。返回值是严格上界，不声称最紧；时间律差的三次量也不等于 P1/P2 差异通常的二阶量。

门：`test_p2_p3_uniform_bound_contains_independent_interval_trigonometry` 用独立阶乘 Taylor 的有理区间（不是浮点 sin/cos）核对正/负角、零角与非零近似误差；全窗性由上面的解析余项证明，而不是用有限采样代替全窗证明。

## T6．投影包围与协变

对任意固定有理方向 n，`R(su)-I` 每个元素绝对值至多 `2|u|`。因此每个顶点的 `n·P2` 位于

```text
n·p + [min(0,n·(d+E(p-c))), max(0,n·(d+E(p-c)))]
    + [-rho,rho],  rho=||n||_1*2|u|*||p-c||_1.
```

所有顶点区间取包络得到 `projected_sweep`；线性函数在多边形上的极值位于顶点。两块包络**严格分离**方可提前返回 `no_contact`，等号不提前排除。此界可用于充分无接触证书；它不是精确最小距离。

`E` 在坐标旋转 Q 下变为 `Q E Q^T`，中心按点变换，d 按向量变换，u 保持；于是 P2 位置按坐标映射协变、首入时间/身份不变。应变充分域取 infinity 范数可能因旋转变得更保守；不保证域外输入在变换后仍被接收，门选取保持充分域的一般非对称输入。

门：`test_projected_sweep_contains_all_independent_rational_probes`；`test_p2_first_entrance_covaries_under_random_rotations_units_and_large_translations`（固定随机种子、一般有理旋转、尺度 `10^-6,1,10^6`、平移 `0,10^3,10^5,10^6`，并断言参数产物互异）。

## 独立 oracle 与冻结影响

`tests/m5b_independent_oracle.py` 导入 `fractions.Fraction` 与既有**测试专属** `m5a_independent_oracle` 的多项式、Sturm、G0 辅助代码。传递导入是 `fractions`、`functools`、`eab.kernel2d.g0_oracle`，后者仅用独立整数/有理 winding 与交段原语，其传递导入 `math.lcm`、`eab.oracle_construction`（不调用显示函数）。不导入生产 `dda_motion/se2/algebraic/motion/exact/global_entrance/construction` 的几何、根求解或法锥原语。

现有生产闭包唯一数值代码改动为 `src/eab/kernel2d/algebraic.py` 的次数上限；这触及 M5a/M5a2 历史绑定，必须由本单主报告记录真实重算，不能只换历史哈希。本文件不冒充已经完成该重算。
