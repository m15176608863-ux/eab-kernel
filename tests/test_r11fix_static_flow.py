"""G6K-K01: finite may-state joins, snapshots and executable cone implants.

Oracle: scanner rules inspect source, independently of numerical construction.
The cone witness is certified only by Fraction KKT and binary64 midpoint cells;
no eab geometry/construction primitive contributes to its expected value.
"""
from fractions import Fraction
import importlib.util
import inspect
import math
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("r11_static_gate", ROOT / "tools/check_exact_construction.py")
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)

LOOPS = ["for _ in ():", "for _ in range(0):", "while False:"]


def _cone_implant(loop):
    original = "return norm_rational(p), noise"
    body = ("root = norm_rational\n    " + loop
            + "\n        root = abs\n    return root(vector_rational(p, allow_underflow=True)), noise")
    source = (ROOT / "src/eab/kernel3d/covers3.py").read_text(encoding="utf-8")
    assert source.count(original) == 1
    return original, body, source.replace(original, body)


def _assert_cone_rejected(scan, loop):
    _, _, source = _cone_implant(loop)
    issues = scan(source, "src/eab/kernel3d/covers3.py")
    assert any(row[2:4] == ("cone_intersection_margin", "rounded-vector") for row in issues), (
        "K01 real cone rounded-vector assertion", loop, issues)


@pytest.mark.parametrize("loop", LOOPS)
def test_k01_zero_iteration_alias_implants_change_real_cone_and_are_rejected(loop):
    import eab.kernel3d.covers3 as covers
    from eab.kernel3d.geom3 import tetra

    original, body, _ = _cone_implant(loop)
    namespace = dict(vars(covers))
    function_source = inspect.getsource(covers.cone_intersection_margin)
    exec(compile(function_source.replace(original, body), "<k01 actual cone implant>", "exec"), namespace)
    u = math.ulp(0.0)
    q = Fraction(1, 2**1074)
    assert Fraction(u) == q
    rows = ((-Fraction(1), Fraction(1), -q), (-q, -Fraction(1), Fraction(1)),
            (Fraction(1), -q, -Fraction(1)))
    projection = (-q / 3,) * 3
    assert projection == tuple(sum(row[i] for row in rows) / 3 for i in range(3))
    squared = sum(x*x for x in projection)
    assert all(sum(x*y for x, y in zip(projection, row)) == squared for row in rows)
    assert (q/2)**2 < squared < (3*q/2)**2
    shape = tetra((0., 0., 0.), (1., -1., u), (u, 1., -1.), (-1., u, 1.))
    assert covers.cone_intersection_margin(shape, 0, shape.reflected(), 0)[0] == u
    assert namespace["cone_intersection_margin"](shape, 0, shape.reflected(), 0)[0] == 0
    _assert_cone_rejected(gate.scan_text, loop)


FLOW_CASES = [
    ("zero_for", "for _ in ():\n        root = abs"),
    ("zero_while", "while False:\n        root = abs"),
    ("zero_comp", "[(root := abs) for _ in ()]"),
    ("zero_setcomp", "{(root := abs) for _ in ()}"),
    ("zero_dictcomp", "{_: (root := abs) for _ in ()}"),
    ("lazy_generator", "((root := abs) for _ in ())"),
    ("comp_filter", "[(root := abs) for _ in [1] if False]"),
    ("nested_comp", "[(root := abs) for _ in [1] for j in ()]"),
    ("short_and", "False and (root := abs)"),
    ("short_or", "True or (root := abs)"),
    ("compare_chain", "0 > 1 > (root := abs)"),
    ("ifexp_body", "(root := abs) if False else 0"),
    ("ifexp_else", "0 if True else (root := abs)"),
    ("if_branch", "if False:\n        root = abs"),
    ("loop_break", "for _ in [1]:\n        break\n        root = abs"),
    ("loop_continue", "for _ in [1]:\n        continue\n        root = abs"),
    ("loop_else", "for _ in [1]:\n        break\n    else:\n        root = abs"),
    ("while_else", "while flag:\n        break\n    else:\n        root = abs"),
    ("try_exception_prefix", "try:\n        risky()\n        root = abs\n    except ValueError:\n        return root(vector_rational(q))"),
    ("try_raise_prefix", "try:\n        raise ValueError()\n        root = abs\n    except ValueError:\n        return root(vector_rational(q))"),
    ("finally_prefix", "try:\n        raise ValueError()\n        root = abs\n    finally:\n        return root(vector_rational(q))"),
    ("try_else", "try:\n        risky()\n    except ValueError:\n        pass\n    else:\n        root = abs"),
    ("try_handler_independence", "try:\n        risky()\n    except ValueError:\n        root = abs\n    except RuntimeError:\n        return root(vector_rational(q))"),
    ("trystar_handler_independence", "try:\n        risky()\n    except* ValueError:\n        root = abs\n    except* RuntimeError:\n        root(vector_rational(q))"),
    ("match_case_independence", "match flag:\n        case 1:\n            root = abs\n        case 2:\n            return root(vector_rational(q))"),
    ("match_guard", "match flag:\n        case 1 if (root := abs):\n            pass\n        case 2:\n            return root(vector_rational(q))"),
    ("container_snapshot", "box = [root]\n    root = abs\n    return box[0](vector_rational(q))"),
    ("name_snapshot", "saved = root\n    root = abs\n    return saved(vector_rational(q))"),
    ("attribute_snapshot", "holder.root = root\n    root = abs\n    return holder.root(vector_rational(q))"),
    ("branch_snapshot", "box = [root]\n    if flag:\n        root = abs\n    else:\n        root = sum\n    return box[0](vector_rational(q))"),
    ("loop_carried_callable", "root = abs\n    saved = abs\n    for _ in range(3):\n        saved(vector_rational(q))\n        saved = root\n        root = norm_rational"),
    ("loop_carried_container", "root = abs\n    box = [abs]\n    for _ in range(3):\n        box[0](vector_rational(q))\n        box = [root]\n        root = norm_rational"),
    ("comp_carried_callable", "root = abs\n    saved = abs\n    [(saved(vector_rational(q)), (saved := root), (root := norm_rational)) for _ in range(3)]"),
    ("for_target_zero", "for root in ():\n        pass"),
    ("call_arg_walrus", "return root((root := abs) and vector_rational(q))"),
    ("call_arg_rounded_walrus", "return norm_rational((v := vector_rational(q)))"),
    ("match_binding", "match root:\n        case saved:\n            return saved(vector_rational(q))"),
    ("with_binding", "with context(root) as saved:\n        return saved(vector_rational(q))"),
]


@pytest.mark.parametrize("label,body", FLOW_CASES, ids=[row[0] for row in FLOW_CASES])
def test_k01_all_control_flow_paths_keep_callable_and_binding_provenance(label, body):
    source = ("def bad(q, flag, holder):\n    root = norm_rational\n    " + body
              + "\n    return root(vector_rational(q))\n")
    issues = gate.scan_text(source, "src/eab/k01_injected.py")
    target_line = next(i for i, line in enumerate(source.splitlines(), 1) if "vector_rational(q)" in line)
    assert any(row[1:4] == (target_line, "bad", "rounded-vector") for row in issues), (label, target_line, issues, source)


@pytest.mark.parametrize("body", [
    "x = scalar_rational(q)\n    [(x := q) for _ in ()]\n    return sqrt_rational(x)",
    "x = scalar_rational(q)\n    False and (x := q)\n    return sqrt_rational(x)",
    "x = scalar_rational(q)\n    (x := q) if False else 0\n    return sqrt_rational(x)",
    "box = []\n    alias = box\n    for _ in ():\n        alias = []\n    alias.append(scalar_rational(q))\n    return sqrt_rational(box[0])",
])
def test_k01_rounded_values_and_mutable_aliases_join_with_callable_state(body):
    issues = gate.scan_text("def bad(q):\n    " + body + "\n")
    assert any(row[2:4] == ("bad", "rounded-root") for row in issues), (body, issues)


@pytest.mark.parametrize("body", [
    "root = norm_rational\n    root = abs\n    return root(vector_rational(q))",
    "root = norm_rational\n    if flag:\n        root = abs\n    else:\n        root = sum\n    return root(vector_rational(q))",
    "root = norm_rational\n    [root for root in [abs]]\n    return root(q)",
    "root = norm_rational\n    try:\n        risky()\n    finally:\n        root = abs\n    return root(vector_rational(q))",
    "v = []\n    alias = v\n    alias = []\n    alias.append(scalar_rational(q))\n    return norm_rational(v)",
])
def test_k01_unrounded_paths_have_no_rounding_false_positive_but_fail_closed(body):
    issues = gate.scan_text("def good(q, flag):\n    " + body + "\n")
    if body.startswith("v = []"):
        # R12FIXb proves two distinct local lists; the rounded write never
        # reaches the original empty vector. No unsupported dispatch remains.
        assert issues == []
    else:
        assert issues and all(row[3].startswith("closed-") for row in issues), issues


EXTRA_CASES = [
    ("scoped_import", "from eab.construction import norm_rational as build\ndef bad(q):\n    return build(vector_rational(q))\ndef safe():\n    from builtins import abs as build\n"),
    ("suppressed_exception", "def bad(q):\n    root = norm_rational\n    with suppress(ValueError):\n        raise ValueError()\n        root = abs\n    return root(vector_rational(q))\n"),
    ("async_suppressed_exception", "async def bad(q):\n    root = norm_rational\n    async with suppressor():\n        raise ValueError()\n        root = abs\n    return root(vector_rational(q))\n"),
    ("guard_false_exit", "def bad(q):\n    root = abs\n    match flag:\n        case _ if (root := norm_rational) and False:\n            return 0\n    return root(vector_rational(q))\n"),
    ("lambda_kwonly_default", "def bad(q):\n    f = lambda *, root=norm_rational: root(vector_rational(q))\n    return f()\n"),
    ("lambda_posonly_default", "def bad(q):\n    f = lambda root=norm_rational, /: root(vector_rational(q))\n    return f()\n"),
    ("partial_bound_argument", "from functools import partial\ndef bad(q):\n    root = partial(norm_rational, vector_rational(q))\n    return root()\n"),
    ("generator_next_export", "def bad(q):\n    root = abs\n    gen = ((root := norm_rational) for _ in [0])\n    root = abs\n    next(gen)\n    return root(vector_rational(q))\n"),
    ("generator_next_callable", "def bad(q):\n    root = abs\n    gen = (root for _ in [0])\n    root = norm_rational\n    saved = next(gen)\n    return saved(vector_rational(q))\n"),
    ("generator_late_call", "def bad(q):\n    root = abs\n    gen = (root(vector_rational(q)) for _ in [0])\n    root = norm_rational\n    return tuple(gen)\n"),
    ("generator_late_rounded", "def bad(q):\n    vals = q\n    gen = (norm_rational(vals) for _ in [0])\n    vals = vector_rational(q)\n    return tuple(gen)\n"),
    ("generator_for_callable", "def bad(q):\n    root = abs\n    gen = (root for _ in [0])\n    root = norm_rational\n    for saved in gen:\n        return saved(vector_rational(q))\n"),
    ("generator_starred", "def bad(q):\n    root = abs\n    gen = (root(vector_rational(q)) for _ in [0])\n    root = norm_rational\n    return [*gen]\n"),
    ("generator_unknown_consumer", "def bad(q):\n    root = abs\n    gen = (root(vector_rational(q)) for _ in [0])\n    root = norm_rational\n    return consumer(gen)\n"),
    ("generator_method_next", "def bad(q):\n    root = abs\n    gen = (root for _ in [0])\n    root = norm_rational\n    saved = gen.__next__()\n    return saved(vector_rational(q))\n"),
    ("generator_map_chain", "def bad(q):\n    root = abs\n    gen = (root(vector_rational(q)) for _ in [0])\n    mapped = map(abs, gen)\n    root = norm_rational\n    return list(mapped)\n"),
    ("async_for_zero", "async def bad(q):\n    root = norm_rational\n    async for _ in stream:\n        root = abs\n    return root(vector_rational(q))\n"),
]


@pytest.mark.parametrize("label,source", EXTRA_CASES, ids=[row[0] for row in EXTRA_CASES])
def test_k01_extended_scoped_bindings_and_deferred_generators(label, source):
    issues = gate.scan_text(source, "src/eab/k01_injected.py")
    target_line = (next(i for i, line in enumerate(source.splitlines(), 1) if "norm_rational(vals)" in line)
                   if label == "generator_late_rounded" else
                   next(i for i, line in enumerate(source.splitlines(), 1) if "vector_rational(q)" in line))
    assert any(row[1:4] == (target_line, "bad", "rounded-vector") for row in issues), (label, target_line, issues)


def test_k01_loop_allocation_site_keeps_prior_object_alias():
    source = """def bad(q):
    old = None
    for _ in range(2):
        new = []
        if old is not None:
            return sqrt_rational(old[0])
        new.append(scalar_rational(q))
        old = new
"""
    issues = gate.scan_text(source)
    assert any(row[1:4] == (6, "bad", "rounded-root") for row in issues), issues


def test_k01_eager_generator_result_does_not_reexecute_exhausted_body():
    source = """def good(q):
    root = abs
    saved = tuple(root(vector_rational(q)) for _ in [1])
    root = norm_rational
    return tuple(saved)
"""
    issues = gate.scan_text(source)
    assert issues and all(row[3].startswith("closed-") for row in issues), issues


def _mutant_scan(old, new):
    source = (ROOT / "tools/check_exact_construction.py").read_text(encoding="utf-8")
    assert source.count(old) == 1
    namespace = {"__file__": str(ROOT / "tools/check_exact_construction.py"), "__name__": "k01_gate_mutant"}
    exec(compile(source.replace(old, new), "<k01 internal scanner rollback>", "exec"), namespace)
    return namespace["scan_text"]


def test_k01_removing_zero_path_join_trips_the_real_cone_assertion():
    # Removing the entry path reproduces the original zero-iteration alias
    # overwrite, inside the scanner rather than fabricating its output.
    source = (ROOT / "tools/check_exact_construction.py").read_text(encoding="utf-8")
    original = "new_head = joined(entry, head, backedge)"
    assert source.count(original) == 1
    namespace = {"__file__": str(ROOT / "tools/check_exact_construction.py"), "__name__": "k01_zero_path_mutant"}
    exec(compile(source.replace(original, "new_head = backedge or head"), "<k01 zero-path rollback>", "exec"), namespace)
    _assert_cone_rejected(gate.scan_text, LOOPS[0])
    with pytest.raises(AssertionError, match="K01 real cone rounded-vector assertion"):
        _assert_cone_rejected(namespace["scan_text"], LOOPS[0])


def test_k01_removing_backedge_iteration_trips_loop_internal_assertion():
    old = "if new_head == head:\n                    break\n                head = new_head\n            # Only condition/exhaustion"
    mutant = _mutant_scan(old, "if True:\n                    break\n                head = new_head\n            # Only condition/exhaustion")
    source = """def bad(q):
    root = abs
    saved = abs
    for _ in range(3):
        saved(vector_rational(q))
        saved = root
        root = norm_rational
    root = abs
    saved = abs
"""

    def check(scan):
        issues = scan(source)
        assert any(row[1:4] == (5, "bad", "rounded-vector") for row in issues), "K01 loop-internal callable fixed-point assertion"

    check(gate.scan_text)
    with pytest.raises(AssertionError, match="K01 loop-internal callable fixed-point assertion"):
        check(mutant)


LAST_CFG_CASES = [
    ("assert_success_skips_message", "def bad(q):\n    root = norm_rational\n    assert True, (root := abs)\n    return root(vector_rational(q))\n"),
    ("assert_failure_evaluates_message", "def bad(q):\n    root = abs\n    try:\n        assert False, (root := norm_rational)\n    except AssertionError:\n        pass\n    return root(vector_rational(q))\n"),
    ("dict_interleaved_values", "def bad(q):\n    root = norm_rational\n    d = {'x': root(vector_rational(q)), (root := abs): 1}\n    return d\n"),
    ("dict_unpack_order", "def bad(q):\n    root = norm_rational\n    d = {**{'x': root(vector_rational(q))}, (root := abs): 1}\n    return d\n"),
    ("augassign_target_evaluated_once", "def bad(q):\n    root = abs\n    holder = [0]\n    holder[((root := abs), 0)[1]] += ((root := norm_rational), 1)[1]\n    return root(vector_rational(q))\n"),
]


@pytest.mark.parametrize("label,source", LAST_CFG_CASES, ids=[row[0] for row in LAST_CFG_CASES])
def test_k01_assert_and_literal_assignment_evaluation_order(label, source):
    target_line = next(i for i, line in enumerate(source.splitlines(), 1) if "vector_rational(q)" in line)
    issues = gate.scan_text(source)
    assert any(row[1:4] == (target_line, "bad", "rounded-vector") for row in issues), (label, target_line, issues)


@pytest.mark.parametrize("body", [
    "def inner(x: norm_rational(vector_rational(q))):\n        return x",
    "x: norm_rational(vector_rational(q)) = 0",
])
def test_k01_annotation_expressions_are_still_scanned(body):
    source = "def bad(q):\n    " + body + "\n"
    issues = gate.scan_text(source)
    assert any(row[1] == 2 and row[3] == "rounded-vector" for row in issues), issues
