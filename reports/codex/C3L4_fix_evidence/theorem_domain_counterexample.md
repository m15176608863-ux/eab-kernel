# WO-C3L4-fix：有限 μ 域上边界的定理反例（停止实施）

## 结论

**按工单原文，定理缺少证书夹逼点属于 `[0,mu_max]` 的前提，因而在上边界不成立。** 下面是标准 profile1 的一对摩擦生成列和一个活载列，不依赖不完整分支枚举、浮点舍入、一阶矩阵截断或接触骨架变化。

在 `mu*=mu_max=1`，给定 `s=1` 可以同时取得原文要求的 K 上 (a) 对偶可行证书与 (b) 原可行点/改进射线；但所有正扰动的域内 UNBOUNDED 集合均为空。若采用扩展实数约定，`mu_crit(epsilon)=+∞`；若不采用该约定，则该值无定义。两种解释下都不能得到有限右导数 `1`。

这属于工单要求发现后停止并报告的定理前提冲突。**尚未开始生产实现，也未自行添加 guard、放宽定义或选择新的边界合同。** 开工 H1 基线由主代理单独记录，不是修后验收；本记录不结束任何进程。

## 1. 模型在现有 profile1 输入族内

取仅有两个平移自由度的自由体，固定接触切向 `T=(1,0)`、法向 `N=(0,1)`；两列为 `N-mu T`、`N+mu T`。活载为 `(1,-t)`，恒载为零，旋转自由度被约束。归一化活载变量是第三个非负变量 alpha：

```text
maximize alpha
A(mu,t) x = 0, x >= 0

A(mu,t) = [ -mu   +mu    1 ]
          [   1     1   -t ]
b = (0,0), c = (0,0,1).
```

矩阵使用未缩放摩擦生成列；接触点、切向、法向、参考点和锚点均固定。`t=1-epsilon` 仅表示原始活载 y 分量的种子为 `+1`。没有非零 threshold μ 种子，没有几何高阶信息缺失，也没有接触骨架变更。该反例即使完整保留所有原始多项式项仍成立。

另一路只读复核已从真实几何进入当前 Python L1/L3：移动矩形 `((2,3),(3,3),(3,4),(2,4))`、固定支承 `((2,2),(3,2),(3,3),(2,3))`，移动 mask `(1,1,0)`，活载 `(1,-t,0)`。自动组装得到两个端点、两对完全相同的摩擦列，矩阵为 `[-mu,+mu,-mu,+mu,1]; [1,1,1,1,-t]`。合并重复生成列即上式，不改变可行锥；也可把本证书射线的第二对接触系数补零，直接用于未合并模型。基准 `t=1,mu_max=1` 得 `exact_threshold=1,attained=true`；扰动 `epsilon=1/16,1/256,1/4096` 均得 `bounded_on_domain`、无精确域内阈值，而域外 `mu=1/(1-epsilon)` 无界。该几何复核还逐一用 Fraction 验了10次显式limit查询的原始 LP 证书，并记录生产源前后哈希不变：真实几何结果（原 `boundary_geometry_probe.json`，已压缩归档，映射见 [historical_compaction.json](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_fix_evidence/historical_compaction.json)；脚本身份见 [boundary_geometry_probe_manifest.json](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_fix_evidence/boundary_geometry_probe_manifest.json)）。这里的标准库 K 证明与那份真实几何运行相互独立。

### 基准点

设 `mu_max=t0=1`。对于 `0 <= mu < 1`，

```text
y = (1/(1-mu), mu/(1-mu))
A^T y - c = (0, 2mu/(1-mu), 0) >= 0.
```

零原点可行，故这些 LP 都有最优值零，不无界。在 `mu=1`，`x0=0` 与 `r=(1,0,1)` 满足 `Ar=0`、`r>=0`、`r_alpha=1`，所以无界。于是基准域内的精确阈值确为 `mu*=1`，且是闭阈。

## 2. 原定理的两个 K 证书确实同时成立

令 `K=Q(eta)(epsilon)`，采用原文的顺序 `0<epsilon<<eta<<1`，令候选 `s=1`：

```text
t       = 1-epsilon
mu_minus= 1+(1-eta)epsilon
mu_plus = 1+(1+eta)epsilon.
```

### (a) 下夹点的对偶证书

记

```text
D = 1-t*mu_minus = eta*epsilon + (1-eta)*epsilon^2.
y_minus = (1/D, mu_minus/D).
```

按先 epsilon 最低非零次、再 eta 最低非零次定号，`D>0`，且 `mu_minus>0`。全部对偶松弛精确为

```text
A(mu_minus,t)^T y_minus - c
    = (0, 2mu_minus/D, 0) >= 0.
```

这完全满足原文 (a)，不需要对任何分量忽略高阶项。

### (b) 上夹点的原可行点和改进射线

令

```text
x0 = (0,0,0)
r  = ((t+1/mu_plus)/2, (t-1/mu_plus)/2, 1).
```

全部等式逐项为

```text
A x0 = b = 0
-mu_plus*r1 + mu_plus*r2 + 1 = 0
r1+r2-t = 0
r_alpha = 1.
```

`r1` 的首项为 `1`，故严格正；对于第二分量，

```text
t*mu_plus-1 = eta*epsilon - (1+eta)*epsilon^2 > 0
r2 = (t*mu_plus-1)/(2mu_plus) > 0.
```

因此所有原非负性、全部平衡等式及归一化改进条件都成立。这完全满足原文 (b)。

### 但是两个证书点都在定义域之外

```text
mu_minus-mu_max = (1-eta)epsilon > 0
mu_plus -mu_max = (1+eta)epsilon > 0.
```

它们不能对定义在 `[0,1]` 的阈值给出所宣称的上界。实闭域转移只会把上述域外证书转移为实参数域外证书，不会补出域内可行的无界点。

## 3. 整个域内集合为空的精确证明

对任意实数 `0<epsilon<1`，对**每一个** `mu∈[0,1]`，取

```text
y_domain = (1/epsilon, 1/epsilon).
A(mu,1-epsilon)^T y_domain - c
    = ((1-mu)/epsilon, (1+mu)/epsilon, 0) >= 0.
```

配合零原点可行，整个域的每个 LP 都是最优值零，均不无界。这不是对若干探测点的猜测：上式直接给出覆盖整个闭区间的对偶证书族。

等价地，对任何可行非负 `x=(r1,r2,alpha)`：

```text
alpha = mu(r1-r2) <= mu(r1+r2) = mu(1-epsilon)alpha.
```

由于 `mu(1-epsilon)<1`，必有 `alpha=0`。因此

```text
{mu∈[0,1] : LP(mu,1-epsilon) is UNBOUNDED} = empty.
```

如果将搜索域扩到正半轴，未截断阈值是 `1/(1-epsilon)`，其右导数确为 `1`；但那是另一个函数，不能代替工单明确写出的有界域函数。

## 4. 独立标准库可复跑核验

脚本不导入 `src/eab`、C++ helper 或第三方数学库。它以 `Fraction` 和完整稀疏双变量多项式实现有理函数恒等运算；定号按 `(epsilon次, eta次)` 字典序，不作 Laurent 截断。它输出：

- (a) 的三个精确对偶松弛及符号；
- (b) 的可行点、射线、所有平衡恒等式、非负性和 alpha 归一化；
- 两个夹点严格超出上界的 K 证明；
- 域内仿射 μ 松弛在 0/1 两端的非负证书，因而覆盖整个区间；
- 三组小有理 `(epsilon,eta)` 的精确代入核对。这些代入只是佐证，不是阈值/导数证明。

执行命令：

```text
python -B reports/codex/C3L4_fix_evidence/theorem_domain_counterexample.py.txt --output reports/codex/C3L4_fix_evidence/tmp/theorem_domain_counterexample.json
```

实测退出码 `0`，原始末行：

```text
THEOREM_DOMAIN_COUNTEREXAMPLE_OK lower_dual=1 upper_primal_ray=1 domain_unbounded_set_empty=1 finite_s_contradicted=1
```

[独立核验脚本](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_fix_evidence/theorem_domain_counterexample.py.txt) · 完整精确结果（原 `theorem_domain_counterexample.json`，已压缩归档，映射见 [historical_compaction.json](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_fix_evidence/historical_compaction.json)） · [原始末行](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_fix_evidence/theorem_domain_counterexample.log)

## 5. 需要 Claude 澄清的最小事项（未擅自采用）

1. **域内夹逼条件**：是否将 `0<=mu_minus<=mu_plus<=mu_max` 作为定理的显式前提，并要求在同一个有序域中精确核验？对于严格内点阈值该条件可由固定正裕度得到；对边界不能省略。
2. **上边界规则与空集约定**：扰动使域内无界集合为空时，阈值/导数用 `+∞`、undefined 还是特定 unresolved reason 表达？不能把域外未截断阈值导数作为域内值输出。
3. **下边界规则**：在 `mu*=0`，`s=0` 的对称下夹点是 `-eta*epsilon<0`；原模型只允许 `mu>=0`。是保留 unresolved，还是另订以域下界代替 (a) 的专门边界定理？后者不能由执行方自行引入。对于 `s<0` 两界均可能出域，更不能直接认证。
4. **接口保留域数据**：现 `CriticalParameter2` 有最终 bracket，但没有独立保留原始 `mu_max`；`mu_hi` 是缩窄后的证书端点，不总是原始搜索域上界。若按域内条件修订，Python/C++ retained payload 与证书必须能可靠绑定最初的域，不能把最后 bracket 高端偷偷当成 `mu_max`。

其他条件性实施草案（完整原始 primitive path、候选和 K 证书）均暂停，直到上述合同由 Claude 明确。没有更改设计正本、公共 ABI 或生产数学。
