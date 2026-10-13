# O02 修复独立只读复核

复核对象：当前 tools/osteomorphic.py 与 tests/test_r15fix_shape.py；本代理未改这两个文件。

- _ShapeJet 保持 Fraction value/seed，乘除为完整一阶代数；坐标/seed 的 scalar_rational 均在 _shape_coordinate 最终边界。
- 实际公式只需现有运算，未发现缺少 __rtruediv__ 导致的真实调用缺口。
- _shape_sin 使用已声明 sampled-libm 角度模型；raw 与 generic 角度表达式兼容。精确坐标 algebra 不误扩为正确舍入超越函数。
- phase unit coefficient 提取后按 Fraction 乘原始 seed，最后与 amp/height 合并后舍入；避免中间下/溢。
- physical primal 检查 D400，jet 只检查有限输入；完整 jet 输出越界才抛具名异常，允许中间超出 binary64 后抵消。
- 新门覆盖完整 residual、一般位置、D400、双通道、pair 平移和早缩放变异。未发现新算术反例；不等价于全域证明或独立 G6 退出。

## 应明示的 callback 兼容边界

实测 phase=Dual(.4,(3.,-5.))，包装标准 eab.dual.sin 的 sin_fn 收到两次 Dual(argument,(1.0,))，而非原始二通道 seed。首 z 返回 Dual(0.5973545855771626,(0.6907957455021638,-1.1513262425036064))，独立 .25*cos(.4)*(3,-5) 核对一致。

这是为完整 jet 构造有意调整的 callback 观察协议；建议公开 generic docstring/设计同步说明必须提供 width-polymorphic、遵守 chain rule 的 sin 实现，phase Dual 路径以 unit seed 采样。依赖调用方原始 width/seed 内容的 callback 不再兼容；不宜只在私有 helper 说明。
