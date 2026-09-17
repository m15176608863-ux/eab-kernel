# 姊妹项目观察台账（只记录，不代为修改）

按 AGENTS.md §1.4：在姊妹仓库发现的缺陷或限制记在这里，由所有者转交。

## 2026-09-18 · Phase 0 读取器落地时的观察

### 3DDA（tf.cpp）
- `retry_contact_pair_probe.tsv` **不是完整接触列表**：只在重试事件时写，且只写涉及触发块/顶压板的接触（`pass 0/1` 两遍筛选，`record_limit = 1024`，tf.cpp:10842-10857）。用作 G2 同构门时，比较对象必须限定为同一筛选子集；完整计数走 `contact_pair_stage.tsv`（逐块对的 nn/ne/np/ee 计数）与 `solver_profile.tsv` 的 `content_xor64/sum64/ordered_hash64`。
- 探针的 `contact_type` 是 **候选类** `c[i][2]`（0 n-n / 1 n-e / 2 n-p / 3 e-e），不是 tf05 展开后的入口类 `m[j][2]`（只有 2/3）；`contact_entry = m0[i][0]` 才指向当前入口。两者不要混比。
- `area` 在 `o[i][3] <= 0` 时被替换为 1.0（tf.cpp:10880），`normal_force = ss·gap·area` 只在 `status_closed` 时非零——读探针时不能把 area=1.0 当真实面积。
- 三维接触枚举（tf04/tf05）目前没有任何独立对账通道（refkernel3d 只覆盖 K/F 装配）。eab-kernel Phase 2 将成为第一份。

### 导师线 DDA4.x（DDAKernel.cpp 4.5）
- `contact_topology_audit_output` 只产出**逐步汇总**（`DDA31::ContactTopologyStepAudit`：接触键 = (vertexId, edgeStartId, edgeEndId)，状态 = `m0[i][2]`，去重/无效计数，跨步差分），写进运行报告 JSON 的 `cross_step_contact_topology_audit` 字段；**没有逐接触导出**。eab 对它只能做集合级/计数级对账。若要逐接触对账需内核加导出——导师线不改，仅记录。

### b-DDA
- `bdda_debug_contacts.csv` 只有顶点号（p1..p3），块号只在 `bdda_debug_df18.csv`；两表必须按 (step, contact) 合并才能得到完整记录。首步 o3/o4 出现 1e-307 量级次正规数（未初始化残值），有限但无意义，读取器原样保留、不清洗。
- `bdda_debug_df18.csv` 同一 (step, contact) 可能多行（逐开闭迭代），读取器保留末行并记 `_df18_rows`。

### 3-b-dda（bdda3d）
- 入口 dict 无块顶点坐标；`tools/ingest_bdda3d.py` 一并导出 `ss.blocks` 顶点，读取器据 `refs` 还原参考点。
- 已知：`_accumulate_rank1` 的 `!= 0.0` 零跳过会丢 `v==0, e≠0` 分量的导数（设计文档 §一 第 4 条）；Phase 5 替换时处理。
