# WO-T1b：独立平移证书核验器

结论：已经实现可独立核验的有理逃逸折线、严格困住闭折线和保守晃动范围；这些核验器本身不承担生产搜索完整性或全算例完成的声明。

## 接口及新增清单候选

- `kernel2d.translation_certificates.translation_segment_is_free(moving, obstacles, start, end) -> bool`。
- `translation_segment_strictly_blocked(moving, obstacles, start, end) -> bool`；仅在同一个独立凸片对严格覆盖整段时为真，跨片的曲线应由生产端显式细分。
- `verify_escape_certificate(moving, obstacles, path) -> CertificateVerification`。
- `verify_trapping_certificate(moving, obstacles, closed_path) -> CertificateVerification`；闭曲线必须显式重复首点。
- `CertificateVerification`：`valid / reason / checked_segments / winding_number / witnesses / ray_direction`。
- `verify_wobble_bounds(moving, obstacles, closed_path, radius) -> WobbleBoundsVerification`。
- `WobbleBoundsVerification`：`valid / reason / area_lower / area_upper / diameter_squared_lower / diameter_squared_upper`。

以上输入是**腐蚀后的**简单多边形，顶点和折线坐标只能为整数或 `Fraction`。不修改已有公共 schema；这些接口尚待所有者决定是否并入设计。

## 独立性与数学依据

核验模块只导入标准库的 `dataclasses / fractions / functools`，没有导入生产几何、E/O 构造、`GlobalEntrance2`、生产三角剖分或 `exact.polygons_overlap_exact`。具名门 `test_verifier_imports_no_production_geometry` 对真实源码 AST 核对这一边界。

1. 独立检查环简单性、非退化性、逆时针方向与共线回折；凸输入保留整片，凹输入使用独立耳切，选择字典序最小的合格耳。
2. 两凸片严格重叠当且仅当它们在双方所有边法向上的投影严格重叠。将位移写为 `p+t(q-p)` 后，每个投影约束成为关于 `t` 的严格仿射不等式；逐个求其开参数区间与 `[0,1]` 的交。交非空则整段中有贯入，不能靠端点代替。
3. 困住证书每段的两个端点满足**同一凸片对**的全部严格投影不等式。仿射性证明整条闭线段均严格重叠；见证索引独立重新生成，不信任生产 cell 或生产标签。有理射线穿越法计算关于零点的整数绕数；原位自由且绕数非零，故原位自由分量不能到无穷。
4. 任意多边形的严格面积重叠可用有限独立凸分片对的严格重叠并集表示；只接触的边/点仍可通行，不能把 `int(E)` 当成 O。

## 逃逸末端约定的澄清

“包围盒直径”在本模块明确为配置空间障碍的包围盒直径，而不是零件本身的包围盒直径。包围盒直接由所有 `b-a` 坐标极值计算，不调用生产 E/O。除了满足 `|endpoint|² > diagonal²`，还要求终点严格处在该矩形外；返回继续远离该矩形的坐标轴方向，独立证明从末端至无穷的整条射线均自由。

单凭“离零点超过矩形直径”不总能推出“在矩形外”：矩形 `[100,101]×[100,101]` 就是反例（原点不在矩形内）。这不是对已经核验的自由路径作反例，而是明确补全末端到无穷的几何证明，不依赖隐藏的“原点位于障碍包围盒内”假设。

## 晃动范围

给定已通过核验的闭曲线，令其包围矩形宽高为 `dx,dy`。由绕数在不穿过曲线时保持不变，原位自由分量必在该矩形内，故面积上界 `dx*dy`，直径平方上界 `dx²+dy²`。

下界用原点为中心的**填充**闭正方形 `[-r,r]²`。核验器独立对“移动凸片 + 闭正方形”与固定凸片作 SAT：沿法向 `(nx,ny)` 将移动片投影扩张 `r*(|nx|+|ny|)`，再加上正方形的两个坐标轴。没有构造 Minkowski 多边形，也不只检查四条边。通过后整个正方形与原点连通且自由，面积下界 `4r²`、直径平方下界 `8r²`。`r=0` 是诚实但平凡的下界。

`test_wobble_checks_the_filled_square_not_only_its_boundary` 在正方形内部放入与四边均不交的小障碍，确认核验器拒绝这一假下界。

## 有牙的门

- `test_mutation_accepting_nonstrict_enclosure_is_killed`：在真实核验函数源码内把严格边界拒绝 `<= / >=` 改为 `< / >`，同一个“接触边界不得作为严格困住证书”语义断言报红。
- `test_mutation_checking_only_escape_endpoints_is_killed`：在真实段核验函数源码内改成只看两个端点，同一个“路径中段穿入必须拒绝”语义断言报红。
- 原点占据、绕数为零、未闭合、经过原点、非有理坐标、非简单或退化环、凹形输入、顺时针/共线输入均有具名门。
- 精确接触允许，`2^-80` 的真实穿入拒绝；不引入容差。
- 3/5–4/5 精确旋转、种子 20261022 的五次随机有理旋转；平移量 `0,10³,10⁵`；尺度 `1/128,1,128` 均核验。小特征与大坐标同时出现。

## 本分工验证记录

最后一次定向命令：

```powershell
$env:PYTHONPATH='src;tools'
$env:PYTHONDONTWRITEBYTECODE='1'
$env:TEMP=(Join-Path (Get-Location) 'reports/codex/T1b_evidence/tmp')
$env:TMP=$env:TEMP
python -m pytest -q -p no:cacheprovider --basetemp reports/codex/T1b_evidence/tmp/pytest_certificates_review tests/test_tia2d_t1b_certificates.py
```

最后一行原样：

```text
28 passed in 0.14s
```

对本分工两个 Python 文件调用现有 `check_exact_construction.scan_text(..., repository_root=Path.cwd())`：

```text
certificate static construction violations: 0
```

现有纯度工具：

```text
kernel purity: 0 violations
```

没有修改静态准入记录。未运行本分工的全档、未创建新鲜树、未作 Git 写操作；完整集成快档/全档由总负责人记录。本分工不负责“只看凸包判有界”生产变异，由生产搜索门核查。

## 内部质量复核（不是 Claude 的独立对抗验收）

阅读 `translation_space.py` 与 `erosion.py`，逐项核对开集合段参数、严格片交中心、绕数闭环、`L∞` 最近边界半径、凸腐蚀偏置符号、凹腐蚀接触事件与填充结构元包含条件。

发现并修复一项可重现的输入消费缺陷：`critical_tolerance` 重复使用障碍迭代器时，低端计算耗尽迭代器，高端误以空障碍族核验逃逸。默认燕尾榫在区间 `[0,1/32]` 两端实际均困住；修复前 tuple 输入返回 `UNPROVED`，同值 iterator 输入错误返回 `CERTIFIED_BRACKET`。总负责人已在入口冻结移动多边形、障碍族和自定义结构元；单次 `tolerance_component` 也冻结需反复使用的结构元。新增 `test_critical_tolerance_freezes_iterators_before_repeated_queries` 同时守护三个 iterator 输入与单次公差查询。

未发现第二项可复现的数学错误，但本次只是内部质量复核，不是另一路独立验收。遗留的资源注意项：生产 `max_cells` 在构造各 `GlobalEntrance2` 后检查；复杂几何仍可能先花费较多分片构造时间，不能将该参数称为严格运行时间上限。

算例口径注意：通用 `erode_obstacles=False` 不腐蚀全部障碍；TIA 算例若同时含内块和 `FIXED_BODY`，必须另按身份处理“仅固定边界不腐蚀”，不得把“不腐蚀全部障碍”误称为该策略。
