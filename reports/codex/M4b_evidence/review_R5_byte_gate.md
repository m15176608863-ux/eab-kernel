# R5：M4b 字节证据门独立审查

## 范围与结论

审查者：shadow_replay 子代理；本轮没有编写或修改被审的 `tools/m4b_verify_byte_evidence.py`、`tests/test_m4b_byte_evidence.py` 与字节捕获器。仅审查 WO-M4b 证据门，不是全仓库 G6。

结论：**critical 0，major 0，minor 1**。当前实际证据支持所声明的 15 例 × 3 模式与两次改前基线逐字节一致；验证器本身只验证记录一致性，不能独立证明历史执行。

## 已实际验证

- 不依赖生产 `validate` 的比较循环，按每条记录的 directory 读取磁盘真实产物，独立重算 75 次运行 × 6 文件，共 **450 个文件**的 SHA256 和长度；全部与冻结矩阵一致。
- 家族为 15 例，每模式总默认时程 1810 步；三种 modified 模式齐全，baseline 两次目录在每例均不相同，baseline mode 实际全部为 unset。
- 原始矩阵经 `validate` 返回 GREEN。矩阵本体 SHA256 为 `7b983ec9bb5e0856cdeda055c4684482127c6ddffe7c882e052d9ff23c5770ad`。
- 工具不依赖可伪造的 PASS 标记，而直接核每模式逐文件摘要；测试通过实际矩阵结构变异覆盖 hash、缺模式、缺家族、短时程、步跳跃、输入哈希变化。
- eab 普通 fixture provenance 门另对矩阵本体字节冻结；回放夹具的源快照摘要已对最终 shadow 源逐文件独立核对。

机器证据：[review_R5_checks.json](review_R5_checks.json)。这里保留范围：磁盘读取复核在本轮确实执行，但没有重复求解 75 次。

## Minor R5-01：baseline 执行身份元数据并非完整 schema 门

对实际矩阵的内存副本进行两种变异，单独 `validate` 仍返回 GREEN：

1. 将第一条 baseline 的 mode 标签改为 shadow。
2. 将 baseline 第二条整体替换成第一条的深复制，即记录同一个 directory/command 两次。

这不推翻当前产物结论：真实基线模式和两个目录已逐条复核，冻结矩阵改动也会被 provenance 哈希门捕获；且验证器模块文档明确限定为“frozen evidence consistency; not a live solver rerun”。但不应把这个验证器扩张解释为证明两次独立执行或证明来源时间。未来可补 mode=unset、baseline directory/command 独立性校验；本次不把这种 provenance 元数据完整性建议升级成当前结果的 major。

## 剩余风险

- SHA256 相等证明给定文件字节一致，不证明接触模型的物理正确性。
- 原 exe/source archives 留在 b-DDA 专用工作树 build；eab 紧凑夹具只保存摘要，不包含可执行历史。
- 当前真实运行和文件均核验过；未来复用此证据时必须保持 source/hash 范围，不可把记录核验冒充新环境实测。
