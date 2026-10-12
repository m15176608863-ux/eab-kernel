# R6FIX 首轮全套复核追加：BB52 稀疏 VE 变异门

## 复现与根因

主执行者首轮全套报告 `test_g0_exit_completeness_has_teeth[drop_VE_subset]` 失败：出口三条守护已通过，但旧距离期望 `584/603` 与现行有理仿射输入的 `603/603` 冲突。

单独重放修前门：[bb52_red.log](bb52_red.log)，`1 failed in 20.33s`，红在
`assert (r["g0_agree"] < r["g0_samples"]) == distance_gate_red`。

[诊断脚本](bb52_diagnose.py) 对**同一21块对×60次平移，种子0**比较两套实际输入；完整逐点坐标舍入差和19条距离见 [bb52_rounding_diagnosis.json](bb52_rounding_diagnosis.json)：

- 有理仿射输入 `Fraction(A)+Fraction(x)`：603个严格分离样本，`drop_VE_subset` 下0条距离缺盖。
- 原逐顶点浮点坐标像 `float(A+x)`：仍603个严格分离样本；使用**当前独立精确 oracle**，同一内核变异确有19条距离缺盖。
- 不是旧浮点 oracle 假红。首次反例为块对 `(1,3)` 的第0次平移 `(0.02990647328741916,-0.042836295079136916)`：真距 `0.052201262739241736`。有理仿射图像保留同距 EV(38,5)；旧浮点图像改变微平行关系，删 VE 后最短剩余盖是 VV(45,1)，距 `1.5326812226663322`。
- 把两套数据的盖冗余要求混为同一条不变量才是旧断言根因；不能恢复浮点真值、不能把19条真实缺盖撤掉。

## 修改（严格增加覆盖，不缩小原门）

`tests/test_bb52_g1.py`：

1. 原三组参数装饰器及 `distance_gate_red=True`、旧投票计数均不改。
2. 三个原出口守护全部不改；其他两种变异仍走原距离断言。
3. 仅 `drop_VE_subset` 分支添加 `_rounded_distance_audit`，每次完整跑原1260格，先形成历史浮点坐标像，再以零追加平移送入现行精确 G0 oracle。
4. **无变异控制组**强制 `draws/agree/samples = 1260/603/603` 且无失败，避免把 oracle 自身误差当作变异的牙。
5. **有变异旧浮点像**保留原 `distance_gate_red` 守护及 `584/603` 固定计数，新增完整失败清单必须恰19条、每条 `got > truth > 0` 且归因为真正“盖漏枚举”。
6. **有理仿射像**额外强制 `603/603` 且无失配，证明确实存在替代 EV 见证，而非距离门没采样。

`tools/bb52_g0.py`：**仅两处模块说明/注释更新**，把过时的“真值=polygons_overlap”改为现行独立整数/有理 oracle。**没有改 API 签名、任何参数默认值、采样过程、生产逻辑或返回字段。**

## 修后及变异证据

- 修后单case：[bb52_green.log](bb52_green.log)，`1 passed in 55.70s`。本次与变异进程并行，不能把此单次耗时当作隔离性能基准。
- 新步骤内部变异：[bb52_mutate_image.py](bb52_mutate_image.py) 在测试辅助函数**形成被测输入的内部路径**去掉逐顶点浮点舍入，错误恢复有理仿射图像，不在结果后添加假数据。
- [bb52_mutant_image.log](bb52_mutant_image.log)：`1 failed in 39.30s`，红在新增旧像的 `distance_gate_red` 守护；前面的无变异控制、原出口守护、有理仿射603/603仍过。这证明新守护真的区分应有的旧像缺盖，而不是依赖偶然断言。
- 整个 `tests/test_bb52_g1.py` 最终复核见 [bb52_all_green.log](bb52_all_green.log)；最后一行由随后实际运行追加，不引用修前全套失败计数冒充修后绿。

## 测试改写台账补充

这是给原门**增加第二套明确输入的完整网格对账和控制组**，不是将距离期望True改为False，也不是把584改成603后放行。原19条真实缺盖、原657个出口样本、原全部块对/平移/种子/容差、原退役投票对照均保留。额外运行只放在该稀疏VE case，不重复加到其他变异格。

## 最终关联复核结果（已完成）

命令：`PYTHONDONTWRITEBYTECODE=1 python -X utf8 -m pytest -q -p no:cacheprovider tests/test_bb52_g1.py --basetemp reports/codex/R6FIX_evidence/tmp/g0_bb52_all`。

完整文件最终最后一行原样：

```text
17 passed in 225.39s (0:03:45)
```

三个原变异参数格全部通过；没有 skip/xfail，没有缩小输入网格。此进程后段与主执行者第二轮全套部分重叠，仅作功能回归证据，不作为隔离性能比较。现在源码/测试/工具均冻结，等待主全套。
