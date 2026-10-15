# WO-M5b 执行合同

- 目标：DDA 参数锚定轨迹、精确六次首入、严格模型稳定性充分证书与可复现证据；不满足者不计稳健结论。
- 范围：只修改 D:/eab-wt/cx-e2；其他工作树、b-DDA、理论正本只读。
- 非目标：不改姊妹求解器、不认定插值为真实物理路径、不将测试全绿等同 G6 验收；不执行 Git 写操作。
- 回滚锚点：执行前工作树干净，HEAD=df4f6f1950be09d6712afafc97ab312d30e03c57。原文件可从只读 Git 对象取回，禁止自动 reset/checkout。证据重发布前另存原字节。
- 成功判据：新主张有独立 oracle/语义变异/不变性门；端点证据绑定输入和代码；全套四片收集=执行、0 skip；静态门0违例；未完成部分列为 PARTIAL。
- 验证：`python -X utf8 tools/m5b_run_gates.py --name <fresh> [--baseline-head]`；所有子 pytest 带 `-p no:cacheprovider` 和显式 `--basetemp`。
- 临时目录：reports/codex/M5b_evidence/tmp，TEMP/TMP 同址；大日志和节点表只放 ignored tmp；长跑不续接。
- 新鲜验证：用户禁止 worktree/branch，沿用既有新鲜字节副本规则，明确不冒称新鲜 Git worktree。
- 并行责任：P2核心/端点重建/INT1遗留分工，主线程负责稳健证书、集成和完整验证。
