# M4a 比较器独立攻击审查（adapter 子任务）

审查对象：`tools/m4_bdda_shadow.py`；本审查不改比较器。适配器作者审查的是另一代理写的比较器，**不是 M4 全里程碑的六路 G6 退出审查**。

审查时文件 SHA256：`72c5bde9183d3b613c6a4ea9bcab38054a46a97499daf035eafdb354dff37561`。以下发现针对该版本；主代理修复之后应另记复测，不把本记录改写成从未发现问题。

## 已验证

1. `support()` 的输入方向是顶点向内的支撑方向；VE 用边外法向，VV 对 A 用 A−B、对 B 用 B−A，方向一致。凸/小反射拓扑、邻点半空间以及单位法向和的正号共同拒绝反向支撑。
2. 以 seed `53499`，使用四边形、两种 L/阶梯凹多边形、近直线顶点多边形，生成 200 组一般位置输入；角窗取 0、1、3、10 度，距离窗 4，段窗 1/1000。逐一比较全部 VE、EV、VV 候选，共 **16299 次** `eligibility()` 调用，与 `tests/test_kernel2d_covers_e3.py::independent_cover_oracle` 无分歧。该 oracle 使用 Fraction 邻点投影和 Fourier–Motzkin 消元，不调用生产 covers/geom/exact 原语。
3. `check_metric()` 使用 exact oracle 构造有符号法向距离，以贴合精度比较 gap；法向平行度是齐次平方比较，并另外约束单位长和正方向。VV 全局顶点排序后的记录方向修正正确；重合 VV 明确允许法向为 None。
4. `classify_extra()` 不把「全部有效局部盖」冒充 legacy 的有序选择子集，也不从局部盖符号推断凹块全局相交。额外有效盖的物理等价性明确未判定，这是适当的信任边界。

## 发现 RC-01：legacy 实际度量列未参与比较（应修）

该版本只对 `ed`（eab）的记录调用 `check_metric()`；legacy 只参加特征键集合比较。即使 legacy 已导出检测几何度量，比较器也完全忽略。`df22.o3` 的确是后求解的另一 observable，不能拿来混比；但 `df18.cs1` 正是当前几何的法向 gap，`df18.s1/s2` 是接触法向。见只读源码 `D:/b-DDA/df/df.c` 的 `df18()`，`b803`、`b804`：先以三个当前顶点计算 `s1`，再用 `dspl` 的平移两列计算 `s[1:2]`。

实测 `bb52_N3` 步 1 第 6 条 VE：

- 独立精确原坐标 gap：`-3.97199607009849e-7`。
- legacy `extra['df18_cs1']`：`-3.9719960701140423e-7`。
- legacy `extra['df18_s'][:2]`：`[0.21101229125351517, -0.9774834080126076]`。

### 真实读入路径变异

没有修改夹具、没有在枚举之后追加伪记录；在现有读取器内部 `_read_csv()` 返回给 `read_df18_csv()` 的列解码阶段，令 `cs1` 错读为 `b1`：

```python
real = bdda_df._read_csv
def corrupted(path):
    rows = real(path)
    if path.name == 'bdda_debug_df18.csv':
        for row in rows:
            row['cs1'] = row['b1']
    return rows
bdda_df._read_csv = corrupted
mutant = compare_fixture(Path('fixtures/bdda_df/bb52_N3'))
assert_classified(mutant)
```

结果：`classifier accepted metric-column misread: True`；变异结果与未变异的 `compare_fixture` 返回值完全相同。错误列不是不可复现 `o3/o4`，而是有物理意义的确定性列；应让目标度量断言报红。

### 建议最小修复

- 对有 `df18_cs1` 和至少两个 `df18_s` 分量的 VE，在不覆盖 df22 状态字段的前提下，用临时 ContactRecord 副本明确置 `gap=cs1`、`normal=s[:2]`，再走 `check_metric()`。
- 仅对导出中的第一参考 `jj=0` 判接触主引用；VV 两套参考不能把一条参考的 VE 法向冒充点点集值法向。
- 每步汇总显式统计 `legacy_exported_metric_checks` 与 `legacy_reconstructed_only`。当前插桩的 df18 主要只有步 1；后续步只有几何重建口径时如实声明，不写成已逐条校核 legacy 内部度量。
- 补上述 `_read_csv` 内部列错位变异，失败必须是 `gap outside fit precision`；另加法向反号变异，失败必须是 `normal direction reversed`。

## 其他边界

- 固定各类计数能抓常规漏盖，但不能单独证明任意输入上的枚举完备性；本任务的独立 oracle 门和刚体/单位变换门应保留。
- `EXACT_LOCAL_COVER_NOT_SELECTED` 中的 exact 意味着零角扩窗下仍为有效局部盖，距离窗/段窗依然是显式 L5 域窗；不要把名称解释成「两块精确接触」或物理全局正确。
- 本审查不推断 legacy VV `p1/p2` 主引用语义；应以 seam-map 对 df05/df06 和 dump 列的追踪结果为准。

## RC-01 修复后复测

主代理已对可观察的 VE `df18.cs1/s1/s2` 加入独立度量检查，并分别报告 `legacy_ve_metrics_observed` 与 `legacy_metrics_geometry_only`。复测版本 SHA256：`656d40fb392d55a57554ebef46ca442b1814d289ab759358b5961697756868c3`。

仍在 `_read_csv` 实际被消费的路径中注入错误，不改夹具，逐个变异且 `finally` 恢复原函数：

| 变异 | 修复后结果 | 报红断言 |
|---|---|---|
| `df18.cs1` 错读为 `b1` | CAUGHT | `gap outside fit precision` |
| `df18.s1/s2` 同时反号 | CAUGHT | `normal direction reversed` |

法向反号通过 `str(-Decimal(row[key]))` 保持合法 CSV 数字文本。首次测试脚本曾用 Fraction 的分数字符串，先触发解析错误；该次不计牙，以上两条均已重跑并确认为目标几何断言报红。

结论：**RC-01 已由主代理修复，目标度量断言有牙。** 仍应保留逐步 `geometry_only` 覆盖边界，不把后续步未导出的 legacy 内部法向/间隙当作已测；VV 的弹簧参考法向与静态径向法向也不应混称。

## 最终交叉审查（不是 G6）

审查快照 SHA256：

- `tools/m4_bdda_shadow.py`：`879fcac0e29e1c1c1f30762a731f01fc7854668f77216109edb1d7f985b090f6`。
- `tests/test_m4_bdda_shadow.py`：`46534f53f746d327b308d487b71590cb250679e488638b31c873f9e9ee9546ee`。
- `docs/m4_difference_ledger.md`：`2d1615f40895db3e33348ff6f476c21577912714c9f3d4733cab0286b4daa1f3`。

再次通读当前比较工具、`tests/test_m4_bdda_shadow.py` 及 `docs/m4_difference_ledger.md`：

- 434 条 `LEGACY_OUTSIDE_FINITE_EDGE_WINDOW` 只判「不在 L5 有限边窗口内」，没有把该事实升级为 legacy 物理错误。
- 98 条 `LEGACY_VV_DIRECTION_OUTSIDE_OPEN_CONE` 只判点间方向不满足静态活跃性，没有混比 legacy 双参考选边。
- 58 条 `VV_IDENTITY_MATCH_TWO_REFERENCE_NORMAL` 与 VE `MATCH` 明确分开；身份一致不等于两个弹簧参考法向与点点径向同构。
- 782 条实际可观测 VE 度量和 1756 条仅几何重构行明确区分；重复主键的第二条实导度量也受到检查。
- 每帧固定计数加逐条差异摘要 SHA256，能抓住计数不变但分类换位；仅固定计数不够的早先边界已补强。

追加两处实际路径攻击（均不改夹具、执行后恢复函数）：

1. 在生产 `covers.ve_cover/ev_cover` 内漏掉 bb52/步 1 的 eab-only `VE(39;93,94)`。目标门以 `pinned shadow tally ... 'eab', 84, 85` 报红。即使漏的不是 legacy 共有盖，也不能悄悄通过。
2. 在生产 `covers.ve_cover` 内把构造法向反号。目标门以 `normal direction reversed` 报红。

针对性重跑：`85 passed in 6.92s`（`test_m4_bdda_shadow.py` + `test_m4_bdda_adapter.py`）。本次没有发现新的分类/度量过度声称或能够绕过上述冻结门的明显漏洞。

文案微小限定建议：台账的「重复步不接受」宜具体写作「重复参数步不接受」或列出各输入门；当前重复参数行受明确计数门约束，而顶点表本来就是每步多行，整段重复几何数据是否拒绝不是本次单独验证命题。此项不影响上述 45 帧已冻结输入的结论。
