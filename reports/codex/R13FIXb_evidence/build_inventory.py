"""Merge the manually reviewed 138-item ledger; node existence is not coverage."""
import ast
from collections import Counter
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
OLD = ROOT / "reports/codex/R13FIX_evidence/construction/public_api_inventory.json"


def write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    baseline = json.loads(OLD.read_text(encoding="utf-8"))
    required = {r["api"]: r for r in baseline if r["public"] and r["kind"] == "callable"
                and r["status"].startswith("未确认")}
    assert len(required) == 138
    maps = {}
    for group in ("kernel", "dual_margin", "readers_oracles"):
        for row in json.loads((HERE / group / "coverage.json").read_text(encoding="utf-8")):
            assert row["api"] not in maps
            maps[row["api"]] = {**row, "review_group": group}
    for api, old in required.items():
        if old["path"] not in ("src/eab/kernel2d/geom.py", "src/eab/kernel3d/geom3.py"):
            continue
        test = "test_remaining_geometry_reports_and_exact_vectors_have_three_scale_references"
        proof = "独立3-4-12解析盒/矩形：每个尺度/噪声/反射坐标/精确向量/Newell分量/交点逐值；无生产几何参考复用。"
        if api.endswith("Polyhedron.interior_point"):
            test = "test_interior_point_declared_roundoff_bound_on_analytic_box"
            proof = "独立盒底三角形心加13s内退，逐分量误差界16u*13s，并核每分量严格在盒内；候选点不是唯一构造。"
        maps[api] = dict(api=api, status="differential", tests=["tests/test_r13fixb_domain.py::"+test],
                         scales=["2^-400", "1", "2^396"], proof=proof,
                         limits="有限输入族门，不把三个尺度样本当全输入证明；一般凹体候选搜索不作全覆盖声明。" if api.endswith("interior_point") else "输入有效性与退化语义沿用原API。",
                         review_group="root", path=old["path"])
    missing = set(required) - set(maps)
    assert not missing, sorted(missing)
    normal = {"covered": "differential", "differential_verified": "differential", "differential": "differential",
              "non_constructing": "nonconstructive", "nonconstructive": "nonconstructive",
              "no_construction": "nonconstructive", "proved_nonconstructive": "nonconstructive", "nonconstruction_proved": "nonconstructive",
              "gap": "gap", "platform_differential_only": "limited", "previously_covered": "prior_coverage"}
    for api, row in maps.items():
        assert row["status"] in normal, (api, row["status"])
        row["status"] = normal[row["status"]]
        row["in_original_138"] = api in required
        for node in row["tests"]:
            path, name = node.split("::", 1)
            name = name.split("[")[0]
            tree = ast.parse((ROOT / path).read_text(encoding="utf-8-sig"))
            assert any(isinstance(n, ast.FunctionDef) and n.name == name for n in ast.walk(tree)), node
    rows = [maps[api] for api in sorted(required)]
    # Cross review may explicitly downgrade overbroad claims, never upgrade by grep.
    audit = HERE / "inventory_cross_review_overrides.json"
    if audit.exists():
        for api, changes in json.loads(audit.read_text(encoding="utf-8")).items():
            assert api in maps
            maps[api].update(changes)
    counts = Counter(row["status"] for row in rows)
    summary = dict(original_remaining=138, dispositions=dict(counts),
                   final_gaps=sum(row["status"] in ("gap", "limited") for row in rows),
                   gap_apis=[row["api"] for row in rows if row["status"] in ("gap", "limited")],
                   additional_reviewed=len(maps)-138,
                   additional_limits=[r["api"] for r in maps.values() if not r["in_original_138"] and r["status"] in ("gap", "limited")],
                   whole_public_surface_fully_proved=False,
                   note="逐值门覆盖列明输入族，源码证明/独立G6不由nodeid存在推定。原249字段与未在此次表内的旧API没有被默认为新完成。")
    write(HERE / "remaining_138.json", rows)
    write(HERE / "additional_review.json", [v for k, v in sorted(maps.items()) if k not in required])
    write(HERE / "coverage_summary.json", summary)
    write(HERE / "public_api_inventory.json", [{**r, "r13fixb": maps[r["api"]]} if r["api"] in maps else r for r in baseline])
    lines = ["# R13FIXb 公开构造 API：138 项逐项处置", "",
             "这是 R13FIX 普查的增量收尾，不把有限测试族当全输入域证明。旧915符号/333 callable/249字段的原表保存在 R13FIX evidence；本轮机器表保留全部原行。", "",
             "## 当前计数", "", "```json", json.dumps(summary, ensure_ascii=False, indent=2), "```", "",
             "支持域与推导：[数值合同](exact_predicates_plan.md#r13fixb-numeric-domain)。", "",
             "- [138 项机读表](../reports/codex/R13FIXb_evidence/remaining_138.json)",
             "- [含原915行的完整机器表](../reports/codex/R13FIXb_evidence/public_api_inventory.json)",
             "- [额外API审查](../reports/codex/R13FIXb_evidence/additional_review.json)",
             "- [报告及变异/全套证据](../reports/codex/R13FIXb_report.md)", "",
             "`differential`=列明三档输入族的独立逐值门；`nonconstructive`=逐项源码证明没有派生构造量（数字ID/布尔/输入搬运不算新几何构造）；`gap`/`limited`=未闭合。", "",
             "## 138 项台账", "", "| API | 状态 | 三档/门 | 依据与限制 |", "|---|---|---|---|"]
    def fmt(value):
        return "; ".join(map(str, value)) if isinstance(value, list) else str(value)
    for row in rows:
        tests = "<br>".join("`"+t+"`" for t in row["tests"]) or "源码证明"
        lines.append("| `"+row["api"]+"` | "+row["status"]+" | "+fmt(row["scales"])+"<br>"+tests+" | "+fmt(row["proof"]).replace("|", "&#124;")+"<br>"+fmt(row["limits"]).replace("|", "&#124;")+" |")
    lines += ["", "## 不可越过的边界", "",
              "1. 一般非整数幂/通用libm界、一般凹体候选与所有复杂活跃集不能由三个尺度样本证明。", 
              "2. `face_noise` 已换无指数限制尾数周长模型；原超长边遗留有回归与独立误差界，不再作为缺口。",
              "3. 混合int/float raw向量域内相消与域外范围均有门；任意第三方标量协议不纳入builtin输入合同。",
              "4. 静态0违例只与逐站点人工排除账一起解释，不是此表完成的替代。", ""]
    path = ROOT / "docs/r13fix_construction_inventory.md"
    with path.open("w", encoding="utf-8", newline="") as f:
        f.write("\n".join(lines))
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
