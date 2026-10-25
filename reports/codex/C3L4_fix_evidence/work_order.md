# WO-C3L4-fix — Claude 裁定摘要（本轮用户原指令的执行摘录）

工作树 D:/eab-wt/cx-c0，eab2-c3l4，cb14522，不 commit。中文报告。只有 src/eab 的阈值敏感性路径获准数学修订，其他 Python 数学合同不动。设计正本 docs/eab2_design.md SHA 保持，另写 amendment。

## 验收根因与复现

开阈多条机构分支同时到 mu* 时，单基隐函数斜率可错误 smooth exact_jet；Python/C++同错。闭阈选中射线基只在 [mu*,mu*] 可行也不是充分论证。
- g1_unreversed_t2（t=1/4），面2种子：block_2 v1 (+1/2,0)、v2 (-1/2,0)；block_3 v0 (+1/2,0)、v3 (-1/2,0)。真右1/2、左0。
- g1(t=1/8,h=1,unreversed)：face1..4 各右1/2、左0；all smooth1。
- 两根独立未反转梁 t1=t2=1/4：tP(R1,L0)、tQ(R1,L0)、tP+2tQ(R2,L1)。
- 再至少两例闭阈多分支（如独立闭阈梁同阈各种子），一例闭阈单点可行基语料 t1b/03。
- 核查员只读资料：C:/Users/m1517/AppData/Local/Temp/claude/C--Agent--claude/659f270b-c2f6-43a9-9717-6dc28c605be4/scratchpad/c3l4_accept/sensmath/oracle/ 的 repro_corpus_face.py、newcfg.py、patterns.py、faces.py、more.py 和 *.jsonl；../pyref/py_referee_faces.py。

## 新合同（须严格遵守，不自行放宽）

mu_crit(epsilon)=inf{mu in [0,mu_max]: L3 UNBOUNDED at (mu,p0+epsilon d)}。
D+ = lim epsilon->0+ (mu_crit(epsilon)-mu*)/epsilon。反向种子另得D-，普通左导=-D-。

**定理**：s有理，K=Q(eta)(epsilon)，序0<epsilon<<eta<<1（先epsilon最低次，系数再eta最低次定号）。若K上(a) mu=mu*+(s-eta)epsilon、p=p0+epsilon d存在对偶可行y，A^T y>=c（机构，证明NOT UNBOUNDED）；(b) mu=mu*+(s+eta)epsilon存在可行x0，A x0=b,x0>=0，和改进r，A r=0,r>=0,r_alpha=1，则D+=s。由实闭域转移，对所有足够小delta>0再足够小epsilon>0，在两界非无界/无界；mu单调嵌套给阈值夹逼。不依赖分支枚举完备。

1. 候选不是证明：可用已有-phi_p/phi_mu、临界面所有可行基（机构顶点/退化顶点全部基；闭阈改进射线多面体），组合开阈每基右上界根min、再基max，闭阈镜像；必要时小有理邻点精确求解取基。候选集/枚举上限写明，超限不报错值。
2. 证书：邻近有理点基提升至K（接触点/T/N随epsilon线性，mu含eta epsilon，矩三次以内），各分量K元素逐个字典序精确定号，核(a)(b)全部等式/不等式。可自适应Laurent截断，但只有精确系数足以决定符号才有效，禁容差。失败换候选/换基/缩探测点；仍失败该方向unresolved，新reason例如threshold_branch_certificate_unavailable；禁止退回单基。
3. 两方向有证且D+=-D- smooth，否则两侧有证one_sided；仅一侧有证按现有枚举表达，不补未证值。phi_mu=0等奇异维持singular/possibly_discontinuous。quality=exact_jet只给有K证书的值。新增可序列化branch_certificate（每方向s、类型、基列/行标签、邻近探测点、足够复核的多项式/级数系数）。tied_labels为候选分支中一阶根斜率等于所证s的约束标签；基依赖，逐侧核每个标签根斜率等于s，跨后端不同登记。
4. 阈值通道非零mu种子拒收，C++ INVALID_INPUT + field/index；语料若有逐条登记。
5. docs/eab2_design_amendment_20261023.md写定理、候选/证书/失败、tied_labels10-23裁定、闭阈单点问题；正本不动。

## 必须门

- Python与C++各一套上述具名复现，L4新branch族。
- frozen tia2d-2全部280、T1b/厚度全部sensitivity复跑；已正确认证smooth/one_sided应保持。任何值/类别变动（含unresolved退化）不改冻结文件，errata覆盖逐条旧/新/证明；floor以修后Python。
- 每个有精确阈值的语料几何至少6通道确定性单面/单顶点/随机有理非对称种子，双端精确比；同骨架精确critical_parameter于正负2^-k的2-3步长作红旗检查，认证斜率落在收敛差商括号外必红，差商不作证明。
- 源内变异：退回单基、只核(a)不核(b)、颠倒eta/epsilon定号、截断不足仍定号，各具名杀死。
- 独立harness不导入src/eab生产代码/C++helper，自实现K定号与基公式核每个branch_certificate。

## 验收minor

- L4 C++-only阈值对称接受：带L3逐例处置，独立核斜率并登记，floor不变。
- geometry_seed.cpp sense=-1删掉必须有门杀：C++ b边移动顶点手算dA；L4 regression_f共享顶点运动通道或每正式几何确定随机derived_seed通道。
- L4增加非零live/dead种子、若干人工非退化稳定基例；缩放y/min号/漏live列变异也须差分杀。
- meta加reflect_x/reflect_y/x-y互换（矩变号、掩码位换），源加g5_rotation_free_mid/g5_y_free/regression_f，杀M5忽略边向、M7锚点力矩平移变号。
- sensitivity字符串数组/种子校验错误走reject_c1，field为数组名、index为通道/元素，不全exception/UINT64_MAX。
- ABI机器表constants冻结全部整数#define EAB2_*；解析所有eab2_*(原型，非eab2_call_status返回/缺EAB2_API也报；冻结返回类型。陈旧release_acceptance改版本元数据或移出冻结块。release_abi.py支持python -I，不从自身目录import consumer。
- README到L4/发布ABI；ABI_CONTRACT写right_derivative,left_derivative普通左导=-D-、method、branch_certificate；seed B按sorted body_ids、solve_limit荷载按装配顺序；COMPLETE须配EXPLICIT_PAIRS；VC++2015–2022运行库MSVCP140/VCRUNTIME140/VCRUNTIME140_1依赖。
- consumer derived_seed为空 iff语料种子为空，否则失配。
- tied_labels_forensics.log UTF16LE转UTF8，audit扫.log；final_full历史2fail/44static、final_fast9070已被取代，移除或明确标历史。改报告凡把Claude裁定称用户决定的为Claude裁定。

## 约束/交付

- 不Git写/安装/下载/结束非自己进程，只本树写；只按H1本单追加外证据；tmp只ignored。
- pytest -p no:cacheprovider +显式basetemp；长跑落盘，中断整体重跑；开工全档4片、收尾快+全4片。不为文档重复全量。
- 真净增相对b34c966全部blob <=2MB，非新增改动大小和；UTF8无BOM、批处理ASCII，编译不入库。
- 历史主报告追加修复轮，不覆盖历史；另C3L4_fix_report.md，给定理实现、每族候选/证书成败/unresolved统计、复现/闭阈、语料errata、非对称红旗、变异、小项、完整build+六层C0/C1/LP/L1/L3全集/L4+releaseABI+consumer+快/全四片原始末行、真实净增、设计差异。
- 末行C3L4FIX_DONE / C3L4FIX_PARTIAL：清单 / C3L4FIX_BLOCKED：原因。发现本单/设计冲突或定理某类不适用必须停下写清楚报告，不自行放宽。
