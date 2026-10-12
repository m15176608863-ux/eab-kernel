# J03 / J05 根因、验证与同类扫描

## J03

`in_cone` 原 strict 分支只查两侧叉积正，不核两边界构成正向凸锥；微反射的反向薄扇区恰同时满足两条叉积。
修复先核非反射/显式微反射域，严格分支再要求精确正转角。大反射和对向射线外部，零射线明确拒收。

修前 `J03_J05_red_corrected.log` 含原复审三姿态 `assert 1 == -1`，并有普通反射、对向射线和零射线错误。
`J03_mutation_red.log` 在内存恢复原 `in_cone` 函数体，原三姿态全部在
`opposite thin sector is exterior` 断言红（不是构造后的伪造产物）。

扫描：读二维 `_cone_nonreflex/_cone_accepts/_ve_side_directions/_open_cone/vv_cover` 与三维
`vertex_cone_contains/edge_arc_contains/cone_constraints/cone_relint_direction/cones_intersect_relint` 的实际依赖。
VE 已先核凸性，VV 先拒非正转角；`_open_cone` 为其受前置条件保护的私有函数，无需无关重构。
三维顶点按全部 incident edge 半空间精确点积，棱弧先核有向三重积凸性，锥交按精确最小范数可行性，
不复用二维漏洞。新增微反射屋脊 h=1/100、2^-80、1/2 与三尺度/平移/有理旋转格，均拒反向方向。
这只是所列路径审查及输入族证据，不是任意曲面法锥的形式证明。

## J05

原流程过早把精确 LP 机构显示成 Inf，舍入预算显示成零，再算 `Inf*0` 得 NaN；
无界分支中 `NaN > threshold` 为假，留下默认 `resolved`。

修复：
1. `_wrench_rounding` 构造无量纲 norm 估计并保留有理尺度和乘法，不丢掉次正规荷载的更小预算；
2. 单体 `_lp_values` / 多体 `_ys` 的精确机构以及精确移轴荷载直接传至比值；
3. `_pushes`、邻域 alpha 相对变化也保持有理数到最终显示；
4. 最优/无界的单/多体四分支均将非有限 U 标 `unresolved`，不更改原始承载状态。

原复审最小次正规输入仍确认为 `unbounded`，现在 U 有限。独立静力证书是
`N = alpha*s - 1 >= 0`，故没有有限上限。退化对偶最优面为
`y_y=1/s, |y_x|/2 + |omega| <= 1/s`；预算各分量均为 `u*s`，因此 `u <= U <= 3u`，
`u=4*2^-53`。实测返回机构 `(0,1/s,-1/s)` 对应 `U=2u`，不是输入报告宣称的恒定 u。

修前日志中原例 `math.isfinite(NaN)` 断言红；此外强制 NaN/Inf 的单/多体状态门红。
修复后最小次正规至 2^1000 的尺度族、optimal 的超过 binary64 范围 alpha/机构视图，均仍保留精确承载证书。
`J05_mutation_red.log` 将 `_wrench_rounding` 的原函数体恢复到实际估计路径，单/多体均得到 U=0，
在独立下界 `u <= uncertainty` 断言红。`run_root_mutations.py` 保存目标断言检测和退出码。

### 测试开发订正（不是旧门放松）

最初新增 J05 测试误把 U 写成固定 u，导致正常尺度也红；在改生产前，读取原 LP 精确对偶并独立推导上述整个最优面，
将新门改成有效范围；原错误日志 `J03_J05_red.log` 与订正后仍复现缺陷的 `J03_J05_red_corrected.log` 都保留。
旧测试文件没有删改；无 skip/xfail、参数删减或精度放松。`test_uncertainty_ratio_completes_before_binary64_display`
另检查完整有理比值与巨大相消后的最终 float 输出。

## 已完成定向验证

- `J03_J05_green.log`：`186 passed in 10.15s`（含旧 limit fuzz/multi/exact_selfcheck）。
- `J03_J05_scan.log`：`81 passed in 0.21s`（含新法锥扫描与旧 R9 solid cones）。
- `J05_optimal_scan.log`：`22 passed in 0.08s`。
- 源内变异：J03 三个目标格红；J05 两个目标格红、六个控制格绿。

上述定向运行不是最终全套数字；最终命令和耗时以 R10FIX_report.md 为准。
