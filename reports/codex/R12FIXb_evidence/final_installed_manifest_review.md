# R12FIXb 局部过渡清单安装复核

复核角色：任务内分工复核（audit_design），**不是独立 G6，也不批准任何数值站点精确安全**。本轮只读 `src/tests/tools`，只向本证据目录写入复核产物。

## 当前结论与状态

- 最终 release 版共 **2365 条局部排除**，涉及 133 个文件、557 个作用域、1755 个唯一 AST；远超目标 200。它们是 root 显式决定的 `LOCAL_LEGACY_EXCLUSION_NOT_MACHINE_PROOF`，不是 2365 条“无先舍入再构造”的证明。
- 初安装版的字段/冻结回放机械检查通过；随后实际静态门仍报 **168 个位置**，原因是证据采集曾将实际 Call/Yield 错记成外层 Expr。机械检查只证明 AST 存在，**不等价于实际扫描命中同一 AST，更不等价于静态门绿**。
- 165 条严格父子绑定更正已由 root 显式采用，覆盖该 168 个实际位置；全部作用域源码哈希未变。[第二轮实际门日志](final_static_gate_r2.log) 为 `exact construction AST gate: 0 violation(s)`；此后五行 UTF-8 理由修复不改变任何诊断指纹或类别。
- 原“未完成数值动态改写”34 行逐站点复核发现过时理由；metadata 建议已采用，最终类别剩 **16 行**。不能再称“34 个独立实际动态调用”。
- 最终 release 的局部字段、全部原始 context、165 条限定 node 更正、39 条显式 metadata 更正、5 条 UTF-8 理由修复与 receipt 哈希均已只读复核通过，耗时 4.38 秒。证据见 [最终机械结果](final_installed_manifest_review_verified.json)。本复核时冻结全套仍在 root 运行，**不在此声称全套结果或 G6 通过**。

## 局部锁与回放机制

[机械检查](final_installed_manifest_review.json) 与 [可重跑检查脚本](verify_final_installed_manifest.py) 对初安装版确认：

1. policy 为 schema 2，不含全库 `dependency_snapshot` 或其他 dependency/snapshot 字段；每行具有非空 `id/path/function/rule/node/context/category/reason/review_evidence`，context 是 64 位十六进制 SHA-256。
2. 每个 AST 在其命名作用域中实际存在；每个 context 与当前 `site_contexts` 结果一致。重复的同限定绑定定义按候选组校验，不取最后一个定义覆盖前者。
3. 2365 条 policy 行逐字段等于已保存 ledger 投影，无重复标识或站点键，证据文件均存在。各行均不声称 reviewer 已批准 waiver。
4. [安装器](install_reviewed_local_manifest.py) 只读固定 ledger，当前 context 仅用于比较；落入 policy 的 node/context 直接复制已保存字段，不能因新源码变化而重算并续签。它不接受 raw scan 自动转 waiver。安装收据明确区分“比较时重算 context”与“更新已保存指纹”。

安装器只验证冻结记录可回放，不证明每条理由语义正确，也不能把排除目录自动变成安全证明。此次 metadata 与 Expr 绑定纠正正是额外人工核对的必要性。

最终 release 不是重跑旧安装器生成：root 使用 [一次性显式更正脚本](apply_reviewed_manifest_amendments.py) 对固定原 ledger/hash 和列举的 delta 操作，再用 [UTF-8 定点修复脚本](repair_review_reason_encoding.py) 修复 5 条损坏理由。两者保留原 ledger 历史；源 context 均不更新，未知新站点不能由这两个脚本自动加入。旧安装器只代表原安装历史，不应作为最终 release 的重装命令。

## 34 行动态类别的当前源码复核

逐项当前作用域/AST 源码及建议见 [suggested_metadata_corrections.json](suggested_metadata_corrections.json)。本复核不修改 policy/node/context。

| 原 34 行的实际情况 | 行数 | 建议 |
|---|---:|---|
| 原 map/lambda/注册表执行已经直接化，理由/类别过时 | 15 | 改为具体证明缺口、给定输入或近似诊断边界 |
| map(str)/join/write_text 是 CSV 序列化，非数值 callable | 3 | 改为结构数据/I/O 协议 |
| 当前仍有数值 callable 引用、传递或执行 | 14 | 保留未完成改写；其中 4 行去掉已经消失的 map(Fraction,p) 描述 |
| 当前仍有 getattr 读取数值 witness 数据 | 2 | 保留反射改写遗留，明确不是 callable 分派 |

root 已采用建议，此类别剩 **16 行（14 行 callable 引用/执行 + 2 行数据反射）**。这是规则行数，不是独立调用数；同一 `self(p)`、`poly(P)`、`P(...)` 或 `getattr(...)` 可同时触发两个规则。

特别纠正：`_margin_ref` 的 `norm(sub(c.point_a,c.point_b))` 仍是真实浮点差后取范数，当前仅用于容差下并列标签诊断；不得把动态 dispatch 已改写等同于这条数值表达式已精确。`_g0_exact_affine` 的 Fraction 运算也只精确保留已经由浮点三角函数/乘法生成的系数，不是理想实数运动的全程无舍入证明。

## Expr 提取错误的独立绑定核对

[fingerprint_binding_review.json](fingerprint_binding_review.json) 对 [165 条 delta](fingerprint_extraction_corrections.json) 全量检查：

- `before_node == 'Expr(value=' + after_node + ')'`；二者为当前源码同一语句的直接 AST 父子。
- path、function、rule、source、line 与已审记录相同，context 未变；after_node 与实际 scanner 的 issue payload 一致。
- [capture_actual_fingerprints.py](capture_actual_fingerprints.py) 仅在内存扩展诊断 payload 并临时使用空 waiver 获取原始报点，不修改 scanner 判定或磁盘 policy。

因此该 delta 是原站点的证据提取绑定修正，不是新增站点批准或作用域哈希续签。最终 release 再次核对这些 node 更正与每一个原始 context 一致。

## 最终安装统计与有限接线复核

| 排除类别 | 行数 |
|---|---:|
| 结构数据/协议审阅 | 276 |
| 输入模型/输出边界 | 639 |
| 人工保留的证明缺口 | 642 |
| 近似/名义诊断范围排除 | 467 |
| 公开诊断 callback | 5 |
| 测试执行/故意变异 | 320 |
| 未完成数值动态改写 | 16 |
| **合计** | **2365** |

附加发现并闭合的证据质量问题：中间版本新增的 5 条 source 理由曾因编码变为大量 ASCII `?`，不是显示问题。已保留中间文件历史；release 中这 5 条与 [明确 UTF-8 修复文本](src_reason_utf8_corrections.json) 完全一致，中文存在、`?` 和替代字符为零，node/context/category 未变。

root 最后的裸 construction 词汇接线也做了限定 5 格 [quick review](final_bare_construction_wiring_review.json)：未绑定的裸 `sqrt_rational` 按旧注入 API 视为 construction；参数同名仍 unknown 拒绝，本地同名定义仍按 defined/shadowed 检查，未知 namespace 的同后缀方法不被认作可信 intrinsic；Fraction 精确算术正向通过，`a=a.x` 的旧门准确回报 `closed-data-attribute`。这只是有限接线核对，不是扩大为任意 Python 的证明。

最终核对命令：

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -X utf8 reports/codex/R12FIXb_evidence/verify_amended_installed_manifest.py --ledger local_review_decisions_release.json --receipt reason_encoding_repair_receipt.json
```

最终 policy SHA-256：`73fde62383d7064ad94b58523a79586015c056b3bc57cea7ea0dd6d30a0abffe`。

最终 `local_review_decisions_release.json` SHA-256：`7e82233f0d0f1200306fbc4643b409ae1df9a7361a199aa79e7f39ce7a91b536`。

## 必须保留的交付边界

> 该版本是局部可失效的遗留排除清单，不是静态证明全库不存在“先舍入再构造”。静态门零违例仅表示在当前模型与显式排除之后没有剩余诊断；证明缺口、给定输入模型、近似诊断以及未完成动态改写均不因此变为数学保证。2365 条排除超过 200 条目标，最终只能报告 PARTIAL。全套绿亦不能替代独立 G6。

仅供历史追踪的原安装版 policy SHA-256：`5f119aecdc9e51d8af3a168d9854c32e415078225547fa33ef77a54defb49ed5`；原 ledger SHA-256：`48bc7cc77cea05d9592b6fad32e0e7c3ba2e8d1d68923e4265b1174ad15633a4`。这两个哈希和旧 receipt 不代表最终 release。
