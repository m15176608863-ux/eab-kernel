"""Read-only source review; never writes policy or changes the numerical code."""
from __future__ import annotations

import ast
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "reports/codex/R12FIXb_evidence"
RAW = OUT / "round6_unreviewed_sites.json"
rows = json.loads(RAW.read_text(encoding="utf-8"))
external = json.loads((OUT / "tests_round6_external_review.json").read_text(encoding="utf-8"))

geom = "tests/test_invariance_geom.py"
interlock = "tests/test_invariance_interlock.py"
margin = "tests/test_margin.py"
fixture_action = (
    "只可明确讨论给定 binary64 测试输入的边界，不得称此算式没有舍入；"
    "若要求理想几何变换也精确，须另做独立 Fraction 构造并核对旧格子，而不是批准通用数值 helper。"
)
scopes = {
    (geom, "body_distance"): (
        "test_execution_legacy_contact_window",
        "此处只把未改动的 A/B 传给生产 contact_resolution，所得尺度窗口显式传给生产 body_distance。"
        "它是保留历史容差窗口的被测 API 调用，不是独立期望值构造；默认精确 API 另逐格审核。"
        "包装层自身没有先计算距离或法向，不能因此断言所有 A/B 上游 fixture 都精确。",
        "保留被测路径和显式 legacy window 标签；应分析 contact_resolution 的实际契约，不能以本调用站点豁免其内部数值实现。",
    ),
    (interlock, "body_distance"): (
        "test_execution_legacy_contact_window",
        "此包装函数把原样 A/B 与 kwargs 传给生产 body_distance，只额外显式提供 contact_resolution(A,B)。"
        "该值规定历史测试所用接触窗口，而不是 independently computed 精确距离；文件另外检查默认精确 API 的实际舍入输入。"
        "本调用站点没有自行作几何差，但也不证明上游 float 构造无舍入。",
        "保持 legacy window 的诚实范围；需要生产函数摘要，而不是给所有以此包装进入的数值路径整体放行。",
    ),
    (geom, "_slab"): (
        "given_input_fixture_boundary",
        "此算式是固定 x_cross / yaw 样本的 box 顶点绕 z 旋转再平移，ct/st 来自 math.cos/sin。"
        "float 乘加确实舍入，结果成为 Polyhedron 的给定坐标，不是精确旋转后的理论点。"
        "独立精确盖/拓扑 oracle 针对这些最终给定坐标；旧蜕变距离仍按声明的噪声预算比较。",
        fixture_action,
    ),
    (geom, "_pair_tetra_box_vv"): (
        "given_input_fixture_boundary",
        "该分量参与固定 VV3 样本：先用 sqrt(3.0) 的显示值形成 r3，再用 0.1*r3 定义 apex，"
        "最后按 apex-T0 顶点的 float 差平移四面体。此流程真实舍入，理想距离 0.1 只是带容差的闭式基准；"
        "不得把它写成精确单位化或精确平移。",
        fixture_action,
    ),
    (geom, "_pair_box_box_face"): (
        "given_input_fixture_boundary",
        "该加法定义面对面方块的 z 中心，来自 half-height 0.5、目标间隙 0.05 与 A 的 half-height 0.35。"
        "它产生实际 binary64 box 输入，可能与实数三数之和不同；测试随后对实际坐标做精确边界/盖检查，"
        "历史 0.05 距离比较不是其无舍入证明。",
        fixture_action,
    ),
    (geom, "_pair_generic"): (
        "given_input_fixture_boundary",
        "Random(5) 的 uniform 样本在此加固定中心偏移，生成第二个凸包的坐标。"
        "该普通 float 运算流入凸包几何，实际有舍入；这里的角色是固定采样输入，不是对采样前理想实数的构造保证。"
        "3 个偏移分量和 RNG 消费顺序均与原工单代码相同。",
        fixture_action,
    ),
    (geom, "_pair_ve3_wedge"): (
        "given_input_fixture_boundary",
        "此分量构造尖棱锥的三个底面顶点：用 cos(0.5)/sin(0.5) 旋转，再平移 x=0.3、z=VE3_GAP+1。"
        "float 乘加确实发生在凸包输入之前；尖端固定 (0.3,0,VE3_GAP) 的闭式分离关系不等于所有底面顶点精确构造。"
        "应只承认给定坐标 fixture 和针对实际输入的独立检查。",
        fixture_action,
    ),
    (geom, "_pair_ridge_needle"): (
        "given_input_fixture_boundary",
        "此表达式参与固定脊+针 fixture：尖端高度 h+0.05，底环以 cos/sin 三个固定角与半径 0.3 生成，底高 h+1.05。"
        "三角函数及 float 加乘均舍入，之后才给 convex_hull_3d；解析 0.05 距离只说明设计意图和旧容差基准。"
        "保留原坐标不等于证明理想实数圆锥构造精确。",
        fixture_action,
    ),
    (geom, "_pair_size_ratio"): (
        "given_input_fixture_boundary",
        "50.0+0.5+1e-3 是尺寸比 100 样本小方块的 x 中心；第二次加法可能舍入。"
        "所得 box 输入保持原 bit pattern，测试的 1e-3 间隙对照带原有容差，不能据此将中心构造称为精确。",
        fixture_action,
    ),
    (geom, "_pair_for_name"): (
        "direct_fixture_dispatch_with_rounded_inputs",
        "此站点是固定名称 if 分支中的已知一阶 fixture 函数直调，不再从 PAIRS 取 callable，也没有 lambda 捕获。"
        "callee 返回固定采样/旋转/三角函数生成的给定 float 顶点，具体舍入已在该 callee 各站点列出；"
        "直接化使调用可追踪，不会让下游浮点几何自动变安全。22 factory 顶点/面/顺序与旧版本逐项运行时相等。",
        "保留一阶调用传播并分别审 callee；不要为此 dispatcher 批准能吞掉 callee 数值风险的整体例外。",
    ),
    (geom, "_base"): (
        "direct_fixture_dispatch_with_rounded_inputs",
        "此调用只按固定 PAIRS 名称取得 A/B，原容器 callable 已换为 _pair_for_name 的显式分支。"
        "所得坐标仍是原有给定 binary64 fixtures；_base 后续被测 API、显示见证 math.dist 的近似并列分类各有独立审核，"
        "不能靠本取样站点替整个 _base 作精确担保。",
        "应分别追踪一阶 factory 的返回值及后续诊断用途，保持源站点诊断；不可 broad-waive _base 的构造或近似距离。",
    ),
    (interlock, "_yawed_stack"): (
        "given_input_fixture_boundary",
        "此算式定义 sep_ee_yaw 固定样本：先设箱体中心 z=1+gap，再用 cos(yaw)/sin(yaw) 旋转顶点。"
        "float 乘加是真实舍入，结果作为 Polyhedron 的给定坐标；该测试检验近乎平行 EE 格，不保证理想实数 yaw 的精确几何。",
        fixture_action,
    ),
    (interlock, "_margin_pair_for_name"): (
        "given_input_fixture_boundary",
        "0.4-3e-10 是原 subtol 格的实际给定平移高度，刻意落在历史接触窗口内部；减法确实舍入。"
        "原 MARGIN_CASES 的 lambda 改成显式 if 后，运算次序、常数、顶点和测试名称完全保留，"
        "默认精确判定另对给定坐标检查；不能把这个 subtract 称为精确派生量。",
        fixture_action,
    ),
    (margin, "_true_normal"): (
        "test_execution_direct_api",
        "这里使用 from eab.margin import inflated_normal as _TRUE_INFLATED_NORMAL 的直接源级绑定，"
        "将未改动的 E/x 传给被测 API 并仅缓存其返回值。它不是容器取 callable 或 callback，"
        "也不是独立真法向 oracle；normal 将进入旧 Lipschitz 浮点差商诊断，该差商另列遗留。",
        "应解析明确导入绑定及生产函数的实际输入契约；保留 cache 行为，不把被测 API 输出当作独立精确期望值。",
    ),
    (margin, "_lipschitz_worst"): (
        "legacy_approximate_diagnostic",
        "nx/ny 是测试驱动预先算好的真实或变异法向样本，此站点先用 float sub 做法向差，再 norm，"
        "确有先舍入再求范数；分母同样对给定点做差后范数。它只产生旧 Lipschitz 差商上下界的近似观测量，"
        "不是精确法向构造，不可写成无先舍入。改写仅取消 normal_fn 高阶参数，原6类正常/变异调用序列和结果逐位等价。",
        "如当前阶段保留全部旧门，必须诚实列为近似诊断遗留并保留真实变异牙；若要满足严格精确构造，需独立有理平方差商重写并复核全部样本。",
    ),
    (margin, "_lipschitz_verdict"): (
        "legacy_approximate_diagnostic",
        "此一阶调用把 local/loops/glob 的 (x,y,nx,ny) 数据交给 _lipschitz_worst，"
        "该 helper 的 float 差后 norm 具有真实提前舍入。此层只按原顺序汇总差商并对 2/delta 与 0.9/delta 判界；"
        "取消 callback 不会使旧经验性 Lipschitz 量成为精确构造证明。",
        "保留独立定理阈值、三组样本和6类故障牙；不能通过仅豁免 caller 掩盖 _lipschitz_worst 的近似构造遗留。",
    ),
}


def key(row):
    return tuple(row[k] for k in ("path", "function", "rule", "node"))


trees = {}


def checked_scope(row):
    path = row["path"]
    if path not in trees:
        source = (ROOT / path).read_text(encoding="utf-8-sig")
        trees[path] = (source, ast.parse(source))
    source, tree = trees[path]
    fn = next(n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == row["function"])
    assert any(ast.dump(n, include_attributes=False) == row["node"] for n in ast.walk(fn)), row
    start = min([fn.lineno] + [d.lineno for d in fn.decorator_list])
    scope_source = "\n".join(source.splitlines()[start - 1:fn.end_lineno])
    return hashlib.sha256(scope_source.encode("utf-8")).hexdigest(), [start, fn.end_lineno]


local = []
for row in rows:
    if row["path"] not in {geom, interlock, margin}:
        continue
    disposition, reason, action = scopes[row["path"], row["function"]]
    scope_sha, scope_lines = checked_scope(row)
    local.append({
        **row,
        "disposition": disposition,
        "reason": f"本 AST 站点 `{row['source']}`：{reason}",
        "recommended_action": action,
        "waiver_approved": False,
        "reviewed_scope_sha256": scope_sha,
        "reviewed_scope_lines": scope_lines,
        "raw_node_still_in_scope": True,
    })

assert len(local) == 53
assert len(external) == 41
sites = sorted(local + external, key=lambda r: (r["path"], r["line"], r["rule"], r["node"]))
assert len({key(r) for r in sites}) == len(sites) == len(rows) == 94
assert {key(r) for r in sites} == {key(r) for r in rows}
assert all(r["waiver_approved"] is False and r["raw_node_still_in_scope"] for r in sites)

summary = {
    "input": RAW.name,
    "input_sha256": hashlib.sha256(RAW.read_bytes()).hexdigest(),
    "review_kind": "source-context review only; NOT waiver approval",
    "reviewed_sites": len(sites),
    "reviewed_functions": len({(r["path"], r["function"]) for r in sites}),
    "category_counts": dict(Counter(r["disposition"] for r in sites)),
    "all_raw_keys_covered_once": True,
    "waiver_approvals": 0,
    "limits": [
        "固定采样输入、近似数值诊断、被测 API 执行与精确 oracle 必须区分；此文件不修改 policy。",
        "真实 float 差/Gram/见证经根或范数的站点如实保留为遗留，不声明无先舍入。",
        "本审核针对 round6 当前源码快照；后续任何源码修改须重新匹配 AST 与所在作用域，不可整体重新批准。",
    ],
}
(OUT / "tests_round6_supplement_review.json").write_text(json.dumps({**summary, "sites": sites}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
(OUT / "tests_round6_supplement_review_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(summary, ensure_ascii=False, indent=2))
