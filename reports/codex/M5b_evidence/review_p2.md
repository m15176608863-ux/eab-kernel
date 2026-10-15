# M5b 独立复核：P2、六次根与 oracle 边界

复核者未实现 `dda_motion.py` 或新 P2 oracle；本轮阅读生产代码、证明和测试，独立重跑数值门并另建探针。**本范围 0 critical、0 major；不是整个工单的六路 G6 验收。** 静态准入由本复核者另行维护，因此本报告不把自己写的静态零违例当成独立数值证据。

## 核验结果

1. **次数未偷换成近似判定。** `RealAlgebraic.__post_init__` 和 `roots_interval` 仅把输入次数上限由 5 改为 6；都在平方自由化之前拒绝七次，原有精确 Fraction、Sturm 根数、gcd 等根、闭端点和隔离唯一性检查保留。额外探针用六个跨正负及零的已知有理因子核对闭窗全根；`x^6-2` 的正负两支核对独立整数符号括区间；`x^7` 虽可约到低次仍拒绝，非法多根括区间也拒绝。
2. **P2 六次公式确有正因子整除。** 对 B 的边/顶点分子，模 `D_B` 后留下 `Q_B e / Q_B v`；叉积和点积的 `Q_B` 恒等式分别给出 `D_B²` 倍，故可整除 `D_B`。生产 `_divide_positive_factor` 真实执行精确除法并检查余式；`u_B=0` 时分母是常数但相应分子次数已经降为一，不能机械减两次，这一分支的证明和实现一致。六次测试实际出现非零最高项，不只是允许更多系数。
3. **首入及法锥复用边界清楚。** P2 自己生成应变事件，不复用 SE2 刚体事件公式；复用的是精确 `_event_times`、关联重建与结果协议。全窗正行列式充分条件保持凸/凹转角符号，而 `_cone` 使用的是 P2 当前边分子。新增的六组一般转动/应变输入都由独立 oracle 检查完整首根、盖、关联和开区间；另外将两个环同时逆序，按独立原顶点/原边编号公式核对标签，全部一致。
4. **P2/P3 上界证明不是采样替代。** 半角包围来自有理交错 Taylor；`|atan'|<=1` 给参数误差，`|f''|<=4|u1|³` 配合二阶线性插值余项给全窗 `|u1|³/2`。旋转算子差再乘半径得到位置界。测试用独立阶乘 Taylor 区间抽查实现，但全窗性来自解析证明。普通 `HalfAngleApproximation` 字段构造器不证明外来字段真包住 tan，这一限制已写入代码、文档和专门拒绝/来源门。

## 独立 oracle 导入及共用边界

主期望路径：

```text
m5b_independent_oracle
  fractions.Fraction
  m5a_independent_oracle
    fractions.Fraction
    functools.cmp_to_key / lru_cache
    eab.kernel2d.g0_oracle.overlap
      fractions.Fraction
      math.lcm
      eab.oracle_construction (其显示函数在本 oracle 路径不调用)
        decimal / fractions / functools / math / struct
        eab.numeric_domain.ConstructionDomainError
```

没有导入被测 `dda_motion/se2/algebraic/motion/exact/global_entrance/construction` 的几何、根隔离或法锥原语。坐标由两次复数乘积独立求值，系数由七点 Lagrange 插值，根/符号由测试专属 Sturm/gcd/有理区间实现，开区间成员由独立 G0 winding/交段路径。G0 名称虽在 `src/eab`，它不是被测生产 `exact` 的几何原语；`numeric_domain` 仅是异常类型，不产生几何或期望数值。

退化一致性门中的 M4c / SE2 调用只是被测实现间的一致性，不冒充独立 oracle。复核探针的六个线性因子由自己的 Fraction 卷积生成，逆序标签期望由显式编号公式生成，不调用生产 label 映射。

## 变异复核

四个生产函数体内部变异均重跑：丢六次项红在**独立首根身份**；剪切加倍红在独立复数坐标；面积形心改顶点均值红在两个矩形层片面积矩；删去时间律界红在独立 P3 区间不能被所报界包含。没有在被测结果之后追加假值。这些数值执行路径不读取任何冻结/source-hash回调，红点不是源码哈希绊线。

另执行本分工的 `as_rational` 余数零门及内部漏余数零变异；其独立期待是有理根 p，数值实现原本正确。

## 实跑证据

- P2 + 既有 M5a / M5a2 数值门：`118 passed in 3.51s`，0 skip；[执行记录](file:///D:/eab-wt/cx-e2/reports/codex/M5b_evidence/review_p2_tests.json)。
- 额外六次 / 一般位形 / 逆序原 ID 探针：6 组全部真六次、总数值失配 0，3 类非法合同拒绝；[可重跑探针](file:///D:/eab-wt/cx-e2/reports/codex/M5b_evidence/review_p2_probe.py)、[探针结果](file:///D:/eab-wt/cx-e2/reports/codex/M5b_evidence/review_p2_probe.json)。

边界：这不证明任意多圈角、非简单环、材料孔洞或不能满足所给非反转充分条件的步；不把 P2 当成 DDA 内部连续物理轨迹；不以少量探针代替主线程全时程、冻结闭包真实重算与全套四片。`algebraic.py` 已触及历史绑定，必须由主报告提供真实重算证据，不能只改哈希。

P2_REVIEW_PASS_WITH_DECLARED_DOMAIN
