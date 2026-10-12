"""Read-only source review of the 83 newly surfaced tests sites in round five."""
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "reports/codex/R12FIXb_evidence"
EXCLUDED = {"tests/test_invariance_geom.py", "tests/test_invariance_interlock.py", "tests/test_margin.py"}


def classify(row):
    p, f, s, rule = row["path"], row["function"], row["source"], row["rule"]
    exact = "exact_proof_gap"
    harness = "test_harness"
    fixture = "given_input_fixture_boundary"
    legacy = "bounded_legacy_diagnostic"
    metadata = "metadata"
    if p in {"tests/e5a_escape_oracle.py", "tests/perf_escape_oracle_reference.py"}:
        if f == "facet":
            return exact, "d 与 pa/pb 来自 Fraction model 的有理 Gram 参数，sub(pa,pb) 是精确差，_signed_gap 仅在最后调用统一 sqrt 显示边界；该诊断不是源码中的 float 差分证据。", "补 model/Gram/分支返回类型，不能靠 waiver 免除几何 primitive。"
        movement = ("冻结 perf move 明确先生成调用方浮点平移像，随后按这组给定坐标求 model；不保证理想精确平移。" if "perf_" in p else "当前 move 对坐标与 z 分别 Fraction 提升后相加，但 z 自身已经是最终显示高度。")
        return legacy, "extent_only=True 分支只消耗给定候选位形的参数范围，不构造未使用的显示残余 gap；阈值 extent 是 legacy 搜索带。" + movement, "精确建模常量 extent_only 分支与阈值用途；若保留局部例外，严格限定已声明候选输入/范围带，不能声称所有派生高度无舍入。"
    if p == "tests/e5a_g2_oracle.py":
        return exact, "construction 的独立 model 先将顶点 Fraction 化；n/difference 来自有理 Gram 和射影，squared=numerator**2/dot(n,n) 仍为 Fraction，_unit/_distance_display 是最终边界。", "补有理模型、模式与同名递归的摘要，不登记此类型误报为几何 waiver。"
    if p == "tests/test_bb52_g1.py":
        if f == "result":
            return harness, "pytest 结果夹具调用既有 bb52_g0.analyze 重放固定21×60网格；报告里混有生产比较、精确 G0 验证和旧近似失配归因，不构成整个 analyze 都精确的证明。", "区分固定报告驱动和真实数值构造；callee tools 源中的近似归因需独立审查，不按名称豁免。"
        return legacy, "此前明确先 translate 得到旧逐顶点 float 平移像，再在该给定数据上作独立精确距离审计；此 classify 调用只在 rep.failures 中生成文字归因，其内部 norm(sub(...)) 仍是旧近似段长诊断。", "只可定位为失败报告的旧近似归因；不让其覆盖主 exact oracle 或把已舍入坐标叫作理想平移。"
    if p == "tests/test_e5b_polyhedron_cache.py":
        return harness, "这是原位更改 p.verts 后的缓存失效被测调用；(x+10,y,z) 明确生成新的给定 binary64 坐标，以点内外和对象身份断言失效，未用此输出构造 expected 根。", "记录缓存测试驱动/给定输入角色，生产 exact_convex_view/predicate 仍独立扫描；不全函数免除舍入。"
    if f == "_prism" and p in {"tests/test_entrance3_concave.py", "tests/test_g03_two_rulers.py"}:
        return exact, "n=len(section) 是 int，i 来自 range(n)；n-1、2*n、模和索引加法均为整数拓扑运算，faces 的 +/+= 是序列连接，不是坐标浮点运算。", "修 len/range/序列连接类型事实与参数敏感传播；这些站点不应申请数值 waiver。"
    geometric_fixtures = {
        ("tests/test_edge_arc_per_side.py", "_chamfered_on_box"),
        ("tests/test_frozen_ee_sign.py", "_wedge_pair"),
        ("tests/test_g03_two_rulers.py", "_ridge_pair"),
        ("tests/test_g03_two_rulers.py", "_chamfered_box"),
        ("tests/test_g03_two_rulers.py", "_truncated_cube"),
        ("tests/test_hull_robustness.py", "_ridge_pair"),
        ("tests/test_margin_resolution.py", "_needle"),
        ("tests/test_margin_resolution.py", "_blunt_needle"),
        ("tests/test_margin_resolution.py", "_small_pair"),
    }
    if (p, f) in geometric_fixtures:
        return fixture, "该 helper 用有限 float/三角函数/仿射运算生成明示测试点集，再调用 hull/merge 形成给定输入物体；存在真实输入生成舍入，不能宣称理想锐棱/间隙/旋转逐位精确。本站点不是从被测距离/法向回算 expected。", "若保留例外只能限定给定 binary64 测试输入构造；核对测试 expected 基于实际点集或明确容差，不能扩大为生产几何构造白名单。"
    if p == "tests/test_geom3_e5a.py":
        return fixture, "_quat(5) 源中确实以 float sum(x*x) 后 sqrt 归一化随机四元数，用于给定随机姿态输入，不是精确范数 oracle。不能称其没有先舍入。", "如继续保留随机姿态生成，例外理由必须承认近似输入姿态；精确距离 expected 必须另从最终给定坐标推导。"
    if p == "tests/test_interlock_sensitivity.py":
        if "_steep_two_branches" in s:
            return legacy, "独立源特征 oracle 的 Fraction Newell/范围谓词是真的独立，但其 z=-gap/nz 使用已显示 gap/nz 并在 report band 内判两支；它检验的是严格带内诊断而非精确高度边界。", "明确报告分辨带与给定候选高度边界，不能把整个 helper 视为无舍入。"
        return fixture, "STEEP_KINK+side*e 与 s*d 是固定拐点两侧/尺度网格的给定 float 参数生成；sensitivity_at 是被测调用，解析 truth 与显式尺度/坐标噪声带另行比较。数值舍入存在但不作为精确 root oracle。", "限定为被测输入参数网格，保留两侧/尺度及阈值断言；不豁免生产敏感度构造。"
    limit_drivers = {
        ("tests/test_end_to_end_cb2.py", "_capacity"),
        ("tests/test_invariance_limit.py", "_solve"),
        ("tests/test_invariance_limit.py", "_reference"),
        ("tests/test_limit.py", "_interlock_capacity"),
        ("tests/test_limit.py", "_flat_block_ratio"),
        ("tests/test_limit_contacts.py", "_hovering_block"),
        ("tests/test_limit_scale.py", "_capacity_ratio"),
        ("tests/test_limit_selfcheck.py", "_utm_block"),
        ("tests/test_r10_resolution.py", "_unbounded"),
    }
    if (p, f) in limit_drivers:
        extra = "_reference 是同一生产求解器的基准位形，用于变换不变性对照，不是独立数值 oracle。" if f == "_reference" else ""
        return harness, "该站点直接调用被测 limit_load/limit_load_multi（或其驱动），实际 contacts/wrench 是本测试给定模型；没有通过未知 callable 构造 expected。仍需审查被调数值实现为何源摘要未知，不能据此宣布它精确。" + extra, "保留测试驱动角色与模型口径；生产求解器原位继续默认拒绝未知/舍入到构造，不能传播 caller waiver 到 callee。"
    if p == "tests/test_frozen_surface_diagonal.py":
        return harness, "frozen.ee_normal_generic 是被测法向 API，结果直接与独立解析 (.8,0,.6) 及显式1e-14容差比较；expected 不借该输出或几何 primitive 构造。", "仅定位为 SUT 断言驱动；继续审查生产 frozen 源摘要，禁止整类 normal 免检。"
    if p == "tests/test_kernel2d_review.py":
        return harness, "将给定 rows 写成 CSV 后让两个生产读取器同读，返回导入的几何/索引供比较；没有在 helper 中以近似范数生成 expected。文本路径或 reader 模型转换被误作构造输入。", "区分 I/O 驱动与 reader 的给定坐标解析，检查源参数依赖，不豁免 reader 内未知数值调用。"
    if p == "tests/test_limit_fuzz.py":
        return fixture, "pert 是按显式相对幅度独立生成的给定浮点荷载；_exact_status_alpha 随后对该同一 LP 用独立 Fraction 证书求状态/最优值。Fn/Mn/R 的近似范数只设扰动幅度，不作为理想精确荷载证书。", "限定扰动模型输入角色并承认近似幅度；核对 exact LP 从最终给定 contacts/dead/pert 重建，不将 perturb 之前理想值冒充精确输入。"
    if p == "tests/test_lp_certificates.py":
        return fixture, "原 SI 模糊生成器先产生随机浮点旋转、尺寸、平移和给定荷载；P 现已是显式局部 def，mv 直接做同次序矩阵乘加，不再 lambda callable。P 定义在分支/循环内且捕获默认 R/off 的源绑定摘要仍不足。", "补局部分支 def/default snapshot 的静态绑定，或保留只面向给定 SI 样本生成的说明；不能声称浮点旋转/归一化本来无舍入。"
    if p == "tests/test_perf_edge_frame.py":
        return harness, "此前 _outcome(func) 已改成直接 C._qedge_contains；该 wrapper 仅取得 SUT 结果/零长棱 ValueError，独立 _reference_outcome 调本地 Fraction oracle。", "补被调源摘要或按单一 SUT 驱动站点审查；不得重新引入任意 callable outcome。"
    if p == "tests/test_perf_interlock.py":
        return harness, "调用缓存版 _candidates，在两个实际不同 offset 上与 uncached 对照；first!=want 防止同产物假牙，等价断言只证明缓存键正确，不证明候选近似窗口无舍入。", "保留缓存路径、产物互异断言及生产原位扫描；不把性能缓存对照提升成独立 exact 构造证明。"
    if p == "tests/test_r12fixb_structure_flow.py":
        return metadata, "source_project 是 pytest 专用临时源码夹具，mkdir/write_text 只在受控 basetemp 写入有限测试字符串供 scanner 读取，字符串内缺陷不会被本 helper 执行。", "按 root 要求明确重命名为 test driver fixture，或建模 Path/pytest 元数据；不为这7项增加范围 waiver。"
    if p == "tests/test_r8fix_margin_gap_gate.py":
        return harness, "保留原 ordinary 姿态的完整被测 invariance 测试，再调用独立 binary64 midpoint gap 牙；调用别的 test driver 不是数值 expected 构造。", "按实际测试驱动定位，不移除原节点或内部变异断言；被调用模块继续单独扫描。"
    if p == "tests/test_r9fix_cover_parameters.py":
        return exact, "a/b 的每个坐标先 F(...)，da/db/w 为 Fraction 分量差；局部 dot 已从 lambda 改成显式 def，sum(x*y) 仍有理，独立 Gram 参数与 c.exact_params 严格比较。", "修 if 分支内局部 def 词法绑定和有理返回摘要；这不是需要豁免的先舍入参数构造。"
    raise AssertionError((p, f, s, rule))


def scope_data(row):
    text = (ROOT / row["path"]).read_text(encoding="utf-8-sig")
    scopes = []
    def visit(node, prefix=""):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                name = prefix + child.name
                if name == row["function"]:
                    scopes.append(child)
                visit(child, name + ".")
            else:
                visit(child, prefix)
    visit(ast.parse(text))
    matching = [n for n in scopes if any(ast.dump(c, include_attributes=False) == row["node"] for c in ast.walk(n))]
    scope = next((n for n in matching if n.lineno <= row["line"] <= n.end_lineno), matching[0] if matching else scopes[0])
    source = ast.get_source_segment(text, scope)
    return {"reviewed_scope_sha256":hashlib.sha256(source.encode("utf-8")).hexdigest(),
            "reviewed_scope_lines":[scope.lineno,scope.end_lineno], "raw_node_still_in_scope":bool(matching)}


def main():
    rows = json.loads((OUT / "round5_unreviewed_sites.json").read_text(encoding="utf-8"))
    selected = [r for r in rows if r["path"].startswith("tests/") and r["path"] not in EXCLUDED]
    reviewed = []
    for row in selected:
        disposition, reason, action = classify(row)
        reviewed.append({**row, "disposition":disposition, "reason":reason,
                         "recommended_action":action, "waiver_approved":False, **scope_data(row)})
    assert len(reviewed) == 83
    (OUT / "tests_round5_supplement_review.json").write_text(json.dumps(reviewed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    counts = Counter(r["disposition"] for r in reviewed)
    summary = {"raw_sites":len(reviewed), "functions":len({(r['path'],r['function']) for r in reviewed}),
               "dispositions":dict(counts), "waivers_approved":0,
               "stale_raw_nodes":sum(not r["raw_node_still_in_scope"] for r in reviewed)}
    (OUT / "tests_round5_supplement_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
