"""Final mechanism probes: power sinks use full CFG and pins cannot collide.

Power oracle: independent Fraction midpoint cells around the supplied float q,
not any eab geometric/construction primitive. The implanted code really loses
q*q through underflow before a computed exponent or math.pow root.
"""
from fractions import Fraction
import importlib.util
import math
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("r12fixb_final_gate", ROOT / "tools/check_exact_construction.py")
gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gate)

CFG_BODIES = [
    ("break_skips_for_else", (
        "    r=q\n"
        "    for i in range(1):\n"
        "        r=q*q\n"
        "        break\n"
        "    else:\n"
        "        r=q\n"
    )),
    ("exception_prefix_survives", (
        "    r=q\n"
        "    try:\n"
        "        r=q*q\n"
        "        unused=1//0\n"
        "        r=q\n"
        "    except ZeroDivisionError:\n"
        "        pass\n"
    )),
]


@pytest.mark.parametrize("path", ["src/eab/final_power_probe.py", "tests/final_power_probe.py"])
@pytest.mark.parametrize("root", ["r**(1/2)", "math.pow(r, .5)", "augmented_power"])
@pytest.mark.parametrize("label,body", CFG_BODIES, ids=[row[0] for row in CFG_BODIES])
def test_power_roots_reject_rounding_retained_by_real_control_flow(path, root, label, body):
    ending = "    r **= (1/2)\n    return r\n" if root == "augmented_power" else "    return " + root + "\n"
    source = "import math\ndef bad(q:float):\n" + body + ending
    namespace = {}
    exec(compile(source, "<actual premature square before root>", "exec"), namespace)
    q = 1e-200
    exact_square = Fraction(q) ** 2
    midpoint_lo = (Fraction(math.nextafter(q, -math.inf)) + Fraction(q)) / 2
    midpoint_hi = (Fraction(q) + Fraction(math.nextafter(q, math.inf))) / 2
    assert 0 < midpoint_lo ** 2 < exact_square < midpoint_hi ** 2
    # Hence the correctly rounded exact root is the representable q, not zero.
    assert namespace["bad"](q) == 0.0 and q != 0.0
    issues = gate.scan_text(source, path)
    assert any(row[2:4] == ("bad", "closed-rounded-construction") for row in issues), (label, root, path, issues)


def test_repeated_qualified_definitions_cannot_overwrite_the_first_source_pin():
    source = (
        "def choose(flag):\n"
        "    if flag:\n"
        "        def read(record):\n"
        "            note = 1\n"
        "            return getattr(record, 'first')\n"
        "    else:\n"
        "        def read(record):\n"
        "            note = 2\n"
        "            return getattr(record, 'second')\n"
        "    return read\n"
        "def unrelated(record):\n"
        "    return getattr(record, 'label')\n"
    )
    before = gate._subset.site_contexts(source)
    after = gate._subset.site_contexts(source.replace("note = 1", "note = 3"))
    assert before["choose.read"] != after["choose.read"], "same-name branches must not erase the first reviewed definition's source pin"
    assert before["unrelated"] == after["unrelated"], "collision fix must stay lexical, not lock the module"


@pytest.mark.parametrize("path", ["src/eab/final_return_probe.py", "tests/final_return_probe.py"])
@pytest.mark.parametrize("operation", ["math_sin", "math_prod", "helper_return"])
@pytest.mark.parametrize("label,body", CFG_BODIES, ids=[row[0] for row in CFG_BODIES])
def test_rounded_call_or_helper_return_survives_control_flow(path, operation, label, body):
    prefix = "import math\nfrom eab.construction import norm_rational\n"
    if operation == "helper_return":
        source = (prefix + "def helper(q:float):\n" + body + "    return r\n"
                  "def bad(q:float):\n    return norm_rational((helper(q),helper(q)))\n")
    else:
        expression = "math.sin(q)" if operation == "math_sin" else "math.prod((q,q))"
        source = (prefix + "def bad(q:float):\n" + body.replace("r=q*q", "r=" + expression)
                  + "    return norm_rational((r,r))\n")
    namespace = {}
    exec(compile(source, "<actual rounded function result through CFG>", "exec"), namespace)
    if operation == "math_sin":
        # This is a policy-flow tooth for a rounded transcendental result; it
        # does not pretend that a float math.sin is an independent exact oracle.
        assert namespace["bad"](0.1) > 0
    else:
        q, u = 1.5e-162, math.ulp(0.0)
        squared = 2 * (Fraction(q) ** 2) ** 2
        assert (Fraction(u) / 2) ** 2 < squared < (3 * Fraction(u) / 2) ** 2
        # Both actual q*q and math.prod underflow, while the exact two-component
        # construction lies inside the binary64 rounding cell of u.
        assert namespace["bad"](q) == 0.0 and u > 0.0
    issues = gate.scan_text(source, path)
    assert any(row[2] == "bad" for row in issues), (label, operation, path, issues)


@pytest.mark.parametrize("path", ["src/eab/final_nested_probe.py", "tests/final_nested_probe.py"])
@pytest.mark.parametrize("transfer", ["break", "continue"])
def test_nested_loop_transfer_cannot_erase_a_helper_return_summary(path, transfer):
    source = (
        "from eab.construction import norm_rational\n"
        "def helper(q:float):\n"
        "    r=q\n"
        "    for _ in range(1):\n"
        "        if True:\n"
        "            r=q*q\n"
        f"            {transfer}\n"
        "        r=q\n"
        "    return r\n"
        "def bad(q:float):\n"
        "    return norm_rational((helper(q),helper(q)))\n"
    )
    namespace = {}
    exec(compile(source, "<actual nested loop exit before clean overwrite>", "exec"), namespace)
    q, u = 1.5e-162, math.ulp(0.0)
    squared = 2 * (Fraction(q) ** 2) ** 2
    assert (Fraction(u) / 2) ** 2 < squared < (3 * Fraction(u) / 2) ** 2
    assert namespace["bad"](q) == 0.0 and u > 0.0
    issues = gate.scan_text(source, path)
    assert any(row[2] == "bad" for row in issues), (transfer, path, issues)


@pytest.mark.parametrize("path", ["src/eab/final_with_probe.py", "tests/final_with_probe.py"])
def test_suppressed_exception_prefix_cannot_erase_a_helper_return_summary(path):
    source = (
        "import pytest\n"
        "from eab.construction import norm_rational\n"
        "def helper(q:float):\n"
        "    r=q\n"
        "    with pytest.raises(type(ZeroDivisionError())):\n"
        "        r=q*q\n"
        "        unused=1//0\n"
        "        r=q\n"
        "    return r\n"
        "def bad(q:float):\n"
        "    return norm_rational((helper(q),helper(q)))\n"
    )
    namespace = {}
    exec(compile(source, "<actual suppressed exception before clean overwrite>", "exec"), namespace)
    q, u = 1.5e-162, math.ulp(0.0)
    squared = 2 * (Fraction(q) ** 2) ** 2
    assert (Fraction(u) / 2) ** 2 < squared < (3 * Fraction(u) / 2) ** 2
    assert namespace["bad"](q) == 0.0 and u > 0.0
    issues = gate.scan_text(source, path)
    assert any(row[2] == "bad" for row in issues), (path, issues)
