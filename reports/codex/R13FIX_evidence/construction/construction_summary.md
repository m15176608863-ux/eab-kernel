# R13FIX 几何构造差分与全公开 API 普查分项报告

## 结论与边界

新增 `tests/test_r13fix_geometry_differential.py`，最终 **59 passed in 0.36s**。发现并修复三组实际生产构造错误：全 float 几何点积/叉积的中间范围损失、相对诊断先构造绝对噪声/面积的范围损失，以及 all-float 坐标基本运算/生成器不检查最终范围。

**不声称补齐全部公开 API。** `docs/r13fix_construction_inventory.md` 对全部 public 函数/方法和数据字段逐项分类；剩余缺口不伪装成已覆盖。`residual_probes.json` 记录仍未修的公开 raw 向量/坐标生成器范围行为，因此最终工单需要 PARTIAL，而不只是“测试更多即可”。

## 1. 修前红 → 修后绿

### 全 float 点积/叉积

- 范围：`kernel2d.geom.dot/cross`、`kernel3d.geom3.dot/cross`；仅全 float 输入改为 Fraction 原始乘积/总和后一次 checked scalar。Fraction、整数和 Dual 等原标量代数路径不改。
- 次正规反例：`s=2^-538`，`(s,s)·(2s,2s)=2^-1074`，原返回 `0.0`；叉积 `(s,-s)×(2s,2s)` 同样原返回 `0.0`。
- 上溢相消反例：`s=2^1020`，`(s,s)·(s,-s)=0`，原返回 `nan`；相同向量叉积应为 0，原也为 `nan`。
- 不可表达非零：最小次正规数乘自身原静默归零，现响亮抛 `ArithmeticError`。
- 修前 `geometry_before.log` 6 个真实红；其中另 3 个红是**新测试初始选错输入**（水平错位不产生有效 VV）而不是生产缺陷，已通过另设斜向错位 VV 构造纠正，未把它们计为修复成果。
- 断言：`public dot exact final construction`、`public cross exact final construction`、`pytest.raises(ArithmeticError)`。

### 相对诊断

- `s=2^-1070` 的立方体，`edge_noise` 原先先构造 `64*eps*C=0`，最终错为 0；独立有理定义应为 `64*eps/2 = 7.105427357601002e-15`。
- `s=2^-600` 及 `s=2^600/2^1018` 的立方体，`face_noise` 原先构造不可表达面面积而抛错，最终相对量 `64*eps` 实际可表达。
- `round_floor/noise_floor(minsub)` 原静默返回 0；现最终真实非零不可表达时抛错。
- `noise_before.log`：**6 failed, 1 passed**。修后全部绿。
- 修法：edge_noise/vertex_edges 对原始精确向量平方和做比例开根；face_noise 不构造面积而使用 exact Newell 平方做最终比值，周长定义为逐边已舍入长度的精确有理和；standalone floor 作 checked scalar。
- 不把面周长多根式升级成“正确舍入的真实根式和”合同。边长本身不在 binary64 范围时仍有残余范围限制。

## 2. 新增差分覆盖

Oracle 是测试内 Fraction 坐标差、点积、叉积、鞋带、三角体积/一阶矩、投影参数等公式；最终舍入使用独立 `construction_oracle` 的 binary64 胞参考，不调用被测几何原语。全部标量/向量分量用 `==` 逐值比，不靠绝对容差吞掉微量。

- norm/unit、2D 边法向/法锥、3D 面法向/棱方向/入射棱方向：`2^[-1070,-600,0,600,1018]`。
- 2D 面积/turn/point_side/centroid 与 3D face_area：`2^[-537,-530,0,500,509]`；另有 final area `2^1023`（先构造两倍面积会溢出）。
- 3D 体积与质心：`2^[-359,-350,0,330,338]`，非对称且剪切几何。
- 2D VE/EV/VV 全数字字段、facet_gap、独立距离：`2^[-1070,0,1018]`。
- 3D VF/FV/EE/VE3/EV3/VV3 的 normal、gap、两见证、参数、area 与精确 gap/area 证书：`2^[-1070,-537,0,509,1018]`。采用各向异性体让极端 gap 与可表达 area 共存，不被无关面积失败遮住。
- 3D closest hull、cone direction、点段/点三角/段段平方距离、表面距离、facet/support gap：次正规/普通/上溢边缘三尺度。
- 角度只核对缩放后的正交解析值；凸包/合并/精确表面仅核对源坐标保真，**非全部角度或拓扑证明**。

## 3. 真实内部变异

`geometry_final.log` 包含被捕获的原始红断言，变异发生在被测函数内部而不是事后改产物：

1. `face_area` 恢复 `0.5*sqrt(nn)`：`representable final face area rejected`。
2. `geom3.dot` 恢复浮点乘积再加和：`public dot exact final construction`，`nan != 0.0`。
3. `geom2.cross` 恢复浮点乘积再相减：`public cross exact final construction`，`0.0 != 5e-324`。
4. `Polyhedron.edge_noise` 恢复先算绝对 floor：`edge relative diagnostic exact ratio`，`0.0 != 7.105427357601002e-15`。

## 4. 既有回归与机器普查

- 集中回归：`test_kernel2d_covers_e3.py`、`test_invariance_geom.py`、`test_invariance_2d.py`、`test_r6fix_construction.py`、`test_r9fix_construction_rounding.py`，**3447 passed in 183.79s (0:03:03)**（日志在 `geometry_regression.log`）。该回归启动早于最终 noise 修复，故不能代替 root 的最终全套。
- `inventory_public_construction.py` 可复跑，AST 保留全部公开/私有函数方法及注解字段，并验证人工 nodeid 映射确实存在。
- 表格中“未确认”不等于“全无旧测试”；它意指没有人工确认到满足本单独立有理参考、极尺度、逐值绑定的完整门。不得用名称命中或测试数量反向证明。
- 几何原有测试未删除/放宽/skip/xfail；此次新增文件 59 格，保留全部网格。

## 5. 确认遗留

`residual_probes_before_coordinate_fix.json` 保留后续修复前的五项观察；`residual_probes.json` 是最终复测：

- all-float `geom3.add/sub/mul`、`geom2.add/sub/translate`、`box`、`Polyhedron.translated` 的不可表达输出已改为 checked 最终转换，前四个反例现分别抛 OverflowError/ArithmeticError。
- `face_noise` 在边长本身超 binary64 范围时仍会先拒绝边长，即使最终相对比例可表达。
- 混合 int/float 的 raw add 等原始代数路径仍可返回 inf；本次只在 all-float 分支加范围保证，未冒险改变 Fraction/Dual/混合标量语义。

另有完整普查表明的一般输入、多活跃集、读取器/转换器字段、普通 Dual 快路及诊断 policy 等未补齐范围。主报告须列入 PARTIAL 清单。

## 6. 收尾补修：all-float 坐标范围

- `coordinate_before.log`：1 failed, 5 passed；首个范围断言 `pytest.raises(OverflowError)` 在 `geom2.add(max,max)` 报 DID NOT RAISE。
- 最小改动：add/sub/mul 只有 all-float 分支先 Fraction 执行一项运算再 checked scalar；translate/translated 复用 add；box 复用 low=sub(center,half)、high=add(center,half)，仍是一项坐标加减，没有多步浮点重排。
- 次正规/普通/上溢边缘逐分量门为 `2^[-1074,-600,0,600,1021]`；另外最大值溢出与 minsub 乘半的非零下溢必须拒绝。
- 内部恢复 unchecked add 的变异由同一范围断言报红（DID NOT RAISE），`geometry_final.log` 打印证据。
- 最终新增几何文件：**59 passed in 0.36s**。root 全套是最后退出证据，此分项不代替它。
