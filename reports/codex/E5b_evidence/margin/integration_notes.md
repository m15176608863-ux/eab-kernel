# 全套首轮集成：几何不变性与近平行棱迁移

## 原失败及迁移范围

- 首轮集成的 127 个 `test_invariance_geom` 失败：默认接口已采用真实折面三角标签和给定数据精确距离，而旧比较对象仍为源面环标签和旧相触窗口。
- 24 个 `test_near_parallel_edges` 失败：实际正间隙约 `1e-9`，旧门要求库隐式钳零；默认精确语义正确保留正间隙。
- 仅迁移这两个测试文件，增加测试专用 `e5b_margin_oracle.py`，**不改生产代码**。

## 原门完整保留

两个文件的 48 + 7 条原 `assert` 源文本逐字保留；全部 11 个测试函数与每个参数装饰器相同。机读证据为 `integration_assertion_retention.json`。完整收集仍是 2454 格。

旧 margin 调用显式传 `contact_window=contact_resolution(A,B)`，这是调用方选择旧窗口而不是库恢复隐式容差。旧 `stack_touch` 报告路径采用原名义相触几何；实际舍入输入的严格贯入分支由下面独立精确检查守住。原 overlap、盖枚举、支撑函数、凸入口块和 G0 门不改。

## 同格追加默认精确检查

没有重复追加大网格：原 `test_margin_layer_is_invariant` 的 385 格、11 个 identity 格、48 个 near-parallel 格内部调用精确检查。

独立 oracle：测试侧 `e5b_frozen_oracle.surface` 用独立投影耳切恢复真实折面；`e5a_cover_oracle` 用循环 Newell、Gram 系数、Gordan 极射线枚举实际表面盖；新增 helper 直接用 Fraction 计算每个真实盖的平方距离和完整标签集合。不调用生产几何、谓词、法向、三角化或距离原语。重叠状态用独立星核四面体并集整数 SAT；近平行格另与原独立两棱 Fraction 最小距离逐值相等，确保最近盖确为其构造声称的两棱。

逐格核对：

1. 默认微贯入哨兵、closed 和 `delta=0` 的 INSIDE；不以旧 ctol 吞掉。
2. 最近标签属于独立有理最小值集合；不是源面环名义并列集。
3. 默认 margin 选出的完整标签集合与独立 `distance² <= delta²` 集合一致，无重复。
4. 输出浮点距离仅作构造，以精确平方量开方的四 ulp 检查；所有择支零容差。
5. 原 delta、零 delta、浮点根及其左右相邻 binary64 阈值逐项按 Fraction 比较 INSIDE / ON_BOUNDARY / OUTSIDE。

验证命令与原始末行见 `integration_complete.log` / `.xml`；阶段子集 `integration_probe.log` 为 `829 passed, 1625 deselected in 91.00s (0:01:30)`。

## 最终结果与牙

完整两文件：`2454 passed in 185.27s (0:03:05)`。首轮 151 个失败节点均在完整 JUnit 中逐名通过，机读映射为 `integration_test_rewrites.json`。

内存编译真实 `_resolve`，再调用迁移后的原测试函数：

- 默认偷偷启用 ctol：被新增默认精确距离断言抓住。
- 显式窗口被忽略：被原 `assert d == 0.0` 抓住。
- 默认改回源面环：被新增真实表面最近标签断言抓住。

全部为目标断言报红，不接受旁路异常；脚本 `integration_mutation_probe.py`、逐条结果 `integration_mutations.json`。注入不写生产文件、不拼接假输出，完整测试后耗时不到一秒。汇总和被验证文件哈希见 `integration_summary.json`。
