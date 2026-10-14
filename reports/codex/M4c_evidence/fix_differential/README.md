# WO-M4c-fix #4：固定种子独立差分门

## 已执行结果

- 门：[`test_m4c_fix_differential.py`](../../../../tests/test_m4c_fix_differential.py)，末行 `124 passed in 1.22s`，0 skip。
- 123 个运动输入：固定种子 `20261014` 的 108 个随机非平移输入，以及 15 个无理根、面/角并列、凹槽、持续相切结构输入。
- 63 个输入含凹环；11 次无理首入；18 次多盖并列。状态为 no_contact 57、contact 35、initial_overlap 31。
- 初态三类为 −1/0/1 = 82/10/31。独立事件超集分出 1113 个开区间，每段检查两个有理时刻：分离/相切/重叠 = 718/3/392 段。
- 完整比较初态、结果状态、精确时刻证书、关联全集与盖全集：0 失配。
- 两个新增测试文件的定向静态构造检查均 0 违例；未修改豁免。

详见 [`summary.json`](summary.json)、完整精确输入和分段状态 [`cases.json`](cases.json)、[`pytest.txt`](pytest.txt) 与 [`pytest.xml`](pytest.xml)。

## 独立性与口径

[`m4c_independent_oracle.py`](../../../../tests/m4c_independent_oracle.py) 的**直接 import 全清单**：

1. `dataclasses.dataclass`
2. `fractions.Fraction`
3. `math.isqrt`
4. `math.lcm`
5. `eab.kernel2d.g0_oracle.overlap`

该文件不导入 `motion.py` 的任何函数，也不导入 `exact.py`、`global_entrance.py` 或生产几何原语。G0 overlap 使用整数绕数/线段相交；其显示辅助模块 `oracle_construction` 虽随 G0 导入，但本门的 overlap 路径不调用显示转换。测试驱动单独导入 `motion_first_entrance`，仅用于取得被测输出；导入边界由 `test_independent_oracle_import_boundary_and_exact_root_selfchecks` 看护。

- **事件与根**：自行在 `t=-1,0,1` 求有向面积并插值成二次多项式，解所有支撑直线根，构成事件超集；永久共线时加入顶点与两端点各坐标相等的根。整数判别式的 `Q(√D)` 算术、等价键和有理隔离排序均在 oracle 内实现，无浮点根或容差。
- **关联**：在代数事件时刻检查面积为零，以及 x/y 独立坐标框，不使用生产的点积夹持判据。
- **盖**：检查局部凸性与两相邻顶点所在的对方边半平面；平坦顶点另检查边反向；点点关系独立枚举。不是只比较任取一盖。
- **分段实体状态**：每个开事件区间使用两枚精确有理内点调用 G0 三态，要求同段一致；首入之前要求全部分离。有理首入处另要求 G0 恰为相切。正确性依赖覆盖全部边界变化的事件超集，不把有限时间网格当连续运动证明。
- **输入域**：随机形变的端点矩阵为 `I+H`，对角和非对角扰动绝对值均不超过 `1/8`。整个仿射步的对角至少 `7/8`，故行列式至少 `49/64−1/64=3/4>0`；凸/凹基础 CCW 环始终保持简单和方向。不调用生产实现筛选有效输入。
- **覆盖边界**：随机输入为单个环的各自整体仿射形变，不宣称穷尽任意逐顶点形变域；独立测试时间/状态/全集比较也不代表工程验证。

## 性能与复跑

JUnit 毫秒舍入后 124 节点总时间约 1.10 s，pytest 墙钟约 1.63 s。相对历史最终全套 call 总计 3523.370647 s 的参考比例为约 0.0312%，显著低于约 1% 预算。该历史分母不是同运行基准；本单最终四片实测时间以父报告为准。

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONIOENCODING='utf-8'
$env:TEMP=Join-Path (Get-Location) 'reports/codex/M4c_evidence/tmp/fix_differential/env'
$env:TMP=$env:TEMP
python -X utf8 reports/codex/M4c_evidence/fix_differential/run_differential.py
```

复跑器仅使用标准库，pytest 使用项目已有测试依赖；所有测试均 `-p no:cacheprovider`，`--basetemp`、TEMP、TMP 均在仓内指定子树。产物全部小于 1 MB。
