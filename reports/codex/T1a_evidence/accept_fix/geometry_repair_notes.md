# WO-T1a 几何与图件返修证据（2026-10-19）

本页记录本轮自行生成的证据，不把验收 scratch 的结果作为本轮运行产物。

## 1. 合同与具名门

- `Body2.from_vertices`：非 `FIXED_BODY` 且掩码不是 `[1,1,1]` 时必须显式给 `dof_anchor`；包含非固定但三自由度均约束的边界描述。`test_partly_constrained_free_body_requires_explicit_dof_anchor` 覆盖五个掩码。
- `test_free_body_anchor_stays_fixed_when_reference_and_wrench_change_together`：自由体掩码 `[1,0,1]`、物理锚点 `(7,11)` 不动，代数参考点从 `(0,0)` 改为 `(13,-5)`，荷载力矩同步精确变换，实际法向矩阵与 LP 的 A/b/c 全部相同。
- `ContactPoint2.boundaries` 保存完整点自由锥边界，`retained` 另记是否进入解析法向约束。`test_maximal_collinear_segment_drops_interior_force_point_but_not_sources` 同时核平坦中点来源/边界仍在、只有两端点放力、单位法向下中点行是两端点行的平均；生产生成元不作归一化。
- `test_true_vv_retention_flag_does_not_conflate_unresolved_with_redundant`：`TRUE_VV` 和 `REDUNDANT_PROVED` 均不放力，但必须由 `fp_type` 及证书区分未解析与已证冗余。
- 一阶未解析结果保存真实三个 DOF，未算数组为 `None`，显示 `NOT_APPLICABLE`；`test_first_order_bare_corner_both_apis_remain_mechanical_unresolved`。
- 纯度门恢复内核模块精确计数 `47`；在实际源码中注入 `tia_block`、`TiaAssembly`、`differentiability_tia` 均被现有 AST 审计拒绝，未扩大白名单。

定向命令：

```text
python -X utf8 -m pytest -q -p no:cacheprovider --basetemp reports/codex/T1a_evidence/tmp/accept_geometry_02 tests/test_tia2d_assembly.py tests/test_tia2d_contacts.py tests/test_tia2d_mobility.py tests/test_tia2d_curvature.py tests/test_kernel_purity.py
```

原样最后一行：`117 passed in 14.17s`。TEMP/TMP 指向本单证据 tmp，禁写 bytecode。第一次定向运行的两项失败均是新增测试调用/行尺度错误，修正测试后重新完整执行，不拼接两次结果。

随后对最终几何源码再跑上述五文件并加入 `tests/test_tia2d_morphology.py`，使用全新 basetemp `accept_geometry_03`；原样最后一行：`121 passed, 39 deselected in 18.21s`。39 个慢档未在此定向快档执行，不冒充全档；完整分片由主线收尾运行负责。

## 2. 真圆格反例：全弧恒等式，而非采样点近似

对象为 TIA-G3-A3-W0 对应的真圆格：A = 1/4，λ = 1/2，半径 R = 1/4；四个圆心依次为 `(-3,R), (-1,R), (1,R), (3,R)`，两端体固定。

以下五体 twist 全部关于全局原点，用 `(vx,vy,ω)` 记：

```text
body 1: (0, 0, 0)
body 2: (R, 3, 1)
body 3: (0, 2, 0)
body 4: (-R, 3, -1)
body 5: (0, 0, 0)
```

各界面相对角速为 `(1,-1,-1,1)`。对圆心 c 与两侧 twist 差 `(a,b,w)`，任意点 p = (x,y) 的径向相对速度为

`(p−c)·((a,b)+w Jp) = (−cx a−cy b) + (a−w cy)x + (b+w cx)y`。

四界面的三个系数逐项精确为 0，故整条圆弧法向速度恒为 0；这不是在若干点抽样检查。圆弧端点的另一侧轮廓与水平外边相切，公共接触法向仍为竖直径向，不添额外端点半平面。

取所有 twist 的反向，中块下移速度 2，向下单位活载做功为 2。μ = 0 时法向力做功为 0，两端固定支座做功为 0，所以平衡要求 `2F = 0`；全零接触力与 F = 0 又精确可行。因此光滑模型该荷载的刚体极限为 0。这里仅是**一阶机构与静力功证书，不是 SE(2) 有限运动证书**。

### 独立重建与生产多边形对照

`tools/tia2d_curvature_probe.py` 用上式生成全弧恒等式，独立于 ContactSet2、胞排布、DD、LP。工具另用单位圆的有理参数式生成真圆的 2/4/8/16 弦内接多边形，每个界面只构造一次；这些有理顶点是 Python-only，不冒充 binary64 子集。

固定表 G3 与四个有理内接多边形均由生产裁判算得 `ZERO_CONE`、9 DOF、精确秩 9。每例的 18 个 ±单位坐标非负法向旋量组合均用独立点积逐项核验。完整矩阵、顶点与组合证书存 [curvature_probe.json](file:///D:/eab-evidence/reports/codex/T1a_evidence/accept_fix/curvature_probe.json)，208575 字节。

具名门：

- `test_true_circle_grid_has_exact_zero_normal_work_and_zero_frictionless_capacity`
- `test_inscribed_circle_polygons_retain_false_smooth_interlock_at_four_refinements[2/4/8/16]`
- `test_tia_g3_true_circle_grid_frozen_polygon_is_not_a_smooth_curve_claim`

因此，**这四次加密仍保留相对于光滑真圆的不安全伪互锁**。不得由此宣称所有 n 的收敛定理，也不得推广到未复核的椭圆与正弦格；足以否定“这批折线已认证代表曲面”的解释。

## 3. 图件订正与视觉核验

[图注](../../T1a_figures/captions_zh.md)、[图件 QA](../../T1a_figures/visual_qa.md) 已更新。图 1d 明示 h−:2 / h+:0；图 2 改为同相退化网格，λ 是一周期占满的块高，并注明伪互锁与关联正阈值不安全下界。工具读取输入经过 `frozen_evidence.data_path` 映射，不重算求解器。

两张完整 PNG 已打开目视核验：三角注记、九格文字、纵轴双行标签与三行页脚均无遮挡/截切；六份图件均 < 1 MB，SVG 保留文字。PDF 由同一 matplotlib Figure 直接导出，未单独栅格化，不冒称已逐页视觉核验 PDF。

语义门原样最后一行：`figure semantic gate: 36 G5 source rows + 36 morphology cases + 6 artifact hashes verified; 0 solver runs`。
