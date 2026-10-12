# WO-G6J：G6 第十轮独立正确性复审

## 0. 结论与口径

**confirmed critical = 0 / major = 4 / minor = 1；M0 不可退出。**

第九轮原六项逐条重放、再反向写“修好应成立”的断言，**六项均已修**。本轮新增确认的是三条窄域计算/分类错误、一条新增静态结构门缺口，以及一条可分辨性报告错误。没有把未确认猜测、无效输入、响亮范围异常或共享谓词扫描的结果计成 critical。

- 被审 HEAD：`0e9ef93f67656b0bfeafd487ff12bde44360ab25`，Windows / Python 3.12.10 / pytest 9.0.3，新鲜 detached 工作树。
- 主审与三个独立分路只审查，不修代码；不读取实现方会话上下文。历史报告、代码与只读正本为已知材料，不当作正确性的证据替代品。
- 自跑全套：**10604 passed in 1299.11s (0:21:39)**，exit 0；JUnit 10604、0 failed/error/skipped。子进程总墙钟 1310.06s。
- 全套 pytest 为**单进程串行**，未用 xdist；其他审查脚本同时运行，不能据此做独占机器性能基准。首先启动完整套，随后先重放六项再开展同类搜索；结果在定稿前收齐。
- 用户命令示例中的 g6f 内 tmp 与“其他工作树只读”冲突，故使用本树 `review/tmp_full`。环境设置 `PYTHONDONTWRITEBYTECODE=1`、`PYTHONIOENCODING=utf-8`，不写 cacheprovider。
- tracked 文件运行前后逐个 SHA-256 比较 **0 漂移**；最终还单独复核。没有 commit/checkout/reset/stash/worktree/branch 等 Git 写操作，没有姊妹源码改动。

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONIOENCODING='utf-8'
python -X utf8 -m pytest -q -p no:cacheprovider tests --basetemp=D:\eab-wt\g6j\review\tmp_full --junitxml=D:\eab-wt\g6j\review\logs\full.xml
```

证据：[完整串行输出](file:///D:/eab-wt/g6j/review/logs/full.log) · [命令/退出码/原字节对账](file:///D:/eab-wt/g6j/review/logs/full_result.json) · [JUnit](file:///D:/eab-wt/g6j/review/logs/full.xml) · [审前SHA-256锚点](file:///D:/eab-wt/g6j/review/tracked_before.json)。

## 1. 已确认发现总表

| ID | severity | file:line | 一句话结论 |
|---|---|---|---|
| G6J-J01 | major | `tools/check_exact_construction.py:230-232` | 静态结构门只检查 positional args，忽略 keyword 值，并把 Fraction 当去污器；明令禁止的同函数 premature-rounding 仍可零违例穿过真实构造路径。 |
| G6J-J02 | major | `src/eab/kernel3d/entrance3.py:246-255` | 三维闭集首入漏普通边界初态，切向短视窗静默报 none 而非 t*=0 |
| G6J-J03 | major | `src/eab/kernel2d/covers.py:145-146` | 公共 in_cone 对允许的微反射 normal_cone 输出把反向薄扇区错误标严格内部 |
| G6J-J04 | major | `src/eab/dual.py:225-228` | Dual.sqrt 的解析导数仍先舍入 primal，再乘 seed，次正规可表达导数错一倍，范围失败也静默返回0/inf。 |
| G6J-J05 | minor | `src/eab/limit.py:414-418;519-524` | 有限荷载输入下无限承载答案正确，但uncertainty=NaN仍标resolved，报告没有告警。 |

分级依据：J02/J03/J04 是边界初态、显式微反射 helper、次正规导数的窄域错，按工单“错误答案但范围窄”记 major；J01 是静态门漏牙，非当前 cone 已错；J05 的核心承载正确，仅报告失效，记 minor。发现按根因去重，不把多个姿态、七种语法、单/多体重复计数。

### G6J-J01 · major

- **位置**：`tools/check_exact_construction.py:230-232`
- **结论**：静态结构门只检查 positional args，忽略 keyword 值，并把 Fraction 当去污器；明令禁止的同函数 premature-rounding 仍可零违例穿过真实构造路径。
- **具体输入 → 输出**：真实 cone_intersection_margin 的 exact p=(-u/3,)*3，u=2^-1074。把 final norm 调用仅改为 norm_rational(values=vector_rational(p,allow_underflow=True)) 后，全真实 covers3.py AST scan=[]，结果从正确 u 变 0；Fraction KKT 和平方中点独立证实最终范数 RN 应为 u。普通 sqrt keyword / Fraction barrier 另有一 ULP 错误，a-=b 会把准确 2^-53 变 0。
- **建议（未实施）**：扫描 node.args 加 node.keywords[].value；已知转换的 Fraction/map(Fraction) 不清 taint；覆盖 AugAssign、for 目标和明确本地容器写入，或相应 fail-closed；新增真实路径的 static mutation 牙。
- **计数/影响边界**：新增 AST 结构门缺口，不是当前 pristine cone_margin 数值错，也不是整套动态门失牙；R9 中点动态门能抓该旧缺陷。任意跨过程/反射不在此次论证范围，关键词绕过不依赖这种能力。
- **可直接重跑**：

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -X utf8 review/repro/static_real_cone_mutant.py
python -X utf8 review/repro/static_fraction_barrier.py
```

[复现1](file:///D:/eab-wt/g6j/review/repro/static_real_cone_mutant.py) · [复现2](file:///D:/eab-wt/g6j/review/repro/static_fraction_barrier.py)；[主审输出1](file:///D:/eab-wt/g6j/review/logs/root_confirm_static_real_cone_mutant.log) · [主审输出2](file:///D:/eab-wt/g6j/review/logs/root_confirm_static_fraction_barrier.log)。

**主审在本 HEAD 亲自运行的完整输出**（所有脚本 exit 0，表示反例已被证明）：

```text
full real covers3 source AST violations: []
real cone margin baseline: 0x0.0000000000001p-1022
real cone margin mutant: 0x0.0p+0
independent KKT midpoint expected: 0x0.0000000000001p-1022
STATIC_REAL_CONE_MUTANT CONFIRMED: keyword known component-first defect accepted by AST

sqrt_keyword AST_issues= [] actual= 0x1.0000000000000p+0 expected= 0x1.0000000000001p+0
norm_keyword AST_issues= [] actual= 0x1.0000000000000p+0 expected= 0x1.0000000000001p+0
fraction_barrier AST_issues= [] actual= 0x1.0000000000000p+0 expected= 0x1.0000000000001p+0
map_fraction_barrier AST_issues= [] actual= 0x1.0000000000000p+0 expected= 0x1.0000000000001p+0
local_loop AST_issues= [] actual= 0x1.0000000000000p+0 expected= 0x1.0000000000001p+0
local_append AST_issues= [] actual= 0x1.0000000000000p+0 expected= 0x1.0000000000001p+0
augmented_subtraction AST_issues= [] actual= 0x0.0p+0 expected= 0x1.0000000000000p-53
STATIC_FRACTION_BARRIER CONFIRMED: 7 silent wrong constructions bypass scanner
```

### G6J-J02 · major

- **位置**：`src/eab/kernel3d/entrance3.py:246-255`
- **结论**：三维闭集首入漏普通边界初态，切向短视窗静默报 none 而非 t*=0
- **具体输入 → 输出**：{
  "A": "[-3/4,5/4] x [-7/8,9/8] x [1,3]",
  "B": "[-1,1]^3",
  "x0": [
    0,
    0,
    0
  ],
  "d": [
    1,
    0,
    0
  ],
  "tol": 0,
  "t_max": "1/16",
  "expected": "kind=entrance,exact_t=0",
  "actual": "kind=none,exact_t=None"
}
- **建议（未实施）**：对初态 E 边界独立收集当前精确有限域零间隙盖，方向无关返回 entrance/exact_t=0；补切向/背离/进入和零/正 t_max 门
- **计数/影响边界**：普通凸盒面接触，非紧配内缝；三尺度/姿态共6格静默none、3格背离异常、3格进入控制正确；此旧漏网并非 R9 新引入
- **合同依据**：src/eab/kernel3d/entrance3.py:34 none 被定义为射线在 t_max 内不触及 E；普通闭集相触初态已经触及 E；src/eab/kernel2d/entrance.py:7 统一闭集首入为 min{t>=0 : x(t) in E}；二维同构路径已含切向/背离初接触；src/eab/kernel3d/entrance3.py first_entrance_brute docstring 明示 x0 已相触/相交时返回0。
- **可直接重跑**：

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -X utf8 review/repro/geom2j_initial_boundary3.py
```

[复现1](file:///D:/eab-wt/g6j/review/repro/geom2j_initial_boundary3.py)；[主审输出1](file:///D:/eab-wt/g6j/review/logs/root_confirm_geom2j_initial_boundary3.log)。

**主审在本 HEAD 亲自运行的完整输出**（所有脚本 exit 0，表示反例已被证明）：

```text
{
  "status": "CONFIRMED",
  "oracle_initial_intersection": "[(Fraction(-3, 4), Fraction(1, 1)), (Fraction(-7, 8), Fraction(1, 1)), (Fraction(1, 1), Fraction(1, 1))]",
  "cases": [
    {
      "scale": "1",
      "rotated": false,
      "direction": [
        1,
        0,
        0
      ],
      "cap": "0",
      "want_kind": "entrance",
      "want_exact_t": "0",
      "got_kind": "none",
      "got_exact_t": "None",
      "wrong": true
    },
    {
      "scale": "1",
      "rotated": false,
      "direction": [
        1,
        0,
        0
      ],
      "cap": "1/16",
      "want_kind": "entrance",
      "want_exact_t": "0",
      "got_kind": "none",
      "got_exact_t": "None",
      "wrong": true
    },
    {
      "scale": "1",
      "rotated": false,
      "direction": [
        0,
        0,
        1
      ],
      "cap": "1/16",
      "want_kind": "entrance",
      "want_exact_t": "0",
      "exception": "RuntimeError('first_entrance3: no in-extent facet-cover candidate, yet the bodies touch at t = Fraction(0, 1); the candidate set missed an earlier entrance')",
      "wrong": true
    },
    {
      "scale": "1",
      "rotated": false,
      "direction": [
        0,
        0,
        -1
      ],
      "cap": "1/16",
      "want_kind": "entrance",
      "want_exact_t": "0",
      "got_kind": "entrance",
      "got_exact_t": "0",
      "wrong": false
    },
    {
      "scale": "1/1000000000",
      "rotated": true,
      "direction": [
        1,
        0,
        0
      ],
      "cap": "0",
      "want_kind": "entrance",
      "want_exact_t": "0",
      "got_kind": "none",
      "got_exact_t": "None",
      "wrong": true
    },
    {
      "scale": "1/1000000000",
      "rotated": true,
      "direction": [
        1,
        0,
        0
      ],
      "cap": "1/16",
      "want_kind": "entrance",
      "want_exact_t": "0",
      "got_kind": "none",
      "got_exact_t": "None",
      "wrong": true
    },
    {
      "scale": "1/1000000000",
      "rotated": true,
      "direction": [
        0,
        0,
        1
      ],
      "cap": "1/16",
      "want_kind": "entrance",
      "want_exact_t": "0",
      "exception": "RuntimeError('first_entrance3: no in-extent facet-cover candidate, yet the bodies touch at t = Fraction(0, 1); the candidate set missed an earlier entrance')",
      "wrong": true
    },
    {
      "scale": "1/1000000000",
      "rotated": true,
      "direction": [
        0,
        0,
        -1
      ],
      "cap": "1/16",
      "want_kind": "entrance",
      "want_exact_t": "0",
      "got_kind": "entrance",
      "got_exact_t": "0",
      "wrong": false
    },
    {
      "scale": "100000000",
      "rotated": true,
      "direction": [
        1,
        0,
        0
      ],
      "cap": "0",
      "want_kind": "entrance",
      "want_exact_t": "0",
      "got_kind": "none",
      "got_exact_t": "None",
      "wrong": true
    },
    {
      "scale": "100000000",
      "rotated": true,
      "direction": [
        1,
        0,
        0
      ],
      "cap": "1/16",
      "want_kind": "entrance",
      "want_exact_t": "0",
      "got_kind": "none",
      "got_exact_t": "None",
      "wrong": true
    },
    {
      "scale": "100000000",
      "rotated": true,
      "direction": [
        0,
        0,
        1
      ],
      "cap": "1/16",
      "want_kind": "entrance",
      "want_exact_t": "0",
      "exception": "RuntimeError('first_entrance3: no in-extent facet-cover candidate, yet the bodies touch at t = Fraction(0, 1); the candidate set missed an earlier entrance')",
      "wrong": true
    },
    {
      "scale": "100000000",
      "rotated": true,
      "direction": [
        0,
        0,
        -1
      ],
      "cap": "1/16",
      "want_kind": "entrance",
      "want_exact_t": "0",
      "got_kind": "entrance",
      "got_exact_t": "0",
      "wrong": false
    }
  ]
}
```

### G6J-J03 · major

- **位置**：`src/eab/kernel2d/covers.py:145-146`
- **结论**：公共 in_cone 对允许的微反射 normal_cone 输出把反向薄扇区错误标严格内部
- **具体输入 → 输出**：{
  "P": [
    [
      0,
      0
    ],
    [
      1,
      0
    ],
    [
      2,
      "-1/100"
    ],
    [
      2,
      1
    ],
    [
      0,
      1
    ]
  ],
  "vertex": 1,
  "normal_cone_tol": "1/50",
  "direction": [
    "1/200",
    1
  ],
  "expected": -1,
  "actual": 1,
  "independent_certificate": "与两条实际报告法向的 Fraction 点积均负，角距均>pi/2，远超1/50 sin窗口"
}
- **建议（未实施）**：strict 分支补精确非反射/同侧约束；微反射同向显式窗口最多返回0，反向必须拒绝
- **计数/影响边界**：只公共helper组合，不把 ve_cover/vv_cover 计为受影响（它们走别的精确谓词）；三姿态均复现
- **合同依据**：src/eab/kernel2d/covers.py:115-117 normal_cone 明示小反射在转角<pi/2且sin不超过窗口时接纳；src/eab/kernel2d/covers.py:143 in_cone 明示对给定向量精确判1严格内部/0边界或显式sin窗口/-1外部；src/eab/kernel2d/covers.py:17-25 局部单盖默认精确，域窗口只放宽有效集，strict始终精确严格性。
- **可直接重跑**：

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -X utf8 review/repro/geom2j_reflex_cone_inverse.py
```

[复现1](file:///D:/eab-wt/g6j/review/repro/geom2j_reflex_cone_inverse.py)；[主审输出1](file:///D:/eab-wt/g6j/review/logs/root_confirm_geom2j_reflex_cone_inverse.log)。

**主审在本 HEAD 亲自运行的完整输出**（所有脚本 exit 0，表示反例已被证明）：

```text
{
  "status": "CONFIRMED",
  "cases": [
    {
      "scale": "1",
      "rotation": [
        "1",
        "0"
      ],
      "reported_cone": [
        [
          0.0,
          -1.0
        ],
        [
          -0.009999500037496875,
          -0.9999500037496876
        ]
      ],
      "direction": [
        "1/200",
        "1"
      ],
      "independent_dot_signs": [
        "negative",
        "negative"
      ],
      "angle_to_each_boundary": ">pi/2",
      "window": "1/50",
      "expected_inverse": "-1",
      "got_inverse": 1,
      "got_downward_window": 0
    },
    {
      "scale": "1/1000000000",
      "rotation": [
        "3/5",
        "4/5"
      ],
      "reported_cone": [
        [
          0.8,
          -0.6
        ],
        [
          0.7939603029772518,
          -0.60796960227981
        ]
      ],
      "direction": [
        "-797/1000",
        "151/250"
      ],
      "independent_dot_signs": [
        "negative",
        "negative"
      ],
      "angle_to_each_boundary": ">pi/2",
      "window": "1/50",
      "expected_inverse": "-1",
      "got_inverse": 1,
      "got_downward_window": 0
    },
    {
      "scale": "100000000",
      "rotation": [
        "3/5",
        "4/5"
      ],
      "reported_cone": [
        [
          0.8,
          -0.6
        ],
        [
          0.7939603029772518,
          -0.60796960227981
        ]
      ],
      "direction": [
        "-797/1000",
        "151/250"
      ],
      "independent_dot_signs": [
        "negative",
        "negative"
      ],
      "angle_to_each_boundary": ">pi/2",
      "window": "1/50",
      "expected_inverse": "-1",
      "got_inverse": 1,
      "got_downward_window": 0
    }
  ],
  "scope": "public helper composition only; ve_cover/vv_cover use other exact predicates"
}
```

### G6J-J04 · major

- **位置**：`src/eab/dual.py:225-228`
- **结论**：Dual.sqrt 的解析导数仍先舍入 primal，再乘 seed，次正规可表达导数错一倍，范围失败也静默返回0/inf。
- **具体输入 → 输出**：u=2^-1074，v=nextafter(1,+inf)，Dual(v,(3u,))：primal=1正确，但导数=2u；原解析导数a/(2sqrt(v))的正确舍入为u。7u/11u/15u也向上错1u。v=2^1022,seed=2^-600导数舍零；v=u,seed=2^1023导数inf，无exact通道或响亮范围异常。
- **建议（未实施）**：把完整带符号解析导数作为最终构造量（其平方a²/(4v)），零种子独立处理；范围不可表达时明确拒收或保留exact证书；增加次正规双侧中点与范围门。
- **计数/影响边界**：窄次正规/范围边缘故major；不声称所有Dual超越函数都具有正确舍入保证，不指控生产construction.sqrt本身错误。
- **可直接重跑**：

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -X utf8 review/repro/root_dual_sqrt_final_rounding.py
```

[复现1](file:///D:/eab-wt/g6j/review/repro/root_dual_sqrt_final_rounding.py)；[主审输出1](file:///D:/eab-wt/g6j/review/logs/root_confirm_root_dual_sqrt_final_rounding.log)。

**主审在本 HEAD 亲自运行的完整输出**（所有脚本 exit 0，表示反例已被证明）：

```text
{
  "result": "CONFIRMED",
  "kind": "representable derivative double-rounding",
  "rows": [
    {
      "v_hex": "0x1.0000000000001p+0",
      "seed_units": 3,
      "actual_primal": 1.0,
      "actual_derivative_units": "2",
      "correct_derivative_units": 1,
      "proof": "a^2/(4*v) lies strictly inside expected neighboring midpoint squares"
    },
    {
      "v_hex": "0x1.0000000000001p+0",
      "seed_units": 7,
      "actual_primal": 1.0,
      "actual_derivative_units": "4",
      "correct_derivative_units": 3,
      "proof": "a^2/(4*v) lies strictly inside expected neighboring midpoint squares"
    },
    {
      "v_hex": "0x1.0000000000001p+0",
      "seed_units": 11,
      "actual_primal": 1.0,
      "actual_derivative_units": "6",
      "correct_derivative_units": 5,
      "proof": "a^2/(4*v) lies strictly inside expected neighboring midpoint squares"
    },
    {
      "v_hex": "0x1.0000000000001p+0",
      "seed_units": 15,
      "actual_primal": 1.0,
      "actual_derivative_units": "8",
      "correct_derivative_units": 7,
      "proof": "a^2/(4*v) lies strictly inside expected neighboring midpoint squares"
    }
  ]
}
UNCHECKED DERIVATIVE RANGE: Dual(6.703903964971299e+153, (0.0,))
UNCHECKED DERIVATIVE RANGE: Dual(2.2227587494850775e-162, (inf,))
```

### G6J-J05 · minor

- **位置**：`src/eab/limit.py:414-418;519-524`；`src/eab/limit_multi.py:193-198;217-224`
- **结论**：有限荷载输入下无限承载答案正确，但uncertainty=NaN仍标resolved，报告没有告警。
- **具体输入 → 输出**：二维两地面接触p=(±1,0),n=(0,1),mu=.5，dead=[0,1,0],live=[0,-2^-1074,0]。独立平衡N=alpha*u-1≥0，所以无界正确；单/多体均返回uncertainty=NaN,resolvability=resolved,statuses=[]。精确量完成所写U比值为4*2^-53有限，float对偶inf乘舍零误差产生NaN。
- **建议（未实施）**：可分辨性比值先在精确/缩放量上完成再显示；任何NaN/Inf估计明确报告unknown/unresolved或诊断，不凭NaN比较走默认resolved；不改本格正确的unbounded容量。
- **计数/影响边界**：仅报告缺陷，未证明capacity错误；此格resolved本身可能合适，不能升级为力学critical。
- **可直接重跑**：

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -X utf8 review/repro/root_resolution_nan.py
```

[复现1](file:///D:/eab-wt/g6j/review/repro/root_resolution_nan.py)；[主审输出1](file:///D:/eab-wt/g6j/review/logs/root_confirm_root_resolution_nan.log)。

**主审在本 HEAD 亲自运行的完整输出**（所有脚本 exit 0，表示反例已被证明）：

```text
{
  "result": "CONFIRMED REPORT DEFECT ONLY",
  "core_capacity_correct": true,
  "all_inputs_finite": true,
  "formula_U_without_display_underflow": "1/2251799813685248",
  "rows": [
    {
      "type": "LimitResult",
      "status": "unbounded",
      "alpha": "inf",
      "uncertainty": "NaN",
      "resolvability": "resolved",
      "resolvability_statuses": []
    },
    {
      "type": "MultiLimitResult",
      "status": "unbounded",
      "alpha": "inf",
      "uncertainty": "NaN",
      "resolvability": "resolved",
      "resolvability_statuses": []
    }
  ]
}
```

## 2. 第一顺序：第九轮六条回归重放

六个原复现从只读 g6i/review/repro 复制至本树 review/repro，ROOT 指向本树。原脚本故意断言“缺陷仍在”，因此本树正确时 exit=1；**不能据此误判回归失败，也不能只凭 exit=1 就宣称已修**。随后保留原输入、独立证书并反转目标断言，六个正向脚本全部 exit=0。两组完整输出分别入 JSON；未更改生产文件。

| 原发现 / 复现脚本 | 原运行关键输出 | 正向复跑关键输出 | 状态 |
|---|---|---|---|
| G6I-GEOM2-01 / geom2_convex_flat_facet_domain | 旧错误 VE(0,2) 断言红；实际 VE(0,3)，points=(.5,1)，gap=0 | 四姿态仅有限域 VE(0,3)；FF 初态正确 t=0，无异常 | **已修** |
| 折面凸性/凹棱 / geom3_folded_reflex_hidden | 旧凸断言红；actual=False、reflex=[(5,7)] | 24格独立中点/折棱证书一致；角=π/2 | **已修** |
| cone margin 次正规 / geom3_cone_margin_subnormal | 旧 actual_margin==0 断言红 | 24格、wrong_cases=0；首格 actual=u=expected=u | **已修** |
| margin oracle 范围 / docs_margin_oracle_range | 旧“正常生产被oracle误拒”断言红 | -500/-540/-600 三格PASS；真实内核 sqrt(float(d2)) 变异分别被 default-exact distance/cover distance 断言拒绝 | **已修** |
| 各闭壳方向 / geom3_manifold_component_orientation | issues==[] 断言红；明确 component1 inward | volume=56不再掩盖负8小壳；whole/small诊断均报告错误方向 | **已修** |
| 当前文档过时句 / docs_stale_current_contracts | 原“命题7、8均未实现”文本断言红 | canon分开命题7/8；README历史审核边界明确；2D不变性每格独立精确oracle且无tol_eff | **已修** |

[六个原脚本及逐条完整输出](file:///D:/eab-wt/g6j/review/logs/r9_originals.json) · [六个正向脚本及逐条完整输出](file:///D:/eab-wt/g6j/review/logs/r9_positive.json) · [原重放runner](file:///D:/eab-wt/g6j/review/replay_r9.py) · [正向验证runner](file:///D:/eab-wt/g6j/review/make_positive_r9.py)。

原运行的末尾断言/异常原文：

**geom2_convex_flat_facet_domain.py，exit=1**
```text
    assert r.label==('VE',0,2) and ('VE',0,2) in r.tied_labels,r
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Entrance2(kind='entrance', t=1.0, x=(0.5, 1.0), label=('VE', 0, 3), normal=(0.0, 1.0), point_a=(0.5, 1.0), point_b=(0.5, 1.0), gap=0.0, tied_labels=(('VE', 0, 3),), n_candidates=2, near_labels=(('VE', 0, 3),), t_exact=Fraction(1, 1))
```

**geom3_folded_reflex_hidden.py，exit=1**
```text
    assert got_convex is True and got_reflex==[],(h,scale,translation,got_convex,got_reflex)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: (Fraction(1, 2), Fraction(1, 1), (0, 0, 0), False, [(5, 7)])
```

**geom3_cone_margin_subnormal.py，exit=1**
```text
    assert rows[0]['actual_margin']==0.0 and rows[0]['expected_margin']==math.ulp(0.)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError
```

**docs_margin_oracle_range.py，exit=1**
```text
    assert all(row["test_oracle_status"] == "AssertionError: default-exact distance construction"
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError
```

**geom3_manifold_component_orientation.py，exit=1**
```text
    assert issues==[],issues
           ^^^^^^^^^^
AssertionError: ['component 1: orientation is inward at nesting depth 0 (expected outward)']
```

**docs_stale_current_contracts.py，exit=1**
```text
    assert "\u4f9d\u8d56\u547d\u9898 7\u30018\uff0c\u5747\u672a\u5b9e\u73b0" in canon93
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError
```

## 3. 第二顺序：历轮同类漏网搜索

| 历轮族 | 本轮重新核的路径/证据 | 结果 |
|---|---|---|
| 标签有限接触域 | R9四姿态原复现；二维产品并首入1192 tied有限域格；VE/EV clamp、FF闭段交、facet root合并后的标签重映射 | 原项已修，未发现新域外标签 |
| 声明三角化凸性/凹棱 | is_convex/reflex/dihedral/public cone都读actual surface；roof24格、Cartesian L/U/分壳；真实拓扑撤回源环变异 | 原项已修，目标断言有牙 |
| 冻结解析导数大跨度相消 | raw多项式Fraction jet，1e±200、1e±40与1e100坐标；独立200 primal/600通道逐值核 | 冻结路径无新错；通用Dual.sqrt另漏J04 |
| 首入初态分类 | 2D E内部紧配和普通边界、3D拓扑初态、tmax0、切向/背离 | **J02** 普通面边界漏网，非旧紧配内缝 |
| 迁移门失牙 | 新静态gate真实内部变异与七语法；E2–PERF断言diff/内部几何、distance、LP污染 | **J01**；不能扩大为全套动态门无牙 |
| 可变缓存/别名/Dual | margin重造Cover3外壳、surface内容payload、interlock值键/函数身份、2D别名压力 | 所测等价/突变隔离通过，未确认串用 |
| 隐式噪声与浮点oracle | 原strict vs explicit window分层；G0整数 arrangement、G03独立耳切/整数凸包、LP原数据证书 | 无新隐式band错；公共in_cone **J03** |
| 先构造舍入/先平方再相减 | 统一scalar/sqrt/norm/unit/normalized及所有R9diff；最大中间2^5000抵消、小root不先舍平方 | 主构造独立边界证书通过；**J04**漏导数，**J05**报告量先显示 |
| 快路只查输入不查派生 | orient2 4907个NaN/Inf determinant；mixed predicates12500；false LP candidate9格；interval非有限污染 | exact fallback接线通过，未确认新错 |
| oracle仅查区间中点 | oracle_construction认证上下两侧RN单元，候选失败bit搜索；R9正常生产+真sqrt(float(d2))污染 | 旧oracle修复且有牙；独立边界 sweep 未见新错 |
| 特征尺度上溢门失效 | checked norm/area、G0 Fraction误差界和非有限独立构造检查；互锁1e±200输出不可表达10格响亮失败 | 不再用Inf bound吞错；10格异常不算“通过有限输出” |
| 暴力真值漏特征 | folded internal edges/slab下界；Cartesian凹并集独立距离；源环边替换变异 | 活跃合法域未确认新遗漏；孤立未引用顶点列未确认 |
| 文档优先性/正本 | 00§3.3/替代入口/早期谱系、canon三层、README撤序数性主张，07缺口表 | 没有再发现当前核心优先性冒称；未外网重做文献优先性 |

## 4. 第三顺序：R9 新代码及251处迁移

`git diff 9f99025..HEAD -- src tests tools` 文件清点：**95文件=18 src + 76 tests + 1 tools**。构造通道逐行看生产与独立参考构造/AST全模块；几何两路看所有所属src hunks；主审核Dual/limit/LP/reader和力学test hunks。迁移量251来自实现方统计，**不是本审重新计算的独立数字**；审查按具体diff和非机械数学变更对账，不凭替换数量确认正确。

重点人工核：cone margin 不先舍分量、support gap 的精确平方比、unit向量单分量最终根、witness exact=True后相减、escape完整比值、direction_noise不先舍sine、margin的平方真值与显示误差分开、oracle从4ULP改成全RN单元、原Fraction/int norm不被float吞掉。J04显示“通用构造迁移”仍不是全仓所有派生量都只舍一次。

新白名单中候选过滤/输入协议/最终显式cast/故意变异都有现行用途依据；但它以函数+规则排除而非具体AST节点排除，**未证明未来编辑安全**。白名单过宽为风险项不重复记第二个已确认finding；普通非白名单keyword绕过已经足够确认J01。

[完整原diff](file:///D:/eab-wt/g6j/review/notes/r9_diff.patch) · [95文件清单](file:///D:/eab-wt/g6j/review/notes/changed_files.json) · [逐文件覆盖/漏项补读及白名单核对](file:///D:/eab-wt/g6j/review/notes/r9_coverage_crosscheck.md) · [两锚点测试结构台账](file:///D:/eab-wt/g6j/review/notes/test_migration_inventory.json)。

结构台账的 R9 锚点9f99025中未删旧test函数；第五轮锚点b6126cf不是0删除，存在6个旧名，须按重命名/语义替换逐项解释，详见覆盖对账。assert数量、test名字和全绿均不自动证明门强度。

## 5. 九镜头覆盖与证据

### 镜头1：精确性声称与实际浮点分支

全src遍历得到138条词法可疑条件，逐路径分类另存；几何通道完整列428条条件并以函数/模块语义归类。清点包括if/while/条件表达式/comprehension，**不是类型推导的全程序证明**，不声称138就是全部浮点决断数。漏匹配的direct return比较、predicates过滤和LP reduced_sign由全文源码人工补核。

允许类有：(a)显式域/角/厚度窗、输入拒收；(b)最终构造输出的范围策略；(c)仅速度候选且exact兜底；(d)分辨性/名义展示；(e)未接线历史私有辅助。不得将它们全部笼统写成“没有浮点阈值”。具体旧geom3 _gordan/_min_norm/EE contacts仍有1e-12等阈值，但全仓引用日志显示现行overlap直接委托exact_geom，无调用；interlock nz噪声确实仅名义候选，96次全部None和假height=-999内部变异不改变权威根17/10与区间证书。readers.bdda_geom 的dup_tol+round_floor改变legacy重建数据，是公开输入政策，不等同默认EPIC原多边形。

本轮没有确认活跃默认成员因隐式噪声带产生的新反例；J02是逻辑漏初态，J03是strict方向条件错误，不能硬归噪声带。J05为报告NaN。

[138条分类及理由](file:///D:/eab-wt/g6j/review/notes/float_branch_classified.json) · [428条件库存](file:///D:/eab-wt/g6j/review/notes/geometry_branch_inventory.json) · [死辅助可达性检索](file:///D:/eab-wt/g6j/review/logs/geom3j_legacy_helper_reachability.log) · [名义决断隔离实测](file:///D:/eab-wt/g6j/review/logs/geom2j_nominal_decision_isolation.log)。

### 镜头2：快路、误差界、缓存等价性

- orient2d独立Fraction行列式12000格，其中111个次正规输入，4907个派生det非有限；无错号。
- orient3/cross/dot自写12500精确比较，mixed float/Fraction指数±1200；没有拿production Fraction helper作主oracle。
- exact_geom outward interval只做必要排除，无法认证/非有限污染回Fraction；convex/star/transverse快路都要原表面精确证书；675个凹并集实体格无差异。未重新形式化证明所有误差界。
- LP filtered pricing8000格，与纯Fraction同符号；三个真状态×三个假float状态候选9格全部由精确层纠正。
- margin/interlock缓存键读全部内容而非对象id；mutable Cover/outer list隔离、geometry edits、offset/窗口/函数身份等门已执行；240个互锁缓存检查及2D别名检查通过。没有证明任意自定义数值类的cache健全性。

### 镜头3：oracle独立性（纪律A）

生产construction用isqrt/精确quantum，中点参考采用自有按位二分+Fraction完整cell、Decimal只候选；不互import。审查者边界oracle再独立写有理平方/邻居cell认证，不把两实现相等当正确证明。

G0二维oracle自有整数winding/local arrangement/rational距，生产耳切/SAT不共helper。G03凸oracle自有整数凸包/支撑/秩，曲面oracle自有耳切/ray parity/全特征距离；相同声明耳切模型是同一输入语义，不可因此断言没有“共同模型错”。本轮Cartesian产品并与slab下界提供第三方结构真值。frozen新jet oracle为审查者本地多项式链式法，不用生产原语。

brute首入二分共享production overlap、暴力逃逸共享predicate、名义source-ring盖均只能佐证；没有拿它们当独立主oracle。孤立点探针两距离同时错属有效域未明，未计“共享helper”finding。

### 镜头4：测试迁移有没有变弱

两锚点所有变动test文件做AST结构台账（b6126cf132文件，9f99025 76文件）。重点全文/diff对比E2–PERF迁移：刚体float边界变形不再硬套旧理想标签，但**每个实际给定坐标**都过独立精确oracle；精确仿射组仍保解析计数。support集、源点保存、exact_params加入对账；不因“边界允许变化”跳过当前真值。

真实内核变异至少包括：撤actual surface使roof凸/内部reflex错；edge arc撤actual面；锥交恒True造成24个假E极点；brute distance只保源棱漏slab中点；body_distance/margin_contacts恢复sqrt(float(d2))；LP真实返回污染alpha/exact_x/exact_y；R9有限标签内部域谓词恒True。红的目标断言及原因存独立日志。不是产物后追加假数据。

**确认例外J01**：静态门对同一个真实cone margin错误变异仍0违例；动态中点门却能抓它，二者必须区分。没有确认已读历史动态门存在“旧能抓、新抓不到”的新实例。未完成所有132个历史文件每条断言的逐条变异穷举。

[五个真实几何变异目标断言](file:///D:/eab-wt/g6j/review/logs/geom3j_teeth.json) · [两条真实距离变异](file:///D:/eab-wt/g6j/review/logs/r9_positive_docs_margin_oracle_range.log) · [四条力学真实返回污染](file:///D:/eab-wt/g6j/review/logs/root_limit_guard.log)。

### 镜头5：几何独立压力/反例

| 范围 | 审查者独立真值 | 当前实测 |
|---|---|---|
| 2D凹凸、flat链、一般位置、剪切与单位/大平移 | 原Cartesian polyomino产品差集、四象限E内部、逐矩形ray区间；不调用生产triangulation/Minkowski/法锥 | E成员3200、body1600、G0 overlap1600、首入1600、tied有限域1192，无分歧 |
| 2D分离距离/盖 | Cartesian产品间平方距、Decimal1000位只最终根，全部候选gap也核 | 1201分离样本精确最短盖与构造全等 |
| 3D凹L/U、分离壳、精确旋转/平移/缩放 | 原box区间并集关系与平方距离，9变换 | 675关系格无分歧，分离平方距/部分最终RN cell核验通过 |
| 冻结primal/导数 | raw多项式Fraction jet + Decimal1000只终根 | 200 primal、600 channel、200 normal证书全等 |
| 互锁/最短非贯入高度 | 60对product box闭式根，精确旋转/平移/缩放与逐interval复核 | 120 exact根、1118区间、240缓存检查通过；10个最终显示不可表达格明确异常 |
| 新反例 | 初态闭集交矩形证书、反向法锥点积证书 | **J02、J03**，主审已重复 |

测试涵盖1e8大坐标、1e-9微尺寸、混合指数、平直链、近平行与次正规；对任意高亏格曲面/所有畸形输入未穷举。短棱/退化输入域拒收不自动算数学错。

### 镜头6：接触窗口（局部贯入厚度）

**需要订正工单镜头的假设**：当前文档没有声称六轴“相触⇒PD_closed≤w”。六轴证书核内部非交，只证非交内部平移下确界rho≤w；紧配封闭空腔原命名门有rho=1/8、PD_closed=19/8。沿用旧PD声称会给错误审查。

薄壳推理核：中心在每个外向三角严格内侧是星核充分证书；各面点凸组合给L1半径上界R；alpha=min(w/R,1/2)保障径向移除段≤w；core与对体内部不交使所有严格重叠落在壳内。axis或shell失败不等价PD>w；L1/六轴坐标依赖，不承诺窗口旋转不变。当前README/exact plan/design/canon和代码相互一致，test_perf_contact_window保留斜向漏检、双壁夹持、空腔、六方向及源内变异。未找到当前合法域可靠性反例，不声称完整欧氏PD算法已实现。

### 镜头7：极限分析与LP证书

主审8000定价、180独立全基LP重放；本轮新seed101012再180个指数±1100 LP，原始/对偶可行、强对偶和exact_x/y浮点views逐格核。60组闭式friction/tilt承载；单/多体分别180个10^-100错候选精确拒绝；污染真实limit_load四种返回都在selfcheck目标断言红。wrench 1e160/1e200先乘溢出再相消的旧问题当前正确给最终零moment。

LP精确证书覆盖optimal/unbounded/infeasible，浮点状态/基错误只能触发精确求解而非返回未核答案。本轮未确认LP核心silent错，但最终显示超范围可能inf，是保留exact证书的显示政策，不能用inf乘0再做报告判断。**J05**就是这样的报告遗漏。Dual并非LP证书替代，**J04**是通用解析导数错。

### 镜头8：文档 / 正本

已读给定README/AGENTS、两份exact设计计划的现行合同及历史更正、canon前言/映射/未实现/优先性三层/第八节；E2/E3E4/E5a/E5a2/E5b/PERF责任项、迁移、变异与边界；只读g6f第五轮之后提交说明。文档通道读01/03/07全文和00各相关节（§3.3、§4.6、§7、第八节），只核给定正本，不外网扩展学术优先性调查。

canon第八节诚实登记07的稳定枚举、六reader范围、G1/G2/G3/G4/G5与Phase3/5缺口；FF/FE只是首入标签，未冒称全部ContactRecord/Cover3构造。原三句过时现行文本已修。**有命名门不等于承诺全域成立**，J02直接反驳三维闭集首入普通边界这一核心语义；作为同一计算finding计数，不另加文档major。

[当前核心声称/测试/断言/边界矩阵](file:///D:/eab-wt/g6j/review/notes/docs_claim_matrix.md) · [正本和canon详细核验](file:///D:/eab-wt/g6j/review/notes/geom3_docs_audit.md) · [只读历史提交体](file:///D:/eab-wt/g6j/review/notes/g6f_commit_bodies.txt)。

### 镜头9：第五轮50条中的25条重放

原JSON无ID，因此以下使用**零起始raw_index**，避免将旧编号+1与raw index错配。选取25个不同项目，超过至少20要求；不是宣称50条全部重放。原脚本或原反例命名门/等价内部变异均标明；已删除旧浮点语句不假装重新杀死同一句。

| raw_index | 原错误与重放 | 当前输出 / 判定 |
|---:|---|---|
| 8 | 原近共线tangent脚本root_g6e_09 | 正确ValueError拒收；旧“接受不垂直模型”不再成立 |
| 10 | 原错alpha/粘聚脚本root_g6e_11 | .4/.001/.0001/1e-5均raise；1e6三错factor全部ok=False |
| 19 | 原multi错误机构root_g6e_20 | D=0/1e3/1e5均False False |
| 20 | 原farbody错alpha root_g6e_21 | D=10/1e6/1e9均False |
| 21 | 原farbody分辨性root_g6e_22 | None/100/1e4/1e6一致alpha与U |
| 23 | 横穿面噪声漏项原公开入口迁移门 | 9 passed，旧路径删除 |
| 24 | **原VV3脚本**psi四格 | 均VV3，无RuntimeError，距约.14142135623730964 |
| 25 | 原微倒角facet probe+独立SAT | state=1；2000Fraction SAT全等 |
| 26 | 原短边有效锐角 | 六格接受 |
| 27 | 原EE每侧arc门 | 12 passed，不借另一侧宽度 |
| 28 | 原G03大小比/双尺四格 | 4 passed，零豁免 |
| 29 | 原近并行局部strict/G0正反 | 六格passed、symdiff=[] |
| 30 | 原oracle两参数近并行见证命名门 | 1 passed |
| 35 | 原EE extent近平行ridge系列 | 48 passed，精确原参数/显式window |
| 37 | 原tolerance-pop极点(1e-15,-.001) | 极点保留，原/变换G0通过 |
| 38 | 锥交真实恒True等价多报变异 | hull_vertex_mismatch=24，报告红；1 passed |
| 39 | facet_vote3默认L命名门 | 1 passed |
| 40 | 原微凹凸路径三tol | 精确拒reflex vertex5；一般state=1 |
| 41 | 原yaw=10^-8.75 roof门 | 1 passed，零豁免 |
| 42 | 原非共面seed/五档scale | 5 passed |
| 43 | **原F4脚本**四对(3,9),(4,8),(7,3),(8,2) | cone=True且VV3；独立有理真值True；G0 passed、ambiguous=0 |
| 44 | 原single远origin错alpha root_g6e_45 | D0..1e6三个错factor均False |
| 45 | 原宽度语句已删除；忽略支持点等价源内变异 | 1 passed，精确支持证书抓漏极点 |
| 48 | 原工程坐标VV噪声补偿 | 三旋转strict=False，仅EV(3,0)，独立负support证书 |
| 49 | 原三微脊G03 ambiguity族及实际假极点 | 3 passed，零豁免，独立真值拒假极点 |

[root六项完整输出](file:///D:/eab-wt/g6j/review/logs/root_checks.json) · [二维六项完整输出](file:///D:/eab-wt/g6j/review/logs/geom2j_g6e_six_replay.log) · [三维13项逐条输出](file:///D:/eab-wt/g6j/review/logs/geom3j_historical_replay.json) · [原24输出](file:///D:/eab-wt/g6j/review/logs/geom3j_g6e_original_24.log) · [原43输出](file:///D:/eab-wt/g6j/review/logs/geom3j_g6e_original_43.log)。

## 6. 未确认（不计critical/major/minor）

1. **孤立未引用顶点**：面仍为两盒、加入未被任何face引用点(2.75,0,0)，面表面真距2，brute/G03 oracle共同给.25，margin响亮报exact squared-distance mismatch；manifold_issues=[]。可重复，但未证明孤立存储点属“有效嵌入闭2-manifold表面”的受保障输入域，且空诊断不声明完整合法性认证，故不扩大合同计数。
2. **2D G0 None见证skip**：没有当前生产输入使其偷偷错过核心最短存在性保证；猜测mutant-green不等于已有错误。未计。
3. **interlock十个1e±200格**：最终名义area/normal等显示不可表达，明确抛范围异常；非静默错误，也不是十格finite构造通过。
4. **白名单范围未来风险**：函数级豁免可能掩盖后来编辑，但未另找当前豁免内错误；J01已是当前scanner真实漏洞，不重复计。

[孤立点探针](file:///D:/eab-wt/g6j/review/repro/geom3j_unreferenced_vertex.py) · [其输出](file:///D:/eab-wt/g6j/review/logs/geom3j_unreferenced_vertex.log)。

## 7. 完整性批评与残余风险

- 合并各分路阅读覆盖全部src/eab生产模块；收尾主审补读各__init__、ContactRecord、四reader、LP浮点主体和margin全文。关键几何/构造/精确模型多数全文逐段看，但**阅读不等于对每个算法/分支形式化证明**。未穷尽所有浮点误差界、所有Python动态taint、所有数值类型。
- R9的95 changed file diff逐文件分路对账；251是实现报告计数，并没有把251个替换各做一套独立变异证明。历史132 test文件有结构清点和高风险人工diff/牙，**没有每个旧断言穷举“旧能抓而新不能抓”所有变异**。这项请求的穷举强度未完全达到，不能包装成迁移全域认证。
- tools/check_exact_construction全文读；其余未变更tools仅按门与报告指向重点查看，**未逐行重读全仓工具脚本/所有未变更tests/helpers**。没有重跑姊妹exe/导出生成器；只核入库夹具和当前门，无姊妹工程验证。
- 文档矩阵核核心现行契约；历史“已完成/已验证”逐句穷举仍受阅读范围限制，文档词法库存明确区分历史与现行，不声称所有历史性能数字或外部论文都已重新核实。
- 独立oracle是有限输入族：产品并、精确变换、随机位形、多指数jet/LP；不覆盖任意高亏格表面、所有耳切模型、所有凹体全局E、所有无界射线display和所有非微分点。没有把全套绿作为退出证据。
- 审查脚本曾有错误test文件名、R.IDENTITY常量和positive runner锚点计数输入错误；纠正后完整重跑，原日志保留。它们不是生产缺陷，报告只采最终有效输出。所有计入finding已由root亲自再跑，子审提出但未复现的一律未计。
- 审查不会修复这五项。下一步应由实现方处置4 major、补内部牙，再在新的只读fresh树复审；目前**M0退出标准未满足**。

## 8. 证据入口与验证

- [机读发现与六回放完整输出](file:///D:/eab-wt/g6j/review/G6J_findings.json)
- [主审亲自复现：退出码、脚本SHA、完整输出](file:///D:/eab-wt/g6j/review/logs/root_confirmations.json)
- [构造/静态分路](file:///D:/eab-wt/g6j/review/notes/construction_audit.md)
- [二维/首入/冻结/互锁分路](file:///D:/eab-wt/g6j/review/notes/geometry_audit.md)
- [三维/拓扑/窗口/正本分路](file:///D:/eab-wt/g6j/review/notes/geom3_docs_audit.md)
- [主审LP/力学分路](file:///D:/eab-wt/g6j/review/notes/root_mechanics_audit.md)
- [全部审查交付与日志索引](file:///D:/eab-wt/g6j/review/EVIDENCE_INDEX.md)
- [最终JSON/链接/源码原字节核验](file:///D:/eab-wt/g6j/review/logs/final_verification.json)
- [35个生产模块/148个test文件/13个tool文件逐文件阅读边界](file:///D:/eab-wt/g6j/review/notes/coverage_scope.json)
- [独立收尾报告与证据交叉核对](file:///D:/eab-wt/g6j/review/notes/final_report_crosscheck.md)

G6J_DONE critical=0 major=4 minor=1
