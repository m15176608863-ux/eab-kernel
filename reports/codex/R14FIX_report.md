# WO-R14FIX 执行报告

日期：2026-10-13。当前工作树 `D:/eab-wt/cx-e2`，分支 `codex-work`，基线 `878d4f0a260cc703eab7d883ab574fddc2ec2f3d`。
修改留在工作树；未 commit/push/reset/checkout/stash/worktree。原输入及 fixtures 不删除、不改写；姊妹仓库/其他工作树未写入。

## 0. 计数、目标与验收口径

输入工单分别写“6 条”和“11 条逐条”，但实际 `G6N_findings.json.findings` 只有 **N01～N05 五条 major**，confirmed_counts 为 **0 critical / 5 major**。
本报告不虚构 N06～N11，而按 **5 条发现 + 6 项交付/验收要求，共 11 项**记账。
输入另有一条 `unconfirmed` 的 U-GEOM-RANGE（极小几何的 rounding_floor 具名失败）；审查方明确未确认静默错误，不能把它算成第六条已确认 major。本轮未修改该路径，不宣称已关闭此未确认项。

目标：消除已确认静默错；明确分项输入/输出域；每项补真实入口红绿、内部关键步骤变异；同类扫描发现一并处置；保留原测试网格与 M4a；全套覆盖可机读核验。
范围：仅本树 src/tests/tools/docs/README 和本轮证据目录。非目标：姊妹求解器修改、在线切换、重新采集真实姊妹输出、工程标定、重新宣布 M0 或独立 G6 退出。
回滚锚：上述 HEAD；[初始逐文件 SHA256](R14FIX_evidence/initial_manifest.json)、[字节备份](R14FIX_evidence/baseline/)、各变异的恢复 SHA。
本单明确禁止新 worktree，因此不把本树全绿说成纪律 D 的新鲜树或独立 G6 验收。

## 1. 十一项台账

### 01 — G6N-N01：精确指数奇偶性

- **修前红**：[dual_red.log](R14FIX_evidence/dual_red.log)，`33 failed, 12 passed, 2 deselected in 0.21s`（包含 N02/同类格，不重复计发现数）。`Dual(-1,(1,)) ** (2**54+1)` 原来返回 primal `+1`、负导数；目标断言为 `exact odd exponent must retain negative primal`。
- **根因/修法**：删除整数分派前的 `float(p)`；用原精确 Fraction 分母区分整数、半整数、一般实幂。整数与完整导数有理求值后才舍入，半整数保留精确平方根路径；大整数奇偶不丢失。
- **修后绿**：全部旧 Dual 相关组及新门 `1216 passed in 1.03s`；含 int/Fraction、正负大奇数和 `2**400+1`。
- **变异**：把实际 `Dual.__pow__` 精确解析改回 `Fraction(float(p))`，上述 primal 断言红；[可重跑脚本/原始 traceback](R14FIX_evidence/dual_mutations.py)、[日志](R14FIX_evidence/dual_mutations.log)。
- 非平凡大幂另有具名资源上限；0/±1 不受该展开上限，普通可表达大奇幂没有靠拒答掩盖。

### 02 — G6N-N02：精确角度与 atan2

- **修前红**：同一 Dual 日志，覆盖 scalar/Dual 的 `2**54+1`、`2**54+1/3`、tiny/tiny。目标拒绝断言原为 `DID NOT RAISE`。
- 审查输入记录的具体错值：`sin(2**54+1)=0.8973347529975925`，独立有理区间约为 `0.11344832269377987`；`atan2(q,q)`、`q=2^-1075` 原返回 `0.0` 而真角位于 `(1/2,1)`。本树新增同输入拒绝门先红，修后在转换前具名拒收，未用近似 sin 值充当 oracle。
- **根因/修法**：libm 隐式 binary64 转换改变了精确参数；新增中央 `binary64_argument`，先检查分母、有效位数和二进制指数，再允许转换。可无损表示的全部有限 binary64（含次正规）保留，不强套 D400。
- 一般非整数幂的底数与指数同样检查；整数/半整数不走此限制。atan2 对正 x 的精确 RN-zero 小角区先拒绝，sin/cos/atan2 的非零输出不得静默成为零。
- **修后绿/变异**：上述 1216 相关门绿。去掉真实参数检查、去掉 atan2 输出胞检查各自命中指定拒绝断言；不是在产物后伪造数据。
- 边界：libm/Decimal80 仍是近似模型，没有升级为全域正确舍入证明。详见 [Dual 摘要](R14FIX_evidence/dual_summary.md)。

### 03 — G6N-N03：JSON/读取器数值早转换

- **修前红**：[readers_before.log](R14FIX_evidence/readers_before.log)，`90 failed, 17 passed in 0.50s`。真实 JSON `1e-400/-1e-400/1e400` 与直接 Fraction 触及五类向量、五类标量、实际 bdda3d 文件入口；失败为目标 `DID NOT RAISE` 或无量名原生溢出，不把 setup error 算红。
- 错误路径是有限非零数字 token `1e-400 → 0.0`、`-1e-400 → -0.0`、`1e400 → inf`；字符串同值与数字 token 的行为曾不一致。门直接调用真实 JSON/文件入口并断言 `pytest.raises(ConstructionDomainError)`，原输出即 `DID NOT RAISE`。
- **根因/修法**：JSON parse_float 层已丢失信息，后置 validate 无法恢复。先精确解析和查 RN 输出域，再按字段决定连续量单次舍入或整数身份精确保留；拒绝 JSON NaN/Infinity。ContactRecord 全连续字段、Feature/整数身份、bdda3d 直接 dict/文件及嵌套数值证据接入。
- **修后绿**：原 ContactRecord/读取器/TF/M4a/R13 加新门最终组 `447 passed in 6.79s`，含 signed-zero 保真及 bdda3d `extra.refs` 的精确整数回归门；[末轮日志](R14FIX_evidence/readers_regression.log)。
- **变异**：JSON parse_float 改裸 float、向量 decode 改裸 float、整数去分母检查、窗口去入口检查、撤销负零保真、refs 重新连续化，六条分别命中目标拒绝/保真断言；[变异机读证据](R14FIX_evidence/readers_mutations.json)。
- 连续文本域是 `q=0` 或 `2^-1075 < |q| < 2^1024-2^970`，不是“所有十进制均无损”。JSON decimal token 先受该词法连续域检查；普通整数 token 保留任意精度。详见 [读取器摘要](R14FIX_evidence/readers_summary.md)。

### 04 — G6N-N04：高摩擦锥不安全

- **修前红**：[mechanics_red.txt](R14FIX_evidence/mechanics_red.txt)：43 个目标失败来自超界入口及界内圆锥包含。高 μ 样例原来过大容量/假无界；普通 μ=.5 亦有舍入微量出圆锥。
- **原 HEAD 独立回放**：只读提取真实旧 `limit.py`，μ=1e16 得 `alpha=1.9506150776589132e16`，容量平方相对于原始法向 `(1,2,3)` 的独立圆锥上界平方之比 `1.3588925647108172>1`（分母 `(14/5)μ²`），旧自校验却为 true；μ=1e17 报 unbounded。与 N01 的旧实际输出一起保存在 [基线回放](R14FIX_evidence/head_failure_replay.json)，不把新模型拒绝超域当作旧错误输出本身。
- **根因/修法**：逐分量 RN 不保持锥集合包含，精确 LP 对错误模型求解仍会给不安全答案。μ 精确检查 `[0,2^20]`；对最终实际方向 g、存储法向 n 独立精确核 `n·g>0` 与 `||n||²||g||²≤(1+μ²)(n·g)²`。不安全候选有限次向内修正并重验；仍不合格具名拒答。
- `μeps≤2^-32` 只说明尺度选择，不当安全证书。自校验改用独立叉积平方约束，不把同一生成器当真值。
- **修后绿**：一般位置 `(1,2,3)` 法向、非对称点、普通/边界 μ、k 网格及圆锥容量精确上界通过；主力学组 `573 passed in 58.71s`，随后入口重验组 `247 passed in 2.67s`。
- **变异**：去 μ 检查 → 超界拒绝断言红；生成器证书说谎 → 圆锥包含断言红；独立自校验删除 → 自校验拒绝断言红。[力学摘要与日志索引](R14FIX_evidence/mechanics_summary.md)。
- **全套发现的修复副作用**：原二维近自锁格中，统一 `16u(1+μ)` 内缩虽安全却过粗。首次全套的两条既有闭式误差断言红；随后二维改为独立精确认证的最近一 ulp 安全邻点优先，必要时仍走原后备。三维流程、原 28 格、uncertainty 算法和原误差阈值不改；不通过抬高不确定性或标 unresolved 隐藏回归。修前实测与新方案的独立补门/变异详见 [回归定位](R14FIX_evidence/full_failure_triage.log)、[内存探查](R14FIX_evidence/two_d_neighbor_experiment.json)。
- 二维 24 个逐值补门先 `6 failed, 18 passed, 98 deselected in 0.16s`（含粗内缩无法分辨的微小 μ 格），修后与原近锁/力学差分组 `356 passed in 22.32s`；[红](R14FIX_evidence/two_d_neighbor_red.log)、[绿](R14FIX_evidence/two_d_neighbor_green.log)。删除真实邻点分支后，traceback 精确落到原 `assert abs(r.alpha - exact) <= ...` 行，而非碰巧失败的状态或不确定性断言；[变异红](R14FIX_evidence/two_d_neighbor_mutation.log)。

### 05 — G6N-N05：错误容量相对界

- **真正修前红**：[mechanics_n05_doc_red.txt](R14FIX_evidence/mechanics_n05_doc_red.txt)，`1 failed in 0.09s`，断言 `N05 unqualified nonlinear capacity bound`。初次 PowerShell stdin 把中文写成问号的尝试无效，已修正并单独重跑；不把它冒充证据。
- **根因/修法**：一般 C(μ) 非线性。理想正 k 棱锥只由集合包含推出 `C(μ cos(π/k))≤C_k(μ)≤C(μ)`，不能把左端替为 `cos(π/k) C(μ)`。README 与模块旋转相对区间错误同步撤回。实际收缩后的 rounded 模型只认证上包含，不无条件宣称理想内切半径。
- **原门核对**：`tests/test_limit.py` 确实断言相对短缺，但仅 `_LIN_AMP=.25,_LIN_MU=.2` 固定族。所有旧数值断言与 k 网格保留，docstring 收窄，不能泛化。
- **数值绿证据**：同几何 μ=1.8，独立六行静力平衡/64 接触圆锥证书认证 `C_true/N≥6.865248226950123`；k5/6/7 离散容量/N 为 `4.4094435091284128 / 4.2153362209181857 / 6.1281784305906921`，比值严格击穿余弦界。未把 Patton 23 猜作真容量。[证书](R14FIX_evidence/mechanics_n05_certificate.txt)。
- **变异**：用真实修前 README 字节恢复旧句，重新运行本门得到同一目标断言红，finally 恢复字节并核 SHA；[日志](R14FIX_evidence/n05_document_mutation.log)、[重跑脚本](R14FIX_evidence/domain_mutations.py)。

### 06 — 分物理量支持域落实

[设计合同](../../docs/r14fix_design_sync.md) 逐项列坐标/长度/力/力矩/面积/黏聚、μ、角度/指数、文本连续量、整数身份、legacy 检测角/长度窗、诊断尺度与证书显示。
`check_mu`、`binary64_argument`、精确 JSON 解码与已有最终一次舍入边界各司其职；没有把精确谓词或完整有理代数统一缩成 D400。
补 `test_r14_domain`：精确上界外一个任意小 Fraction 也不能先舍入后混入；二维角窗与骨形 phase 的六个早转换格先红后绿。
骨形 `lx/ly/lz/amp/center` 的分项 D400 与最终坐标检查亦落地：12 格先红，相关 139 门通过；包括域内 `lx=2+2^-2000,center_x=1` 抵消出不可表达非零坐标的响亮拒绝，而不只检入口量级。[修前红](R14FIX_evidence/shape_red.log)、[相关绿](R14FIX_evidence/shape_green.log)、[最终 32 个域门](R14FIX_evidence/domain_final.log)。撤销原精确系数保留后，该抵消断言再次报红；[五项域/文档变异](R14FIX_evidence/domain_mutations.json)。
独立位数推导与 μeps 推导见设计，不把有限网格写成全域证明。

### 07 — 同类数值问题扫描及修复

全 `src/eab` 与 tools 做可重跑 AST 候选索引，[扫描器](R14FIX_evidence/scan_numeric_surface.py)、[签名/调用清单](R14FIX_evidence/numeric_surface_audit.json)。这是覆盖索引，不是静态正确性证明。
最终索引覆盖 58 个模块、571 个公开签名、251 个候选调用位点（40 初等函数、114 checked boundary、91 float 候选、6 JSON/通用 loader）；[逐族复核与限制](R14FIX_evidence/numeric_call_review.md)。

| 同类问题 | 处置与证据 |
|---|---|
| 一般非整数幂精确底数、atan2 非零结果下溢、精确大幂资源爆炸 | 双重参数预检、精确输出胞拒绝、具名资源界；Dual 独立参考与内部变异 |
| ContactRecord/Feature/bdda3d 非整数身份被 int 截断 | 精确分母必须 1；保留大整数身份，不把编号当连续量 |
| Bdda2DWindow 直接 Fraction 参数先被 math.isfinite 转换 | 入口精确语义及可表达性检查，距离窗口原值仍给精确几何；八格先红 |
| 二维摩擦方向也舍入出锥 | 同样核最终方向；四格先红；旧二维候选逐值参考保留 |
| 黏聚方向不再精确切向/超单位盘 | LP 内部保留有理正交投影和内缩；独立核 dot=0/norm²≤1；九格先红 |
| 黏聚 cap 中间乘积与空 covers / 可变材料漏重验 | c*A 完整有理乘积；材料入口与每次列构造重验；非法材料十一格先红 |
| 二维显式角窗、骨形 phase 早混合浮点 | 在 libm / 混合加法前检查参数；六格先红，三种内部撤步变异抓红 |
| G2/bb52/G4/M4 capture/ingest 工具的原文本与子导出 | 真实临时文件入口及假子模块门；21+3 格先红；checked 解码，不运行姊妹 exe |
| M4 `extra.df18_cs1` 原字符串及 G4 极小检测角 | 复制本树 bb52_N3 到证据 tmp 后确证；度量前 checked scalar，h1 原文先分项验域；2 格先红，77 相关门绿 |
| 工具新增通用 decode 的 decimal 整数身份回归 | 交叉复核发现并改 schema-aware 解码；不隐瞒修复过程中新引入的问题 |
| ContactRecord signed-zero 往返保真 | 专属解码保留已有 float/JSON decimal 负零；不改全局有理构造的零语义 |
| showcase 演示构造器密度/面积早舍入 | 按半径、密度、分段数、μ 分项入口检查；鞋带面积、形心与重力旋量完成有理代数后才舍入；schema/示例组合 7 格先红、56 门绿；不运行整套画图/姊妹采集 |
| 骨形生成器长度/振幅/中心早浮点化 | 12 格先红，入口分项检查与最终完整坐标表达式保真；保留 Dual 通道与既有采样模型，相关 139 门绿，内部撤销精确系数保留的变异抓红 |

详细分工账：[Dual](R14FIX_evidence/dual_summary.md)、[读取器](R14FIX_evidence/readers_summary.md)、[力学](R14FIX_evidence/mechanics_summary.md)、[工具](R14FIX_evidence/tool_readers_summary.md)。
最终调用逐族核查与剩余边界另列本目录审阅文件，不以“全仓搜索过”宣称任意 API 全输入数学证明。

### 08 — 定量文档声称扫描

[定量声称复核](R14FIX_evidence/quantitative_claim_review.md) 区分当前命题、固定族、历史记录和未升级声称。README 一般余弦界/limit 旋转相对界撤回，历史 plan 加订正；canon A.9 的纯滑动固定族不误删。
发现 `face_noise` 文档的 `(2u+u²)` 常数原来只引用较宽包围测试；现增加 `test_r14_claims.py` 对原常数的独立有理平方两侧断言，保留原三尺度与旧门。`4 passed in 0.05s`；真实函数内部加 8u 偏置后目标常数断言红。[严格常数变异](R14FIX_evidence/mechanics_mut_noise_constant.txt)。
README 拱例 480/2240、10/28 等计数明确标为历史结果而非现行精确门；G3 的 1.9995 标为观测值，现有门实际上断言 `2±0.1`。不拿较宽测试声称逐字定量结论。

### 09 — 变异牙与测试改写

所有原发现均有被测内部步骤或实际旧文恢复的变异。表中红的不是 setup/import 崩溃或随机 LP 顶点的脆断言；具体 traceback 保留。
源码内存编译变异不写源；文档/少数磁盘变异以 finally 原字节恢复并核 SHA。

| 旧测试文件 | 改写与强度 |
|---|---|
| `test_r6fix_dual_lp.py` | 原极小 atan2 格曾要求 primal=libm 的零；保留该输入，改为具名拒绝，同时原完整导数独立 Fraction 参考仍核，不接受静默零 |
| `test_r7fix_dual.py` | 原有损幂快路变异移入新的实际整数分支；同一输入、同一“非零导数不能变零”断言继续命中，876 格保留 |
| `test_r13fix_mechanics_differential.py` | μ/k 原网格全部保留；按所有者明确新 μ 域，原2^1022格改严格拒绝；域内二维保留原 RN 候选逐值核并增最终安全/偏移界；三维另核最终最小认证收缩的逐值参考，不能用安全证明取代候选精度 |
| `test_limit.py` | 仅文案订正；全部数值断言和网格原样保留 |
| `test_r13fixb_readers_oracles.py` | h1 的 D400 检查从旧 property 扩展到构造入口后，原只删除 property 检查的变异不再能重引缺陷；变异迁移到实际两处检查，保留原 `2^-1074` 输入及 `DID NOT RAISE` 目标，所有域外格与独立 Taylor 断言不改 |

其余旧门未删、未 skip/xfail、未缩网格；完整基线节点保存/实际执行核验见全套审计。新测试不以“预期失败”豁免生产缺陷。

### 10 — 全套、M4a 与耗时

标准 pytest 完整文件分片，无安装/xdist/-k；审计插件只记录 nodeid 与三阶段报告，不改选择。
收集集合、每片收集集合与实际 call 集合须多重集合精确相等；11998 个原节点须全部保留；setup/call/teardown 均通过；运行期间源码/测试/政策/文档 SHA 不变。

首轮完整跑完 12402 格，660.926 s，6 条失败：2 条二维近自锁精度、2 条 h1 具名异常的旧量名兼容、1 条 h1 旧变异被新增入口守卫挡住、1 条 canon 头部插入段把原静态合同从第三行挤走。全部保留原始 [首轮审计](R14FIX_evidence/full_suite_final/summary.json)；这不是最终绿。修复异常名、迁移变异、恢复 canon 合同行位置，并按上文改善二维安全舍入；原数值门与网格不放松。
补修后读取器/M4a/完整 R13b readers 定向组 `549 passed in 15.49s`，canon 原门 `3 passed in 0.06s`，与上文二维 356 格一并先行验证。第二轮调度权重采用首轮实际逐文件耗时，只影响完整文件分配，不影响集合。

第二轮 **12427 收集 = 12427 实际 call**，原 11998 格全部保留，新增 429 格；无重复、失败、skip/xfail 或 setup/teardown 异常。M4a 原 `adapter/shadow/vv_reader` 共 **109 格全部通过**，不改其旧测试。分片墙钟 **579.5198395 s**；收集 3.1170178 s；从记录启动到完成的总墙钟 **582.796179 s**，均小于 900 s。四进程耗时相加为 2219.543823 s，不把并行墙钟误称串行加速基准。

四个 pytest 进程的最后一行原样：
```text
2357 passed in 539.43s (0:08:59)
1837 passed in 574.99s (0:09:34)
2818 passed in 541.22s (0:09:01)
5415 passed in 538.96s (0:08:58)
```
完整集合审计最后一行原样：
```text
R14FIX_FULL_SUITE PASS: 12427 calls; wall=579.520s; failures_or_skips=0; source_drift=0
```
[最终全套机读审计](R14FIX_evidence/full_suite_verified/summary.json)、[完整收集清单](R14FIX_evidence/full_suite_verified/collection_nodes.json)、[原始运行日志](R14FIX_evidence/full_suite_verified_runner.log)。分片不省略任何文件/节点；各片命令、逐项 setup/call/teardown 事件与前后哈希判定均保留。

### 11 — 文档同步、指针、交付与完整性

README、canon_map、exact_predicates_plan、exact_3d_design、历史 plan 提示、R13 清单增量提示和本树 R14 设计已同步。
定义行移动后已执行 `python -X utf8 tools/fix_canon_ptrs.py --apply`；[应用日志](R14FIX_evidence/canon_ptrs_apply.log)、[冻结后零改动复核](R14FIX_evidence/canon_ptrs_final_verify.log)。
静态辅助门只在逐站点源码复核后续 pin/增加精确例外，分析器不放宽；它不代替数值运行时证据。最终政策变更和零诊断输出在本轮 static 证据中。
最终原命令末行：`exact construction AST gate: 0 violation(s)`，88.8759242 s；扫描前后 src/tests/policy/分析器 SHA 相同。[最终静态状态](R14FIX_evidence/static_final_status.json)。政策相对初始 2674 条变为 3035 条：新增 384、移除 23、原 pin 续审 53、新 import 13；逐项代码、理由和哈希见 [审阅差异](R14FIX_evidence/static_changes.json) 与 [说明](R14FIX_evidence/static_summary.md)。首版 87.828 s 证据保留但不冒充补修后的最终状态；另有一轮中途扫描虽零诊断，但期间测试发生变动，明确排除最终证据。原静态分析器只扫描 src/tests，工具边界另靠运行时门和逐族复核，不从静态零诊断推论全 tools 已证明。
最终文件清单、逐文件 SHA256、fixture 完整性及 HEAD/分支不变核验见 [交付清单](R14FIX_evidence/ARTIFACTS.md)、[机器结果](R14FIX_evidence/delivery_result.json)、[SHA256 清单](R14FIX_evidence/final_manifest.json)。可用 [交付复核脚本](R14FIX_evidence/verify_delivery.py) 重跑；其检查全部初始入库文件未删除、夹具字节未变、旧测试改写文件恰与五项台账相符、报告 11 项/末行/UTF-8/链接及所有证据 JSON 可解析。未生成新工作树，未提交。

## 2. 重跑与边界

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONIOENCODING='utf-8'
# 普通串行入口（不以其运行时替代本次实测）：
python -X utf8 -m pytest -q -p no:cacheprovider --basetemp=reports/codex/R14FIX_evidence/tmp/manual_full
# 本次审计分片方式；每次用新结果目录，拒绝覆盖既有日志：
$env:R14_RUN_NAME='full_rerun_unique'
python -X utf8 reports/codex/R14FIX_evidence/run_full_suite.py
python -X utf8 tools/check_exact_construction.py
python -X utf8 tools/fix_canon_ptrs.py
```

剩余边界不是未披露的“已验证”：没有证明跨平台 libm/一般非整数幂的全域误差界、任意用户数值协议或无限资源；没有重新认证全部历史数学/文献声称，也没有任意凹体全局 E 的新证明。
本次候选索引、有限参数门和同一实现团队内部交叉复核不是另一轮独立 G6；待审查方复核。外部设计正本及姊妹目录均未回写。

R14FIX_DONE
