"""WO-T2d source-local checks, not a proof of numerical correctness.

The oracle is literal policy/source inspection. New exact helpers must pass
the existing three scanners without new admission. Mutation controls enter
the policy parser or an actual helper's AST, not a post-hoc result list.
"""
import ast
import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import check_exact_construction as checker


ROOT = Path(__file__).resolve().parents[1]
PREFIXES = ("tests/t2d_", "tests/test_t2d_", "tools/t2d_")
SCANNERS = {
    "tools/check_exact_construction.py": "cc6143a27369f1247718b2e48ae80f3afb7b5060b23de845437a53b5a0768517",
    "tools/exact_construction_subset.py": "35e6262a7c36ea5f20679f047dd6f030feeb6fcbe8be7813573212829b503274",
    "tools/exact_construction_flow.py": "814f00ab607726c7753fa86ddedc08fd728eb48c4e57b8a61dda55140c3cd1db",
}


def test_t2d_static_admission_and_floating_sink_counts_are_zero():
    policy = json.loads((ROOT / "tools/exact_construction_policy.json").read_text("utf-8"))
    admissions = [row for row in policy["waivers"] if row["path"].startswith(PREFIXES)]
    assert admissions == [], ("T2d requires zero static admissions and zero floating sink admissions", admissions)


def test_t2d_internal_policy_admission_mutation_is_rejected():
    for path in ("tests/t2d_knob_family_exact.py", "tests/test_t2d_family.py", "tools/t2d_probe.py"):
        # The count assertion must reject even a nominal proof-gap entry.
        policy = {"waivers": [{"path": path, "rule": "closed-unproved-call"}]}
        with patch.object(json, "loads", return_value=policy):
            with unittest.TestCase().assertRaisesRegex(AssertionError, "T2d requires zero static admissions"):
                test_t2d_static_admission_and_floating_sink_counts_are_zero()


def test_t2d_three_static_scanners_remain_byte_unchanged():
    for path, expected in SCANNERS.items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected, path


def test_t2d_exact_sources_reject_internal_floating_injections():
    # This source-local screen recognizes literal/import aliases and simple
    # numeric bindings, not arbitrary Python dispatch or whole-program types.
    # In particular UNKNOWN is not silently treated as Fraction for powers.
    def audit(source):
        tree = ast.parse(source)
        aliases, assignments = {}, {}
        parents = {child: node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)}

        def scope(node):
            parent = parents.get(node)
            while parent is not None and not isinstance(parent, (
                    ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)):
                parent = parents.get(parent)
            return parent

        def binding_key(node, name):
            owner = scope(node)
            while owner is not None:
                key = owner, name
                if key in assignments or key in aliases:
                    return key
                owner = scope(owner)
            return None

        def dotted(node, seen=frozenset()):
            if isinstance(node, ast.Name):
                key = binding_key(node, node.id)
                if key is None:
                    return node.id
                if key in seen:
                    return ""
                if key in assignments:
                    names = {dotted(value, seen | {key}) for _, value in assignments[key]}
                    return names.pop() if len(names) == 1 else ""
                names = aliases[key]
                return next(iter(names)) if len(names) == 1 else ""
            if isinstance(node, ast.Attribute):
                return dotted(node.value, seen) + "." + node.attr
            return ""

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for item in node.names:
                    key = scope(node), item.asname or item.name.split(".")[0]
                    aliases.setdefault(key, set()).add(item.name)
            elif isinstance(node, ast.ImportFrom):
                for item in node.names:
                    key = scope(node), item.asname or item.name
                    aliases.setdefault(key, set()).add((node.module or "") + "." + item.name)
            elif isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
                targets = node.targets if isinstance(node, ast.Assign) else (node.target,)
                for target in targets:
                    if isinstance(target, ast.Name):
                        value = None if isinstance(node, ast.AugAssign) else node.value
                        assignments.setdefault((scope(node), target.id), []).append((node, value))
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)):
                # Defining an identically named callable invalidates an import
                # constructor binding; no inferred return type is assumed.
                if not isinstance(node, ast.Lambda):
                    assignments.setdefault((scope(node), node.name), []).append((node, None))
                if not isinstance(node, ast.ClassDef):
                    arguments = node.args.posonlyargs + node.args.args + node.args.kwonlyargs
                    arguments += [arg for arg in (node.args.vararg, node.args.kwarg) if arg is not None]
                    for argument in arguments:
                        assignments.setdefault((node, argument.arg), []).append((node, None))
            elif isinstance(node, (ast.ExceptHandler, ast.MatchAs, ast.MatchStar, ast.MatchMapping)):
                name = node.rest if isinstance(node, ast.MatchMapping) else node.name
                if name is not None:
                    assignments.setdefault((scope(node), name), []).append((node, None))
            elif isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)):
                parent = parents.get(node)
                simple_assignment = (isinstance(parent, ast.Assign) and node in parent.targets
                                     or isinstance(parent, (ast.AnnAssign, ast.AugAssign)) and parent.target is node)
                if not simple_assignment:
                    # Unknown fallback for unpacking, walrus, loop/with targets,
                    # comprehension targets and deletion. These cannot retain
                    # a previously imported Fraction/Surd constructor proof.
                    assignments.setdefault((scope(node), node.id), []).append((parent, None))

        def integer_constant(node):
            if isinstance(node, ast.Constant) and type(node.value) is int:
                return node.value
            if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
                value = integer_constant(node.operand)
                if value is not None:
                    return -value if isinstance(node.op, ast.USub) else value
            return None

        def numeric_kind(node, seen=frozenset()):
            if isinstance(node, ast.Constant) and type(node.value) is int:
                return "integer"
            if isinstance(node, ast.Name):
                key = binding_key(node, node.id)
                if key is None or key in seen:
                    return "unknown"
                bindings = [(binding, value) for binding, value in assignments.get(key, ())
                            if not (isinstance(binding, ast.AugAssign) and binding.target is node)]
                # An unconditional earlier assignment replaces a parameter.
                if any(parents.get(binding) is key[0] and isinstance(binding, (ast.Assign, ast.AnnAssign))
                       and binding.lineno < node.lineno for binding, _ in bindings):
                    bindings = [(binding, value) for binding, value in bindings
                                if not isinstance(binding, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda))]
                kinds = {numeric_kind(value, seen | {key}) for _, value in bindings}
                return kinds.pop() if len(kinds) == 1 else "unknown"
            if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
                return numeric_kind(node.operand, seen)
            if isinstance(node, ast.Call):
                if dotted(node.func) in ("fractions.Fraction", "tests.t2d_knob_family_exact.Surd"):
                    return "exact"
            if isinstance(node, ast.BinOp):
                left, right = numeric_kind(node.left, seen), numeric_kind(node.right, seen)
                if left in ("integer", "exact") and right in ("integer", "exact"):
                    if isinstance(node.op, ast.Div):
                        return "exact" if "exact" in (left, right) else "unknown"
                    if isinstance(node.op, ast.Pow):
                        exponent = integer_constant(node.right)
                        if exponent is None or (exponent < 0 and left != "exact"):
                            return "unknown"
                        return left
                    if isinstance(node.op, (ast.Add, ast.Sub, ast.Mult)):
                        return "exact" if "exact" in (left, right) else "integer"
                    if isinstance(node.op, (ast.LShift, ast.RShift, ast.FloorDiv, ast.Mod)):
                        return "integer" if left == right == "integer" else "unknown"
            return "unknown"

        def deliberate_surd_conversion_rejection(node):
            # Exactly the pre-existing negative test. This is NOT an exemption
            # for F.__float__, another Surd call, an alias or another context.
            if not isinstance(node, ast.Call) or ast.dump(node, include_attributes=False) != ast.dump(
                    ast.parse("exact.Surd(0, 1, 2).__float__()", mode="eval").body,
                    include_attributes=False):
                return False
            statement = parents.get(node)
            context = parents.get(statement)
            function = parents.get(context)
            return (isinstance(statement, ast.Expr) and isinstance(context, ast.With)
                    and context.body == [statement] and len(context.items) == 1
                    and ast.dump(context.items[0].context_expr, include_attributes=False)
                    == ast.dump(ast.parse("unittest.TestCase().assertRaises(TypeError)", mode="eval").body,
                                include_attributes=False)
                    and isinstance(function, ast.FunctionDef)
                    and function.name == "test_t2d_algebra_rejects_nonexact_or_mixed_field_operations")

        forbidden = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and type(node.value) is float:
                forbidden.append((node.lineno, "floating literal"))
            elif isinstance(node, (ast.BinOp, ast.AugAssign)) and isinstance(node.op, ast.Pow):
                base = node.left if isinstance(node, ast.BinOp) else node.target
                exponent = integer_constant(node.right if isinstance(node, ast.BinOp) else node.value)
                if exponent is None:
                    forbidden.append((node.lineno, "power exponent is not an integer constant"))
                elif exponent < 0 and numeric_kind(base) != "exact":
                    forbidden.append((node.lineno, "negative power base is not proven Fraction or Surd"))
            elif isinstance(node, (ast.BinOp, ast.AugAssign)) and isinstance(node.op, ast.Div):
                left = node.left if isinstance(node, ast.BinOp) else node.target
                right = node.right if isinstance(node, ast.BinOp) else node.value
                if numeric_kind(left) == numeric_kind(right) == "integer":
                    forbidden.append((node.lineno, "integer true division produces binary64"))
            elif isinstance(node, ast.Call):
                name = dotted(node.func)
                if (name in ("float", "builtins.float", "pow", "builtins.pow", "operator.pow")
                        or name.endswith(".__pow__")
                        or (name.endswith(".__float__") and not deliberate_surd_conversion_rejection(node))
                        or (name.startswith("math.") and name != "math.isqrt")
                        or name.startswith(("numpy.", "struct.", "ctypes.", "float.", "builtins.float.",
                                            "cmath.", "decimal."))):
                    forbidden.append((node.lineno, name))
                if name in ("__import__", "builtins.__import__"):
                    forbidden.append((node.lineno, "dynamic import is outside the exact source subset"))
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                names = [item.name for item in node.names] if isinstance(node, ast.Import) else [node.module or ""]
                exact_integer_import = (isinstance(node, ast.ImportFrom) and node.module == "math"
                                        and all(item.name == "isqrt" for item in node.names))
                if not exact_integer_import and any(name.split(".")[0] in (
                        "math", "numpy", "struct", "ctypes", "cmath", "decimal") for name in names):
                    forbidden.append((node.lineno, "floating or binary64 import"))
            if isinstance(node, (ast.Name, ast.Attribute)) and isinstance(node.ctx, ast.Load):
                name = dotted(node)
                if name in ("pow", "builtins.pow", "operator.pow") or name.endswith(".__pow__"):
                    forbidden.append((node.lineno, "power callable reference: " + name))
                if name.endswith(".__float__") and not deliberate_surd_conversion_rejection(parents.get(node)):
                    forbidden.append((node.lineno, "floating conversion callable reference: " + name))
        assert not forbidden, ("T2d exact source excludes floating sinks", forbidden)

    paths = sorted(set((ROOT / "tests").glob("t2d_*.py")) | set((ROOT / "tests").glob("test_t2d_*.py")))
    helper = ROOT / "tests/t2d_knob_family_exact.py"
    assert helper in paths, "the exact helper must be inspected, not silently absent"
    for path in paths:
        encoded = path.read_bytes()
        assert not encoded.startswith(b"\xef\xbb\xbf") and b"\r" not in encoded, path
        audit(encoded.decode("utf-8"))

    source = helper.read_text("utf-8")
    tree = ast.parse(source)
    target = next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef))
    for accepted in (
            "from fractions import Fraction as F; value = F(5) ** -2",
            "from tests.t2d_knob_family_exact import Surd; value = Surd(5) ** -2",
            "from fractions import Fraction as F; value = F(5); value **= -2",
            "from tests.t2d_knob_family_exact import Surd; value = Surd(5); value **= -2",
            "from fractions import Fraction as F; value = (F(5)+1) ** -2",
            "value = 5 ** 2; value **= +2",
            "from fractions import Fraction as F; value = F(1, 2); other = F(1)/2; reverse = 1/F(2)",
            "from pathlib import Path; value = Path('root') / 'child'",
            "from math import isqrt; exact_integer_root = isqrt(9)"):
        audit(accepted)
    for injection in (
            "float(0)", "import builtins as b; b.float(0)",
            "convert = float; convert(0)", "import math; math.sqrt(4)",
            "from math import sin as sine; sine(0)",
            "import numpy as np; np.asarray([0])",
            "from struct import unpack as decode; decode('d', b'12345678')",
            "import ctypes; ctypes.c_double(0)", "value = 0.5",
            "value = 5 ** F(1, 2)", "value = 5 ** exponent", "value = 5 ** True",
            "value = 5; value **= F(1, 2)", "value = 5; value **= exponent", "value = 5; value **= True",
            "value = 2 ** -1", "value = 2; value **= -1", "value = unknown ** -1",
            "value = 2; result = value ** -1", "value = 1/2", "left = 1; right = 2; value = left/right",
            "value = 1; value /= 2", "value = (1+2)/(3*4)",
            "pow(2, -1)", "import builtins as b; b.pow(2, -1)",
            "import operator as op; op.pow(2, -1)", "from operator import pow as power; power(2, -1)",
            "value = 2; value.__pow__(-1)", "F(2).__pow__(-1)",
            "import cmath", "from cmath import sqrt", "import decimal", "from decimal import Decimal",
            "__import__('math')", "import builtins as b; b.__import__('math')",
            "F.__float__(F(1))", "F(1).__float__()", "convert = F.__float__; convert(F(1))",
            "exact.Surd(0, 1, 2).__float__()", "callback = pow",
            "import operator; callback = operator.pow", "callback = F(1).__pow__",
            "callback = F.__float__",
            "def shadow(F):\n    return F(2) ** -1",
            "def F(value):\n    return value\nvalue = F(2) ** -1",
            "for F in (int,):\n    value = F(2) ** -1",
            "with resource as F:\n    value = F(2) ** -1",
            "value = [F(2) ** -1 for F in (int,)]",
            "class F:\n    pass\nvalue = F(2) ** -1",
            "F, other = int, 0\nvalue = F(2) ** -1",
            "[F, other] = [int, 0]\nvalue = F(2) ** -1",
            "(F := int)\nvalue = F(2) ** -1",
            "del F\nvalue = F(2) ** -1",
            "async def F(value):\n    return value\nvalue = F(2) ** -1",
            "async def shadow(F):\n    return F(2) ** -1",
            "callback = lambda F: F(2) ** -1",
            "try:\n    operation()\nexcept Exception as F:\n    value = F(2) ** -1",
            "match resource:\n    case F:\n        value = F(2) ** -1",
            "match resource:\n    case [*F]:\n        value = F(2) ** -1",
            "match resource:\n    case {**F}:\n        value = F(2) ** -1"):
        # Every injection is INSIDE the exact helper's first function. No
        # synthetic violation is appended to the audit's output afterwards.
        mutant = ast.parse(source)
        selected = next(node for node in ast.walk(mutant)
                        if isinstance(node, ast.FunctionDef) and node.lineno == target.lineno)
        selected.body[0:0] = ast.parse(injection).body
        with unittest.TestCase().assertRaisesRegex(AssertionError, "T2d exact source excludes floating sinks", msg=injection):
            audit(ast.unparse(mutant))


def test_t2d_exact_runtime_outputs_reject_internal_float_injections():
    # Representative output closure, not a claim about every possible input.
    # The three helpers and all 12 declared family cases are exercised; Surd
    # coefficient channels are traversed rather than treated as opaque values.
    from fractions import Fraction as F
    import tests.t2d_knob_family_exact as exact
    import tests.t2d_critical_escape_exact as escape
    import tests.t2d_sections_exact as sections

    def check(value):
        assert type(value) is not float, "binary64 value escaped an exact helper"
        if isinstance(value, exact.Surd):
            for coefficient in (value.a, value.b, value.q):
                check(coefficient)
        elif isinstance(value, dict):
            for key, item in value.items():
                check(key)
                check(item)
        elif isinstance(value, (tuple, list, set, frozenset)):
            for item in value:
                check(item)
        else:
            assert value is None or isinstance(value, (F, int, str, bool)), "unexpected exact-output type"

    for n, element in exact.TABLE:
        check(exact.verify_family_geometry(n))
        check(exact.edge_candidates(n, element))
        values = exact.verify_values(n, element)
        check(values)
        check(values["delta"].bounds(96))
        check(exact.verify_C(n, element))
        check(escape.truth_obstacles(n))
        check(escape.verify_disk_subset(n, element, values["delta"]))
        if all(values["S"]):
            check(escape.verify_critical_escape(n, element))
        check(sections.element_profile(element))
        check(sections.eroded_polygon(n, element, F(1, 4)))
    for element in ("square", "octagon", "K16"):
        check(exact.circle_limits(element))

    # Real primitive mutations in freshly compiled function code, before its
    # geometry is computed. Original modules/files are left byte unchanged.
    for module, name, call in (
            (exact, "full_arc", lambda function: function(4)),
            (escape, "truth_obstacles", lambda function: function(4)),
            (sections, "_line_at", lambda function: function(((F(0), F(0)), (F(1), F(1))), F(1, 2)))):
        tree = ast.parse(Path(module.__file__).read_text("utf-8"))
        function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name)
        if name == "full_arc":
            # F(2*i,n) -> (2*i)/n creates binary64 before arc coordinates.
            rational_call = next(node for node in ast.walk(function) if isinstance(node, ast.Call)
                                 and isinstance(node.func, ast.Name) and node.func.id == "F")
            replacement = ast.BinOp(left=rational_call.args[0], op=ast.Div(), right=rational_call.args[1])
            parent = next(node for node in ast.walk(function) if rational_call in ast.iter_child_nodes(node))
            assert isinstance(parent, ast.BinOp) and parent.left is rational_call
            parent.left = replacement
        elif name == "truth_obstacles":
            # The floor's primitive height is corrupted before wall creation.
            function.body.insert(0, ast.parse("FLOOR_TOP = 1/2").body[0])
        else:
            # Corrupt the affine slope calculation, not the returned container.
            assignment = next(node for node in ast.walk(function) if isinstance(node, ast.Assign)
                              and any(isinstance(target, ast.Name) and target.id == "slope" for target in node.targets))
            assignment.value = ast.parse("1/2", mode="eval").body
        namespace = dict(vars(module))
        code = ast.fix_missing_locations(ast.Module(body=[function], type_ignores=[]))
        exec(compile(code, "<t2d internal numeric mutation>", "exec"), namespace)
        with unittest.TestCase().assertRaisesRegex(AssertionError, "binary64 value escaped"):
            check(call(namespace[name]))


def test_t2d_new_test_sources_pass_unmodified_static_gate():
    paths = sorted(set((ROOT / "tests").glob("t2d_*.py")) | set((ROOT / "tests").glob("test_t2d_*.py")))
    assert ROOT / "tests/t2d_knob_family_exact.py" in paths
    issues = []
    for path in paths:
        issues.extend(checker.scan_text(path.read_text("utf-8"), path.relative_to(ROOT).as_posix(), repository_root=ROOT))
    assert issues == [], issues


def test_t2d_policy_preserves_original_crlf_without_bom():
    encoded = (ROOT / "tools/exact_construction_policy.json").read_bytes()
    assert not encoded.startswith(b"\xef\xbb\xbf"), "policy must remain UTF-8 without BOM"
    assert encoded.count(b"\r\n") == encoded.count(b"\n"), "policy must preserve CRLF"
    assert encoded.count(b"\r\n") == encoded.count(b"\r"), "policy must preserve CRLF"
