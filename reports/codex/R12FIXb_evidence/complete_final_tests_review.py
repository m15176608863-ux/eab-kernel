"""Supplement source review against raw_frozen; no policy or source edits."""
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "reports/codex/R12FIXb_evidence"


def key(row):
    return tuple(row[k] for k in ("path", "function", "rule", "node"))


prior_names = ["tests_numerical_review.json", "tests_structural_review.json",
               "tests_round5_complete_review.json", "tests_round6_supplement_review.json"]
prior_keys = set()
for name in prior_names:
    data = json.loads((OUT / name).read_text(encoding="utf-8"))
    prior_keys.update(key(r) for r in (data if isinstance(data, list) else data["sites"]))
raw_path = OUT / "raw_frozen.json"
raw = json.loads(raw_path.read_text(encoding="utf-8"))
pending = {key(r): r for r in raw if r["path"].startswith("tests/") and key(r) not in prior_keys}
review = {}


def add(path, function, category, reason, action=None):
    if not path.startswith("tests/"):
        path = "tests/" + path
    review[path, function] = (category, reason, action or {
        "exact_proof_gap": "补充实际 Fraction/整数返回及容器字段的证明传播；不可用 caller waiver 隐藏数值 callee。",
        "given_input_fixture_boundary": "保留原样本及输入契约，承认实际舍入；不得声称理想几何变换精确或以其整体放行后续构造。",
        "legacy_approximate_diagnostic": "若保留旧门须明确近似范围；严格精确构造要求下应独立有理化后复核原格子及牙，不批准此数值例外。",
        "test_execution": "保持被测 API 调用与独立期望值边界；按源分析 API，不给 caller 的数值链整体豁免。",
        "test_harness": "只可讨论本测试架构站点，不得把其调用或注入的数值实现视为安全。",
        "metadata": "证明字符串/字节/结构校验的非数值用途，不应依赖通用 callable 或路径整体豁免。",
    }[category])


add("e5a_cover_oracle.py", "_margin_witness_distance", "exact_proof_gap",
    "非平面折面分支中 point=q(X.verts[vertex]) 与 _model(Y) 均先转 Fraction；test-owned ear clipping 返回有理三角形，"
    "_point_tri_sq 的平方距离有理精确，min 只选其中一项，最后 sqrt_exact(squared) 才显示。这里不是 float 距离平方后再开方。")
for filename in ("e5a_escape_oracle.py", "perf_escape_oracle_reference.py"):
    add(filename, "facet", "exact_proof_gap",
        "a/b 是独立 model 将给定顶点转为 Fraction 后的坐标、Newell 法向与拓扑；n/w/d 来自有理差、叉积及 Gram 参数。"
        "_signed_gap 精确算 dot(n,w)^2/dot(n,n) 后才 sqrt_exact，unit(d) 则在精确方向上调用 unit_exact；"
        "不能把另一条 tolerance/显示分支的 float 值混成这些方向系数的来源。perf 版本的输入可能先被 move 舍入，但 model 后这一局部运算仍对所给坐标精确，非理想平移保证。")
    add(filename, "geometry_noise", "legacy_approximate_diagnostic",
        "此函数独立重算显式 legacy 面/棱噪声窗口：vertices 可能是原始 float，sub 后 norm 的棱长/周长确有提前舍入；"
        "这些量用于 64*EPS*coordinate 的噪声比例，不是精确几何真值。m[2][fi] 则来自 Fraction model 的 Newell 向量，"
        "它单独的 norm 是精确方向上的末端显示，必须与原始 vertices 的差分区分。")
    add(filename, "windows", "legacy_approximate_diagnostic",
        "length 是相对首顶点的最大距离再跨两体取最小，sub(p,v[0]) 的输入可为 binary64，因此先差后 norm 可能真实舍入；"
        "结果只用于明确的 legacy extent/rounding 窗口 max(1e-9*length,64*EPS*max(coordinate,length))，不是独立精确距离 oracle。")
    add(filename, "_candidates", "exact_proof_gap",
        "unit(normal) 的 normal 来自 facet(...,exact_coefficients=True) 的 Fraction Newell/叉积方向，"
        "先以 normal[2]、dot(normal,normal)、有理 numerator 对方向/高度作精确比较，保留候选之后才把单位 nz 显示。"
        "该站点不是先将方向 float 化再归一化；legacy threshold 与输入 move 的契约仍需分别审核。")
add("e5b_margin_oracle.py", "check_exact_margin", "test_execution",
    "production.inflated_membership 是被测 API：probe 是 delta、0、已由独立 Fraction 中点证书验证的显示距离及其两侧 nextafter。"
    "期望值用 F(probe)**2 与独立 nearest 比较，不回用被测状态或几何原语；采样相邻 binary64 delta 不要求它是未舍入实数距离。")
add("test_bb52_g1.py", "_retired_vote", "legacy_approximate_diagnostic",
    "明确重放已退役 sign(min非VV gap) 规则以统计其误报/漏报；At 是旧 float 平移像。enumerate_covers 的输出在这里是被观察的旧投票，"
    "与 polygons_overlap 比较并累计错误，不是当前精确 oracle，不可把这个调用站点解释成旧规则可靠。")
add("test_bb52_g1.py", "_rounded_distance_audit", "test_execution",
    "rounded=translate(A,x) 故意保留原21×60网格的实际 float 顶点像，g0_distance_completeness 在零追加平移下检查这组给定数据；"
    "classify_completeness_failure 只为 rep.failures 加归因。这里不声称原理想仿射变换精确，也不以失败归因生成期望距离。")
add("test_frozen_ee_sign.py", "_ee_exact", "exact_proof_gap",
    "independent._model(A/B) 将原坐标化为 Fraction；u/v、Newell/Gram 参数和 cross(v,u) 均有理，direction 只在 n 与 scale(n,-1) 中选择。"
    "unit_exact(direction) 是精确方向的最后显示边界，未先构造 float 法向。")
add("test_frozen_ee_sign.py", "_frozen_gap_of_chosen_label", "test_execution",
    "先从实际 body_distance 取得被测 label，再以对应 frozen_ee_sign 驱动冻结路径并返回结果用于对照；此调用的平移/裕度为零。"
    "这里测试 API 间冻结标签一致性，不是独立精确期望值生成器；不以调用通过来证明 callee 内部安全。")
add("test_frozen_lowdim.py", "_check_one", "test_execution",
    "两个站点分别测试已平移 At+零平移，以及未平移 A+Dual 位移/裕度的冻结 API；label/sign 来自实际被测几何。"
    "值与显示距离作容差比较，delta 导数必须严格 -1；后续梯度范数/有限差分仍是独立列出的近似诊断，非本调用的精确担保。")
add("test_frozen_surface_diagonal.py", "_check", "test_execution",
    "此 helper 在固定三角面内部对角 EE 格调用 body_distance、冻结 gap 与 ee_normal_generic；期望标签固定，"
    "期望距离来自 scale*(F(1.7)-F(1.5)) 的独立有理式，法向对固定(.8,0,.6)容差检查。"
    "函数是被测路径驱动，不把生产函数调用本身当作数值 oracle。")
add("test_g2_bdda3d.py", "_seg_seg_dist", "legacy_approximate_diagnostic",
    "w 来自 float 段端点/见证差，_dot3(w,w)**0.5 是真实 float Gram 后开方。其用途仅固定 cb2 夹具的非面距离窗口佐证，"
    "虽然实现与生产几何独立，仍不是精确构造；原 G2 内部枚举变异牙必须继续保留。")
add("test_interlock_escape.py", "_check_escape", "test_execution",
    "在 escape_height_covers 实际胜出 label 上调用冻结逃逸 API，off 保持给定样本；以独立 truth 检验高度，并比较冻结值与实际显示高度。"
    "用于验证选盖后路径一致性，不独立构造精确逃逸期望，也不掩盖参数/下游构造的舍入。")
add("test_interlock_exact.py", "_wall", "given_input_fixture_boundary",
    "W._place 用固定 RNG16、尺度.7、场址1e5及4个姿态参数生成历史 wall 样本；调用结果是实际给定 float 坐标。"
    "exact 测试针对最终输入，不证明 _place 的随机旋转/平移是理想实数变换。")
add("test_invariance_2d.py", "_covers", "test_execution",
    "translate(A,x) 保留本组给定 float 平移像，再调用被测 enumerate_covers；数学模式将历史 tau 置0，legacy 显式 cone/seg 窗口仍保留。"
    "本函数仅提取实际标签/gap，不生成独立期望，不能据此为 float 平移作精确构造保证。")
for filename in ("test_invariance_geom.py", "test_invariance_interlock.py"):
    for function in ("body_distance", "margin_contacts", "inflated_membership"):
        add(filename, function, "test_execution",
            "包装层把原 A/B 交给同名 exact_margin API，只显式附加 contact_resolution(A,B) 的 legacy 接触窗口并转发 kwargs。"
            "它保留历史窗口内的被测路径，不是独立距离/法向构造；默认精确 API 另对最终给定坐标审计。"
            "不能把窗口参数的显示舍入混成全部 A/B 上游构造已获证明。")
add("test_invariance_geom.py", "_base", "test_execution",
    "在固定 fixture 的恒等格直接调用被测 body_distance/local_facets3；无闭式 d0 的分离对另用全特征 brute_feature_distance 佐证。"
    "后者与盖筛选不同，但仍需独立审其数值契约；此 helper 中显示见证 math.dist 并列分类是旧近似诊断，不能整体叫作精确 oracle。")
add("test_invariance_interlock.py", "_escape", "test_execution",
    "_ilock 与 _vec 给出本轮实际 float 位形/偏移，escape_height_covers 是被测逃逸调用；之后冻结 Dual 路径用于方向导数对照。"
    "给定输入角色不保证其旋转缩放无舍入，也不让逃逸函数内部的未知构造被 caller 豁免。")
add("test_invariance_interlock.py", "_resolution", "legacy_approximate_diagnostic",
    "effective_geom_tol/rounding_floor/characteristic_length 在给定变换后 At/L 上读取生产声明的尺度与噪声量，"
    "组合成逃逸高度分辨率报告 (g+2*r)/NZ 与噪声是否主导的布尔值；不是独立精确几何期望。"
    "本报告属于明确的 legacy resolution 口径，不声称所有中间距离或乘除无舍入。")
add("test_invariance_interlock.py", "_margin_ref", "test_execution",
    "body_distance(A,B) 取得固定 MARGIN_CASES 恒等位形的实际基准解，后续测试核对它与独立特征枚举。"
    "本函数另以 float witness 差后 norm 选并列标签，属既有近似诊断；不得整体把 _margin_ref 当精确构造契约。")
add("test_invariance_limit.py", "_reference", "test_execution",
    "_transform(case,I,0,1,1) 生成恒等格的给定接触/荷载，_solve 调用生产 limit_load 并返回基准解。"
    "它为蜕变测试提供参考格，不是独立精确力学 oracle；原 force/moment 汇总与独立静力核验的边界必须分开审。")
add("test_invariance_limit.py", "_dual_residuals", "legacy_approximate_diagnostic",
    "g 是 _generators 给出的显示摩擦锥列，_norm(g) 用于把功率残差按速度/转动/力列尺度归一化。"
    "这些 float 范数和点积是旧相对残差诊断，确实可能提前舍入，不是有理最优性证书。")
add("test_kernel2d_review.py", "_load_both", "metadata",
    "_verts_csv(rows) 生成测试 CSV 文本，Path.write_text 把同一文本写入本树 pytest 临时 fixture，随后两个读取器消费它。"
    "此写文本站点不产生 sqrt/norm/单位化/几何差分；内容可含故意异常数值供读取器测试，不能把内容安全性与文件 I/O 混淆。")
add("test_kernel3d_geom.py", "_g6_rot", "given_input_fixture_boundary",
    "固定 RNG 的四个高斯 float 先平方求和再 **0.5 归一化四元数，确有先舍入再开方。"
    "这里只定义 G6 随机姿态采样输入；不得因测试名含几何不变性就说该理想旋转精确。")
add("test_limit_fuzz.py", "_genuinely_unresolvable", "legacy_approximate_diagnostic",
    "Fn/Mn/R 的 float 平方和 **0.5 用于给每个活荷载分量设 ±1e-12 采样扰动幅度；这些范数确有舍入。"
    "每组实际 pert 后再由 _exact_status_alpha 检查给定数据的精确状态/承载比，精确求解不倒推保证扰动幅度是精确实数。")
for filename, function in (("test_limit.py", "_interlock_capacity"), ("test_limit_scale.py", "_capacity_ratio")):
    add(filename, function, "test_execution",
        "从实际互锁盖生成 contacts，以 centroid 处独立给定 dead/live 调用生产 limit_load；该站点是承载比实验的被测 LP 路径，"
        "不是独立几何或静力期望构造。wrench、contacts_from_covers 的数值定义须按源另审，不可用 caller 豁免隐藏。")
add("test_limit_selfcheck.py", "_utm_block", "test_execution",
    "_box 在固定 UTM 偏移(5e5,4.4e6,100)产生样本，limit_load 被测求解后必须 optimal，返回解供独立静力自检。"
    "这里不通过共享生产力矩生成期望，也不声称 UTM 输入平移无舍入。")
add("test_lp_certificates.py", "_si_case.P", "given_input_fixture_boundary",
    "P 是原 SI fuzz 生成器的二维/三维局部直接函数，mv(R,p) 的 float 矩阵乘法后加 off 形成给定接触坐标。"
    "R/off 默认参数刻意冻结本轮 RNG 样本；调用可追踪但确有提前舍入，精确 LP 证书只对最终给定数据成立。")
add("test_m4_bdda_adapter.py", "_assert_matches_independent_oracle", "metadata",
    "validate(rec) 校验 adapter 输出 ContactRecord 的模式/结构契约；标签集合已由不共享生产几何的 Fraction 邻接支撑消元 oracle 比较。"
    "该站点不计算期望几何，也不是 lambda/数值 callback；结构校验并不允许数值路径获得整体豁免。")
add("test_m4_bdda_shadow.py", "_digest", "metadata",
    "json.dumps(...sort_keys=True,separators=...) 的文本 encode 为 bytes 后计算 SHA-256，生成差异台账的固定摘要。"
    "不作任何数值构造；其中观察值只是被序列化的数据，不会由 hash 回流为几何坐标。")
add("test_m4_bdda_shadow.py", "_gate_case", "test_harness",
    "读取 fixture、比较 shadow 输出后调用 _assert_baseline，后者核对固定步骤、分类计数与差异行 SHA，"
    "不生成几何期望；真实几何归因保留在被测 shadow 路径与独立分类定义中，不能以此调用整体放行。")
add("test_margin.py", "_lipschitz_probe_points", "given_input_fixture_boundary",
    "cone_relint_direction(E.vertex_edge_dirs(vi)) 用于选择顶点法锥内的探针方向，决定在哪儿采样，"
    "并不产生 Lipschitz 界的期望值（界来自投影非扩张定理）；其方向/点位置是旧 float 构造采样，不应冒充精确几何 oracle。")
add("test_margin.py", "_lipschitz_worst", "legacy_approximate_diagnostic",
    "数据样本中的 nx/ny 或 x/y 先做 float sub 再 norm，真实发生提前舍入；结果是旧 Lipschitz 差商诊断。"
    "取消 normal_fn callback 后只改变数据传递形式，6类正常/变异结果与调用顺序等价，不意味着差商数值构造变精确。")
add("test_margin.py", "_legacy_global_pairs", "legacy_approximate_diagnostic",
    "norm(sub(pts[i],pts[j]))>0 只在原66个全局点对生成时剔除零距离，float 差后 norm 仍是真实近似构造。"
    "这组保留采样不生成理论 Lipschitz 常数；独立全局变异牙另验证其作用，不能称作通用精确范数。")
add("test_margin.py", "_lipschitz_setup", "test_execution",
    "entrance_block_convex 是被测凸入口块构造；后两调用生成原 local/loops/global 采样数据并缓存，不计算独立正确法向。"
    "探针筛选共用最近点 API 的事实在原 docstring 明示，Lipschitz 理论界另给；不把该 setup 概括为精确 oracle。")
add("test_perf_interlock.py", "_assert_cache_does_not_cross_offsets", "test_harness",
    "直接比较零偏移缓存结果、另一给定偏移的 uncached 结果及同偏移 cached 结果；先断言两偏移产物不同，再断言缓存等于同输入未缓存。"
    "这是缓存键内容隔离牙，不是独立几何正确性 oracle；几何路径仍按各自实现审核。")
add("test_r11fix_static_flow.py", "_assert_cone_rejected", "test_harness",
    "scan 参数是测试注入的静态扫描器，输入 source 是真实 cone 内部变异后的源文本；断言必须出现 cone_intersection_margin/rounded-vector。"
    "这里保留扫描器 callback 是测试架构而非数值高阶构造，且有意要求被扫描的坏数值代码报红。")
add("test_r6fix_geom3.py", "_assert_returned_view_isolation", "test_harness",
    "exact_convex_view 返回视图后，测试故意把 view.verts 的 x 加100，再断言源 p 的顶点/面与源成员/重叠结果未变。"
    "三个诊断调用都观察生产隔离契约，坏写入只落视图；不是用于生成精确几何期望的普通数值 helper。")
add("test_r6fix_geom3.py", "_assert_face_hints_do_not_change_convex_membership", "test_harness",
    "故意反序/交叉/循环或清空 box 的 face hints，再以原点仍在凸包内的固定真值验证两个生产成员 API。"
    "这是拓扑提示不影响坐标凸包的变异牙，不应该通过宽泛数值安全说明豁免其刻意坏输入。")
add("test_r9fix_construction_rounding.py", "_certificate", "exact_proof_gap",
    "lower/upper 是相邻 binary64 转成 F 后加 center 再除2的精确 Fraction 中点；实际所有调用 power 为默认整数1或显式整数2。"
    "lower**power/upper**power 只是有理中点的整数幂证书，不是浮点指数开方。需把有限调用点的整数 power 传播进来；不批准任意指数。")
add("test_r9fix_g03_construction.py", "_bad_witness_report", "test_harness",
    "先在生产 enumerate_covers3 内部源代码插入坏 point_a 再调用 G0，要求 construction_failures 有记录且 completeness 不变。"
    "这是坏显示见证必须报红的真实内部变异牙；调用本身不是安全构造案例，更不能批准注入 payload 的数值路径。")


def matched_scopes(text, scope):
    found = []
    def visit(node, prefix=""):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            qualified = prefix + node.name
            if qualified == scope:
                found.append(node)
            prefix = qualified + "."
        for child in ast.iter_child_nodes(node):
            visit(child, prefix)
    visit(ast.parse(text))
    return found


sites = []
for row in pending.values():
    scope = (row["path"], row["function"])
    category, reason, action = review[scope]
    source = (ROOT / row["path"]).read_text(encoding="utf-8-sig")
    functions = matched_scopes(source, row["function"])
    matching = [fn for fn in functions if any(ast.dump(n, include_attributes=False) == row["node"] for n in ast.walk(fn))]
    assert matching, row
    fn = next((fn for fn in matching if fn.lineno <= row["line"] <= fn.end_lineno), matching[0])
    start = min([fn.lineno] + [n.lineno for n in getattr(fn, "decorator_list", [])])
    selected = "\n".join(source.splitlines()[start - 1:fn.end_lineno])
    # Same function has exact direction sites and separate raw-coordinate noise sites.
    if row["function"] == "geometry_noise" and row["source"].replace(" ", "") == "norm(m[2][fi])":
        category = "exact_proof_gap"
        reason = "m=model(vertices,faces) 先将每个给定标量转 Fraction，m[2][fi] 是有理 Newell 法向；此 norm_exact 在精确向量上末端显示，没有先做 float 差。此局部事实不覆盖同函数 raw vertices 棱长/周长噪声计算。"
        action = "补 model 字段返回证明；只证明本 exact 向量，不把整个 geometry_noise 近似窗口函数作为安全例外。"
    if row["path"] == "tests/perf_escape_oracle_reference.py" and row["function"] == "_candidates":
        if row["source"].startswith(("windows(", "direction_noise(")):
            category = "legacy_approximate_diagnostic"
            reason = "本调用读取明确 legacy extent/方向噪声窗口；av 来自 perf 快照保留的 float move，windows/direction_noise 的原始坐标差可舍入。输出只作为原性能参考的窗口阈值，不是精确几何真值；有理 facet 系数另审。"
            action = "承认性能旧参考的近似窗口边界；不能为 callee 原始 float 差后范数作无舍入担保。"
        elif row["source"].startswith("facet("):
            reason = "a/b=model(av/af,bv/bf) 在 perf 旧 float move 之后将最终坐标转 Fraction；exact_coefficients=True 让 facet 返回有理方向/分子而非显示法向/gap。它对最终给定坐标局部精确，不证明 perf move 是理想实数平移。"
    sites.append({**row, "disposition": category,
                  "reason": f"本 AST 站点 `{row['source']}`：{reason}",
                  "recommended_action": action, "waiver_approved": False,
                  "reviewed_scope_sha256": hashlib.sha256(selected.encode("utf-8")).hexdigest(),
                  "reviewed_scope_lines": [start, fn.end_lineno], "raw_node_still_in_scope": True})

sites.sort(key=lambda r: (r["path"], r["line"], r["rule"], r["node"]))
assert len(sites) == len(pending) == 92
assert set(map(key, sites)) == set(pending)
assert all(r["waiver_approved"] is False for r in sites)
summary = {
    "input": raw_path.name, "input_sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
    "review_kind": "frozen-source supplemental review; NOT waiver approval",
    "prior_reviews": prior_names, "reviewed_sites": len(sites),
    "reviewed_functions": len({(r["path"], r["function"]) for r in sites}),
    "category_counts": dict(Counter(r["disposition"] for r in sites)),
    "all_remaining_frozen_test_keys_covered_once": True,
    "remaining_unreviewed_frozen_test_keys": 0,
    "waiver_approvals": 0, "stale_ast_sites": 0,
    "limits": ["只读审核，不更新 policy；真实近似构造不写成无先舍入。",
               "这是 raw_frozen 与既有四份 tests review 以 path/function/rule/node 交集后的全部剩余测试站点；本轮没有额外 With 站点。",
               "调用被测 API、纯架构/字节摘要、给定输入、近似诊断与有理证明缺口分别列类。"]
}
(OUT / "tests_final_supplement_review.json").write_text(json.dumps({**summary, "sites": sites}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
(OUT / "tests_final_supplement_review_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(summary, ensure_ascii=False, indent=2))
