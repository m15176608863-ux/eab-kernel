# M5a2 独立审查 R3 / R4（最终读回）

## 结论

**GREEN：0 critical、0 major、0 未关闭 minor；3 个 minor 已修复并独立复测关闭。**

只接受完整的 **baseline_suite_r2 + final_suite_r3**。本次终审没有重跑 pytest、没有改动源码；独立读取原始全局收集、派发清单、实际 collection 与 setup/call/teardown 记录，逐节点多重集核验，不只比计数或转述汇总。完整逐条结果、执行记录 SHA256、策略站点审查及反例保存在[同名 JSON](file:///D:/eab-wt/cx-e2/reports/codex/M5a2_evidence/review_static_runner.json)。

## R3：准入、回调与数值 inventory

1. 与只读 `git show 58733eb:tools/exact_construction_policy.json` 对照，旧 **3220 = 3103 + 117** 条 JSON 原值完全一致；schema、review_contract、imports、members 未扩张。
2. 新增 **170** 条逐一核验 AST 节点在声明函数体作用域内、完整 context 指纹精确匹配、理由逐站点说明；`static_admissions.json` entries 与 policy 新增尾部逐值相等。未发现整模块或通用 callable 的宽泛豁免。
3. **23** 条显式续审：旧 ID 原条目 SHA256 正确，新 context 对应当前函数；续审只退休旧 pin，不自动准入当前 AST。变更作用域与伪造旧哈希均有红门。
4. 涉及新增站点的独立 targeted scan **0 violation**；最终全仓库静态门也为 **0 violation**。
5. 15 种恶意/未知 callback 写法全部被拒，包括形参、属性、namespace、import alias、默认参数、容器/属性流、factory、partial、kwargs、stars、条件 alias、闭包、`__call__` 和模块级 lambda。factory 由 closed-subset 的其他规则拒绝，不声称所有写法由同一条规则识别。
6. 两个 `algebraic-comparator-site` 准入仅限 `RealAlgebraic.time` 的 `self.compare` 与 `scalar_algebraic` 内部符号反射递归。静态门不是任意 Python 动态行为的正确性证明。
7. 数值 inventory 的 10 个具名测试均存在；affine 精确构造、delta 坐标 L-infinity、orientation 充分非必要的口径与实现吻合。一般仿射首入和正残差首盖认证明确为 PARTIAL，未把端点诊断当作物理路径证书。
8. 最终 policy 已恢复原 LF 风格（CRLF 0、LF 38543），当前/执行快照 SHA256 均为 `bf474851e4630262d14cc118c8dc2b9d7656ddcd6f365d7c53a8e82f5e49820c`。终审重新核对旧 3220、新 170、续审 23；本次受审源码哈希未变化。

## R4：运行器缺陷与关闭证据

- 独立 runner 定向测试：**18 passed in 1.43s**，包括单测内部非终止、总步骤 deadline、非有限 timeout 拒绝、源文件增删改。
- 真正四进程最小 pass 探针：4 收集 = 4 执行、0 skip、GREEN；skip 探针：4 收集 = 4 执行、1 skip、RED。
- 新增文件反例：修复前，4 个调用全 pass 但增加 `src/added.py` 仍错误 GREEN；修复后重跑同一反例，`after_mismatches=["src/added.py"]`，**exit 1 / RED**。红来自完整快照集合检查。
- 最小探针的静态脚本只返回零，故它仅验证调度/记账协议；项目静态证据取最终全套真实扫描。

| ID | 级别 | 最小反例 | 修复与独立复验 |
|---|---|---|---|
| R4-01 | minor，已关闭 | nan/inf 绕过有限 deadline | run/plugin/CLI 全部验证 finite 且正；nan、inf、-inf、0、-1 在启动前被拒 |
| R4-02 | minor，已关闭 | 只核原 manifest，漏过运行中新文件 | 完整最终路径集合加共同路径字节；真实四片新文件探针 RED |
| R4-03 | minor，已关闭 | affine run-name 绝对/上级路径、workers 越界 | portable basename、resolve 后 TMP 直接子目录、workers 1..4；10 组非法参数全部 exit 2 |

## 完整四片原始读回

| 项目 | baseline_suite_r2 | final_suite_r3 |
|---|---:|---:|
| 全局收集 / 派发 / 实际收集 / 实际 call | 13254 / 13254 / 13254 / 13254 | 13360 / 13360 / 13360 / 13360 |
| 重复节点 / skip / fail | 0 / 0 / 0 | 0 / 0 / 0 |
| setup、call、teardown | 每节点各一次，全部 passed | 每节点各一次，全部 passed |
| 全目录导出文件数 | 5588 | 5941 |
| 导出新增 / 删除 / 字节变化 | 0 / 0 / 0 | 0 / 0 / 0 |
| 静态门退出码 | 0 | 0 |

基线四片最后一行原样：

```text
3314 passed in 804.77s (0:13:24)
3314 passed in 783.68s (0:13:03)
3313 passed in 801.20s (0:13:21)
3313 passed in 1435.18s (0:23:55)
```

最终四片最后一行原样：

```text
3340 passed in 772.64s (0:12:52)
3340 passed in 1325.65s (0:22:05)
3340 passed in 606.45s (0:10:06)
3340 passed in 928.20s (0:15:28)
```

两套静态门最后一行均原样：

```text
exact construction AST gate: 0 violation(s)
```

最终 export manifest SHA256：`7a8e117fa22f40e7bd9344fb433d0810e4e31559d24eee3a3c16b1a8604a2d71`；summary SHA256：`34ec25b633b84e94d831443686bf8d1e498f2832203568571e03312843ab86a8`。以上不只核 manifest 行：独立枚举整个目录，验证所有路径集合、长度和 SHA256；最终当前工作区非生成交付的 **5603** 个文件也与执行导出逐字节一致，无新增、删除或变化路径。

## 性能与诚实边界

- 最终比基线新增 **106** 节点、删除 **0**。其中 105 条 `test_m5a2_*` 直接 call 合计 **3.0613311999768484 s**；另一个新增 PROVENANCE 参数节点为 **0.0005473000055644661 s**。
- **全部 106 新节点** call 合计 **3.061878499982413 s**，相对基线全部 call **3558.873351800823 s** 为 **0.08603505090826213%**。`performance.json` 的 `new_gate_call_seconds` 按文件名前缀只统计前 105 条；这里明确补齐差集口径，不混称 106 条。
- 全套 call：基线 **3558.873351800823 s**，最终 **3370.4264257004106 s**；wall：基线 **1601.3730563999998 s**，最终 **1496.5159172999993 s**。主机并行任务未受控，不能把比值下降解释为受控性能优化证明。
- baseline_r1 因 180 秒单测 watchdog 正确报 RED，整体作废；baseline_r2 用 900 秒限制另跑。final_r1 审查中断作废；final_r2 因 policy 恢复原 LF 字节作废；**没有跨轮拼接结果**。
- 用户禁止新建 worktree，使用全新、不可变字节导出；明确 `fresh_git_checkout=false`，不冒充 fresh Git checkout。TEMP/TMP、pytest basetemp 和大节点/执行日志均在本工作树 `M5a2_evidence/tmp`。
- 本审查与主报告更新后，交付方须重生成 artifact_manifest；这是收尾的产物摘要刷新，不需要重跑测试或修改冻结源码。
