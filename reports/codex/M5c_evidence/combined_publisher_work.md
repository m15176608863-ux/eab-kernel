# M5c 联合全时程证据发布器

状态：fresh R2 全 1810 步及研究 68 候选均已真实发布；冻结联合发布器已成功执行，最终专项 130 passed、0 skip、0 deselect。下文早期验证记录保留为过程证据，最终结果见末节。

## 运行

```powershell
python tools/m5c_publish_combined.py --name combined_final_r1
```

默认写 `reports/codex/M5c_evidence/combined_summary.json`，已有目标拒绝覆盖。进度保存在 ignored `tmp/<name>/progress.json`；中断后使用新 name，不能续接。

## 核验合同

- 纯标准库，不 import 生产几何/求根/证书/replay；不是第三次全对求根。
- 核验全部旧/新 case gzip 哈希，逐条比 64010 对的 key 与 P1/P2 status/features/time 精确 JSON 表达及 R2 分类。
- 独立读取冻结 endpoint shards 构造每一步真实 block ID 集，要求 raw 是其完整二组合；不是从 raw 自己反推块集合后自证完整。
- 研究 compact/exact 候选与 fresh 新接触 key 必须恰好同为 68；R2 通过标志、全局特征、R3 双路径生产证书、逐case统计一致。
- 所有 fresh/研究源码哈希首尾相等且符合当前字节；研究覆盖 fresh 完整源集合并包含诊断入口与 R3 内核；实际导入集合完整性另由 A7 独立 import-origin 门证明。
- 每候选逐phase替换 legacy_counts，但主参考/VV 二参/共边槽的物理总数不可变；已证与未证类别互斥，逐行命中与块对缺失/正式集合/全部槽答案自洽。
- 保留 full R2、candidate R2、candidate union、full combined 四个清晰口径，按case汇总仅 R3 新增证书带来的升级。
- 初态贯入群单独累加主/VV/共边记录计数，明确 **0 出口排序证书**，不把可读记录数写成出口命中数。
- 输入、源码、脚本自己在开始/结束均核验；不齐不发布，默认不覆盖。

## 验证

专项：`25 passed, 1 deselected in 0.94s`。仅暂排除等真实 combined_summary 出版的冻结门；不是全套收集=执行结论。新增测试生产静态扫描 0 违例。

合成反例修改相应外层文件哈希之后，仍在指定语义断言拒绝：错time/feature、旧流缺行、重复key、候选缺失、伪造同数量block IDs、研究物理参考总数增长、已证/未证类别残留、逐case计数不符、来源变更及已有目标覆盖等。

独立审查者 semantic_teeth 找到初版参考物理总数可增长及 raw block IDs 自证两处缺口，已补断言与修hash反例。未改动在跑 R2/R3 的任何冻结闭包文件。

## 冻结研究输入兼容复核

研究 bbF038/bbS038 三个零计数实际序列化为 JSON false（Counter 初次 update 的编码行为）。只在未绑定的 publisher 将这三个已知字段的 False 规范为整数 0；True、候选字段布尔值、浮点等仍拒绝，研究摘要与源均未改。68 个 exact 行重新独立累计与规范后的逐case统计完全一致，获证 19。修后专项 `36 passed, 1 deselected in 0.92s`，静态 0。

## 真实重算发布后的最终核验

完整 R2 已实际完成并发布（1810 步、15220 块帧、64010 对），15 个 worker 的 21 项源码首尾映射与父进程完全一致；旧 r1 作废且未拼接。冻结 publisher 实际执行成功并发布 `combined_summary.json`：逐对重核旧/新 64010 个 P1/P2 精确状态、特征、时间，68 个研究候选齐全，单首盖由 2 增至 19（净增 17）。所有绑定/联合及对应会计门含真实冻结产物全绿：`130 passed in 5.48s`，0 skip、0 deselect。

端点 29 项、稳健 21 项完整闭包门及最小例重算门均已执行，不再保留早期待发布剔除项。初态贯入 16676 对每阶段参考计数为主参考 81209、正式 VV 二参 2001、共边候选槽 19785；仍为 0 个出口排序证书，计数不代表出口命中结论。完整四分片收集=执行与静态总门由主代理最后发布。

可核验记录：`combined_publication_verification.json`、`combined_publisher_freeze.json`、`binding_combined_actual_r1.log`。
