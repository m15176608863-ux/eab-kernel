# WO-G6G：G6第七轮独立正确性复审

**确认：critical=0 / major=9 / minor=2。M0不得退出。**

第六轮12条原始输入均已修；本轮新增9条major与2条minor，不把同类发现重复记为旧案未修。未修改实现代码。

## 全套自跑结果

- HEAD `d44dd78e84fa0434860f52ca1a76306ddc498c48`。
- `8866 passed in 1545.12s (0:25:45)`；exit=0。
- 起止 UTC：2026-10-12T02:40:31.621160+00:00 → 2026-10-12T03:06:34.730572+00:00；墙钟 1563.110s（并行审查共享机器，不能与实现方单跑时长直接比较）。
- 命令：`"C:\Program Files\Python312\python.exe" -X utf8 -m pytest -q -p no:cacheprovider tests --basetemp=D:\eab-wt\g6g\review\tmp_full_suite`；`PYTHONDONTWRITEBYTECODE=1`、`PYTHONIOENCODING=utf-8`。
- tracked SHA-256差异0；[全套原始日志](file:///D:/eab-wt/g6g/review/logs/full_suite.log) / [命令与完整性元数据](file:///D:/eab-wt/g6g/review/logs/full_suite.json)。

## 已确认发现总表

|编号|严重性|位置|一句话结论|复现|
|---|---|---|---|---|
|G6G-01|major|`src/eab/kernel2d/g0_oracle.py:136-141`|first-exit oracle 只查事件区间中点，跳过前后均重叠的瞬时相触事件，出口完备性门会漏检真正的第一出口。|[脚本](file:///D:/eab-wt/g6g/review/repro/g6g_geom2_first_exit_pinch.py) / [实跑输出](file:///D:/eab-wt/g6g/review/logs/root_confirm_first_exit_final.log)|
|G6G-02|major|`src/eab/kernel2d/covers.py:238-239; src/eab/kernel2d/geom.py:63-71`|2D VV 仍先舍入精确差分量再 norm/unit，次正规与巨大有限输入给错误单位法向，且可表示的最终 gap 也会错。|[脚本](file:///D:/eab-wt/g6g/review/repro/g6g_geom2_vv_extremes.py) / [实跑输出](file:///D:/eab-wt/g6g/review/logs/root_confirm_vv.log)|
|G6G-03|major|`src/eab/kernel2d/g0.py:56-63,205-206`|有限坐标的特征长度显示上溢后变成无限验收阈值，二维 G0 在实际全部漏盖、误差为 inf 时仍报告 passed=True。|[脚本](file:///D:/eab-wt/g6g/review/repro/g6g_geom2_g0_infinite_scale.py) / [实跑输出](file:///D:/eab-wt/g6g/review/logs/root_confirm_g0_infinite_scale.log)|
|G6G-04|major|`src/eab/kernel3d/geom3.py:831`|brute_feature_distance只枚举源面边界棱，漏三角化折面内部棱，普通有效曲面的最小距离静默高估。|[脚本](file:///D:/eab-wt/g6g/review/repro/geom3_brute_missing_diagonals.py) / [实跑输出](file:///D:/eab-wt/g6g/review/logs/root_confirm_geom3_brute_final.log)|
|G6G-05|major|`src/eab/kernel3d/geom3.py:215`|全仓同类扫描漏掉face_area和facet_gap3/support_gaps3的最终缩放前舍入，可表达非零面积/间隙被放大为两倍。|[脚本](file:///D:/eab-wt/g6g/review/repro/geom3_area_double_rounding.py) / [实跑输出](file:///D:/eab-wt/g6g/review/logs/root_confirm_area_and_gap_final.log)|
|G6G-06|major|`src/eab/margin.py:142`|margin_contacts仍从舍入后的全局EE见证相减构造normal，正确非零距离的法向被清成None或转错方向。|[脚本](file:///D:/eab-wt/g6g/review/repro/geom3_margin_normal_loss.py) / [实跑输出](file:///D:/eab-wt/g6g/review/logs/root_confirm_ee_normal_final.log)|
|G6G-07|major|`src/eab/dual.py:106-131`|Dual 幂的快路仅检查输入范围，不检查派生幂系数，先下溢再乘种子会静默抹掉可表示的导数。|[脚本](file:///D:/eab-wt/g6g/review/repro/root_power_range.py) / [实跑输出](file:///D:/eab-wt/g6g/review/logs/root_confirm_power_final.log)|
|G6G-08|major|`src/eab/kernel3d/geom3.py:329-356`|Polyhedron.volume/centroid 的浮点叉积中间下溢破坏体积、体心，甚至使循环重排同一面环改变答案。|[脚本](file:///D:/eab-wt/g6g/review/repro/root_polyhedron_mass_range.py) / [实跑输出](file:///D:/eab-wt/g6g/review/logs/root_confirm_mass_final.log)|
|G6G-09|major|`docs/exact_3d_design.md:116`|六轴只证内部不交，不能推出理论正本01所定义的闭集完全分离PD≤w：恰好贴合的封闭空腔是反例。|[脚本](file:///D:/eab-wt/g6g/review/repro/docs_tight_cavity_pd.py) / [实跑输出](file:///D:/eab-wt/g6g/review/logs/root_confirm_cavity_pd_final.log)|
|G6G-10|minor|`docs/canon_map.md:19`|当前文档仍将 GAP3 同时写为开放和已处置，README 还把已替换的 polygons_overlap 写成当前非凸 G0 oracle。|[脚本](file:///D:/eab-wt/g6g/review/repro/docs_residual_claims.py) / [实跑输出](file:///D:/eab-wt/g6g/review/logs/root_confirm_docs.log)|
|G6G-11|minor|`docs/canon_map.md:395`|将第一份实现限定成 DDA 圈内仍不成立，违背 AGENTS 订正及 00 自己列出的早期入口块实现。|[脚本](file:///D:/eab-wt/g6g/review/repro/docs_residual_claims.py) / [实跑输出](file:///D:/eab-wt/g6g/review/logs/root_confirm_docs.log)|

## 逐条发现与总审查方核验输出

以下脚本 exit=0 表示**成功复现所断言的错误**，不是内核已通过新正确性门。每条日志均由总审查方在此HEAD再次运行，脚本SHA随JSON保存。

### G6G-01 · major · first-exit oracle 只查事件区间中点，跳过前后均重叠的瞬时相触事件，出口完备性门会漏检真正的第一出口。

- 位置：`src/eab/kernel2d/g0_oracle.py:136-141`。
- 具体输入 → 错误输出：B 为 L 形 [(0,0),(3,0),(3,1),(1,1),(1,3),(0,3)]；A=[(1/2,3/2),(1,3/2),(1,2),(1/2,2)] 沿 u=(1,-1)。两矩形并集独立 oracle 证明 t<1/2 时内部重叠，t=1/2 仅沿 x=1、y=1 接触。对任意 eps>0，平移 (1/2+eps,-1/2+eps) 后 min(x)=min(y)=1+eps，严格分离，故 t=1/2 真在拓扑 ∂E，不是 E 内部接缝。brute_ray_exit 返回 2。内核法锥路径删除第一出口全部盖，G0 仍 samples=1、passed=True。
- 直接运行：`python -X utf8 review/repro/g6g_geom2_first_exit_pinch.py`。[复现脚本](file:///D:/eab-wt/g6g/review/repro/g6g_geom2_first_exit_pinch.py)。
- 建议修复（审查方未实施）：事件本身也必须检查。明确 first-exit 是首次实体非内部重叠，还是拓扑 int E 的出口（两者对非凸对不总等价）；后一口径需精确识别事件邻域是否有 E 外方向，不能只看射线上邻接两个区间。补 L 形反角独立门要求 t=1/2，且真首出口缺盖变异必须报红。

```text
{
  "expected_first_exit": "1/2",
  "actual_return": "2",
  "independent_states": [
    {
      "t": "0",
      "state": 1
    },
    {
      "t": "499/1000",
      "state": 1
    },
    {
      "t": "1/2",
      "state": 0
    },
    {
      "t": "501/1000",
      "state": 1
    },
    {
      "t": "2",
      "state": 0
    }
  ],
  "topological_boundary_certificate": "for every eps>0: A translated by (1/2+eps,-1/2+eps) has min(x)=min(y)=1+eps, strictly disjoint from both B rectangles",
  "transverse_probes": [
    {
      "eps": "1/100",
      "state": -1
    },
    {
      "eps": "1/1000",
      "state": -1
    },
    {
      "eps": "1/1125899906842624",
      "state": -1
    }
  ],
  "baseline_gate": {
    "samples": 1,
    "passed": true
  },
  "internal_cone_mutant": {
    "first_boundary_covers": 0,
    "samples": 1,
    "passed": true
  }
}
```

### G6G-02 · major · 2D VV 仍先舍入精确差分量再 norm/unit，次正规与巨大有限输入给错误单位法向，且可表示的最终 gap 也会错。

- 位置：`src/eab/kernel2d/covers.py:238-239; src/eab/kernel2d/geom.py:63-71`。
- 具体输入 → 错误输出：q=2^-1074；浮点 d=(q,q) 给 normal=(1,1)，而应为 (1/sqrt2,1/sqrt2)；精确 d=(149q/100,49q/100) 给 gap=q，而精确平方介于 (1.5q)^2 和 (2.5q)^2，正确舍入 gap=2q；浮点 d=(maxfinite,maxfinite) 给 normal=(0,0)、gap=inf。全部 vv.strict=True。
- 直接运行：`python -X utf8 review/repro/g6g_geom2_vv_extremes.py`。[复现脚本](file:///D:/eab-wt/g6g/review/repro/g6g_geom2_vv_extremes.py)。
- 建议修复（审查方未实施）：保持 Fraction 相对向量，最终 gap 由精确平方构造根；单位法向独立缩放或精确分量平方比，不用已舍入 gap 作分母。与 3D 一致明确不可表示 gap 的报错/精确证据政策。补 2D 次正规、混合标量、巨大有限方向门。

```text
[
  {
    "input": "binary64 d=(minsubnormal,minsubnormal)",
    "gap": 5e-324,
    "normal": [
      1.0,
      1.0
    ],
    "normal_expected": [
      0.7071067811865476,
      0.7071067811865476
    ],
    "normal_norm": 1.4142135623730951
  },
  {
    "input": "rational d=(1.49q,0.49q)",
    "gap": 5e-324,
    "gap_expected": 1e-323,
    "normal": [
      1.0,
      0.0
    ],
    "normal_expected": [
      0.9499506873676175,
      0.31239989047659905
    ]
  },
  {
    "input": "binary64 d=(maxfinite,maxfinite)",
    "gap": "inf",
    "normal": [
      0.0,
      0.0
    ],
    "normal_expected": [
      0.7071067811865476,
      0.7071067811865476
    ],
    "expected_gap_policy": "unrepresentable norm should raise, not silently inf"
  }
]
```

### G6G-03 · major · 有限坐标的特征长度显示上溢后变成无限验收阈值，二维 G0 在实际全部漏盖、误差为 inf 时仍报告 passed=True。

- 位置：`src/eab/kernel2d/g0.py:56-63,205-206`。
- 具体输入 → 错误输出：m=maxfinite、h=m/2、k=m/4；B 为 L 形 [(-h,-h),(h,-h),(h,0),(0,0),(0,h),(-h,h)]，A 为上右凹槽内 [k,5k/4]^2。独立区间积距离为可表示的 k=4.4942328371557893e307，正常 G0 samples=1、passed=True、error=0；char_length 却为 inf。真实 _ve_side 全部改成 -1、VV 删除后无盖，G0 仍 samples=1、passed=True、worst_abs_error=inf、failures=[]。
- 直接运行：`python -X utf8 review/repro/g6g_geom2_g0_infinite_scale.py`。[复现脚本](file:///D:/eab-wt/g6g/review/repro/g6g_geom2_g0_infinite_scale.py)。
- 建议修复（审查方未实施）：缺盖/非有限候选或误差必须独立拒绝，不能靠 inf>threshold；有理或缩放形式评估特征尺度与验收界，任何不可表示验收界须 fail loud，而非自动通过。补纯有限大坐标控制组和真实全盖删除变异。

```text
{
  "all_input_coordinates_finite": true,
  "independent_exact_distance_display": 4.4942328371557893e+307,
  "float_characteristic_length": "inf",
  "baseline": {
    "samples": 1,
    "passed": true,
    "worst_abs_error": 0.0
  },
  "internal_cone_mutant": {
    "covers": 0,
    "samples": 1,
    "passed": true,
    "worst_abs_error": "inf",
    "failures": []
  },
  "cause": "atol*L = inf; abs(inf - finite) > inf is False"
}
```

### G6G-04 · major · brute_feature_distance只枚举源面边界棱，漏三角化折面内部棱，普通有效曲面的最小距离静默高估。

- 位置：`src/eab/kernel3d/geom3.py:831`。
- 具体输入 → 错误输出：A={|x|,|y|<=1,-1<=z<=1-|x+y|/2}; B={|x|,|y|<=1,3+|x-y|/2<=z<=6}，顶面/底面各由一个非共面四边形源环表示。三角化屋脊棱(5,7)/(1,3)的中点为(0,0,1)/(0,0,3)，独立距离下界与上界均2；函数返回sqrt(6)=2.449489742783178。同一表面展开为三角形源面后返回2。
- 直接运行：`python -X utf8 review/repro/geom3_brute_missing_diagonals.py`。[复现脚本](file:///D:/eab-wt/g6g/review/repro/geom3_brute_missing_diagonals.py)。
- 建议修复（审查方未实施）：在完整三角化表面的全部真棱上枚举棱棱距离，含折面内部对角棱；不要仅用A.edges()/B.edges()的源拓扑。增加折面屋脊独立slab/中点真值门及删除内部对角棱变异。

```text
{
  "independent_distance": 2.0,
  "source_result": 2.449489742783178,
  "expanded_same_surface": 2.0,
  "source_A_top_ring": [
    4,
    5,
    6,
    7
  ],
  "source_B_bottom_ring": [
    0,
    3,
    2,
    1
  ],
  "omitted_ridge_edges": [
    [
      5,
      7
    ],
    [
      1,
      3
    ]
  ],
  "ridge_witness_a": [
    "0",
    "0",
    "1"
  ],
  "ridge_witness_b": [
    "0",
    "0",
    "3"
  ],
  "source_witness_membership": [
    0,
    0
  ]
}
CONFIRMED source-ring brute_feature_distance silently overestimates exact surface distance; true=2, returned=sqrt(6)
```

### G6G-05 · major · 全仓同类扫描漏掉face_area和facet_gap3/support_gaps3的最终缩放前舍入，可表达非零面积/间隙被放大为两倍。

- 位置：`src/eab/kernel3d/geom3.py:215`。
- 具体输入 → 错误输出：u=2^-1074。三角[(0,0,0),(1,0,0),(1,(29/10)u,0)]精确面积29u/20<3u/2，正确显示u=5e-324；face_area先hypot舍入Newell为3u再/2，返回2u=1e-323。高度u时精确面积u/2按其fail-loud契约应报错，实际0。另A=B标准单位四面体，VF顶点0与face3 n=(1,1,1)，x=(1+(51/20)u,0,0)，精确gap=(51/20)/sqrt(3)u<3u/2；facet_gap3和support_gaps3同返回2u，正确u。
- 直接运行：`python -X utf8 review/repro/geom3_area_double_rounding.py`。[复现脚本](file:///D:/eab-wt/g6g/review/repro/geom3_area_double_rounding.py)。
- 建议修复（审查方未实施）：面积先精确形成norm²/4再最终开方；facet/support距离先精确形成signed numerator²/norm²，再统一最后开方并保符号。补最终缩放跨subnormal舍入中点的非对称格，不能仅测恰好tie。
- 同根位置：`src/eab/kernel3d/geom3.py:222`, `src/eab/kernel3d/covers3.py:768-772`, `src/eab/kernel3d/covers3.py:815-822`。

```text
{
  "exact_area_in_smallest_subnormal_units": "29/20",
  "expected_area": 5e-324,
  "reported_area": 1e-323,
  "ratio": 2.0
}
unrepresentable exact area=u/2, face_area= 0.0 (no exception)
CONFIRMED face_area rounds Newell norm before halving, doubles a representable area and silently underflows an unrepresentable one
facet_gap3 exact midpoint oracle: 5e-324 actual: 1e-323
support_gaps3 same supporting facet: 1e-323
CONFIRMED facet_gap3/support_gaps3 round numerator before normal-length division; same doubled representable final gap
```

### G6G-06 · major · margin_contacts仍从舍入后的全局EE见证相减构造normal，正确非零距离的法向被清成None或转错方向。

- 位置：`src/eab/margin.py:142`。
- 具体输入 → 错误输出：所有输入面已显式三角化，两个凸屋脊盒仅z向间隙g=1e-9、全坐标平移T=1e8，唯一最近EE。独立slab与屋脊中点证明距离g、B->A法向(0,0,-1)；body_distance正确g，margin_contacts(delta=2g,tol=0)返回distance=g且exact_distance_squared=g²，但normal=None、point_a==point_b。再施精确3-4-5 y旋转，g=2e-8，期望(-.8,0,-.6)，实际(-.7071067811865475,0,-.7071067811865475)，最大分量错0.10710678118654748。
- 直接运行：`python -X utf8 review/repro/geom3_margin_normal_loss.py`。[复现脚本](file:///D:/eab-wt/g6g/review/repro/geom3_margin_normal_loss.py)。
- 建议修复（审查方未实施）：保留原始数据上的精确EE/VE/EV最近点相对向量或正确原盖法向来构造margin normal，不能反减全局float显示点；不要用4*rounding构造豁免绕过法向修复。补实际margin_contacts平移/旋转门，不仅核inflated_normal(E,x)。
- 同根位置：`src/eab/margin.py:265`, `src/eab/margin.py:445`。

```text
{
  "result": "CONFIRMED",
  "rows": [
    {
      "gap": "1/1000000000",
      "translation": "0",
      "rotation": "identity",
      "expected_normal": [
        -0.0,
        -0.0,
        -1.0
      ],
      "reported_normal": [
        0.0,
        0.0,
        -1.0
      ],
      "reported_distance": 1e-09,
      "label": [
        "EE",
        [
          "edge",
          5,
          7
        ],
        [
          "edge",
          1,
          3
        ]
      ],
      "point_a": [
        0.0,
        0.0,
        1.0
      ],
      "point_b": [
        0.0,
        0.0,
        1.000000001
      ],
      "body_distance": 1e-09
    },
    {
      "gap": "1/1000000000",
      "translation": "100000000",
      "rotation": "identity",
      "expected_normal": [
        -0.0,
        -0.0,
        -1.0
      ],
      "reported_normal": null,
      "reported_distance": 1e-09,
      "label": [
        "EE",
        [
          "edge",
          5,
          7
        ],
        [
          "edge",
          1,
          3
        ]
      ],
      "point_a": [
        100000000.0,
        100000000.0,
        100000001.0
      ],
      "point_b": [
        100000000.0,
        100000000.0,
        100000001.0
      ],
      "body_distance": 1e-09
    },
    {
      "gap": "1/50000000",
      "translation": "100000000",
      "rotation": "exact_3_4_5",
      "expected_normal": [
        -0.8,
        -0.0,
        -0.6
      ],
      "reported_normal": [
        -0.7071067811865475,
        0.0,
        -0.7071067811865475
      ],
      "reported_distance": 2e-08,
      "label": [
        "EE",
        [
          "edge",
          5,
          7
        ],
        [
          "edge",
          1,
          3
        ]
      ],
      "point_a": [
        100000000.8,
        100000000.0,
        100000000.6
      ],
      "point_b": [
        100000000.80000001,
        100000000.0,
        100000000.60000001
      ],
      "body_distance": 2e-08
    }
  ],
  "rotated_normal_max_abs_error": 0.10710678118654748
}
CONFIRMED exact default margin distance remains correct but public normal is erased or directionally wrong by rounded global EE witnesses
```

### G6G-07 · major · Dual 幂的快路仅检查输入范围，不检查派生幂系数，先下溢再乘种子会静默抹掉可表示的导数。

- 位置：`src/eab/dual.py:106-131`。
- 具体输入 → 错误输出：x=2**200；Dual(x,(x,))**-5 的 primal=2**-1000 正确，但导数返回 -0.0；独立 Fraction 真值 -5*2**-1000=-4.666318092516094e-301，所有输入和最终输出均有限、可表示。876 个满足可表示条件的指数格中发现13个静默错，另14个响亮拒绝不计作静默错。
- 直接运行：`python -X utf8 review/repro/root_power_range.py`。[复现脚本](file:///D:/eab-wt/g6g/review/repro/root_power_range.py)。
- 建议修复（审查方未实施）：按派生指数和种子乘积的范围选择快路，或对整数幂用精确有理导数后最终舍入；非整数使用保留指数的构造。补输入仍在 _ordinary 框内而派生系数越界的门。
- oracle独立性：Fraction 二的整数/半整数幂闭式，不调用被测 Dual 或构造 helper。
- 分级依据：极端幂指数的窄范围算术错误，归 major；不是普通 primal 计算失效。

```text
{
  "checked": 876,
  "silent_wrong": 13,
  "loud_refusals": 14,
  "examples": [
    {
      "base_exp": 140,
      "seed_exp": 100,
      "p": "-7",
      "primal": 9.785978320356312e-296,
      "got_derivative": -0.0,
      "expected_derivative": -6.230206803820164e-307
    },
    {
      "base_exp": 140,
      "seed_exp": 200,
      "p": "-15/2",
      "primal": 8.289046e-317,
      "got_derivative": -0.0,
      "expected_derivative": -7.167464590104721e-298
    },
    {
      "base_exp": 140,
      "seed_exp": 200,
      "p": "-7",
      "primal": 9.785978320356312e-296,
      "got_derivative": -0.0,
      "expected_derivative": -7.897725394408629e-277
    },
    {
      "base_exp": 160,
      "seed_exp": 100,
      "p": "-6",
      "primal": 1.0261342003245941e-289,
      "got_derivative": -0.0,
      "expected_derivative": -5.340177260417283e-307
    },
    {
      "base_exp": 160,
      "seed_exp": 200,
      "p": "-13/2",
      "primal": 8.487983164e-314,
      "got_derivative": -0.0,
      "expected_derivative": -6.066213520270923e-301
    },
    {
      "base_exp": 160,
      "seed_exp": 200,
      "p": "-6",
      "primal": 1.0261342003245941e-289,
      "got_derivative": -0.0,
      "expected_derivative": -6.769478909493111e-277
    },
    {
      "base_exp": 180,
      "seed_exp": 100,
      "p": "-11/2",
      "primal": 9.556619453472961e-299,
      "got_derivative": -0.0,
      "expected_derivative": -4.35e-322
    },
    {
      "base_exp": 180,
      "seed_exp": 100,
      "p": "-5",
      "primal": 1.1830521861667747e-271,
      "got_derivative": -0.0,
      "expected_derivative": -4.892989160178156e-295
    }
  ],
  "minimal": {
    "x": 1.6069380442589903e+60,
    "p": -5,
    "seed": 1.6069380442589903e+60,
    "got_primal": 9.332636185032189e-302,
    "got_derivative": -0.0,
    "expected_derivative": -4.666318092516094e-301,
    "expected_hex": "-0x1.4000000000000p-998"
  }
}
```

### G6G-08 · major · Polyhedron.volume/centroid 的浮点叉积中间下溢破坏体积、体心，甚至使循环重排同一面环改变答案。

- 位置：`src/eab/kernel3d/geom3.py:329-356`。
- 具体输入 → 错误输出：全 binary64、闭合平面外向面盒，半宽 x=y=2**-600，半高 z=2**600。区间积分真体积1.9279358920823073e-180、体心(0,0,0)；返回体积1.2852905947215381e-180（2/3）和(-2**-600,-2**-600,-2**598)。同尺度四面体真体积4.0165331085048066e-182；面环(1,2,3)返回0，循环改为(2,3,1)返回真值。
- 直接运行：`python -X utf8 review/repro/root_polyhedron_mass_range.py`。[复现脚本](file:///D:/eab-wt/g6g/review/repro/root_polyhedron_mass_range.py)。
- 建议修复（审查方未实施）：以精确相对三重积及一阶矩累计，最后才构造浮点体积和体心；或使用经证实保守的缩放快路并保留精确兜底，不能让中间零触发零体积体心替代。
- oracle独立性：盒区间乘积和对称中心、四面体坐标积/6，未使用生产叉积、三角化或质量函数。
- 分级依据：混合极端尺度的有效输入窄域；独立构造 API 错误，不声称默认成员谓词同错。

```text
{
  "box": {
    "half_width_x": 2.409919865102884e-181,
    "half_width_y": 2.409919865102884e-181,
    "half_height": 4.149515568880993e+180,
    "got_volume": 1.2852905947215381e-180,
    "expected_volume": 1.9279358920823073e-180,
    "ratio": 0.6666666666666666,
    "got_centroid": [
      -2.409919865102884e-181,
      -2.409919865102884e-181,
      -1.0373788922202482e+180
    ],
    "expected_centroid": [
      0.0,
      0.0,
      0.0
    ]
  }
}
{
  "tetra": {
    "expected_volume": 4.0165331085048066e-182,
    "original_face_ring_volume": 0.0,
    "cyclically_shifted_face_ring_volume": 4.0165331085048066e-182
  }
}
CONFIRMED valid finite planar-face geometry: intermediate range loss changes volume and centroid
```

### G6G-09 · major · 六轴只证内部不交，不能推出理论正本01所定义的闭集完全分离PD≤w：恰好贴合的封闭空腔是反例。

- 位置：`docs/exact_3d_design.md:116`。
- 具体输入 → 错误输出：二进制可精确表示float输入：A为half=1/2方块，中心(-1/8,0,0)；B为half=2外方块减half=1/2开空腔，内表面反向；w=1/8。原严格贯入，+x移w后恰合空腔而无内部重叠，window公开状态ON_BOUNDARY。完全分离只能把A移出外方块，独立区间证明闭集PD=19/8，明显大于w。
- 直接运行：`python -X utf8 review/repro/docs_tight_cavity_pd.py`。[复现脚本](file:///D:/eab-wt/g6g/review/repro/docs_tight_cavity_pd.py)。
- 建议修复（审查方未实施）：明确区分PD_closed=inf{norm(t):(A+t)交B为空}与最短非贯入平移rho=inf{norm(t):int(A+t)交intB为空}。六轴保证只写rho≤w；若坚持01的PD承诺，应接受闭集完全分离证书而非仅state!=1，并提供零净间隙夹持/空腔门。同步README、两设计文档、canon及PERF报告相关命题和测试名，薄壳政策不需冒称PD。

```text
{
  "A_center": [
    "-1/8",
    "0",
    "0"
  ],
  "A_half": "1/2",
  "B_outer_half": "2",
  "B_open_cavity_half": "1/2",
  "contact_window": "1/8",
  "initial_overlap": 1,
  "after_plus_x_window_state": 0,
  "default_distance": [
    0.0,
    [
      "PENETRATING"
    ]
  ],
  "window_distance": [
    0.0,
    [
      "VF",
      [
        "vertex",
        1
      ],
      [
        "face",
        6
      ]
    ]
  ],
  "default_inflated_state": 1,
  "window_inflated_state": 0,
  "closed_set_PD_independent": "19/8",
  "strictly_disjoint_cavity_fit_possible": false,
  "int_disjoint_escape_distance": "1/8",
  "claim_refuted": "six-axis int-disjoint certificate does not imply 01 closed-set PD <= w",
  "theory01_closed_set_PD_definition": [
    34,
    "(ii) 重叠时，最小分离平移（穿透深度）PD = inf{|x| : (A+x)∩B = ∅} = d(a₀, E^c) = **d(a₀, ∂E)**（a₀ ∈ int E 时）。由命题 1 直接推出。"
  ],
  "reviewed_six_axis_PD_claim": [
    116,
    "- 六轴分支：存在 `d ∈ {±w e_x, ±w e_y, ±w e_z}`，`int(A+d) ∩ int(B)=∅`，因而 `PD ≤ ||d||₂ = w`。对原本分离输入另由真实距离平方 `d² ≤ w²` 接受；这不是贯入分支的结论。"
  ]
}
```

### G6G-10 · minor · 当前文档仍将 GAP3 同时写为开放和已处置，README 还把已替换的 polygons_overlap 写成当前非凸 G0 oracle。

- 位置：`docs/canon_map.md:19`。
- 具体输入 → 错误输出：阅读 canon_map:19 与 :23 得到互斥复审状态；README:102 的旧 oracle 描述与当前 g0.py 不符，禁用生产 polygons_overlap 后距离 G0 仍 passed/samples=1。
- 直接运行：`python -X utf8 review/repro/docs_residual_claims.py`。[复现脚本](file:///D:/eab-wt/g6g/review/repro/docs_residual_claims.py)。
- 建议修复（审查方未实施）：为 GAP3 旧状态句添加明确历史范围或统一现状；README 非凸 G0 改指 g0_oracle 独立有理分类/事件/距离。

```text
{
  "GAP3_open_claim": [
    19,
    "**状态更新（2026-10-10，G6 第五轮之后）**：本表的代码指针一律写成\"`file.py:当前定义行 函数名`\"，无名的行号 / 区间指针已全部改写（模块文档里的段落按节名指，不写行号），并由 `tests/test_doc_pointers.py` 逐条核\"行号 = 该函数当前的定义行\"——改代码挪了定义行，门就红在那个指针上，用 `tools/fix_canon_ptrs.py --apply` 重排。此前三次人工校正（第三轮后 34 处、第四轮又 13 处）都在之后的提交里再次过期（第五轮实核 40 处带名指针 29 处不在该行），这是建门的原因；下段\"HEAD 094861c / 1209 passed / 尚未经过 G6\"是 09-24 写表时的口径，此后 G6 第二轮（09-27，`reports/g6b_20260927.md`）与第三轮（10-10，`reports/g6c_20261010.md`）都读过本表；K4 行与附录 A.9 的 LP 契约数字按 HEAD 复跑订正（见各处 2026-10-10 注）。\"正本对代码\"（审查 GAP3）三轮都没有一路打开 `D:\\E(A, B)` 的三份正本核对——**仍开放**。"
  ],
  "GAP3_closed_claim": [
    23,
    "**本表自身的状态**：本文件与本批 M0 收尾文档**一起提交**（HEAD `094861c` 上尚不存在）；它此后经过 G6 第二至第五轮的独立重审（第四轮 provenance-canon 镜头打开过 01、03 全文与 00 多节，第五轮核过第八节\"07 对代码\"），GAP3（正本对代码）已按各轮报告逐条处置（`reports/g6d_20261010.md`、`reports/g6e_20261010.md`）。按 README 的规矩，本表里任何比现有 README/报告更强的说法，都要等 G6 之后才能升级到那些文件里。"
  ],
  "README_old_oracle_claim": [
    102,
    "| L1 二维 | G1 复现 legacy bb52 顶点-边 53/53 ✔（`test_bb52_g1.py::test_g1_tier1_all_legacy_ve_reproduced`）。**E2 凸路径（2026-10-11，已实现并配定向门，待 G6）**：只接受精确凸输入，允许平直顶点，微凹/折回/绕圈/零长边清晰拒收；仅精确平行同向边合并 FF。成员对给定坐标和精确平移判定；显式 `tol` 无舍入地板，凸报告带用精确欧氏边界距离，非凸回退用精确相交加保守四轴边界见证、报告带不保证完备（`test_kernel2d_exact.py`、`test_kernel2d_report_band.py`）。凸 G0 三票零容差、不跳样本，边界探针参与计分；票二对独立全顶点支撑集核对严格/边界标签，票三只数严格凸顶点（`test_kernel2d_g0.py::test_g0_random_convex_pairs`、`test_kernel2d_exact.py::test_g0_flat_chains_use_exact_support_sets_without_ambiguity_exemptions`）。**凹块 G0** 仍以暴力 `polygons_overlap` 检验距离/出口完备性，历史 bb52 1260 次平移为 603/603、657/657（`test_bb52_g1.py::test_g0_distance_completeness_real_concave_geometry` / `::test_g0_exit_completeness_real_concave_geometry`）；精确一般多边形相交回退已有闭式门，但**基于盖裁剪的凹块全局 E 仍未实现**（M3）。**E3 二维收尾（WO-E3E4，有定向门、待 G6）**：凸/凹首入初态与判定均对给定数据精确；凹 VE/EV 仿射根、各自时刻段内和前事件漏候选自校验在 Fraction 上完成，t_max 不被容差放宽。`tied_labels` 只报精确同时，接近项另报 `near_labels`；`shortest_exit` 精确比较在程负间隙的平方距离（局部最浅盖，不声称一般凹对全局最小分离；`test_kernel2d_entrance_e3.py`）。局部 VE/EV/VV 默认精确，显式长度/角度域窗口只放宽、不抬舍入地板，严格性与窗口活跃分开（`test_kernel2d_covers_e3.py`）；二维 `convex_hull` 返回精确极点，tol 不再隐式删点。bb52 的 53 条 legacy 窗口盖对账保留；运动首入门对精确微贯入另核局部出口，不把 FIT 内贯入当接触（`test_kernel2d_entrance.py::test_every_legacy_vertex_edge_contact_of_bb52_is_a_first_entrance_along_its_edge_normal`）。旧静态 `first_entrance_for_vertex` 仍不是一般凹块的运动首入。全套、突变、调用点分类见 `reports/codex/E3E4_report.md`，不等于 G6 退出 |"
  ],
  "g0_with_production_polygons_overlap_forbidden": {
    "passed": true,
    "samples": 1
  },
  "first_implementation_advice": [
    395,
    "| 07 第 33 行\"它既是 2015 理论的第一份实现\" | — | **措辞风险**：在 07 的上下文里指\"自家代码里第一份\"，单独引出去容易读成全局首次实现，越 00 §4.6 第三层红线（CGAL 早有非凸多面体 Minkowski 和的精确构造）；对外须限定为\"DDA 圈内 / 本课题组代码里第一份\" |"
  ],
  "prior_implementation_in_read_only_00": {
    "path": "D:\\E(A, B)\\00 石根华 E(A,B)·理论内核与向外发展分析.md",
    "line": [
      482,
      "- Zheng, F., Jiao, Y-Y. et al. (2016). Int. J. Geomech., 10.1061/(ASCE)GM.1943-5622.0000718. — 首个三维入口块实现"
    ]
  },
  "AGENTS_explicit_correction": [
    7,
    "> （该表标为\"首个三维入口块实现\"）、Feng & Tan 2020、Ni et al. 2020 等，都是更早或同期的实现"
  ]
}
```

### G6G-11 · minor · 将第一份实现限定成 DDA 圈内仍不成立，违背 AGENTS 订正及 00 自己列出的早期入口块实现。

- 位置：`docs/canon_map.md:395`。
- 具体输入 → 错误输出：按 canon_map 第八节措辞建议对外声称 DDA 圈内第一份，而只读理论正本 00:482 已把 Zheng/Jiao 2016 标为首个三维入口块实现，AGENTS:7 明言更早或同期实现。
- 直接运行：`python -X utf8 review/repro/docs_residual_claims.py`。[复现脚本](file:///D:/eab-wt/g6g/review/repro/docs_residual_claims.py)。
- 建议修复（审查方未实施）：删除 DDA 圈内选项，只保留本课题组/姊妹三线独立 oracle，不能把实现成熟度当学术优先性。

```text
{
  "GAP3_open_claim": [
    19,
    "**状态更新（2026-10-10，G6 第五轮之后）**：本表的代码指针一律写成\"`file.py:当前定义行 函数名`\"，无名的行号 / 区间指针已全部改写（模块文档里的段落按节名指，不写行号），并由 `tests/test_doc_pointers.py` 逐条核\"行号 = 该函数当前的定义行\"——改代码挪了定义行，门就红在那个指针上，用 `tools/fix_canon_ptrs.py --apply` 重排。此前三次人工校正（第三轮后 34 处、第四轮又 13 处）都在之后的提交里再次过期（第五轮实核 40 处带名指针 29 处不在该行），这是建门的原因；下段\"HEAD 094861c / 1209 passed / 尚未经过 G6\"是 09-24 写表时的口径，此后 G6 第二轮（09-27，`reports/g6b_20260927.md`）与第三轮（10-10，`reports/g6c_20261010.md`）都读过本表；K4 行与附录 A.9 的 LP 契约数字按 HEAD 复跑订正（见各处 2026-10-10 注）。\"正本对代码\"（审查 GAP3）三轮都没有一路打开 `D:\\E(A, B)` 的三份正本核对——**仍开放**。"
  ],
  "GAP3_closed_claim": [
    23,
    "**本表自身的状态**：本文件与本批 M0 收尾文档**一起提交**（HEAD `094861c` 上尚不存在）；它此后经过 G6 第二至第五轮的独立重审（第四轮 provenance-canon 镜头打开过 01、03 全文与 00 多节，第五轮核过第八节\"07 对代码\"），GAP3（正本对代码）已按各轮报告逐条处置（`reports/g6d_20261010.md`、`reports/g6e_20261010.md`）。按 README 的规矩，本表里任何比现有 README/报告更强的说法，都要等 G6 之后才能升级到那些文件里。"
  ],
  "README_old_oracle_claim": [
    102,
    "| L1 二维 | G1 复现 legacy bb52 顶点-边 53/53 ✔（`test_bb52_g1.py::test_g1_tier1_all_legacy_ve_reproduced`）。**E2 凸路径（2026-10-11，已实现并配定向门，待 G6）**：只接受精确凸输入，允许平直顶点，微凹/折回/绕圈/零长边清晰拒收；仅精确平行同向边合并 FF。成员对给定坐标和精确平移判定；显式 `tol` 无舍入地板，凸报告带用精确欧氏边界距离，非凸回退用精确相交加保守四轴边界见证、报告带不保证完备（`test_kernel2d_exact.py`、`test_kernel2d_report_band.py`）。凸 G0 三票零容差、不跳样本，边界探针参与计分；票二对独立全顶点支撑集核对严格/边界标签，票三只数严格凸顶点（`test_kernel2d_g0.py::test_g0_random_convex_pairs`、`test_kernel2d_exact.py::test_g0_flat_chains_use_exact_support_sets_without_ambiguity_exemptions`）。**凹块 G0** 仍以暴力 `polygons_overlap` 检验距离/出口完备性，历史 bb52 1260 次平移为 603/603、657/657（`test_bb52_g1.py::test_g0_distance_completeness_real_concave_geometry` / `::test_g0_exit_completeness_real_concave_geometry`）；精确一般多边形相交回退已有闭式门，但**基于盖裁剪的凹块全局 E 仍未实现**（M3）。**E3 二维收尾（WO-E3E4，有定向门、待 G6）**：凸/凹首入初态与判定均对给定数据精确；凹 VE/EV 仿射根、各自时刻段内和前事件漏候选自校验在 Fraction 上完成，t_max 不被容差放宽。`tied_labels` 只报精确同时，接近项另报 `near_labels`；`shortest_exit` 精确比较在程负间隙的平方距离（局部最浅盖，不声称一般凹对全局最小分离；`test_kernel2d_entrance_e3.py`）。局部 VE/EV/VV 默认精确，显式长度/角度域窗口只放宽、不抬舍入地板，严格性与窗口活跃分开（`test_kernel2d_covers_e3.py`）；二维 `convex_hull` 返回精确极点，tol 不再隐式删点。bb52 的 53 条 legacy 窗口盖对账保留；运动首入门对精确微贯入另核局部出口，不把 FIT 内贯入当接触（`test_kernel2d_entrance.py::test_every_legacy_vertex_edge_contact_of_bb52_is_a_first_entrance_along_its_edge_normal`）。旧静态 `first_entrance_for_vertex` 仍不是一般凹块的运动首入。全套、突变、调用点分类见 `reports/codex/E3E4_report.md`，不等于 G6 退出 |"
  ],
  "g0_with_production_polygons_overlap_forbidden": {
    "passed": true,
    "samples": 1
  },
  "first_implementation_advice": [
    395,
    "| 07 第 33 行\"它既是 2015 理论的第一份实现\" | — | **措辞风险**：在 07 的上下文里指\"自家代码里第一份\"，单独引出去容易读成全局首次实现，越 00 §4.6 第三层红线（CGAL 早有非凸多面体 Minkowski 和的精确构造）；对外须限定为\"DDA 圈内 / 本课题组代码里第一份\" |"
  ],
  "prior_implementation_in_read_only_00": {
    "path": "D:\\E(A, B)\\00 石根华 E(A,B)·理论内核与向外发展分析.md",
    "line": [
      482,
      "- Zheng, F., Jiao, Y-Y. et al. (2016). Int. J. Geomech., 10.1061/(ASCE)GM.1943-5622.0000718. — 首个三维入口块实现"
    ]
  },
  "AGENTS_explicit_correction": [
    7,
    "> （该表标为\"首个三维入口块实现\"）、Feng & Tan 2020、Ni et al. 2020 等，都是更早或同期的实现"
  ]
}
```

## 1. 审查契约与证据边界

- 对象：新鲜 detached 工作树 `d44dd78e84fa0434860f52ca1a76306ddc498c48`。不修代码、不进行 git 写操作。
- 本树 tracked 文件以审查起点的逐文件 SHA-256 为回滚/完整性锚。全部新脚本、日志、变异副本只在 `review/`；外部工作树、姊妹与理论正本只读。
- 成功标准不是实现方或测试全绿，而是确认后 **0 critical / 0 major**。每条最终发现均有独立输入真值，且由总审查方再次运行复现脚本。
- 用户命令里的 `<g6f 内 tmp>` 与 g6f 只读约束冲突，故 basetemp 设本树 `review/tmp_full_suite`，其他参数保持。没有在 g6f 写临时文件。
- 分级：本轮数值反例集中在极端/混合尺度或特殊表面、主 oracle/门缺口；按工单的窄域错误和无牙门归 major。没有把所有静默错误一律扩大成全生产域 critical，也没有因默认成员在若干反例正确而降为 minor。

## 2. 第六轮 12 条原输入回归重放

“已修”仅指旧案具体输入不再出现原症状，**不是同类根因已全仓消除**。原脚本断言的是旧错误，修复后 AssertionError / StopIteration 是预期；已加逐格新期望的正向复跑，避免原脚本早停掩盖其他格。

| G6F | 当前原输入输出摘要 | 状态 | 当前期望复跑证据 |
|---|---|---|---|
|01 可变凸视图缓存|返回视图不等于源对象；修改返回视图后源点态仍1，新等价源亦1|已修|[3D逐格输出](file:///D:/eab-wt/g6g/review/logs/root_confirm_g6f_geom3_postfix.log)|
|02 源面提示污染凸 hull|反向提示未保留；origin点态1，凸重叠1，E成员1|已修|同上|
|03 微凹性噪声带|原有理两格及 binary64 微凹格均 `is_convex=False`，reflex `(3,8)`|已修|同上|
|04 G0 微样本跳过/门无牙|2D 距离及出口删盖均 samples1/passedFalse；3D samples1/skipped0/passedFalse|已修|[二维/三维逐格](file:///D:/eab-wt/g6g/review/logs/g6g_g6f_geom2_replay.log)|
|05 极小距离/首出口 oracle|首出口 `1/549755813888`；距离 `1.204959932551442e-181`，均等真值|已修|同上；新瞬时反角出口另案|
|06 signed gap 先平方下溢|VE gap `-1.204959932551442e-181`，法向(1,0)|已修|同上；VV 同类漏网另案|
|07 Dual atan2/除法极端尺度|atan2 三尺度导数一致；大比值消去导数为1|已修|[Dual/LP逐格](file:///D:/eab-wt/g6g/review/logs/root_g6f_dual_lp_replay.log)|
|08 全局点先舍入再相减|原 VF 的 T=0/1000/1e8 距离1e-9、法向(-1,0,0)均正确|已修|[3D逐格](file:///D:/eab-wt/g6g/review/logs/root_confirm_g6f_geom3_postfix.log)；EE normal另案|
|09 offset浮点零混入精确逃逸|整数零/浮点零均 exact_height `7/4000000000`|已修|同上|
|10 margin精确差点文档|旧句已消失；当前差点 `19999999999999989/2`，未用提前舍入差点|已修|[等价实跑](file:///D:/eab-wt/g6g/review/logs/root_g6f10_replay.log)|
|11 Dual零次幂|零/非零底均 value1、全部导数0|已修|[Dual/LP逐格](file:///D:/eab-wt/g6g/review/logs/root_g6f_dual_lp_replay.log)|
|12 空约束LP精确见证|min/max均 optimal，exact_x=(0,0)、exact_y=()；浮点视图一致|已修|同上|

原脚本副本、原失败输出、正向补充均保留在 review。机读：[二维回归](file:///D:/eab-wt/g6g/review/notes/g6f_geom2_replay.json)、[三维回归](file:///D:/eab-wt/g6g/review/notes/geom3_g6f_afterfix.json)。

## 3. 同类漏网扫描与新代码细审

### 3.1 五类根因

|第六轮根因|本轮结论|
|---|---|
|可变缓存 / 别名|凸视图、表面视图已变为 immutable payload + fresh mutable view；二维完整内容键与 immutable返回检查未找到新 confirmed 串用。不将此提升为任意恶意可变/非法对象的全称证明。|
|隐式噪声带 / 浮点 oracle|默认精确成员与新独立oracle消除了旧微尺度跳格；但二维 ray_exit 漏掉反角的孤立边界事件，G0 验收尺度上溢也会全漏盖仍绿。|
|构造量先舍入再相减/运算|原VF已修，EE margin normal仍减舍入后的全局见证；VV gap/unit、area/facet gap 双舍入、volume/centroid中间范围损失另有反例。|
|Dual极端算术|atan2、比值与零次幂原例已修；幂的“ordinary输入”不保证派生系数ordinary，静默导数零仍可发生。|
|LP精确见证缺口|空约束 exact_x/y 已补。独立顶点 oracle、强制精确路径及多类错误候选注入未发现新的确认见证漏洞；不冒称任意规模LP穷尽。|

### 3.2 `2f6c518..HEAD -- src tests`

共 **35文件，2061插入/533删除，17个src文件、18个tests文件**。保存逐 hunk 差异，不只依据提交说明。分项阅读/核验责任如下：

|改变文件|审查要点及结论|
|---|---|
|construction.py / dual.py|有理sqrt与单位向量最终构造；Dual整数/非整数极端慢路及普通快路。幂快路发现新错；没有修实现。|
|kernel2d/covers.py / entrance.py / geom.py|精确相对gap、仿射平移、tiny norm/overlap内点重写；VV剩余构造错。|
|kernel2d/g0.py / 新g0_oracle.py|移除跳样、换独立整数oracle；G0新两项无牙/错oracle反例。|
|kernel3d/covers3.py / geom3.py|exact payload视图、相对距离、normal/gap构造；source边与三角内部边差异导致brute错距；双舍入、质量构造另错。|
|kernel3d/exact_geom.py / exact_sweep.py / interlock.py|精确相对平方距离、浮点offset有理化、事件与表面路径；旧offset和微凹例已修。|
|kernel3d/frozen.py|VV/EE精确相对量与Dual导数保留、新门的独立差分对象；定向与全套执行，未确认新导数错。|
|kernel3d/g03.py / 新g03_surface_oracle.py|非凸G0改独立有理表面oracle；独立性与三角插值输入模型核；不是brute_feature_distance换名。|
|lp.py|空约束最优的exact_x/y；min/max原例及原始LP精确层回放通过。|
|margin.py|surface view别名修复、exact_d2替代浮点距离、VF构造修复；EE法向未同样修。六轴“非贯入⇒PD”命名/声称仍不成立。|
|e5a_escape_oracle.py / e5a_g2_oracle.py|独立相对法锥和角度判据，不以生产norm当真值；escape共享对照仅佐证。|
|test_bb52_g1.py / test_invariance_2d.py|区分精确仿射与逐点float数据；旧缺盖牙仍有真实删盖红格，而非简单删断言。|
|test_e5a2_covers.py / test_e5a2_integer_arithmetic.py / test_geom3_e5a.py|微反角、signed numerator变异、独立平面/法锥。目标断言仍检查对应语义。|
|test_invariance_interlock.py / test_kernel2d_entrance.py / test_kernel2d_review.py|补浮点offset、精确根及候选控制，不强迫圆整后的另一份数据保持理想边界。|
|test_margin.py / test_margin_exact.py|精确相对见证断言；现有门未覆盖EE法向失分辨率的新反例。|
|六个test_r6fix_*文件|construction、dual_lp、frozen_construction、g0、g2_oracle、geom3 的原12条专门门；原输入通过，但极端VV/幂派生量/反角事件等新增格未包含。|

没有确认由本次 diff 直接把原门弱化成全无牙的缺陷；**有确认新oracle自身不正确和全仓扫描遗漏**。全部旧门迁移逐函数清单已抽取，不等于113个旧函数每一条新断言都做过独立变异。

## 4. 九个镜头的覆盖、证据与边界

### 镜头1：精确性声称 vs 代码

全 `src/eab` 33个Python文件枚举；AST扫描得到312个相关 If/Compare 条目（含重复语法节点，不是312个独立噪声带）。[分支清单](file:///D:/eab-wt/g6g/review/notes/whole_src_branches.json)；[二维逐函数分类](file:///D:/eab-wt/g6g/review/notes/geom2_coverage.md)；[三维分类](file:///D:/eab-wt/g6g/review/notes/geom3_coverage.md)。

- 二维 tol/cone_tol/window/t_max 为显式域或报告带，truth在Fraction里判；orient2d不确定时精确兜底。历史eff_tol等未接答案路径，不能据名字当缺陷。
- 三维显式长度/角域窗口与薄壳/六轴政策允许改变contact classification，但其承诺必须正确；本轮PD文字不正确。部分旧几何diagnostic helper仍为浮点，不能统称“全src任何输出精确”。
- LP FEAS/PIV/噪声阈值只用于浮点候选；原始数据的有理证书和有理单纯形兜底实际存在，错误候选注入可验证。limit 的风险窗口属于resolvability报告，不应替代exact状态/alpha。
- Dual `_ordinary`是速度选择而非择支真值，但幂快路错误说明“有慢路”不代表所有危险输入能进入它。
- `readers/bdda_geom.py` 的去重/整形地板是**声明的legacy输入归一化政策**，不是canonical exact geometry。dup_tol=0也不承诺保留所有不同点；原始p1/p2保存在记录extra。记录此例外，不把全仓所有阈值写成只有显式窗口。

### 镜头2：过滤/缓存等价性

新增独立搜索：1500 rational3 dot/cross对、4000混合精确/浮点二维filter对、1500 orient3d排列行列式，均一致。[过滤输出](file:///D:/eab-wt/g6g/review/logs/root_extra_scan_fixed.log)。覆盖次正规、巨大有限量、混合尺度与误差候选非有限情况；不是浮点全位模式穷举。

完整坐标/面环键、fresh-view cache隔离与旧篡改回归均核；未确认新cache串用。构造快路不完全等价的反例见本轮Dual、VV、area/gap、volume、EE法向，不能被predicate过滤通过替代。

### 镜头3：oracle独立性

二维新g0_oracle不import生产geom/covers；三维新g03_surface_oracle自写整数平面/winding/射线与段-面/段-段，不调用生产exact_geom/predicates。共享“源面确定性三角插值”模型定义是契约，不是共享被测几何helper。凸三票采用独立内联SAT、全顶点支撑、gift-wrap/极点核。

例外明确：brute_feature_distance共享exact_geom，escape_height_brute共享事件/谓词，first_entrance_brute共享production overlap——只当佐证，不能当主oracle。独立oracle仍可能错，二维反角首出口正是实例。本轮新反例真值使用独立区间积、Fraction闭式、中点平方界及拓扑扰动证明。

### 镜头4：测试迁移有没有变弱

历史diff `b6126cf..HEAD` 涉及96个tests文件、113个改变的旧函数、6个重命名；[逐函数旧/新断言清单](file:///D:/eab-wt/g6g/review/notes/gates_docs_inventory.json)。不能把6个重命名误算为删门。

隔离副本内部变异目标断言结果：二维共线内部重叠退为0→18红/81绿；boundary→inside→1红；保留非极点→1红；边弧边界→strict→1红；错误合并微平面→2红/3绿；取消extent→6红；公共extent设0→4红；弱化exact supporting证书→1红；VV active强置True→12红。LP风险屏关闭→4红，exact admissibility换宽带→3红/29绿。全部按原字节恢复并核SHA。

LP #47最初只跑multi两个节点，28绿，原因仍被另一精确条件拦住；加入真正看护负功率的节点后3个目标断言红。**不把一次局部不杀变异虚报为全门无牙**。二维reflex首出口删真实cone路径、全漏盖inf误差两项则确认仍绿，计本轮major。没有靠在产物后追加假数据造牙。

### 镜头5：几何压力与独立反例

审查方新Fraction耳分解/片裁剪面积/闭段相交、独立parity与三维区间积：二维290格（18分离/9相触/263贯入）、180精确内点、三维96距离格均对拍通过。包括凸/凹/平直链、近1e-15、T1e8、小1e-9、2^±600、3-4-5有理旋转与单位变化。[压力输出](file:///D:/eab-wt/g6g/review/logs/g6g_geometry_pressure.log)。120个额外rounded非凸格中10个已重复点塌缩，不强求非法non-simple输入；其余110按实际数据核，无边界skip。

压力PASS不排除针对性VV、质量、孤立出口、三角内棱、EE法向等错。一般非凸全局E/全局最小欧氏出口在M3未实现，本轮不把未承诺能力当静默错。

### 镜头6：接触窗口

默认精确路径与显式window政策分别核。六轴证书可证明存在长度w的**非贯入**位移，但不能对封闭恰-fit空腔保证闭集完全分离PD≤w。主反例全binary64，w=1/8而闭集PD=19/8。

正本01开头有凸前提；**本轮没有声称反驳凸理论**。问题是仓内一般闭表面实现/文档把非贯入证书外推成整体最短完全分离PD界。若所有者另定义PD_int为非贯入距离，则算法政策可成立，但当前必须明示口径与01不同。

薄壳 star-core / 径向壳依据及既有box/双壁门审读，未确认新反例；没有独立穷举任意非星形实体的所有壳交区域，不能说该命题全域已证明。

### 镜头7：极限分析与LP

独立有理Gaussian顶点枚举：180个bounded LP对拍；8000个pricing候选对有理符号；强制纯有理路径与float候选路径答案一致，x/y浮点视图与exact_x/y一致。空约束min/max也核。[LP输出](file:///D:/eab-wt/g6g/review/logs/root_lp_audit_fixed.log)。

60个2D闭式承载比单/多体格（尺度2^±600、摩擦/倾倒分界、零摩擦、平移），180单体+180多体错误候选精确拒绝；真实limit_load调用内分别污染float alpha、exact alpha、exact_x、exact_y，4种均RuntimeError拒绝。[自校验输出](file:///D:/eab-wt/g6g/review/logs/root_limit_guard.log)。没有确认本轮LP见证漏洞；这是有限候选覆盖，不是任意维度/无界/不可行全部问题的形式证明。

### 镜头8：文档 / 正本

必读README、AGENTS、两份exact设计、canon、E2–PERF各报告、R6FIX、第五轮raw50条和g6f修复提交说明；只读正本00/01/03/07。69处✔/已完成/已验证/已实现/有门行抽查定位：显式具名测试missing0；不代表这些断言能证明每个声称全称正确。[69声称台账](file:///D:/eab-wt/g6g/review/notes/docs_claim_review.json)。

canon第八节“07对代码”378–395共18行逐行核；六表示/G1/G2/G4/Phase规模与缺口多数已诚实明示。G5、姊妹切换、MLCP、一般非凸全局E不冒称完成。仍有两项残留minor（GAP3/README旧oracle和DDA圈内第一份措辞），另有核心PD错误major。[逐行文档报告](file:///D:/eab-wt/g6g/review/notes/docs_review.md)。

未联网重查题录/学术优先性；minor是仓内正本及AGENTS自相矛盾，不把本轮只读题录当外部学术检索证据。没有重跑姊妹exe或验证远端当前状态。

### 镜头9：第五轮50条重放

已覆盖50个唯一ID：docs分项48条，加root的23/47内部等价变异。至少26个数值/门条目采用原输入或当前接口的等价数值复现，其余文档项读回现行语句/指针及专门门；**不是把50条都声称为50个独立数学数值oracle**。

详细逐条表在下节；必须保留口径限制：#34原噪声选根退休，现brute对拍共享事件只作症状消失；#36原round-band删除，float旋转新数据仍可能失去理想边界label，按实际数据核；#40提前float差点hull不是当前exact差点模型，NameError已消失，需精确差点等价复现；#9明确ValueError拒绝，脚本exit1是预期而非新漏洞。

## 5. 未确认、撤回与完整性批评

1. **撤回旧U形紧槽首出口候选**：该单时刻无实体内部交可能仍在Minkowski int E内部，不能用它否证“first exit from int E”；已改为L反角并用任意eps的NE严格分离证明真正∂E，最终计数只含后者。
2. 折面源 `is_convex` 与三角展开凸性不一致另有候选，但该诊断接口存在“平面源面”域限制，未证明符合接口输入合同，列未确认，不计数。
3. 非零准确量不可表示时响亮拒绝、浮点显示点自身塌缩、float旋转后一份新数据不再边界，都不直接算默认精确成员错判。EE normal缺失则有可表示的局部单位向量，不能用显示点塌缩豁免。
4. 未独立给113个改变旧函数逐一做变异；本轮重点语义门已有真实内部变异，余者为静态比较+全套执行。不能据69个test名字存在宣称所有文档全称命题成立。
5. 全33个src模块已清点和全仓条件扫描；重点及本次17个src变更按分项审读。未对所有未改的通用helper、readers格式错误路径、每个浮点统计函数做逐行形式证明；没有任何未读模块被用来支持“全部正确”的结论。
6. 三维g03_exact的深入独立oracle已有前轮依据，本轮检查调用/合同并回归，不对其全行重新建立数学证明。无新增对任意nonmanifold/self-intersecting非法实体的承诺。
7. 未读取全部大体积历史证据/夹具每一文件内容，未运行外部solver、未写姊妹或正本；原件provenance由当前全套门检查。无远端、生产部署或工程校准结论。
8. 有理证书验证强于有限随机对拍，但本轮没有对全部LP规模、所有thin-shell区域或任意近舍入中点构造作形式正确性证明。

具体未逐行重新精审项：`src/eab/kernel3d/g03_exact.py` 主要复核其独立性接口/合同及调用，未逐行重建原有全部三票证明；`src/eab/readers/*.py` 已读格式与归一化路径，但非法/截断格式的全部分支未逐格构造；未改的私有历史cone/诊断辅助只核调用隔离及数值口径，未作为主oracle证明。仓库tests全部执行，**并非全部全文逐行读取**；历史113个改写函数的未深审条目在逐函数清单中可定位，动态变异只覆盖本报告明确列出的节点。外部原始大夹具与历史reports除必读及针对性引用未全读，不把它们当确认当前正确性的证据。

本轮给出的不是“代码已正确”证明，而是**已确认反例、原案修复复跑、门的实质牙与诚实覆盖边界**。保留日志中的初次脚本输入/编码/复制依赖错误；它们经更正后才采纳最终exit0输出，未误计为实现缺陷。


## 6. G6E 50条逐条重放台账

原输入/等价数值复现、内部等价变异与文档读回须区分；下表是处置核查，不是50个全域数学证明。完整输出：[机读逐案台账](file:///D:/eab-wt/g6g/review/G6E_replay_ledger.json)。

|旧ID|当前状态/限制|脚本|
|---|---|---|
|1|已修错误外部前提，读取器仍未实现|[docs_replay_extra.py](file:///D:/eab-wt/g6g/review/repro/docs_replay_extra.py)|
|2|已修（当前接口等价输入与精确断言；原失败未重现）|[gates_replay_g6e.py](file:///D:/eab-wt/g6g/review/repro/gates_replay_g6e.py)|
|3|已修（当前接口等价输入与精确断言；原失败未重现）|[gates_replay_g6e.py](file:///D:/eab-wt/g6g/review/repro/gates_replay_g6e.py)|
|4|已修描述并明确缺口|[docs_replay_extra.py](file:///D:/eab-wt/g6g/review/repro/docs_replay_extra.py)|
|5|已修凸 G0 跳样描述；全局双侧探针缺口显式保留|[docs_replay_extra.py](file:///D:/eab-wt/g6g/review/repro/docs_replay_extra.py)|
|6|主要矛盾已订正，独立复审状态残留小矛盾另列|[docs_replay_extra.py](file:///D:/eab-wt/g6g/review/repro/docs_replay_extra.py)|
|7|已修（原输入重放）|[solid_g6e_07.py](file:///D:/eab-wt/g6g/review/repro/solid_g6e_07.py)|
|8|旧噪声实现退休；当前同类内部变异被目标语义门捕获|[docs_more_mutations.py](file:///D:/eab-wt/g6g/review/repro/docs_more_mutations.py)|
|9|已修（原错误切向现显式 ValueError；exit 1 是预期拒绝）|[root_g6e_09.py](file:///D:/eab-wt/g6g/review/repro/root_g6e_09.py)|
|10|已补实质平拱门并纠正引用|[docs_replay_extra.py](file:///D:/eab-wt/g6g/review/repro/docs_replay_extra.py)|
|11|已修（原输入失真/错候选现被拒或正确分类）|[root_g6e_11.py](file:///D:/eab-wt/g6g/review/repro/root_g6e_11.py)|
|12|范围/版本已限定为历史，不当作当前全套|[docs_replay_extra.py](file:///D:/eab-wt/g6g/review/repro/docs_replay_extra.py)|
|13|范围/版本已限定为历史，不当作当前全套|[docs_replay_extra.py](file:///D:/eab-wt/g6g/review/repro/docs_replay_extra.py)|
|14|用按定义行执行门替代过期指针|[docs_replay_extra.py](file:///D:/eab-wt/g6g/review/repro/docs_replay_extra.py)|
|15|报告处置列已补订正|[docs_replay_extra.py](file:///D:/eab-wt/g6g/review/repro/docs_replay_extra.py)|
|16|主要矛盾已订正，独立复审状态残留小矛盾另列|[docs_replay_extra.py](file:///D:/eab-wt/g6g/review/repro/docs_replay_extra.py)|
|17|已修描述并明确缺口|[docs_replay_extra.py](file:///D:/eab-wt/g6g/review/repro/docs_replay_extra.py)|
|18|已修描述并明确缺口|[docs_replay_extra.py](file:///D:/eab-wt/g6g/review/repro/docs_replay_extra.py)|
|19|已修现有48条条目；没有再次重跑姊妹exe|[docs_replay_extra.py](file:///D:/eab-wt/g6g/review/repro/docs_replay_extra.py)|
|20|已修（原输入失真/错候选现被拒或正确分类）|[root_g6e_20.py](file:///D:/eab-wt/g6g/review/repro/root_g6e_20.py)|
|21|已修（原输入失真/错候选现被拒或正确分类）|[root_g6e_21.py](file:///D:/eab-wt/g6g/review/repro/root_g6e_21.py)|
|22|已修（原输入失真/错候选现被拒或正确分类）|[root_g6e_22.py](file:///D:/eab-wt/g6g/review/repro/root_g6e_22.py)|
|23|已修：真实风险屏关闭变异4个目标断言红，原字节SHA已恢复|[root_lp_gate_mutations.py](file:///D:/eab-wt/g6g/review/repro/root_lp_gate_mutations.py)|
|24|已修（原输入重放）|[solid_g6e_24.py](file:///D:/eab-wt/g6g/review/repro/solid_g6e_24.py)|
|25|已修（原输入重放）|[solid_g6e_25.py](file:///D:/eab-wt/g6g/review/repro/solid_g6e_25.py)|
|26|已修（当前接口等价输入与精确断言；原失败未重现）|[gates_replay_g6e.py](file:///D:/eab-wt/g6g/review/repro/gates_replay_g6e.py)|
|27|已修（当前接口等价输入与精确断言；原失败未重现）|[gates_replay_g6e.py](file:///D:/eab-wt/g6g/review/repro/gates_replay_g6e.py)|
|28|已修（原输入重放）|[solid_g6e_28.py](file:///D:/eab-wt/g6g/review/repro/solid_g6e_28.py)|
|29|已修（原输入重放）|[solid_g6e_29.py](file:///D:/eab-wt/g6g/review/repro/solid_g6e_29.py)|
|30|已修（当前接口等价输入与精确断言；原失败未重现）|[gates_replay_g6e.py](file:///D:/eab-wt/g6g/review/repro/gates_replay_g6e.py)|
|31|已修（原输入重放）|[solid_g6e_31.py](file:///D:/eab-wt/g6g/review/repro/solid_g6e_31.py)|
|32|用按定义行执行门替代过期指针|[docs_replay_extra.py](file:///D:/eab-wt/g6g/review/repro/docs_replay_extra.py)|
|33|已修现有48条条目；没有再次重跑姊妹exe|[docs_replay_extra.py](file:///D:/eab-wt/g6g/review/repro/docs_replay_extra.py)|
|34|原噪声选根已退休；原输入现与共享事件 brute 一致，不算独立最早根证明|[solid_g6e_34.py](file:///D:/eab-wt/g6g/review/repro/solid_g6e_34.py)|
|35|旧噪声实现退休；当前同类内部变异被目标语义门捕获|[docs_more_mutations.py](file:///D:/eab-wt/g6g/review/repro/docs_more_mutations.py)|
|36|原参数带缺陷已删除；逐数据精确门通过，边界标签不承诺浮点旋转完全不变|[docs_g6e_36.py](file:///D:/eab-wt/g6g/review/repro/docs_g6e_36.py)|
|37|已修（原输入重放）|[solid_g6e_37.py](file:///D:/eab-wt/g6g/review/repro/solid_g6e_37.py)|
|38|已修（当前接口等价输入与精确断言；原失败未重现）|[gates_replay_g6e.py](file:///D:/eab-wt/g6g/review/repro/gates_replay_g6e.py)|
|39|已修（当前接口等价输入与精确断言；原失败未重现）|[gates_replay_g6e.py](file:///D:/eab-wt/g6g/review/repro/gates_replay_g6e.py)|
|40|NameError 已修；原浮点差点 hull 与 exact E 是不同模型，需精确差点等价复现|[solid_g6e_40.py](file:///D:/eab-wt/g6g/review/repro/solid_g6e_40.py)|
|41|已修（当前接口等价输入与精确断言；原失败未重现）|[gates_replay_g6e.py](file:///D:/eab-wt/g6g/review/repro/gates_replay_g6e.py)|
|42|已修（原输入重放）|[solid_g6e_42.py](file:///D:/eab-wt/g6g/review/repro/solid_g6e_42.py)|
|43|已修（原输入重放）|[solid_g6e_43.py](file:///D:/eab-wt/g6g/review/repro/solid_g6e_43.py)|
|44|已修（原输入重放）|[solid_g6e_44.py](file:///D:/eab-wt/g6g/review/repro/solid_g6e_44.py)|
|45|已修（原输入失真/错候选现被拒或正确分类）|[root_g6e_45.py](file:///D:/eab-wt/g6g/review/repro/root_g6e_45.py)|
|46|旧噪声实现退休；当前同类内部变异被目标语义门捕获|[docs_more_mutations.py](file:///D:/eab-wt/g6g/review/repro/docs_more_mutations.py)|
|47|已修：exact负功率换宽带，目标门3红/29绿，原字节SHA已恢复|[root_lp_gate_mutations.py](file:///D:/eab-wt/g6g/review/repro/root_lp_gate_mutations.py)|
|48|已修：旧0.5台阶门仍保留，新增1e-12和2^-80微台阶杀真实容差回退|[gates_docs_mutations.py](file:///D:/eab-wt/g6g/review/repro/gates_docs_mutations.py)|
|49|旧噪声实现退休；当前同类内部变异被目标语义门捕获|[docs_more_mutations.py](file:///D:/eab-wt/g6g/review/repro/docs_more_mutations.py)|
|50|原三种带宽已退休；当前多报极点必须红且不能豁免|[docs_g6e50.py](file:///D:/eab-wt/g6g/review/repro/docs_g6e50.py)|

## 7. 交付与复跑

- [最终机读发现](file:///D:/eab-wt/g6g/review/G6G_findings.json)；[产物索引](file:///D:/eab-wt/g6g/review/ARTIFACT_INDEX.md)；[tracked完整性及脚本哈希](file:///D:/eab-wt/g6g/review/verification_integrity.json)。
- [全部确认发现复跑入口](file:///D:/eab-wt/g6g/review/repro/replay_confirmed.py)：`python -X utf8 review/repro/replay_confirmed.py`。
- 最终聚合实跑：[10个唯一脚本全部复现成功](file:///D:/eab-wt/g6g/review/logs/final_confirmed_replay.log)，reproduction_failures=[]。
- 全套可用同一pytest命令重跑，注意删除/重写同一review日志不是修复；实现修复后应另做正确期望门，而非保留本轮“错误复现必须成功”的断言。

G6G_DONE critical=0 major=9 minor=2
