"""M5b INT1 residue-zero and shared-domain semantic closure.

Numerical oracle imports: fractions.Fraction only. The polynomial (x-p)(x*x+p)
is expanded by integer arithmetic here, not by production polynomial helpers.
Static-policy oracles inspect literal import provenance and exact source pins;
hash-tripwire assertions are not the oracle for either internal mutant below.
"""
from fractions import Fraction as F
from pathlib import Path
import sys

import pytest
from mutation_support import mutated_function

from eab.kernel2d import algebraic as alg

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import check_exact_construction as gate


@pytest.mark.parametrize("prime", (2, 3, 5, 7))
def test_as_rational_modular_filter_includes_the_zero_residue(prime):
    # Modulo p, (x-p)(x*x+p) is x^3 and its ONLY root is residue 0. The
    # isolated real root is nonzero, avoiding a special zero-root shortcut.
    p = prime
    polynomial = (-p*p, p, -p, 1)
    assert [r for r in range(p) if sum(c*r**i for i, c in enumerate(polynomial)) % p == 0] == [0]
    root = alg.RealAlgebraic(polynomial, p-F(1, 4), p+F(1, 3))
    assert root.as_rational() == p, "M5b residue-zero modular root must survive the no-root filter"


def test_residue_zero_guard_kills_the_internal_nonzero_residues_only_mutant(monkeypatch):
    test_as_rational_modular_filter_includes_the_zero_residue(2)
    mutant = mutated_function(alg.RealAlgebraic.as_rational, alg,
                              (("value in range(prime)", "value in range(1, prime)"),))
    monkeypatch.setattr(alg.RealAlgebraic, "as_rational", mutant)
    # No frozen source/file hash callback occurs along this numerical path.
    with pytest.raises(AssertionError, match="M5b residue-zero modular root"):
        test_as_rational_modular_filter_includes_the_zero_residue(2)


@pytest.mark.parametrize("replacement", (
    "from unrelated_module import mutated_function, replace_module_callable",
    "from mutation_support import mutated_function, replace_module_callable\nmutated_function = foreign_helper",
))
def test_shared_instrumentation_binds_caller_helper_import_resolution(replacement):
    path = "tests/test_int1_semantics.py"
    source = (ROOT / path).read_text(encoding="utf-8")
    old = "from mutation_support import mutated_function, replace_module_callable"
    assert source.count(old) == 1
    subset = gate._subset
    assert subset.instrumentation_scope(source, path, "inject_semantic_mutation", "closed-dynamic-call")
    changed = source.replace(old, replacement)
    # The reviewed function's source is untouched. This exercises the new
    # import binding, not the already-existing function-body fingerprint.
    assert subset.site_contexts(changed)["inject_semantic_mutation"] == subset.site_contexts(source)["inject_semantic_mutation"]
    assert not subset.instrumentation_scope(changed, path, "inject_semantic_mutation", "closed-dynamic-call"), \
        "M5b caller helper import resolution must invalidate the shared review"


def test_import_binding_guard_kills_internal_ignored_module_pin_mutant(monkeypatch):
    replacement = "from unrelated_module import mutated_function, replace_module_callable"
    test_shared_instrumentation_binds_caller_helper_import_resolution(replacement)
    subset = gate._subset
    mutant = mutated_function(subset.instrumentation_scope, subset, ((
        'and row.get("module_context") == contexts.get("<module>")',
        'and True'), (
        'and row.get("module_source_sha256") == _hash(text.replace("\\r\\n", "\\n").replace("\\r", "\\n"))',
        'and True')))
    monkeypatch.setattr(subset, "instrumentation_scope", mutant)
    # Existing helper bytes and function pins remain valid in both runs;
    # the red assertion specifically requires caller import-source binding.
    with pytest.raises(AssertionError, match="M5b caller helper import resolution"):
        test_shared_instrumentation_binds_caller_helper_import_resolution(replacement)


@pytest.mark.parametrize("shadow", (
    "\ndef mutated_function(*args, **kwargs):\n    return 1\n",
    "\nclass mutated_function:\n    pass\n",
))
def test_shared_helper_import_binding_rejects_module_definition_shadowing(shadow):
    path = "tests/test_int1_semantics.py"
    source = (ROOT / path).read_text(encoding="utf-8")
    subset = gate._subset
    assert subset.instrumentation_scope(source, path, "inject_semantic_mutation", "closed-dynamic-call")
    changed = source + shadow
    # Direct definitions are excluded from the old non-definition module pin.
    # The imported helper spelling is nevertheless rebound by Python.
    before, after = subset.site_contexts(source), subset.site_contexts(changed)
    assert before["<module>"] == after["<module>"]
    assert before["inject_semantic_mutation"] == after["inject_semantic_mutation"]
    assert not subset.instrumentation_scope(changed, path, "inject_semantic_mutation", "closed-dynamic-call"), \
        "M5b direct def/class shadowing cannot inherit imported helper authorization"


def test_definition_shadowing_guard_kills_internal_missing_whole_caller_pin_mutant(monkeypatch):
    shadow = "\ndef mutated_function(*args, **kwargs):\n    return 1\n"
    test_shared_helper_import_binding_rejects_module_definition_shadowing(shadow)
    subset = gate._subset
    mutant = mutated_function(subset.instrumentation_scope, subset, ((
        'and row.get("module_source_sha256") == _hash(text.replace("\\r\\n", "\\n").replace("\\r", "\\n"))',
        'and True'),))
    monkeypatch.setattr(subset, "instrumentation_scope", mutant)
    with pytest.raises(AssertionError, match="M5b direct def/class shadowing"):
        test_shared_helper_import_binding_rejects_module_definition_shadowing(shadow)


def test_nonmutation_assertion_dispatch_and_hash_masking_are_not_shared_scopes():
    policy = gate._subset._policy()
    active = policy["mutation_instrumentation_reviews"][-1]
    assert not any(row["function"] in ("semantic_guard", "mask_source_hashes") for row in active["scopes"])
    assert "reflected float" in active["proof_domain"]
    assert "NOT covered" in active["proof_domain"]
