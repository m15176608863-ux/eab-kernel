# WO-G6F：G6 第六轮独立正确性重审

审查方报告（不修代码） · 2026-10-12 · 被审新鲜 detached 工作树 `D:\eab-wt\g6f`

## 1. 结论

**confirmed critical=1 / major=7 / minor=4。M0 不可以退出。** 已去重、已运行；未确认问题不入计数。全套全绿不是退出门的替代品。

核心反例是可变 canonical convex view 泄漏缓存别名：源顶点/面未变，仅编辑返回视图，就让同一源的精确成员与相交从 1 变成 −1。其他 major 包括显式凸模型受面提示绕向影响、旧 G0 跳样无牙/错误 oracle，以及局部出口、导数和凸距离辅助 API 的尺度错误。

严重度口径：普通合法源几何被缓存污染、静默错误为 critical；窄输入范围的错误谓词/数值输出或门无牙为 major；响亮拒答、字段缺口及过时弱文档陈述为 minor。特别说明：反绕面发现只针对 `conv(vertices)` 的显式凸契约，不把它当合法一般闭表面；极端数值输出发现不等同于所有默认状态判定都错误。

机读结果：[G6F_findings.json](file:///D:/eab-wt/g6f/review/G6F_findings.json)；全部成果：[证据与脚本清单](file:///D:/eab-wt/g6f/review/INDEX.md)。

## 2. 续做、范围与基线

- HEAD：`2f6c51811edba364e846923da04c45c901a9af8c`。开始/收尾 Git 均仅显示 `?? review/`；**1482 份基线文件 SHA-256 零变化**，没有 commit/checkout/reset/stash/worktree/branch 等 Git 写操作。[收尾完整性证据](file:///D:/eab-wt/g6f/review/notes/final_integrity.json)。
- 所有新/改文件仅在 `review/`。缺陷注入要么为进程内 monkeypatch 并 finally 恢复，要么在 `review/copies/gates_docs_mutations/` 副本改一处；副本变异后原字节 SHA-256 恢复。未修任何被审源码；未运行姊妹仓库 exe、未改姊妹仓库或实现方工作树。
- 上次全套日志停在约 20%，**是中断日志，不算完成**。保留 [旧全套日志](file:///D:/eab-wt/g6f/review/logs/full_suite.log)。上次完成的 13 条 gates 重放和 12 条 solid 重放直接沿用，去重为 20 条，不为数量重复跑；报告第 7 节逐条标注来源。
- 已有二维 20,000 谓词、144 凸包、1,440 成员、144 射线独立 Fraction 扫描沿用旧证据；已有疑点脚本本次加强并亲跑确认。主审查者又对新确认发现复跑：[主审重复确认输出](file:///D:/eab-wt/g6f/review/notes/root_confirmations.json)。
- 范围目标是审查，不是数学修复、性能调优或工程认证。回滚锚为原字节 [baseline_hashes.json](file:///D:/eab-wt/g6f/review/baseline_hashes.json)；本树本来就是用户给定的新鲜工作树，审查未新建另一 worktree。

## 3. 自跑全套

环境：`PYTHONDONTWRITEBYTECODE=1`、`PYTHONIOENCODING=utf-8`，Python 3.12。

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -X utf8 -m pytest -q -p no:cacheprovider tests --basetemp=D:\eab-wt\g6f\review\tmp_full_suite_resume
```

**实际末行：`8582 passed in 876.70s (0:14:36)`**；退出码 `0`；进程墙钟 `883.742 s`。这是本次审查自己跑出的结果，不引用实现方 870 s 当实测。

[完整日志](file:///D:/eab-wt/g6f/review/logs/full_suite_resume.log) · [命令/退出码/耗时](file:///D:/eab-wt/g6f/review/notes/full_suite_resume.json) · [可重跑 runner](file:///D:/eab-wt/g6f/review/repro/run_full_suite.py)。

另亲跑 LP 证书、E4 自校验和 PERF 接触窗三个文件：**274 passed in 12.29s**；文档镜头独立性/指针/窗口定向门 **30 passed in 0.80s**。这两组是定向补验，不加进 8582。

## 4. 已确认发现表

| ID | 级别 | 位置 | 一句话结论 | 可运行证明 |
|---|---|---|---|---|
| G6F-01 | critical | `src/eab/kernel3d/geom3.py:1118-1120` | 可变 canonical convex view 以别名泄漏缓存；只改返回视图，未改变源数据却使源的精确成员与相交静默答错。 | [solid_convex_cache_alias.py](file:///D:/eab-wt/g6f/review/repro/solid_convex_cache_alias.py) |
| G6F-02 | major | `src/eab/kernel3d/geom3.py:1125-1129` | 凸视图保号捷径只比面顶点集合，不校验面绕向，违背显式凸 API 与面提示无关的 conv(vertices) 契约。 | [solid_convex_face_hint.py](file:///D:/eab-wt/g6f/review/repro/solid_convex_face_hint.py) |
| G6F-03 | major | `src/eab/kernel3d/geom3.py:430-443` | is_convex/reflex_edges 即使调用方 tol=0 仍以隐式二面角噪声带吞掉真实凹棱，返回错误的几何谓词结果。 | [solid_hidden_convexity.py](file:///D:/eab-wt/g6f/review/repro/solid_hidden_convexity.py) |
| G6F-04 | major | `src/eab/kernel2d/g0.py:239-245; src/eab/kernel2d/g0.py:359-365; src/eab/kernel3d/g03.py:203-205` | 二维与三维非凸完备性 G0 仍以隐式噪声预筛跳过严格样本，真实枚举路径全毁仍可报通过。 | [geom2_confirmed.py](file:///D:/eab-wt/g6f/review/repro/geom2_confirmed.py) / [geom3_g0_skip.py](file:///D:/eab-wt/g6f/review/repro/geom3_g0_skip.py) |
| G6F-05 | major | `src/eab/kernel2d/g0.py:310-311; src/eab/kernel2d/g0.py:163-166` | 非凸 G0 的浮点出口与距离 oracle 会给错误真值：微贯入报零出口，极小可表达线段距离因平方下溢高估，并令正确内核假红。 | [geom2_confirmed.py](file:///D:/eab-wt/g6f/review/repro/geom2_confirmed.py) |
| G6F-06 | major | `src/eab/kernel2d/entrance.py:226` | 二维精确最短出口的 gap 构造先把有理平方转为 float，微尺寸下把可表达的非零侵入间隙静默变成 -0.0。 | [geom2_confirmed.py](file:///D:/eab-wt/g6f/review/repro/geom2_confirmed.py) |
| G6F-07 | major | `src/eab/dual.py:85` | Dual 除法和 atan2 在中间平方/乘积溢出或下溢时给出错误导数，即使输入与正确答案全部有限。 | [root_dual_scaling.py](file:///D:/eab-wt/g6f/review/repro/root_dual_scaling.py) |
| G6F-08 | major | `src/eab/margin.py:491` | 凸入口块距离与法向辅助 API 先舍入全局投影再相减，工程坐标下将可表达真实正距离答成 0、外法向答成 None。 | [root_margin_projection.py](file:///D:/eab-wt/g6f/review/repro/root_margin_projection.py) |
| G6F-09 | minor | `src/eab/kernel3d/interlock.py:175-181; src/eab/kernel3d/geom3.py:380-381` | 精确逃逸前置 nominal 浮点平移拒绝合法 Fraction 微尺度输入；等值零偏移仅 int→float 就造成零长棱错误。 | [geom3_nominal_translation_loss.py](file:///D:/eab-wt/g6f/review/repro/geom3_nominal_translation_loss.py) |
| G6F-10 | minor | `docs/canon_map.md:55` | canon_map仍称入口块先浮点差点，实际E5b已先有理化再相减，代码描述过时。 | [gates_docs_stale_margin_claim.py](file:///D:/eab-wt/g6f/review/repro/gates_docs_stale_margin_claim.py) |
| G6F-11 | minor | `src/eab/dual.py:107` | Dual ** 0 在零底数上错误抛出 ZeroDivisionError，而该运算是常数1、导数0。 | [root_boundary_contracts.py](file:///D:/eab-wt/g6f/review/repro/root_boundary_contracts.py) |
| G6F-12 | minor | `src/eab/lp.py:412` | 零约束 OPTIMAL LP 快路遗漏 exact_x/exact_y，与一般最优结果精确见证接口不一致。 | [root_boundary_contracts.py](file:///D:/eab-wt/g6f/review/repro/root_boundary_contracts.py) |

## 5. 每条复现输入、输出与建议

以下均为确认故障的实跑，不是修复方案已实施。脚本在同一 HEAD 上运行；具体反例中有理数 oracle 不调用被测几何 helper。

### G6F-01 · critical · 可变 canonical convex view 以别名泄漏缓存；只改返回视图，未改变源数据却使源的精确成员与相交静默答错。

位置：`src/eab/kernel3d/geom3.py:1118-1120`；分审原编号 `G6F-3D-01`。

**输入 → 错误输出：** P 为 [-1,1]^3 的合法朝外三角表面，H=exact_convex_view(P)，H is not P。将 H.verts 原地平移 +100，P 的 verts/faces 原字节内容不变。精确源成员由 1 变 -1，P 与内含半边长0.5盒的 exact_convex_overlap 报 -1；独立区间积真值均为1，新建等效源对象也仍答1。两表面在编辑前后均合法；不是修改源模型后的预期变化。

**重现：** cd D:/eab-wt/g6f; $env:PYTHONDONTWRITEBYTECODE="1"; python -X utf8 review/repro/solid_convex_cache_alias.py

[solid_convex_cache_alias.py](file:///D:/eab-wt/g6f/review/repro/solid_convex_cache_alias.py)

```text
view is source False

before point state 1

source still origin-centred -1.0 1.0

after returned-view mutation state -1

fresh equivalent source state 1

source exact general surface state 1

cached source exact convex overlap with contained small box -1

CONFIRMED valid-source unchanged; independent box oracle inside=1 overlap=1; cached results=-1/-1
```

**建议（未修改）：** 将缓存 canonical payload 设为不可变、返回隔离副本，或在源取回缓存时同时核验缓存产物内容签名；增加改返回视图但源不变的成员与相交回归及牙。

### G6F-02 · major · 凸视图保号捷径只比面顶点集合，不校验面绕向，违背显式凸 API 与面提示无关的 conv(vertices) 契约。

位置：`src/eab/kernel3d/geom3.py:1125-1129`；分审原编号 `G6F-3D-02`。

**输入 → 错误输出：** P 顶点恰为 [-1,1]^3 八角点，仅将 top 面提示反绕；Q 为原点半边长1/2盒。explicit-convex API 保留 P is exact_convex_view(P)，exact_point_in_convex_polyhedron(0,P)=-1，membership_convex3(Q,P,0)=-1；独立顶点凸包真值均1；同一八顶点用空 faces 提示时两者都答1。一般 surface API 不在复现中调用，反绕面提示不满足一般 surface 朝外前提，但本发现针对明确只按顶点凸包、面为提示的显式凸契约（geom3.py:1155、1170，exact_3d_design §1）。

**重现：** cd D:/eab-wt/g6f; $env:PYTHONDONTWRITEBYTECODE="1"; python -X utf8 review/repro/solid_convex_face_hint.py

[solid_convex_face_hint.py](file:///D:/eab-wt/g6f/review/repro/solid_convex_face_hint.py)

```text
vertex-set oracle: origin inside hull = True

canonical view retained malformed source hint = True

exact_point_in_convex_polyhedron(origin) = -1

exact_convex_overlap(contained Q,P) = 1

membership_convex3(Q,P,0) = -1

same vertices, empty source hints: convex point = 1 E member = 1

CONFIRMED explicit conv(vertices) contract violated by face-hint-only change; no general surface API called
```

**建议（未修改）：** 保号捷径仍应使用已生成 canonical outward supporting ring，或精确核验源面平面、简单环、支撑面及朝外绕向后才能复用；面提示不得改变顶点集凸模型的答案。

### G6F-03 · major · is_convex/reflex_edges 即使调用方 tol=0 仍以隐式二面角噪声带吞掉真实凹棱，返回错误的几何谓词结果。

位置：`src/eab/kernel3d/geom3.py:430-443`；分审原编号 `G6F-3D-03`。

**输入 → 错误输出：** 朝外闭合嵌入棱柱的 x-z 截面为 (0,0),(2,0),(2,1),(1,1-eps),(0,1)，y∈[-1,1]。取 eps=2^-50（原点，所有坐标为可精确表达binary64），或 eps=2^-24 且 x 平移1e8（Fraction保持原数）。两 roof 峰中点高1，而精确屋顶中点高1-eps，严格在实体外，故实体非凸且有凹棱。当前 is_convex(tol=0)=True、reflex_edges(tol=0)=[]；manifold_issues=[]。docstring 已说明内部加noise，但它不是调用方显式窗，也没有精确分类兜底。本发现不声称默认 surface_overlap 或 E5b 精确求解走该路径，检索 src 中无生产调用。

**重现：** cd D:/eab-wt/g6f; $env:PYTHONDONTWRITEBYTECODE="1"; python -X utf8 review/repro/solid_hidden_convexity.py

[solid_hidden_convexity.py](file:///D:/eab-wt/g6f/review/repro/solid_hidden_convexity.py)

```text
epsilon 1/1125899906842624 translation 0

independent concavity determinant -1/562949953421312

roof at peak midpoint 1125899906842623/1125899906842624 midpoint height 1

is_convex(tol=0) True

reflex_edges(tol=0) []

min_dihedral_turn -1.7763568394002505e-15

manifold_issues []

CONFIRMED exact midpoint concavity witness; API returned convex/no reflex

epsilon 1/16777216 translation 100000000

independent concavity determinant -1/8388608

roof at peak midpoint 16777215/16777216 midpoint height 1

is_convex(tol=0) True

reflex_edges(tol=0) []

min_dihedral_turn -1.192092895507811e-07

manifold_issues []

CONFIRMED exact midpoint concavity witness; API returned convex/no reflex

binary64-only valid input: True is_convex(tol=0) True reflex_edges(tol=0) []
```

**建议（未修改）：** 按未归一化原数据有理二面角符号/全支撑平面分类；显式 tol 正窗若保留应另报近边界，而不能在 tol=0 把真实凹答为凸；加入binary64微凹及工程坐标元门。

### G6F-04 · major · 二维与三维非凸完备性 G0 仍以隐式噪声预筛跳过严格样本，真实枚举路径全毁仍可报通过。

位置：`src/eab/kernel2d/g0.py:239-245; src/eab/kernel2d/g0.py:359-365; src/eab/kernel3d/g03.py:203-205`；分审原编号 `G6F-G2D-01`。

**输入 → 错误输出：** 单位方块或方盒间严格正间隙为 2^-44；二维另用严格微贯入 2^-44。独立 Fraction 区间 oracle 给出 -1 或 1，但 G0 的 1e-12*L 带将样本判成 0 并跳过。内核法锥判据置为 -1 使完整盖集为空，报告仍 passed=true、samples=0。

**重现：** 在 D:/eab-wt/g6f 运行 python -X utf8 review/repro/geom2_confirmed.py，查看 G2D-01；再运行 python -X utf8 review/repro/geom3_g0_skip.py。

[geom2_confirmed.py](file:///D:/eab-wt/g6f/review/repro/geom2_confirmed.py) · [geom3_g0_skip.py](file:///D:/eab-wt/g6f/review/repro/geom3_g0_skip.py)

```text
{
  "2d": {
    "gap": 5.684341886080802e-14,
    "exact_states": [
      -1,
      1
    ],
    "distance": {
      "passed": true,
      "samples": 0,
      "touching": 1
    },
    "exit": {
      "passed": true,
      "samples": 0,
      "touching": 1
    }
  },
  "3d": {
    "true_gap": "1/17592186044416",
    "exact_state": -1,
    "baseline": {
      "passed": true,
      "samples": 0,
      "skipped_intersecting": 1
    },
    "internal_mutant": {
      "covers": 0,
      "passed": true,
      "samples": 0,
      "skipped_intersecting": 1
    }
  }
}
```

**建议（未修改）：** 完备性门先以独立精确成员 oracle 分配严格分离、内部和边界样本，不以隐式带宽跳过严格样本；每个看护格明确检查实际样本数量，并加入二维与三维微间隙、微贯入的真实内部缺陷注入门。浮点见证误差只用于构造审核。

### G6F-05 · major · 非凸 G0 的浮点出口与距离 oracle 会给错误真值：微贯入报零出口，极小可表达线段距离因平方下溢高估，并令正确内核假红。

位置：`src/eab/kernel2d/g0.py:310-311; src/eab/kernel2d/g0.py:163-166`；分审原编号 `G6F-G2D-02`。

**输入 → 错误输出：** 单位方块 A 沿 x 移动 1-2^-39，B 为单位方块，u=(1,0)：初态满足 polygons_overlap==1，真首次出口为 2^-39=1/549755813888，brute_ray_exit 返回 0，且返回位形仍严格内部相交。另取边长 s=2^-600 的方块，A 相对 B 错位 (1.5*s,.5*s)，真距离为 s/2=1.204959932551442e-181，brute_polygon_distance 返回 1.7040706787304193e-181，正确盖距离被 G0 判失败。

**重现：** 在 D:/eab-wt/g6f 运行 python -X utf8 review/repro/geom2_confirmed.py，查看 G2D-02 与 G2D-03。

[geom2_confirmed.py](file:///D:/eab-wt/g6f/review/repro/geom2_confirmed.py)

```text
{
  "first_exit": {
    "true": "1/549755813888",
    "true_float": 1.8189894035458565e-12,
    "got": 0.0,
    "initial_state": 1,
    "state_at_got": 1
  },
  "distance_underflow": {
    "scale": 2.409919865102884e-181,
    "true": 1.204959932551442e-181,
    "got": 1.7040706787304193e-181,
    "gate_false_red": true,
    "correct_cover": 1.204959932551442e-181
  }
}
```

**建议（未修改）：** 出口 oracle 按独立 Fraction 事件和精确状态求首边界，不在区间中点加噪声带。距离 oracle 采用独立精确点到闭线段平方距，再作稳健开方，或者先缩放避免平方下溢；加入极端单位尺度和微贯入自校验。不能把正确内核假红当作抓住生产缺陷。

### G6F-06 · major · 二维精确最短出口的 gap 构造先把有理平方转为 float，微尺寸下把可表达的非零侵入间隙静默变成 -0.0。

位置：`src/eab/kernel2d/entrance.py:226`；分审原编号 `G6F-G2D-03`。

**输入 → 错误输出：** A=B 为边长 s=2^-600 的方块，x0=(s/2,0)。shortest_exit 正确选择 exit 与右边标签，却报告 gap=-0.0；精确几何 gap=-s/2=-1.204959932551442e-181，可以作为 binary64 非零数表示。错误源于中间平方转 float 下溢，而非输出本身不可表达。

**重现：** 在 D:/eab-wt/g6f 运行 python -X utf8 review/repro/geom2_confirmed.py，查看 G2D-04。

[geom2_confirmed.py](file:///D:/eab-wt/g6f/review/repro/geom2_confirmed.py)

```text
{
  "scale": 2.409919865102884e-181,
  "true_gap": -1.204959932551442e-181,
  "got_gap": -0.0,
  "kind": "exit",
  "label": [
    "VE",
    0,
    1
  ]
}
```

**建议（未修改）：** 采用指数拆分或缩放后开方的稳健有理量构造，不要先将微小平方直接转成 float；加入 tiny scale 下真 gap 与浮点输出的非零、相对误差门，同时保留 kind 与 label 的精确门。

### G6F-07 · major · Dual 除法和 atan2 在中间平方/乘积溢出或下溢时给出错误导数，即使输入与正确答案全部有限。

位置：`src/eab/dual.py:85`；分审原编号 `root_dual_extreme`。

**输入 → 错误输出：** Dual(1e200,(1e200,))/1e200 应为值1、导数1，实得导数inf；尺度1e-200实得0而非1。atan2(Dual(1e200,(0,)),Dual(1e200,(1,))) 导数应为-5e-201，实得-0.0；1e-200版反而ZeroDivisionError。窄极端尺度范围，故major，不将普通算术误差冒充核心精确谓词错。

**重现：** 在 D:/eab-wt/g6f 运行：$env:PYTHONDONTWRITEBYTECODE="1"; python -X utf8 review/repro/root_dual_scaling.py

[root_dual_scaling.py](file:///D:/eab-wt/g6f/review/repro/root_dual_scaling.py)

```text
atan2 scale=1.0 primal=0.7853981633974483 derivative=-0.5 expected=-0.5 equal=True

atan2 scale=1e+200 primal=0.7853981633974483 derivative=-0.0 expected=-5e-201 equal=False

atan2 scale=1e-200 exception=ZeroDivisionError: float division by zero expected=-5e+199

division=Dual(1.0, (inf,)) expected=Dual(1.0,(1.0,))

division_small=Dual(1.0, (0.0,)) expected=Dual(1.0,(1.0,))

zero_power_0.0=ZeroDivisionError: 0.0 cannot be raised to a negative power

zero_power_1.0=Dual(0.0, (1.0,))

zero_power_2.0=Dual(0.0, (0.0,))
```

**建议（未修改）：** 采用尺度规整的商/atan2导数表达式，避免先形成a*ov、x²+y²；若无法得到可信有限输出则响亮失败；补单位缩放与指数跨度门。

### G6F-08 · major · 凸入口块距离与法向辅助 API 先舍入全局投影再相减，工程坐标下将可表达真实正距离答成 0、外法向答成 None。

位置：`src/eab/margin.py:491`；分审原编号 `root_margin_projection`。

**输入 → 错误输出：** 精确盒 E=[T+s,T+3s]×[-s,s]^2，s=1e-9、T=1e8，点 x=(T,0,0)。独立区间积距离 s、投影 (T+s,0,0)、法向 (-1,0,0)；实际 distance=0、normal=None。相同模型移回原点时全部正确；这里 Fraction 保存合法微尺寸，并非 float 输入已塌缩。默认 body_distance 状态不受本脚本直接影响，缺陷在公开辅助 API 和所谓凸距离独立 oracle。

**重现：** 在 D:/eab-wt/g6f 运行：$env:PYTHONDONTWRITEBYTECODE="1"; python -X utf8 review/repro/root_margin_projection.py

[root_margin_projection.py](file:///D:/eab-wt/g6f/review/repro/root_margin_projection.py)

```text
[

  {

    "translation": "0",

    "expected_distance": 1e-09,

    "reported_distance": 1e-09,

    "expected_projection": [

      "1/1000000000",

      "0",

      "0"

    ],

    "reported_projection": [

      1e-09,

      0.0,

      0.0

    ],

    "expected_normal": [

      -1,

      0,

      0

    ],

    "reported_normal": [

      -1.0,

      0.0,

      0.0

    ],

    "exact_state": -1

  },

  {

    "translation": "1000",

    "expected_distance": 1e-09,

    "reported_distance": 9.999894245993346e-10,

    "expected_projection": [

      "1000000000001/1000000000",

      "0",

      "0"

    ],

    "reported_projection": [

      1000.000000001,

      0.0,

      0.0

    ],

    "expected_normal": [

      -1,

      0,

      0

    ],

    "reported_normal": [

      -1.0,

      0.0,

      0.0

    ],

    "exact_state": -1

  },

  {

    "translation": "100000000",

    "expected_distance": 1e-09,

    "reported_distance": 0.0,

    "expected_projection": [

      "100000000000000001/1000000000",

      "0",

      "0"

    ],

    "reported_projection": [

      100000000.0,

      0.0,

      0.0

    ],

    "expected_normal": [

      -1,

      0,

      0

    ],

    "reported_normal": null,

    "exact_state": -1

  }

]
```

**建议（未修改）：** 保留相对投影向量的精确数据，直接由其平方范数计算距离/法向，不从舍入的全局投影坐标反减；公开点输出若是 float 视图，需另给精确点见证或声明表示界限；补单位和大平移门。

### G6F-09 · minor · 精确逃逸前置 nominal 浮点平移拒绝合法 Fraction 微尺度输入；等值零偏移仅 int→float 就造成零长棱错误。

位置：`src/eab/kernel3d/interlock.py:175-181; src/eab/kernel3d/geom3.py:380-381`；分审原编号 `G6F-3D-04`。

**输入 → 错误输出：** 两个合法精确盒为原点盒 A 与 z=3/4 盒 B，半边长各1/2；统一scale=1e-9、坐标origin=1e8，以Fraction保存。独立区间积最早竖向脱离根为7/4000000000。offset=(0,0,0)返回该精确根；完全等值的offset=(0.,0.,0.)使 nominal At=A.translated(offset) 将微特征舍成相同float，抛ValueError zero-length edge，精确求解器未运行。没有静默返回错误根，因此按minor计。

**重现：** cd D:/eab-wt/g6f; $env:PYTHONDONTWRITEBYTECODE="1"; python -X utf8 review/repro/geom3_nominal_translation_loss.py

[geom3_nominal_translation_loss.py](file:///D:/eab-wt/g6f/review/repro/geom3_nominal_translation_loss.py)

```text
independent exact product-interval earliest root 7/4000000000
offset integer zero exact_height 7/4000000000
equivalent offset float zero rejected: ValueError zero-length edge (0, 1) (consecutive duplicate vertex)
CONFIRMED nominal-report float translation fails before exact authoritative solver
```

**建议（未修改）：** nominal 报告构造须保留非Dual原坐标精确仿射值，或让显示候选构造失败不会阻断权威精确求解；增加等值标量类型与混合尺度门。

### G6F-10 · minor · canon_map仍称入口块先浮点差点，实际E5b已先有理化再相减，代码描述过时。

位置：`docs/canon_map.md:55`；分审原编号 `GD-01`。

**输入 → 错误输出：** A=box(center=(1,0,0),half=(.5,.5,.5)), B=box(center=(1e16,0,0),half=(4,.5,.5)); 文档称差点先舍入，实际最小x为正确Fraction(19999999999999989,2)，而float差点是9999999999999994。

**重现：** python -X utf8 review/repro/gates_docs_stale_margin_claim.py

[gates_docs_stale_margin_claim.py](file:///D:/eab-wt/g6f/review/repro/gates_docs_stale_margin_claim.py)

```text
{
  "doc_line": 55,
  "doc_claim": "margin.entrance_block_convex 仍先浮点构造 b−a",
  "exact_min_x": "19999999999999989/2",
  "rounded_difference_min_x": "9999999999999994",
  "actual_min_x": "19999999999999989/2",
  "code_actually_preserves_exact_input_difference": true
}
```

**建议（未修改）：** 更新canon_map命题1当前代码列为先有理化后作差，指向test_entrance_block_forms_differences_before_any_float_rounding；不修实现。

### G6F-11 · minor · Dual ** 0 在零底数上错误抛出 ZeroDivisionError，而该运算是常数1、导数0。

位置：`src/eab/dual.py:107`；分审原编号 `root_dual_power_zero`。

**输入 → 错误输出：** Dual(0.,(1.,)) ** 0. 求 c=p*v**(p-1) 时先计算0**-1抛错；同API对非零底数正确返回Dual(1,(0,))。

**重现：** 在 D:/eab-wt/g6f 运行：$env:PYTHONDONTWRITEBYTECODE="1"; python -X utf8 review/repro/root_boundary_contracts.py

[root_boundary_contracts.py](file:///D:/eab-wt/g6f/review/repro/root_boundary_contracts.py)

```text
min status= optimal x= [0.0, 0.0] y= [] exact_x= None exact_y= None

max status= optimal x= [0.0, 0.0] y= [] exact_x= None exact_y= None

one-row reference exact_x= (Fraction(0, 1),) exact_y= (Fraction(1, 1),)

pow0 0.0 ZeroDivisionError 0.0 cannot be raised to a negative power

pow0 2.0 Dual(1.0, (0.0,))

python_float_zero_power= 1.0
```

**建议（未修改）：** p==0作为恒等常数幂处理，返回同宽全零导数；增加零底数/零指数闭式边界门。

### G6F-12 · minor · 零约束 OPTIMAL LP 快路遗漏 exact_x/exact_y，与一般最优结果精确见证接口不一致。

位置：`src/eab/lp.py:412`；分审原编号 `root_lp_zero_witness`。

**输入 → 错误输出：** solve([],[],[0.,1.])及maximize([],[],[0.,-1.])状态/浮点答案正确，但exact_x=None、exact_y=None；应至少输出(Fraction(0),Fraction(0))与空tuple。一行参考LP正常携带见证。该项不是错误最优值。

**重现：** 在 D:/eab-wt/g6f 运行：$env:PYTHONDONTWRITEBYTECODE="1"; python -X utf8 review/repro/root_boundary_contracts.py

[root_boundary_contracts.py](file:///D:/eab-wt/g6f/review/repro/root_boundary_contracts.py)

```text
min status= optimal x= [0.0, 0.0] y= [] exact_x= None exact_y= None

max status= optimal x= [0.0, 0.0] y= [] exact_x= None exact_y= None

one-row reference exact_x= (Fraction(0, 1),) exact_y= (Fraction(1, 1),)

pow0 0.0 ZeroDivisionError 0.0 cannot be raised to a negative power

pow0 2.0 Dual(1.0, (0.0,))

python_float_zero_power= 1.0
```

**建议（未修改）：** 在m==0的optimal分支填零原始有理向量和空对偶向量，补所有optimal分支字段契约门。

## 6. 九个镜头的覆盖与结果

### 镜头 1：精确声称与浮点分支

全 `src/eab/` 的 **30 个模块、1399 个 Compare 节点、161 个容差语法候选**已作 AST 库存并按函数/调用角色分类，见 [分支库存](file:///D:/eab-wt/g6f/review/notes/tolerance_inventory.json)。它包括比较符零/非零、名称含 tol/noise/eps/band 等的候选，**不是“1399 个都是浮点容差裁决”**，也不是每点都动态证正确。

- 允许域窗口/报告：covers 的显式长度/角度/枚举窗；`near_labels`、nominal tie 标签；margin 的显式 `contact_window/atol`；limit 的 `uncertainty/resolvability` 和 `tol*fmax` 截断展示 force/active。展示字段不是静力证书，后者从 lambdas 精确核。
- 允许启发式且兜底：LP 浮点选基/缩放/松弛后必须 `_Exact.certify` 或有理 simplex；predicates 的符号过滤与 exact_geom 区间排除不确定时回 Fraction；纯整数代数优化不是浮点过滤。
- 确认有答案影响：`is_convex/reflex_edges` 隐式 noise 分类、旧距离/出口 G0 的 band 跳样及其 oracle。见对应已确认项。
- 活代码与历史代码区分：geom3 的旧 `_contact_cone_witness/_gordan_direction/_active_normals` 不在当前 `polyhedra_overlap → exact_geom.surface_overlap` 决策链，未因 grep 容差而虚报默认贯入错误。读入器 `strip_duplicate_vertices` 的噪声剥点是仍存的 legacy 几何简化口径，不算默认数学内核 exact 已证明。

### 镜头 2：浮点过滤与缓存

上次 20,000 二维谓词极端指数扫描沿用；本次三维 orient/cross/dot 极端过滤 12,000 格、polygon locate 区间快路 900 格、LP reduced-sign 8,000 格独立 Fraction 比较均零错。含次正规、下溢/上溢中间量、巨大坐标、混合指数及 Fraction 转 float 不可表示格。读过过滤误差界与 fallback 链；**没有穷举或完成普适误差界的形式证明**。

缓存检验包含内容替换 warm-vs-clear、Dual 拒收而非静默 primal 命中，找到返回可变 convex view 的别名污染。其他事件/三角化/距离缓存按完整内容与必要实现指针读了键；未穷举任意自定义可变 numeric。[LP 独立过滤/顶点 oracle](file:///D:/eab-wt/g6f/review/repro/root_lp_audit.py)。

### 镜头 3：Oracle 独立性

重点核 E2–PERF 的主 oracle：2D 内联 SAT/gift-wrap/support；3D g03_exact 全点整数/有理凸包及 SAT；一般表面、margin/frozen、最早互锁和 PERF 窗口的自有耳切/扫掠/Gram/Gordan/区间积。未发现新主 oracle 直接复用生产几何原语的已确认实例。

不夸大独立性：`test_lp_certificates._exact_limit_lp` 仍共享 `_build_columns` 锥方向/owner 的模型定义，独立重建的是力矩、平移、容量与 simplex；它不能单独证明该共享模型。2D/3D brute、旧凹 G0 等共用几何或事件者仅是佐证。实际错误 oracle 已入发现，不把“函数叫 brute”当独立证明。

### 镜头 4：旧门迁移是否变弱

对 `git diff b6126cf..HEAD -- tests/` 的 **89 个改动测试/辅助文件、107 个改动既有函数**保存旧/新源码和 assert AST；台账核 E2 的35格、E5a41项、E5a2 18项、E5b21项及 E3E4/PERF。[完整库存](file:///D:/eab-wt/g6f/review/notes/gates_docs_inventory.json)。

本次额外 **4 种**隔离源码变异，baseline 全绿而 mutant 语义断言红，恢复 SHA：2D 边界错票、3D 保留非极点、棱弧端点标 strict、微台阶误合并。微台阶变异中旧0.5格仍绿，新2^-80/1e-12门红，如实记录。[红断言及恢复字节](file:///D:/eab-wt/g6f/review/notes/gates_docs_mutations.json)。

未找到“旧能抓而当前完整新体系漏抓”的另一已确认迁移逃逸；但旧凹 G0 噪声跳过能让真实内核枚举删除仍 pass，已单列 major。**107 个函数没有各自全做人工可达链/变异**，不会把节点数不降当“不弱化”证明。

### 镜头 5：独立几何压力

- 沿用二维 144 hull / 1440 member / 144 ray；新增 **175 凸局部出口 + 150 凹 L 射线首入**，自写 Fraction oracle 均零错。
- 三维一般 L 凹柱/含 cavity 中空盒：**132 格**独立区间积并模型，含尺度1e-9、平移1e8与精确轴循环，成员/相交零错；非单调 cavity 最早抬升 **24 格中20正确，4格响亮拒答**归入同一 minor。
- 相同几何平移/缩放中的反例包括二面角噪声、辅助投影的工程坐标消去、极小尺寸局部出口 gap/距离下溢、Dual 单位缩放。覆盖共线/共面/平直、微尺寸、混合和退化数据；非法自交/非流形/零体积不在一般表面结果保证范围。
- 任意凹对全局最短分离不是已交付 API 契约；局部 shortest_exit/shortest_exit3 不外推为全局问题，未将明确限制重新算缺陷。

### 镜头 6：局部贯入厚度窗口

读 `star_core/contact_models → exact overlap → margin/interlock OR` 证书链，自己另写 **75 盒对、12 个被接受模型**：区间积核六轴非贯入与位移平方=w²；homothety 比例和全顶点最大径向段平方≤w²，加凸范数论证给连续壳上界，不只是抽查碰撞点。未找到可靠性命题反例。

六轴成功推出 PD≤w；星核薄壳仅推出每处严格重叠在径向厚度≤w壳内，**不**推出短刚体脱离。坐标轴/L1 旋转依赖、斜向短脱离漏检、报贯入不推出 PD>w 都已明示。[独立表面/窗口压力脚本](file:///D:/eab-wt/g6f/review/repro/geom3_independent_stress.py)。对任意非星形凹表面不是完备 PD 或全壳算法认证。

### 镜头 7：极限分析

本审查自己写 Fraction 高斯消元与有界小 LP 全基顶点枚举：**180 格**目标正确，快过滤与纯有理符号路径答案一致，通常 OPTIMAL `x/y` 与 `exact_x/exact_y` 单次舍入视图一致。仅零约束最优快路漏 exact 见证入 minor，非错误最优值。

单/多体独立闭式滑动/倾覆 **60 对**，荷载2^(-600)..2^600、微尺寸与大平移，精确 alpha 均正确；分别注入 alpha/lambda/机制10^-100误差 **180+180 次全部拒绝**，真实 limit_load 路径4种毒化（float/Fraction alpha、exact_x、exact_y）全抛 self-check。[独立构造错误候选脚本](file:///D:/eab-wt/g6f/review/repro/root_limit_guard.py) · [输出](file:///D:/eab-wt/g6f/review/logs/root_limit_guard.log)。

旧9/11/20/21/22/45原输入重放均不再给原错误。可分辨报告按文档只报告、不改原 status/alpha；承认一阶 U 和 alpha_min=0 刀刃可能漏筛，不称全不确定性稳定证书。没有另找到精确自校验漏掉错误 optimal 候选。

### 镜头 8：文档、代码、正本

README/canon_map/两设计共库存 **69 条**✔/完成/实现/有门声称，具名测试指针能解析，定向指针门通过；不是逐句定理验证。canon 第八节 “07 对代码” 的 ContactRecord 生命周期/溯源缺口、Phase0 3而非6读取器、G2手写清单、G1锁态缺口、G3/G4/G5/M3剩余项与正本07基本如实映射。canon 命题1行仍错误说 margin 先 float 差点，确认 minor。

正本01/03/07全文读取并核关键数学/设计条目；00主要精读§3/§4/§6.2，其余历史/完整文献未逐行审读。没有借正本文献声称做外部学术优先性认证。README 三维“最短出口”标题未同步局部限定列未确认，不追加 major。

### 镜头 9：第五轮回归重放

**26 条去重原发现**已重放原输入或等价输入；上次20条证据直接沿用，本次新增6条。都只说“该原反例不再成立”，不把选取的26条外推为50条关闭。完整输入/输出与出处：[重放索引](file:///D:/eab-wt/g6f/review/notes/g6e_replay_index.json)。

## 7. 原始回归逐条来源

编号为 `g6e_findings_raw.json.findings` 数组 **1 起始**位置，不是过时源码行号。

| 原编号 | 本轮证据来源 | 当前观察与边界 |
|---|---|---|
| 2 | 上次中断前运行，直接沿用；[gates_g6e_replay.json](file:///D:/eab-wt/g6f/review/notes/gates_g6e_replay.json) | 沿用已保存原输入运行输出；旧特定故障不再成立，非该API全域证明。 |
| 3 | 上次中断前运行，直接沿用；[gates_g6e_replay.json](file:///D:/eab-wt/g6f/review/notes/gates_g6e_replay.json) | 沿用已保存原输入运行输出；旧特定故障不再成立，非该API全域证明。 |
| 7 | 上次中断前运行，直接沿用；[solid_replay_results.json](file:///D:/eab-wt/g6f/review/notes/solid_replay_results.json) | 沿用已保存原输入运行输出；旧特定故障不再成立，非该API全域证明。 |
| 9 | 本次当前 HEAD 亲跑原 Python 复现体；[root_g6e_09.log](file:///D:/eab-wt/g6f/review/logs/root_g6e_09.log) | 原切向不安全值改为 ValueError；这是预期入口拒收，不将退出码1当重放失败。 |
| 11 | 本次当前 HEAD 亲跑原 Python 复现体；[root_g6e_11.log](file:///D:/eab-wt/g6f/review/logs/root_g6e_11.log) | 构造的错承载/贯入/次优解全部被拒绝；未再发生旧放行。 |
| 20 | 本次当前 HEAD 亲跑原 Python 复现体；[root_g6e_20.log](file:///D:/eab-wt/g6f/review/logs/root_g6e_20.log) | 构造的错承载/贯入/次优解全部被拒绝；未再发生旧放行。 |
| 21 | 本次当前 HEAD 亲跑原 Python 复现体；[root_g6e_21.log](file:///D:/eab-wt/g6f/review/logs/root_g6e_21.log) | 构造的错承载/贯入/次优解全部被拒绝；未再发生旧放行。 |
| 22 | 本次当前 HEAD 亲跑原 Python 复现体；[root_g6e_22.log](file:///D:/eab-wt/g6f/review/logs/root_g6e_22.log) | 单/多体及无关远体下 alpha、U 一致，不再篡改原状态。 |
| 24 | 上次中断前运行，直接沿用；[solid_replay_results.json](file:///D:/eab-wt/g6f/review/notes/solid_replay_results.json) | 沿用已保存原输入运行输出；旧特定故障不再成立，非该API全域证明。 |
| 25 | 上次中断前运行，直接沿用；[gates_g6e_replay.json](file:///D:/eab-wt/g6f/review/notes/gates_g6e_replay.json) / [solid_replay_results.json](file:///D:/eab-wt/g6f/review/notes/solid_replay_results.json) | 沿用已保存原输入运行输出；旧特定故障不再成立，非该API全域证明。 |
| 26 | 上次中断前运行，直接沿用；[gates_g6e_replay.json](file:///D:/eab-wt/g6f/review/notes/gates_g6e_replay.json) | 沿用已保存原输入运行输出；旧特定故障不再成立，非该API全域证明。 |
| 27 | 上次中断前运行，直接沿用；[gates_g6e_replay.json](file:///D:/eab-wt/g6f/review/notes/gates_g6e_replay.json) | 沿用已保存原输入运行输出；旧特定故障不再成立，非该API全域证明。 |
| 28 | 上次中断前运行，直接沿用；[solid_replay_results.json](file:///D:/eab-wt/g6f/review/notes/solid_replay_results.json) | 沿用已保存原输入运行输出；旧特定故障不再成立，非该API全域证明。 |
| 29 | 上次中断前运行，直接沿用；[gates_g6e_replay.json](file:///D:/eab-wt/g6f/review/notes/gates_g6e_replay.json) / [solid_replay_results.json](file:///D:/eab-wt/g6f/review/notes/solid_replay_results.json) | 沿用已保存原输入运行输出；旧特定故障不再成立，非该API全域证明。 |
| 30 | 上次中断前运行，直接沿用；[gates_g6e_replay.json](file:///D:/eab-wt/g6f/review/notes/gates_g6e_replay.json) | 沿用已保存原输入运行输出；旧特定故障不再成立，非该API全域证明。 |
| 31 | 上次中断前运行，直接沿用；[gates_g6e_replay.json](file:///D:/eab-wt/g6f/review/notes/gates_g6e_replay.json) / [solid_replay_results.json](file:///D:/eab-wt/g6f/review/notes/solid_replay_results.json) | 沿用已保存原输入运行输出；旧特定故障不再成立，非该API全域证明。 |
| 34 | 上次中断前运行，直接沿用；[solid_replay_results.json](file:///D:/eab-wt/g6f/review/notes/solid_replay_results.json) | 沿用已保存原输入运行输出；旧特定故障不再成立，非该API全域证明。 |
| 37 | 上次中断前运行，直接沿用；[solid_replay_results.json](file:///D:/eab-wt/g6f/review/notes/solid_replay_results.json) | 沿用已保存原输入运行输出；旧特定故障不再成立，非该API全域证明。 |
| 38 | 上次中断前运行，直接沿用；[gates_g6e_replay.json](file:///D:/eab-wt/g6f/review/notes/gates_g6e_replay.json) | 沿用已保存原输入运行输出；旧特定故障不再成立，非该API全域证明。 |
| 39 | 上次中断前运行，直接沿用；[gates_g6e_replay.json](file:///D:/eab-wt/g6f/review/notes/gates_g6e_replay.json) | 沿用已保存原输入运行输出；旧特定故障不再成立，非该API全域证明。 |
| 40 | 上次中断前运行，直接沿用；[gates_g6e_replay.json](file:///D:/eab-wt/g6f/review/notes/gates_g6e_replay.json) / [solid_replay_results.json](file:///D:/eab-wt/g6f/review/notes/solid_replay_results.json) | 默认分支不再 NameError；有诊断 hull_anomaly 计数，不据此说所有G0格正确。 |
| 41 | 上次中断前运行，直接沿用；[gates_g6e_replay.json](file:///D:/eab-wt/g6f/review/notes/gates_g6e_replay.json) | 沿用已保存原输入运行输出；旧特定故障不再成立，非该API全域证明。 |
| 42 | 上次中断前运行，直接沿用；[solid_replay_results.json](file:///D:/eab-wt/g6f/review/notes/solid_replay_results.json) | 沿用已保存原输入运行输出；旧特定故障不再成立，非该API全域证明。 |
| 43 | 上次中断前运行，直接沿用；[solid_replay_results.json](file:///D:/eab-wt/g6f/review/notes/solid_replay_results.json) | 沿用已保存原输入运行输出；旧特定故障不再成立，非该API全域证明。 |
| 44 | 上次中断前运行，直接沿用；[gates_g6e_replay.json](file:///D:/eab-wt/g6f/review/notes/gates_g6e_replay.json) / [solid_replay_results.json](file:///D:/eab-wt/g6f/review/notes/solid_replay_results.json) | 沿用已保存原输入运行输出；旧特定故障不再成立，非该API全域证明。 |
| 45 | 本次当前 HEAD 亲跑原 Python 复现体；[root_g6e_45.log](file:///D:/eab-wt/g6f/review/logs/root_g6e_45.log) | 构造的错承载/贯入/次优解全部被拒绝；未再发生旧放行。 |

## 8. 未确认与不计数

1. README 三维已侵入“最短出口”未当场限定局部，设计与 docstring 已限定；没有另写合法一般凹体新反例证明本次新增核心承诺，未入计数。
2. `_exact_limit_lp` 共享锥方向/owner 模型的共同错误风险，没有独立制造出当前解析门也漏掉的错误，因此仅作独立性覆盖不足，不入 confirmed major。
3. 未找到已查过滤、六轴/薄壳可靠性、矩形并类一般表面的静默反例；零错搜索不是正确性证明。
4. 边界由 float 旋转舍入后变了实际数据，逐格 exact oracle 要核新数据，而非强行保理想计数。没有将此原则作为样本跳过许可；实际 G0 跳样仍计 major。

## 9. 完整性批评（明确不能据此推论的内容）

- `src/eab/` 30 个 Python 模块均至少静态扫描；二维6模块、三维10模块逐函数审读，主审读 LP/limit/limit_multi/Dual/contact_record/rational3/predicates 和4读取器。margin 关键原语、窗口、缓存、闭合、凸投影和冻结路径读过；**不声称每个源码 token 都完成人工形式证明**。没有完全未打开的生产 Python 模块；测试和 tools 远未全逐行读。
- **未逐行审读全部 tests 文件**：重点/执行/静态库存与逐函数深审不等价；107个既有改动函数未各自做全调用链检查与变异，69条具名声称未各自单独隔离运行。详细分审说明见 [文档/迁移完整性批评](file:///D:/eab-wt/g6f/review/notes/gates_docs_final.md)。
- 00 正本早期历史、其余应用段、完整参考文献未逐行精读；03需求侧文献及全部外部原论文未核；DDA4.x导出事实沿用既有本地记录，没重新打开导师源码。不能据此提供外部文献、学术优先性或任何法律认证。
- 一般凹表面独立压力主要是矩形并/中空盒及认证星核/测试专用族；未构造覆盖任意非星形凹表面的独立体积 oracle，未穷举任意环耳切退化/随机 SE(3)。非法自交、非流形、零体积和任意自定义可变 numeric 的结果域未认证。
- 浮点过滤采样与手读误差界不是对所有 binary64 输入的穷举证明；缓存源内容/Dual/返回别名已查，任意所有外部别名组合未穷举。几何/力学单位不变性压力不能代替全域证明。
- 根、状态、距离显示与构造/证书的边界分开：未把 float 根显示重新逐顶点平移当同一 exact_motion 证书；没有修姊妹适配器、部署 shadow 开关或进行动力学/岩石标定。
- 本轮已经找到足以阻 M0 的确认缺陷，**完整性边界不会被全套绿补齐**。实现方修复后仍需独立复核，不能由本文 suggested_fix 或本轮重放推断修复已完成。

## 10. 交付与重跑

- [本中文总报告](file:///D:/eab-wt/g6f/review/G6F_report.md)
- [机读发现（含实际输出）](file:///D:/eab-wt/g6f/review/G6F_findings.json)
- [全部证据、复现脚本与目录清单](file:///D:/eab-wt/g6f/review/INDEX.md)
- [被审文件未改证明](file:///D:/eab-wt/g6f/review/notes/final_integrity.json)

复现脚本只写 `review/`，不要在姊妹仓库/实现方树执行。确认反例可运行 [主审确认 runner](file:///D:/eab-wt/g6f/review/repro/root_confirmations.py)，另运行 `root_dual_scaling.py`、`root_boundary_contracts.py`、`root_margin_projection.py`。源码变异只用 [副本 runner](file:///D:/eab-wt/g6f/review/repro/gates_docs_mutations.py)；全套用 `run_full_suite.py`，后者若重跑会更新本次续跑日志/结果。

G6F_DONE critical=1 major=7 minor=4
