# WO-R8FIX 修复报告

## 0. 状态与编号口径

工作树：`D:/eab-wt/cx-e2`，分支 `codex-work`，基线 HEAD `30ee15336f64540141d9ba89f8656539dcc08e7c`。修改留树，**不提交**。

本工单输入实际是 **G6H-01～06，共 6 major**；交付段的“11 条”沿用旧轮数量。本报告不虚构 G6H-07～11：先逐条列出 6 条确认发现，再完整列出本次扫描追加问题。原第七轮 11 条由输入审查报告确认已修，不冒称本次重新执行了独立第九轮 G6。

**当前结论：原 6 条及本次确认的同类缺陷已修复，最终全套与机器验收通过；修改未提交。M0 仍待下一轮独立 G6，不因本树全绿而退出。**

关键入口：[设计同步与只读正本清单](file:///D:/eab-wt/cx-e2/docs/r8fix_design_sync.md) · [交付清单及哈希](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/ARTIFACTS.md) · [机器验收](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/verification.json)。

## 1. 执行合同与范围

- 目标：修复原 6 条、每条保存有效修前红与修后绿、真实内部变异、旧门强度对照、同类扫描、全套验证和本树文档同步。
- 写范围仅指定工作树。没有 commit / push / reset / checkout / stash / worktree，也没有运行/修改姊妹求解器、删除 fixtures 或改用户级配置。
- 初始 `git status --short` 仅本轮三个输入项未跟踪；其余 tracked 文件干净。回滚锚：[HEAD 只读导出快照](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/baseline_HEAD_30ee153.zip)，另有各分组首次修改前字节副本。未实际执行恢复。
- Python 使用 `PYTHONDONTWRITEBYTECODE=1`、`python -X utf8`；测试缓存关闭，basetemp 在本树证据 tmp 下。复用 R7 留在本树的 pytest-xdist 3.8.0 / execnet 2.1.1，不安装系统包、不修改项目依赖。
- “修前红”只算目标断言失败；新门写错前提、环境错误、运行中源码行数变化导致 inspect 读错函数，都另列，不伪称数学缺陷证据。

## 2. 六条确认发现逐条闭环

### G6H-01：二维首入把凹 E 内缝误当边界

**修前红**：独立矩形并证明 `E=[-2,2]×[-5/2,3/2]`，`x0=(0,0)` 在 int(E)。新门在未修代码上实际得到：

```text
assert got.kind == 'exit', ('topological interior must use exit policy', got)
E assert 'entrance' == 'exit'
26 failed, 2 deselected in 0.41s
```

其中 24 格是初态错误，另 2 格为相同错误的凹 membership。[原始红日志](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/initial_state/red.log)。

**根因/修法**：实体内部相交是 int(E) 的充分条件，不是一般凹对的必要条件。保留 `polygons_overlap_exact` 的实体三态；新增生产 `entrance_membership_exact`，在相触态构造精确三角对 Minkowski 单元，以局部切锥并覆盖全部角扇区判定 E 的拓扑初态。初态和凹 membership/report-band 探针统一接线，不调用独立 G0 oracle。

**修后/变异**：新增二维门最终 48 格绿；恢复生产初态分支到旧 body-overlap 判据，24 格仍在上述 `kind` 断言红。覆盖非对称 U、尺度、工程平移、旋转、`1±2^-80` 紧配阈值、`2^40` 剪切窄外扇区。[变异日志](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/initial_state/mutation_entrance.log) · [二维分报告](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/initial_state/REPORT.md)。

**边界**：按原模块合同转入局部 `shortest_exit`，不是新实现一般凹体全局 PD。紧配缝可返回局部 `exit/gap=0`；这不声称真正全局 ∂E 距离为零，也不保证一次局部平移脱开所有接触。三维同构扫描结果另列于第 3 节。

### G6H-02：冻结法向先舍入，大切向跨度污染 gap/jet/lift

**修前红**：原输入 `M=10^20`，真实 gap=1，实际 `6662.338147750939`；交换旋转分量后实际 `-6660.338147750939`。切向真导数 0，实际 `4440.892098500626`。纯标量 lift=`5/8`，零种子 Dual primal 却为 `-8326.047684688674`。目标断言分别为 `frozen signed gap`、`exact rigid tangent derivative`、`Dual seed changed exact lift primal`。[原始日志](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/frozen_angle/before.log)。

**根因/修法**：不能将显示单位法向再次 Fraction 化当成原始特征。面 Newell、EE 叉积、VE/EV 残差与全部 jet 从原坐标精确形成；以原始 `c=N·r,h=N·N` 构造 `c/sqrt(h)` 和导数，最后才舍入。`frozen_normal` 携 raw jet；普通自定义法向元组仍是另一个明确输入模型。lift 的普通标量与 Dual 统一为精确 `-c/Nz`。

**修后/变异**：原审查输入回放 gap=`1,1,1e-9`、切向导数均 0、零种子 lift=`0.625`。在 `_frozen_raw_normal` 内恢复舍入单位 jet 后 **18 failed**，红在 gap/导数/比值的目标断言。frozen / interlock / margin 均已接同一模型。[变异日志](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/frozen_angle/mutation_rounded_raw.log) · [原输入修后重放](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/frozen_angle/replay_original_frozen.log)。

追加修复最终 `gap-delta` 及公开 `margin_contacts.margin_gap` 的零/非零相消，见第 3 节；不是只修本轮那个 gap=1 输入。

### G6H-03：极薄二面角被单位法向舍入成 0

**修前红**：`M=10^8` 的合法四面体，精确三重积=1、dot=`2M²`，真角 `5e-17`，旧结果 0。初版新增测试另有 30 格前提错误（对尺度 `2^±400` 构造不可表达体积、逆向后检查朝外），不算修前数学红；保持全部 36 角度格，仅纠正新增测试的前提检查，再将保存的**原始函数 AST** 装回实际方法，36 格全部在 `exact thin signed dihedral` 断言红。[原函数完整重放](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/frozen_angle/mutation_old_dihedral.log)。

**根因/修法**：由精确原面法向和真实棱向量形成 triple、dot，再对 `triple²/|edge|²` 与 `dot²` 同次缩放，最后构造 atan2 参数。没有先分别舍入两个单位法向。

**修后/变异**：6 个 M × 3 个尺度 × 2 个绕向全部正确；原先薄角/反向角恢复，正常 run 含内部复原看护。原审查 6 个 M 输入重放全部通过。[二面角测试](file:///D:/eab-wt/cx-e2/tests/test_r8fix_dihedral.py) · [原输入修后重放](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/frozen_angle/replay_original_dihedral.log)。

### G6H-04：力矩中间乘积溢出，有限结果返回 NaN

**修前红**：二维/三维 `force=point=(1e160,...)/(1e200,...)`，精确力矩全部为 0；新门实际得到 NaN：

```text
assert all(map(math.isfinite, actual)), "finite exact wrench must not contain NaN/inf"
E AssertionError: finite exact wrench must not contain NaN/inf
22 failed, 1 passed in 0.19s
```

22 格还包括非零残差、力臂先溢出、次正规最终结果、不可表达时未报错，以及同类旋量平移/速度变换。[原始红日志](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/wrench/red.log)。

**根因/修法**：公开 `wrench` 接已有 `_exact_wrench`，力臂和叉积对给定值精确形成，再受检舍入。速度旋量的 LP Fraction 输入保持 Fraction；浮点调用也在所有消差完成后舍入。最终非零不可表达时响亮报错。

**修后/变异**：30 格新门绿。将 HEAD 原始 `wrench` AST 装回真实函数，12 格在有限值/NaN 目标断言红；非对称参考点、`2^1008` 非零残差、最终最小次正规和中间越界但最终有限的功率也有门。定向旧力学回归连同初版新门为 `314 passed in 42.05s`。[变异日志](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/wrench/mutationwrench.log) · [最终新门](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/wrench/final_green.log)。

### G6H-05：迁移 facet 门的 expected 先借用被测凸视图

**修前红**：新增回归先对同一正常输入核 baseline，再在 `exact_convex_view` 内删除真实极点/错置源面编号，要求原迁移门抛目标 AssertionError。未修门没有抛错，回归真实报红（`DID NOT RAISE`），不是给枚举结果追加假数据。[有效修前日志](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/gate_teeth/before_valid.log)。

**根因/修法**：新增独立 raw-coordinate convex oracle；从保存的原始顶点/面提示构造精确支撑集合、来源映射，不调用生产 hull/view/cache。独立核极点集合和编号保持条件；稳定纯平移格保留旧完整 facet 标签集合断言。

**修后/变异**：删除极点 2 格、源面错序 3 格，`b6126cf` 旧门和新门 baseline 全绿、内部变异均红。新门红在 `raw-coordinate convex view lost or reordered extreme vertices` / 来源编号断言，而不是偶然顶点顺序。迁移同类五处也修复，见第 4 节。[旧/新实跑机读表](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/gate_teeth/old_gate_comparison.json)。

### G6H-06：坐标噪声地板吞掉真实漏盖

**修前红**：区间并 oracle 给出 `q=ulp(1e8)`。在真实 `_outside_dot_band` 内拒绝 z 向盖，平移后旧 margin 返回 `10q`，G0 却 passed。新增门要求公共自校验拒绝、G0 不通过，未修代码真实失败。[有效修前日志](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/gate_teeth/before_valid.log)。

**根因/修法**：将精确最小平方距的完整性票与显示见证构造票分开。G0 独立表面 oracle 暴露精确平方距；被测所有盖的最小平方距必须完全相等，不加 global-coordinate noise。margin 内部全特征自校验同治；该内部核共享生产几何，只当佐证，不冒充主 oracle。

**修后/变异**：同一个内部拒盖缺陷在原点、`1e3`、`1e8`、短特征及尺度变化下均拒绝；错误量仍为 `9q`。旧门在工程坐标漏过，新门击中精确票。显式窗口的折面源标签先计算原有真实曲面 minimum 再验票，避免拿不同几何模型误判；原显示误差票与阈值不放松。[常驻门](file:///D:/eab-wt/cx-e2/tests/test_r8fix_gate_teeth.py) · [精确票复原变异](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/gate_teeth/revert_fix_mutations.json)。

## 3. 全仓同类扫描与额外修复

扫描不限于六个给定行号；完整路径/反例/有限范围见 [二维分报告](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/initial_state/REPORT.md)、[冻结及角分报告](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/frozen_angle/report.md)、[历史迁移清单](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/gate_teeth/migration_inventory.json)。

| 同类路径 | 修前错误及修复；牙 |
|---|---|
| 凹 `membership_convex` 与报告带探针 | 同一紧配缝错报0，改精确 E 拓扑态；原2格红，恢复旧分支2格红 |
| 二维 `cone_width` | 精确微叉积变0；共同极端缩放变0/NaN。精确叉/点积共同缩放；旧函数变异5红 |
| 二维 `point_side` | `M=2^40/2^50` 的det=-1变0，共线大数变NaN。精确差/行列式，纯Fraction调用不降型；旧函数变异3红 |
| 冻结最终裕度及 delta 导数 | `10^20+1 - 10^20` 得0；最终代数差精确中点构造。先红2格，恢复提前舍入2格红 |
| 公开 `margin_contacts.margin_gap` | 真余量±10000变±16384；原只修gap==0。精确构造sqrt(d²)-delta，15原子格修前6红、修后全绿；内部回退12红/3绿，保留带证书显示下溢合同 |
| `_shift_wrench`、`_twist_back/forward` | 中间叉积溢出污染有限结果；最终舍入并保留LP Fraction。恢复原函数分别2/1/1格红 |
| `mechanism_power`、接触中点 | 有限功率变NaN、中点变inf。精确完整功率/平均后构造；两格先红，原函数变异各1红 |
| 五处迁移 expected 共享凸视图 | support、G0 three-votes、vote-two、yaw、frozen EE 集合改独立 raw-coordinate oracle；保留旧网格和断言，新增内部变异证明 |

### S3D：三维首入和零裕度的同构初态缺陷

将同一个 U 槽沿 z 挤出，独立区间并得到 `E=[-2,2]×[-5/2,3/2]×[-3/4,3/4]`，原点仍在内部。旧 `first_entrance3` 沿 `(1,1,0)` 返回 `entrance/t=0`，沿 `(0,1,0)` 误抛 missed-entrance；`inflated_membership(delta=0)` 误报 ON_BOUNDARY。新门在未修该三维路径时 **14 failed**，分别命中 `topological int E must use local exit policy` 和 `zero-margin E topology mismatch`。[修前日志](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/initial_state/red3d.log)。

新增生产 `entrance_topology.py`：从全部实际三角片构造 VF/FV/EE 配置平面超集；中央平面排列的每个球面开室都取有理代表，两层步长精确限制中央扰动和非中央墙穿越。由全部开室的实体相交态判 E 拓扑，不依赖固定 epsilon 或随机方向。只有相触态进入这条路径。零裕度接线在原 `_resolved` 及完整性自校验之后，不能绕过 G6H-06 的牙；非零显式报告带/窗口不改口径。

新增 **30 格**，包含尺度、精确有理旋转、大平移、`1±2^-80` 紧配阈值、`2^30` 剪切窄外室及 rank-1/2/3 球室。与旧 entrance3/margin 四文件合跑：**142 passed in 34.98s**。[定向日志](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/initial_state/regression3d.log) · [三维补充报告及四组变异](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/initial_state/REPORT_3D.md)。四个实际内部变异：恢复首入旧物理初态 **12 红**；恢复零裕度旧分类 **1 红**；删掉真实外部球室 **1 红**；删掉非中央墙步长界 **1 红**。磁盘生产源码 SHA 前后相同。

另一个子代理只读独立核验：Gordan 严格分离 + 独立 Fraction 消元穷举可行号型，与被测射线法在 rank-1/2/一般位置/`2^-200` 窄室的全部号型一致；独立原始环平面逐 probe 证实未跨墙，U 槽 60 室全在内部，L 角及大剪切 L 角各 46 室为 36 内/10 外。[数学、代码及独立实验复核](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/gate_teeth/topology3_review.md)。这不是下一轮 G6；依赖合法闭合实体和既有精确物理相交合同，高面数/大有理数位宽下成本仍可能较高。

有限扫描不是全域形式证明。精确 LP 证书、已经精确构造的支撑/距离多项式不另造替代模型；nominal reporting root 不升级为精确几何声称；不把死私有浮点辅助函数说成已确认公开缺陷。

## 4. 测试迁移强度与改写台账

- 原始测试不删、不 skip/xfail、不缩网格；最终机器验收比较基线 AST 的测试函数存在性和全部原装饰器，报告实际变更清单。
- `tests/test_invariance_geom.py`：完整标签、support、three-votes、vote-two 的 expected 从被测凸视图迁至独立原坐标 oracle；增加极点/来源映射断言和稳定格旧完整标签断言。原参数网格与原有数值/状态断言保留。
- `tests/test_covers3_g0_vote2.py`：yaw 迁移完整标签 expected 去掉被测 convex-view 前处理。新增真实 canonical 编号错置门，修前 `DID NOT RAISE`，修后命中 raw-coordinate。
- `tests/test_frozen_ee_sign.py`：canonical EE 完整集合 expected 同治；原源环分支与各法向比较不删。真实 hull 构造内部漏极点门修前无异常、修后报红。此文件在 `b6126cf` 尚不存在，其旧门对照明确取 HEAD `30ee153`，不虚构历史。
- 两处追加迁移门原样红日志：[other_migrated_before.log](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/gate_teeth/other_migrated_before.log)；修后连同两个旧文件完整原格：`215 passed in 39.58s`。
- 历史 `b6126cf..HEAD` 的迁移清单逐文件静态登记；实际内部旧/新对照至少22组：05五格、同类support/G0/vote六格、06三坐标格、G2六格、position-independence两格。每个未注入baseline新旧均PASS，变异仅目标 AssertionError/G0失败算红，不把导入/签名错误计入。
- 上述 support/G0/vote 等同类格中部分旧门本来只核计数，源编号错位不敏感，新门进一步加强。不宣称22组穷尽每个历史门的所有可能变异；全部原测试运行仍由最终全套确认。
- 完整测试暴露的旧裕度等式另作第七项语义改写：`test_margin_layer_is_invariant` 保留全部 385 格、标签/显示距离/成员/刚体变换断言，仅将错误的逐次舍入等式换为**独立原始坐标的精确 d² 校验 + 唯一 round-to-nearest-even 中点证书**，没有容差。旧 `e5a_cover_oracle` 保留默认显示见证行为，新增 `exact=True` 的 Gram 见证，折面使用独立测试三角化。
- 该原网格修后 `385 passed, 2021 deselected in 64.78s`；新增 18 格及相邻旧门合跑 `108 passed in 3.92s`。普通一 ULP 和巨大相消两种输入，均在真实 `margin_contacts` 函数体注入旧 `w-delta`、忘减 delta、delta 反号、距离翻倍，八格都命中精确中点目标断言；后面三类也是旧等式本可捕捉的错误，未因改写丢掉。新增正负 halfway、奇偶尾数、次正规与有符号零的 oracle 自证门。[新门](file:///D:/eab-wt/cx-e2/tests/test_r8fix_margin_gap_gate.py) · [独立只读交叉复核](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/frozen_angle/margin_assertion_review.md) · [七项完整改写台账](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/gate_teeth/test_rewrites.json)。

## 5. 失败分类和迭代记录

1. 二维早期宽回归7个 tmp_path setup错误来自 basetemp父目录不存在；建父目录后恢复。另3个inspect-based变异在运行途中源码行号变化读到邻接函数；冻结后新进程定向77格全绿。没有改弱旧门。
2. 三维初期新二面角门30个前提错误已明确排除数学红计数；36原角度格完整保留后由原函数重放取得有效红。
3. 门补强早期大子集19失败：18个是显式窗口源环与曲面 minimum 的计算顺序不一致，前移原有精确曲面计算后385个距离格全绿；另1个为并行编辑引起inspect错位。所有旧断言保留。
4. 首次正式全套在 **94.0761591 s** 时主动停止，原因是补充扫描发现公开 `margin_contacts` 非零相消，需要纳入新快照。只停止核对过PID/父子链的本任务pytest及4 workers；没有将中止算成功。[中止日志](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/interrupted_first_full_suite.log) · [原因/计时](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/interrupted_first_full_suite.json)。
5. 第二次完整运行在冻结快照上得 `105 failed, 9977 passed in 404.70s (0:06:44)`（外层壁钟 407.4342695 s），没有源码漂移。JUnit 核实 **105 个失败全部且仅** `test_margin_layer_is_invariant` 的旧等式 `margin_gap == float_distance - delta`：这是强制先舍入再减的失真合同，与最终精确差构造冲突；不是用容差掩盖的新几何错误。[完整失败日志](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/failed_margin_contract_full_suite.log) · [快照和计时](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/failed_margin_contract_full_suite.json)。修正方式是独立精确舍入证书，而不是放宽容差；原网格和其他断言保持，补真实旧相减路径的变异看护。
6. 定位该问题时，独立 `-x` 三维不变性重放得 `1 failed, 1597 passed in 107.06s`，二维不变性完整重跑为 `851 passed in 44.98s`。最初关于缓存污染的排查假设被上述确定的旧浮点等式反例否定，没有据此修改缓存或放松断言。
7. 所有最终结论只依据最终源/测试/文档冻结后的全套及快照无漂移核验，分组中途跑只作辅助证据。包括中止和失败在内的累计全仓尝试耗时单列，不把失败时间藏在最终成功计时之外。

## 6. 最终全套与复跑

最终原样最后一行：

```text
10100 passed in 400.10s (0:06:40)
```

最终 pytest 运行 **402.386 s 壁钟**，退出码 0；低于 900 s。使用 4 个本地 worker，完整收集 **10100 格 = 原 9851 + 新增 249**，无失败、错误、skip 或 xfail；没有缩格。

- [全套原样日志](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/full_suite.log) · [命令/环境/时间/SHA](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/full_suite.json) · [JUnit逐格结果](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/full_suite.junit.xml)。
- [机器验收](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/verification.json) 为 `verified=true`：248 个冻结输入文件无漂移/新增，62 个基线夹具字节未改；所有原测试函数和参数装饰器保留，HEAD 未变，`git diff --check` 通过。各旧测试断言的语义改写另有第 4 节台账，AST 检查不冒充语义证明。
- 指针最终同步及定向门通过，实际记录见 [canon日志](file:///D:/eab-wt/cx-e2/reports/codex/R8FIX_evidence/canon_apply_final.log)；复跑命令如下。
- 三次全仓尝试的累计壁钟 **903.896 s**（中止 94.076 + 旧合同失败 407.434 + 最终全绿 402.386），超过 900 s。追加公开差值修复、旧断言合同冲突和完整重跑造成这些额外时间；900 s 内指标仅对应最终完整验收，不把中止/失败伪称成功或藏掉。定向回归、变异和独立审计耗时另留各日志。

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONIOENCODING='utf-8'
python -X utf8 tools/fix_canon_ptrs.py --apply
python -X utf8 reports/codex/R8FIX_evidence/run_full_suite.py
python -X utf8 reports/codex/R8FIX_evidence/verify_delivery.py
git -c core.whitespace=cr-at-eol diff --check
```

## 7. 文档、交付与遗留

- README、canon_map、两份本树设计文档同步当前状态，并链接 [R8FIX设计补充](file:///D:/eab-wt/cx-e2/docs/r8fix_design_sync.md)。定义移动后执行 canon 指针脚本及其门。
- 外部 `D:/E(A, B)` 正本只读，未回写；设计补充逐项列出给正本所有者的同步清单。没有将本树同步说成外部正本已改。
- 用户禁止新建worktree和提交，本轮只对指定工作树验证；不冒称满足新鲜worktree里程碑退出条件。下一轮独立 G6 仍由所有者安排。
- 不声称解决一般凹体全局PD、跨盖切换光滑性、全binary64形式证明、工程标定或生产可靠性。

R8FIX_DONE
