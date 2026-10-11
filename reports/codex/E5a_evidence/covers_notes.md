# WO-E5a 盖分支子任务证据

## 已实施
- `covers3.py` 的顶点锥、棱弧凸性/方向/严格性、VF/FV 投影、EE 与 VE/EV 参数及在程判断，均以原始坐标的有理派生量判定；不再加入几何噪声地板。
- `closest_point_of_convex_hull_to_origin` 改为精确完全校正最小范数迭代，每次至多四点单形；精确 KKT 核验全部点后返回。每步非最优迭代的有理平方距离严格下降，没有容差停机或迭代上限。
- VV3 锥交存在性直接读取有理最近点是否为零，不读取浮点距离，不用 `tol` 删薄锥。
- 显式凸 API 统一使用 `exact_convex_view`，标签解析与精确 `facet_plane3` 使用同一规范视图；E 平面基点 `b-a` 不先舍入。
- 有理坐标/面法向/局部模型缓存；缓存模型的键包含被测谓词函数身份，不掩盖 monkeypatch 变异。

## 第五轮 covers3.py:247
修前 `covers_before.json` 原屋脊四组顶点对均为 `margin=0`、锥交 `False`；额外一般位置单形把明确在外的原点吸为零。
修后 `covers_after.json` 四组锥交均为 `True`，独立 Gordan 极射线 oracle 同意；一般位置单形最近点为 `(1e-13,0,0)`。

## 验证与变异
- `test_covers3_e5a.py`：69 passed in 0.42s；其中 36 格最近点对独立有理 Gram 系统穷举，无被测几何原语共用。
- `test_covers3_strict_lowdim.py` + `test_near_parallel_edges.py` 原测试未改：114 passed in 19.83s（较早实现快照）。
- `test_covers3_membership.py` + `test_margin.py` + `test_margin_resolution.py` + `test_kernel3d_covers.py`：172 passed in 70.79s（最终全套由主代理重跑）。
- 三条源码内部变异均在独立复制目录执行：棱弧严格 `>` 改 `>=`，3 红；锥交退 `distance > 1e-12` 浮点阈值，4 红、4 绿（额外 `yaw=-2^-44` 四个真顶点被删）；单形恢复绝对重心阈值，2 红、1 绿。均检查到目标断言，不是运行/收集错误。详细 `covers_mutations.json` 与对应文本日志。
- `tests/e5a_cover_oracle.py` 独立完整枚举局部盖，面法向用坐标循环式、棱弧用 Gram 系数、EE 参数用 Gram 方程、VV 用极射线。11 个输入家族 × 3 个刚体/工程坐标格，label+strict 对拍零差；主代理将其用于完整不变性网格。
- 五条旧测试迁移逐条见 `covers_test_rewrites.json`；没有删测试、删输入、skip 或 xfail。移除的是理想旋转几何固定计数/允许歧义的旧断言，换为每格有理 oracle 全量计数；原距离/最近标签/膨胀成员断言保留。
- 裕度不变性门：385 passed, 2021 deselected in 89.84s。原 37 个理想标签假不变性红格，换为同输入完整独立盖枚举、见证构造与裕度选择 oracle；状态、哨兵、非空、距离及稳定标签距离缩放门保留。对 `margin_contacts` 内部循环删首见证的变异，目标集合断言准确报缺 VF 标签。
- 后续纯缓存优化：棱楔凸性与两半空间、原始棱向量缓存，单互锁枚举冷进程 cProfile 从 2.3828 s 降为 1.7282 s，均 31 个盖；源语义未改。新门加 kernel 牙共 72 passed in 1.82s。

## 精确口径与尚未完成
- 一般单盖/枚举仍解释原输入面环与 Newell 平面；非精确共面的一般面不等于其三角化实体表面。此处不能声称一般非平面表面全部精确化已完成；凸路径已显式换为精确顶点凸包。
- `tol>0` 的 `membership_convex3` 明确是支撑平面域带，不是欧氏 offset；有理平方比较且无隐含地板。零 `tol` 是精确成员定理。
- `cone_intersection_margin` 报告的是有理正比例归一（最大分量范数）的约束凸包距离，不再宣称单位球面角裕度。第二返回量仍仅为噪声报告，不能裁决。
- 外层距离搜索窗口目前比较浮点 `Cover3.gap`；窗口之外的几何/严格/在程分支不依赖该构造量。若工单把精确窗口边界也视为必须项，此项尚未迁移。
- 公共最近点向量是浮点构造，极端下溢可变成零；内部锥存在性不读取它，始终读取有理结果。
