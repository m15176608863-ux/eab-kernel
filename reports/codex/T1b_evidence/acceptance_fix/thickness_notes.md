# WO-T1b 验收补充：形貌创造正摩擦阈值的厚度带

**结论：在指定的零相位、刚体、无限抗压、关联流动模型里，确有“平直界面临界摩擦为零，而加齿后为正”的厚度带；这是严格限定参数族的极限承载结论，不是平移几何困住，也不是有限运动或真实材料的验证。**

## 1. 输入、范围和证据

- 继承 `g1_morphology` 的五块布置、两端 `FIXED_BODY`、中块竖向单位活载、无恒载，参考点与约束锚点均为 `(5/8,-3/8)`；自由块含转动自由度。
- 固定 `t=3/32`、界面间距 `ell=2`、相位 `phi=0`。记 `r=h/ell`、`a=A/h`，`n` 为周期数，`eta` 为一周期中上升齿段的占比。
- 本补充有四个正带主族和两个无正带对照，不是 `a,n,eta,phi` 的全参数扫描。六族均 `a<=1/64`，包含 `n=1,2`、对称 `eta=1/2` 和非对称 `eta=1/4`。
- 全带边界的解析论证限定于六个固定族、`0<r<=3/16`；正阈值的具体分式逐个样本由 LP 与临界基单侧延拓认证，不把一个推力线候选当作全参数公式。
- [厚度摘要与各样本精确值](file:///D:/eab-wt/cx-e2/reports/codex/T1b_evidence/acceptance_fix/thickness_summary.json)：39 个厚度样本，另 18 个离散厚块对照；源码前后 SHA 相等，39 样本与对照生成共 29.941 s。
- [完整原始矩阵、LP 与临界基证书](file:///D:/eab-evidence/reports/codex/T1b_evidence/acceptance_fix/thickness_final/)：40 个 gzip 数据文件，不修改 tia2d-2 schema。
- [保存后独立矩阵回读](file:///D:/eab-wt/cx-e2/reports/codex/T1b_evidence/acceptance_fix/thickness_readback.json)：文件 SHA 全相等，118 份去重 LP 证书通过精确原/对偶/射线算术，其中 22 OPTIMAL、96 UNBOUNDED。该回读不独立重构几何 LP，不独立重写 Sturm 算法。

## 2. 精确厚度边界：不是网格插值

零相位的左侧两个界面为相同折线沿 x 平移 `ell`。写 `z=y/h`，

```text
g(z) = t(z-1/2) + a f(z),       x = offset - h g(z).
s_up   = t + a*n/eta,
s_down = t - a*n/(1-eta).
```

零摩擦时，每段齿面法向的水平分量为正。把接触合力水平分量归一化为 1，竖/水平力比记为 `q`；端点力矩可写成 `offset*q - h*b`，其中

```text
b = z + q*g(z).
```

因此一个界面的所有分布压力所能产生的归一化合力—力矩集合，恰是各齿段端点 `(q,b)` 的凸包：段内力可移到两端，若干力可作非负凸组合。零摩擦只有 `q=s_up,s_down` 两种齿面坡度，故凸包在固定 `q` 处的竖向截宽 `D(q)` 是这两种坡度处宽度的线性插值。端点宽度直接为

```text
d_up   = 1 - (1-eta)/n,
d_down = 1 - eta/n,
D_up   = d_up*(1+s_up*t) + s_up*a,
D_down = d_down*(1+s_down*t) - s_down*a.
```

无外载边块的两端合力必须相等、反向且共线，力矩平衡要求

```text
h*(b_inner-b_outer) = ell*q,
即 r*D(q) >= q.
```

`q/D(q)` 是线性分式，正分母区间中单调或常数，因此最小值必在 `s_up,s_down` 之一取得：

```text
r_zero = min(s_up/D_up, s_down/D_down).
```

**必要性**：若 `r<r_zero`，任一边块都无法同时平衡力和力矩。**充分性**：若 `r>=r_zero`，取相应齿面坡度和截宽内的两合力位置即可平衡边块；右侧取镜像，两侧水平力及对中块的力矩相消，正竖向合力可归一化承受单位荷载。六族的 `s_down>0`，所以原位零摩擦的接触力不能靠无界的零荷载自应力逃过这个判断：在足够小的摩擦邻域，向上合力保持正下界，单位载荷限制了各接触力之和；紧致性排除了 `mu` 趋零却没有零摩擦解的开零阈。由此 `r<r_zero` 的阈值严格为正，`r>=r_zero` 的阈值为闭零阈。

这段解析论证只依赖端点力矩和凸组合，不调用生产几何/LP 原语。`0<r<=3/16` 内 `h<=3/8`，六族的 `|h*g(z)|<1/32`，宽度为 2 的相邻界面不交叉；边界体也保持正宽度。因此没有在这段厚度区间里换了接触拓扑的隐藏前提。测试用实际生产 LP 检查边界两侧和带内有理点；有限测试本身不等于全实数区间证明。

平直 T1a 对照为

```text
mu_flat(r) = max(0, t-r*(1+t^2)),
r_flat = t/(1+t^2) = 96/1033 ≈ 0.0929332043.
```

于是形貌创造正阈值的带恰为 `[r_flat,r_zero)`（若 `r_zero<=r_flat` 则为空）：下端闭，因平直对照刚好闭零而齿形仍正；上端开，因齿形在该点也已经闭零。

| A/h | n | eta | 精确正带 r=h/ell | 上界约值 |
|---|---:|---|---|---:|
| 1/64 | 1 | 1/2 | `[96/1033,32/257)` | 0.124513619 |
| 1/128 | 1 | 1/4 | `[96/1033,16/145)` | 0.110344828 |
| 1/256 | 2 | 1/2 | `[96/1033,1280/12373)` | 0.103451063 |
| 1/256 | 2 | 1/4 | `[96/1033,64/677)` | 0.094534712 |
| 1/64 | 2 | 1/2 | 空；`r_zero=128/3079<96/1033` | 0.041571939 |
| 1/64 | 2 | 1/4 | 空；`r_zero=1280/21589<96/1033` | 0.059289453 |

因此“齿形创造阈值”并非所有周期数和幅值组合都成立；在同一 `A/h=1/64` 下改成双周期，本组两个 eta 的正带反而消失。

## 3. 带内精确阈值、证书与分支范围

对本次已认证的正阈值样本，控制推力线从第一段下降齿面的齿顶指向最后的齿谷。记

```text
s = s_down,
d = 1-eta/n,
Delta_g = t*d-a,
q = r*d/(1-r*Delta_g),
mu_candidate = (s-q)/(1+s*q)
             = [s-r*(d+s*Delta_g)]/[1+r*(s*d-Delta_g)].
```

这里只把它当候选：工具对候选逐一核验临界基多项式的精确根，以下侧对偶基在 `(mu_lo,mu_candidate)` 的符号延拓排除更小阈值，并直接在候选点取得精确 `UNBOUNDED` 原始矩阵射线证书。三种证据同时满足才标为精确闭阈；没有按括号宽度或小数接近升级。摩擦锥嵌套性把这个局部单侧证书延伸成阈值判定。`UNBOUNDED` 在无恒载、无限强度模型里表示存在可齐次放大的承载平衡，不表示几何锁定。

下表各行的平直对照均 `mu_flat=0`；`r_mid` 是相应正带上下界的有理中点。

| A/h,n,eta | r | 精确 mu_crit | 是否取得 |
|---|---|---|---|
| 1/64,1,1/2 | 96/1033 | 131/8264 | 闭 |
| 1/64,1,1/2 | 3/32 | 253/16384 ≈ 0.015441895 | 闭 |
| 1/64,1,1/2 | 28864/265481 (`r_mid`) | 131/16528 | 闭 |
| 1/128,1,1/4 | 96/1033 | 163/12396 | 闭 |
| 1/128,1,1/4 | 15224/149785 (`r_mid`) | 163/24792 | 闭 |
| 1/256,2,1/2 | 96/1033 | 4201/528512 | 闭 |
| 1/256,2,1/2 | 1255024/12781309 (`r_mid`) | 51978973/13078020224 | 闭 |
| 1/256,2,1/4 | 96/1033 | 1/708 | 闭 |
| 1/256,2,1/4 | 65552/699341 (`r_mid`) | 677/958628 | 闭 |

39 个厚度样本包括各带下端下方、下端、四分之一/中点/四分之三、上端、上端上方和厚度 `3/16`，并显式补 `r=3/32`；其中 17 点满足平直零阈且齿形正阈。额外 18 个离散厚块对照为六族各取 `r∈{3/16,1/4,1/2}`，全部取得闭零阈的精确 LP 证书。这 18 点不是无限厚度范围的普遍材料命题。

## 4. 具名门、成本与复现

[新增测试文件](file:///D:/eab-wt/cx-e2/tests/test_tia2d_t1b_thickness.py)：

- `test_t1b_thickness_band_exact_wrench_boundaries`：四个精确上下界；独立端点 `b` 算术核对解析截宽，不用生产几何或 LP 作主 oracle。
- `test_t1b_thickness_band_flat_zero_teeth_positive_exact_certificates`：四族的下端/中点/四分之三处都“平直零而齿形正”；正阈原始 LP 与基延拓证书。
- `test_t1b_thickness_band_open_upper_and_closed_lower`：带上下端及两侧，包含非对称双周期。
- `test_t1b_thickness_two_period_large_tooth_has_no_creation_band`：不把所有加齿组合都报告成创造阈值。
- `test_t1b_thickness_discrete_thick_controls_remain_closed_zero`：六族×三种离散厚块。
- `test_t1b_thickness_peak_value_and_scan_input_guards`：`253/16384` 特例与输入域。

定向实跑最后一行：

```text
41 passed in 16.80s
```

[测试命令、耗时与最后一行](file:///D:/eab-wt/cx-e2/reports/codex/T1b_evidence/acceptance_fix/thickness_tests.json)，[原始测试输出](file:///D:/eab-wt/cx-e2/reports/codex/T1b_evidence/acceptance_fix/thickness_tests.txt)。[新增测试静态扫描](file:///D:/eab-wt/cx-e2/reports/codex/T1b_evidence/acceptance_fix/thickness_changed_static.json) 为 0 违例；这是新增文件扫描，不替代主线收尾完整静态门。

数据复现须用新的输出目录，不能覆盖本次证据：

```powershell
python -X utf8 tools/tia2d_t1b_thickness.py --output D:/eab-evidence/reports/codex/T1b_evidence/acceptance_fix/thickness_rerun --summary reports/codex/T1b_evidence/acceptance_fix/thickness_rerun_summary.json --source-revision e757883
python -X utf8 reports/codex/T1b_evidence/acceptance_fix/thickness_readback_command.py.txt --summary reports/codex/T1b_evidence/acceptance_fix/thickness_summary.json --output reports/codex/T1b_evidence/acceptance_fix/thickness_readback_rerun.json
```

工具自行把 `TEMP/TMP` 指到本单 `reports/codex/T1b_evidence/tmp/`；正式运行必须源码前后不变才写完成标记。[工具源文件](file:///D:/eab-wt/cx-e2/tools/tia2d_t1b_thickness.py) 与上述函数均为适配器诊断工具助手，不建议升级成冻结设计合同。未改 adapter、内核数学、设计文档、schema 或静态准入；未作任何 Git 写操作。
