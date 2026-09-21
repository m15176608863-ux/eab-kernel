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

## 2026-09-20 · G2 三维同构门首次运行时的观察

### 3DDA（tf.cpp）—— 两条，第一条是**阻塞项**

1. **探针与 stage 文件都不带块体顶点坐标**，因此**无法重跑盖枚举做 G2 对账**。
   `retry_contact_pair_probe.tsv` 有接触点 (px,py,pz)、法向 (nx,ny,nz)、gap、contact_type，
   `contact_pair_stage.tsv` 有逐块对的 nn/ne/np/ee 计数——但没有几何，就无法独立枚举。
   **具体请求**：在 HeavyProbe 里加一份逐块顶点导出（块号 + 顶点号 + 坐标，步初一次即可），
   或在 stage 文件里补上每条接触的参考特征顶点号。有了它，三维枚举才能第一次被独立对账。

2. **三份夹具共 6716 条接触，100% 是 n-p，e-e / n-e / n-n 各 0 条**
   （smoke_cpu stage 5296 条、sandstone_fine 探针 864 条、sandstone_medium 探针 556 条）。
   两种可能，**在拿到几何之前无法区分**：
   (a) 这几个算例的几何就是如此（轴对齐块体的面-面接触在 DDA 里正是用多个 n-p 表达，
       eab-kernel 在 cb2 上复现的也恰是 4 个 VF 盖、零 EE）；
   (b) tf05 的展开**漏掉了交叉棱-棱**。
   若为 (b)，这是 legacy 三维枚举的一处实质缺陷。eab-kernel 在真正非轴对齐的位形上
   **能**产出严格 EE 盖（`test_wedge_on_wedge_gives_strict_crossing_edge_cover`），
   所以一旦拿到几何就能判。**这条把上面的几何导出请求的优先级抬高了。**

### 3-b-dda（bdda3d）

- G2 首次对账**通过**：cb2_locked / cb2_sliding / cb_bond 三例，legacy 4 条 / 内核 4 条，
  两个方向零差异，间隙与法向逐条吻合。这是三维接触枚举的第一份 legacy 对账。
- legacy 的 `np` 入口用**顶点三元组**指代一个平面，同一个平面会被不同三元组表示
  （cb2 里 (4,7,6) 与 (4,6,5) 并存）。对账必须把三元组归约到"它所在的几何面"。
- 入口里的 `area = 1.0`、`d1 = 16.0`（= 下块顶面全面积 4×4），与探针一样是占位/归一量，
  不是该接触的真实分担面积。
