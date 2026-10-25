"""Read-only minimal reproductions of the T2a frozen-admission conflict.

The source strings are scanned in memory under a kernel module path. No
sample module, policy waiver, source rewrite or analysis change is created.
The JSON output is evidence of current checker behavior, not a proof that
every possible compliant implementation is mathematically impossible.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

from check_exact_construction import scan_text


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = Path("D:/eab-evidence/reports/codex/T2a_evidence/static_minimal_repro.json")
SAMPLE_PATH = "src/eab/kernel2d/t2a_static_readonly_probe.py"
SAMPLES = (
    ("control_rational_time_constructor", 0,
     "from fractions import Fraction as F\n"
     "from .motion import QuadraticTime\n"
     "def f():\n    return QuadraticTime(F(0))\n"),
    ("control_typed_motion_endpoint", 0,
     "from .se2 import SE2Motion\n"
     "def f(t: SE2Motion, p):\n    return t.endpoint(p)\n"),
    ("motion_constructor", 2,
     "from .se2 import SE2Motion\n"
     "def f():\n    return SE2Motion()\n"),
    ("algebraic_root_enumeration", 2,
     "from fractions import Fraction as F\n"
     "from .algebraic import roots_interval\n"
     "def f():\n    return roots_interval((F(-1), F(1)))\n"),
    ("algebraic_rational_factory", 2,
     "from .algebraic import RealAlgebraic\n"
     "def f():\n    return RealAlgebraic.from_rational(0)\n"),
    ("typed_algebraic_refinement", 2,
     "from .algebraic import RealAlgebraic\n"
     "def f(t: RealAlgebraic):\n    return t.refine()\n"),
    ("typed_rational_reconstruction", 2,
     "from .algebraic import RealAlgebraic\n"
     "def f(t: RealAlgebraic):\n    return t.as_rational()\n"),
    ("direct_algebraic_constructor", 2,
     "from fractions import Fraction as F\n"
     "from .algebraic import RealAlgebraic\n"
     "def f():\n    return RealAlgebraic((F(-1), F(1)), F(1), F(1))\n"),
)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    policy_path = ROOT / "tools/exact_construction_policy.json"
    policy_before = policy_path.read_bytes()
    policy = json.loads(policy_before)
    samples = []
    for name, expected_count, source in SAMPLES:
        diagnostics = scan_text(source, SAMPLE_PATH, repository_root=ROOT)
        samples.append(dict(
            name=name, source=source, scanned_as=SAMPLE_PATH,
            expected_diagnostic_count=expected_count,
            actual_diagnostic_count=len(diagnostics),
            count_matches=len(diagnostics) == expected_count,
            diagnostics=[dict(path=p, line=line, function=function, rule=rule, source=code)
                         for p, line, function, rule, code in diagnostics]))
    baseline_modules = []
    for relative in ("src/eab/kernel2d/se2.py", "src/eab/kernel2d/algebraic.py"):
        path = ROOT / relative
        rows = [row for row in policy["waivers"] if row["path"] == relative]
        diagnostics = scan_text(path.read_text("utf-8"), relative, repository_root=ROOT)
        baseline_modules.append(dict(
            path=relative, sha256=digest(path), diagnostic_count=len(diagnostics),
            context_pinned_waiver_count=len(rows),
            waiver_rule_counts=dict(sorted(Counter(row["rule"] for row in rows).items()))))
    unchanged = policy_before == policy_path.read_bytes()
    output = dict(
        schema="t2a-static-minimal-repro-1", python=sys.version,
        repository=str(ROOT), source_modules_written=False,
        policy=dict(path="tools/exact_construction_policy.json",
                    sha256=hashlib.sha256(policy_before).hexdigest(), bytes=len(policy_before),
                    waiver_count=len(policy["waivers"]),
                    imports_count=len(policy["imports"]), members_count=len(policy["members"]),
                    admission_entry_total=len(policy["waivers"])+len(policy["imports"])+len(policy["members"]),
                    list_entry_counts={key: len(value) for key, value in policy.items()
                                       if isinstance(value, list)},
                    unchanged_after_scan=unchanged),
        scanner_files=[dict(path=relative, sha256=digest(ROOT / relative)) for relative in (
            "tools/check_exact_construction.py", "tools/exact_construction_subset.py",
            "tools/exact_construction_flow.py")],
        old_modules=baseline_modules, samples=samples,
        expected_observations_reproduced=all(row["count_matches"] for row in samples),
        conclusion=("未发现仅改新增 src、保留既有 SE2Motion/RealAlgebraic 复用协议、"
                    "不新增准入且不扩展静态分析器的合规最小一阶重构路线。"
                    "这是当前静态门与冻结合同的实证冲突，不是所有可能实现均不可能的数学证明。"),
        forbidden_workarounds_not_used=["新增豁免", "重键旧准入到新 AST", "改名或路径避扫",
                                        "将生产数值逻辑移入测试驱动豁免", "修改静态分析器准入域"])
    if not unchanged:
        raise RuntimeError("policy changed during the read-only evidence scan")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(dict(output=str(args.output), policy_unchanged=unchanged,
                          expected_observations_reproduced=output["expected_observations_reproduced"],
                          counts={row["name"]: row["actual_diagnostic_count"] for row in samples}),
                     ensure_ascii=False))
    return 0 if output["expected_observations_reproduced"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
