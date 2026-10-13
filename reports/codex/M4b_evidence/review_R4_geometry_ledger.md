# M4b 独立审查 R4：几何 oracle、分类与冻结门

审查日期：2026-10-13。审查者：bdda_switch 子代理（未实现 eab 回放/分类）。
范围仅为 WO-M4b；不是全库 G6，也不是工程验证或 legacy/eab 可替换证明。

## 当前结论

分类/回放实现尚未发现 critical 或 major；中文台账交付历史发现 **1 major，已关闭**：
`docs/m4b_difference_ledger.md` 初次生成的中文在磁盘上大量变成字面 `?`，不是终端解码问题。
作者修复后，本审查再次直接读文件并检查：1063 个汉字、0 个字面问号，开头及全时程/投影说明可读。
证据：[文档独立复核](review_R4_document_recheck.json)。**剩余 0 critical、0 major、0 minor**。

## 独立性与度量覆盖

- 回放只把 `StepGeometry` 和显式 `d0/h1` 送给 M4a L5 `detect_step()`；
  legacy raw/post 两张表只在检测之后参与比较，不充当候选过滤器。
- M4a 的 `eligibility()` / `check_metric()` 使用独立 Fraction 邻边、点积、行列式、
  距离平方及严格半平面可行性；不调用生产 cover/cone/normal/project 原语。
  输入规范化与显式角窗系数是共享合同，不把这些读入约定误称为新独立几何证明。
- 每条 eab 盖在分类前都核身份、gap、法向同向/平行/单位长度和局部有效性；
  VV 重合点保留集值 None。raw/post legacy 快照没有直接 gap/normal 观测列，
  其规范化记录不伪造这些度量或当前锁态；不能据本门宣称全部 legacy 力学量一致。
- 闭集注册之外的类别必红；legacy 中 oracle 判有效而 eab 缺失者不是豁免，
  而是 `UNCLASSIFIED_EAB_MISSING_VALID_COVER`。重复主键原行有自己的分类和序号。

## 真实生产路径变异（本审查单独执行）

均在本审查 Python 进程内临时替换生产函数，未编辑生产源码、未在枚举后追加假数据：

| 缺陷注入 | 命中断言/原因 |
|---|---|
| `_boxes_may_meet` 恒 False | 步 1 有 53 个 `UNCLASSIFIED_EAB_MISSING_VALID_COVER`，闭集门红 |
| `_record` 的 gap 加 1 | `gap outside fit precision` |
| `_record` 的法向反号 | `normal direction reversed` |

证据：[逐反例记录](review_R4_counterexamples.json)。三个反例均命中所看护的缺陷断言，
不是碰巧依赖顶点顺序的无关断言。

## M4a 解释与冻结门

- `compare_m4a()` 先重现 M4a 冻结计数及逐差异哈希，再比较本轮 post-df06。
  分类逐 key 变化必须有相关顶点（含邻边）、相关 `d0/h1` 或该 key 的 legacy
  重数变化；不允许“其他无关顶点动了”成为整帧豁免。
- 每个变化 key 同时输出前后严格/放宽有效性与具体坐标/参数变化；分 key 的
  分类 Counter 必须重构全部计数。计数相同但键迁移也被记录。
- 15 个 30 步冻结夹具核每文件 SHA256、总类别计数、逐帧/逐差异哈希、前三步
  M4a 计数及变化 key 数，检查 450 帧覆盖与至少 14 个不同检测产物。
- 30 步前缀是明确的数据投影，不伪称原生产过程只跑 30 步；完整原时程证据另存。
  比较 oracle 证明的是该域窗中的局部几何条件，不证明 legacy 为何选此参考、
  df06 历史继承是否应改变、开闭/力/位移同构或真正替换可行。

定向回归原始日志：[21 passed, 15 deselected](review_R3_R4_targeted_pytest.log)。
全 15 族重算、全时程结果与新鲜导出全套结论由主报告汇总，不在本审查冒领。
