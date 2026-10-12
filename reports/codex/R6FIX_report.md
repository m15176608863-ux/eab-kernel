# WO-R6FIX：第六轮 12 条确认发现修复报告

日期：2026-10-12。执行树：`D:/eab-wt/cx-e2`，分支 `codex-work`，HEAD 保持 `2f6c51811edba364e846923da04c45c901a9af8c`。12 条已修，工作树未提交；最终全套 8866 项通过。

## 1. 范围、验收与回退

- 目标：逐条修复 G6F-01…12，修前真实红、修后绿，每条至少一个穿过实现的变异；扫描同根问题；全套绿；同步仓内说明。
- 范围：仅本工作树源码、测试、仓内 README/设计/canon 与 `reports/codex/R6FIX_evidence/`。未操作姊妹仓库或其他工作树，未执行 commit/push/reset/checkout/stash/worktree。
- 非目标：不改变姊妹内核、不启动 solver、不升级 M0/G6/工程认证，不修改只读 `D:/E(A, B)` 正本。
- 回退锚：改动前备份全部 1482 个 tracked 文件，[逐文件 SHA-256](file:///D:/eab-wt/cx-e2/reports/codex/R6FIX_evidence/baseline.json) 与 [原字节 ZIP](file:///D:/eab-wt/cx-e2/reports/codex/R6FIX_evidence/baseline_tracked.zip)。初始未跟踪内容仅为本轮输入，保留未改。
- 验证环境：所有 Python 均 `PYTHONDONTWRITEBYTECODE=1 python -X utf8`；pytest 禁缓存，临时目录在本树 evidence/tmp。禁止新建 worktree，因此本树全绿**不是**纪律 D 的新鲜 worktree 验证，也不是独立六路 G6。

## 2. 12 条逐项证据

修前红均为新增测试在对应实现尚未修复时的实际运行；不把 collection error、注入定位器过期或环境错误当作“牙”。修后最终统一以第 5 节全套为准。原复现数据或等价最小输入已进入 `tests/test_r6fix_*.py`。

| ID / 级别 | 修前的看护断言与错误输出 | 根因修复 | 修后与内部变异 |
|---|---|---|---|
| G6F-01 critical | `source-membership-isolated`：源顶点/面不变，改返回 view 后 `-1 != 1`；相交也错误 | canonical 缓存只存不可变内容，返回隔离对象；源内容签名仍每次核验；所有拓扑 list 返回副本。合法 self-view 保留 `view is source`，不是外泄的另一个模型 | 原点成员=1、内含盒重叠=1；恢复 mutable 缓存别名 → 同一成员断言红 |
| G6F-02 major | 仅反绕 top 提示，`convex-point-ignores-face-hints`：`-1 != 1`；交叉提示曾抛 zero-area | 复用源面前核验与 canonical outward ring 循环同序，不能只比顶点集合 | reverse/crossed/cycle/empty 都与顶点凸包真值一致；删绕向核验 → 精确成员断言红 |
| G6F-03 major | `exact-midpoint-concavity`：2^-50 真凹槽仍 `is_convex=True`，无 reflex edge | 原输入有理未归一化法向、棱方向三重积判号；移除隐式 dihedral_noise | 精确凹棱 `(3,8)`，含 binary64、Fraction、尺度、工程平移/有理旋转；恢复噪声带 → 中点凹性断言红 |
| G6F-04 major | 微间隙/微贯入严格样本 `samples=0`，枚举法锥内部故障时 `passed=True` | 2D/3D 非凸 G0 用独立精确分类，不以 1e-12*L 或噪声地板跳严格样本；明确检查实际样本数 | 2D 两侧和 3D 微隙均 `samples=1`；法锥内部缺陷确实被门发现；恢复带宽预筛 → `strict sample was skipped` 断言红 |
| G6F-05 major | 微贯入首次出口 `0 != 2^-39`；tiny 方块距离 `1.70407e-181 != 1.20496e-181`，正确内核假红 | 独立 Fraction 边事件与区间状态；独立点段平方距，Decimal 开方不先将平方转 float | 真首次出口/可表达距离正确，tiny/normal/huge 均核；恢复 midpoint 噪声及平方早舍入各自使目标出口/距离断言红 |
| G6F-06 major | `representable signed gap`：`-0.0 != -1.204959932551442e-181`；大尺度中间平方溢出 | 公用有理根构造：拆指数给候选，精确相邻中点作最终 ties-to-even 舍入；符号保留；2D 接触投影先精确 | kind/label/normal 与非零 gap 一并核验；恢复 `sqrt(float(square))` → 原 signed-gap 断言红，独立进程 `1 failed` |
| G6F-07 major | 除法导数 `inf/0 != 1`；atan2 导数 `-0 != -5e-201`，tiny 曾 ZeroDivisionError | 常规快路限制安全指数范围；极端/相消用精确二幂规整后的有理表达式最终舍入；反除、乘积相消等同类一并修 | 多通道、跨指数、独立 Fraction 导数；恢复旧商/atan2 实现分别在导数值断言红，不借 primal 或异常碰巧报红 |
| G6F-08 major | 工程坐标距离 `0 != 1e-9`，法向 None；原点 tiny 距离也平方下溢 | 保留精确相对投影，距离/normal 不反减舍入后的全局显示点；公开 `exact=True` 有理投影见证 | 平移/尺度/非轴对称角点有理旋转，距离和法向均核；去掉精确投影返回步骤 → `exact relative distance` 红，独立进程 `1 failed` |
| G6F-09 minor | offset 从整型 0 换 float 0 后 nominal 先抛 `zero-length edge`，精确 solver 未运行 | 混合标量平移先有理化；进一步修 nominal 的所有平移点，连全 float 微体+大 offset 也走 exact translation | 三种等值 offset 根均 `7/4000000000`；恢复普通平移 → 精确仿射值断言红；恢复 nominal 浮点构造 → 目标精确逃逸门红 |
| G6F-10 minor | canon 命题 1 仍含“仍先浮点构造”，且缺已有精确差点门指针 | 修正为先有理化再作 b−a，指向既有 `test_entrance_block_forms_differences_before_any_float_rounding`；不改已正确的 entrance_block 实现 | 文档与既有行为门通过；进程内把该陈述变回旧句 → `stale pre-rounded margin difference claim` 红，`1 failed` |
| G6F-11 minor | `Dual(0,(1,)) ** 0` 求 0**-1，错误 ZeroDivisionError | p==0 恒等常数分支，返回 1 与同宽全零导数 | 零/非零底与多通道核验；移除常数分支 → 常数幂边界门红 |
| G6F-12 minor | 零约束 optimal 返回 `exact_x=None, exact_y=None` | 填充有理零向量与空对偶 tuple；核全部公共 optimal 返回路径 | solve/maximize 零约束及一般证书门；删 exact 字段 → 目标见证完整性断言红 |

### 可重跑细节与完整失败栈

- [三维分项报告](file:///D:/eab-wt/cx-e2/reports/codex/R6FIX_evidence/geom3/report.md)：01/02/03/09、修前 17 红、8 个变异的实际断言与完整栈。
- [G0 分项报告](file:///D:/eab-wt/cx-e2/reports/codex/R6FIX_evidence/g0/report.md)：04/05、独立 oracle 自检、严格样本数量、旧门迁移。
- [Dual/LP 分项报告](file:///D:/eab-wt/cx-e2/reports/codex/R6FIX_evidence/dual_lp/report.md)：07/11/12、极端导数原红、内部变异与同类冻结构造。
- 构造/文档组：[修前 13 failed, 2 passed](file:///D:/eab-wt/cx-e2/reports/codex/R6FIX_evidence/construction/pre_fix.log)，[06 变异](file:///D:/eab-wt/cx-e2/reports/codex/R6FIX_evidence/construction/mutant_06.log)，[08 变异](file:///D:/eab-wt/cx-e2/reports/codex/R6FIX_evidence/construction/mutant_08.log)，[10 变异](file:///D:/eab-wt/cx-e2/reports/codex/R6FIX_evidence/construction/mutant_10.log)。红日志同时包含断言和实际输出。

## 3. 全仓同类扫描与补修

静态扫描 `src/eab` 全部 Python 模块的缓存/返回别名、noise/tol 分支、平方与全局舍入投影、Dual 商/atan2/幂、LP optimal 返回分支；再沿调用链和最小反例验证。扫描清单不等于全域形式证明。

1. **可变缓存/别名**：修 Polyhedron 五类拓扑 getter、`_ray_directions` 首建返回、`translate_exact` 的 faces 别名、margin `_surface_view/_resolved_cached` 的可变私有产物。margin 两条新门先 `2 failed`，现在 cache 只存不可变 payload、每次恢复新对象。其余标量/向量/三角化/事件/平面缓存逐项核类型与内容 key，详见三维分项。
2. **隐式带宽/浮点 oracle**：G0 主 oracle 完全去掉生产几何调用；2D 旧公开 convex/reflex、point-in-polygon、crossing、overlap 辅助去隐藏地板，显式正 tol 单独表达窗口。3D 独立表面 oracle 自检覆盖多连通分量，不能只测第一顶点是否被包含。保留的无生产入口私有历史噪声链明确不称精确 oracle。
3. **2D 构造量**：VE/EV 与 facet gap 对混合 Fraction/float 先作精确差；凸首入点投影参数不平方 float；FF 两个相反面环起点不是接触点，改给实际公共段点。测试覆盖 2^±600、1e8+1e-9 混合标量。orientation/centroid/interior 的面积和仿射量早舍入同根问题也补门修复。
4. **3D 距离构造**：norm、点段、段段、点面、segment closest points、brute feature distance 改有理平方/参数与最后开方；普通 norm 用 hypot，真不可表达范数显式溢出；unit 先缩放，避免原范数溢出毁掉可表达单位向量。brute_feature_distance 与生产共享 exact_geom，文档已改“内部佐证”，不是 G0 独立 oracle。
5. **Dual / frozen 同类**：反除、两乘积导数溢出相消、幂的先系数溢出，冻结低维盖的平方范数/全局投影/混合标量构造均补极端门。详情见 Dual/LP 分项，不把稳定算术快路范围当几何容差。
6. **不可表达显示与精确状态**：根构造默认不静默非零→0/inf。margin 内部显示若显式允许下溢，公开 `MarginContact.exact_distance_squared` 保留证据，原 `closed=False` 状态门原样保留并加强；精确谓词不能因显示范围受阻或改变答案。`nearest_point_on_convex_entrance(exact=True)` 提供全局 float 不能分辨的投影。
7. **全套发现后的盖构造补修**：VF/FV 的面积、六类盖的 gap 从有理相对量最终开方；`Cover3` 追加 `exact_gap_squared/exact_gap_sign/exact_area_squared`，原微尺度显示 0 的窗口门不再被面积显示下溢挡住。新增 2^-1075 三分量距离格：每分量先舍入为 0 会错误给 0，而最终范数应为最小 subnormal。新增门修前 `4 failed, 1 passed`，内部恢复 VV3 的分量早舍入后，`round final norm, not its components` 断言 `0 != 5e-324` 红。证据：[修前](file:///D:/eab-wt/cx-e2/reports/codex/R6FIX_evidence/construction/cover_before.log)、[变异](file:///D:/eab-wt/cx-e2/reports/codex/R6FIX_evidence/construction/mutant_cover.log)、[关联 129 门通过](file:///D:/eab-wt/cx-e2/reports/codex/R6FIX_evidence/construction/cover_final.log)。

## 4. 测试改写台账与文档同步

没有删测试、放松阈值、加 skip/xfail 或缩减参数网格。所有已有门的改写仅为移植到真实新路径或修正“舍入后的新数据仍须等于理想边界”的不成立前提。

| 原文件/门 | 改写及不弱于原门的依据 |
|---|---|
| `test_margin.py::test_theorem_two_gate_has_teeth_shrinking_the_nearest_point_is_caught` | 注入接受 `exact=True`，在真实精确投影上乘 Fraction(99,100)，仍保全部原 60 样本、n>40、caught==n；不再注入已退出距离路径的显示点 |
| `test_kernel2d_review.py::test_r7_third_vote_hull_vertices_match_and_catch_sign_flip` | 原 300 样本、全 gap 反号/误差>1 和精确成员内部变异都保留。新增原 normal 反号检查及 gap 独立于显示 normal；gap 的反号改注入真实有理分子内部，而非失效的 outward_normal 路径 |
| `test_geom3_e5a.py::test_g6e_near_parallel_legacy_parameter_mutation_is_killed` | 删除 float fallback 分支后旧 substring 不存在；改为真实入口内恢复旧浮点参数/全局舍入投影。相同几何、独立 oracle、2 ulp、交换次序和 body distance 门全部保留 |
| `test_invariance_2d.py` | 原运动/尺度/几何网格全部保留；对每个实际浮点输入核独立精确 oracle，并加精确有理仿射变换的原计数/分类不变性；不再依靠噪声把舍入后微隙/微凹强压成理想边界 |
| `test_kernel2d_entrance.py` | 原 30 种子、brute 时刻容差、gap 门保留；真实边界由原 x0/d 与 t_exact 重建，独立 oracle 要求恰好 0；浮点 e.x 另按它实际代表的数据核精确分类 |
| `test_margin_exact.py::test_closed_is_exact_when_the_display_gap_underflows_to_zero` | 原显示 0、非闭合及精确 OUTSIDE 断言全保留；额外核 `exact_distance_squared == gap**2 > 0` |
| `test_e5a2_covers.py::test_enumeration_window_does_not_read_a_gap_rounded_to_zero` | 原显示 0、完整盖集和窗口拒绝断言全保留，额外核每盖精确 gap 平方与符号 |
| `test_e5a2_integer_arithmetic.py::_eager_ee` | eager 参数计算次序、原 9 格×所有棱对×2 窗口及整条 `Cover3 ==` 均不动；独立 Fraction/Decimal100 为新正确舍入的 gap 及新增证书字段给 expected，停止复刻旧的单位法向×早舍入相对向量求 gap |
| `test_bb52_g1.py::test_g0_exit_completeness_has_teeth[drop_VE_subset]` | 原装饰器、21×60 输入网格、出口缺盖归因和旧 1186 投票保留。精确仿射像保有等价 EV 见证，距离必须 603/603；另新增旧逐顶点 float 坐标像完整 1260 格，控制组 603/603，真实删 VE 变异组仍必须 584/603、全部 19 条 `got > truth > 0` 且归因为缺盖。把两组不同输入混同的变异被新增断言抓红，详 [追加报告](file:///D:/eab-wt/cx-e2/reports/codex/R6FIX_evidence/g0/bb52_followup.md)；`tools/bb52_g0.py` 仅同步两处旧 oracle 注释 |
| `tests/e5a_escape_oracle.py::move` / `test_invariance_interlock.py` | 独立 oracle 先对每个输入 F 化再平移，Newell/Gram/独立枚举不变。原 18 格×4 偏移、候选集合、并列标签及全部断言原样保留，另加精确仿射输入门；恢复旧 float 加法使该门红。详 [追加报告](file:///D:/eab-wt/cx-e2/reports/codex/R6FIX_evidence/geom3/interlock_oracle_followup.md) |
| `tests/e5a_g2_oracle.py::construction` | 原 G2 27 个刚体/单位格及逐字段字典相等不动；独立 Fraction 平方距、按位长提高精度的 Decimal 最终开方替代早舍入 dot/norm。新增 2^±600 和工程坐标微斜面 gap 三格先红后绿；独立 oracle 的旧平方早舍入变异另有牙门 |

README、canon_map、仓内两设计文档同步；canon 命题 1 的 G6F-10 旧句已订正。外部设计正本按只读约束未改。代码定义行变动后运行 `tools/fix_canon_ptrs.py --apply`，并跑指针门。

## 5. 最终全套及耗时

第一轮实际全套末行（不是最终验收）：

```text
6 failed, 8849 passed in 1312.89s (0:21:52)
```

runner 墙钟 1324.8708759 s。失败是 BB52 缺盖牙 1 格、微尺度盖构造 1 格、互锁独立输入像 4 格，已按第 3/4 节返修并保留原网格。原日志和冻结清单另存：[第一轮日志](file:///D:/eab-wt/cx-e2/reports/codex/R6FIX_evidence/full_suite_first.log)、[第一轮运行元数据](file:///D:/eab-wt/cx-e2/reports/codex/R6FIX_evidence/full_suite_first.json)、[第一轮文件哈希](file:///D:/eab-wt/cx-e2/reports/codex/R6FIX_evidence/verified_tree_first_start.json)。不会把这轮失败覆盖或写成全绿。

返修后运行 canon 指针同步，283 项专项/指针门通过。曾有一次专项命令把文件名误写为不存在的 `test_canon_map.py`，属于输入错误（exit 4/no tests ran），改为实际 `test_doc_pointers.py` 后运行通过；该失败日志保留且不作为红→绿/变异证据。

第二次完整全套命令：

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -X utf8 reports/codex/R6FIX_evidence/run_logged.py full_suite python -X utf8 -m pytest -q -p no:cacheprovider --basetemp=reports/codex/R6FIX_evidence/tmp/full_suite_second --durations=30
```

第二次完整全套最后一行原样：

```text
8866 passed in 1493.49s (0:24:53)
```

- pytest 实测 **1493.49 s**；runner 墙钟 **1511.760510299995 s**；exit code **0**。没有引用审查方 8582/876.70 s 作为本次验证。
- **未达到尽量 ≤900 s 的耗时目标**。本轮保留全部原网格，严格样本不再被浮点噪声带跳过，G0 分类/距离/出口改为独立有理 oracle；为保住原 19 条缺盖牙，BB52 另加旧浮点坐标像的完整 1260 格控制组和 1260 格变异组。这些验证有额外算术/采样成本，未以删门、缩网格或改 skip 换速度。
- `--durations=30` 实测最慢单项：BB52 drop_VE_subset **58.91 s**；no_EV_covers **35.03 s**；strict_cone_only **29.10 s**；no_VV_covers **23.71 s**；凸体 400 标签冻结路径 **22.57 s**。原大型互锁 G0 三尺度门各 **19.32–21.41 s**。新增专项加指针 283 项单跑为 **1.17 s**，不能把总超时简单归给新增用例数量。
- 时间来自共享执行环境；全套开头与 BB52 关联复核有部分重叠。没有做隔离性能归因，也不将本轮时间当作稳定性能基准；性能优化仍不能牺牲独立 oracle 或原门。
- 最终源码/测试/工具/仓内文档 **168 个文件**在全套前冻结，结束后路径集合与 SHA-256 均无增删改；**62 个 fixtures**与起点哈希完全一致。既有测试函数无删除、旧参数装饰器无变化、无新 skip/xfail 语法，`git diff --check` 通过。AST 清单不能独自证明断言强度，第 4 节人工改写台账仍是必需证据。

证据：[最终全套日志](file:///D:/eab-wt/cx-e2/reports/codex/R6FIX_evidence/full_suite.log)、[运行元数据](file:///D:/eab-wt/cx-e2/reports/codex/R6FIX_evidence/full_suite.json)、[完整性审计](file:///D:/eab-wt/cx-e2/reports/codex/R6FIX_evidence/delivery_audit.json)、[冻结清单](file:///D:/eab-wt/cx-e2/reports/codex/R6FIX_evidence/verified_tree_start.json)。定义行最后同步 **23 rewritten; 0 kept**，指针门已进入最终全套。

逐条机器状态及 24 条实际变异链由交付脚本校验 exit、实际末行、FAILED 节点和目标断言后生成：[12 条状态](file:///D:/eab-wt/cx-e2/reports/codex/R6FIX_evidence/findings_status.json)、[变异校验](file:///D:/eab-wt/cx-e2/reports/codex/R6FIX_evidence/mutation_validation.json)。[工作改动 ZIP](file:///D:/eab-wt/cx-e2/reports/codex/R6FIX_evidence/working_tree_delivery.zip) 包含新增与修改代码/测试、文档和小型重放脚本/分项报告；不是完整仓库。辅助 [tracked diff](file:///D:/eab-wt/cx-e2/reports/codex/R6FIX_evidence/working_changes.patch) 不含新增文件，不能独自替代 ZIP 或当前工作树。

## 6. 遗留与信任边界

- 本工单 12 条没有已知未修项；≤900 s 的尽量目标未达到，耗时与原因见上。完整全套已经全绿。
- 本单修复不等于独立审查通过；仍需所有者安排新的只读 G6。未创建新 worktree，不能声称已满足对应退出纪律。
- 默认精确模型、显式 contact_window 的局部厚度语义、一般凹体全局 E / 整体最短分离尚未实现等原边界均不升级。
- 有理 oracle 和各构造自检有明确输入前提；未证明任意非法自交/非流形输入，也不是所有 binary64 数据的穷举证明。
- G6F 的 52 个新输入文件在任务起点未单独记录哈希；操作中没有改写它们，但交付清单中的当前哈希只记录现状，不能冒充起点字节一致性证明。已有 tracked 输入及 fixtures 另与起点备份核验。
- 最终证据清单、变更补丁和完整性核验见 [INDEX](file:///D:/eab-wt/cx-e2/reports/codex/R6FIX_evidence/INDEX.md)。

R6FIX_DONE
