# WO-PERF 保留审计

状态：PASS

- 基线节点 8267；当前节点 8582；旧节点丢失 0。
- 旧断言修改/丢失 0；旧函数非标记 AST 修改 0；模块语句/参数网格修改 0。
- fixtures 62 份，改变/缺失 0；新增 skip/xfail 0。
- exhaustive 标记函数 0 个。

详细节点、原断言 AST、阻塞项与命令见 `retention_audit.json`；当前收集原文见 `current_collect.txt`。

AST retention is deliberately stricter than semantic assertion strength; any flagged edit requires independent review. This audit does not execute assertions or prove production equivalence.
