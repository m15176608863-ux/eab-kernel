# INT1 R1：真实回放与发布协议独立复核

审查者：theory_docs 子代理；未编写或修改两套回放编排。对象为最终 **motion_refresh_r2 / se2_revalidation_r2**；r1 不作为本轮最终证据。

结论：**0 critical、0 major、0 open minor**。机器结果见 [review_replay.json](file:///D:/eab-wt/cx-m4/reports/codex/INT1_evidence/review_replay.json)。此结论限定回放/发布协议，不替代整单全套与其他路线审查。

## 方法与实际读回

1. 逐行审阅 `tools/int1_refresh_motion.py`、`tools/int1_revalidate_replay.py`，并穿透读取其复用的 `m4c_run_replays.validate_case_files`、`m5a2_revalidate_replay.compare_rows/main`、底层回放文件的读写与输入闭包检查。
2. M4c：重新解压最终 r2 的 15×30 帧，与 `fixtures/m4c_motion/expected.json` 指向的历史 normalized 文件逐 JSON 值深比较。**450帧全部相同**；另查每案 audit、帧摘要序列、counts/secondary/stats/input_hashes，与历史逐字段相同。
3. M5a2：只读 cx-e2 旧验收 `revalidation_r1` 的 15 个 normalized 文件，先核其 SHA256 等于本单最初字节副本中的旧清单，再与本单 r2 实际产物逐值深比较。**450帧全部相同**；counts、stats、steps、先前获准的时间证书表示差异路径列表也逐值不变。底层 runner 另对 M5a 原冻结逐叶比较，唯一特许是 rigid.time 经独立 oracle 证成同一个精确实数，不能豁免其他字段。
4. 比较当前与初始新鲜字节副本的全部 **218个 fixtures 文件**：仅 `PROVENANCE.json` 与 `m5a2/revalidation.json` 两文件变化；历史 M4c/M5a 输入和冻结夹具没有变化。
5. PROVENANCE 共 **217条**；仅既存 `dest=m5a2/revalidation.json` 的一条变化，变化字段严格是 `source / bytes / sha256`。其他所有条目及顶层值逐值不变；新 bytes/hash 与实际清单一致。
6. M4c 摘要的 `m3c_refresh` 与 `m5a_revalidation` 均与本单初始副本逐值相同；新增 `int1_refresh` 指向本轮重算与回退锚。最终摘要与 r2 实际原始目录 summary 的 SHA256 一致。
7. 两份最终产物的生产源码闭包均等于当前文件；M4c 另绑定本单 wrapper 与旧 batch 验证器；M5a2 同时核旧 runner、独立 oracle 和本单 wrapper 哈希。所有输入闭包当前哈希一致。

## 先比较后发布、失败处理

- M4c 子进程全部结束后逐案验证，再逐帧深比较，核全450帧与源码/旧夹具稳定，才发布摘要。不同即抛错，目标摘要不会被“改哈希”抢先刷新。
- M5a2 既有 runner 的候选 manifest 重定向到本单 ignored tmp；完成450帧、历史逐叶比较后，再对旧 M5a2 normalized 哈希与语义统计比较；全部相同才发布目标和对应 PROVENANCE 单行。
- 新目录 `exist_ok=False`、已有备份/候选拒绝复用；长跑写独立 progress。重跑 r2 使用新名，从头重算，没有把 r1 片段拼入 r2。
- 同目录 `.writing → replace` 保证每个目标文件独立原子替换。**manifest 与 PROVENANCE 两个文件不是一个事务**：若两次替换间中断，哈希门会报红，必须用备份/新鲜整轮恢复，不能宣称已完成。哈希前后检查也不是针对恶意并发写入者的锁。

## 审查发现与闭合

| 级别 | 初查发现 | 最终处理与复核 |
|---|---|---|
| minor | r1 M4c docstring 写 atomic，但旧 `write_json` 是直接 write_text | r2 改为同目录原子 replace；读取实际实现确认。 |
| minor | r1 新 wrapper/M4c 验证器未包含在编排哈希证据 | r2 添加前后编排哈希并入产物；两套450帧均完整另名重跑。当前字节核对通过。 |

上述 minor 均已闭合；未发现要求推翻最终 r2 数值对账或旧夹具保护结论的缺陷。

R1_REPLAY_REVIEW_PASS
