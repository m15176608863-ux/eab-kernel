# G6H-01 同类扫描追加：三维初态拓扑与零裕度成员

## 结论与范围

已修复只读扫描确认的两个三维同类入口：`first_entrance3`、默认精确零裕度 `inflated_membership`。它们原先都把“两个实体内部不相交、但闭体相触”一概认作 `∂E`；紧配合槽的真实入口块却可能在该处具有内点。**未改变** `polyhedra_overlap` 的实体三态、`body_distance=0` 的物理语义、显式非零接触窗口/报告带的政策，亦未把局部最浅盖出口宣传为一般凹入口块的全局穿透深度。

- [新拓扑模块](file:///D:/eab-wt/cx-e2/src/eab/kernel3d/entrance_topology.py)
- [首入接口](file:///D:/eab-wt/cx-e2/src/eab/kernel3d/entrance3.py)
- [零裕度成员接口](file:///D:/eab-wt/cx-e2/src/eab/margin.py)
- [30 格新门](file:///D:/eab-wt/cx-e2/tests/test_r8fix_initial_state3.py)
- [原只读扫描与覆盖范围](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/initial_state/SCAN_3D_READONLY.md)

生产旧版备份为本目录 `before3_entrance3.py`、`before3_margin.py`；后者保存的是三维拓扑改动前的当时版本，已包含其他代理此前完成的数值修改，不能拿它覆盖最终共享文件。没有 Git 写操作。

## 修前红：独立 Cartesian 区间并 oracle

把二维 U 槽挤出至 `z∈[0,1]`，A 为中心 `(.5,1,.5)`、半长 `(.5,.5,.25)` 的箱。将 U 分成三个 Cartesian 箱，逐坐标作差并取并，不调用生产的相交、三角化、平面、叉乘或球室原语，即得：

```text
E = [-2,2] × [-5/2,3/2] × [-3/4,3/4]
(0,0,0) ∈ int(E)，但 polyhedra_overlap(A,B) == 0
```

修前断言和实际输出见[原样红日志](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/initial_state/red3d.log)：

```text
assert got.kind == 'exit', 'topological int E must use local exit policy'
E AssertionError: topological int E must use local exit policy
E assert 'entrance' == 'exit'

assert margin.inflated_membership(A,B,delta=0) == margin.INSIDE
E assert 0 == 1

14 failed, 7 deselected in 1.17s
```

14 红包含 12 个尺度/平移/旋转格的错误 `entrance`、竖直运动的“missed an earlier entrance”异常，以及零裕度成员错误；[初次只读结果](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/initial_state/scan_3d_initial_state.json) 保留修前输出与当时源 SHA。

## 根治方法及正确性边界

1. 仅实体三态为接触 `0` 时细分；本已穿入或分离的状态不绕路。
2. 全部边界三角形的 VF/FV 与全部三角边 EE 配置平面组成真实 `∂E` 的超集。保留人工三角对角线，避免漏掉面三角化产生的边界；冗余平面只多分室，不改变成员答案。
3. 对经过当前位形的中央平面精确枚举三维方向球室：所有两法向交线的正负射线，逐射线切平面内各角扇区取有理方向；用第一个有理步长界保证不跨过其它中央平面。单平面单独取正负法向；按完整符号向量去重。
4. 第二个步长界保证局部探针在到达任何非中央配置平面之前停止。若任何开室探针分离，则为真实边界；全部开室穿入则为内点。离开全部候选墙后仍只相触，会响亮报错而非猜测。
5. 两层步长与所有分支均为 `Fraction`，不是固定 epsilon、角采样网格或浮点带。

`inflated_membership` **先执行原有 `_resolved` 和其内部自校验**，只在真实实体相触、`delta==0`、没有非零显式 band/window 时调用拓扑分类；没有绕过 G6H-06 的门和缓存路径。

一般凹入口块的 `shortest_exit3` 仍为既有局部盖政策。紧槽内点返回 `kind='exit', gap=0` 表示该局部政策，不声称该盖就是全局 `∂E`；接口 docstring 已明确这一边界。

## 30 格与独立交叉核验

新门覆盖：12 格精确旋转/尺度/大平移，竖直初态，零裕度/显式报告带，宽度 `1±2^-80` 与精确分界，真实 L 角外室及 `2^30` 剪切后的极窄外室，rank 1/2/3 球室计数与 `2^-200` 窄室，禁止生产调用独立 G0 oracle，以及 4 个内部变异守卫。没有删旧测试、放松断言、缩网格或添加 skip/xfail。

同团队另一代理只读交叉核验（**不是下一轮独立 G6 退出审查**）：

- [数学/逐探针审核](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/gate_teeth/topology3_review.md)
- [独立全部符号可行性证书](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/gate_teeth/topology3_chamber_audit.json)：通过 Fraction 高斯消元与 Gordan/Caratheodory 至多四点证枚举全部符号型，与生产球室集合完全一致；不共用生产几何原语。
- [独立逐探针证书](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/gate_teeth/topology3_step_audit.json)：按原面环 Newell 法向和源棱重建带符号配置平面，全部探针不跨非中央墙、不落墙；状态与独立区间并一致。U 槽 60 室全部内；L 角及其极窄剪切均 46 室、36 内/10 外。

## 真实内部变异：分别启动进程、目标断言原样报红

[重放脚本](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/initial_state/replay_mutations3.py) 在进程内注入真实被测路径，不修改磁盘源码，也不向函数返回之后追加伪造坏数据。各 JSON 记录三个生产文件的前后 SHA 相同。

| 内部变异 | 被目标门捕获的错误 | 原样结果 |
|---|---|---|
| `entrance3`：把入口的拓扑分类恢复为 `polyhedra_overlap` | `kind='entrance'`，目标断言应为 `'exit'` | [12 failed, 18 deselected in 0.99s](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/initial_state/mutation_entrance3.log) |
| `margin3`：把零裕度拓扑分类恢复为实体三态 | `0 != INSIDE(1)`，`zero-margin E topology mismatch` | [1 failed in 0.14s](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/initial_state/mutation_margin3.log) |
| `chamber3`：内部漏掉 `dx>0,dy>0` 的球室 | L 角误认内点，`narrow exterior chamber was lost` | [1 failed in 0.14s](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/initial_state/mutation_chamber3.log) |
| `step3`：删除非中央平面的局部步长上界 | 小尺度紧槽探针越过局部邻域，目标首入断言再次得到 `'entrance'` | [1 failed in 0.16s](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/initial_state/mutation_step3.log) |

重跑每个变异预期退出码为 `1`：

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -X utf8 reports/codex/R8FIX_evidence/initial_state/replay_mutations3.py entrance3
python -X utf8 reports/codex/R8FIX_evidence/initial_state/replay_mutations3.py margin3
python -X utf8 reports/codex/R8FIX_evidence/initial_state/replay_mutations3.py chamber3
python -X utf8 reports/codex/R8FIX_evidence/initial_state/replay_mutations3.py step3
```

## 冻结后绿与命令

新源/测试冻结后，新进程[独立跑 30 格](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/initial_state/green3d_final.log)：

```text
30 passed in 3.41s
```

同样冻结后的[新旧门合跑](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/initial_state/regression3d.log)：

```text
142 passed in 34.98s
```

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -X utf8 -m pytest -q -p no:cacheprovider tests/test_r8fix_initial_state3.py tests/test_entrance3.py tests/test_entrance3_exact.py tests/test_margin_exact.py tests/test_margin.py --basetemp=reports/codex/R8FIX_evidence/tmp/initial3_regression
```

仅在相触位形触发的有理平面/球室枚举有额外成本；此次合跑已经包含旧三维入口和裕度门。没有为性能跳过窄室或缩减配置平面。全仓耗时与最后一行由主任务正式全套日志统一报告，当前子报告不宣称全仓或 M0 退出完成。
