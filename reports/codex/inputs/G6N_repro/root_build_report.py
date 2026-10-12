"""Build the final Chinese audit only after the primary full suite completes."""
from pathlib import Path
import hashlib
import json
import re
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
REV = ROOT/'review'
def readj(path): return json.loads((ROOT/path).read_text('utf-8-sig'))
def link(path, title=None): return f'[{title or Path(path).name}](file:///D:/eab-wt/g6n/{path})'
def readlog(path):
    data=(ROOT/path).read_bytes()
    return data.decode('utf-16' if data.startswith((b'\xff\xfe',b'\xfe\xff')) else 'utf-8-sig')

suite=readlog('review/logs/full_pytest.log')
exitcode=(REV/'logs/full_pytest_exitcode.txt').read_text('utf-8-sig').strip()
match=re.search(r'(\d+) passed in ([\d.]+)s(?: \(([^)]+)\))?',suite)
assert exitcode=='0' and match, 'Primary suite must complete successfully before finalization.'
assert 'failed' not in suite[-300:]
integrity=readj('review/evidence/final_integrity.json')
assert integrity['tracked_bytes_unchanged']
primary=readj('review/evidence/primary_confirmation.json')
bycase={x['case']:x for x in primary['results']}
support=readj('review/evidence/support_findings.json')['findings']
findings=[]
for i, item in enumerate(support,1):
    item=dict(item)
    item['id']=f'G6N-N0{i}'
    item['file:line']=item['file']
    item['file']='src/eab/dual.py'
    item['line']=108 if i==1 else 254
    item['primary_verified']=True
    item['verified_log']=bycase['N01' if i==1 else 'N02_inside']['log']
    if i==2:
        item['file:line']='src/eab/dual.py:254-276,279-289'
        item['how_to_reproduce']='python -X utf8 review/repro/root_trig_exact_argument.py; python -X utf8 review/repro/support_dual_trig_domain.py'
        item['repro_path']='review/repro/root_trig_exact_argument.py'
        item['verified_output']=bycase['N02_inside']['verified_output']+'\n'+bycase['N02_outside']['verified_output']
        item['suggested_fix']='保留给定 int/Fraction 参数语义；对巨大参数采用可认证的精确约减或明确检查可支持的参数域，不能只检 D400 幅度。对域外输入应具名拒绝，atan2 可用精确齐次缩放避免参数先归零。补大整数参数及 tiny/tiny 真实入口门；不把 libm 系数模型当作输入早舍入许可。审查方不修复。'
    else:
        item['verified_output']=bycase['N01']['verified_output']
    findings.append(item)

findings.append({
    'id':'G6N-N03','severity':'major','file':'src/eab/contact_record.py','line':184,
    'file:line':'src/eab/contact_record.py:183-186,221-222; src/eab/readers/bdda3d.py:67,85',
    'conclusion':'JSON 数值字面量与 ContactRecord 解码在检查之前转 float，有限非零输入静默变成 0 或 infinity；实际 bdda3d 读取路径也漏检。',
    'failure_scenario':'合法 JSON 含 normal=[1e-400,0]、ref_points 等五类向量字段时，records_from_json 返回零；1e400 返回 inf，没有入口异常。ContactRecord.from_dict 的 Fraction(1,2**2000) 也被裸 float 归零，另调用 validate 仍接受。实际 bdda3d.load_records 读取 area:1e-400 返回0，而同值字符串 area:"1e-400" 正确抛 ConstructionDomainError。共21个 ContactRecord 格与真实文件路径佐证。',
    'how_to_reproduce':'python -X utf8 review/repro/root_records_domain.py; python -X utf8 review/repro/support_json_reader.py',
    'repro_path':'review/repro/root_records_domain.py',
    'suggested_fix':'从 JSON parse_float 层起保留精确十进制值，在转最终 float 前走量名化 scalar_rational 边界；ContactRecord._decode 的裸 float 也需同样规则。补真实文件入口的 numeric literal，而不是只测字符串或直接 Fraction 调 record_from_entrance。审查方不修复。',
    'verified_output':bycase['N03_records']['verified_output']+'\n'+bycase['N03_reader']['verified_output'],
    'verified_log':bycase['N03_records']['log'],'additional_verified_log':bycase['N03_reader']['log'],
    'primary_verified':True,
    'grading':'只在有限精确值越过 binary64 舍入零/无穷边界的读取输入族触发，按窄范围错误计 major。不是仅静态绕过；与两个读取入口同根，合并计一条。',
    'independent_oracle':'Fraction(decimal token)，精确 RN-even 零胞/上溢胞端点；不调用生产构造来决定 expected。'
})
cone=dict(readj('review/evidence/limit_findings.json')['findings'][0])
cone['id']='G6N-N04'; cone['conclusion']=cone['summary']; cone['repro_path']='review/repro/limit_cone_safety.py'
cone['verified_output']=bycase['N04']['verified_output']; cone['verified_log']=bycase['N04']['log']; cone['primary_verified']=True
findings.append(cone)
optional=REV/'evidence/document_confirmed_by_primary.json'
if optional.exists():
    item=json.loads(optional.read_text('utf-8-sig'))
    assert item['primary_verified'] and item['id']=='G6N-N05'
    findings.append(item)
counts={s:sum(f['severity']==s for f in findings) for s in ('critical','major','minor')}
unconfirmed=readj('review/evidence/geometry_findings.json').get('unconfirmed',[])
if (REV/'evidence/document_claim_review.json').exists():
    claims=readj('review/evidence/document_claim_review.json')
else: claims=None
result={
    'work_order':'WO-G6N','head':integrity['head'],'reviewer_role':'独立正确性审查；不修生产代码',
    'generated_utc':datetime.now(timezone.utc).isoformat(),'confirmed_counts':counts,
    'strict_G6_exit_passed':counts['critical']==counts['major']==0,
    'owner_M0_decision':'已按所有者决定退出；本审计不修改管理决定。本轮严格0 critical/0 major验收条件未达。',
    'findings':findings,'unconfirmed':unconfirmed,
    'verification':{'full_suite_mode':'单 pytest 进程串行；其间并行子审查探针，不作为无竞争性能基准',
                    'full_suite_command':'PYTHONDONTWRITEBYTECODE=1 python -X utf8 -m pytest -q -p no:cacheprovider tests --basetemp=D:/eab-wt/g6n/review/tmp_full',
                    'full_suite_passed':int(match[1]),'full_suite_seconds':float(match[2]),
                    'full_suite_exitcode':int(exitcode),'full_suite_log':'review/logs/full_pytest.log',
                    'primary_confirmation':'review/evidence/primary_confirmation.json',
                    'r13_replay':'review/evidence/r13_replay.json',
                    'legacy_replays_unique':25,'legacy_primary_evidence':'review/evidence/primary_coverage_replay.json',
                    'tracked_files_hashed':integrity['tracked_count'],'tracked_bytes_unchanged':True,
                    'integrity_evidence':'review/evidence/final_integrity.json'},
    'coverage_limitations':[
        '全src 38模块做AST索引不等于逐行/逐分支数学证明；geom3/frozen部分路径为重点阅读而非全部公式重推。',
        '156个改写共享测试/辅助函数未逐一全部重新造旧红新绿变异；有执行和阅读的具体门另列。',
        '2674静态例外、全部915 API未逐条证明；2365遗留排除未证明按所有者规则不计发现。',
        '没有一般libm/非整数幂的跨平台全域误差证明，没有任意凹体全局E或任意折面体完整对拍。',
        '文档索引115条不等于115条声称全部语义认证；按文档核验账区分完整核对/仅存在性/历史/未核。',
        '外部正本00/01/03/07已通读或分段读完；其中文献事实/优先性未重新访问原论文验证，不计为新文献审查。',
        '姊妹exe/输入不重运行；本轮只用冻结输出，不作工程标定/性能达标证明。'
    ]}
(REV/'G6N_findings.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')

lines=[f'''# WO-G6N：G6 第十四轮独立正确性复审

## 一、结论与边界

被审对象：新鲜 detached 工作树，HEAD **`{integrity['head']}`**。本轮是审查方，不是实现方；**没有修代码，没有修改任何已跟踪文件，也没有 Git 写操作**。

确认计数：**critical={counts['critical']} / major={counts['major']} / minor={counts['minor']}**。全部确认项均由主审在现有、未变异的生产代码上亲自复现；静态绕过、未证明排除和响亮的构造域错误没有升级成发现。

**按“0 critical / 0 major”严格 G6 退出条件，本轮不通过，不能据本轮签发 M0 的独立正确性退出证书。** 所有者已让 M0 管理性退出并并行复审；本报告不擅自撤销或改写那项决定。

完整现行套件：**{match[1]} passed in {match[2]}s；exit=0**。这与确认发现不矛盾：仍有未覆盖的真实数值错误，以及离散锥正常答案反驳核心量化承诺的实例。新鲜树全绿不是独立 G6 退出的充分条件。

### 主要交付

- {link('review/G6N_findings.json','机读发现与核验状态')}
- {link('review/evidence/primary_confirmation.json','主审逐条真实复现输出')}
- {link('review/evidence/final_integrity.json','4402项跟踪文件 SHA-256 核对')}
- {link('review/ARTIFACTS.md','全部审查产物、可点击链接与哈希索引')}

## 二、确认发现表

| ID | 分级 | 位置 | 一句话结论 |
|---|---|---|''']
for f in findings: lines.append(f"| {f['id']} | {f['severity']} | `{f['file:line']}` | {f['conclusion']} |")
lines.append('''
**分级理由与去重**：N01 是巨大精确整数指数；N02 是巨大精确角参数或极小同尺度参数；N03 是数值输入跨舍入零/无穷边界；N04 是高摩擦方向失分辨。前四条依工单“错误答案但范围窄”计 major，不冒充一般正常尺度 critical。N03 多个字段/两个入口计一个根因；N04 同根的越锥、无界、自检和文档问题不拆成多条。N05 是普通参数下的核心相对量化承诺错误，代码正常求解离散锥；依工单“文档对核心承诺的错误陈述”计 major，与N04舍入根因不同。

### N01：整数幂先转 float，奇偶性静默丢失

输入 `Dual(-1.0,(1.0,)) ** (2**54+1)`；把指数写成 Fraction 仍复现。真实代数结果的 primal 是 -1，导数是正指数，最终 RN-even 为正 `2**54`。当前先在 dual.py:108 转 float，指数变成偶数，结果 primal 和导数符号同时反转。指数在 D400，结果可表达；不是一般非整数幂的误差证明缺口。
''')
lines.append(f"重放：{link('review/repro/support_dual_power.py')}；输出：{link(bycase['N01']['log'])}\n\n```text\n{bycase['N01']['verified_output'].strip()}\n```\n")
lines.append('''
建议：保留精确指数，在转 float 前按精确整数/半整数分派，完整表达式后一次舍入。**本轮不实施修复。**

### N02：三角函数丢给定参数；atan2 两个非零数先变零

支持域内 `q=2**54+1`（int 也直接接受，不依赖 Fraction 类型注解争议）：当前 sin 为 0.8973347529975925，而独立有理区间包住 0.11344832269377987，绝对误差 **>0.783886**；cos 也有 **>0.552193** 的宏观误差。另一个 `q=2**54+1/3` 也错。Dual primal 同错。

主 oracle 不用 math/Decimal/mpmath 或生产构造：Machin 恒等式 `pi=16 atan(1/5)-4 atan(1/239)` 配交错有理尾界；有理 2pi 约减区间；42项 Taylor + 下一项界 + Lipschitz 常数1包住全部约减误差。所有通过/失败断言用 Fraction，float 仅显示。第二审查路线独立核了 Machin 恒等式、尾项单调条件和周期区间，并复跑；没有另行独立认证导数通道。

域外的 `x=2^-1075/2^-1100/2^-2000` 是有限非零 Fraction。`check_input` 若被调用会正确拒绝，但实际公开 atan2(x,x) 没有检查，返回0；真实角的独立积分界在 `(1/2,1)`，应为 pi/4。其输出是普通可表达非零角，不能用“最终角不可表达”免责。

这是**现有答案错误**，不是仅因通用 libm 误差界尚未证明而报缺陷。代码承认 libm 系数近似，不能把给定参数早舍入造成0.78误差或零角写成系数的一ulp缺口。
''')
lines.append(f"重放：{link('review/repro/root_trig_exact_argument.py')}、{link('review/repro/support_dual_trig_domain.py')}；{link('review/evidence/limit_trig_cross_review.md','独立数学交叉复核')}。\n\n```text\n{bycase['N02_inside']['verified_output'].strip()}\natan2(2**-1075,2**-1075)=0.0；独立角区间=(1/2,1)\n```\n")
lines.append('''
建议：精确参数约减或明确且可认证的输入支持域；无能力保证的输入具名报错。只加 D400 幅度检查仍修不了本例域内相位误差。atan2 可独立精确齐次缩放。详尽输出在机读发现和主审日志。

### N03：JSON 真入口没有守住数值边界

五类向量字段 `ref_points/normal/params/shear/slip_ref`、四个正负极值 token，共20格；再加 direct from_dict 的精确 Fraction，共21格。`1e-400` 是有限非零十进制数，解码返回0；`1e400` 是有限十进制数，入口返回inf，另行 validate 只能事后检查inf，无法发现已归零。直接 Fraction 避开 JSON 来源争议，仍被 `_decode` 的裸 float 清零并通过 validate。

真实 bdda3d 文件 `area:1e-400` 被默认 json.loads 先归零，后面的 checked scalar_rational 只看见0；同值字符串却被正确拒绝。R13FIXb 原门直接传 Fraction 给 record_from_entrance，没有穿过真实 JSON 数值 literal 解析，因而漏网。

独立参考是 Fraction 对原 token 的精确解析，以及 RN-even 零/无穷胞端点，不是用生产 constructor 判断 expected。
''')
lines.append(f"重放：{link('review/repro/root_records_domain.py')}、{link('review/repro/support_json_reader.py')}；{link(bycase['N03_records']['log'],'21格完整主审输出')}。\n\n```text\nContactRecord.from_dict: Fraction(1,2**2000) -> normal=(0.0,0.0); validate=accepted\n{bycase['N03_reader']['verified_output'].strip()}\n```\n")
lines.append('''
建议：JSON parse_float 起保留精确值，到最终字段构造边界统一具名验域；测试应穿过真实文件读取入口。两条 reader 路径同根合并计一条，不把单独 validate 的有限性承诺误称物理验证。

### N04：三维“内接所以偏安全”在高摩擦格失效

一个接触足够：`point=(0,0,0), normal=(1,2,3), tangent=(2,-1,0), k=4`；恒载 `(-1,-2,-3,0,0,0)`，活载 `(2,-1,0,0,0,0)`。mu=1e16 时 alpha 高估约16.6%，精确自检 ok=True；mu=1e17 时有限圆锥容量报成 unbounded，并报告 resolved。

独立 Fraction 证明：原法向 n 与活载 l 精确垂直，n²=14、l²=5。圆锥平衡必须 `5 alpha² <= 14 mu²`。还以**实际保存的 binary64 法向** a 独立核 `a·l=0`，令 s=a²、q=a·n，圆锥上界为 `((mu²+1)q²-14s)/(5s)`；实际 exact alpha² 仍严格超出，不能用“原法向归一化后的模型不同”解释掉。无界格的两条生成射线 `a·g<0`，已经含抗拉方向。

这些输入、方向、真正容量均可表达且在声明支持域。本例不是 LP 算法或证书错：LP 正确求解了已经失真的舍入生成锥；静力与自检共享 friction_generators，故无法认证物理圆锥安全。逐分量 RN-even 不保持向量的圆锥包含关系。模块 :48-49 披露方向浮点，与 :66-68 无条件偏安全/夹逼承诺不能同时成立。
''')
lines.append(f"重放：{link('review/repro/limit_cone_safety.py')}；{link('review/evidence/support_cone_cross_review.md','第二路线独立上界核验')}。\n\n```text\n{bycase['N04']['verified_output'].strip()}\n```\n")
lines.append('建议：最终方向需独立精确核单边性与圆锥内接证书；否则缩到可认证的、入口实际检查的支持域并响亮拒绝。补一般三分量法向和高摩擦格；不得用自检同一生成锥代替认证模型。\n')
if len(findings)>4:
    f=findings[4]
    lines.append(f"### N05：{f['conclusion']}\n\n{f['failure_scenario']}\n\n位置：`{f['file:line']}`。建议：{f['suggested_fix']}\n\n重放：{link(f['repro_path'])}。\n\n```text\n{f['verified_output']}\n```\n")
    lines.append(f'''独立证书不是“相信另一次LP答案”：LP只提供候选力，测试侧Fraction核64个接触的压缩性、真实圆形摩擦锥包含和全部六维平衡，因此获得真实圆锥容量下界。第二路线补核零黏聚、4×64索引、原点力矩，并独立认证k=5/6/7的原始—对偶最优证书，排除离散LP低估的伪反例。主审亦亲自复跑补证书。pi<22/7及cos有理下界单独认证。{link('review/evidence/limit_relative_bound_cross_review.md','N05独立交叉复核')}。

**不否定 limit.py:69 的纯滑动限定句**，也不把它计成求解器数值缺陷。真正错误是把 `C(mu*cos(pi/k)) <= C(poly) <= C(mu)` 无条件替换成 `C(poly) >= cos(pi/k)*C(mu)`；容量对摩擦系数一般非线性。README“本几何”也已击中：使用同一_interlock_capacity几何，只改变普通mu参数。当前命名门固定_LIN_MU=.2，因此没有覆盖反例mu=1.8。
''')

lines.append(f'''
## 三、执行顺序、支持域专审及新代码

1. 先确认 HEAD、干净基线并冻结全部跟踪文件 SHA；启动主审**单进程串行**全套。随后只读分工并行审查、探针，与实现方不共享上下文。
2. 回放第十三轮三条：类生命周期/实例更新漏传播的三个原SOURCES现在均报 closed 诊断；实际 first_entrance3 返回 x0 而非事件中点的单处内部变异，被 **event position midpoint binding** 断言捕获；canon-map 现行合同明确降级静态工具为辅助检查。三条均闭合，见 {link('review/evidence/r13_replay.json')}。旧 g6m 只读，未执行其中写旧树路径的脚本。
3. 支持域 D400 输入盒本身不是充分条件。差值401、二次800、三次1200指数推导自洽；相消、任意近零除数和派生结果可超输出域，合同明确另验最终/声明中间量。RN-even 默认开区间端点正确，支持域外响亮报错不计。
4. 原 remaining_138 全条分类/测试映射已读；29个“不产生派生构造量”逐个读完整函数返回链，**20 kernel + 2 dual_margin + 7 reader_oracle** 均成立。它只证明返回的是离散量/输入搬运/索引/None，不自动证明内部全域判定和执行路径。109个其他处置的有限逐值门不等于所有输入正确，N01～N03 已给漏网入口。
5. 生产 construction 的 isqrt/significand 与参考 oracle_construction 的独立有理中点胞/bit搜索不同，只共用异常类型；额外 **4364** 个独立胞检查：接受2844、响亮正确拒绝1520、失配0。face_noise 的53位无限指数边长误差论证和 `(2u+u²)|R| + 2^-1075` 范围未见矛盾，但未推广成一切多根式正确舍入。
6. 新 diff `fabe303..HEAD -- src tests tools docs`：52文件、8390增/1290删。数值/reader/adapter公开构造、几何构造与报告、新四组逐值门、静态生命周期/事件绑定及设计同步均按分工审读。静态工具flow/subset/checker读代码及新门，不逐条推翻或认证2674个局部pin。未加修复，也未把“静态零诊断”当退出证据。

细账：{link('review/evidence/support_audit.md')}、{link('review/evidence/support_nonconstructive_29.json')}、{link('review/evidence/inventory_summary.json')}。主审另逐函数族归类construction/contract/reader/margin的263个Compare节点，见 {link('review/evidence/root_branch_review.json')}；索引数量仍不冒充动态全域证明。第五轮之后提交说明只读保存于产物索引。

## 四、九镜头独立覆盖

| 镜头 | 实际工作与结果 | 剩余边界 |
|---|---|---|
| 1 精确性声称/分支 | 38模块1637 Compare全仓索引，223词法候选；几何1033节点按函数族归类，力学297语法分支分类。默认几何精确、显式caller窗、诊断报告、快路fallback分别检查；公开默认几何未找到改变答案的隐式噪声带。LP浮点阈值只给候选，9次说谎候选验证精确兜底。Dual参数早转换为N01/N02，reader边界为N03。 | Compare清单不是动态证明；旧geom3私有浮点链无公开调用，不称其有fallback。legacy reader去重带属明示来源规约，不等同默认精确几何。 |
| 2 过滤/缓存 | 72000独立Fraction谓词调用、600面内区间过滤零错，含次正规/上溢/下溢/混合尺度；内容键、mutable verts/faces/view payload/covers与运动缓存审读；既有内部缺键/别名毒化门219定向集中实跑。LP/Dual无持久答案缓存。 | 不穷尽任意用户数值协议/别名与所有误差界分界点。 |
| 3 oracle独立性 | 自写区间积集合并、Fraction凸包/极点/运动/LP顶点 oracle，不共用被测几何。构造reference不同算法。g0/g03 oracle import与关键路径核查。N04点出自检共享锥模型的现实盲区。 | brute_feature_distance、二分逃逸共享production predicate，只作佐证；同一合法插值模型不是任意折面模型保证。 |
| 4 旧门迁移/牙 | 索引156改写共享函数；E2～PERF台账及风险迁移审读；R13事件内部单处变异准确报红。复制树两处力学变异分别22红/4红，正确看护断言且原字节SHA恢复；未变异本树。窗口/缓存/过滤现有内部变异实跑。 | 没有逐一为全部156函数重新造“旧能抓新漏”的变异，不能称全迁移证明完毕。 |
| 5 几何压力 | 1440凸2D、1080凹2D成员；110穷举3D极点；集合并126点/95相交/25E拓扑/30逃逸/20首入，另60二维首入、70距离、280裕度，零失配。L/U/C/环/闭空腔/台阶，尺度1e-9/1/1e8、大平移1e8、精确3/5-4/5旋转。 | 不证明任意非星凹体、一般非正交运动、任意折面体完整全局E。 |
| 6 局部接触窗 | 51格：六轴接纳30、仅薄壳接纳6、拒绝15；67壳厚检查，零错。独立区间±w移位与星核壳检查，不共用生产证书。 | 现行合同是六轴rho≤w（内部不交），**不是一般PD_closed≤w**；薄壳不是统一短平移保证，也不保证旋转不变。旧无条件PD承诺已被现行文档明确纠正。 |
| 7 极限分析 | 300个独立Fraction枚举顶点LP对拍；行/列缩放到±1200；exact_x/exact_y可行、强对偶、RN视图核。9伪float状态候选+4真实maximize返回毒化均被检出。分辨性仅报告、不覆盖原答案，旧远体/无界screen重放。N04为共享模型漏检。 | 300族非随机全域Farkas/无界证明；资源cap响亮拒答不是错误结果。 |
| 8 文档/正本 | 背景README/AGENTS/两设计/canon-map、各E报告与提交说明已读。00/01/03/07只读分段读完，对动A/reference/E方向、闭集PD vs内部rho、凸/凹与局部盖边界映射核查。115声明索引另分现行/历史/存在性/语义核验。N04为核心安全承诺反例。 | 不重新查文献优先性/原论文、也不把所有测试文件存在等同所有句子被证明。 |
| 9 原发现回放 | 主审重跑25个不同raw条目：几何15、力学10。完整stdout/契约迁移见下表，均未重现原错误；不把print脚本exit0称自动通过。 | 尚余25条不在本轮独立重放集合；全套执行不是全部原反例的独立重放。 |

详尽路线：{link('review/evidence/geometry_audit.md')}、{link('review/evidence/limit_audit.md')}。文档115条的明确分级：**40条只对限定子句做语义核、36历史/替代、20仅存在性、19未语义认证**；128引用token存在不等于整段证明，canon_map第八节另有18行映射账。{link('review/evidence/document_claim_review.md','逐条文档核验')}。该路线另跑50个参数展开node，全绿；不把它加成主全套。机读分支与文档核验账均在 {link('review/ARTIFACTS.md','产物索引')}。

## 五、第五轮原始发现的25条重放

**统一下表使用原 findings 数组0基索引。** 子力学原账用1基编号，所以统一减1；避免混淆工单历史报告编号。原几何15个脚本多是print，主审读完整stdout作语义核验；其中共享predicate对照不是主 oracle。

| raw0 | 当前实测/关闭的具体含义 |
|---:|---|
| 1 | Windows source_note 导入/无控制字符，严格SyntaxWarning检查通过 |
| 6 | 3 EE冻结位形gap为正、盖法向同向，半距离裕度仍分离 |
| 8 | 几乎法向的tangent响亮拒收，不再生成错误框架 |
| 9 | flat arch门现存在；mu=0不可行，正mu自锁无界 |
| 10 | 低摩擦/黏聚alpha×.999或更小毒化被真正selfcheck拒绝 |
| 19 | 无关体高速不再使1e-100贯入被放行 |
| 20 | 无关重体下静力可行但次优alpha，精确gap=1/100令ok=False |
| 21 | 远体不改变本体不确定性/分辨性/原答案 |
| 22 | 原unbounded精确答案保留，邻域风险nearby_infeasible报告；禁用screen内部变异4红 |
| 25 | 原两短边反例成员=独立同态对照，G0 2000点失配0 |
| 26 | 极短合法凸例成功，实际微凹例精确拒收 |
| 27 | 假EE不出现，3姿态G0和4原深度探针正确 |
| 28 | 原四尺寸比/yaw/旋转格G0通过 |
| 29 | 6近平行格8严格facet，双向G0不生成假FF |
| 30 | 近乎平行距离与原独立参考同为4.579391932681403e-09，不再自检抛错 |
| 33 | jitter U墙当前exact/二分显示一致；共享predicate只是佐证，另有30个独立闭式escape格 |
| 36 | 小体进大体3姿态时刻约1，未再因退步窗口抛错 |
| 37 | 原凸包无外漏，两G0位形极点差0 |
| 39 | 默认eps不再NameError；rounded差点hull仍可报hull_anomaly，这不是当前精确差点的假红 |
| 40 | 微凹凸入口拒收，一般精确成员两深度都为1，原答-1未重现 |
| 41 | 原roof实际精确凸性False/True，旧前提已不成立；显式convex-model G0通过，不称一般表面绿 |
| 42 | 5坐标档位G0通过，不再拟合虚假支持面 |
| 43 | 4薄锥relint=True，独立Fraction Gordan正裕度，G0无ambiguous豁免 |
| 44 | 远体不放大力偶残差容许，12个毒化格全拒 |
| 46 | 贯入跨度×1e-3至1e-100的24格全拒 |

主审完整重跑记录：{link('review/evidence/primary_coverage_replay.json')}。几何原输出与解释见子审账；力学脚本内有实体assert，原始输出与300 LP逐值结果保留。没有修改原raw文件或其他树。

## 六、未确认 / 不计发现

1. **U-GEOM-RANGE（已复现响亮拒答，但不分级）**：Fraction两盒半尺寸2^-1070或2^-1074、中心差4s；真实gap=2s可表达，exact overlap/E均-1。body_distance与inflated_membership先造不可表达rounding_floor而具名抛ConstructionDomainError。不是静默错误，依所有者规则不算构造缺陷；纯状态API全有限判定合同与内部报告构造义务的归属值得澄清。{link('review/repro/geometry_unconfirmed_predicate_range.py')}。
2. g0_oracle.boundary_has_exterior直接以raw float调用的一般极端退化正确性未穷尽；正常ray_exit路径先提升Fraction。没有具体错误答案，不计数。
3. static任意Python生命周期/别名形态全面封闭未证明；未证明2365排除、一般非整数幂/libm界都不直接计发现。N01/N02是已证明实际答案错误，而不是缺证明本身。
4. 文档量化的初始单倾面候选不直接计数，因为README有“本几何”范围；将Patton公式23直接当作整个互锁体真容量也不计，因为忽略了力矩限制。N05后来改用同一互锁几何、逐接触真实圆锥+六维平衡的独立证书，**只用认证下界而不假设真值23**，因此最终确认。未确认候选与确认发现没有混为一谈。

## 七、完整性批评（不掩盖漏审）

- 全仓源模块做索引，**不表示每一行或每一个API都完整数学重推**。完整细读主要为numeric_domain/construction/oracle_construction/Dual/ContactRecord/readers/adapters与LP/limit/limit_multi；二维各主实现、三维exact/sweep/topology/covers/entrance/interlock/G0/cache核心按分工阅读。geom3历史私有浮点链只作调用可达性/相关段检查，frozen只细核EE方向、gap/法向与原复放，未重新推导全部Dual导数。
- 没有逐一阅读/证实全部915公开API、2674局部静态例外；remaining138分类已核不等于138 API所有路径都给出了新的独立范围定理。
- 未逐一重做全部156旧门的旧红新绿变异，也未逐项重跑E2～PERF全部历史内部突变。报告只把实际执行的单处事件、两处copy变异、219定向门和候选毒化作为牙证据。
- 文档115条索引内有历史、辅助和条件陈述；文件名命中不等于语义断言成立。细账明确区分完整语义核、只查存在、当前限制与尚未核；不以全套绿替代这一义务。
- 任意凹体全局E、任意折面/非星体、所有瞬态路径、跨平台libm、用户自定义数值协议、所有缓存别名以及资源复杂度均未穷尽。不重跑姊妹exe，不作benchmark/工程验证/动力学标定。
- 原50发现只独立重放25；其余不能据本轮宣布关闭。oracle有限零差分是所列输入族证据，**不是软件全面正确性证明**。

## 八、主审全套与完整性证据

环境：Windows / PowerShell，Python 3.12.10、pytest 9.0.3；本轮主套一个pytest进程串行，子审探针可能同时运行，不把耗时当独占性能基准。开始约2026-10-13 04:24:25 +08；所有临时输出在本树review，未写只读g6f工作树。工单命令中的“g6f内tmp”依更严格只读约束改用当前review/tmp_full。

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONIOENCODING='utf-8'
python -X utf8 -m pytest -q -p no:cacheprovider tests --basetemp=D:/eab-wt/g6n/review/tmp_full
```

```text
{match.group(0)}
exit_code=0
```

{link('review/logs/full_pytest.log','未裁剪全套原始日志')} 为PowerShell重定向UTF-16；其他主审最后复现日志为UTF-8。定向集支持域275 passed/1.86s、几何219/4.76s、力学653/18.32s只是补充，不重复算成完整套件。

全程回滚锚：初始tracked SHA清单；最终再次逐文件哈希，**{integrity['tracked_count']}个跟踪文件0变更、0路径增删，HEAD不变**，git status仅 `?? review/`。copy内部变异恢复与SHA见独立机读账，主工作树从未变异。支持域定向初跑tmp父目录缺失、几何oracle开发误报、旧脚本提取SyntaxError与copy核验脚本引号问题均分类为审查环境/输入错误，修正review脚本后复跑，不拿它们凑产品发现。

本报告和机读JSON可用 {link('review/repro/root_build_report.py','报告重建脚本')} 重建；所有 confirmed 可用 {link('review/repro/root_verify_confirmed.py','主审复现编排脚本')} 复跑。审查产物哈希与链接见总索引。

G6N_DONE critical={counts['critical']} major={counts['major']} minor={counts['minor']}
''')
(REV/'G6N_report.md').write_text('\n'.join(lines),encoding='utf-8')

# Index regular artifacts, link large temporary/copy directories without
# pretending their transient node files are stable audit evidence.
indexed=[]
for folder in ('repro','logs','evidence'):
    for path in sorted((REV/folder).rglob('*')):
        if path.is_file():
            rel=path.relative_to(ROOT).as_posix()
            if rel=='review/evidence/deliverable_qa.json':
                continue
            indexed.append({'path':rel,'url':'file:///D:/eab-wt/g6n/'+rel,
                            'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
for path in (REV/'G6N_report.md',REV/'G6N_findings.json'):
    rel=path.relative_to(ROOT).as_posix()
    indexed.append({'path':rel,'url':'file:///D:/eab-wt/g6n/'+rel,'bytes':path.stat().st_size,
                    'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
(REV/'ARTIFACTS.json').write_text(json.dumps({'head':integrity['head'],'artifacts':indexed,
    'temporary_directories_not_individually_hashed':['review/tmp_full','review/tmp','review/copies'],
    'self_index_not_hashed':'ARTIFACTS.md/json and deliverable_qa.json are excluded to avoid verification self-hashing cycles'},ensure_ascii=False,indent=2),encoding='utf-8')
idx=['# G6N 审查产物索引','',f'HEAD `{integrity["head"]}`；下面是可保存的脚本、原始日志、证据及报告。',
     '',link('review/ARTIFACTS.json','机读链接/大小/SHA-256清单'),'',
     f'临时和隔离副本目录：{link("review/tmp_full/","全套tmp")}、{link("review/tmp/","探针tmp")}、{link("review/copies/","变异隔离副本")}。未逐项哈希 transient 文件；副本恢复的证据在limit_poison_mutation_results.json。',
     '', '| 文件链接 | 字节 | SHA-256 |','|---|---:|---|']
if (REV/'evidence/deliverable_qa.json').exists():
    idx.insert(4,link('review/evidence/deliverable_qa.json','交付结构/链接/哈希核验（不自哈希）'))
idx.insert(4,'本清单为最终当前字节哈希；子路线较早快照索引不替代本清单。')
for row in indexed: idx.append(f'| [{row["path"]}]({row["url"]}) | {row["bytes"]} | `{row["sha256"]}` |')
(REV/'ARTIFACTS.md').write_text('\n'.join(idx)+'\n',encoding='utf-8')
print('FINAL_REPORT_BUILT',counts,match.group(0),'artifacts=',len(indexed))
