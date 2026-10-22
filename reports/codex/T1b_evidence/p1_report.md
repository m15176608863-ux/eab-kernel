# WO-T1b / P1：真正依赖形貌的二维阈值

**白话结论：在明确选取的薄块、真实折线界面与关联流动模型中，摩擦阈值不再恒为零，并随齿幅、倾角、相位、非对称度和周期数改变；这不是实际材料强度、有限运动或一般形貌规律的证明。**

> 本文件为主报告可并入的 P1 分节。最终证据须使用 `p1_final_20261022`，早期 `p1_scan_20261022` 仅为探索；最终运行核验见本文件末节及 `p1_summary.json`。

## 1. 模型与族

全部使用冻结 `profile1`：刚体、小变形、无限抗压、无黏聚、恒定 μ、关联流动；两端为 `FIXED_BODY`，中块在 x=0 受竖向单位活载，无恒载。UNBOUNDED 只是这个锥模型可无限增大的载荷射线，**不是几何锁定**。关联模型相对于非关联摩擦仍保留 T1a 的不安全侧边界。

五块的四条内部界面定义为

\[
x_k(y)=-5+2k+\sigma_k[t(y-h/2)+A f_k(y)],\quad
\sigma=(-1,-1,1,1),\quad 0\le y\le h.
\]

采用 `h=1/16`，水平名义间距 `ℓ=2`；`t∈{3/32,11/128}`。这比 T1a 默认厚块更细长，是公开的几何选择，不隐称同一尺寸下所有形貌都非退化。参考点及实际 LP 约束锚点均为 `(5/8,-3/8)`，不是原点。四条面左右镜像，配合两侧引用同一组精确顶点，没有各自舍入。

- **锯齿**：`u=(y/λ+(k−1)φ) mod 1`；`f=u/η`（u≤η），否则 `f=(1−u)/(1−η)`。`η` 是峰顶所占周期位置，左右齿面坡度分别为 `A/(ηλ)` 和 `−A/((1−η)λ)`。`η∈{1/4,1/2,3/4}`。
- **周期与相位**：`λ=h/n`，`n∈{1,2,4}`；`φ∈{0,1/4,1/2}`。波长不是必须等于块高；输入同时给定 h、λ、n 时会核对一致性。φ 是相邻界面的相位增量，不是每面都相同的绝对相位。
- **两段 kinked 面**：`f=max(0,(y/h−η)/(1−η))`。下段坡度为 `σt`，上段为 `σ[t+A/(h(1−η))]`，不冒充周期圆弧或光滑曲线。

所有界面都是真多边形折线；每块完整轮廓及预期邻接 CONTACT 用精确谓词复核。正式结果不引用文献数值，也不把多边形互锁外推到光滑面。

具名门：`test_t1b_profiles_are_true_shared_rational_polygons`、`test_t1b_profile_input_guards_and_period_independence`。

## 2. 非退化证据与设计曲线

扫描共 36 个构型：两个 t、三个非零 A、三个相位的一周期组合；二/四周期相位组合；两种非对称补点；六个 kinked 点；两个 A=0 控制。它是有针对性的设计曲线/交叉补点，**不是五维全笛卡尔网格**。

例如 `t=3/32, φ=0, η=1/2, n=1`：

| A | A/λ | 精确 μcrit | 端点 |
|---|---:|---:|---|
| 0 | 0 | 2039/32768 | 闭 |
| 1/4096 | 1/256 | 9177/131104 | 闭 |
| 1/2048 | 1/128 | 16359/262144 | 闭 |
| 1/1024 | 1/64 | 767/16384 | 闭 |

可见“增加齿幅一定降低/提高阈值”都不成立于这些点：改变形貌也会改变控制接触位置和力矩臂。基准 `A=1/2048` 改为二、四周期，同相对称的精确阈值分别为 `319/8188`、`201/52352`。改相位也改变阈值：在 `t=11/128,A=1/1024,φ=1/2` 时，精确阈值 `7/128` **不取到**；在 `t=3/32` 对应点为开阈 `1/16`。不能把所有阈值一律写成闭。

36 例得到 25 个精确有理阈值（23 闭、2 开）与 11 个认证括号。括号点的开闭为 `null/未证`，不从括号宽度猜测根或端点性质。每个括号均保存下端有界最优证书和上端无界射线证书；原始精确矩阵随 gzip 留存。图中的连线只连接有限采样点，不主张两点之间线性。

全部 36 例的一阶自由锥为 `NONZERO_CONE`；低于阈值的规范化对偶机制均保留平移/转动自由度的精确坐标。这仅给出一阶候选，**不推出存在有限运动**。全表中的 `mode=associated_translation_rotation` 是从所存机制的非零转动坐标读取，不宣称唯一破坏模式或真运动路径。

对照用原 `morphology_geometry` 现场重跑 TIA-G2/G3/G4 的 `A=1/8,λ=h=1` 同相族：三个阈值都为闭零阈；没有重放整个 T1a 历史网格，也没有改旧冻结数据。

具名门：`test_t1b_nondegenerate_shape_and_t1a_zero_control`、`test_t1b_phase_changes_actual_threshold_and_preserves_an_open_endpoint`、慢门 `test_t1b_design_curve_cases_have_exact_certificates_and_mobility`。

## 3. 闭式对照：只限明确的活动齿面分支

对一周期、同相、对称齿，在实测的上半齿面控制分支，设上段高度 `H=h/2`、倾斜量 `s=t−2A/h`。相邻同侧界面的水平名义间距为 `ℓ=2`。侧块所受两压缩合力必须共线；两控制端点的水平间距为 `ℓ−sH`、高度差 H，因此合力竖/横比

\[
q=\frac{H}{\ell-sH}.
\]

对坡度 s 的平面，库仑锥边界力由未归一化法向/切向线性组合得到，对应

\[
q=\frac{s-\mu}{1+s\mu}.
\]

直接消去 q：

\[
\mu_{\rm branch}=\frac{s-q}{1+sq}
=s-\frac{H}{\ell}(1+s^2),\qquad
\frac{\partial\mu}{\partial t}=1-2\frac{H}{\ell}s,\qquad
\frac{\partial\mu}{\partial A}=-\frac2h\left(1-2\frac{H}{\ell}s\right).
\]

这是静力与单齿面摩擦角的手推关系，不调用生产的几何或 LP 来生成参考值。**必要适用条件**是这组上半齿面控制端点确实给出有效的全组装证书、其余齿面不先控制；并且 `ℓ−sH>0`、正分支成立。六个具名回归点 `t∈{3/32,11/128}`、`A∈{1/2048,3/4096,1/1024}` 逐点与生产精确证书一致。没有证明整个参数区域都处于此分支；较小幅值 `A=1/4096` 已不应套用此式。

在 `h=1/16,t=3/32,A=1/2048`，得到

\[
\mu_{crit}=16359/262144,\quad
\partial\mu_{crit}/\partial A=-2043/64,\quad
\partial\mu_{crit}/\partial t=2043/2048.
\]

生产导数通过 T1a `evaluate_sensitivity2` 的 `implicit_certificate` 路径认证，不是用阈值差商拟合。A/t 种子从原始共享顶点传到接触点、边切向、法向、力矩与活载列；参考点、锚点与 x=0 的竖向荷载不随 A/t 变化。二维矩阵里的力矩至多二次，门只用精确中心差验证**矩阵多项式的导数**，不将阈值有限差分当认证导数。

23 个非零形貌点的 A/t 导数获 `smooth` 认证，11 个括号点两者均为 `unresolved/null`。两个 A=0 控制点的 A 方向改变接触骨架，保持未证；只改变 t 不改变骨架，分别认证 `509/512`、`2037/2048`。所有导数均依赖输出中列明的骨架及活动证书有效条件，不允许跨切换点直接外推。

具名门：`test_t1b_upper_tooth_hand_wrench_threshold_and_implicit_derivatives`、`test_t1b_profile_jets_match_exact_affine_matrix_derivatives`。

## 4. 元门及信任边界

- 确切有理旋转由有理半角参数构造；平移量取 0、10³、10⁵；几何尺度分别为 1、8、2⁻²⁰；荷载单位独立取 1、3/2、11。
- 在原阈值下方、阈值本身及上方，逐一核对有界/无界状态并重算精确证书算术。最大平移与最小特征尺度同现，未把大坐标噪声吞成公差。
- 固定端与自由体掩码在正交变换下保持各自全固定/全自由；参考点及实际使用锚点一起变换，力矩按单位缩放。
- `certificate_arithmetic` 仅对保存的精确矩阵核 `Ax=b,x≥0,Aᵀy≥c,bᵀy=cᵀx` 或可行点/下降射线，不调用生产证书检查函数。但它仍消费生产模型矩阵，**不是独立几何装配 oracle**；因此另有手推闭式及共享输入几何门。

具名门：`test_t1b_rational_rotation_large_translation_and_units`。有限元门不等于全输入域证明。

## 5. 工单订正与建议新增清单

**订正/具体化**：

1. 不把“加锯齿”本身视作非退化保证；先做薄块小扫描，选择左右镜像且含正阈值的族。既有 T1a 同相族未改。
2. φ=1/2 的两个样点出现开阈。括号未解精确根者不声明开闭。
3. 不是每点都有可认证导数，严格保留 null。没有修改设计合同、枚举或 tia2d-2 schema。

**建议 Claude 决定是否并入下一版设计**：

- `MorphologyProfile2`：`assembly,family,amplitude,wavelength,height,tilt,phase,asymmetry,periods,interfaces,vertex_seeds_amplitude,vertex_seeds_tilt`。
- `g1_morphology(...) -> MorphologyProfile2`，新增参数为族名、A、t、h、λ/周期数、相位增量、非对称峰位，保留 G1 边界/荷载。
- `g1_morphology_seed(problem,geometry,parameter)`，仅 A/t，直接消费 T1a 阈值导数合同。
- P0 辅助几何 `tolerance_dovetail`、`tolerance_knob`；后者额外报半圆采样段数和裁颈后实际鼓包段数，详见 P0 报告。二者本身不声明困住/阈值结论。
- 工具的 `tia2d.t1b.morphology.*.v1` 是**私有诊断格式**，不是新正式 schema；新增诊断字段不加入 tia2d-2，也不生成正式 C++ 批次。

## 6. 文件与复跑

- [精确小汇总](file:///D:/eab-wt/cx-e2/reports/codex/T1b_evidence/p1_summary.json)
- [设计曲线 PNG](file:///D:/eab-wt/cx-e2/reports/codex/T1b_evidence/p1_figures/p1_design_curves.png) / [SVG](file:///D:/eab-wt/cx-e2/reports/codex/T1b_evidence/p1_figures/p1_design_curves.svg)
- [外部最终证据目录](file:///D:/eab-evidence/reports/codex/T1b_evidence/p1_final_20261022/)
- [扫描工具](file:///D:/eab-wt/cx-e2/tools/tia2d_t1b_morphology.py) / [具名测试](file:///D:/eab-wt/cx-e2/tests/test_tia2d_t1b_morphology.py)
- [定向快档日志](file:///D:/eab-wt/cx-e2/reports/codex/T1b_evidence/p1_targeted.log)

复跑必须使用新的外部目录；`--source-revision 7f95105` 仅标识开工提交，脏树的实际字节由工具在前后核对的全 `src/eab/**/*.py` 与自身工具 SHA256 决定。进度逐例落盘；中断无完成标记，不允许拼接。PNG/SVG 为常规工程图，精确判断只读取 JSON 分数而非图像像素。

```powershell
python tools/tia2d_t1b_morphology.py --output D:/eab-evidence/reports/codex/T1b_evidence/p1_fresh_run --summary reports/codex/T1b_evidence/p1_fresh_summary.json --source-revision 7f95105 --max-steps 40
python -m pytest tests/test_tia2d_t1b_morphology.py -q -p no:cacheprovider --basetemp reports/codex/T1b_evidence/tmp/pytest_p1_fresh
```

`TEMP/TMP` 均置本单 `reports/codex/T1b_evidence/tmp/`。大证据由主报告在 `reports/EVIDENCE_ARCHIVE.md` 统一登记；本分任务不改该共用文件。

## 7. 最终状态

最终新目录扫描已完成，67 个 Python 源文件（整个 `src/eab` 及扫描工具）运行前后 SHA256 完全一致；耗时 124.712 秒。36 例、25 精确阈值（23 闭 2 开）、11 认证括号、全部 `NONZERO_CONE`；A/t 分别 23/25 个 smooth 导数，其余保持未证。实际最大括号宽度 `1/1099511627776=2^-40`。

独立标准库回读器没有导入 eab：对保存的 36 个 gzip 逐文件 SHA256、97 份精确 LP 最优/无界证书以及所有保存的自由锥生成元完成精确算术复核。该回读只核保存的矩阵，不冒充独立几何装配。

最终扫描与定向快档最后一行原样：

```text
P1_COMPLETE 36 cases; 124.712 seconds
22 passed, 36 deselected in 11.33s
P1_READBACK_OK cases=36 certificates=97
```

[QA 清单](file:///D:/eab-wt/cx-e2/reports/codex/T1b_evidence/p1_qa.json)包括源守护、PNG 1600×1120 实际目视检查和 SVG XML 解析；四面板坐标、图例及开/闭/括号标记可读、无遮挡。精确数值仍以 JSON 为准。[回读结果](file:///D:/eab-wt/cx-e2/reports/codex/T1b_evidence/p1_readback_audit.json)及[可复跑回读脚本](file:///D:/eab-wt/cx-e2/reports/codex/T1b_evidence/p1_readback_command.py.txt)一并保留。

全仓快档、四分片、新鲜树及 Claude 安排的独立对抗复核由主代理统一记录，本分任务不冒称执行；本 P1 不新增正式 tia2d-2 语料，11 点精确根/开闭及未证导数仍为明确局限，不把 null 包装成已解。
