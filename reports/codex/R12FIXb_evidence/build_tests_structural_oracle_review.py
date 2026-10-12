"""Read-only, explicit per-scope review of the round-4 structural inventory."""
from __future__ import annotations

import ast
from collections import Counter
import fnmatch
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "reports/codex/R12FIXb_evidence"
EXCLUDED = {
    "closed-rounded-construction", "closed-unproved-arithmetic",
    "closed-reduction", "closed-rounded-call",
}
PATTERNS = ["tests/e5*oracle.py", "tests/perf_*reference.py", "tests/test_perf_*.py"]


def classify(row):
    p, f, s, rule = row["path"], row["function"], row["source"], row["rule"]
    exact = "exact_proof_gap"
    meta = "metadata"
    rewrite = "dynamic_numeric_rewrite"
    legacy = "bounded_legacy_diagnostic"
    mutation = "intentional_mutation"
    harness = "test_harness"

    if p.endswith("e5a_convex_oracle.py"):
        if f == "canonical_payload":
            return meta, "key 只排序面环的整数拓扑标签，并未调用数值函数或构造坐标；嵌套 sorted/tuple 投影超出现有键摘要。", "改成显式预计算拓扑排序键，或补可验证的纯数据键摘要；不放行任意 lambda。"
        if f == "canonical_view":
            return meta, "SimpleNamespace 仅承载 Q.hull 已算出的顶点、面和来源索引；此站点无数值运算。", "为显式字段记录载体补有限摘要，继续传播字段的真实类型和污染。"

    if p.endswith("e5a_cover_oracle.py"):
        if f in {"dot", "cross"}:
            return meta, "F/int 出现在 type(x) in (F,int) 的类型身份比较，不被间接调用，也不产生数值。", "按 AST 使用位置证明类型身份引用；不得整体允许 callable 作为数值值流转。"
        if f == "witness_points":
            return exact, "FV/EV3 对称分支仅交换两物体并转为 VF/VE3，保持 exact 标志；模型顶点先转 Fraction，Gram 差分精确，exact=True 在最终显示转换前返回。", "补有限枚举分支/对称递归摘要并保持 exact 模式敏感；不能豁免整个 witness_points。"
        if f == "witness_distance":
            return exact, "明确 witness_points(...,exact=True)，随后对有理见证作分量差，最后才 norm_exact；递归/模式返回类型未获证明。", "修 witness_points 的源返回类型摘要，证明精确差分后的一次边界构造。"
        if f == "_margin_witness_distance":
            return exact, "此分支调用 witness_distance，后者取 exact=True 有理见证再差分并最终 norm_exact；折面另走有理三角形距离。", "修被调函数精确返回摘要；不可把外层名称作为可信构造白名单。"
        if f == "margin_witness_squared":
            if "witness_points" in s:
                return exact, "此站点明确 exact=True，预期得到 Fraction 见证；本函数返回平方距离而非先舍入的根。", "补模式敏感见证摘要，不登记数值 waiver。"
            if "_ring_triangles" in s:
                return exact, "points/ring 来自先 Fraction 化的表面模型；该 helper 做有理三角剖分。其源实现的数值 key 投影需另行证明或改写。", "沿实际源调用链处理三角剖分摘要及 key 投影，不直接豁免该 call。"
            return exact, "_point_tri_sq 对 Fraction 点和三角形求平方距离，外层 min 仍在有理域；此处无 float 根回流。", "修精确三角剖分/平方距离摘要并保留输入污染。"
        if f == "assert_margin_gap_rounding":
            return meta, "此前已断言 value 是有限 binary64；>d pack 与 >Q unpack 只重解释结果位型取得偶数尾数，作为独立 Fraction 中点舍入格检验，不构造几何。", "可审查本对固定端序/位宽的位型读取站点；禁止推广成任意 struct.pack/unpack 保精确。"
        if f == "margin_selection":
            return legacy, "_margin_witness_distance 的最终显示距离参与既有 ctol/legacy 选择带；距离计算源链可精确，但显示带裁决不是精确集合选择定理。", "先修被调源证明；若仍保留例外，只能表述为指定 legacy 显示/容差选择契约。"

    if p.endswith("e5a_escape_oracle.py") or p.endswith("perf_escape_oracle_reference.py"):
        frozen = "perf_" in p
        movement = ("冻结参考 move 先执行调用方浮点平移，其后 model 把这些给定坐标提升为有理数；不声称理想精确运动。" if frozen else "当前 move 在加法前分别 F(p[k])/F(offset[k])，模型几何保持有理域。")
        if f == "facet":
            if s.lstrip().startswith("facet("):
                return exact, "对称 FV 分支交换物体并转为 VF，原样保留 extent_only/exact_coefficients；有理 Gram 几何的有限对称递归摘要缺失。" + movement, "补标志敏感/对称分支源摘要，不豁免一般递归或所有 facet 调用。"
            return exact, "法向及见证差来自 model 的 Fraction 顶点和 Gram 运算；unit/_signed_gap 仅在返回显示值时调用统一边界。" + movement, "证明有理操作数及分支模式；真实 float 派生输入仍须拒绝。"
        if f == "geometry_noise":
            if "m[2]" in s:
                return legacy, "m[2][fi] 为有理模型法向，最终 norm 用于面/边噪声报告；整个函数的原始边长分支仍可能先作浮点差，不能宣称函数整体精确。", "仅按 legacy 噪声诊断角色逐分支核对；不要全函数或 norm 原语豁免。"
            return legacy, "原始 vertices 的 sub 可先浮点舍入，再 norm；这是遗留边长/周长噪声估计而非精确几何证书，不能说没有先舍入。", "明确保留的近似诊断契约或改成 Fraction 差分；不得当 exact-proof-gap 自动免除。"
        if f == "direction_noise":
            return legacy, "geometry_noise 的近似不确定量仅驱动遗留方向噪声阈值；F(ae)+F(be) 固定的是已给定诊断量，不会恢复此前精度。", "把近似噪声估计与几何证书边界分开，逐站点限定诊断用途。"
        if f == "windows":
            return legacy, "norm(sub(p,v[0])) 可对原始 float 先作差；此结果只形成 legacy extent/epsilon 窗口，不能包装成精确差分构造。", "优先 Fraction-before-difference，或明确局部近似搜索窗口例外；绝不一般放行。"
        if f == "candidates":
            return legacy, "一阶缓存封装调用 _candidates；其内部同时含 exact_coefficients 的几何与 legacy 噪声/窗口筛选，不能由包装函数名证明全部精确。" + movement, "分别审查内部近似窗口和精确几何参数，避免全参数 sink 或整函数 waiver。"
        if f == "_candidates":
            if rule == "subtract-rounded":
                return legacy, "z-zprev 只与 rounding 比较决定是否复用已计算平移体；不流入 sqrt/norm/unit。每个候选仍以给定 z 位形通过 extent_only 的独立检查。" + movement, "记录缓存复用比较的有界 legacy 用途；不能据此允许一般浮点几何差分。"
            if "windows(" in s:
                return legacy, "windows 只给候选搜索的 legacy extent/epsilon 阈值；其 raw-coordinate 长度存在先浮点差分，不能当精确原语。", "精确化窗口长度或把近似搜索阈值用途作为局部待审项目。"
            if "direction_noise(" in s:
                return legacy, "调用近似几何噪声估计作为候选方向的 legacy 容差门；没有提供精确消失/非消失证明。", "保持诚实近似诊断边界，不能让整个候选流程无条件可信。"
            if "unit(" in s:
                return legacy, "normal 来自 exact_coefficients 的有理几何，unit 最终显示分量仅服务 legacy 方向阈值；不是从舍入差分重建法向。", "补 exact_coefficients 返回摘要；文档保留该方向阈值是 legacy 选择规则。"
            if "exact_coefficients=True" in s:
                return exact, "显式 exact_coefficients=True，facet 在 unit/显示转换前返回有理法向与分子，用于后续精确高度比。", "证明该常量分支返回 Fraction；不能把容差参数也视为几何 sink。"
            return exact, "extent_only=True 仅检查候选给定 z 位形的范围；有理 model/Gram 路径不依赖 facet 的显示单位法向。" + movement, "补 extent_only 常量模式摘要，保持所声明的给定坐标契约。"
        if f == "tied_labels":
            return legacy, "candidates 的显示高度在既有分辨率带内裁决 tied labels；源码自述 legacy 决策，不是精确高度全序证明。", "先分离 callee proof gap；保留时只说明局部显示带用途。"

    if p.endswith("e5a_g2_oracle.py"):
        if f == "construction":
            if s.startswith("construction("):
                return exact, "对称 FV/EV3 分支转 VF/VE3，distance_squared=True 原样保留；几何来自独立 Fraction 模型，不是原浮点差分。", "补有限对称调用及平方/显示双模式源摘要。"
            return exact, "n/squared 来自有理 Gram 几何；_unit/_distance_display 是最终统一精确舍入边界，无已舍入范数回流。", "证明输入 Fraction 事实并检查被调统一边界，不能 blanket-waive 单位化。"
        if f == "assert_comparison":
            if rule == "closed-method-call":
                return meta, "blocks.values/aliases.get 仅读取已加载夹具的字典与整数索引映射；不执行数值 callable、不构造坐标。", "补输入 Mapping 的有限数据协议摘要，未知对象方法仍拒绝。"
            if "repr" in s:
                return meta, "repr 仅给 actual/expected 诊断记录稳定排序键，结果用于错误报告；不参与几何数值构造。", "证明实际 builtin repr 绑定及纯报告排序位置，不允许任意 callable key。"
            return exact, "对同一独立有理 construction 分别读取最终显示结果及 distance_squared=True 精确平方值，后者核对搜索窗口。", "补 callee 双模式摘要，不豁免整个 assert_comparison。"

    if p.endswith("e5b_frozen_oracle.py"):
        if f == "_surface":
            return meta, "SimpleNamespace 只装载先 Fraction 化的 points 和独立三角剖分 rings；显式记录字段不是动态数值执行。", "补有限记录载体字段摘要，保留每个字段实际值污染。"
        return exact, "surface/_surface 将给定顶点转 Fraction 后独立处理折面，调用方只读拓扑或计算有理平方距离；阻塞来自记录/源摘要。", "修 SimpleNamespace 字段和被调源摘要，不用全函数 waiver。"

    if p.endswith("e5b_margin_oracle.py"):
        if f == "_cover_squared":
            if s.startswith("SimpleNamespace"):
                return meta, "显式 verts/faces 记录仅把给定物体数据交给独立 surface；此站点无算术。", "为显式字段记录补数据摘要，而不是允许反射构造。"
            return exact, "surface 将给定顶点 Fraction 化；后续点面/边边平方距离为有理值，未从显示根回算。", "修记录载体和 surface 的精确字段摘要。"
        if f == "cover_squared" or (f == "check_exact_margin" and s.startswith("cover_squared")):
            return exact, "独立 _cover_squared/surface 分支求 Fraction 平方距离，包装缓存不执行传入 callable。", "补源调用和记录摘要，不登记精确数值 waiver。"
        if s.startswith("production."):
            return harness, "此调用读取被测 production 结果；预期 cover_squared 与中点证书另由独立有理路径给出，不把被测输出冒充 oracle 构造。", "测试驱动与 expected 构造角色分离；生产函数本身仍单独扫描，不能名称豁免。"
        if s.startswith("assert_sqrt_rounding"):
            return exact, "此 helper 用独立有理中点格断言给定 distance 对应 d2 的正确 binary64 舍入，不调用生产 sqrt 生成 expected。", "沿 helper 源证明其比较证书，不将断言回调当构造。"

    if p.endswith("e5b_wall_oracle.py"):
        return meta, "walrus span 只绑定 _interval 的有理交区间；整数共同分母模型随后比较有理端点，未捕获 callable。", "改为显式循环和 span 赋值，或补 NamedExpr 的有限绑定语义；不豁免几何算法。"

    if p.endswith("perf_cover_oracle_reference.py"):
        if f == "witness_points":
            return exact, "冻结参考的对称 FV/EV3 分支保持 exact 标志；Fraction 模型和 Gram 见证在 exact=True 下先于 vector_exact 返回。", "补常量模式与有限对称递归摘要；不整体允许递归。"
        if f == "witness_distance":
            return exact, "明确 exact=True 取有理见证，对分量作精确差后仅最终 norm_exact。", "修 mode-sensitive callee 返回类型，不用 waiver 掩盖。"
        return legacy, "witness_distance 本身最终边界精确，但其显示值用于冻结的 legacy margin 选择规则；未声称精确集合裁决。", "先修几何 callee proof gap，另如实保留 legacy 显示选择边界。"

    if p.endswith("perf_witness_reference.py"):
        return exact, "性能冻结参考在 Fraction 平面/三角形上调用 exact_geom 原语并求有理单元中心；这里与生产共用原语，不能声称是独立几何 oracle。", "补一阶 callee 数据/返回摘要；文档保留性能对照而非独立正确性证据定位。"

    if p.endswith("test_perf_2d_directions.py"):
        if f == "_reference":
            return rewrite, "map(F,vector) 把数值转换函数作为参数传递，即使 F 已知仍属于用户要求改写的数值高阶写法。", "改成显式 tuple(F(component) for component in vector)，保持先精确提升再比较。"
        if rule == "subtract-rounded":
            return legacy, "F(endpoint)-F(origin) 是对实际已舍入工程坐标端点的精确差，定义给定数据的谓词输入；源码明确不是理想平移差，不能宣称恢复理想几何。", "把给定坐标模型边界写明，或由精确 fixture 直接供差；不一般豁免 rounded 差分。"
        return meta, "yield 只枚举确定的 (lo,hi,e,tol,cone_tol) 输入样本；供给的 float 被视为题设数据，不生成 oracle 根。", "补数据 generator 输出摘要或改为显式样本列表；独立检查各样本构造。"

    if p.endswith("test_perf_contact_window.py"):
        if f == "_mutant":
            return mutation, "该独立 helper 复制被测函数源码和模块命名空间，compile/exec 注入函数内部缺陷；用实际路径红灯证明牙，不属于数值 oracle 构造。", "仅可考虑逐站点锁定的内部变异基础设施例外；保持生产/普通 helper 的反射执行默认拒绝。"
        return harness, "M.inflated_membership 是被测调用，轴向/双边厚度预期由此测试独立证书断言；不是 expected 的几何构造来源。", "分离测试驱动与 expected 计算；callee 生产实现仍须原位扫描。"

    if p.endswith("test_perf_covers.py"):
        if f == "_samples":
            return meta, "yield 仅枚举已明确 Fraction 化的给定随机输入点集；不通过产出后追加数据伪造牙。", "补已知数据 generator 摘要或显式列表；保留输入的给定值边界。"
        if s.startswith("_reference_simplex"):
            return rewrite, "此静态调用被 _reference_simplex 内容器取出的 operation callable 与数值 lambda key 阻塞；不能在调用站点绕过内部动态执行。", "先改写 callee 为两个显式几何分支及预计算 (key,index,value) 稳定排序。"
        if "operation" in s or s in {"_segment", "_triangle"}:
            return rewrite, "_segment/_triangle 被装入容器后以 operation(*subset) 执行，属于数值函数间接分派。", "按 size=2/3 写两个直接命名调用循环，保留候选枚举与 tie 次序。"
        return rewrite, "key=lambda 捕获/调用数值 _dot 以决定几何最小候选；不是仅取数据字段的 metadata key。", "先直接计算 (dot_value,stable_index,candidate) 再无 callback 选最小，保持原平局顺序。"

    if p.endswith("test_perf_edge_frame.py"):
        if f in {"_v", "_outcome"} or "map(" in s or s == "scalar_exact":
            if f == "_outcome":
                return rewrite, "func(*args) 为数值函数的通用结果/ValueError 包装器；它是测试基架用途，但仍直接执行未知 callable，不能称纯 metadata。", "改为直接命名的两个结果包装器/显式 try 调用；确实无法改写时再逐站点论证，不先批准。"
            return rewrite, "map 把 F/scalar_exact 数值函数作为参数传递；应保留明确 Fraction 提升或最终显示转换语义但去掉高阶形态。", "改为相同次序的直接生成式 F(x)/scalar_exact(x)，不要放宽通用 map。"
        if rule == "closed-syntax":
            return meta, "yield 仅枚举 edge/direction/tol 输入查询；数值方向源仍应由 _frame 的 Fraction 几何证明。", "补数据 generator 摘要或显式查询列表，并先修 _v 的 map。"
        return rewrite, "该一阶调用的有理 frame/normal 路径依赖 _v 内 map(F,...)；当前阻塞来自下游数值动态转换，不应在 caller 逐个免检。", "先将 _v/_body map 改成直接生成式，再重扫源返回摘要；仍保留实际污染。"

    if p.endswith("test_perf_integer_geometry.py"):
        if "map(" in s or s == "scalar_exact":
            return rewrite, "map 将 scalar_exact/G.vector 作为数值 callable；它们分别是最终给定坐标转换/精确向量提升，也应采用简单直接写法。", "改直接生成式，保留原迭代次序、rounded fixture 模式与 Fraction-before-geometry。"
        if rule == "closed-syntax":
            return meta, "yield 只枚举 exact/rounded 两种明示的给定坐标样本；rounded 模式不声称理想精确运动。", "补数据 generator 摘要或显式列表；各样本内部数值构造另行检查。"
        if s.startswith("_move"):
            return rewrite, "一阶 _move 调用依赖 helper 中的 map(scalar_exact,...)；先精确变换再给出可选 rounded 输入，不应在 caller 免除动态 helper。", "先改 _move 的 map，保持两种 fixture 模式，再重扫。"
        return exact, "box 使用显式 Fraction 零/一生成题设几何夹具；该调用不是求 oracle 的 sqrt 或单位化。", "補静态 Polyhedron/fixture 记录摘要，仍扫描构造器内部。"

    if p.endswith("test_perf_interlock.py"):
        return exact, "嵌套 move 用 t+scale*F(p[k])+delta[k] 生成给定多面体输入，当前 t/scale/delta 组合为 int/Fraction；闭包及 Polyhedron 记录摘要不完备，无动态 callable 执行。", "补源定义闭包参数/显式构造器摘要；不得仅凭函数名或 Fraction 注解覆盖实际值。"

    raise AssertionError((p, f, s, rule))


def scope_data(path, qualname, node_dump):
    text = path.read_text(encoding="utf-8-sig")
    tree = ast.parse(text)
    scopes = {}
    def visit(node, prefix=""):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                q = prefix + child.name
                scopes[q] = child
                visit(child, q + ".")
            else:
                visit(child, prefix)
    visit(tree)
    scope = scopes[qualname]
    source = ast.get_source_segment(text, scope)
    return {
        "reviewed_scope_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
        "reviewed_scope_lines": [scope.lineno, scope.end_lineno],
        "raw_node_still_in_scope": any(ast.dump(n, include_attributes=False) == node_dump for n in ast.walk(scope)),
    }


def main():
    inventory = json.loads((OUT / "raw_scan_round4.json").read_text(encoding="utf-8"))
    chosen = [r for r in inventory if r["rule"] not in EXCLUDED and any(fnmatch.fnmatch(r["path"], pattern) for pattern in PATTERNS)]
    rows = []
    for row in chosen:
        disposition, reason, action = classify(row)
        rows.append({**row, "disposition": disposition, "reason": reason,
                     "recommended_action": action, "waiver_approved": False,
                     **scope_data(ROOT / row["path"], row["function"], row["node"])})
    assert len(rows) == 162
    assert all(r["waiver_approved"] is False for r in rows)
    (OUT / "tests_structural_oracle_review.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    counts = Counter(r["disposition"] for r in rows)
    missing = [r for r in rows if not r["raw_node_still_in_scope"]]
    lines = ["# tests oracle/performance：结构站点逐项只读审核", "",
             "输入为 raw_scan_round4.json；只覆盖 tests/e5*oracle.py、tests/perf_*reference.py、tests/test_perf_*.py，并排除四类数值规则。",
             "", f"共 {len(rows)} 个 raw 站点，{len({(r['path'],r['function']) for r in rows})} 个函数作用域；本审查 **0 条 waiver 批准**。", "",
             "| 分类 | 站点数 |", "|---|---:|"]
    lines += [f"| {key} | {value} |" for key, value in sorted(counts.items())]
    lines += ["", "## 必须保留的边界", "",
              "- 数值 map、lambda 调用 _dot、容器内取出 _segment/_triangle、_outcome(func) 都需简单改写；不能由 caller 例外绕过。",
              "- 有理见证、精确平方距离和最终 construction 边界的源类型缺失属于 proof gap，不是数值 waiver 的理由。",
              "- escape oracle 的 raw-coordinate 噪声/搜索窗口确有近似几何派生量；仅有 bounded legacy diagnostic 角色，不能改写成‘无先舍入’。",
              "- perf_escape 冻结参考的 move 先执行给定坐标平移；e5a_escape 当前 move 先分别转 Fraction。逐项理由保留了这一区别。",
              "- 性能 witness reference 共用生产 exact_geom 原语，仅属性能对照，不是独立 correctness oracle。",
              "- _mutant 的 exec/compile 是注入被测函数内部缺陷的专用基架；不推广为普通动态调用准入。", "",
              "## 可重复核对", "",
              "生成脚本只读输入 JSON 与选中源文件，仅写本审核的 JSON/Markdown；每项记录实际最小函数源码 SHA-256。",
              f"raw AST 节点在当前函数源码中未找到的站点：{len(missing)}。这是快照漂移标志，不会自动批准或删除记录。", ""]
    for row in missing:
        lines.append(f"- {row['path']}:{row['line']} {row['function']} {row['rule']} — `{row['source']}`")
    (OUT / "tests_structural_oracle_review.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"rows":len(rows), "functions":len({(r['path'],r['function']) for r in rows}), "dispositions":dict(counts), "stale_raw_nodes":len(missing), "waivers_approved":0}, ensure_ascii=False))


if __name__ == "__main__":
    main()
