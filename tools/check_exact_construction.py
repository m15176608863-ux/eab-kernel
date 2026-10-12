"""AST gate for the exact-to-binary64 boundary (src and test oracles).

Not a proof of arbitrary Python dataflow: deliberately fail closed on direct
float conversions, with narrow reviewed input/filter exceptions. Additionally
reject premature sqrt/norm/unit and subtract-after-rounding idioms, including
local aliases and assigned rounded vectors. Exceptions match a named function
and rule; none is a whole-file exemption. Run from any working directory.
"""
from __future__ import annotations

import ast
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

# (relative path, qualified function, rule) -> individual auditable rationale.
EXCEPTIONS = {
    ("src/eab/adapters/bdda2d.py", "load_window", "direct-float"):
        "Legacy detparams CSV string parsing at the explicit L5 input boundary; not a derived exact construction.",
    ("src/eab/construction.py", "normalized_difference_rational", "subtract-rounded"):
        "Untrusted initial candidate only; exact algebraic comparisons bracket it and certify the final midpoint or perform full bit search.",
    ("src/eab/margin.py", "_resolve", "subtract-rounded"):
        "Diagnostic residual comparing two already-constructed witness displays; exact feature squared distance separately governs completeness.",
    ("tests/test_r8fix_frozen.py", "test_contact_margin_postround_subtraction_mutant_is_caught.premature_round", "subtract-rounded"):
        "Deliberately faulty internal compound-construction mutation; independent midpoint assertion must reject it.",
    ("src/eab/oracle_construction.py", "_candidate_positive", "direct-float"):
        "Untrusted candidate only; independent Fraction midpoint certificate precedes acceptance, else exact bit bisection.",
    ("tests/test_limit_exact_selfcheck.py", "test_exact_witness_is_preserved_by_copy_not_by_float_arithmetic", "direct-float"):
        "Tests builtin float's intentional certificate-stripping protocol; not an oracle numeric construction.",
    ("src/eab/construction.py", "scalar_rational", "direct-float"):
        "Single checked Fraction-to-binary64 boundary; exact midpoint gates certify RN-even.",
    ("src/eab/construction.py", "sqrt_rational", "direct-float"):
        "The integer significand is <= 2**53, so its cast is exact; ldexp is the final construction.",
    ("src/eab/predicates.py", "_float_value", "direct-float"):
        "Outward error-bounded filter candidate only; not a geometric output or exact decision.",
    ("src/eab/kernel3d/exact_geom.py", "_iv", "direct-float"):
        "Nextafter-enclosed interval candidate; inconclusive filters fall back to rational arithmetic.",
    ("src/eab/limit.py", "_rational", "direct-float"):
        "Read the already-rounded float subclass to check its immutable exact witness, not construct a quantity.",
    ("tests/test_r6fix_construction.py", "test_g6f06_gap_magnitude_gate_has_teeth", "direct-float"):
        "Intentional broken internal sqrt mutation; the target nonzero-gap assertion must reject it.",
    ("tests/test_r6fix_construction.py", "test_g6f06_gap_magnitude_gate_has_teeth", "rounded-root"):
        "Intentional broken internal sqrt mutation, not an oracle.",
    ("tests/test_r6fix_g2_oracle.py", "test_g2_oracle_early_square_rounding_mutation_is_caught", "direct-float"):
        "Intentional old oracle mutation; the independent range assertion rejects it.",
    ("tests/test_r6fix_g2_oracle.py", "test_g2_oracle_early_square_rounding_mutation_is_caught", "rounded-root"):
        "Intentional old oracle mutation, never an expected-value constructor.",
    ("tests/test_r9fix_construction.py", "_premature_sqrt_mutant", "direct-float"):
        "G6I-04 defect injected inside the real distance function; midpoint certificate must fail.",
    ("tests/test_r9fix_construction.py", "_premature_sqrt_mutant", "rounded-root"):
        "G6I-04 deliberately faulty sqrt factory, used only by internal mutation tests.",
    ("src/eab/contact_record.py", "_decode", "direct-float"):
        "Decode serialized scalar tags; this is external input parsing, not exact derived geometry.",
    ("src/eab/dual.py", "Dual.const", "direct-float"):
        "Public Number-to-primal input coercion (int/float), not a derived exact quantity.",
    ("src/eab/dual.py", "Dual.seed", "direct-float"):
        "Public Number-to-primal input coercion before derivative seeding.",
    ("src/eab/dual.py", "Dual._pair", "direct-float"):
        "Public Number input coercion; exact derivative output uses scalar_rational.",
    ("src/eab/dual.py", "Dual.__pow__", "direct-float"):
        "Coerce public real exponent parameter, preserving documented Number API.",
    ("src/eab/dual.py", "Dual.__lt__", "direct-float"):
        "Primal-only comparator on public Number operand, not a constructed output.",
    ("src/eab/dual.py", "Dual.__le__", "direct-float"):
        "Primal-only comparator on public Number operand, not a constructed output.",
    ("src/eab/dual.py", "Dual.__gt__", "direct-float"):
        "Primal-only comparator on public Number operand, not a constructed output.",
    ("src/eab/dual.py", "Dual.__ge__", "direct-float"):
        "Primal-only comparator on public Number operand, not a constructed output.",
    ("src/eab/dual.py", "val", "direct-float"):
        "Explicit public primal extraction required by the Dual contract.",
    ("src/eab/dual.py", "is_exact_zero", "direct-float"):
        "Number input comparator; Dual inputs inspect every stored channel separately.",
    ("src/eab/readers/bdda3d.py", "record_from_entrance", "direct-float"):
        "Parse finite legacy export fields; no rational geometric intermediate.",
    ("src/eab/readers/bdda_df.py", "read_contacts_csv", "direct-float"):
        "CSV string input parsing under the legacy format contract.",
    ("src/eab/readers/bdda_df.py", "read_df22_csv", "direct-float"):
        "CSV string input parsing under the legacy format contract.",
    ("src/eab/readers/bdda_df.py", "read_verts_csv", "direct-float"):
        "CSV vertex input parsing, before any exact geometric operations.",
    ("src/eab/readers/bdda_df.py", "load_records", "direct-float"):
        "Legacy dump scalar decoding, not derived rational constructions.",
    ("src/eab/readers/bdda_geom.py", "load_step_geometries", "direct-float"):
        "CSV coordinate string parsing, before the documented input normalization.",
    ("src/eab/readers/tf_probe.py", "read_pair_stage", "direct-float"):
        "Probe time-string parsing, not exact intermediate construction.",
    ("src/eab/readers/tf_probe.py", "load_records", "direct-float"):
        "Probe export string parsing; stored values are the supplied binary64 data.",
    ("tests/test_lp.py", "test_weak_and_strong_duality", "subtract-rounded"):
        "The cast integer grid defines LP input floats; subtraction is a residual on that given model, not a rational constructor.",
    ("src/eab/limit.py", "_norm", "implicit-root"):
        "Only the explicit nonfinite-report branch uses hypot; every finite vector uses the checked exact root.",
    ("src/eab/kernel3d/geom3.py", "_ray_directions", "implicit-root"):
        "Caller-independent bounded binary64 golden-angle seed generation, not a constructor from exact geometric intermediates.",
}


def _name(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return _name(node.value) + "." + node.attr
    return ""


def scan_text(text, path="<injected>"):
    tree = ast.parse(text, filename=path)
    aliases = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for item in node.names:
                aliases[item.asname or item.name] = item.name
        elif isinstance(node, ast.ImportFrom):
            for item in node.names:
                aliases[item.asname or item.name] = (node.module or "") + "." + item.name

    def canonical(node):
        name = _name(node)
        seen = set()
        while name not in seen:
            seen.add(name)
            first, _, tail = name.partition(".")
            replacement = aliases.get(first, first) + ("." + tail if tail else "")
            if name == replacement:
                break
            name = replacement
        return name

    def is_float(node):
        return canonical(node) in ("float", "builtins.float")

    rounded = set()
    converters = {"_float_vector", "_display_fraction", "_construction_float",
                  "scalar_rational", "vector_rational", "scalar_exact", "vector_exact",
                  "ratio_rational", "ratio_exact", "sqrt_rational", "sqrt_exact",
                  "norm_rational", "norm_exact", "unit_rational", "unit_exact",
                  "normalized_difference_rational"}

    def lossy(node):
        if isinstance(node, ast.Name):
            return node.id in rounded
        if isinstance(node, ast.Call):
            name = canonical(node.func).split(".")[-1]
            if is_float(node.func) or name in converters:
                return True
            if name == "map" and node.args:
                # Fraction explicitly establishes exact arithmetic on the
                # supplied model values, as with direct Fraction(value).
                if canonical(node.args[0]).split(".")[-1] == "Fraction":
                    return False
                return (is_float(node.args[0]) or canonical(node.args[0]).split(".")[-1] in converters
                        or any(lossy(arg) for arg in node.args[1:]))
            # Propagate local container/reduction values, not arbitrary API
            # calls. Fraction(...) explicitly declares supplied input data.
            if name not in {"tuple", "list", "sum", "min", "max", "abs"}:
                return False
        return any(lossy(child) for child in ast.iter_child_nodes(node))

    issues = []

    class Check(ast.NodeVisitor):
        def __init__(self):
            self.stack = []

        def issue(self, node, rule):
            function = ".".join(self.stack) or "<module>"
            if (path, function, rule) not in EXCEPTIONS:
                issues.append((path, node.lineno, function, rule, ast.get_source_segment(text, node)))

        def visit_FunctionDef(self, node):
            old = set(rounded)
            old_aliases = dict(aliases)
            self.stack.append(node.name)
            self.generic_visit(node)
            self.stack.pop()
            rounded.clear()
            rounded.update(old)
            aliases.clear()
            aliases.update(old_aliases)

        visit_AsyncFunctionDef = visit_FunctionDef

        def visit_ClassDef(self, node):
            self.stack.append(node.name)
            self.generic_visit(node)
            self.stack.pop()

        def visit_Assign(self, node):
            self.generic_visit(node)
            self.bind(node.targets, node.value)

        def bind(self, targets, value):
            for target in targets:
                names = {p.id for p in ast.walk(target) if isinstance(p, ast.Name)}
                if lossy(value):
                    rounded.update(names)
                else:
                    rounded.difference_update(names)
                if isinstance(target, ast.Name) and isinstance(value, (ast.Name, ast.Attribute)):
                    aliases[target.id] = canonical(value)

        def visit_AnnAssign(self, node):
            self.generic_visit(node)
            if node.value is not None:
                self.bind([node.target], node.value)

        def visit_NamedExpr(self, node):
            self.generic_visit(node)
            self.bind([node.target], node.value)

        def visit_BinOp(self, node):
            if isinstance(node.op, ast.Sub) and lossy(node.left) and lossy(node.right):
                self.issue(node, "subtract-rounded")
            if (isinstance(node.op, ast.Pow) and isinstance(node.right, ast.Constant)
                    and node.right.value == 0.5 and not path.startswith("tests/")):
                self.issue(node, "implicit-root")
            self.generic_visit(node)

        def visit_Call(self, node):
            name = canonical(node.func).split(".")[-1]
            if canonical(node.func) in {"math.sqrt", "math.hypot"} and not path.startswith("tests/"):
                self.issue(node, "implicit-root")
            sentinel = (len(node.args) == 1 and isinstance(node.args[0], ast.Constant)
                        and isinstance(node.args[0].value, str)
                        and node.args[0].value.lower().lstrip("+-") in {"inf", "infinity", "nan"})
            if is_float(node.func) and not sentinel:
                self.issue(node, "direct-float")
            if canonical(node.func) == "map" and node.args and is_float(node.args[0]):
                self.issue(node, "direct-float")
            if name in {"sqrt", "sqrt_rational", "sqrt_exact", "hypot", "norm", "unit", "norm_rational", "unit_rational", "norm_exact", "unit_exact"}:
                if any(lossy(arg) for arg in node.args):
                    self.issue(node, "rounded-root" if name in {"sqrt", "sqrt_rational", "sqrt_exact"} else "rounded-vector")
            self.generic_visit(node)

    Check().visit(tree)
    return issues


def scan_repository(root=ROOT):
    return [issue for folder in ("src", "tests")
            for path in sorted((root / folder).rglob("*.py"))
            for issue in scan_text(path.read_text(encoding="utf-8-sig"), path.relative_to(root).as_posix())]


if __name__ == "__main__":
    found = scan_repository()
    for path, line, function, rule, code in found:
        print(f"{path}:{line} {function}: {rule}: {code}")
    print(f"exact construction AST gate: {len(found)} violation(s)")
    sys.exit(bool(found))
