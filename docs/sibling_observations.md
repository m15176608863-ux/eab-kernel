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
   - **补注（2026-09-24）**："6716 条、100% n-p"这个数字现在由测试重算看护：
     `tests/test_tf_reader.py`（`test_tf_census_recomputed_through_the_readers` 等；stage 5296 + fine 探针 864 + medium 探针 556）。
     状态码映射的依据问题见下文 2026-09-24 一节。

### 3-b-dda（bdda3d）

- G2 首次对账**通过**：cb2_locked / cb2_sliding / cb_bond 三例，legacy 4 条 / 内核 4 条，
  两个方向零差异，间隙与法向逐条吻合。这是三维接触枚举的第一份 legacy 对账。
  - **订正（2026-09-24）**：这句的分量要打折。三例的块体几何逐点相同（2026-09-24 用 `tools/g2_bdda3d.load_case`
    读三例比较顶点集，全等），所以实际只是**一种几何、只有 VF 类**的对账；而且当时 legacy 侧的三个 JSON
    没有进 `fixtures/PROVENANCE.json`，改一个字节"零差异"也不会失效（09-21 审查盲区 3）。溯源已补，见下文。
- legacy 的 `np` 入口用**顶点三元组**指代一个平面，同一个平面会被不同三元组表示
  （cb2 里 (4,7,6) 与 (4,6,5) 并存）。对账必须把三元组归约到"它所在的几何面"。
- 入口里的 `area = 1.0`、`d1 = 16.0`（= 下块顶面全面积 4×4），与探针一样是占位/归一量，
  不是该接触的真实分担面积。

## 2026-09-24 · M0 收尾时的观察

### 3DDA（tf.cpp）—— 接触状态码只有一句注释作依据

- 读取器 `contact_record.TF_MODE` 把 tf.cpp 的接触状态码 `m0[i][1]` 翻成统一词汇，**唯一的依据**是 tf.cpp 里 `m0` 数组声明上方的注释：
  `0 open 1 friction 2 s-spring 3 t-tension 4 2f-friction 5 2f-lock 6 top-lock`（tf.cpp:306-313；
  2026-09-24 在 `C:\3DDA\3d-DDA-work\tf.cpp` 工作副本上只读核对，行号对得上；未做 git 操作，故修订号未记录）。
  这条引文此前没有登记在本台账里。
- 因此 4 / 5 / 6（2f-friction、2f-lock、top-lock）现在标 `Mode.UNVERIFIED`，不再断言折进 SLIDING / LOCKED，原始码保留在 `raw_mode`
  （`tests/test_tf_reader.py::test_tf_mode_states_4_5_6_are_unverified_not_asserted`）。入库的三份夹具只出现状态 1、2
  （`test_tf_fixtures_never_exercise_states_4_5_6`），所以这一改不改变任何现有记录。
- 0–3 的映射（尤其 2 "s-spring" → LOCKED）同样只靠这句注释，没有更硬的依据。
- **要解除 UNVERIFIED**：需要引用 tf.cpp 里开闭迭代中**给出这些状态码的代码行**，说明 "2f" 与 "top" 在迭代里到底指什么。由所有者提供或确认。

### 3-b-dda（bdda3d）—— 三个导出 JSON 已进溯源，但来源仍有两处不明

- `fixtures/bdda3d/` 的三个 JSON 现已在 `fixtures/PROVENANCE.json` 里按哈希看护（c1326a0；
  `tests/test_fixture_provenance.py::test_every_fixture_file_is_hash_gated`、`test_bdda3d_gate_has_teeth`）。
  哈希是按 b74a3a2（2026-09-18）入库的字节**补登**的，没有重跑导出（M0 纪律不许运行读姊妹仓库的脚本）。
- 仍不知道的两件事，PROVENANCE 条目里如实写着（`test_bdda3d_provenance_states_what_is_and_is_not_known` 只看护第 (1) 句
  "版本未记录"还在；第 (2) 句目前只是条目文本，没有门）：
  (1) 导出时 3-b-dda 的**修订号没有记录**；
  (2) 入口列表是 `detect.py` 的**枚举产出**，还是算例里**预置**的列表，**未核实**。
- 下次重跑导出时把这两件都记下来。
- **导出里分不出 locked 与 sliding**：`fixtures/bdda3d/cb2_locked.json` 与 `cb2_sliding.json` 逐字段比较，只有 `case` 名不同
  （几何、入口节理参数全同），三份 JSON 都没有荷载/驱动字段（2026-09-24 用 json 逐字段 diff 复核）。
  计划 M1 的"cb2 夹具的 sliding/locked 判决"因此做不了，除非重新导出时带上荷载或状态差异（`docs/plan_20260921.md` M1 订正）。
  **请求**：下次重跑导出时一并导出各例的荷载/驱动与步末接触状态。

### 三个姊妹仓库与本仓库的换行符设置（`core.autocrlf`）

- **Git for Windows 的系统级配置默认 `core.autocrlf=true`**（本机 `C:\Program Files\Git\etc\gitconfig`，
  `git config --system --list --show-origin` 可见）。全局级没有设置。
- **它对 eab-kernel 造成的事**：10 个 Phase 0 夹具（sensor/studio 两组 bdda_df 导出与三份 tf 探针/stage 文件）是在
  `.gitattributes` 出现之前入库的，入库时被规范成 LF；而 `fixtures/PROVENANCE.json` 记的是 CRLF 原件的哈希。
  主树工作副本仍是 CRLF、git 的 stat 缓存让 `git status` 显示干净，于是逐字节溯源门只在这台机器的主树上是绿的，
  **任何新克隆（包括从 GitHub 克隆）自己的溯源门都是红的**。09-21 六路审查全在主树里跑，没发现。
  修复：cc5d7cf 在 `* -text` 下 `git add --renormalize` 重新入库原始字节，并在本仓库本地设 `core.autocrlf=false`。
  验证：2026-09-24 对 HEAD 77600c9 做全新克隆（该克隆继承系统级 true），全套 1174 passed；对 HEAD 8376ec2 再做一次，全套 1209 passed；对 HEAD 094861c（只改 `src/eab/limit.py` 模块文档一行）再做一次，仍 1209 passed。由此立下纪律
  "新鲜 worktree 基线必须全绿"（AGENTS.md §2a 纪律 D）。
- **三个姊妹仓库的实况**（2026-09-24 直接读各自 `.git/config` 文本，未执行任何 git 命令）：
  - b-DDA（`D:\b-DDA`）：本地 `autocrlf = false`，早已如此（cc5d7cf 提交时已记录；`.git/config` 最后修改 2026-07-08 11:34，早于 cc5d7cf）。
  - 3DDA 真仓库（`C:\3DDA\3d-DDA-work`）：本地 `autocrlf = false`，**自 2026-09-18 起**——该 `.git/config` 文件的最后修改时间是
    2026-09-18 16:52（只读查看文件时间戳），早于 cc5d7cf（2026-09-23 23:53），所以 cc5d7cf 提交时它已是 false。
  - 3-b-dda（`D:\3-b-dda`）：本地 `autocrlf = false`，由所有者设置（`.git/config` 最后修改 2026-09-24 01:18，晚于 cc5d7cf）。
- **订正一处误报**：cc5d7cf 的提交说明写"3DDA 与 3-b-dda 仍继承系统级 true"。其中 **3DDA 那半句是错的**：
  当时查的是 `C:\3DDA`，而 `C:\3DDA\.git` 是一个**空目录**——空 `.git` 不是有效仓库，git 会当作不在仓库里、只读到系统级的 true（按 git 的仓库发现规则推断；按红线未在该目录执行 git 验证）；
  真仓库在 `C:\3DDA\3d-DDA-work`，本地自 09-18 起就是 false（见上条时间戳）。该提交说明已推送、不可改，以本条为准。
  3-b-dda 现在是 false（所有者已设，时间在 cc5d7cf 之后）；它在 cc5d7cf 时是否确实继承 true，本次无法回头核对。
- **遗留物提醒（所有者自行处理）**：`C:\3DDA\.git` 空目录是遗留物。它会误导工具——在 `C:\3DDA` 下查 git 配置或状态的
  脚本会以为那里有仓库、实际读到的是系统或上层配置。本仓库按红线不动它。
