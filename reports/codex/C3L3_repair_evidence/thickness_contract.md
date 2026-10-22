# C3-L3 返修：T1b 厚度输入域与静力速度坐标合同

## 1. 结论及本次写域

本次新增 [持久厚度输入生成器](../../../tools/eab2_c3l3_thickness.py)、[测试输入摘要副本](../../../tests/data/eab2_c3l3_thickness_summary.json) 和本文，不改 `src/eab`、旧夹具或差分脚本，不提交 Git，也不自行运行全档。测试输入文件是既有仓内 [T1b 厚度冻结摘要](../../codex/T1b_evidence/acceptance_fix/thickness_summary.json) 的**原字节副本**，未重算历史证据、未修改原文件，符合测试输入放置于 `fixtures/` 或 `tests/data/` 的要求。生成器运行时只读该 `tests/data` 副本获得参数/阈值期望，只重建输入，不调用 LP、critical 或外部验收脚本。

39 个 T1b 厚度扫描条目中，**7 个完整模型可无损进入 binary64 ABI，32 个模型含非 binary64 精确输入**。另有 18 个厚块对照均在 ABI 域内。因此新 `thickness` 族含 **25 个来源条目、19 个唯一模型**：6 个 `r=3/16` 扫描模型与厚块对照重复，保留其来源身份，但不将重复项包装成新几何覆盖。

每条目给出 `mu={0,1/64,1/4}` 三个 limit 查询和一个 `mu_max=1,max_steps=64` 的 critical 查询，合计 **75 limit + 25 critical**。这些是生成器的查询计划与输入审计计数，不是本文自行认领的 C++ 差分通过数；实际结果以主 agent 的权威差分日志为准。

## 2. 历史原作者覆盖与外部验收覆盖必须分开

已经只读核对整个外部 `C3L3_acceptance.md`：

- 原 C3L3 工具/报告的 T1b 差分族覆盖 **36 个 morphology 参数模型**；它没有把 39 个 thickness 扫描条目或 18 个厚块对照列为当时已跑差分。因此不能事后声称原作者当时已经覆盖了本次 25 条目。
- 外部静力验收报告另列 **7 个 binary64 精确厚度样点 + 18 个重建厚块对照，0 failures**。这是 Claude 安排的外部验收所报结果，不是本次重新执行该独立检查器的结果。
- `run_thick.py` 从外部 archive 中筛选 7 个可表示的扫描模型；其遍历 `controls()` 时发现控制记录无 `assembly`，会跳过这 18 条。真正补齐 18 个控制模型的是独立文件 `run_thick_controls.py`：它只用 Python adapter 生成输入，再交外部独立装配/LP 检查器核 C++ 结果。
- `run_thick_controls.py` 导入 `run_thick.run`；原 `run_thick.py` 无 `__main__` 保护，因此导入时会再次执行 7 条样点，不能把这次重复运行加算为新的不同模型。

外部检查器路径只作为只读溯源，**不是本次持久工具运行依赖**。来源基址：

`C:/Users/m1517/AppData/Local/Temp/claude/C--Agent--claude/659f270b-c2f6-43a9-9717-6dc28c605be4/scratchpad/c3l3_accept/`。

| 来源文件（相对上述基址） | 本次只读 SHA-256 |
|---|---|
| `C3L3_acceptance.md` | `9b4a19a3861dcbc4ec339e6180653f00788da9c7c4f122b09bb6450b157b38d6` |
| `statics/work/run_thick.py` | `28b6987b40355cff4e23e210768e2dee47d6318d41e94a68307d16ae6b839841` |
| `statics/work/run_thick_controls.py` | `a7eec2ece4c32bd77a182127d8f95cc67260f2109c608c9a5d17ffcc995e2a9d` |
| `statics/work/thick_scan.py` | `05d774c54caab308fe79c700540d6c403b13cc3191390e91dd7714c0eff24af1` |

## 3. 可进入 ABI 的精确子集

模型继承 T1b 厚度工具的五块形貌、两端固定、中块竖向单位活载、无恒载。固定参数 `tilt=3/32,spacing=2,phase=0`，记 `r=h/spacing`、`a=A/h`，则输入生成用 `height=2*r,amplitude=2*r*a`。

筛选不是“ratio 是二进有理即可”，而是重建模型后检查**实际传输的所有原始顶点坐标、参考点、DOF 锚点、恒载、活载和 mu**。每个值 `q` 必须满足有限 `float(q)` 且 `Fraction(float(q))==q`。不对输入舍入、不缩放到近似替代几何、不将 Python 有理后端的输入域冒充发布 C ABI 的输入域。

| 扫描来源 | r | a | n | eta | 已来源的 exact_threshold | attained |
|---|---|---|---:|---|---|---|
| `thickness_00_07.json.gz` | 3/16 | 1/64 | 1 | 1/2 | 0/1 | true |
| `thickness_00_08.json.gz` | 3/32 | 1/64 | 1 | 1/2 | 253/16384 | true |
| `thickness_01_07.json.gz` | 3/16 | 1/128 | 1 | 1/4 | 0/1 | true |
| `thickness_02_07.json.gz` | 3/16 | 1/256 | 2 | 1/2 | 0/1 | true |
| `thickness_03_07.json.gz` | 3/16 | 1/256 | 2 | 1/4 | 0/1 | true |
| `thickness_04_02.json.gz` | 3/16 | 1/64 | 2 | 1/2 | 0/1 | true |
| `thickness_05_02.json.gz` | 3/16 | 1/64 | 2 | 1/4 | 0/1 | true |

18 个厚块对照为上述六种 `(a,n,eta)` 各取 `r={3/16,1/4,1/2}`；来源摘要每条均为 `exact_threshold=0/1,attained=true,certificate_arithmetic=true`。其中 `r=3/16` 六条已出现在 7 个样点中；只多出其余 12 个厚块模型。

排除示例：`thickness_00_00.json.gz` 的 `r=392183/4231168`，`block_1` 的 `vertices[1][0]=-405015579/135397376` 不能无损转成 binary64。生成器的 `thickness_inventory()` 列出所有 32 条排除项、失败字段数量与第一个实际失败字段。这些条目仍是有效的 Python 精确有理诊断输入，不是算例错误；只是**不在当前 ABI 输入域内**。本次没有移植其非二进有理输入接口。

本子集不证明连续厚度带或无限厚块范围：T1b 六族厚度解析边界及逐点认证来源见 [厚度带说明](../../codex/T1b_evidence/acceptance_fix/thickness_notes.md) 和 [既有具名门](../../../tests/test_tia2d_t1b_thickness.py)。厚块 18 点不能推广成所有 `r>=3/16` 或任意齿形的结论；UNBOUNDED 也不等于几何锁定或安全承载力。

## 4. 持久生成器与来源保护

运行时只需要本仓：

```python
from eab2_c3l3_thickness import thickness_cases, thickness_inventory
for case_id, assembly, queries in thickness_cases():
    # harness 接入 fresh_case(case_id, "thickness", assembly, queries)
    ...
```

命令行 `python -X utf8 tools/eab2_c3l3_thickness.py` 输出纯输入审计 JSON，不执行 solver。每个查询附 `thickness_source`：来源条目、六族参数、冻结摘要 SHA、来源 revision `e757883`、当前精确输入身份 SHA，以及已来源的阈值期望。`source_summary` 保留历史 `reports/.../thickness_summary.json` 来源路径，`input_fixture` 明确实际读取的 `tests/data/eab2_c3l3_thickness_summary.json`；前者不是运行依赖。critical 查询另外带 harness 需要的 `expected_threshold/expected_attained` 字段。

原摘要与测试输入原字节副本均为 39,519 字节，SHA-256 完全相同：

`64b39696af3b91b459726d6ac58515c7edc67264669196ada32216c35bb1a920`。

工具保护的是**冻结数据完整性**，不要求当前数学源码 hash 等于历史产生源码；这不是改历史 hash 让当前源码过门。输出模型完全由仓内 `g1_morphology` 以有理参数构造；阈值从已认证冻结数据的测试副本读取，绝不由当前被测 C++ 或 Python solver 临时计算成期望。差分中的 Python/C++ 求解与独立原始几何证书核验仍由 harness 完成，前后输入 hash 应从工具导出的 `SUMMARY` 实际路径取得。

此次另只读打开 `D:/eab-evidence/reports/codex/T1b_evidence/acceptance_fix/thickness_final/` 的 7 个对应原始 gzip，与摘要逐个验证 SHA；将重建后的各体顶点、body ID、边界类型、DOF mask、参考点/锚点和恒/活载逐项与 archive 相比，全部一致。又验证 `thick_controls.json.gz` 的文件 SHA、18 条元数据及其 UNBOUNDED 证书状态。没有执行旧扫描工具、没有重新生成全量历史证书、没有写外部 archive。

本次输入与只读回读的实际末行：

```text
C3L3_THICKNESS_INPUTS_OK samples=7 controls=18 outside_domain=32 source_entries=25 unique_models=19 limit=75 critical=25
C3L3_THICKNESS_ARCHIVE_READBACK_OK sample_geometry=7 sample_hashes=7 control_metadata=18 control_hashes=1 external_write=0
```

这两行仅证明输入域、来源、回读一致性，不是重新执行外部独立 LP 验收，也不是最终差分验收。

## 5. 静力 anchor twist 建议正文措辞

外部静力验收的信息项属坐标约定澄清，不是发现数值错误。建议主报告使用以下正文：

> 接触和荷载 wrench 先关于各体冻结的 `reference_point=o` 精确表达，再统一投影到独立 `dof_anchor=a` 的速度基；因此包括三自由度完全放开的体在内，LP 的转动平衡行实际上是关于锚点 a 的力矩，端板再按 dof_mask 保留自由行。`exact_y` 与 `mechanism` 是按这些自由行排列的 anchor twist，而非未经变换的 reference-point twist。这个约定与 Python 裁判一致；换参考点时接触与荷载矩共同变换，并不移动物理约束。C3-L4 消费 y 时必须保持同一坐标基或显式完成对偶坐标变换。

具体恒等式，设 `d=a-o`、`J(x,y)=(-y,x)`：

```text
M_a = M_o - d × F
v_a = v_o + omega * J(d)
v_o = v_a - omega * J(d)
F·v_a + M_a*omega = F·v_o + M_o*omega
```

这解释了自由体 `dof_anchor != reference_point` 时，求解值/状态与物理问题等价，但 `exact_y` 的平移分量不能直接当作 `o` 点速度。被约束锚点自由度填零后再变换，不能把被删行简单解释成另一参考点的零速度约束。无需为了文字逐字符合而修改生产实现，否则会破坏 Python 对齐和既有锚点合同。

THICKNESS_INPUT_CONTRACT_COMPLETE_NUMERICAL_DIFF_REPORTED_SEPARATELY
