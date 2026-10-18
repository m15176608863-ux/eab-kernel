# H1-fix：纯度、注释与冻结准入记账

## 处置

| 项 | 处理与边界 |
|---|---|
| m8 | 每个内核模块的 BFS 加自身父包作为起点。向副本 `contact_record.py` 注入适配器导入时，40/40 个内核模块均报告越界，包含无显式导入的 `eab.predicates`。 |
| m9 | 保留字母数字串、复数、下划线/驼峰与缩写小写拼接；词表补 legacy/zsto/lock_second/bolt/m4/m6/csv/slot/tuple7 及中文领域词。扫描 bytes、模块路径、match 关键字属性；常量拼接导入及 `sys.modules` 字面量也进入图。每类均由源副本注入断言把守，不向审计产出补假数据。 |
| m10 | 40 个内核模块之外，`eab/__init__.py`、`contact_record.py`、`numeric_decode.py` 纳入词法扫描，共 43 个。`joint_material` 仅保留既有契约字段及整数解码键两个站点；`slots` 仅豁免 dataclass 关键字；普通数学单词的 tia 子串误报有精确整词白名单。新同名变量、字符串均不豁免。 |
| m11 | 三个映射表适配器恢复来源说明；TF 注释恢复源码行号、码表、4/5/6 未核实及“审查盲区 5”的理由，修复 `test_tf_reader.py` 所引注释缺失。 |
| m12 | 清理公共记录的引擎/槽位说明，修正 affine fit 与重复顶点输入边界 docstring，删除搬家多余空行。7 个源文件去 docstring 后可执行 AST 均与 `476c5d6` 相同，无算法变更。仅 R12b-L0008 模块说明上下文需机械重钉，root 已独立补同站点/同可执行 AST 和完整策略逆投影核验。 |
| m13 | 19 个历史死键（imports 13、members 6）在重键 CSV 逐条标 retired；策略中保留，不新增、不删除准入。 |
| m17 | 补记 `test_int1_semantics.py` 单行导入从 `kernel2d.affine_motion` 到 `adapters.bdda2d_affine` 的重钉；函数源码不变，同一修改在三份历史插桩 review 出现，不是三次新修改。 |

## 验证

- 定向测试最后一行：`35 passed in 6.97s`。原 6 个节点保留，新加 29 个；精确清单见 [nodes.json](file:///D:/eab-wt/cx-e2/reports/codex/H1_evidence/fix_purity/nodes.json)。
- 删除审计器内部的父包 BFS 起点后：`1 failed in 0.96s`；红在 `assert reached == expected`，不是任意源码哈希或进程错误，漏项含 `eab/predicates.py`。
- 第一次定向静态如预期报告旧 R12b-L0008 上下文过期及其 tuple 调用，共 2 项，原记录保留于 validation.json；root 完成唯一说明文字 context 重钉后，8 个受影响文件静态为 **0 违例**，见 static_final.json。
- `geom.py` 基线已有 8 处 CRLF 混在 LF 中；本轮用字节替换统一 LF，AST 与 site_contexts 均不变。9 个编辑文件最终均为 UTF-8 无 BOM、纯 LF；字节哈希及修复前后证据见 comment_context_proof.json。
- 这里只运行定向门，不声称已完成全档或整库静态；由 root 收尾统一执行。
- 未写外部归档；未作 Git 写操作。旧重键 CSV/JSON 保存在本目录的 `*_v1.*`，原始搬家证明的适用版本明确为 `476c5d6`，不把它冒充新说明文字下的逐字节证明。

## 文件链接

- [纯度审计器](file:///D:/eab-wt/cx-e2/tools/h1_kernel_purity.py)、[纯度门](file:///D:/eab-wt/cx-e2/tests/test_kernel_purity.py)
- [公共记录](file:///D:/eab-wt/cx-e2/src/eab/contact_record.py)、[二维适配器](file:///D:/eab-wt/cx-e2/src/eab/adapters/bdda2d.py)、[三维适配器](file:///D:/eab-wt/cx-e2/src/eab/adapters/bdda3d.py)、[TF 适配器](file:///D:/eab-wt/cx-e2/src/eab/adapters/tf.py)
- [仿射拟合说明](file:///D:/eab-wt/cx-e2/src/eab/kernel2d/affine_motion.py)、[几何边界说明](file:///D:/eab-wt/cx-e2/src/eab/kernel2d/geom.py)、[路径证书空行整理](file:///D:/eab-wt/cx-e2/src/eab/kernel2d/model_robustness.py)
- [重键 CSV](file:///D:/eab-wt/cx-e2/reports/codex/H1_evidence/policy_rekey.csv)、[重键 JSON](file:///D:/eab-wt/cx-e2/reports/codex/H1_evidence/policy_rekey.json)
- [全部本子项证据目录](file:///D:/eab-wt/cx-e2/reports/codex/H1_evidence/fix_purity/)、[定向验证](file:///D:/eab-wt/cx-e2/reports/codex/H1_evidence/fix_purity/validation.json)、[最终静态](file:///D:/eab-wt/cx-e2/reports/codex/H1_evidence/fix_purity/static_final.json)
- [说明文字等价证明](file:///D:/eab-wt/cx-e2/reports/codex/H1_evidence/fix_purity/comment_context_proof.json)、[最终 context 逆投影证明](file:///D:/eab-wt/cx-e2/reports/codex/H1_evidence/fix_purity/context_update.json)、[19 死键](file:///D:/eab-wt/cx-e2/reports/codex/H1_evidence/fix_purity/stale_admissions.json)、[插桩范围说明](file:///D:/eab-wt/cx-e2/reports/codex/H1_evidence/fix_purity/instrumentation_scope_repin.json)
