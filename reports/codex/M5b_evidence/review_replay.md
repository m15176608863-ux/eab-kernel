# M5b 独立协作审查 R2：legacy配对、稳健分类与冻结

对象为主线程编写的 `tools/m5b_robust_replay.py`（r2预算版本）、相关接线门及冻结legacy输入；不是本人P2代码的独立验收。只读生产工具，新增一个测试驱动口径门；没有编辑正在长跑的源码闭包。

## 结论

- **critical：0。未处置major：0。曾发现major：1，已通过限制声称范围处置，完整功能仍PARTIAL。minor：0。**
- 全1810步两阶段原始参考→冻结主参考配对独立复核零失配。
- r2预算显式补P3自己的端点闭合误差，可覆盖说明中的三类连续模型及校正族。
- legacy结论仅针对**primary主参考**，次参考secondary未对账；无该限定就会产生错误“首盖未选”结论。
- 本审查不代替最终r2完整结束校验；完整64,010块对分类分布、源码/输入结束绑定及四片全绿必须由主报告引用完成的运行证据。

## R2-M1：次参考未统计（已限制声称，功能遗留）

既有M4c规则：当`raw[0]==1 and raw[4]>0`，tuple7后3项是第二条VE参考。当前`freeze_legacy`保留完整raw但只给primary规范标签，`legacy_counts`仅检查primary。因此可能出现：secondary恰是首盖、primary不是首盖，而`ROBUST_FIRST_COVER_NOT_SELECTED`仍加1。

最小独立接线例：`raw=[1,11,20,21,20,10,11]`；primary=`VE(11;20,21)`；secondary=`VE(20;10,11)`；名义稳健单首盖取后者。现有分类返回OTHER_REFERENCE=1、FIRST_COVER_NOT_SELECTED=1、MISSING_PAIR=0。

新增门 `tests/test_m5b_replay.py::test_legacy_ledger_is_primary_only_even_if_secondary_matches_first_cover` 固定此明确口径：**未选是未选作主参考，不是所有参考中未选**；已有pair不能误记pair漏检。主线程已接受主报告所有此类计数加primary-only限定、secondary列PARTIAL。该处置不是实现了secondary对账，不能声称缺口已补齐。

## 独立全输入配对复核

独立程序流式读取仓内tmp的原始`shadow.jsonl`，先核对历史来源hash。规范顶点ID使用**同块内相等坐标首次出现的ID**重建，未调用生产“尾两个别名映射前两个”的公式，也未import生产几何或读取器。

逐帧核对step序列、原始tuple7逐值相等、primary规范标签、block pair、header/requested_steps和terminal完成状态。结果见 [review_replay_checks.json](review_replay_checks.json)：

| 项目 | 计数 / 结果 |
|---|---:|
| 算例 / 步 | 15 / 1810 |
| raw_df05主参考行 | 141594，零失配 |
| post_df06主参考行 | 141594，零失配 |
| 每阶段带secondary的原始行 | 7768，当前未做secondary类别对账 |
| 全输入配对审查耗时 | 约0.51秒，不含求解 |

完整原始行仍留在冻结legacy输入，足以之后补次参考分类，不需回写姊妹库。

## 预算与分类只读审查

记`Delta(s)=P3(s)-P2(s)`，`e2=raw_end-P2(1)`，`e3=raw_end-P3(1)=e2-Delta(1)`。P2位置管界为`delta_all`；在s=1，时间律差为零，故`|Delta(1)|<=radius_l1*parameter_angle=delta_end`。r2使用

```text
radius = delta_all + max|e2| + delta_end.
```

于是`|P3(s)+s*e3-P2(s)|`由三角不等式被该radius覆盖。该额外端点项是安全充分预算，不声称最紧。P1和P2证书都支付同一保守半径，不能仅因两个名义模型状态相同就免去正误差。

读过 `model_robustness.py` 与其理论：双线性误差展开、全部非邻顶点的严格凸性、一般分母导数、两端异号/边内投影与竞争排除条件未见假稳健漏洞。这项是主线程代码的协作审查，不将其算作本人P2核心的独立门。

`MODEL_SENSITIVE_OR_UNPROVED`同时包括实测P1/P2差异和充分证书未知，报告必须分开。初始贯入没有正扰动出口排序证明时保守未证；这不意味着P1/P2/P3名义初态不同。

## 冻结完整性与运行状态

工具绑定全`src/eab/**/*.py`、自身及endpoint工具；输入绑定endpoint与legacy两目录全部文件。每worker前后及整批前后比较绑定；输出目录要求新建；每5步写未完成进度；总覆盖要求1810步/15220块帧/64010块对且三类分区守恒。输入读取器验证各压缩分片hash和行数。未见通过拼接中断运行发布complete的路径。

r1因预算变更作废；r2须真实重算，不能复用r1类别或只替换hash。审查时r2在运行，故这里不提前认证其最终计数。

运行接线门（TEMP/TMP均在M5b本树tmp）：

```text
python -m pytest tests/test_m5b_replay.py -q -p no:cacheprovider --basetemp=reports/codex/M5b_evidence/tmp/replay_independent_scope_review
7 passed in 0.17s
```

这些是literal期望的接线/口径门，不冒称七套独立几何oracle；全时程不塞入pytest默认耗时。
