from pathlib import Path
import ast, json, hashlib, collections
ROOT = Path(__file__).resolve().parents[2]
E = ROOT / "review/evidence"
inventory = json.loads((E / "document_claim_inventory.json").read_text(encoding="utf-8"))
assert len(inventory) == 115
index = {}
for p in (ROOT / "tests").glob("test*.py"):
    s = p.read_text(encoding="utf-8-sig")
    index.setdefault(p.stem, []).append({"kind":"file", "file":p.relative_to(ROOT).as_posix()})
    for n in ast.walk(ast.parse(s)):
        if isinstance(n, ast.FunctionDef):
            index.setdefault(n.name, []).append({"kind":"function", "file":p.relative_to(ROOT).as_posix(),
                "line":n.lineno, "end_line":n.end_lineno,
                "assert_expressions":[ast.unparse(a.test) for a in ast.walk(n) if isinstance(a,ast.Assert)]})

H, S, X, U = "historical_or_superseded", "confirmed_scoped_semantics", "existence_only", "not_semantically_verified"
manual = {}
def mark(ids, status, note):
    for i in ids:
        manual[i] = {"status":status, "manual_review":note, "verified_scope":note,
                     "unchecked_remainder":"未将同段其他子声称或有限门外输入外推成一般证明。"}

mark([0,84,85,86,87,88,89], S, "亲读支持域合同、代数构造及275新门：D400不保证三次量/相消输出可表达；RN胞严格端点；代数路径不人为截域；PARTIAL不是全API保证。4364有理胞独立探针无差异。SUP反例照计，缺口未证明不另计。")
mark([1,41,90,97], S, "现行静态检查明确辅助性，生命周期/返回绑定的具名补门存在；历史任意Python安全保证撤回。仅核有限补门和边界，不证明全部动态协议。")
mark([2,3,42,91,98], H, "有日期的R11/R12状态与当前R13辅助合同一起读，不把旧默认拒绝当全仓安全保证；未重新认证历史全套/所有者流程。")
mark(list(range(6,20))+list(range(30,41))+[44,83,96,100,104], H, "明确日期/阅读边界的历史报告或E5a2待E5b续作状态，不是当前HEAD正确性证明；不重新认证历史数字或G6状态。")
mark([4,43,92,99,105,106,107,111], S, "亲读六轴rho与闭集PD不同定义、星核径向厚度界及不完备/不旋转不变的限制。不是完整PD算法；test_perf_contact_window/R7空腔门存在。未重证任意凹体。")
mark([5,21,52,53,94,108], S, "分层目标/声明规则/表头，而非额外计算定理；README的✔受历史及待G6限制，不能仅凭符号推全域验证。")
mark([20,22,50,54,55,56,57,59,60,61,64,72,73,93], X, "指名门/文件存在；仅部分相关源码已读，长段全部几何性质/构造族未在本补充逐条认证。存在性不能当语义证明，其他几何审查另核。")
mark([23], S, "亲读G1断言ve_legacy==ve_common==53、legacy_only为空、gap<1e-6；它不核锁态/滑动符号/位移同构。G0的1260/603/657断言已读，定向只重跑G1；整段E2/E3其他声称仅存在性。")
mark([24], S, "亲读G2各4项、G03的26个边界点计分及边界错票/假局部顶点失败断言。不把手写夹具对账冒充检测器。源环descriptor限制另核；首入/一般凸性整段未全认证。")
mark([25,58,62,63,65,66,67], S, "亲读margin距离恒等有限凸族(<1e-9,分离样本>40)、Lipschitz局部/全局上界与紧性下界、顶点膨胀连续式。膨胀成员门共用body_distance非独立及KKT后半无实现已明示。未把有限测试外推全域C1,1数值证明。")
mark([26], S, "亲读lower/upper、Patton、锥门及固定_LIN_MU=.2范围，现有窄格通过。README未限定相对短缺cos界被同一amp=.25互锁几何mu=1.8的有理静力圆锥证书反证，计root N05；巨大mu射线舍入出锥是不同的N04，不重复。")
mark([27], X, "全部端到端/闭式/不变量节点存在，共用块体生成及盖枚举的限制如实承认。未逐条核115格及对偶最优面所有不变量。")
mark([28], S, "亲读G3：order近2±.1、谷底<1e-9、两步误差比近16，不是逐位1.9995保证；phase=0逐19行标不可微及两侧区间。Dual隐式float拒绝门存在，但SUP反例说明✔不保证全部整数幂/实数函数输入。")
mark([29], S, "亲读TF census/helper：5296+探针=6716全部n-p，独立原TSV逐字段/extra对账，MODE4/5/6为UNVERIFIED。非对称25偏移门确读解析truth；未独立重证全部TIA族或JSON文本极尺度。")
mark([45,46,47,48,49,51,68,69,70,71,74,75,76,77,78,79,80,81,82], U, "已读段落并按模型/历史/缺口限制理解；完整数学命题、正本文献或全仓未实现的否定证明没有在本补充独立认证。间接门存在不自动认证本句。")
mark([95], S, "给定输入精确值不同于背后理想设计几何，语义成立；D400内大整数进入libm再丢位不算用户输入已舍入，SUP-02按给定数据反证。")
mark([101,102], S, "亲读折面反例及Euclidean band断言：见证不在任意源三顶点平面、轮转首点改变gap/见证、source标签不可偷换canonical；解析盒平方距离核外角，不能只读支撑平面gap。一般折面完整法锥未保证。")
mark([103], H, "E5a2 nominal浮点桥接安全上探，被后文E5b exact_height/offset权威证书替代，不当全链最早逃逸保证。")
mark([109,110,112,113,114], X, "指名窗口反例/事件/冻结/G0节点与源码存在；全部Fraction区间构造与凹体完备性未在本补充逐行重证，其他任务另核。")
assert set(manual) == set(range(115)), set(range(115))-set(manual)
rows = []
for i, x in enumerate(inventory):
    r = {"index":i, **x, **manual[i]}
    bindings = []
    for token in x["same_line_test_names"]:
        matches = index.get(token)
        if matches is None:
            matches = [v for k,vs in index.items() if k.startswith(token) for v in vs]
        assert matches, token
        bindings.append({"cited_token":token,"resolved":matches,
                         "resolution_scope":"仅存在性及assert定位，不是自动语义证明。"})
    r["existence_bindings"] = bindings
    rows.append(r)

def readlog(name):
    b = (ROOT/"review/logs"/name).read_bytes()
    return b.decode("utf-16") if b[:2] in (b"\xff\xfe",b"\xfe\xff") else b.decode("utf-8-sig")

finding = {"id":"G6N-N05", "severity":"major", "file":"README.md:125; tests/test_limit.py:157-160",
    "conclusion":"把摩擦系数mu*cos(pi/k)的圆锥包含夹逼，误推成一般极限承载力相对短缺≤1−cos(pi/k)。",
    "failure_scenario":"同README命名门_interlock_capacity的amp=.25几何，mu=1.8、k5/6/7。独立圆锥静力证书给真实容量/N≥6.86524822695且≤23.000000000000007；离散值分别4.40944350913/4.21533622092/6.12817843059，对真实容量比至多.642285/.614011/.892638，均严格小于cos(pi/k)。固定_LIN_MU=.2的旧门没覆盖此μ。",
    "how_to_reproduce":"python -X utf8 review/repro/support_cone_interlock_relative_bound.py",
    "suggested_fix":"一般问题只保留C(mu*cos)<=C(poly)<=C(mu)的容量函数夹逼；1−cos相对界仅适用承载正比切向能力的纯滑动或另证条件。扩门含普通高摩擦及力矩约束族。审查不修代码。",
    "verified_output":readlog("support_cone_interlock_relative_bound.txt"),
    "independence":"生产LP/棱只提供候选数据，自写Fraction点积/叉积验各合力压缩、真实圆锥不等式和六维精确平衡，建立真实容量下界；不用生产wrench/check_duality作oracle，不假设Patton23是完整真容量。",
    "dedup_note":"root已交叉复核确认N05；与高mu方向舍入出锥N04根因不同；单倾面辅助例不另计。"}

lines = (ROOT/"docs/canon_map.md").read_text(encoding="utf-8-sig").splitlines()
canon = []
for number in range(391,409):
    status, note = X, "前三列明确历史日期；第四列限定离线M4a，不升级07完整合同。仅核路径/门存在，不重捕获历史规模。"
    if number in (391,392,394,400,401,402,403,406):
        status, note = S, "读相关ContactRecord/reader/kernel/adapter结构，FF/FE仅合并标签、三种legacy入口、M3/MLCP/在线接缝等缺口没有被M4a关闭。JSON数值边界另有root确认错误。"
    if number in (393,399):
        status, note = S, "读M4断言：15配对各3步、仅14份不同几何字节时序、未知类别必失败；不是锁态/滑动/位移同构或真实首入。"
    if number in (397,398,404,405,407,408):
        status, note = U, "历史G3/G4、所有过往姊妹只读、远程状态或文献优先性未重新认证；不以test名称替代历史/文献证明。"
    canon.append({"file":"docs/canon_map.md","line":number,"claim":lines[number-1],"status":status,"manual_review":note})

counts = dict(collections.Counter(r["status"] for r in rows))
data = {"scope":"九镜头8补充：115个收录段落及canon_map第八节18行；不是全部自然语言声称穷尽表。",
    "status_definitions":{S:"亲读指定子句/断言/数学；verified_scope及unchecked_remainder限制必读，不认证整段所有性质。",X:"仅存在性。",H:"有日期/阅读边界的历史或被替代合同。",U:"未作独立语义认证。"},
    "category_counts":counts,"unique_cited_tokens":len({n for x in inventory for n in x["same_line_test_names"]}),
    "unresolved_cited_tokens":0,"claims":rows,"canon_map_section8":canon,"new_confirmed_findings":[finding],
    "verification":{"selected_gate_run":readlog("document_claim_selected.txt"),"mode":"标准单进程21个指定nodeid展开50例，不重跑全套；全套由root另报。"},
    "limitations":["未全读每个引用文件/全部helper链；assert抽取只定位，不是语义证明。","未认证所有历史HEAD/数字、过往姊妹事务及文献主张。","有限门不外推一般数学证明；整体正本逐条比较由root汇总。"]}
(E/"document_claim_review.json").write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
md = "# G6N 镜头8：文档声明与实际门\n\n115条清单不是全部自然语言声明的穷尽表，另补canon_map第八节18行。128个引用token全部存在（含文件名/prefix），只是存在性，**不是语义证明**。\n\n"
md += "[完整逐条机读清单](file:///D:/eab-wt/g6n/review/evidence/document_claim_review.json)。\n\n## 分层计数\n\n"
for key,value in counts.items(): md += f"- {key}: {value}条。\n"
md += "\nconfirmed_scoped_semantics必须连同verified_scope/unchecked_remainder读，只确认亲读的具体子句/断言，不认证一个含十项子声称的整个段落。现行静态/支持域文档明确PARTIAL；未证明缺口不另计，已有生产反例仍照计。\n\n## 新确认核心量化界错误（root N05）\n\n"
for key,title in [("file","位置"),("conclusion","结论"),("failure_scenario","场景"),("independence","独立性"),("suggested_fix","建议")]: md += f"- **{title}**：{finding[key]}\n"
md += "\n[复现](file:///D:/eab-wt/g6n/review/repro/support_cone_interlock_relative_bound.py) / [日志](file:///D:/eab-wt/g6n/review/logs/support_cone_interlock_relative_bound.txt)。\n\n```text\n" + finding["verified_output"].strip() + "\n```\n"
md += "\nPatton23不能直接当完整真容量，其他力矩/倾覆限制会降低它；本复现独立可行圆锥力证书给下界，已足以否定相对cos界。与巨大mu射线舍入出锥不重复，单倾面辅例不另计。\n\n## 指定门实跑\n\n```text\n" + readlog("document_claim_selected.txt").strip() + "\n```\n"
md += "\n21个nodeid参数展开50例，涵盖G1/G2、margin、LP/Patton/现有cos窄格、G3/phase、TF、G03、源环及M4。现有全绿没有覆盖新mu=1.8格。\n\n## 115条逐条状态\n\n| 索引 | 来源 | 层级 | 核验边界 |\n|---|---|---|---|\n"
for r in rows: md += f"| {r['index']} | {r['file']}:{r['line']} | {r['status']} | {r['verified_scope']} |\n"
md += "\n## canon_map第八节07→代码\n\n| 行 | 层级 | 边界 |\n|---|---|---|\n"
for r in canon: md += f"| {r['line']} | {r['status']} | {r['manual_review']} |\n"
md += "\n## 完整性批评\n\n未逐行读完每个引用文件/全部helper；未重捕获姊妹输出、重做历史G4或文献优先性；自动命名/断言抽取不是语义证明。主套由root报告，本补充只报已实跑50例。只写review，没有tracked修改。\n"
(E/"document_claim_review.md").write_text(md,encoding="utf-8")
for name in ("document_claim_review.md","document_claim_review.json"):
    s=(E/name).read_text(encoding="utf-8")
    assert "????" not in s and any("\u4e00"<=c<="\u9fff" for c in s)
print("DOCUMENT_CLAIM_REVIEW_VERIFIED", counts, "115 rows; 18 section8 rows; 128 cited tokens resolved")
