"""Read-only review of newly visible power-sink paths outside three agent files."""
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "reports/codex/R12FIXb_evidence"
EXCLUDED = {"tests/test_invariance_geom.py", "tests/test_invariance_interlock.py", "tests/test_margin.py"}


def review(row):
    path, function, source = row["path"], row["function"], row["source"]
    if path == "tests/test_g2_bdda3d.py":
        if function == "_sub3":
            detail = "该站点直接对 float 坐标/已算见证作分量差，确实可能先舍入；结果进入 _seg_seg_dist 的 dot 后 **0.5，也用于窗口点面距离。"
        elif function == "_dot3":
            detail = "该站点是未 Fraction 提升的分量乘积/累加，调用者将平方长度交给 **0.5；确实是先浮点舍入再构造根，不能以 _dot3 名字豁免。"
        elif function == "_seg_seg_dist":
            if "p1[" in source or "p2[" in source or "d1[" in source or "d2[" in source:
                detail = "该站点先以浮点参数构造夹紧见证坐标，随后两见证作差、dot 并 **0.5；见证构造的舍入历史真实存在。"
            elif "/" in source:
                detail = "该站点是浮点 Gram/夹紧参数的除法，参数继续构造见证并最终 **0.5；并非 Fraction 精确参数。"
            else:
                detail = "该站点是浮点 Gram 行列式/参数分子算术，继续驱动近点见证并最终 **0.5；根之前的舍入真实存在。"
        else:
            raise AssertionError((path, function))
        return {
            "disposition": "legacy_approximate_oracle",
            "reason": detail + "现有使用范围是固定轴对齐 cb2 夹具的宽分离窗口佐证：non_face≈1（abs=1e-12），G2_WINDOW≤1e-3*non_face。它与生产几何原语独立，但‘独立’不等于精确数值 oracle，不能写成无先舍入。",
            "recommended_action": "若必须保持原格子，可将其明确列为旧近似窗口佐证的遗留，且不声称满足精确构造要求；更稳妥是独立有理参数/平方距离比较，保留现有内部枚举变异牙。不得批准泛型 _sub3/_dot3 数值豁免。",
        }
    if path == "tests/test_kernel3d_geom.py" and function == "_g6_rot":
        return {
            "disposition": "given_input_fixture_boundary",
            "reason": "高斯 float 四元数先 c*c 与 sum，再 **0.5 和除法单位化，真实先舍入。此 helper 只生成测试给定姿态矩阵；_placed_exact 会精确提升已存储矩阵而不是恢复理想旋转，独立 Fraction hull 证书检查最终给定坐标。不能称随机矩阵精确正交或开方无舍入。",
            "recommended_action": "若保留此生成器，只能说明近似随机姿态输入角色并保留最终坐标的独立证书；不要把给定输入例外推广到生产 normal/norm 构造。",
        }
    if path == "tests/test_limit_fuzz.py" and function == "_genuinely_unresolvable":
        return {
            "disposition": "bounded_legacy_diagnostic",
            "reason": "Fn/Mn/R 由原始给定浮点荷载/接触点作平方和后 **0.5，确实先舍入后开方；ct.point 不是已证明的精确长度。所得幅度仅定义±1e-12随机荷载扰动诊断，pert 的实际binary64分量随后交独立Fraction LP状态/最优值层，不是理想精确扰动或精确几何范数。",
            "recommended_action": "如保留，报告为旧近似扰动幅度诊断并说明精确 LP 对最终给定 pert 成立；不得把这5站点称精确证明误报或批准普通范数先舍入。",
        }
    raise AssertionError((path, function))


rows = json.loads((OUT / "round6_unreviewed_sites.json").read_text(encoding="utf-8"))
reviewed = []
for row in rows:
    if row["path"] in EXCLUDED:
        continue
    text = (ROOT / row["path"]).read_text(encoding="utf-8-sig")
    scope = next(n for n in ast.parse(text).body if isinstance(n, ast.FunctionDef) and n.name == row["function"])
    source = ast.get_source_segment(text, scope)
    reviewed.append({**row, **review(row), "waiver_approved": False,
                     "reviewed_scope_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
                     "reviewed_scope_lines": [scope.lineno, scope.end_lineno],
                     "raw_node_still_in_scope": any(ast.dump(n, include_attributes=False) == row["node"] for n in ast.walk(scope))})
assert len(reviewed) == 41
assert all(r["raw_node_still_in_scope"] for r in reviewed)
(OUT / "tests_round6_external_review.json").write_text(json.dumps(reviewed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"raw_sites":len(reviewed), "dispositions":dict(Counter(r["disposition"] for r in reviewed)), "waiver_approved":0}, ensure_ascii=False))
