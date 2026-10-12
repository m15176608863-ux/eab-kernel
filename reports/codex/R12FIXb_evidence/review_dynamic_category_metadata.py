"""Read current source and propose metadata corrections; never modify the policy."""
import ast
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
ledger_path = HERE / "local_review_decisions.json"
ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
rows = [r for r in ledger["decisions"] if r["category"] == "UNFINISHED_NUMERICAL_DYNAMIC_REWRITE"]
assert len(rows) == 34

# These conclusions were made by reading every listed scope and the relevant
# Frame.__call__, _move, _pair_for_name and _margin_pair_for_name definitions.
descriptions = {
    "_fraction_membership": (
        "REMOVED_DYNAMIC_SYNTAX_STALE_REASON", "PROOF_GAP_MANUAL_EXCLUSION", "SOURCE_PROOF_GAP_EXACT_FLOW",
        "当前 point 已由显式 Fraction generator 转为有理数，不再使用 map(F, point)。本调用为命名的一阶 exact_convex_view/local_facets3；后续点差、点积、tol² 与 closest-hull 比较在 Fraction 路径。当前 scanner 尚未证明完整来源/返回摘要，故仅登记局部证明缺口，不再以动态 map 为由排除；这不是对任意来历坐标或调用链的精确安全批准。"),
    "_wedge_pair": (
        "REMOVED_DYNAMIC_SYNTAX_STALE_REASON", "INPUT_MODEL_OR_OUTPUT_BOUNDARY", "given_input_fixture_boundary",
        "mirror 已改为局部命名 def 并直接调用，当前函数没有旧数值 lambda 分派。convex_hull_3d 消费由浮点楔形位置/间隙公式形成的实际给定坐标；这些公式存在舍入，后续符号 oracle 应基于实际坐标核对。此项是测试输入模型边界与 callee 证明缺口，不是理想未舍入楔形的精确构造批准。"),
    "Frame.poly": (
        "CURRENT_NUMERICAL_CALLABLE_PROTOCOL", "UNFINISHED_NUMERICAL_DYNAMIC_REWRITE", "DYNAMIC_NUMERIC_REWRITE",
        "当前仍执行 self(p)，通过 Frame.__call__ 对顶点作浮点姿态变换后包装 Polyhedron。对象 callable 协议超出当前一阶证明，需改为明确方法/变换参数；此局部过渡排除不证明任意 self 的实现，也不声称浮点乘加无舍入。两个规则行对应同一 AST 调用，不是两个独立调用。"),
    "_T": (
        "CURRENT_NUMERICAL_CALLABLE_ESCAPE", "UNFINISHED_NUMERICAL_DYNAMIC_REWRITE", "DYNAMIC_NUMERIC_REWRITE",
        "当前 _T 仍返回捕获旋转/尺度/位移的 pt、vec、poly 函数元组，调用方解包并调用；该 AST 是 callable 逃逸引用而非一次调用。应改显式参数和一阶 helper。采样坐标/噪声尺度使用浮点乘加，过渡排除不构成无舍入保证。"),
    "_floor_in_reference_units": (
        "CURRENT_NUMERICAL_CALLABLE_INVOCATION", "UNFINISHED_NUMERICAL_DYNAMIC_REWRITE", "DYNAMIC_NUMERIC_REWRITE",
        "当前 poly 由 _T 返回的函数元组解包得到，此处仍以 poly(P) 执行数值变换，随后仅计算参考单位下的坐标噪声尺度。需要改显式变换参数/一阶 helper；近似阈值用途不能作为允许未知 callable 的机器证明。两个规则行对应同一 AST 调用。"),
    "_g0_exact_affine": (
        "CURRENT_DYNAMIC_WITH_PARTLY_STALE_REASON", "UNFINISHED_NUMERICAL_DYNAMIC_REWRITE", "DYNAMIC_NUMERIC_REWRITE",
        "当前仍返回 vec/poly 闭包，poly 内仍有 map(vec, P)，但旧 map(Fraction, p) 已改成显式 generator。vec 的输入分量转 Fraction 后执行有理 affine；cos/sin 和 tm*cos/sin 的系数先在浮点中生成，Fraction 仅保留这些给定系数，不能声称对理想实数运动无中间舍入。需把闭包逃逸和 map(vec, P) 改为一阶显式参数/helper，当前仅局部过渡排除。"),
    "_g0_exact_affine.poly": (
        "CURRENT_DYNAMIC_WITH_PARTLY_STALE_REASON", "UNFINISHED_NUMERICAL_DYNAMIC_REWRITE", "DYNAMIC_NUMERIC_REWRITE",
        "当前 poly 中 map(vec, P) 仍将数值闭包传入高阶函数；旧 map(Fraction, p) 已不存在。vec 对当前给定系数及 Fraction 分量作有理运算，但系数由浮点三角函数/乘法形成，不能把整体理想运动称为无舍入。应改直接 comprehension/一阶 helper；此引用或调用的排除不自动证明未知 callback。"),
    "_base": (
        "REMOVED_DYNAMIC_SYNTAX_STALE_REASON", "APPROXIMATE_OR_NOMINAL_SCOPE_EXCLUSION", "test_execution_with_approx_diagnostic",
        "当前已由 _pair_for_name 的固定分支直接调用各 fixture factory；虽仍从 PAIRS 取出 make 身份，但本函数不执行它。该站点读取被测 body_distance 或 local_facets3；math.dist 仅用已显示见证点选近距离并列标签，含真实浮点差/范数舍入。闭式/独立 brute 参考另行给出；这只是测试基准/近似标签诊断范围排除，不是精确距离证明，也不再是动态 factory 改写遗留。"),
    "_margin_ref": (
        "REMOVED_DYNAMIC_SYNTAX_STALE_REASON", "APPROXIMATE_OR_NOMINAL_SCOPE_EXCLUSION", "APPROXIMATE_DIAGNOSTIC_NOT_EXACT",
        "当前已由 _margin_pair_for_name 的固定分支直接建立 fixture，取出的 make 身份不再被执行。body_distance 的输出用作参考距离；norm(sub(c.point_a, c.point_b)) 对已显示见证点先作浮点差再求范数，用于容差下的并列标签选择，确实可能先舍入再构造。此项仅排除该近似诊断，不能声称精确距离/逃逸真值安全，也不再属于动态 factory 改写遗留。"),
    "_map_back": (
        "CURRENT_NUMERICAL_CALLABLE_INVOCATION", "UNFINISHED_NUMERICAL_DYNAMIC_REWRITE", "DYNAMIC_NUMERIC_REWRITE",
        "当前 P 仍为传入的位置变换 callable，并在 P((0.0,) * dim) 执行，用于求解机构回到参考系的近似功率残差核查。需改传显式 R/s/t 并直接调用一阶 helper；近似诊断用途不是未知 callable 的安全证明。两个规则行对应同一 AST 调用。"),
    "_transform": (
        "CURRENT_NUMERICAL_CALLABLE_ESCAPE", "UNFINISHED_NUMERICAL_DYNAMIC_REWRITE", "DYNAMIC_NUMERIC_REWRITE",
        "当前仍返回捕获 R、t、s 的 P 数值闭包，供 _map_back 等调用；该 AST 是 callable 逃逸引用。浮点位置/荷载/面积公式形成 LP 的实际给定模型，不能称为理想变换的无舍入证书。需改显式变换数据/一阶 helper，本项保留为未完成动态改写而非精确批准。"),
    "q": (
        "CURRENT_NUMERICAL_DATA_REFLECTION_NOT_CALLABLE_DISPATCH", "UNFINISHED_NUMERICAL_DYNAMIC_REWRITE", "DYNAMIC_NUMERIC_REWRITE",
        "当前仍通过 getattr(v, 'exact', F(v)) 反射读取 exact-witness 数据属性，未调用取出的属性，因此不是数值 callable 分派；默认 F(v) 在 getattr 调用前求值。若原始 v 已先舍入，转 Fraction 不能恢复理想值。应改为明确受支持类型/字段分支；仅保留此数值 helper 的反射改写遗留，不允许任意 getattr 或属性协议。两个规则行对应同一 AST。"),
    "_write_case": (
        "NONNUMERICAL_SERIALIZATION_CATEGORY_MISMATCH", "STRUCTURAL_DATA_OR_PROTOCOL_REVIEW", "METADATA_OR_IO",
        "当前 map(str, ...) 将给定 CSV 字段转为文本，join/write_text 写入 reader 测试输入；此路径不取出或执行数值函数，也不做开方、范数、单位化或几何差分构造。str 的格式化及重新读取定义的是实际测试文件内容，不是理想数值的精确构造保证。仅为序列化/I/O 协议的局部排除，不应列为未完成数值动态改写。"),
    "_small_pair": (
        "REMOVED_DYNAMIC_SYNTAX_STALE_REASON", "INPUT_MODEL_OR_OUTPUT_BOUNDARY", "given_input_fixture_boundary",
        "sc 已改为局部命名 def 并直接调用，当前不再有旧数值 lambda。convex_hull_3d/merge_coplanar 接收三角函数、平移、尺度等浮点公式形成的实际 fixture 坐标，存在舍入；测试关注给定坐标下的短棱/分辨率行为，不保证理想 affine 精确保持。此项为测试输入模型/调用摘要边界，不再是动态 lambda 遗留。"),
    "sat_cases": (
        "REMOVED_DYNAMIC_SYNTAX_STALE_REASON", "INPUT_MODEL_OR_OUTPUT_BOUNDARY", "given_input_fixture_boundary",
        "当前 _move 已把 map(scalar_exact, ...) 改为显式 generator，每次 scalar_exact 均直接命名调用。旋转、尺度、位移先在 Fraction 域计算；rounded=False 保留有理坐标，rounded=True 则有意输出最终 rounded fixture 坐标作为实际被测输入。这不是未知高阶调用，也不承诺两种输入代表同一理想未舍入几何；本行保留的是调用摘要/输入模式边界，不能再以旧 map 理由排除。"),
}

scopes = {}
texts = {}
for row in rows:
    path = row["path"]
    if path in scopes:
        continue
    text = (ROOT / path).read_text(encoding="utf-8-sig")
    texts[path] = text
    found = {}
    def walk(node, prefix=""):
        for child in ast.iter_child_nodes(node):
            name = prefix
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                name = (prefix + "." if prefix else "") + child.name
                found.setdefault(name, []).append(child)
            walk(child, name)
    walk(ast.parse(text))
    scopes[path] = found

suggestions = []
for row in rows:
    issue, category, disposition, reason = descriptions[row["function"]]
    candidates = scopes[row["path"]][row["function"]]
    matches = [n for scope in candidates for n in ast.walk(scope)
               if ast.dump(n, include_attributes=False) == row["node"]]
    assert matches, row["id"]
    node = matches[0]
    suggestions.append({
        "id": row["id"], "path": row["path"], "function": row["function"], "rule": row["rule"],
        "old_category": row["category"], "old_reason": row["reason"],
        "new_category": category, "new_review_disposition": disposition,
        "new_reason": "当前站点 `" + row["source"].replace("\n", " ") + "`：" + reason,
        "metadata_only": True, "may_change_node_or_context": False,
        "source_review_result": issue,
        "reviewed_node_at_inspection": row["node"],
        "reviewed_context_at_inspection": row["context"],
        "current_ast_source": ast.get_source_segment(texts[row["path"]], node),
        "current_ast_line": node.lineno,
        "current_scope_source": "\n\n".join(ast.get_source_segment(texts[row["path"]], n) for n in candidates),
        "waiver_approved": False,
    })

result = {
    "purpose": "只读逐站点复核后建议更正 category/reason/disposition；不批准数值安全，不安装 policy。",
    "ledger_sha256_at_review": hashlib.sha256(ledger_path.read_bytes()).hexdigest(),
    "rows_reviewed": len(suggestions),
    "current_source_results": dict(Counter(r["source_review_result"] for r in suggestions)),
    "proposed_categories": dict(Counter(r["new_category"] for r in suggestions)),
    "dynamic_category_after_proposed_reclassification": 16,
    "remaining_callable_reference_or_invocation_rows": 14,
    "remaining_data_reflection_rows": 2,
    "removed_dynamic_syntax_reason_rows": 15,
    "serialization_category_mismatch_rows": 3,
    "partly_stale_reason_rows_with_actual_dynamic_remaining": 4,
    "application_contract": "仅由 root 显式采用每行新 metadata；不得复制、刷新或替换 node/context。真实 issue AST 更正由 root 的独立绑定证据处理，不能由本建议续签。",
    "corrections": suggestions,
}
(HERE / "suggested_metadata_corrections.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="")
print(json.dumps({k: v for k, v in result.items() if k != "corrections"}, ensure_ascii=False, indent=2))
