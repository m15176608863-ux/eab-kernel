"""Combine the supplemental test review, retaining zero automatic waivers."""
import ast
from collections import Counter
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]
raw = json.loads((BASE / "round5_unreviewed_sites.json").read_text(encoding="utf-8"))
extra = json.loads((BASE / "tests_round5_supplement_review.json").read_text(encoding="utf-8"))
if isinstance(extra, dict):
    extra = extra["sites"]
reasons = {
    ("tests/test_invariance_geom.py", "_pair_generic"): "rng.uniform 点在加固定2.6/0.3/-0.2后定义实际给定的binary64一般位置夹具，再对该实际点集求hull。存在float派生输入，不能声称是未舍入理想坐标或精确expected；独立oracle从最终坐标求真值。",
    ("tests/test_invariance_geom.py", "_pair_ve3_wedge"): "c/s固定角度旋转底面采样坐标并将顶点提高VE3_GAP+1，convex_hull接收实际给定binary64点集。输入姿态不是正确舍入法向/距离oracle；必须保持采样输入边界明示。",
    ("tests/test_invariance_geom.py", "_pair_ridge_needle"): "固定三角函数角度和h+0.05/h+1.05生成实际roof/needle测试点，再求hull；float坐标舍入真实存在，后续距离/标签真值不能冒充未舍入理想几何。",
    ("tests/test_invariance_interlock.py", "_tia"): "s*delta0和_tia_geom参数表用于给定尺度的敏感性试验；sensitivity_at是被测执行，scaled offset不是独立精确预期。仍须证明有限kwargs或改显式字段，不能因被测函数已知就开放任意unpack。",
    ("tests/test_invariance_interlock.py", "_escape"): "o先作为给定姿态的偏移；d=Dual.seed(1,...)，od=d*c把这些给定分量播种成参数化路径，再执行被测冻结cover。该站点不是把独立预期距离显示值返送root；后续hypot归一化导数仍属近似诊断，不能写为精确逃逸高度oracle。",
}
mine = []
for row in raw:
    key = row["path"], row["function"]
    if key not in reasons:
        continue
    text = (ROOT / row["path"]).read_text(encoding="utf-8-sig")
    nodes = {ast.dump(n, include_attributes=False) for n in ast.walk(ast.parse(text))}
    assert row["node"] in nodes, key
    mine.append({**row, "disposition": "given_input_fixture" if key[1] != "_escape" else "test_execution_with_approx_diagnostic",
                 "reason": "站点 `" + row["source"].replace("\n", " ") + "`：" + reasons[key],
                 "recommended_action": "明示给定输入/近似诊断边界并与最终node/context匹配；不批准精确构造例外。",
                 "waiver_approved": False, "raw_node_still_in_current_file": True})
combined = extra + mine
expected = {tuple(r[k] for k in ("path", "function", "rule", "node")) for r in raw if r["path"].startswith("tests/")}
actual = {tuple(r[k] for k in ("path", "function", "rule", "node")) for r in combined}
assert expected == actual, (len(expected), len(actual), expected-actual)
assert all(not r["waiver_approved"] for r in combined)
payload = {"input": "round5_unreviewed_sites.json", "review_kind": "test supplemental review; NOT waiver approval",
           "reviewed_sites": len(combined), "category_counts": dict(Counter(r["disposition"] for r in combined)),
           "limits": ["按round5快照审核，随后fixture重命名与数值helper直接化需最后匹配node/context。",
                      "动态数值、给定采样输入、近似诊断与纯测试架构不得混为无先舍入保证。"], "sites": combined}
(BASE / "tests_round5_complete_review.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({k: v for k, v in payload.items() if k != "sites"}, ensure_ascii=False, indent=2))
