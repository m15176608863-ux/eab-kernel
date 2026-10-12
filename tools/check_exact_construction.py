"""AST gate for the exact-to-binary64 boundary (src and test oracles).

Not a proof of arbitrary Python dataflow: deliberately fail closed on direct
float conversions, with narrow reviewed input/filter exceptions. Additionally
reject premature sqrt/norm/unit and subtract-after-rounding idioms, including
keywords/unpacking, local aliases, containers, loops and augmented assignment.
Fraction preserves known rounding provenance; it cannot recover discarded bits.
Unknown interprocedural/reflective Python is not a proved dataflow domain.
Exceptions match a named function
and rule; none is a whole-file exemption. Run from any working directory.
"""
from __future__ import annotations

import ast
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

# (relative path, qualified function, rule) -> individual auditable rationale.
EXCEPTIONS = {
    ("src/eab/limit.py", "_tangents", "subtract-rounded"):
        "The documented model defines t2 from the returned binary64 t1; Fraction completes that model cross product exactly before the final scalar construction, not a norm of prematurely rounded components.",
    ("tests/e5a_escape_oracle.py", "_candidates", "subtract-rounded"):
        "Cache-reuse window between constructed candidate displays; the independent exact facet-extent oracle is evaluated at the chosen supplied candidate coordinates.",
    ("tests/perf_escape_oracle_reference.py", "_candidates", "subtract-rounded"):
        "Frozen performance reference cache-reuse window between candidate displays, not an exact derived geometry constructor or branch oracle.",
    ("tests/test_perf_2d_directions.py", "direction_cases", "subtract-rounded"):
        "Generates supplied predicate inputs from the actual rounded engineering-coordinate endpoints, as required by the test's documented data model.",
    ("tests/test_filtered_predicates.py", "test_orient3d_filter_has_a_real_fast_path", "direct-float"):
        "Exercises float and Fraction supplied input types using only exactly representable 0/1 coordinates; no derived construction or expected-value conversion.",
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
        while True:
            first, _, tail = name.partition(".")
            # a=a.x changes the full string forever; the alias *head* is the
            # finite graph node, so detect cycles before expanding it again.
            if first in seen:
                break
            seen.add(first)
            replacement = aliases.get(first, first) + ("." + tail if tail else "")
            if name == replacement:
                break
            name = replacement
        return name

    def is_float(node):
        return canonical(node) in ("float", "builtins.float")

    rounded = set()
    bindings = {}
    converters = {"_float_vector", "_display_fraction", "_construction_float",
                  "scalar_rational", "vector_rational", "scalar_exact", "vector_exact",
                  "ratio_rational", "ratio_exact", "sqrt_rational", "sqrt_exact",
                  "norm_rational", "norm_exact", "unit_rational", "unit_exact",
                  "normalized_difference_rational"}

    def arguments(node):
        """Every Python call argument, including *args and **kwargs."""
        return [*node.args, *(item.value for item in node.keywords)]

    def callable_names(node, seen=frozenset()):
        """Resolve statically visible callable aliases, not arbitrary returns."""
        name = canonical(node)
        if name.endswith(".__call__"):
            name = name[:-len(".__call__")]
        result = {name} if name else set()
        bound_name = _name(node)
        if bound_name in bindings and bound_name not in seen:
            result |= callable_names(bindings[bound_name], seen | {bound_name})
        elif isinstance(node, ast.Subscript):
            result |= callable_names(node.value, seen)
        elif isinstance(node, (ast.Tuple, ast.List, ast.Set)):
            for item in node.elts:
                result |= callable_names(item, seen)
        elif isinstance(node, ast.Dict):
            for item in node.values:
                result |= callable_names(item, seen)
        elif isinstance(node, ast.IfExp):
            result |= callable_names(node.body, seen) | callable_names(node.orelse, seen)
        elif isinstance(node, ast.NamedExpr):
            result |= callable_names(node.value, seen)
        elif isinstance(node, ast.Lambda) and isinstance(node.body, ast.Call):
            result |= callable_names(node.body.func, seen)
        elif isinstance(node, ast.Call) and canonical(node.func) in {"functools.partial", "partial"}:
            for item in node.args[:1]:
                result |= callable_names(item, seen)
        return result

    def short_names(node):
        return {name.split(".")[-1] for name in callable_names(node)}

    def target_names(node):
        if isinstance(node, (ast.Tuple, ast.List)):
            return set().union(*(target_names(item) for item in node.elts))
        if isinstance(node, ast.Starred):
            return target_names(node.value)
        if isinstance(node, (ast.Attribute, ast.Subscript)):
            return target_names(node.value)
        if isinstance(node, ast.Name):
            return {node.id, canonical(node).split(".")[0]}
        return set()

    def lossy(node):
        if isinstance(node, ast.Name):
            return bool(target_names(node) & rounded)
        if isinstance(node, ast.Call):
            names = short_names(node.func)
            if is_float(node.func) or names & converters:
                return True
            args = arguments(node)
            if names & {"map"} and node.args:
                return (bool(short_names(node.args[0]) & (converters | {"float"}))
                        or any(lossy(arg) for arg in args))
            # Input rationalization does not undo a *known* local conversion.
            # Unknown application APIs are not claimed interprocedural proof.
            if not names & {"tuple", "list", "dict", "set", "sum", "min", "max", "abs",
                            "Fraction", "from_float", "zip", "enumerate", "reversed", "sorted",
                            "values", "items", "get", "copy", "__getitem__"}:
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
            old_bindings = dict(bindings)
            self.stack.append(node.name)
            positional = [*node.args.posonlyargs, *node.args.args]
            for arg, value in zip(positional[-len(node.args.defaults):], node.args.defaults):
                self.bind([ast.Name(id=arg.arg)], value)
            for arg, value in zip(node.args.kwonlyargs, node.args.kw_defaults):
                if value is not None:
                    self.bind([ast.Name(id=arg.arg)], value)
            self.generic_visit(node)
            self.stack.pop()
            rounded.clear()
            rounded.update(old)
            aliases.clear()
            aliases.update(old_aliases)
            bindings.clear()
            bindings.update(old_bindings)

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
                if (isinstance(target, (ast.Tuple, ast.List))
                        and isinstance(value, (ast.Tuple, ast.List))
                        and len(target.elts) == len(value.elts)
                        and not any(isinstance(item, ast.Starred) for item in target.elts)):
                    for left, right in zip(target.elts, value.elts):
                        self.bind([left], right)
                    continue
                known_loss = lossy(value)
                names = target_names(target)
                if known_loss:
                    rounded.update(names)
                elif isinstance(target, ast.Name):
                    # Overwriting a container slot cannot clean other slots.
                    # Nor can rebinding an alias clean its former referent.
                    rounded.discard(target.id)
                if isinstance(target, ast.Name):
                    resolved = canonical(value)
                    aliases.pop(target.id, None)
                    if isinstance(value, (ast.Name, ast.Attribute)):
                        aliases[target.id] = resolved
                    bindings[target.id] = value
                elif isinstance(target, ast.Attribute):
                    bindings[_name(target)] = value

        def visit_AugAssign(self, node):
            self.generic_visit(node)
            if isinstance(node.op, ast.Sub) and lossy(node.target) and lossy(node.value):
                self.issue(node, "subtract-rounded")
            if lossy(node.target) or lossy(node.value):
                rounded.update(target_names(node.target))

        def visit_For(self, node):
            self.visit(node.iter)
            self.bind([node.target], node.iter)
            # A loop can run zero or many times. Iterate the local may-taint
            # set to a fixed point so loop-carried assignment is not missed.
            before = set(rounded)
            while True:
                for statement in node.body:
                    self.visit(statement)
                rounded.update(before)
                if rounded == before:
                    break
                before = set(rounded)
            for statement in node.orelse:
                self.visit(statement)

        visit_AsyncFor = visit_For

        def visit_While(self, node):
            before = set(rounded)
            while True:
                self.visit(node.test)
                for statement in node.body:
                    self.visit(statement)
                rounded.update(before)
                if rounded == before:
                    break
                before = set(rounded)
            for statement in node.orelse:
                self.visit(statement)

        def visit_If(self, node):
            self.visit(node.test)
            before = set(rounded)
            before_aliases, before_bindings = dict(aliases), dict(bindings)
            for statement in node.body:
                self.visit(statement)
            after_body = set(rounded)
            body_aliases, body_bindings = dict(aliases), dict(bindings)
            rounded.clear()
            rounded.update(before)
            aliases.clear()
            aliases.update(before_aliases)
            bindings.clear()
            bindings.update(before_bindings)
            for statement in node.orelse:
                self.visit(statement)
            rounded.update(after_body)
            # Either branch's callable may be selected at runtime. Do not let
            # the branch visited last erase the other branch's constructor.
            for name in set(body_bindings) | set(bindings):
                left, right = body_bindings.get(name), bindings.get(name)
                if left is not right:
                    bindings[name] = ast.Tuple(elts=[item for item in (left, right) if item is not None])
            for name in set(body_aliases) | set(aliases):
                if body_aliases.get(name) != aliases.get(name):
                    aliases.pop(name, None)

        def visit_With(self, node):
            for item in node.items:
                self.visit(item.context_expr)
                if item.optional_vars is not None:
                    expr = item.context_expr
                    # Unknown context-manager return: preserve known argument
                    # taint conservatively rather than claiming to decontaminate.
                    if isinstance(expr, ast.Call):
                        expr = ast.Tuple(elts=arguments(expr))
                    self.bind([item.optional_vars], expr)
            for statement in node.body:
                self.visit(statement)

        visit_AsyncWith = visit_With

        def merge_callables(self, states):
            """Keep every statically visible callable from alternative paths."""
            names = set().union(*(set(a) | set(b) for a, b in states))
            for name in names:
                values = [b[name] for _, b in states if name in b]
                distinct = {id(value): value for value in values}
                if len(distinct) > 1:
                    bindings[name] = ast.Tuple(elts=list(distinct.values()))
                elif values:
                    bindings[name] = values[0]
                alias_values = {a.get(name) for a, _ in states}
                if len(alias_values) > 1:
                    aliases.pop(name, None)

        def visit_Try(self, node):
            # Any statement in a try body can raise. Retain may-taint from
            # every visited alternative, including handler/else/finally paths.
            cumulative = set(rounded)
            states = [(dict(aliases), dict(bindings))]
            paths = [node.body, *(handler.body for handler in node.handlers), node.orelse, node.finalbody]
            for statements in paths:
                for statement in statements:
                    self.visit(statement)
                    cumulative.update(rounded)
                    rounded.update(cumulative)
                    states.append((dict(aliases), dict(bindings)))
            self.merge_callables(states)

        visit_TryStar = visit_Try

        def visit_Match(self, node):
            self.visit(node.subject)
            known_loss = lossy(node.subject)
            before = set(rounded)
            states = [(dict(aliases), dict(bindings))]
            for case in node.cases:
                if known_loss:
                    rounded.update(item.name for item in ast.walk(case.pattern)
                                   if isinstance(item, (ast.MatchAs, ast.MatchStar)) and item.name)
                    rounded.update(item.rest for item in ast.walk(case.pattern)
                                   if isinstance(item, ast.MatchMapping) and item.rest)
                if case.guard:
                    self.visit(case.guard)
                for statement in case.body:
                    self.visit(statement)
                before.update(rounded)
                rounded.update(before)
                states.append((dict(aliases), dict(bindings)))
            self.merge_callables(states)

        def visit_ListComp(self, node):
            old, old_aliases, old_bindings = set(rounded), dict(aliases), dict(bindings)
            for generator in node.generators:
                self.visit(generator.iter)
                self.bind([generator.target], generator.iter)
                for condition in generator.ifs:
                    self.visit(condition)
            if isinstance(node, ast.DictComp):
                self.visit(node.key)
                self.visit(node.value)
            else:
                self.visit(node.elt)
            # PEP 572: a comprehension's iteration targets are local, but its
            # walrus targets bind in the containing scope. Preserve just those
            # bindings when restoring the comprehension-local environment.
            exported = {item.target.id for item in ast.walk(node)
                        if isinstance(item, ast.NamedExpr)}
            exported_rounded = exported & rounded
            exported_aliases = {name: aliases[name] for name in exported if name in aliases}
            exported_bindings = {name: bindings[name] for name in exported if name in bindings}
            rounded.clear()
            rounded.update(old)
            rounded.difference_update(exported)
            rounded.update(exported_rounded)
            aliases.clear()
            aliases.update(old_aliases)
            bindings.clear()
            bindings.update(old_bindings)
            for name in exported:
                aliases.pop(name, None)
            aliases.update(exported_aliases)
            bindings.update(exported_bindings)

        visit_SetComp = visit_ListComp
        visit_DictComp = visit_ListComp
        visit_GeneratorExp = visit_ListComp

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
            names = short_names(node.func)
            if callable_names(node.func) & {"math.sqrt", "math.hypot"} and not path.startswith("tests/"):
                self.issue(node, "implicit-root")
            sentinel = (len(node.args) == 1 and isinstance(node.args[0], ast.Constant)
                        and isinstance(node.args[0].value, str)
                        and node.args[0].value.lower().lstrip("+-") in {"inf", "infinity", "nan"})
            if callable_names(node.func) & {"float", "builtins.float"} and not sentinel:
                self.issue(node, "direct-float")
            if canonical(node.func) in {"map", "builtins.map"} and node.args:
                first = node.args[0]
                if isinstance(first, ast.Starred):
                    first = first.value
                if callable_names(first) & {"float", "builtins.float"}:
                    self.issue(node, "direct-float")
            roots = {"sqrt", "sqrt_rational", "sqrt_exact"}
            vectors = {"hypot", "norm", "unit", "norm_rational", "unit_rational", "norm_exact", "unit_exact"}
            if any(lossy(arg) for arg in arguments(node)):
                if names & roots:
                    self.issue(node, "rounded-root")
                if names & vectors:
                    self.issue(node, "rounded-vector")
                if (isinstance(node.func, ast.Attribute)
                        and node.func.attr in {"append", "extend", "insert", "update", "setdefault", "add", "__setitem__"}):
                    rounded.update(target_names(node.func.value))
            self.generic_visit(node)

    Check().visit(tree)
    return list(dict.fromkeys(issues))


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
