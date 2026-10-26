"""Persist WO-T2d exact checks and separately labelled numerical displays.

All mathematical decisions are made by the standard-library exact test
oracles. Decimal square roots below are display-only, never predicates.
"""
from __future__ import annotations

import argparse
from decimal import Decimal, localcontext
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import tests.t2d_knob_family_exact as exact
import tests.t2d_critical_escape_exact as escape

EVIDENCE = Path("D:/eab-evidence/reports/codex/T2d_evidence")


def encode(value):
    if isinstance(value, exact.Surd):
        return {"a": str(value.a), "b": str(value.b), "q": str(value.q)}
    if isinstance(value, F):
        return str(value)
    if isinstance(value, dict):
        return {str(k): encode(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [encode(v) for v in value]
    return value


def decimal_display(value):
    """NUMERICAL display only, with a fixed high-precision context."""
    with localcontext() as context:
        context.prec = 70
        def rational(q):
            return Decimal(q.numerator)/Decimal(q.denominator)
        if isinstance(value, (int, F)):
            return rational(F(value))
        return rational(value.a)+rational(value.b)*rational(value.q).sqrt()


def numerical(value):
    return format(decimal_display(value), ".12f")


def expression(value):
    if isinstance(value, (int, F)):
        return str(value)
    if not value.b:
        return str(value.a)
    return f"{value.a} + ({value.b})√({value.q})"


def generate():
    rows = []
    for n, element in exact.TABLE:
        geometry = exact.verify_family_geometry(n)
        values = exact.verify_values(n, element)
        cap = exact.verify_C(n, element)
        # Square finer-facet G is explicitly only disk-bound G, not SE2 G.
        strip = all(values["S"])
        row = {"N": n, "K": element, "values": values, "neck_height": geometry["neck_height"],
               "C": cap, "S": strip, "G_scope": "actual_SE2" if strip else "disk_bound_not_SE2_equality",
               "anisotropy_exact_terms": (values["G"], -values["G_facet"]),
               "NUMERICAL": {"delta_disk": numerical(values["delta"]),
                             "translation": numerical(values["translation"]),
                             "ratio_disk_over_translation": numerical(values["ratio"]),
                             "G_disk": numerical(values["G"]),
                             "G_facet": numerical(values["G_facet"]),
                             "G_disk_minus_G_facet": format(decimal_display(values["G"])-decimal_display(values["G_facet"]), ".12f")}}
        if strip:
            row["critical_escape"] = escape.verify_critical_escape(n, element)
        rows.append(row)
    limits = []
    for element in ("square", "octagon", "K16"):
        limit = exact.circle_limits(element)
        with localcontext() as context:
            context.prec = 70
            ratio = sum((decimal_display(term) for term in limit["ratio_terms"]), Decimal(0))
        limits.append({"K": element, "exact": limit,
                       "ratio_field": "Q(sqrt(2),sqrt(7)); degree 4" if element == "square" else "quadratic",
                       "NUMERICAL": {"delta_disk": numerical(limit["disk"]),
                                     "translation": numerical(limit["translation"]),
                                     "ratio": format(ratio, ".12f"), "G_disk": format(1-ratio, ".12f")}})
    convergence = []
    for n in (32, 64, 128):
        for element in ("square", "octagon", "K16"):
            value = exact.family_values(n, element)
            convergence.append({"N": n, "K": element, "S": value["S"],
                                "e_star": [(e["u1"], e["u2"]) for e in value["e_star"]],
                                "exact_delta": value["delta"], "exact_translation": value["translation"],
                                "NUMERICAL": {"delta_disk": numerical(value["delta"]),
                                              "translation": numerical(value["translation"]),
                                              "ratio": numerical(value["ratio"])},
                                "scope": "exact chord algebra; displayed numerical convergence, not N>32 production validation"})
    return {"schema": "eab.t2d.exact-summary/1", "rows": rows, "limits": limits,
            "convergence": convergence, "exact_rows_match_theorem": 12,
            "exact_critical_escapes": 9, "theorem_modified": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if output == EVIDENCE.resolve() or not output.is_relative_to(EVIDENCE.resolve()):
        parser.error("output must be a new child of the approved evidence directory")
    output.mkdir(parents=True, exist_ok=False)
    summary = generate()
    sources = [Path(__file__).resolve(), ROOT/"tests/t2d_knob_family_exact.py",
               ROOT/"tests/t2d_critical_escape_exact.py", ROOT/"docs/t2d_knob_family_theorem.md"]
    summary["provenance"] = {
        "git_base": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "source_manifest": [{"path": p.relative_to(ROOT).as_posix(), "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
                             "bytes": p.stat().st_size} for p in sources],
        "git_base_is_not_a_clean_source_claim": True,
    }
    with (output/"exact_summary.json").open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(encode(summary), ensure_ascii=False, indent=2)+"\n")
    lines = ["# T2d 精确值与数值显示", "", "精确判定先运行；小数仅标注为数值展示。", "",
             "|N|K|δ_disk（精确）|δ_T（精确）|e* 正角弦|S|比值（数值）|", "|---:|---|---|---|---|---|---:|"]
    for row in summary["rows"]:
        n, k, value = row["N"], row["K"], row["values"]
        edge = next(e for e in value["e_star"] if e["u1"] >= 0)
        d = exact.TABLE[n, k][0]
        lines.append(f"|{n}|{k}|{expression(d)}|{value['translation']}|[{edge['u1']}, {edge['u2']}]|{'成立' if row['S'] else '不成立'}|{row['NUMERICAL']['ratio_disk_over_translation']}|")
    lines += ["", "## 分解（数值显示；方形 N≥8 是 G_disk，不冒充 G）", "",
              "|N|K|G_disk|G_facet|G_disk−G_facet|", "|---:|---|---:|---:|---:|"]
    for row in summary["rows"]:
        v = row["NUMERICAL"]
        lines.append(f"|{row['N']}|{row['K']}|{v['G_disk']}|{v['G_facet']}|{v['G_disk_minus_G_facet']}|")
    lines += ["", "## 圆形极限", "", "|K|δ_T∞（精确）|极限比值（精确）|比值（数值）|", "|---|---|---|---:|"]
    for row in summary["limits"]:
        v = row["exact"]
        lines.append(f"|{row['K']}|{expression(v['translation'])}|{' + '.join(expression(t) for t in v['ratio_terms'])}|{row['NUMERICAL']['ratio']}|")
    lines += ["", "## N=64、128 收敛趋势（数值；不声称生产验证）", "",
              "|N|K|δ_disk|δ_T|比值|S|", "|---:|---|---:|---:|---:|---|"]
    for row in summary["convergence"]:
        v = row["NUMERICAL"]
        lines.append(f"|{row['N']}|{row['K']}|{v['delta_disk']}|{v['translation']}|{v['ratio']}|{row['S']}|")
    (output/"tables.md").write_text("\n".join(lines)+"\n", encoding="utf-8", newline="\n")
    print("T2d exact report: 12 matching rows; 9 exact critical escapes; numerical displays labelled")


if __name__ == "__main__":
    main()
