# C1E 主报告模板：差分作者文档 QA

审阅对象：`reports/codex/C1E_evidence/finalize_report.py` 中的中文主报告模板，以及最终差分、生成器、规模测量 JSON。只读核验；本轮仅新增本文件，不修改产品、测试或工具源码。**这是实现作者对自己的交付说明作一致性检查，不是 Claude 指派的非作者独立对抗核查。**

审阅时模板 SHA-256：`3f492916c098768387abb7bcc3e506bfa2835a6c952cb98b85367ad72f0cbe7b`；根任务后续采纳建议修改证据模板不改变本次审阅范围。

## 已核对的数据

| 项目 | 最终证据值 | 核验来源 |
|---|---:|---|
| 命名/正式语料出现数 | 1763 | `diff_final.json::coverage` |
| 有序 binary64 输入去重后完成数 | 657（52 命名 + 605 正式） | `diff_final.json::cases` |
| 主语料双向层查询合计 | 100086 | 所有 case 的 `cpp_layer_samples_rechecked + python_layer_samples_reverse_checked` 求和 |
| 元门 | 17 | `diff_final.json::metamorphic`；flags 0–7 加 9 项变换/置换 |
| 零窗盖核验数 | 2530 | `zero_window_covers_checked` 求和 |
| E3 显式窗口 | 26 例 × 4 组 = 104 组 | `explicit_cover_window_checks` |
| 生成器尝试 / 合法唯一 / 完成 | 10079 / 10000 / 10000 | `generated_final.json` |
| 生成器双向层查询 | 322334 / 322334 | `generated_final.json::totals` |
| 生成器原始来源 / 独立局部扇区样本 | 13194 / 87200 | 同上 |
| 合成实际接触块对测量 | 55 / 55，MEASURED | `scale_final.json` |

原始末行一致：

```text
C1_DIFF selected=657 completed=657 mismatches=0 layer_queries=100086
C1_GEOMETRY_MUTATIONS mutants=3 semantic_kills=3 original_unchanged=1
```

## 两点措辞建议

1. **明确 100086 的计数分母。** 建议 §3.1 写成：“主 657 例的双向层样本核验合计 100086；不含 17 项元门、0 点发布批量查询或 10⁴ 生成器的查询。”现有数字无误，但裸写“总”容易被理解为整个工单所有查询总量。

2. **避免表头混淆两种 Python 计时工作量。** 建议 P2 表的 Python 列标题改为“Python 对应裁判工作量（见口径）”。正式语料的 `python_seconds` 从构造 `GlobalEntrance2` 开始，到 `python_export` 完成为止：包括 raw 排布、来源标签、紧凑 subdivision、逐层 topology 及 CONTACT 边界 topology 准备；**不包括**后续 `canonical/compare_exports`、clipped_covers/盖比较、local verify 或 DLL 反向查询。合成组装的 Python 列才是 `GlobalEntrance2` 构造加 `model.subdivision` 两段墙钟。两者都不含正式语料的 Python 慢 boundary，不能作为相同工作量的内核加速比。模板已有不计算严格加速比的限制，保留该说明即可。

## 其余结论

- 双方共同在 Python 中精确规范化、保留源标签分层、端点/孤立点，以及有向面边界重数消除人工竖直分片的描述与 `canonical/face_regions` 一致；未把有限采样冒充完整集合判等。
- 零窗和显式窗口检查确实比较 `strict`、`window_active`、来源 label、精确投影与距离 recipe、法向同向，不仅比较计数。
- `geometry2_local.cpp::local_origin`、`eab2_local_origin2_exact`、`verify_local` 等所述名称可定位；模板相对链接以 `reports/codex/C1E_report.md` 为基准未发现指向层级错误。CSV、交付清单与最终完整性文件为 finalize 阶段产物，仍应在生成后统一核链接。
- 三个 RN 后出现零长边的历史有理输入作为公开输入域排除，未伪装为合法例通过；非二进有理输入仅声称共同 RN 后的精确结果，表述正确。
- 报告保持作者验证、非作者核查、新鲜树复现三者边界，并以 PARTIAL 收尾，没有把作者变异门当独立核查。

结论：所审范围未发现需回滚实现或重跑数学差分的报告错误；上述两点是分母与计时范围的澄清建议。未修改冻结源码，未启动额外测试或全档运行。
