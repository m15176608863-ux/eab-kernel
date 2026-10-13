# O02 修复分项

## 根因与修复
`_shape_value` 和 `_shape_coordinate` 直接透传 `Dual`，使全局 Dual 的合法逐运算舍入发生在本具名工具的完整坐标/jet 构造之前。仅在 `tools/osteomorphic.py` 新增私有 `_ShapeJet` 有理一阶代数；所有最终坐标及通道由 `scalar_rational` 构造，超界具名拒答。**没有修改全局 Dual。**

## 修前红 → 修后绿
- 原代码新增门后：`20 failed, 2 passed in 0.23s`（`o02_red.log`）。其中 18 项实际相消/提前域拒答，2 项最终异常应具名为 osteomorphic jet 的加强门。
- 示例断言：`actual.v == expected == raw.verts[8][axis]` → `0.0 != 7.888609052210118e-31`；`actual.e == expected` → `(0.0, 0.0) != (1.0, -3.0)`。
- 完整定向兼容：`157 passed in 46.11s`（`o02_compatibility.log`），涵盖新门、R14 domain、全部 interlock sensitivity、R14 Dual。
- 未改写任何已有测试，未删门/skip/xfail/缩网格。

## 同类扫描新增修复
1. `interlocking_pair_generic` 提前计算上块 center：原上块底面残差 2^-100 被删，下块顶面却保留；现在内部中心和坐标完整计算后才舍入。
2. 相位导数 `cos(angle)*seed` 在 sin 内过早构造：原 seed=2^-1074、amp=2^400 时内部下溢，seed=2^1200、amp=2^-400 时内部溢出，最终 jet 均可表达。现在 callback 用单位 seed 取近似模型的一阶系数，再精确乘原 seed/amp 至完整坐标。
3. 另扫工具 float/sum/零初值：M4 是整数计数；showcase 普通中心求和为近似绘图；tia_sensitivity CLI 均值是已构造浮点 jet 的四位摘要，不冒充 Fraction 证书。

## 变异有牙
详见 `o02_mutations.py` / `.json` / `.log`，均在真实运行路径中修改内存函数，退出恢复，不改磁盘生产源。
|内部变异|被击中的指定断言|
|---|---|
|每次局部加法先舍入 primal|`complete coordinate residual`|
|每次局部加法先舍入 jet|`complete jet residual`|
|完整高度未完成就舍入|`complete height residual`|
|pair 中心先构造再进生成器|`complete pair translation residual`|
|sin 内先乘原 seed 再乘 amp|`representable complete phase jet rejected`|

## 覆盖与边界
参数覆盖 x/y/z、2^-100 与 D400 下端 2^-400、小/原/大尺度、正负双通道、nx=5/ny=3 一般位形所有顶点和通道；独立 oracle 仅用 Fraction 完整表达式与 math.sin/cos 的既定采样系数，不调用生产 Dual 算术或几何原语。
libm 仍是采样近似模型；没有声称一般超越函数全域正确舍入。自定义 sin_fn 作为一阶标量回调，收到宽 1 的 Dual(argument,(1.0,))，必须返回宽 1 的 Dual；依赖调用方原 seed/宽度的非一般标量回调不再兼容。双通道 phase seed=(13,-15) 由一般位形独立 oracle 验证完整比例。
