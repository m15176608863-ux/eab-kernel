"""R13 lifecycle regression: numeric oracle uses only independent Fraction cells.

Source probes execute real premature rounding, then exercise the static checker.
The checker is auxiliary; this test is not a proof for arbitrary Python.
"""
from fractions import Fraction
import importlib.util
import math
import shutil
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("r13_lifecycle_gate", ROOT / "tools/check_exact_construction.py")
gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gate)

LIFECYCLE_CASES = {
    'dataclass_post_init': """from dataclasses import dataclass
from fractions import Fraction
from eab.construction import norm_rational
@dataclass
class Holder:
    points: tuple[Fraction, Fraction]
    def __post_init__(self):
        self.points = tuple(component*1.0 for component in self.points)
def bad(q: Fraction):
    return norm_rational(Holder((q,q)).points)
""",
    'inherited_init': """from dataclasses import dataclass
from fractions import Fraction
from eab.construction import norm_rational
class Parent:
    def __init__(self, points: tuple[Fraction,Fraction]):
        self.points = tuple(component*1.0 for component in points)
class Holder(Parent):
    points: tuple[Fraction,Fraction]
def bad(q: Fraction):
    return norm_rational(Holder((q,q)).points)
""",
    'instance_method_mutation': """from dataclasses import dataclass
from fractions import Fraction
from eab.construction import norm_rational
@dataclass
class Holder:
    points: tuple[Fraction, Fraction]
    def update(self):
        self.points = tuple(component*1.0 for component in self.points)
def bad(q: Fraction):
    holder=Holder((q,q))
    holder.update()
    return norm_rational(holder.points)
""",
    'property_setter': """from fractions import Fraction
from eab.construction import norm_rational
class Holder:
    points: tuple[Fraction, Fraction]
    _points: tuple[Fraction, Fraction]
    def __init__(self, points):
        self._points = points
    @property
    def points(self):
        return self._points
    @points.setter
    def points(self, value):
        self._points = tuple(component*1.0 for component in value)
def bad(q: Fraction):
    holder = Holder((q, q))
    holder.points = (q, q)
    return norm_rational(holder.points)
""",
}


@pytest.mark.parametrize("case", LIFECYCLE_CASES)
def test_lifecycle_rounding_reaches_construction_diagnostic(case):
    source = LIFECYCLE_CASES[case]
    q = Fraction(1, 2**1075)
    expected = math.ulp(0.0)
    squared = 2*q*q
    assert (Fraction(expected)/2)**2 < squared < (3*Fraction(expected)/2)**2
    namespace = {}
    exec(compile(source, "<r13-runtime>", "exec"), namespace)
    actual = namespace["bad"](q)
    assert actual == 0.0 and actual != expected, (case, actual, expected)
    path = f"src/eab/r13_{case}_new.py"
    assert gate._subset.approved_sites(source, path) == set()
    issues = gate.scan_text(source, path)
    assert any(row[3] == "closed-rounded-construction" for row in issues), (case, issues)


@pytest.mark.parametrize("case", ["dataclass_post_init", "inherited_init", "instance_method_mutation"])
def test_equivalent_exact_lifecycle_stays_admissible(case):
    source = LIFECYCLE_CASES[case].replace("component*1.0", "component*1")
    issues = gate.scan_text(source, f"src/eab/r13_safe_{case}.py")
    assert issues == [], issues


@pytest.mark.parametrize("case", ["dataclass_post_init", "inherited_init", "instance_method_mutation", "property_setter"])
def test_internal_lifecycle_mutation_loses_the_target_diagnostic(case, tmp_path):
    replacements = {
        "dataclass_post_init": ("if generated_init and not own_init:", "if False and generated_init and not own_init:"),
        "inherited_init": ("return None if tail is None else [(module, cls), *tail]", "return None if tail is None else [(module, cls)]"),
        "instance_method_mutation": (
            "method_results.append(self._invoke(module, scope, node, env, method_owner, method,\n                                                                   [receiver, *args], keywords, [node.func.value, *node.args]))",
            "method_results.append(self._function(method_owner, method, [receiver, *args], keywords))"),
        "property_setter": ("if setters:", "if False and setters:"),
    }
    tools = tmp_path / "tools"
    tools.mkdir()
    for name in ("check_exact_construction.py", "exact_construction_flow.py", "exact_construction_subset.py", "exact_construction_policy.json"):
        text = (ROOT / "tools" / name).read_text(encoding="utf-8")
        if name == "exact_construction_flow.py":
            before, after = replacements[case]
            assert text.count(before) == 1, (case, before)
            text = text.replace(before, after)
        (tools / name).write_text(text, encoding="utf-8")
    spec = importlib.util.spec_from_file_location("r13_lifecycle_mutant", tools / "check_exact_construction.py")
    mutant = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mutant)
    source = LIFECYCLE_CASES[case]
    path = f"src/eab/r13_{case}_new.py"
    baseline = gate.scan_text(source, path, repository_root=ROOT)
    assert any(row[3] == "closed-rounded-construction" for row in baseline)
    issues = mutant.scan_text(source, path, repository_root=ROOT)
    # The defect is injected in the checker itself, not by appending fake output.
    # This is exactly the assertion from the regression test above.
    with pytest.raises(AssertionError, match="lifecycle rounding must reach construction"):
        assert any(row[3] == "closed-rounded-construction" for row in issues), "lifecycle rounding must reach construction"


@pytest.mark.parametrize("variant", ["inherited_method", "alias_method", "keyword_initializer", "cached_property"])
def test_related_lifecycle_shapes_preserve_field_rounding(variant):
    case = "instance_method_mutation" if variant in {"inherited_method", "alias_method"} else "inherited_init" if variant == "keyword_initializer" else "property_setter"
    source = LIFECYCLE_CASES[case]
    if variant == "inherited_method":
        source = source.replace("class Holder:", "class Parent:").replace("def bad(q: Fraction):", "@dataclass\nclass Holder(Parent):\n    points: tuple[Fraction, Fraction]\ndef bad(q: Fraction):")
    elif variant == "alias_method":
        source = source.replace("holder.update()", "alias = holder\n    alias.update()")
    elif variant == "keyword_initializer":
        source = source.replace("Holder((q,q))", "Holder(points=(q,q))")
    else:
        source = source.replace("holder.points = (q, q)", "before = holder.points\n    holder.points = (q, q)")
    namespace = {}
    exec(compile(source, "<r13-related-runtime>", "exec"), namespace)
    assert namespace["bad"](Fraction(1, 2**1075)) == 0.0
    issues = gate.scan_text(source, f"src/eab/r13_related_{variant}.py")
    assert any(row[3] == "closed-rounded-construction" for row in issues), (variant, issues)


def test_exact_normal_is_not_tainted_by_unrelated_position_field():
    source = """from dataclasses import dataclass
from fractions import Fraction
from eab.construction import norm_rational
@dataclass
class Holder:
    position: tuple[float, float]
    normal: tuple[Fraction, Fraction]
    def __post_init__(self):
        self.length = norm_rational(self.normal)
def safe(q: Fraction):
    return Holder((1.0*1.0, 2.0*2.0), (q, q)).length
"""
    assert gate.scan_text(source, "src/eab/r13_distinct_fields.py") == []


@pytest.mark.parametrize("annotation, argument, expected", [
    ("tuple[Fraction, Fraction]", "(q, q)", "exact"),
    ("tuple[Fraction, ...]", "()", "float"),
])
def test_type_guard_distinguishes_fixed_tuple_contract_from_empty_iterable(annotation, argument, expected):
    import ast
    source = f"""from fractions import Fraction
def guard(values: {annotation}):
    if all(type(x) is float for x in values):
        return 0.5
    return Fraction(1)
def caller(q: Fraction):
    return guard({argument})
"""
    analysis = gate._subset._flow.analyze(source, "src/eab/r13_type_guard.py")
    calls = [n for n in ast.walk(ast.parse(source)) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "guard"]
    assert len(calls) == 1
    # Fixed-tuple contract excludes the floating branch. A possibly empty
    # variadic tuple does not justify assuming all(False) is False.
    assert analysis.return_kind(calls[0]) == expected


def test_repository_scan_rejects_all_three_new_lifecycle_sources_without_waivers(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("r13")
    for folder in ("src", "tests", "tools"):
        shutil.copytree(ROOT / folder, tmp_path / folder,
                        ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
    paths = []
    for case in ("dataclass_post_init", "inherited_init", "instance_method_mutation"):
        path = f"src/eab/r13_{case}_new.py"
        paths.append(path)
        (tmp_path / path).write_text(LIFECYCLE_CASES[case], encoding="utf-8")
    assert (tmp_path / "tools/exact_construction_policy.json").read_bytes() == (ROOT / "tools/exact_construction_policy.json").read_bytes()
    issues = gate.scan_repository(tmp_path)
    reached = {row[0] for row in issues if row[3] == "closed-rounded-construction"}
    assert set(paths) <= reached, (set(paths) - reached, issues)



def test_undecorated_subclass_inherits_generated_dataclass_initialization():
    source = LIFECYCLE_CASES["dataclass_post_init"].replace("class Holder:", "class Parent:")
    source = source.replace("def bad(q: Fraction):", "class Holder(Parent):\n    pass\ndef bad(q: Fraction):")
    namespace = {}
    exec(compile(source, "<r13-inherited-dataclass>", "exec"), namespace)
    assert namespace["bad"](Fraction(1, 2**1075)) == 0.0
    issues = gate.scan_text(source, "src/eab/r13_inherited_generated_init.py")
    assert any(row[3] == "closed-rounded-construction" for row in issues), issues
