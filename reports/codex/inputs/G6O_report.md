# WO-G6O：G6 第十五轮独立正确性复审

## 一、结论

- 被审 HEAD：`03a41b56f900334e4ed9ecebc88cf1e8b824bd04`；新鲜 detached 工作树 `D:/eab-wt/g6o`。
- **确认：0 critical / 3 major / 2 minor**，5 条均由主审实际复跑，按共因去重；没有修生产代码。
- **当前 HEAD 不满足独立 G6 的退出条件（0 critical / 0 major）。不能据本轮批准数学正确性退出。** 所有者已经决定的 M0 管理退出保持不变；本报告不撤销该历史决定。
- 自跑全套（串行，不使用实现方分片结果）：**12427 passed in 2211.32s**，进程退出码 0。全绿并未发现下面的生产构造/显示漏网。
- 本轮未确认新的默认几何成员状态错或 LP 精确容量/证书错；这不是对任意有限输入全域正确的证明。3 major 的范围分别是接触合力显示、Dual 示例几何完整构造、极小裕度贯入早返回的具名证书/输出域合同。

### 审查契约与回滚锚

目标是找错并给可运行证据，不修复。范围仅为本 HEAD 的只读源码、测试、文档及 `review/` 新产物；姊妹仓库、其他工作树、外部正本均只读；没有运行姊妹 exe、部署开关或任何 git 写命令。初始全部 tracked 字节 SHA-256 是回滚/完整性锚；结束核对 **4645 个 tracked 文件，0 变更、0 缺失**，HEAD 不变，git status 仅 `?? review/`。变异仅在进程内临时替换真实函数并恢复，没有改磁盘源码。

证据：[初始字节清单](file:///D:/eab-wt/g6o/review/evidence/tracked_sha256_before.json)；[结束完整性核对](file:///D:/eab-wt/g6o/review/evidence/tracked_sha256_final_verification.json)。

## 二、全套自跑

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONIOENCODING='utf-8'
python -X utf8 -m pytest -q -p no:cacheprovider tests --basetemp=D:/eab-wt/g6o/review/tmp_full_suite
```

原始结果：`12427 passed in 2211.32s`。带时区的开始/结束时间、墙钟秒数和准确 argv 见 [运行元数据](file:///D:/eab-wt/g6o/review/evidence/full_suite_result.json)；逐行 stdout 见 [全套原始日志](file:///D:/eab-wt/g6o/review/logs/full_suite.log)。pytest计时2211.32秒；外层墙钟2220.843秒，包含启动/收尾开销。
工单命令中 `<g6f 内 tmp>` 与 g6f 只读冲突，故临时目录全部放本树 review 内，不写 g6f。

主审另选 19 个模块/节点 selector 跑内部变异/独立性相关门：**356 passed in 4.46s**，见 [精选门日志](file:///D:/eab-wt/g6o/review/logs/root_selected_teeth.log)。分路定向结果为支持域303、力学432、缓存/窗口57 passed；它们与全套重叠，不能相加冒充额外总测试数。

## 三、逐条确认发现

|ID|等级|位置|一句话|
|---|---|---|---|
|O01|major|`limit.py:674-677`、`limit_multi.py:260-263`|tol=0 仍因 float 起始累加删掉非零合力或产生虚假力|
|O02|major|`tools/osteomorphic.py:24,48-49,143,147-149`|Dual 路径未完成具名完整坐标/jet 代数就逐步舍入|
|O03|major|`margin.py:483-486,494`|贯入早返回把非零 gap 下溢为0，未给指定 exact 显示证书或域异常|
|O04|minor|`readers/numeric_decode.py:17-20,38-40`|decimal 整数身份在 schema 前被连续输出域过拒收|
|O05|minor|`kernel3d/interlock.py:308-310`|有限根的向上显示为 inf，有限输出例外未明示；根和方向舍入正确|

### O01 · 接触合力提前舍入（major）

**输入→错输出**：二维 `point=(1,0), n=(0,1), μ=1/2, dead=[2^-60,-10,0], live=[0,0,-1], dim=2, tol=0`。独立静力/力矩给 α=10、λ=(5+2^-60,5-2^-60)，合力应 `(-2^-60,10)`，实际 `(0,10)`。大 W=2^60 时应 `(-1,2^60)`，仍报 `(0,2^60)`。三维 W=2^60 时本应 y=0，却产生约32的虚假 y 力。单体/多体共10格成立，合并计一条。

```text
single W=10 H=2^-60 status=optimal alpha=10 selfcheck=True
expected_RN=(-8.673617379884035e-19,10.0) actual=(0.0,10.0)
single3d W=2^60 H=1 selfcheck=True
expected_RN=(-1.0,0.0,1.152921504606847e18)
actual=(-0.9999999999999929,32.00000000000001,1.152921504606847e18)
```

原因是初始 `forces=0.0`，后面每一步 Fraction 列力加到 float。tol=0 排除了公开的显示截断豁免。α、λ 精确见证和自校验正确：文档明确静力证书是 lambdas，不指控容量/LP 核算错。错误限于高动态范围列力相消的普通输出，因此按窄范围 major 而非 critical。

复现：[O01脚本](file:///D:/eab-wt/g6o/review/repro/mechanics_force_report.py)；[主审实跑输出](file:///D:/eab-wt/g6o/review/logs/root_verified_mechanics_force_report.log)。建议保留现有选列政策，但逐接触逐分量先完整 Fraction 求和，再最终受检舍入；补相消、零分量、单/多体门与真实内部变异。

### O02 · generic Dual 骨形坐标/导数相消（major）

**输入→错输出**：`nx=2, ny=1, lx=2, amp=0, center_x=Dual(2^-100,(1,))`，中点 u=1/2 的完整精确 x 是 `cx-lx/2+lx*u=cx`，最终 RN 可表达。标量生成器返回 `7.888609052210118e-31`；generic 返回 `Dual(0.0,(1.0,))`。D400 下端2^-400同错。普通原点几何、`center_x`种子1与 `lx`种子2^60，完整解析中点导数应1，却返回0。

```text
center=2**-100: scalar x=7.888609052210118e-31
generic Dual x=Dual(0.0,(1.0,))
center seed=1, lx seed=2**60: exact derivative=1
generic Dual x=Dual(0.0,(0.0,))
```

参考只用独立 Fraction 完整坐标与导数，无生产 Dual 算术/libm。所有几何参数都在 D400，最终坐标和 jet 都可表达；不是“域外拒答正确”的格子。R14具名骨形构造承诺完整坐标最终舍入，但 `_shape_value/_shape_coordinate` 直接透传 Dual 导致中间舍入。**不要求任意用户 Dual 复合式最终只舍入一次**；只审核此具名工具构造承诺。primal 和 jet 共因只计一条。

复现：[O02脚本](file:///D:/eab-wt/g6o/review/repro/support_shape_dual_cancellation.py)；[主审实跑输出](file:///D:/eab-wt/g6o/review/logs/root_verified_support_shape_dual_cancellation.log)。建议仅此构造保留完整有理表达式及各 jet 至最终边界，补 generic/raw 同模型相消门，不以全局改变 Dual 逐操作语义修复。

### O03 · 贯入裕度早返回漏掉最终域/指定显示证书（major，窄合同缺口）

**输入→错输出**：同一单位盒 A=B，δ=`Fraction(2)**-2000`。独立盒区间证明严格贯入，工作空间距离0，文档定义完整 gap=-δ（非零）。当前返回 `margin_gap=+0.0`、`_exact_closed=None`、`exact_distance_squared=None`，无异常。

```text
delta=2**-2000; actual margin_gap=0.0; closed=True
label=('PENETRATING',)
exact_closed=None; exact_distance_squared=None
```

**确切计级理由**：`margin.py:483-486`点名完整表达式后舍入及“下溢伴随 exact_distance_squared、单独 exact closed”；通常非零量域外须具名拒答，带指定证书才允许显示下溢。`:494` 绕过两者。没有普通最终 RN 非零域内版本；本条是域外却未拒答/未履行具名证书合同，不能写成成员判错或 critical。

**反方与裁定**：PENETRATING 和 closed 实际完全正确，调用方结合标签与原δ可数学重建 gap。若所有者明确认可该标签已经是足够的精确显示证书，可以降minor。现行文字却明确指定两字段，且该路径没有权威 exact_gap；本报告采用当前严格字段合同计major，不隐藏这一裁级边界。

复现：[O03脚本](file:///D:/eab-wt/g6o/review/repro/support_margin_penetration_domain.py)；[主审实跑输出](file:///D:/eab-wt/g6o/review/logs/root_verified_support_margin_penetration_domain.log)；[正反第二意见](file:///D:/eab-wt/g6o/review/evidence/support_second_opinion.md)。建议贯入分支也完成精确-delta并走最终域检查，或明确允许下溢并补所声明 exact 显示证书；距离0/normal=None合法哨兵无需改动。

### O04 · 等值 decimal 整数身份过拒收（minor）

`step/block_a/bi=10^400` 的 int、Fraction、整数字面量均保留正确身份；同值合法 JSON decimal `1e400` 在 schema 分派前被 `_decimal` 的 `scalar_rational` 当连续量拒收。ContactRecord与真实bdda3d reader/tool四入口均复现。整数身份按现行分项合同无幅度界；这是入口/合同不一致，没有错误计算结果，计minor。

```text
int/Fraction/integer JSON accepted exactly
decimal JSON rejected: JSON numeric literal: exact scalar is outside finite binary64 range
```

复现：[O04脚本](file:///D:/eab-wt/g6o/review/repro/support_decimal_identity_domain.py)；[主审实跑输出](file:///D:/eab-wt/g6o/review/logs/root_verified_support_decimal_identity_domain.log)。建议先保留 exact token，按schema决定整数/连续量后再验各自域；不要在 parse_float 阶段套全部连续输出限制。

### O05 · 向上高度显示 inf 的支持域例外未明示（minor）

令 M=maxfloat 的精确有理值、H=M+1，A=`[-1/8,1/8]^2×[0,H/2]`，B=`[-1/4,1/4]^2×[-1/4,H]`。独立 z 开区间判据给最早非贯入根 H。当前 exact_height=H、根处state=0均正确，但height=inf，未给overflow标记或具名拒答；六格网格中3格如此。

```text
target_RN_finite=True; height='inf'
exact_height_equals_interval_root=True; nonpenetrating_state=0
```

**降级理由**：扩展IEEE集合的向上舍入本来就为inf，没有正确有限向上显示值；API已有完整权威 exact_height，故不称“逃逸根错/问题被判无界”。当前通常有限输出条款与专属向上显示条款存在张力，且未明示此例外，计minor。不可建议用M代替H（M不是上界）。

复现：[O05直接probe](file:///D:/eab-wt/g6o/review/repro/geometry_escape_output_overflow_probe.py)；[主审输出](file:///D:/eab-wt/g6o/review/logs/root_verified_geometry_escape_output_overflow_probe.log)；[六格合同断言脚本](file:///D:/eab-wt/g6o/review/repro/geometry_escape_nonfinite.py)。六格脚本最后的finite-policy目标断言按当前实现exit=1；这个红只证合同张力，不是数学根错误。建议明示并标注overflow显示，或依据所有者finite政策最终具名拒答。

所有完整字段与原始输出：[机读发现](file:///D:/eab-wt/g6o/review/G6O_findings.json)。

## 四、按工单顺序的审计记录

### 1. 第十四轮五条重放

原脚本只复制进本review再改路径，不写g6n。原“缺陷必须成立”的断言在修后可红，不能当产品红；主审另运行修后合同版。

|原项|当前实跑|裁定|
|---|---|---|
|N01 巨大奇整数幂|6格，primal -1 / 正确导数，整数/半整数精确分派|已消解|
|N02 精确角度/一般幂早float|30格，不能无损表示的实参在转换前具名拒绝；支持的微角对照保留|按新域已消解，不证明libm全域误差|
|N03 字面量下溢/上溢|43格，真实reader/vector/scalar及直接Fraction越界拒答|已消解；同类另发现O04|
|N04 高μ锥不安全|μ=1e16/1e17已在公共入口按μ≤2^20拒答；成功射线逐个精确认证|域外具名拒答正确|
|N05 一般相对余弦容量界|数值反例仍成立，但现行文档已撤回该一般界，只保留条件模型集合包含|错误声称已消解，不计旧反例残留|

[主审R14重放](file:///D:/eab-wt/g6o/review/logs/root_replay_support_r14_replay.log)；[原脚本输出/台账](file:///D:/eab-wt/g6o/review/evidence/support_r14_old_replays.json)。

### 2. 分项支持域专审

- binary64无损实参：约分分母为2幂、去尾零有效位≤53、最低指数≥-1074、最高指数≤1023的推导与实现相符；独立292格（101接受/191拒绝）一致。
- 连续文本最终RN胞：0或 `2^-1075 < |q| < 2^1024-2^970`，开端点定义正确；整数身份应另走schema，O04是混用。
- μ≤2^20：`μ·2^-52≤2^-32`的尺度估计成立，但不充当内接证明；成功生成元以独立 `n·g>0`、叉积平方/圆锥包含和黏聚正交/单位盘检查认证。4270成功射线全部通过；65个μ=2^-50格因有限调整无法认证而具名拒答，公开允许，不计发现，也不声称界内必成功。
- D400只约束示例近似物理输入，不保证三次量/相消/病态除法输出；支持域仍需最终量条件。O02是条件均满足却错误；O03是早返回遗漏最终域/指定证书。一般libm/非整数幂误差证明仍PARTIAL，不以“未证明”另记发现。
- 面噪声两次相对舍入界 `(1+u)^2-1=2u+u²` 推导适用于正周长求和加最终RN，不宣称多根式和正确舍入。角度与幂的无损实参检查只是输入保真，不是超越函数精度定理。

独立controls主审实跑：292实参格、6μ边界格、2480 Dual单操作格（1730正确/750具名越界）；详见 [主审控制实验](file:///D:/eab-wt/g6o/review/evidence/root_control_results.json)及[分项推导/入口覆盖](file:///D:/eab-wt/g6o/review/evidence/support_review.md)。
另专门把纯判定与构造分开：自建有限Fraction盒/多边形，尺度2^±2000、2^±4000、平移2^4000及短特征2^-2000，119格公共成员/相交/精确凸性均与独立区间参考一致，没有借内部构造输出域拒答。主审已独立再跑；见 [纯判定全量程有限格](file:///D:/eab-wt/g6o/review/evidence/support_predicate_fullrange.json)。有限格不证明任意曲面全域。

### 3. 历轮同类漏网与新diff

对噪声带、舍入前置、原点/力矩、LP候选证书、输入解码、Dual通道、几何模型混用、缓存别名、oracle共用、门无牙及文档夸大等类别做本树扫描/定向重放；实际新错为上表，不把静态例外或无证明本身计发现。
`git diff 878d4f0..HEAD -- src tests tools docs`：36文件，6097插入/536删除，其中policy文件占4808行变更。源码/数学入口由支持、力学、几何三路细核；policy只做结构/站点审阅，没有把每个人工例外逐个重新证明。
[新代码完整diff](file:///D:/eab-wt/g6o/review/evidence/new_diff_878d4f0.txt)；[E2–PERF旧测试完整diff](file:///D:/eab-wt/g6o/review/evidence/tests_diff_b6126cf.txt)。

## 五、九镜头覆盖与结果

|镜头|具体工作与结果|范围限制|
|---|---|---|
|1 精确声称/浮点分支|39个src模块AST全列1680比较、230词法候选；几何1115站点按函数族分类；区分显式窗口、候选过滤/精确兜底、构造显示、历史私有链。LP容差只候选；resolvability不改答案。确认O01–O03构造漏网|AST不是运行可达性或全域证明；未将出现float/1e-12直接算缺陷|
|2 过滤/缓存等价|72000独立符号、7000 LP reduced_sign、450 BFS+12状态；几何37缓存key/内容/返回别名检查，57定向门；量程/次正规/下溢/溢出/强相消均有格|未穷举任意自定义标量协议、所有mutable/Dual缓存别名与每条快路的全输入界|
|3 oracle独立|根冻结输入后，毒化26个生产原语并清oracle缓存，独立SAT/表面/2D/盖距答案不变；审读g03_exact、g0_oracle、独立构造reference。明确PERF旧新路径对拍共用原语只是等价检查，不充当主oracle|模型定义共用与原语共用分开；跨层共享造型/盖枚举仍不是零共用|
|4 旧门迁移|b6126cf..HEAD列157个共享改写test/helper及删除断言；精读边界/不变性/G0/hull/window重点；356精选门含真实生产内部变异。未确认旧门有效性质被偷删的新反例|没有对157函数逐一跑旧/新配对变异，不能声称“所有旧门都未变弱”|
|5 几何独立压力|本轮新Fraction H平面交/Cramer/rank 280重叠+1120成员、线段QP600、闭窗700；旧独立几何oracle本树重放，凸/凹/退化/大平移/单位缩放均有格，零差分|有限有效实体族，不是任意凹体全局E/最短脱离完备证明；无效自交表面不在输入前提|
|6 局部贯入窗口|51自有区间格：30六轴/6薄壳接受/15拒绝；67壳半径检查；六轴只证rho≤w，薄壳证局部径向厚度，闭空腔rho≠PD_closed及旋转依赖明确|没有发现当前可靠性析取反例；不把窗口当完整欧氏PD或旋转不变算法|
|7 极限分析|450独立BFS原始/对偶/目标和float视图一致；错误α/机构/力矩真实候选被精确自校验拒绝；删除锥认证及忘参考点内存变异红在物理不变量；O01合力显示仍错|静力证书lambdas正确不代表contact_forces显示正确；未跑大稠密LP/全病态枚举|
|8 文档/代码/正本|四份指定文档116声称行测试名/文件存在核对无缺失；命名门实际通过；读正本01、03、07及00相关理论/归属/衔接，核canon第八节；N05错误一般界已撤回|存在/通过不等于断言了全文所有量词。历史状态段、条件模型、PARTIAL逐项区别；文献优先性/产品史未重新外网查证|
|9 历史重放|第五轮50条中25不同条实际主审重放；R14全部5条重放；原数据/实际舍入几何模型区别保留|另25条原始复现未逐条执行，详列下文；不能宣称50条全闭合|

关键证据：[全src比较索引](file:///D:/eab-wt/g6o/review/evidence/all_source_comparisons.json)、[几何分支分类](file:///D:/eab-wt/g6o/review/evidence/geometry_branch_inventory.json)、[缓存索引](file:///D:/eab-wt/g6o/review/evidence/geometry_cache_inventory.json)、[生产原语毒化验证](file:///D:/eab-wt/g6o/review/evidence/root_oracle_poison.json)、[文档指针台账](file:///D:/eab-wt/g6o/review/evidence/root_doc_claim_ledger.json)。

### 测试迁移与“门有牙”的具体限界

旧容差模型把实际已微凹/微贯入的舍入输入强行当理想对称边界；新门保留格子并对实际Fraction几何核，不将旧常量计数/边界标签当不变量。主审读了二维真实bb52入口、二维/三维不变性、G0三票、hull掉点及Lipschitz门的前后差异；新default exact与显式window各自核。没有看到新增skip/xfail把所有边界情况绕开；这是有限审读结论。
内存变异删除真正锥安全认证，独立物理圆锥断言和 selfcheck 均红；忘减实际LP参考点，红在独立静力/互补检查，非偶然对偶顶点分量。root_selected_teeth还实跑原有翻法向、掉凸包点、丢窗口方向、壳窗翻倍及造型提前float变异门。SHA保持不变。
[变异断言/完整性证据](file:///D:/eab-wt/g6o/review/evidence/mechanics_mutations.json)；[157函数对照台账](file:///D:/eab-wt/g6o/review/evidence/test_migration_inventory.json)。
另补五项精选逐条旧/新断言审读及三处实际内部变异，主审已独立再跑：strict VE/EV被错误标成boundary，旧断言体PASS而新门在 `test_invariance_2d.py:154` 独立标签集红；真实微小escape根夹0，旧断言体PASS而新门在 `test_invariance_interlock.py:312` 独立精确根红；一般凹边界误报外部，新门在 `test_kernel2d_review.py:506` 精确分类红。没有旧抓新放的新反例。旧断言体使用当前helpers/SUT以隔离断言语义，**不是旧commit整环境复演**；五项只跑代表格，剩余152项没有逐项配对变异。见 [五项旧新审读](file:///D:/eab-wt/g6o/review/evidence/geometry_migration_review.md)和[主审再跑变异输出](file:///D:/eab-wt/g6o/review/logs/root_control_geometry_migration_probe.log)。

### 正本07对代码（canon_map第八节）

07是目标规格而非当前交付清单：现表已区分四生命周期字段与仅source/canonical_key的溯源、3类读取器与尚缺2线读取器、窄快照与完整benchmark、G1仅bb52检测53条而非锁态/位移、G2手写np列表而非tf05检测、G3非批量逐位、G4静态关闭/有限多步、G5/M4a离线而非已接姊妹开关。FF/FE只标签组、不冒充CoverType产出；EEP没有合并规则。源非平面描述符不冒充实体完整法锥，凹块盖裁剪/全局E仍M3未实现。
正本01的闭集PD与现行内部不交rho确实不同，当前文档已经显式说明封闭空腔反例；不重报已订正的“六轴⇒PD_closed”旧声称。正本03 KKT虚拟力后半无实现、07外部开关未部署均明确，不因“应有功能”缺少而报新的核心计算错。

## 六、第五轮25条重放明细

统一按原始 `findings[]` **1-based**：`[7, 9, 10, 11, 20, 21, 22, 23, 25, 26, 27, 28, 29, 30, 31, 34, 37, 38, 40, 41, 42, 43, 44, 45, 47]`。几何分路文件名是0-based，力学是1-based，已专门归一化，不能误报重复/计数。
这25条包括冻结EE符号、切向退化拒答、静力/对偶注入、远体可分辨性、刀刃无界风险、薄VV、二维微凹/折回/错误半平面、近竖直逃逸、近平行EE、首入尺度、二维hull、G0豁免/默认eps/微倒角/锥最近点等类别。旧错误未再现；公开的新拒答、当前输入的精确微凹和canonical模型如实记录，不把脚本exit0当一切语义自动正确。
[逐条原发现/当前输出/脚本台账](file:///D:/eab-wt/g6o/review/evidence/root_g6e_replay_ledger.json)，含每条原文与主审实跑输出；[17脚本主审运行记录](file:///D:/eab-wt/g6o/review/evidence/root_replay_results.json)。

## 七、未确认与不计发现

1. μ=2^-50部分界内normal无法在有限次RN调整中认证：具名拒答且现行文档允许，不计发现，不将μ界宣传为全界内成功。
2. 极大Fraction window触发原生OverflowError/部分纯构造在rounding_floor处具名拒答：无已确认错结果，不扩充major；纯谓词与构造须分开。
3. 通用libm/Decimal80幂的全输入误差证明、静态扫描2365遗留排除“未证明”：按所有者决定，不作为发现。静态扫描绿不是主数值保证。
4. O03没有最终RN非零域内实例，且闭合状态正确；正反解释已列，不把缺字段包装成几何critical。
5. O05正确向上舍入和权威精确根，已从原major候选降minor；六格finite-policy红不证明数学根错。

## 八、完整性批评

- 全仓39个src模块已列静态比较，但**不是39模块逐行数学证明**。几何19模块重点函数族读核；geom3历史私有浮点链只读相关段/调用搜索；冻结Dual全部导数没有逐式重证。支持路全文读numeric_domain/construction/dual/contact_record、5类reader、adapter及相关工具；力学路全文读limit/limit_multi/lp/margin。
- 工具diff入口已查，未全文细读所有gallery/CLI/静态分析器实现和每条4808行policy变更；未运行capture/ingest姊妹过程，不做真实求解器或工程标定。fixture读取/哈希门经过全套，但没有重跑所有原exe。
- 157个迁移函数/helper有完整AST台账和关键前后断言审读，**未逐个旧/新配对变异**；不能无遗漏地认定每个旧门都有牙。现有门的红并不能证明每条潜在缺陷都会红。
- 正本01/03/07已阅读用于对应；00只读相关内核/归属/衔接段，未重新核全部文献史/市场段。指定仓内文档/报告按数学合同、迁移台账与当前/历史边界核查，未重新证明每条历史实测数字与每个“已验证”量词。116行指针台账不冒充全部语义证明。
- 第五轮剩余原号未逐条执行：`[1, 2, 3, 4, 5, 6, 8, 12, 13, 14, 15, 16, 17, 18, 19, 24, 32, 33, 35, 36, 39, 46, 48, 49, 50]`。部分文档项已读核，但不冒充原复现重放；其他第6–13轮以现行分类/回归门和本树重放为主，没有逐条重跑历轮全部脚本。
- 未穷尽任意非星凹体、任意折面/多壳拓扑、所有瞬态路径、任意可变数值协议、任意病态大LP、资源复杂度与跨平台超越函数；随机/参数格零错不是全域定理。
- 所有新发现由根审查方再实跑；分路证据经过中文可读/JSON解析核验。没有把未确认假设计入critical/major。

补充完整覆盖与未读清单：[几何分审](file:///D:/eab-wt/g6o/review/evidence/geometry_coverage.md)、[力学分审](file:///D:/eab-wt/g6o/review/evidence/mechanics_coverage.md)、[支持域分审](file:///D:/eab-wt/g6o/review/evidence/support_review.md)。全部可交付文件见 [成果索引](file:///D:/eab-wt/g6o/review/ARTIFACTS.md)；每条建议均未实施。

G6O_DONE critical=0 major=3 minor=2
