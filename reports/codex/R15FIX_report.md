# WO-R15FIX 执行报告

2026-10-13；工作树 `D:/eab-wt/cx-e2`，分支 `codex-work`，基线 `03a41b56f900334e4ed9ecebc88cf1e8b824bd04`。
修改留在工作树，不 commit / push / reset / checkout / stash / worktree；不写姊妹仓库、其它工作树或外部设计正本，不删改 fixtures。

## 0. 计数、执行合同和证据入口

工单正文出现“6 条”和“11 条逐条”，但 `G6O_findings.json.findings` 与审查报告实际只有 **O01～O05 五条：0 critical / 3 major / 2 minor**。
沿用明确可核对的口径：本报告按 **5 条发现＋6 项交付验收，共11项**记账，不虚构 O06～O11。

- **目标**：五项真实入口先红后绿，修复同类输出构造问题；每项真实内部变异红；原测试与M4a门保留；完整测试节点一项不漏。
- **范围**：仅本工作树生产源、工具、新增测试、README／本树docs及R15证据。
- **非目标**：不改LP求解器／几何成员定义／全局Dual逐运算合同，不改姊妹语义或在线开关，不重新宣布M0退出或独立G6通过。
- **回滚锚**：[4645个已跟踪文件初始SHA256](file:///D:/eab-wt/cx-e2/reports/codex/R15FIX_evidence/tracked_before.json)、[源码/工具/测试/文档字节备份](file:///D:/eab-wt/cx-e2/reports/codex/R15FIX_evidence/rollback_before.zip)；基线HEAD未变。初始未跟踪审查输入原样保留。
- **复跑**：以下所有Python命令均需 `$env:PYTHONDONTWRITEBYTECODE='1'`；使用 `python -X utf8`，pytest关闭cacheprovider，basetemp在本树 `reports/codex/R15FIX_evidence/tmp/`。完整分片器另把TEMP/TMP也放此目录。
- **边界**：本单禁止新worktree，因此本树完整绿不冒充纪律D的新鲜树或独立G6。M0于2026-10-12的所有者管理退出保持；本轮仍交回独立复审。

## 01 — O01 major：接触合力的提前舍入

**修前红**：[原日志](file:///D:/eab-wt/cx-e2/reports/codex/R15FIX_evidence/o01_red.log)：`16 failed, 6 passed, 6 deselected in 0.18s`。
`ct=((1,0),(0,1),mu=1/2)`，`dead=(2^-60,-10,0)`，`live=(0,0,-1)`，tol=0；独立静力要求合力 `(-2^-60,10)`。
实际目标断言：

```text
assert r.contact_forces == [tuple(float(x) for x in exact)]
AssertionError: ('O01 complete exact resultant', 'single', 2,
  (Fraction(-1, 1152921504606846976), Fraction(10, 1)), [(0.0, 10.0)])
At index 0 diff: (0.0, 10.0) != (-8.673617379884035e-19, 10.0)
```

**根因与修法**：不止float零初值，`raw[j]*C.cols[j][i]` 本身也因方向为float提前舍入。
单体/多体均改为完整Fraction列乘积、Fraction零起算、逐接触完整和之后一次checked scalar；最终上溢具名拒答；非零下溢通过 `exact_contact_forces` 加 `contact_force_display_underflow` 明确标记并保留负零。
LP容量和lambdas证书未改；原按tol选列的显示政策保留。

**同根补漏**：高μ=2^20、W=2^1010时中间相消切向列约2^1029，最终 `(-1,W)` 可表达，旧 `fmag=_norm(fvec)`却在汇总前原生上溢。
[单独修前红](file:///D:/eab-wt/cx-e2/reports/codex/R15FIX_evidence/o01_columns_red.log)：`2 failed, 28 deselected in 0.13s`。
改为精确平方范数比较选列，无需构造中间范数，最终合力照常构造。

**修后绿**：[最终新48格](file:///D:/eab-wt/cx-e2/reports/codex/R15FIX_evidence/o01_final_verified.log)：`48 passed in 0.15s`；更早的力学相关组169格通过。
含2D/3D、单/多体、相消／本应为零轴、2^400尺度、一般非整数荷载、tol=0/1分界及产物互异。

**变异**：[最终12条机读证据](file:///D:/eab-wt/cx-e2/reports/codex/R15FIX_evidence/o01_mutations.json)、[原traceback](file:///D:/eab-wt/cx-e2/reports/codex/R15FIX_evidence/o01_mutations_final.log)：
每个API分别撤Fraction乘积、恢复float零、撤最终上溢检查、恢复中间范数、删除下溢标记、删除精确合力字段。
前两者红在 `O01 complete exact resultant`；第三者红在 `DID NOT RAISE`；第四者红在 `O01 selected intermediates must not be constructed`。
删除下溢标记／精确字段分别红在 `O01 nonzero force display underflow must be flagged` 与 `O01 exact underflow resultant certificate`。不是对生产输出追加假力。

## 02 — O02 major：骨形generic完整坐标／jet

**修前红**：[日志](file:///D:/eab-wt/cx-e2/reports/codex/R15FIX_evidence/o02_red.log)：`20 failed, 2 passed in 0.23s`。
中点 `cx-lx/2+lx/2` 原返回0而cx=2^-100应为 `7.888609052210118e-31`；cx种子1、lx种子2^60时完整中点导数应1，原为0。
目标是逐值断言 `actual.v == expected == raw.verts[8][axis]`、`actual.e == expected`，并包括D400下边界2^-400。

**根因与修法**：工具直接透传Dual，把全局合法的逐操作舍入用于本工具承诺的完整坐标。
新增私有有理 `_ShapeJet`，primal和每通道一直留到完整坐标，再用具名scalar构造；**全局Dual源码未改**。

**同类补漏**：pair上块中心 `center_z+lz` 不提前构造；sin用单位seed获得近似系数，原seed与amp在有理层结合。
否则seed=2^-1074配amp=2^400、seed=2^1200配amp=2^-400，会在最终jet可表达时仍因中间失域失败。
公开docstring明确自定义sin_fn收到宽1单位seed的Dual；依赖原通道宽度/seed而非一般链式法则的callback不再兼容。

**修后绿**：[兼容日志](file:///D:/eab-wt/cx-e2/reports/codex/R15FIX_evidence/o02_compatibility.log)：`157 passed in 46.11s`，含新30格、原R14域、旧灵敏度和Dual门。
一般位置nx=5/ny=3、双通道非均匀种子、缩放及全部顶点由独立Fraction完整表达式核对；libm系数仍是声明的近似采样模型，不冒充超越函数精确oracle。

**变异**：[5条证据](file:///D:/eab-wt/cx-e2/reports/codex/R15FIX_evidence/o02_mutations.json)分别恢复primal早舍入、jet早舍入、高度早舍入、pair中心早舍入、sin内先乘原seed。
各红在 `complete coordinate residual`、`complete jet residual`、`complete height residual`、`complete pair translation residual`、`representable complete phase jet rejected`。
[详细说明](file:///D:/eab-wt/cx-e2/reports/codex/R15FIX_evidence/o02_summary.md)。

## 03 — O03 major：贯入早返回的显示证书

**修前红**：常规单位盒A=B，delta=2^-2000，实际 `(margin_gap,_exact_closed,exact_distance_squared)=(0.0,None,None)`；
`penetration output must carry exact distance/closed certificates` 报红。
[O03/O05合并原红日志](file:///D:/eab-wt/cx-e2/reports/codex/R15FIX_evidence/o03_o05_red.log)：`18 failed, 1 passed, 3 deselected in 0.57s`（不重复按发现数相加）。

**根因与修法**：贯入捷径未执行常规分支的精确表达式／证书合同。delta/band先验证有限性，完整 `-delta` 后允许显示下溢，
同时给 `exact_distance_squared=0` 与独立 `_exact_closed=(delta>=0)`；普通非有限输入、最终上溢具名拒绝。
tiny负gap显示为负零时必须依证书读closed；负delta的sentinel并不closed。未把成员判定错记为此次缺陷。

**修后绿**：delta格含±tiny、2^-1075、2^-1074、1/8、0及非有限／上溢；与O05/同类合计26新增格通过。
**变异**：真实 `margin_contacts` 的贯入返回恢复 `0.0-delta` 和无证书构造，红在上述证书断言。
[详细红绿/变异](file:///D:/eab-wt/cx-e2/reports/codex/R15FIX_evidence/o03_o05_summary.md)。

## 04 — O04 minor：整数身份在JSON schema前被过拒收

**修前红**：[日志](file:///D:/eab-wt/cx-e2/reports/codex/R15FIX_evidence/o04_red.log)：`57 failed, 3 passed, 1 deselected in 0.76s`。
其中37格整数身份被 `JSON numeric literal: exact scalar is outside finite binary64 range` 拒绝，红在 `unbounded integer schema rejected an exact integer`。
另12格虽应拒绝连续量，但检查必须落到字段量名而非未知schema的词法阶段；其余8格为同类分派遗漏。

**根因与修法**：`parse_float`提前套连续输出域。现只精确解析Fraction并保留实数负零；字段确定后，整数核分母1、连续量核RN输出域，NaN/Infinity仍拒绝。
实际ContactRecord／嵌套Feature／bdda3d文件／工具document入口验证 `1e400`、`10.00e399` 的身份精确保留。

**同类补漏**：nsign/owner漏整数分派；t1/t2单独存在绕检查；d1/fa/coh/tens的整数token绕连续域。
按已有字段schema统一处置，复制输入dict而非原地改变用户数据；未知元数据不擅自加物理语义。

**修后绿**：[相关446格](file:///D:/eab-wt/cx-e2/reports/codex/R15FIX_evidence/o04_green_final.log)：`446 passed in 5.62s`；
[tools/M4额外77格](file:///D:/eab-wt/cx-e2/reports/codex/R15FIX_evidence/o04_m4_tools.log)：`77 passed in 9.92s`。新文件71格。
**变异**：[9个独立普通门真实红](file:///D:/eab-wt/cx-e2/reports/codex/R15FIX_evidence/o04_mutations.json)：恢复parser预检、撤nsign/owner分派、逐个撤6连续字段。
目标分别为身份接受断言与 `DID NOT RAISE ConstructionDomainError`，每次退出码1，非偶然setup错误。
[分报告](file:///D:/eab-wt/cx-e2/reports/codex/R15FIX_evidence/o04_report.md)。

## 05 — O05 minor：有限精确根的向上infinity显示例外

**修前红**：最大float M、真实有限H=M+1，height正确向上显示inf，但没有专属overflow字段；精确根和状态原来正确。
`finite exact root needs explicit upward-display overflow marker` 报红；五个边界格都明确检查字段，不误指控IEEE方向舍入错误。

**修法**：追加兼容默认字段 `EscapeSolution.height_display_overflow=False`；H>M且RN仍有限时height=inf、标记True、exact_height仍权威。
RN本身溢出仍具名拒答，不用M伪装向上界。API docstring与设计合同均明示此窄例外。

**修后绿**：H=M-1、M、M+1、M+2^969、M+2^970-1及RN溢出端点门；同O03合计26格 `26 passed in 0.58s`。
**变异**：生产返回构造把标记强制False，红在专属标记断言。
[六个几何内部变异总证据](file:///D:/eab-wt/cx-e2/reports/codex/R15FIX_evidence/o03_o05_mutations.json)另含O03与以下四类传播/构造门。

## 06 — 全仓同类扫描与追加修复

[可重跑候选扫描器](file:///D:/eab-wt/cx-e2/reports/codex/R15FIX_evidence/scan_numeric_surface.py)、
[逐族处置说明](file:///D:/eab-wt/cx-e2/reports/codex/R15FIX_evidence/numeric_surface_review.md)、
[几何早返回清单](file:///D:/eab-wt/cx-e2/reports/codex/R15FIX_evidence/o03_o05_scan.json)。
除01/02/04已列出的补漏，还实际修复：

1. `escape_height_brute` 丢弃完整解的标记、裸报inf：无证书可返回的float接口现具名拒答，撤检查变异红。
2. `dilatancy_profile` 丢根／标记：每行追加exact_height和overflow标记；相同大根不再inf-inf出NaN，撤标记变异红。
3. profile对已舍入根作差：顶面z=2^60+x的独立斜平面，原tan_psi=0、解析中心差分为1；现在精确根差后最终舍入，恢复显示根差变异红。
4. profile在求根前用Fraction delta乘float方向并点：delta=1/16±2^-100，原tan_psi=0、应1；现精确offset乘积。
   [此项单独修前红](file:///D:/eab-wt/cx-e2/reports/codex/R15FIX_evidence/o03_o05_offset_red.log)：`1 failed, 25 deselected in 0.16s`；恢复早乘法变异精确击中offset断言。

LP浮点候选层、outward区间、已定义零/inf哨兵、带证书视图与近似绘图摘要分别核对，不以“删光float”混淆各层语义。
扫描范围与未改理由明列，不声称有限候选清单等价于任意输入全域证明。

## 07 — 变异强度、独立参考与交叉核查

四组共 **32个内部变异实例**：O01 12、O02 5、O03/O05与geometry同类6、O04 9，均命中目标断言。
变异均进入真实生产函数／类方法，在进程内重编译或monkeypatch，随后恢复；没有往输出追加假数据。
几何主oracle为独立有理盒区间／斜平面，力学为单接触静力闭式，造型为完整Fraction坐标与jet，schema为精确文字数值。
原LP自校验只作补充，未以共享生产原语冒充独立主oracle。

团队交叉只读复核了O02 callback、O03/O05证书与负delta文案、O04 schema；O01中间范数失域被另一路独立复现后纳入修复。
[最终O01只读复核](file:///D:/eab-wt/cx-e2/reports/codex/R15FIX_evidence/o01_final_readonly_review.md)另跑新48格与原次正规容量门，共 `49 passed in 0.17s`；[静态／原门复核第二轮](file:///D:/eab-wt/cx-e2/reports/codex/R15FIX_evidence/final_readonly_review.md)核对183个原测试文件、3个分析器哈希和当前156条准入复核。
这些协作复核**不是审查方的独立G6退出审查**。

## 08 — 测试改写台账与静态准入维护

- 原已跟踪测试文件：**0修改、0删除**；不加skip/xfail、不放松原断言、不缩原网格。新增四文件共 **175格**：48+30+26+71。
- **本轮新门演进另记**：初版新增的“最终下溢必须异常”测试，在原成功域门揭示过拒答后，调整为“正确返回＋精确证书＋当且仅当下溢标记＋符号检查”，并增加正负边界、零、可表达次正规、上溢拒答、删标记／删证书变异。此为显式证书显示合同的调整，不谎称与原异常断言逻辑等价或严格加强；原仓任何门均未改。
- 初始12427节点来自上轮完整收集清单；本轮全量收集与执行并核每个原节点仍在，不能把集合子集当完整执行。
- 静态分析器源码未改；局部源码变更导致过期pin，手工按函数/站点复核后续签79项、删除9个已不存在节点，新增77个明确站点（16生产、61测试）。
- 新pin多数为真实被测API调用、独立参考的最终float、或故意的内部变异反射；没有全scope免检，没有扩大任意动态生产调用权限。
- [逐站点复核](file:///D:/eab-wt/cx-e2/reports/codex/R15FIX_evidence/static_review.json)、[复跑维护脚本](file:///D:/eab-wt/cx-e2/reports/codex/R15FIX_evidence/static_review.py)、
  [局部零诊断](file:///D:/eab-wt/cx-e2/reports/codex/R15FIX_evidence/static_local_final.log)。原reason保留为历史，追加的R15合同与当前设计同步优先；静态零诊断不冒充数值证明。

## 09 — README／canon／设计同步

[README](file:///D:/eab-wt/cx-e2/README.md)、[canon_map](file:///D:/eab-wt/cx-e2/docs/canon_map.md)、
[R15设计合同](file:///D:/eab-wt/cx-e2/docs/r15fix_design_sync.md)、
[精确谓词计划](file:///D:/eab-wt/cx-e2/docs/exact_predicates_plan.md)与R14设计补充均同步。
执行 `python -X utf8 tools/fix_canon_ptrs.py --apply`，[日志](file:///D:/eab-wt/cx-e2/reports/codex/R15FIX_evidence/canon_ptrs.log)：首轮 `10 rewritten; 0 kept`；补充字段后末轮另 `4 rewritten; 0 kept`，原指针门不改。
外部07设计正本只读，未回写；本树增补负责登记现行差异，不谎称完成外部编辑。

## 10 — 全套最后一行、耗时和M4a

首次完整覆盖12586项：`R15FIX_FULL_SUITE FAIL: 12586 calls; wall=572.010s; failures_or_skips=2; source_drift=0`。
两红均已定位，不掩去首次失败：
- canon新增顶行挤掉原门要求的“局部／Fraction／辅助／不是安全保证”合同文字：补回现行文字，不改文档测试。
- O01初版严格拒绝 -2^-1075 的接触力显示，让 `test_public_limit_single_and_multi_match_analytic_sliding_capacity[-1073]` 的正确可表达容量也无法返回。
  改为完整精确合力字段＋显式下溢标记；默认值追加在结果类型末尾，保持旧位置参数兼容。证书仅是tol选列后的合力，静力证明仍是lambdas。
  包含正负半最小次正规、最小次正规、真正零：标记当且仅当精确非零而显示零，符号保留；上溢仍拒答。
[修复后定向302格](file:///D:/eab-wt/cx-e2/reports/codex/R15FIX_evidence/pre_verified.log)：`302 passed in 1.39s`，含全部R15门、原R13力学与文档门、原指针和多体门。

完整覆盖 **12602 passed / 0 failed / 0 skipped**；新增175格，原12427节点全保留。
这是完整分片核验统计，不是单一串行pytest进程的伪造输出。

各分片最后一行原样：

```text
1825 passed in 556.03s (0:09:16)
2793 passed in 552.32s (0:09:12)
2438 passed in 553.09s (0:09:13)
5546 passed in 564.12s (0:09:24)
```

全套审计器最后一行原样：

```text
R15FIX_FULL_SUITE PASS: 12602 calls; wall=570.735s; failures_or_skips=0; source_drift=0
```

完整测试分片墙钟 **570.735s**；收集 **3.182s**；
两者合计 **573.918s**，4进程累计 **2250.706s**。
最终一轮目标≤900s：达成。
两轮全套（含各自收集）累计墙钟 **1149.113s**，超过900s；原因是首轮暴露两处回归后必须完整重跑，不能以定向绿替代。此累计还不含修复、红门和变异用时。
M4系列 **109项全通过**（包含离线shadow、adapter、VV reader等）；所有setup/call/teardown均pass。

[机器汇总](file:///D:/eab-wt/cx-e2/reports/codex/R15FIX_evidence/full_suite_verified/summary.json)；[全套原日志](file:///D:/eab-wt/cx-e2/reports/codex/R15FIX_evidence/full_suite_verified_runner.log)；[完整文件分片表](file:///D:/eab-wt/cx-e2/reports/codex/R15FIX_evidence/full_suite_verified/partition.json)。

复跑用 [run_full_suite.py](file:///D:/eab-wt/cx-e2/reports/codex/R15FIX_evidence/run_full_suite.py)：4个普通pytest进程按完整文件分片，不安装xdist，不作-k筛选。
先全量collect，再逐节点审计setup/call/teardown、分片collect并集、执行并集、不重复、无skip/xfail、原12427节点保留及源码/工具/测试/文档/policy运行前后hash无漂移。
不伪造单个串行pytest进程的总计行：逐分片pytest最后行与整体验证器最后行均保留原样。

## 11 — 完整性、失败台账、交付和遗留

- 审查输入/fixtures/M4a生产源不改；无提交和Git写命令。最终逐文件变化、文件哈希、未修改原门检查及交付链接清单见最终机读核验。
- 二次迭代新增参数化测试初次带默认参数，pytest collection拒绝；去掉默认值后重跑通过。静态批准脚本第一次读取了新增行后的旧行号，按fail-closed拒绝，重新扫描后定位当前AST，不放宽定位规则。
- O04首次新测试因basetemp父目录不存在产生setup error，创建本树tmp后重新取得正式断言红；不计作修前缺陷证据。
- 一次初始扫描脚本遇AnnAssign.value=None是脚本输入处理错误，修正后正式清单生成；不计作生产缺陷。
- PowerShell stdin默认ASCII使两份早期中文分报告出现问号，已按UTF-8重写并回读；生产代码/英文断言不受影响。
- 交付核验器首次按UTF-8读取O04的PowerShell UTF-16变异日志而失败；按BOM选择解码后重跑。原始证据字节保留，不作替换解码或忽略错误。
- 几何重复周边合集为避免与正式全套争用资源而中止，日志标 `INTERRUPTED_BY_COORDINATOR`，不算通过；由完整套覆盖。
- 残留边界：仍待审查方独立G6；本单未做新鲜worktree验证；已有libm／近似绘图与全域构造清单缺口不因本次有限回归自动关闭。M0管理退出与M4a离线边界不改。

最终核验：[机读验收](file:///D:/eab-wt/cx-e2/reports/codex/R15FIX_evidence/verification.json)；[全部交付链接与哈希索引](file:///D:/eab-wt/cx-e2/reports/codex/R15FIX_evidence/delivery_index.md)；[团队只读复核](file:///D:/eab-wt/cx-e2/reports/codex/R15FIX_evidence/final_readonly_review.md)。

R15FIX_DONE
