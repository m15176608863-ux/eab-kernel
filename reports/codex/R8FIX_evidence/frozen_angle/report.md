# R8FIX 分报告：G6H-02 / G6H-03 与同类构造扫描

## 范围与结果

- 仅修改本树 `src/eab/kernel3d/frozen.py`、`interlock.py`、`geom3.py` 的二面角函数，及 `src/eab/margin.py` 的冻结闭式、`margin_contacts` 构造段；未动姊妹仓库或 fixtures，未执行任何 Git 写操作。
- 新增 `tests/test_r8fix_frozen.py` 65 格、`tests/test_r8fix_dihedral.py` 37 格，共 **102 格**；既有测试没有删除、放松、跳过或缩网格。
- 最后定向运行包含上述 102 格和既有 `test_margin_exact.py` 13 格：`115 passed in 6.12s`。全套结果由主代理另行登记。
- 回滚锚：本证据目录的 `frozen_before.py`、`interlock_before.py`、`geom3_before.py` 保存修改前字节；其余以主代理全树基线为准。这些只是证据副本，不是运行时依赖。

## G6H-02：冻结 gap / jet / 逃逸高度

### 修前红

`before.log` 保存最初未修源码下的运行。大切向跨度 `M=10^20` 的独立 3-4-5 旋转区间盒，正确距离和冻结 gap 为 1，原 gap 为 `6662.338147750939`；交换 3/5 与 4/5 后为 `-6660.338147750939`。切向种子 `(-8e19,6e19,0)` 的正确导数为 0，原为 `4440.892098500626`。`M=10^8,gap=10^-9` 同样失败。

新门同时包含 VF/FV、VE3/EV3/EE、三个间隙/跨度输入、几何 rigid-rotation jet 和普通标量/零种子 Dual 的统一 lift。原第三方 lift 的纯标量 `5/8` 正确，但零种子 Dual 的 primal 为 `-8326.047684688674`。目标断言分别是 `frozen signed gap`、`exact rigid tangent derivative` 和 `Dual seed changed exact lift primal`。

### 根因与修法

原链条先构造单位法向 float，再用 Fraction 将这个**已舍入的显示向量**重新精确化；大切向杠杆将法向的舍入误差放大到 gap 和导数。lift 的非 Dual 支路使用精确未归一化平面，而 Dual 支路退回上述污染路径。

修复将面 Newell、EE 叉积及 VE/EV 投影残差拆为精确 raw jet；相对位移、点积、法向导数归一化修正均先用有理数形成。gap 及其导数只在最后对精确平方根表达式构造一次。法向显示仍兼容 tuple，但携带 raw jet 证书，直接传入 `frozen_gap` 不丢失精确原模型；调用方显式转换为普通 tuple 则表示提供另一个任意法向输入模型，这一路仍保留原来的自定义 n 契约。

`escape_height_from_frozen_cover` 的普通标量与 Dual 均走同一个 `-raw_gap/raw_nz` 有理比值模型，法向的朝向和归一化在计算前约掉。

### 修后与变异

- `replay_original_frozen.py/.log`：只调整第三方复现导入路径和期望方向，保留原几何/种子；原三组 gap 分别为 `1,1,1e-9`，切向导数全部 0，零种子 lift primal 为 `0.625`，导数 `(0,)`。
- `mutation_rounded_raw.log`：在 `_frozen_raw_normal` 内部把精确 raw jet 替换为已经归一化、舍入的 jet，之后仍执行真实生产点积/比值；**18 failed**，击中 gap/切向导数及 raw-plane ratio 的目标断言，不是枚举后伪造输出。
- 常驻 `test_raw_normal_rounding_mutant_is_caught_inside_frozen_gap` 保存上述缺陷的内部注入看护。

## G6H-03：可表达的极薄二面角

### 修前红与新门前提纠正

四面体的截面法向为 `(M+1,M)`、`(M,M-1)`，点积 `2M²`、按面遍历方向的三重积为 `+1`。独立真值是 `atan(1/(2M²))`，不调用生产 dot/cross/normal。

最初 `before.log` 共 60 failed，其中冻结相关 24 格是实际数学目标红；二面角 **6 格**在正确的角度断言红，另 **30 格**是新测试前提错误：对 `2^±400` 缩放直接调用 `manifold_issues()` 会构造超出 binary64 范围的体积，逆绕向后调用该检查又会报告预期的负体积。不能将这 30 格误记为修复证据。

只纠正**新增测试**的前提检查：全部尺度检查每棱双面遍历；单位尺度在反转前核 manifold/体积；保持全部 `6 M × 3 scale × 2 winding = 36` 角度格和目标断言不变。`mutation_old_dihedral.log` 随后在独立进程载入保存的**原始 dihedral_turn 函数 AST**，36 格全部在 `exact thin signed dihedral` 目标断言红；这是修前函数的真实重放，不是人工修改返回值。

### 根因、修法、结果

原函数先分别舍入两单位面法向，再叉积；`M≥10^8` 时二者相同，可表达的 `5e-17` 转角被清为 0。新函数直接由精确面法向和精确棱向量形成三重积、点积；以 `triple²/|edge|²` 与 `dot²` 同次缩放后构造 atan2 的两个参数。最终薄角、正负绕向及极端单位缩放保持正确。

`replay_original_dihedral.py/.log` 原 6 个 M 输入全部回放通过；常驻 `test_rounded_unit_normal_dihedral_mutant_is_caught` 重新安装原始“先单位化再点叉积”缺陷，目标断言报红。

## 同类扫描与额外修复

`scan_inventory.txt` 保存相关源码检索。实际检查覆盖冻结路径全部六种标签、面/EE/线残差 normal jet、margin 的两个差值出口、interlock lift 及 nominal candidate、geom3 angle/dihedral、二维 facet-gap 和三维 support-gap 构造。

### S02-a：冻结裕度的最终 delta 相减仍过早舍入

即使 raw gap 修复，`float_gap - delta` 仍会将 `distance=10^20+1, delta=10^20` 的正确余量 1 清为 0，导数也有同样问题。`scan_before.log`：2 failed，目标断言 `margin was subtracted after gap rounding`。

新增 `_normalized_difference(c, nn, delta)` 直接构造 `c/sqrt(nn)-delta`：先用符号和平方进行精确比较；通常只需检查一个 float 候选及邻点；严重相消时在 binary64 的有序位表示上最多二分 63 步，最后按精确相邻 midpoint 判定 ties-to-even。没有固定 Decimal 精度、绝对容差或“近零就当零”。所有解析导数减 delta 通道也使用同一最终构造。

测试覆盖正负无理数相消、精确零、上下溢、中间 gap/导数不可表达但最终差值为 1、半 ULP ties-to-even；冻结数学量下溢仍响亮抛错。`mutation_margin.log` 恢复“先舍入再减”后 2 failed，目标断言正确。

### S02-b：margin_contacts 的非零显示差也会相消

在初次源快照冻结后继续扫描确认：最近特征精确距离为 `10^20+10000`、delta=`10^20`，原代码返回 `margin_gap=16384` 而非 `10000`。此前仅 `gap==0` 才做共轭修正，漏掉已经非零但严重失真的差值。主代理收到发现后中止旧快照全套，再纳入修复。

`contact_margin_before_tests.log`：真实余量 `{-10000,-1,0,1,10000}` × 尺度 `{2^-200,1,2^200}`，修前 **6 failed, 9 passed**；六个红格是 ±10000 返回 ±16384 的对应缩放。修后直接用证书 d² 构造 `sqrt(d²)-delta`，15 格全绿。

保留旧门 `test_closed_is_exact_when_the_display_gap_underflows_to_zero`：该 API 是带 `exact_distance_squared` 证书的显示出口，显式允许显示下溢为 0，但 closed 分类独立精确；新 helper 的 `allow_underflow=True` 只在此出口使用，未放松冻结数学量的默认合同。

`mutation_contact_margin.log` 删除最终精确差值构造，在生产 `margin_contacts` 内部恢复普通先舍入再减：**12 failed, 3 passed**，均为 `contact margin rounded before subtraction` 断言；包括旧共轭修正原本能处理的 ±1 格，新增门至少保留此能力。

### 检查但未扩改的路径

- `geom3.angle_between`、二维 facet gap、三维 facet/support gap 已经由原始精确差向量/法向形成多项式后最后开方；本次未找到相同“显示法向重当精确原数据”的链条。
- `interlock._normal_noise` 已从精确棱叉积构造 sine。`_cover_escape_z` 仍是明确标注的 nominal reporting root，不决定精确 escape/membership；精确根由独立精确事件链返回，未把该报告近似升级为数学精确性声称。
- `margin_contacts` 的贯入哨兵 `0-delta` 没有两个大近量相减，不属于本次证实的相消缺陷。
- 这是有限静态检查和定向构造，不是全域几何/API 形式证明。

## 额外数值抽查与运行台账

- `pressure_difference.py/.log`：seed 8302，600 个有限选定的混合尺度输入，对照独立 Decimal precision=1600；569 个有限输出逐值一致，31 个不可表达结果正确报错。范围限定在脚本构造集，不能当所有 binary64 的形式证明。
- `after.log`：137 passed in 107.45s。该进程启动时包含最初 60 个新门和既有精确 jet/低维/互锁敏感性门；运行中源码增补了最终 delta 相减，Python 已导入模块不热更新，因此它只作为那个进程已载入版本的辅助回归证据，**不作为最终全套绿**。
- `after_final.log`：86 passed in 0.46s，包含原两条修复、S02-a 及其变异/极端输出门（在 S02-b 纳入前）。
- `contact_margin_after_tests.log`：**115 passed in 6.12s**，为本分工最终源码+测试下定向运行，包含所有 102 个新门与既有 13 个 margin exact 门。
- 额外两次 pytest 命令因误写不存在的 `test_margin_dual.py` / `test_margin_sensitivity.py` 路径而未收集；这是命令输入错误，随后按实际文件列表修正，未作为测试成功证据。
- 最终全仓耗时、最后一行、文档同步和残留以主报告为准。

## 复跑

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONIOENCODING='utf-8'
python -X utf8 -m pytest -q -p no:cacheprovider tests/test_r8fix_frozen.py tests/test_r8fix_dihedral.py tests/test_margin_exact.py --basetemp=reports/codex/R8FIX_evidence/tmp/frozen_angle_recheck
python -X utf8 reports/codex/R8FIX_evidence/frozen_angle/run_mutations.py rounded_raw
python -X utf8 reports/codex/R8FIX_evidence/frozen_angle/run_mutations.py old_dihedral
python -X utf8 reports/codex/R8FIX_evidence/frozen_angle/run_mutations.py postround_margin
python -X utf8 reports/codex/R8FIX_evidence/frozen_angle/run_mutations.py postround_contact
python -X utf8 reports/codex/R8FIX_evidence/frozen_angle/pressure_difference.py
```

变异 runner 要求内层 pytest 退出 1，外层正常退出表示成功检测到目标缺陷；不写生产源码，进程结束前恢复 patch。
