# M5a：二维刚体转动入口块与首入（先行理论合同）

日期：2026-10-15。工单 WO-M5a；回退锚：开始时 `codex-work / 3bf5e95` 与最终文件清单。
范围仅 `D:/eab-wt/cx-e2`，不执行 Git 写操作，不改姊妹仓库或其他工作树。
**本稿在新内核实现之前写入。数学论证、拟议 API 与待执行门不是“已通过”声明；最终状态见 M5a 报告。**
目标是在明确的一步有理刚体轨迹上精确计算闭集首次接触，而不是从两个快照恢复唯一真实连续运动。
非目标：SE(3)、在线替换、接触力正确性、全配置空间曲面安排、材料多环输入、一般非零残差首盖稳定性认证。

## 1. 对象与两个三态（T1）

设 A、B 为平面紧致正则闭多边形实体。数学定义允许有限边界环；本阶段程序支持域为各一个无自交、全维、无零长边的简单环。
平直相邻边允许，但回折、重复边、自交和嵌套多环输入拒绝。环方向可规范化，特征身份必须还原到输入编号。

相对位形 `(t,theta) in R² × S¹` 的闭 C-障碍与贯入集为

```text
C = {(t,theta) : (R_theta A + t) ∩ B != empty},
P = {(t,theta) : int(R_theta A + t) ∩ int(B) != empty}.
```

实体三态：分离为 `C` 外，相触为 `C \ P`，贯入为 `P`。
拓扑三态：`C` 外、`boundary(C)`、`interior(C)`。相触不能无条件等同于配置障碍边界；紧配合可能存在接触内缝。
本单返回的是实体三态；冻结切片仍保持 M3 已区分的实体/拓扑语义。

**固定角切片定理。** 对每个固定转角，

```text
E_theta = {t : (R_theta A+t) ∩ B != empty} = B ⊕ (-R_theta A).
```

证明：左侧等价于存在 `a in A,b in B` 使 `R_theta a+t=b`，即 `t=b-R_theta a`。不需凸性。
所以固定有理旋转后的 A 可以不改 M3 语义地交给 `GlobalEntrance2`。
**全体 C 不再是 R² 中一个固定 Minkowski 差**，不能把固定切片结论扩成跨转角的平移射线结论。

### 1.1 接触族与边界的限定

写 `cross(x,y)=x_x*y_y-x_y*y_x`。A 顶点 `a` 与 B 边 `[b,b+e]` 的 VE 族：

```text
cross(e, R_theta*a+t-b)=0,
0 <= dot(e,R_theta*a+t-b) <= dot(e,e).
```

B 顶点 `b` 与 A 边 `[a,a+f]` 的 EV 族：

```text
cross(R_theta*f, b-t-R_theta*a)=0,
0 <= dot(R_theta*f,b-t-R_theta*a) <= dot(f,f).
```

VV 族为向量方程 `R_theta*a+t=b`，是上述闭 VE/EV 族的端点退化，不能因此删掉并列闭段关联。
一般 VE/EV 族是三维配置空间中的曲面片，VV 是其较低维交会；平行边重叠由端点—边闭族覆盖。
`boundary(C)` 包含于这些族之并：边界位形不能有内部相交；非平行边内部横交对小扰动稳定，亦不是边界。
剩余边界接触必有端点落在边上。**反包含不成立**：这些方程也含贯入中的边界关联和接触内缝。
取真实配置障碍边界必须再作全局外部邻域判别；本单没有构造整个三维配置空间边界安排。
运动首时刻处的 `incidences` 是全部闭段关联；`features` 是再经 M3 同口径局部法锥筛选的有效盖及 VV。
局部法锥标签不被冒称为全配置空间边界证明。

## 2. 精确旋转与一步轨迹（T2）

定义

```text
D(u)=1+u²,
M(u)=[[1-u²,-2u],[2u,1-u²]],  R(u)=M(u)/D(u).
```

直接展开得 `M^T M=D² I`、`det(M)=D²`，故 `R^T R=I, det(R)=1`。
其角度是 `theta=2 atan(u)`，单 chart 覆盖 `-pi<theta<pi`；`u` 有理时全部矩阵元素有理。
旋转方向约定为逆时针正向；输入有限 binary64 按其精确有理值解释，不以浮点 sin/cos 判事件。

数学公式对任何有限有理 u 有效。**M5a 拟议公开路径保守限制 `|u1|<=1`，即每块一步转角不超过 90°**；
它是已声明的研究级支持域，不是声称 tan 半角表示在 90° 失效。接近 pi、跨 chart、多圈绕转须响亮报域外，
不能取主值后静默当成小转角；分段跨 chart 尚未实现并列入 PARTIAL。固定坐标系的 180°/270° 变换仍可用于元门。

对每个块 `i in {A,B}`，给定参考点 `c_i`、参考点位移 `d_i`、终点半角参数 `u_i`：

```text
0 <= s <= 1,
C_i(s)=c_i+s*d_i,
D_i(s)=1+(s*u_i)²,
M_i(s)=M(s*u_i),
X_i(s,x)=C_i(s)+M_i(s)*(x-c_i)/D_i(s).
```

端点精确为 `X_i(0,x)=x`、`X_i(1,x)=c_i+d_i+R(u_i)*(x-c_i)`。
对任意两点，其差为同一 `R(s*u_i)` 乘原差，故长度、方向次序、简单性、边长与面积全程保持。
因此有效初环加合法有理参数就给出整步有效刚体轨迹，无需照抄 M4c 非刚体轨迹的全步退化求根。
若用户传两端几何而不是轨迹参数，则必须先拟合并保留残差，不能把不相容端点宣称为此公式的准确终点。

### 2.1 不等于匀角速度或 DDA 的真实步内运动

角速度 `theta'(s)=2*u_i/(1+s²*u_i²)`，除 `u_i=0` 外不恒定。
当一个块围绕固定参考点纯转动、另一个静止时，任何严格单调覆盖同一角区间的时间重参数化经过相同位形，
首盖顺序相同，但 s 时刻不同。两块同时转动、参考点同时平移或采用常体速度 SE(2) 指数插值时，
一般不存在同一个时间重参数化使两条配置轨迹重合；可以穿越不同接触曲面，因而状态、首盖甚至是否接触可能不同。
本轨迹只是一族**明示且可精确认证的模型路径**，不声称是 b-DDA 的匀角速度螺旋运动或真实步内积分。

## 3. 首入存在、事件完备与五次上界（T3）

初态分离时定义

```text
tau=min {s in [0,1] : X_A(s,A) ∩ X_B(s,B) != empty}.
```

集合为空返回 `no_contact`；擦触、端点接触和单时刻相触都属于闭集接触。
初态相触返回 `s=0` 与全接触集；初态贯入独立返回 `initial_overlap`，不伪造分离意义的“首入=0”。

**存在性。** 两块紧且轨迹连续，若一列接触时刻收敛，接触见证可取收敛子列，极限仍为接触，
故时刻集为 `[0,1]` 中闭集，非空必有最小元。

**VE/EV 完备性。** 首次接触不可能含共同内部点，否则其邻域在稍早时刻仍重叠，矛盾。
两边相对内部的非平行横交同样对小扰动稳定，不能是首次接触的唯一见证。
余下为端点落边或共线闭段重叠，后者至少有一端点属于对边。故双向 VE 枚举含首次接触，包括 VV、多特征并列与共线退化。
该论证不需凸性，也不以离散采样或浮点近零判断替代连续完整性。

### 3.1 消去正分母后每个事件最多五次

A 顶点的局部坐标记为 `a=x-c_A`。B 边起点局部坐标 `b=q-c_B`，边向量 `e=r-q != 0`。
设 `L=C_A-C_B`、`Q=D_A*D_B>0`，定义

```text
W = L*D_A + M_A*a,
F = cross(M_B*e, W) - Q*cross(e,b),
G = dot(M_B*e, W) - Q*dot(e,b),
H = dot(e,e)*Q - G.
```

直接展开并使用 `cross(M_B e,M_B b)=D_B² cross(e,b)`、
`dot(M_B e,M_B b)=D_B² dot(e,b)` 得：

```text
cross(X_B(r)-X_B(q), X_A(x)-X_B(q)) = F/Q,
dot(X_B(r)-X_B(q), X_A(x)-X_B(q)) = G/Q.
```

B 边长度平方仍为 `dot(e,e)`，故点落在**闭**边上当且仅当 `F=0, G>=0, H>=0`。
`deg M_i<=2, deg D_i<=2, deg L<=1`，故 `deg W<=3`，`deg F,G,H<=5`。
交换 A/B 得 EV。只有一个转动块且另一个固定时上界降为三次；单块固定轴纯转动时进一步降为二次。
两块都转动但参考点均不动时不超过四次。这里没有先平方相对点差制造十次式，也没有忽略高次项。

### 3.2 恒共线与端点

若 `F` 不是零多项式，枚举其 `[0,1]` 全部不同实根，再用 `G,H` 的精确符号筛选。
若 `F` 恒零，点一直在边的支撑直线上，不能跳过此对：可行时刻是 `G>=0,H>=0` 的闭集。
把 G、H 的非零多项式实根和 0、1 排序，其间开区间符号恒定；若最早可行区间有正长度，闭性使它的左端也可行。
因此只需检验这些端点即可找到最早可行时刻；若 G 或 H 恒零，另一式及窗口端点仍完备。
所有候选并集有限，精确取最小，再在该时刻**重枚举全部** VE/EV/VV，不能只保留触发最小值的一对。

## 4. 精确实代数数及显示（T4）

时间用“非零有理多项式的指定实根 + 有理隔离区间”表示；生成多项式次数不超过五。
不要求一般五次根有根式。先用 `gcd(p,p')` 去重根，再用有理 Sturm 序列计数隔离。
Sturm 序列为 `p,p',-rem(p,p'),...`；去掉求值为零的项计符号变化。非根端点 a,b 的根数为 `V(a)-V(b)`。
端点根单列处理，避免把开区间计数当成闭区间。重根去重后仍保留其接触事件，不把“无符号翻转”等同于无根。

**Sturm 计数论证。** 序列内部项过零时，前后邻项符号相反，局部变化数不变；
平方自由 p 的简单实根处，p 与 p' 的首对使变化数由左到右减少一。余处连续且无零项变化，
故端点变化数之差恰为不同根数。有理二分可避开/单列有理根；不同根的正分离距离保证隔离终止。

**判等与排序。** 两个表示允许不同多项式。先计算有理 gcd；若两条指定根的隔离区间交集含 gcd 的同一根，二者相等。
不是简单“gcd 非常数就相等”，也不是“区间重叠就相等”。相等被精确识别后，
不同根的区间反复有理细分直到分离即可排序，因有限不同实根必有正距离而终止。
对于根 alpha 上的另一个有理多项式 q，先判公共根得零；否则区间细分到 q 的符号不再跨零，得到其严格符号。
近邻根、同一根的不同生成多项式、重根和有理根均不得调用 float/epsilon 作身份判断。

显示值是可选 binary64 构造量，只许经 `construction.py`。隔离区间要细化到舍入唯一，
恰在舍入中点的有理根用精确比较和 ties-to-even；不得把一个未足够收紧区间的中点当成已正确舍入根。
证书内多项式系数、区间、参数、点坐标使用有理字符串，不是浮点构造；显示与谓词严格分层。

### 4.1 精确区间快速排除（实现阶段补证）

Horner 区间运算每次乘法取四个端点乘积的最小/最大，再加系数，归纳包含所有区间内的多项式值。
因此有理 Horner 包含区间严格不含 0 时，该输入区间没有根；若包含 0，只表示未知，不能据此报有根或无根。
同样，在代数根隔离区间上另一个多项式的 Horner 包含区间严格为正/负时，可在 gcd 之前安全给出其符号。

另一种安全快路是 Bernstein 系数：令 `x=lo+(hi-lo)*y, 0<=y<=1`，原幂系数为 p_k，次数 n，

```text
q_j=(hi-lo)^j * sum_{k>=j} p_k*binom(k,j)*lo^(k-j),
b_i=sum_{j<=i} q_j*binom(i,j)/binom(n,j).
```

于是 `p(x)=sum_i b_i*binom(n,i)*y^i*(1-y)^(n-i)`。
各 Bernstein 基函数非负且和为 1，故取值在系数最小/最大值之间。
若所有 b_i 非负且 b_0、b_n 严格为正，端点值严格为正，内部所有基函数均严格为正，亦严格为正，故闭区间无根；
全非正且两端严格负的情形对称。其余情形一律“未知”并回退完整 Sturm，不删除端点根或双重擦触根。
上述仅是有理包含证明的剪枝，不是浮点阈值；命中率不能改变代数数/首入合同。

## 5. 平移退化、闭式与不变性（T5）

当 `u_A=u_B=0` 时，`D_i=1,M_i=I`，逐点轨迹严格变为 `x+s*d_i`。
接触等价于 `s*(d_A-d_B) in B-A`，所以 M3 `first_entrance((0,0),d_A-d_B)` 的 `[0,1]` 结果逐值相同；
又因它与 M4c 端点弦轨迹逐点相同，时刻、初态、闭段关联、有效盖与全部并列也逐值相同。
零相对位移时直接按初态解释，不调用拒绝零方向的 M3 射线 API。
实现必须让一般事件路径参加退化一致门，不能用直接返回旧 API 的分支掩盖新路径错误。

初态贯入的比较量冻结为 `PD_closed(0)`：在步初 `E_0=B-A` 上到完整真实边界（含 E 洞壁）的距离、
所有并列最短点及其有效盖。它不随本步 u 改变；不是沿轨迹脱离时间，也不是旋转位形空间中的最短逃逸，更不是 legacy 弹簧压入量。
材料限单环不等于 E 无洞；带洞门应明确为 **E 的洞**，不能冒称支持材料多环。

### 5.1 闭式对照

正方形 `[-1,1]²` 绕原点逆时针转动，右侧墙内边为 `x=h`，其中 `1<h<sqrt(2)`，墙高覆盖全部角点。
在 `0<=theta<=pi/4`，右端支撑为 `cos(theta)+sin(theta)`，首次接触满足

```text
(1+h)*u² - 2*u + (h-1)=0,
u_first=(1-sqrt(2-h²))/(1+h),
s_first=u_first/u1  (u1>0 且事件位于窗口).
```

取 `h=5/4` 得无理首时刻；取 `h=7/5` 得 `u_first=1/3`。闭式不仅比根值，还应比实际右下角身份与墙边标签。
绕顶点的杠杆：`A=[(0,0),(L,0),(L,-w),(0,-w)]`，以原点为固定转轴，上方横墙内边 `y=h`。
在正向不超过 90° 的区间内，最高角为原顶点 `(L,0)`，其高度为 `2Lu/(1+u²)`；`0<h<L` 时首次接触

```text
h*u²-2L*u+h=0,
u_first=(L-sqrt(L²-h²))/h.
```

取 `L=5,h=3` 得 `u_first=1/3`；墙水平范围必须覆盖该接触点，并独立排除别的墙边先接触。
这些例的论证只用旋转坐标与矩形支撑，不 import 生产事件多项式或求根，适合独立主 oracle。

### 5.2 刚体坐标与单位协变

令全局相似变换 `T(x)=lambda*Q*x+z`，其中 `lambda>0`，`Q` 为有理二维旋转。
同时变换初环、`c_i`，且 `d_i'=lambda*Q*d_i`，保留 `u_i`。二维旋转可交换，故

```text
X_i'(s,T(x)) = T(X_i(s,x)).
```

因此首时刻、状态、带身份的特征集合不变，点按 T 变换，PD 距离乘 lambda、平方距离乘 lambda²。
对称形状的 lex 代表不保证旋转协变，必须比较所有最优点集合。大平移由精确有理坐标处理，不引入绝对容差。
**参考点是轨迹合同的一部分**：只换 c 而保持 d、u 不变一般会改变轨迹；不能把这种不同路径误叫坐标不变性失败。
为比较同一物理端点可相应改 d，但这仍不保证线性参考点轨迹在步内相同，故元门只能按上式整体变换。

## 6. 快照刚体拟合与认证边界（T6）

快照两端顶点按稳定身份对应为 `x_j,y_j`。初参考点可取顶点有理算术均值 `c=mean(x_j)`，
末参考点取 `c'=mean(y_j)`，平移 `d=c'-c`。以居中点形成点积/叉积协方差估计角度，
选定一个**显式保存的精确有理** `u1`，再计算 `yhat_j=c+d+R(u1)*(x_j-c)`。
拟合算法可以用近似值提出 u 候选，但选定后的变换、残差和事件必须重新在精确有理数上计算；
不得从“非常小”阈值把残差改零。具体确定性有理参数选择和舍入合同应由实现及门补记；不预称全局最优 Procrustes 拟合。

定义

```text
r_j = y_j - yhat_j,
delta_i = max_j max(abs(r_j.x),abs(r_j.y)),
delta_pair = delta_A+delta_B.
```

全部量精确有理；报告存 L-infinity 单位，并区分其与欧氏残差，不能混单位。
delta 汇集了应变、快照 binary64 舍入与本次有理参数选择的拟合误差，单凭它不能拆解出每一来源。
`delta=0` 当且仅当这组保存端点与选定刚体端点逐点一致。
认证标签应为“**指定刚体模型、端点精确相容**”，不能叫“与端点弦轨迹相同”：
即便 delta=0，只要有非零转动，圆弧与 M4c 的弦通常就不同。
它同样不证明 b-DDA 在两个快照之间实际走了本轨迹；所有首入结论仍带该模型限定。
`delta>0` 统一计未认证，不进入认证一致/不一致分母。两条模型分别精确计算后结果相等只是描述性一致，不是稳定性证书。

### 6.1 为什么不能拿端点残差认证整段首盖

只约束两端的连续轨迹可以在步内偏离任意远后返回；即使端点残差为零，也不能约束未指定的内部路径。
即便另外给出整段位置误差上界，首盖平局附近任意小扰动仍能拆分并列集。
一般非零 delta 首盖不变需要**整段**轨迹误差界、目标事件唯一且横截、竞争特征在此前有严格间隔等证书，
不能只比较两个端点或近似采样。M5a 不主张已证明并实现这一证书；该项明确 PARTIAL。

### 6.2 实现前补充：确定性有理拟合与安全宽阶段

拟合令 `p_j=x_j-mean(x), q_j=y_j-mean(y)`，`Q0=sum dot(p_j,p_j)>0`，
`c0=sum dot(p_j,q_j)/Q0`、`s0=sum cross(p_j,q_j)/Q0`。
若 `c0²+s0²=1` 且 `1+c0!=0`，直接取 `u=s0/(1+c0)`；精确刚体输入可由此恢复精确有理半角。
否则令 `N=c0²+s0²`，若 N 有有理平方根则精确取根；没有时用整数平方根构造不大于真值的 `2^-80` 网格近似，
提出 `u=s0/(sqrt_approx(N)+c0)`，再作明确分母上限的确定性有理近似（拟定 `2^40`）。
分母为零、无确定角度、返回参数超过公开支持域时响亮失败，不以钳位方式假装属于支持域。
该过程只提出有限分母参数，不声称在该有理集合中全局最小化残差；精确残差一定用最终参数重算。
精确单位协方差的分支不能经过 denominator limit，否则可把原来严格刚体端点错误改成有残差。

**宽阶段引理 T8（代码注释的别名，属于本节 T6 对接合同）**：安全宽阶段只准排除被证明不接触的块对。对 `v=x-c`、`w=s*u`，
`R(w)-I` 的对角元素为 `-2w²/(1+w²)`，非对角元素为 `±2w/(1+w²)`。
在 `|u|<=1,0<=s<=1` 上各元素绝对值不大于 `2|u|`，故

```text
|R(su)*v-v|_infinity <= 2|u|*|v|_1.
```

任意固定有理方向 n 上得到

```text
n·X(s,x) in n·x + [min(0,n·d),max(0,n·d)]
                 + [-rho,rho],
rho=|n|_1*2|u|*|x-c|_1.
```

取全部顶点下界最小、上界最大，得到整个刚体与所有时刻的投影包含区间（实体对线性函数极值在顶点）。
两块的包含区间**严格分离**才可判全窗 `no_contact`；等号可能为闭集接触，不能排除。
n 可用坐标轴或任一初始边法向，选择不影响证明，只影响剪枝效率。
它不是采样，也不依赖 legacy 候选表；若轨迹参数变化，包含区间必须重算。

## 7. 验证合同及主张索引（拟议，完成状态以后续报告为准）

以下各行是必须具名落地的门，不是完成打勾；实际 pytest 节点名称落定后在本节末尾追加索引，不重写历史先行合同。

| 主张 | 必须观测的语义门 |
|---|---|
| T1 固定切片 | 独立有理旋转坐标 + M3 切片实体/拓扑状态；E 洞与接触内缝 |
| T2 刚体、端点、符号 | 两端逐值闭合、距离平方不变、逆时针非对称例、域外拒绝 |
| T3 五次与完整首入 | 解析多项式同值、闭式平方/杠杆、恒共线、VV 和完整并列集 |
| T4 实代数算术 | Sturm 根数、重根、不同生成多项式公共根、近邻根、独立有理二分、显示三档 |
| T5 退化一致 | L/槽角楔/互锁截面/零间隙/E洞/共线，三档尺度，M3+M4c 全字段逐值 |
| T5 协变 | 有理旋转含 90° 系列、非对称大平移、单位缩放；集合而非单见证 |
| T6 认证分母 | 精确刚体合成输入 delta=0；加非零应变 delta>0；不得混入认证 MATCH |
| 影子闭集 | 15例×30步完整冻结；全1810步完整源与末帧核验、逐对分类、未分类红 |

独立 oracle 允许 import `fractions`、测试工具及既有 `g0_oracle`；不得 import 生产旋转公式、事件生成、根隔离、
法锥筛选再冒称独立。有理 s 上独立重建几何并用 G0 实体三态只能证明采样处，
完整首入 oracle 还需独立根/区间边界，或解析闭式的区间内排除证明。随机差分含凹形、并列、无理时刻，固定种子。

必做内部变异：隔离区间错位、选错根支、近似相等、转动符号反号、退化分支绕开一般路径、终点不闭合。
先屏蔽源码哈希绊线，再确认红在对应语义断言；源码改动哈希本身不是有牙门。
所有新公开构造登记 inventory，静态构造门零违例；整数标签、有理证书、状态不是浮点构造量。
全套四片要求执行节点多重集合等于收集节点，0 skip；新增门累计时间与全套增量不可偷换。
禁止新建 Git worktree，若以本树 tmp 内新鲜字节副本替代，只能按其真实口径报告，不冒充提交后 worktree 或六路 G6。

## 8. 文献核验与理论归属

本单的轨迹选择、正分母消去、五次上界、退化一致与残差边界由本文直接推导，不宣称学术首次。
文献状态以本次实际阅读为准，旧报告的“已核”不自动继承成这次已核。

| 文献 | 状态 | 本单核验范围与不承担的主张 |
|---|---|---|
| S. M. LaValle, *Planning Algorithms* (2006), Ch.4, §4.2.1、§4.3.1–4.3.3 | **已核原文（所列相关节，不是全书）** | 作者公开版 pp.145–146、156–166：平面位形、C-障碍定义、平移 Minkowski 差、含转动 VE/EV 接触与代数化；不据此声称本实现或五次轨迹定理已被该书证明。链接：[作者 Ch.4 PDF](https://lavalle.pl/planning/ch4.pdf)。 |
| Basu, Pollack, Roy, *Algorithms in Real Algebraic Geometry*, 2nd ed. (2006) | **未核原文** | 本次仅核作者下载页及书目，不以此替代 §4 的 Sturm/gcd 证明或实现门。链接：[作者下载页](https://www.math.purdue.edu/~sbasu/bpr-posted1.html)。 |
| 石根华 E(A,B) 及设计正本引用的历史实现论文 | **未核原文** | 本单未重新核对外文论文，不作优先性、还原原算法或真实 DDA 步内连续路径的主张。 |

本地背景已读 `docs/m3_global_entrance_design.md`、`docs/m4c_motion_entrance_design.md`、
`docs/m4c_difference_ledger.md`、`reports/codex/M3_report.md`、`reports/codex/M4c_report.md`、
`docs/plan_20260921.md` 的 M5 与诚实条款。它们是仓库合同与历史证据，不是外文原论文核验。

## 9. 明确保留的研究边界

1. 只处理给定单 chart、每块不超过 90° 的一步轨迹；跨 chart 分段、接近 pi 与多圈运动未支持。
2. 输入材料限单环；固定切片 E 可有洞，但材料多环未支持。
3. 计算沿给定路径的首入，不构造完整 `R²×S¹` 障碍曲面安排，不给出 SE(2) 最短逃逸。
4. 非零端点拟合残差不认证真实运动首盖；零残差也只认证端点相容的指定刚体模型，不恢复真实连续积分。
5. 到 SE(3) 尚缺多 chart 旋转表示、双体 VF/FV/EE 完备事件、退化共面/共线分支、次数与代数复杂度、
   独立三维 oracle 和刚体拟合信任合同；二维五次结论不得照搬三维。
6. 论文级正确性、物理标定、生产替换、完整独立 G6 和提交后新鲜 worktree 退出仍由后续专项决定。

## 10. 实施后具名门索引（不替代最终执行报告）

| 理论合同 | 实际门 |
|---|---|
| T1 固定切片复用 M3；旋转坐标有理 | `test_m5a_se2.py::test_fixed_slice_is_m3`（凹形、三档、独立 G0）；E 洞/紧配合在下面平移家族门，不宣称额外旋转带洞穷举 |
| T2 刚体、端点、方向 | `test_rotation_is_rigid_and_endpoints_close`；`test_clockwise_feature_identity_and_unsupported_domains_are_explicit` |
| T3 首入完备、五次与全并列 | `test_m5a_oracle.py::test_random_complete_events_match_independent_sturm_and_g0`（十个双体五次输入、独立分段检查）；`test_square_center_rotation_closed_form_and_two_real_roots`；`test_pivot_rotation_has_independent_lever_closed_form` |
| T3 恒共线、初态与闭窗 | `test_initial_states_zero_motion_and_persistent_collinearity_equal_m4c`；`test_rotating_closed_endpoint_is_not_lost` |
| T4 隔离、判等、排序、重根 | `test_m5a_algebraic.py::test_root_isolation_matches_independent_rational_bisection`；`test_gcd_equality_means_the_same_selected_common_root_not_any_common_root`；`test_repeated_rational_and_closed_endpoint_roots_are_retained_once`；`test_adjacent_algebraic_roots_do_not_become_equal_at_a_float_tolerance` |
| T4 显示与精确快排除 | `test_algebraic_display_is_in_its_independent_binary64_midpoint_cell`；`test_algebraic_display_resolves_exact_ties_underflow_and_overflow`；`test_exact_interval_rejection_is_conservative_and_preserves_endpoint_roots` |
| T5 平移逐值、PD 冻结 | `test_zero_rotation_is_exactly_m3_and_m4c_all_fields`；`test_initial_pd_is_frozen` |
| T5 相似变换协变 | `test_se2_is_rigid_frame_and_unit_covariant`；`test_two_rotating_translating_bodies_transform_with_their_reference_points` |
| T6 精确拟合及未认证残差 | `test_m5a_replay.py::test_exact_rational_rigid_fit_recovers_rotation_and_zero_residual`；`test_guard_nonzero_residual_never_enters_certified_denominator`；`test_fit_and_residual_displays_round_once_in_three_bands` |
| T6 宽阶段包含界 | `test_projected_sweep_contains_independently_evaluated_rational_paths`；`test_swept_projection_is_only_a_sufficient_separation_certificate` |
| oracle 自校验与真变异 | `test_independent_oracle_is_self_checked_on_repeated_adjacent_and_irrational_roots`；`test_independent_cayley_path_closes_without_production_rotation`；`test_independent_oracle_detects_lost_degree_five_term_inside_kernel`；外部实际源变异见 `tools/m5a_mutation_evidence.py` |

该表是主张到测试的可追踪性，不把有限测试误作全输入域形式化证明，也不把专题协作复核误称独立六路 G6。
