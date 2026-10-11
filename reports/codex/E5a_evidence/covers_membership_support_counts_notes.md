# 退化 facet 计数补门（技术留树，不恢复作废工单）

## 审计缺口与修正

初版两组旋转门迁移把错误的理想 `facet_degenerate=3/6` 固定值移除后，只核局部/全局严格面数量相同，未以独立精确计数替代退化面字段。这是实际门强度缺口，不能靠原台账文字消除。

本次只改 `tests/test_covers3_membership.py`：

1. 保留原 20 个逐顶点舍入的旋转输入、每格 `samples=60`、全部距离/最近标签/膨胀状态断言。
2. 新独立 oracle 直接读取原坐标，公共分母仅作精确整数倍缩放。候选法向穷举每体的全部点三元组及两体全部点对方向的叉积；精确支持集与仿射维数确定真正二维 Minkowski facet。没有调用生产凸包、canonical view、支撑或维数原语。
3. 实际 strict 标签经 canonical view 仅解码为坐标集合，与独立完整 strict 支撑集逐项相等；同时断言 `facet_local=facet_global=独立strict数` 和 `facet_degenerate=独立退化数`。没有只比两个生产计数的循环证明。
4. 追加 20 格：将完全相同的存储 R 元素看作 Fraction，精确应用共同可逆仿射映射，消除逐顶点舍入但不假称 R 精确正交。解析旧命题完整保留：四面体/方块 7 strict + 3 degenerate、13 极点；方块/方块 0 strict + 6 degenerate、8 极点；每格也有 60 随机样本及全部边界探针。
5. 真内部牙：编译实际 `facet_vote3` 函数，将其分类分支 `degenerate += 1` 改为 `+= 2`。原 `rep.passed` 仍为真，但独立新门在 `(实际 6, 期望 3)` 目标断言拒绝；不是返回后改 report，不添加假输出。

## 验证快照

- 首轮 `covers_membership_support_counts.json`：93 passed in 15.90s，wall 18.172s；记录 `tests/test_geom3_merge.py` 的并行收尾漂移，不当作冻结证据。
- 冻结复跑：`covers_membership_support_counts_frozen.json/log/xml`：**93 passed in 14.88s**，wall **16.853s**，`source_drift=[]`。使用既有 runner，`PYTHONDONTWRITEBYTECODE=1`，TEMP/TMP 和 pytest `--basetemp` 全部显式指向证据 tmp。
- 两条旧门迁移台账已补充本缺口、独立 oracle、20 个额外有理仿射格和内部牙。没有生产修改。
