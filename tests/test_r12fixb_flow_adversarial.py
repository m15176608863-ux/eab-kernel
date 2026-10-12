"""R12FIXb adversarial first-order flow regressions.

The numeric oracle is the exact Fraction square comparison against binary64
midpoint cells; it does not use any eab geometry/construction primitive.
Each source actually executes the premature-rounding defect before scanning.
"""
from fractions import Fraction
import importlib.util
import math
from pathlib import Path
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("r12fixb_flow_adversarial_gate", ROOT / "tools/check_exact_construction.py")
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)

PREFIX = "from fractions import Fraction\nfrom eab.construction import norm_rational\n"
FLOW_DEFECTS = [
    ("computed_fractional_power_is_a_root_sink", PREFIX + (
        "def bad(q: Fraction):\n"
        "    rounded = (2*q*q)*1.0\n"
        "    exponent = 1/2\n"
        "    return rounded ** exponent\n"
    )),
    ("math_pow_fractional_exponent_is_a_root_sink", "import math\n" + PREFIX + (
        "def bad(q: Fraction):\n"
        "    rounded = (2*q*q)*1.0\n"
        "    return math.pow(rounded, 0.5)\n"
    )),
    ("math_namespace_parameter_shadow", "import math\n" + PREFIX + (
        "def bad(math, q):\n"
        "    rounded = math.isfinite(q)\n"
        "    return norm_rational((rounded, rounded))\n"
    )),
    ("math_import_alias_parameter_shadow", "from math import isfinite as safe\n" + PREFIX + (
        "def bad(safe, q):\n"
        "    rounded = safe(q)\n"
        "    return norm_rational((rounded, rounded))\n"
    )),
    ("closure_captured_rounded_number", PREFIX + (
        "def bad(q: Fraction):\n"
        "    rounded = q*1.0\n"
        "    def read():\n"
        "        return rounded\n"
        "    return norm_rational((read(), read()))\n"
    )),
    ("mutable_list_alias_append", PREFIX + (
        "def bad(q: Fraction):\n"
        "    box = []\n"
        "    alias = box\n"
        "    alias.append(q*1.0)\n"
        "    alias.append(q*1.0)\n"
        "    return norm_rational(box)\n"
    )),
    ("for_break_unreachable_reset", PREFIX + (
        "def bad(q: Fraction):\n"
        "    rounded = q\n"
        "    for item in range(1):\n"
        "        rounded = q*1.0\n"
        "        break\n"
        "        rounded = q\n"
        "    return norm_rational((rounded, rounded))\n"
    )),
    ("for_continue_unreachable_reset", PREFIX + (
        "def bad(q: Fraction):\n"
        "    rounded = q\n"
        "    for item in range(1):\n"
        "        rounded = q*1.0\n"
        "        continue\n"
        "        rounded = q\n"
        "    return norm_rational((rounded, rounded))\n"
    )),
    ("try_raise_unreachable_reset", PREFIX + (
        "def bad(q: Fraction):\n"
        "    rounded = q\n"
        "    try:\n"
        "        rounded = q*1.0\n"
        "        raise ValueError()\n"
        "        rounded = q\n"
        "    except ValueError:\n"
        "        pass\n"
        "    return norm_rational((rounded, rounded))\n"
    )),
    ("for_else_must_not_run_after_break", PREFIX + (
        "def bad(q: Fraction):\n"
        "    rounded = q\n"
        "    for item in range(1):\n"
        "        rounded = q*1.0\n"
        "        break\n"
        "    else:\n"
        "        rounded = q\n"
        "    return norm_rational((rounded, rounded))\n"
    )),
    ("conditional_break_keeps_exit_state", PREFIX + (
        "def bad(q: Fraction):\n"
        "    rounded = q\n"
        "    for item in range(1):\n"
        "        if True:\n"
        "            rounded = q*1.0\n"
        "            break\n"
        "        rounded = q\n"
        "    return norm_rational((rounded, rounded))\n"
    )),
    ("conditional_continue_keeps_backedge_state", PREFIX + (
        "def bad(q: Fraction):\n"
        "    rounded = q\n"
        "    for item in range(1):\n"
        "        if True:\n"
        "            rounded = q*1.0\n"
        "            continue\n"
        "        rounded = q\n"
        "    return norm_rational((rounded, rounded))\n"
    )),
    ("try_else_must_not_run_after_exception", PREFIX + (
        "def bad(q: Fraction):\n"
        "    rounded = q\n"
        "    try:\n"
        "        rounded = q*1.0\n"
        "        raise ValueError()\n"
        "    except ValueError:\n"
        "        pass\n"
        "    else:\n"
        "        rounded = q\n"
        "    return norm_rational((rounded, rounded))\n"
    )),
    ("exception_handler_sees_prefix_state", PREFIX + (
        "def bad(q: Fraction):\n"
        "    rounded = q\n"
        "    try:\n"
        "        rounded = q*1.0\n"
        "        unused = 1//0\n"
        "        rounded = q\n"
        "    except ZeroDivisionError:\n"
        "        pass\n"
        "    return norm_rational((rounded, rounded))\n"
    )),
    ("typed_helper_mutates_shared_container", PREFIX + (
        "def alter(box: list[Fraction], q: Fraction):\n"
        "    box.append(q*1.0)\n"
        "    box.append(q*1.0)\n"
        "def bad(q: Fraction):\n"
        "    box = []\n"
        "    alter(box, q)\n"
        "    return norm_rational(box)\n"
    )),
    ("nested_default_captures_definition_time_value", PREFIX + (
        "def bad(q: Fraction):\n"
        "    rounded = q*1.0\n"
        "    def read(x=rounded):\n"
        "        return x\n"
        "    rounded = q\n"
        "    return norm_rational((read(), read()))\n"
    )),
    ("module_default_captures_definition_time_value", PREFIX + (
        "q = Fraction(1, 2**1075)\n"
        "rounded = q*1.0\n"
        "def read(x=rounded):\n"
        "    return x\n"
        "rounded = q\n"
        "def bad(ignored):\n"
        "    return norm_rational((read(), read()))\n"
    )),
    ("module_rebinding_does_not_rewrite_prior_snapshot", PREFIX + (
        "q = Fraction(1, 2**1075)\n"
        "rounded = q*1.0\n"
        "retained = rounded\n"
        "rounded = q\n"
        "def bad(ignored):\n"
        "    return norm_rational((retained, retained))\n"
    )),
    ("class_annotation_does_not_hide_rounded_initializer", PREFIX + (
        "class Holder:\n"
        "    value: Fraction = Fraction(1, 2**1075)*1.0\n"
        "def bad(ignored):\n"
        "    holder = Holder()\n"
        "    return norm_rational((holder.value, holder.value))\n"
    )),
    ("function_definition_shadows_math_import", "from math import isfinite\n" + PREFIX + (
        "def isfinite(q):\n"
        "    return q*1.0\n"
        "def bad(q):\n"
        "    rounded = isfinite(q)\n"
        "    return norm_rational((rounded, rounded))\n"
    )),
    ("nested_definition_shadows_math_import", "from math import isfinite\n" + PREFIX + (
        "def bad(q):\n"
        "    def isfinite(value):\n"
        "        return value*1.0\n"
        "    rounded = isfinite(q)\n"
        "    return norm_rational((rounded, rounded))\n"
    )),
    ("class_definition_shadows_math_namespace", "import math\n" + PREFIX + (
        "class math:\n"
        "    def isfinite(q):\n"
        "        return q*1.0\n"
        "def bad(q):\n"
        "    rounded = math.isfinite(q)\n"
        "    return norm_rational((rounded, rounded))\n"
    )),
    ("dataclass_annotation_does_not_hide_actual_float_argument", "from dataclasses import dataclass\n" + PREFIX + (
        "from eab.construction import sqrt_rational\n"
        "@dataclass\n"
        "class Holder:\n"
        "    x: Fraction\n"
        "def bad(q: float):\n"
        "    holder = Holder(q)\n"
        "    return sqrt_rational(holder.x*holder.x)\n"
    )),
    ("custom_init_annotation_does_not_hide_rounded_field", PREFIX + (
        "class Holder:\n"
        "    x: Fraction\n"
        "    def __init__(self, q):\n"
        "        self.x = q*1.0\n"
        "def bad(q: Fraction):\n"
        "    holder = Holder(q)\n"
        "    return norm_rational((holder.x, holder.x))\n"
    )),
    ("typed_helper_mutates_shared_record_field", "from dataclasses import dataclass\n" + PREFIX + (
        "@dataclass\n"
        "class Holder:\n"
        "    x: Fraction\n"
        "def assign(holder: Holder, q: Fraction):\n"
        "    holder.x = q*1.0\n"
        "def bad(q: Fraction):\n"
        "    holder = Holder(q)\n"
        "    assign(holder, q)\n"
        "    return norm_rational((holder.x, holder.x))\n"
    )),
]


@pytest.mark.parametrize("path", ["src/eab/r12fixb_flow_probe.py", "tests/r12fixb_flow_helper.py"])
@pytest.mark.parametrize("label,source", FLOW_DEFECTS, ids=[row[0] for row in FLOW_DEFECTS])
def test_first_order_flow_does_not_hide_executed_rounding(path, label, source):
    namespace = {}
    exec(compile(source, "<R12FIXb actual premature-rounding source>", "exec"), namespace)
    q = Fraction(1, 2**1075)
    u = math.ulp(0.0)
    # Exact independent oracle: two exact q components must round to u, not 0.
    assert (Fraction(u)/2)**2 < 2*q*q < (3*Fraction(u)/2)**2
    if label == "math_namespace_parameter_shadow":
        answer = namespace["bad"](SimpleNamespace(isfinite=lambda x: x*1.0), q)
    elif label == "math_import_alias_parameter_shadow":
        answer = namespace["bad"](lambda x: x*1.0, q)
    elif label == "dataclass_annotation_does_not_hide_actual_float_argument":
        # Here the raw float input is valid; only x*x prematurely underflows.
        # sqrt(Fraction(u)**2) lies exactly at representable u, independently
        # of the construction primitive used by the implanted implementation.
        assert (Fraction(u)/2)**2 < Fraction(u)**2 < (3*Fraction(u)/2)**2
        answer = namespace["bad"](u)
    else:
        answer = namespace["bad"](q)
    assert answer == 0.0 and answer != u, (label, answer, u)
    issues = gate.scan_text(source, path)
    assert issues, ("R12FIXb executed first-order rounding must be rejected", label, path)
    assert any(row[2].startswith("bad") for row in issues), (label, path, issues)
