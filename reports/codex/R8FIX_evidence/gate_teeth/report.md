# R8FIX 门失牙分项报告（G6H-05 / G6H-06）

## 结论与边界

已修两条确认发现，并同治 5 处 oracle 源坐标/编号信任缺口。只修改本工作树；未执行 Git 写操作。
本分项不声称通过 G6，不将定向绿替代全套/独立审查。全套结果由总报告给出。

- [有效修前红](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/gate_teeth/before_valid.log)：`9 failed, 4 passed in 1.55s`。
- [05/06及已有G0门](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/gate_teeth/after2.log)：`88 passed in 1.54s`。
- [新门、margin旧门和R7 G0](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/gate_teeth/more2.log)：`113 passed in 5.79s`。
- [追加两处修前红](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/gate_teeth/other_migrated_before.log)：`2 failed, 19 deselected in 0.79s`。
- [最终21新格及两旧测试文件全网格](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/gate_teeth/other_migrated_after.log)：`215 passed in 39.58s`。

## G6H-05：被测凸视图污染 oracle

**修前断言**：`test_g6h05_migrated_facet_gate_rejects_internal_convex_view_fault` 中
`with pytest.raises(AssertionError, match="raw-coordinate|stable-source")` 未抛出；5 格全报 `DID NOT RAISE`。
在 `exact_convex_view` 原编号保留分支内部删除最后一个真实极点（两格），或循环错置源面编号（三格）。未在枚举之后伪造产物。

**根因**：新完整 facet 对照虽然用了独立有理支撑算法，却先调用被测 `exact_convex_view` 来决定 oracle 输入；漏点和错编号已被当成真值。

**修法**：新增 `tests/e5a_convex_oracle.py`，从冻结原始坐标独立构造凸包/原编号保留条件/规范面顺序/源映射；只依赖独立的 `g03_exact` 有理凸包，不调用生产 `geom3` / `covers3` 原语。
`_raw_coordinate_views` 在任何被测 canonicalization 前保存两侧 oracle，逐项核实际极点顺序、facet编号和source映射；完整 facet 预期由独立模型产生。审查点名的3个稳定纯平移格另保留旧 `facets == base["facets"]` 断言。

**变异**：恢复HEAD修前共享oracle实现，目标新门重新 `DID NOT RAISE AssertionError`。详见[撤回修复变异](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/gate_teeth/revert_fix_mutations.json)。

## G6H-06：坐标噪声地板吞掉真漏盖

**修前断言**：`assert result.samples == 1 and not result.passed` 在 T=1e8、scale=1和8失败；margin对应 `pytest.raises(RuntimeError, match="missed the nearest pair")` 两格未抛出。
原点及T=1e3已能抓同一内部 `_outside_dot_band` 拒绝z盖缺陷，工程坐标下却放过10倍错误距离。

**根因**：把精确特征完备性与浮点显示构造误差混为一票；无论atol=0仍加全局坐标噪声。

**修法**：
1. `g03_surface_oracle.separated_distance(..., squared=True)` 保留独立整数/有理全部特征最小平方距离。
2. G0枚举实际折面表面，取得被测候选精确平方距离，与oracle严格等号比较，记入 `completeness_failures`；单独保留原浮点见证容差票，记 `construction_failures`。任一红则 `passed=False`，不删除旧构造/非有限检查。
3. `geom3.brute_feature_distance(..., squared=True)` 暴露生产全特征精确平方证书；margin以它和最小盖证书精确比较，另保留 `4*rounding_floor` 浮点见证票。
4. 旧显式窗口的源环标签可能不是折面上的精确最近特征；把原来已有的actual-surface minimum步骤移到self-check之前，未放宽或跳过完备性票。该生产brute与被测层共享原语，仅称自校验，主G0 oracle仍独立。
5. 同显示值但精确证书不同，诊断明确为 `exact squared-distance mismatch`，不误说仅显示见证偏离。

**变异**：分别删除G0的exact-completeness票和margin的exact票，目标断言分别报
`exact nearest-cover completeness must reject missing z covers` / `DID NOT RAISE RuntimeError`。
[变异源码/断言/前后SHA](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/gate_teeth/revert_fix_mutations.json)。

## 同类扫描：5处补门

全仓搜索所有 `exact_convex_view` 对oracle输入的使用，并读取 E5a / E5a2 / E5b 的80条迁移汇总（覆盖23个文件）。
另记录E2迁移计划3文件，其不在本分项改写范围。静态盘点不是任意变异等价性证明。
[迁移库存与审查边界](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/gate_teeth/migration_inventory.json)。

| 追加项 | 路径/具体门 | 修复与牙 |
|---|---|---|
| S1 | `test_invariance_geom::test_support_gaps_scale_and_membership_is_invariant` | expected支撑间隙转独立raw model；删极点/源面错序均红；b612旧新两格均红 |
| S2 | 同文件 `test_g0_three_votes_are_invariant` | 计数对照改raw model并核source编号；删极点旧新均红；错源面旧绿新红 |
| S3 | 同文件 `test_vote_two_ambiguity_band_is_pinned_on_the_generic_cells` | 同治raw model；删极点旧新均红；错源面旧绿新红 |
| S4 | `test_covers3_g0_vote2::test_yawed_stack_passes_g0_under_random_rotations` | 规范编号内部循环错位时，HEAD旧迁移门同错绿；新增回归先红，独立raw model修后绿 |
| S5 | `test_frozen_ee_sign::test_frozen_ee_orientation_agrees_with_ee_cover_and_facet_normal3_on_every_ee_pair` | 在凸包构造内部删真实极点，HEAD旧迁移门同错绿；预期EE边集/Gram/法锥只用独立raw hull，新回归修后绿 |

`test_covers3_membership::_assert_exact_facet_counts` 从原坐标独立产生expected，再用tested view只解码actual，不是共享expected；`_assert_exact_rotated_vote_counts`另有raw-support和独立E顶点票交叉检查。缓存隔离门中的tested view是明确被测产物；integer-arithmetic的Fraction路径是算术等价性对照，不冒充独立G0；其余pure construction的tested view使用不属于本缺陷。

## 与 b6126cf 的实跑对照

[22组原样日志](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/gate_teeth/old_gate_comparison.log) / [逐断言JSON](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/gate_teeth/old_gate_comparison.json)。
所有22组的未注入新旧baseline均PASS；拒绝仅以AssertionError或G0的`passed=False`计，不把TypeError/ImportError/接口不兼容当杀死。

- G6H-05：删除真极点2格 + 源面错序3格，新旧均红。
- S1/S2/S3：共6格，新门全红；旧门4红2绿（两条纯计数旧门不能看源编号错）。
- G6H-06：T=0、1e3旧新红；T=1e8旧绿新红。旧G0的坐标地板同样存在，修复是加强，不虚称该角落旧门有牙。
- G2迁移：`_qvertex_contains` / `_qedge_contains` 恒边界内部变异 × 3 fixtures，共6格，旧新断言均红。
- 位置不变性：内部棱向量忘减端点 / facet gap忘位移2格，新旧均红。

另追加[2组HEAD对照](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/gate_teeth/other_gate_comparison.json)：S4/S5 baseline旧新PASS，变异HEAD绿、新红。
S4在b612的理想degenerate=10断言对当前精确舍入语义baseline已红，**不计有效旧牙**；S5文件当时尚不存在，明确记UNAVAILABLE，改用HEAD30ee153对照。
这些实跑覆盖上述故障族，不声称80条迁移对任意内部变异已全部等价。

## 测试改写台账与中途失败

[6个既有测试函数改写全文、断言数量、装饰器审计](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/gate_teeth/test_rewrites.json)：旧参数装饰器逐AST相同，没有删除函数、缩网格或新增skip/xfail；只替换被污染expected并追加raw/source身份检查。

- 最初 `before.log` 的G6H05注入helper误patch不存在alias导致AttributeError，不计有效修前红；修正helper后从只读 `git show HEAD` 原内容临时恢复本任务自己编辑的测试，运行 `before_valid.log` 再恢复当前内容，得到真正目标断言红；06原生产代码当时尚未改。
- `related.log` 是修改过程中大子集，不作终态证据：18红来自显式窗口actual minimum步骤顺序，已修；1红来自运行中源码改行使inspect读错函数。随后body-distance385格全绿，主门子集113绿，追加全文件215绿。最终全套必须由总报告冻结快照后重跑。
- 不改变fixture，不声称新鲜git worktree验收（本工单明确禁止worktree）。

## 重跑

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -X utf8 -m pytest -q -p no:cacheprovider tests/test_r8fix_gate_teeth.py tests/test_covers3_g0_vote2.py tests/test_frozen_ee_sign.py --basetemp=reports/codex/R8FIX_evidence/tmp/gate_teeth_rerun
python -X utf8 reports/codex/R8FIX_evidence/gate_teeth/compare_old_gates.py
python -X utf8 reports/codex/R8FIX_evidence/gate_teeth/compare_other_gates.py
python -X utf8 reports/codex/R8FIX_evidence/gate_teeth/revert_fix_mutations.py
python -X utf8 reports/codex/R8FIX_evidence/gate_teeth/audit_migrations.py
```

本分项完成；总单的6项修复、其它同类发现、文档同步、全套和独立G6退出边界以总报告为准。


## ????????????????R8 ???????

????????? `105 failed, 9977 passed in 404.70s` ? 105 ???? JUnit ?????
`test_margin_layer_is_invariant` ? `contact.margin_gap == contact.distance - s*delta`?
??? `box_box_face/R7/t0/s0.001`?EE ?? `(0,1)/(5,6)`??? distance
`5.000000000000007e-05`??????? gap `-4.999999999999995e-05`?
**????? distance ??????????????????? sqrt(d?)**????????
???????????????? equality ?? tolerance??????????

??????? oracle?
- `e5a_cover_oracle.witness_points(exact=True)` ??? Fraction Gram ?????????????????
- `margin_witness_squared` ????????????? + point/triangle ???????????????????
  ????? `_witness_squared` / `_normalized_difference` / sqrt?????????? label ????? label?
- ??? `margin_selection` ????????????????? `exact_distance_squared`?
- ?? gap ??????? binary64 ??????? RN-even ????
  `sqrt(d?) ? delta+midpoint` ??????????????????? gap???????ties-to-even?
  ???????/????????? sqrt/Decimal ?????
- ? 385 ??????/????/??/????/???? closed ????????
  ??????????????????????????????????????????????

???
- `margin_rounding_after.log`?`385 passed, 2021 deselected in 64.78s (0:01:04)`?
- `margin_rounding_teeth.log`??? 18 ? + ?? R7 margin oracle?R8 gate/frozen ?
  `108 passed in 3.92s`??? 10 ??????????? half-way ?????? signed-zero?
- `audit_margin_gap_migration.py` ?? compile ?? `margin_contacts` ????????
  `gap=w-delta`?`gap=w`?`gap=w+delta`?`gap=2*w-delta`?????? records?
  ?????? `10^20+1-10^20=1` ???? 4 ??8 ?????
  `AssertionError: exact margin-gap midpoint`??? traceback ? `margin_gap_mutation_tracebacks.log`?
  ?? `w-delta` ????????????????????/??/???????????????
  ?? clean baseline ?????????????????????**????? baseline ?**?
- `margin_gap_migration_comparison.json` ???/???????? src/tests ???? SHA256?
- `test_rewrites.json` ?? **7 ?**?????????????????????? AST?????????
  ??????????????????? skip/xfail?????????????????????????
