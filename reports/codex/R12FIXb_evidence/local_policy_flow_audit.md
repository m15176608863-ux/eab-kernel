# R12FIXb 局部例外机制与一阶数据流独立对抗记录

审核对象：`tools/exact_construction_subset.py` 的局部锁与新增 `tools/exact_construction_flow.py`；本审核未修改数值模块，也未替作者修改 flow 实现。

## 1. 局部锁机制

- 删除全库 dependency snapshot；review 键仍包含 `path/function/rule/AST node/context`。
- `context` 是最近函数源码的 SHA-256（含签名、装饰器与函数内注释），不是整文件或传递依赖哈希。
- 嵌套函数使用自身源码；模块/类的非定义语句与子函数/方法分别锁定。改同文件其他函数不会让该函数 review 失效。
- 失效 review 显式报 `closed-stale-waiver`；把被豁免函数改写为安全代码或删除函数，也须人工清理旧 review，不会静默残留。
- 这是局部审查锁，不宣称把其他文件的行为永久锁定；跨函数数值保证必须来自当前源码的数据流分析。

机制测试：[test_r12fixb_maintenance.py](file:///D:/eab-wt/cx-e2/tests/test_r12fixb_maintenance.py)。

第一次定向运行（尚未执行真实仓库复制注释项）原样末行：

```text
8 passed, 1 deselected in 0.06s
```

日志：[maintenance_local_mechanism_pytest.log](file:///D:/eab-wt/cx-e2/reports/codex/R12FIXb_evidence/maintenance_local_mechanism_pytest.log)。这些绿节点内部实际要求：被修改函数的 review 红、另一个函数 review 仍绿、新禁止函数红、错误 AST 指纹红、安全重写后的过期 review 红。合成 review 仅用于测试匹配机制，不属于生产豁免。

## 2. 正向证明范围测试

[test_r12fixb_safe_subset.py](file:///D:/eab-wt/cx-e2/tests/test_r12fixb_safe_subset.py) 提供 8 类正向 × 2 源路径、4 类负向 × 2 源路径，共 24 个节点。正向覆盖 Fraction/int 算术与比较、Fraction 求和、已知纯函数、普通 float 展示运算、规范构造调用和一阶精确 helper；负向保留 float 派生经 helper 流入构造、Fraction 不可洗去 float 乘法来源、动态 callable 与未知 math 成员。

## 3. 数据流对抗：缺陷先实际执行，再要求静态门拒绝

[test_r12fixb_flow_adversarial.py](file:///D:/eab-wt/cx-e2/tests/test_r12fixb_flow_adversarial.py) 当前包含 20 种形态 × 2 源路径，共 40 个节点。

每格先执行构造了真实错误的程序，再使用独立 Fraction 中点平方不等式说明正确结果必须是最小次正规数 `u`，而程序因提前舍入返回 0；随后才断言静态门必须报红。oracle 不调用 eab 的几何或构造原语来决定正确结果。因而失败原因是静态门漏报，不是求解器顶点选择、异常或伪造产物。

| 轮次 | 实测漏报机制 | 证据与处理 |
|---|---|---|
| 1 | math 模块参数遮蔽、math 导入别名参数遮蔽、闭包数值捕获、可变容器 alias.append、break 后不可达重置 | 初始逐形态 `scan_text=[]`；作者首次修复后连同 continue/raise 配对形态，`14 passed in 0.09s` |
| 2 | break 后错误执行 for-else、条件内 break/continue 退出状态丢失、异常后错误执行 try-else、异常 handler 未接收前缀状态、带类型容器参数 helper 的副作用丢失 | 修复前：`12 failed, 14 passed in 0.22s`；全部失败在 `assert issues` |
| 3 | 嵌套默认值与模块默认值错误使用调用时环境、模块重绑定追溯改写旧快照、class 注解掩盖舍入 initializer | 修复进行中：`18 failed, 16 passed in 0.28s`；此前 helper 副作用已修复 |
| 4 | 函数、嵌套函数、class 重定义 math 导入时仍误用 math 纯函数摘要 | 修复前：`6 failed, 34 deselected in 0.12s` |

原始日志：

- [首轮修后绿](file:///D:/eab-wt/cx-e2/reports/codex/R12FIXb_evidence/flow_adversarial_pytest.log)
- [第二轮真实红](file:///D:/eab-wt/cx-e2/reports/codex/R12FIXb_evidence/flow_adversarial_round2_red.log)
- [第三轮真实红](file:///D:/eab-wt/cx-e2/reports/codex/R12FIXb_evidence/flow_adversarial_round3_red.log)
- [遮蔽轮真实红](file:///D:/eab-wt/cx-e2/reports/codex/R12FIXb_evidence/flow_adversarial_shadow_red.log)

## 4. 当前边界

作者完成上述修复后的独立定向复核（40 对抗 + 24 正反向子集 + 8 局部锁机制）原样末行：

```text
72 passed, 1 deselected in 0.33s
```

日志：[local_flow_review_current.log](file:///D:/eab-wt/cx-e2/reports/codex/R12FIXb_evidence/local_flow_review_current.log)。本次唯一排除项为依赖最终生产 manifest 的真实仓库复制注释测试。

本文保存审核过程中真实发现与原始红证据，不将中间红状态冒充最终结果。最终修复后 40 个对抗节点、真实仓库复制注释门与全套门，应以最终复核日志及主报告为准。此局部对抗检查也不替代仓库规定的完整 G6 六路里程碑退出审查。
