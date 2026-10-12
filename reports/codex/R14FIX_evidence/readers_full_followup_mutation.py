"""Re-run the migrated angle-domain tooth without changing source bytes."""
import hashlib
import json
from pathlib import Path
import sys
import traceback

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "tests")]

import pytest
from fractions import Fraction
import test_r13fixb_readers_oracles as gate


paths = [ROOT / "src/eab/adapters/bdda2d.py",
         ROOT / "tests/test_r13fixb_readers_oracles.py"]
before = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
with pytest.MonkeyPatch.context() as patch:
    mutant = gate._mutate(
        patch, gate.adapter,
        ('check_input(q, "bdda2d.cone_tol.h1_degrees")',
         'check_input(self.h1_degrees, "bdda2d.cone_tol.h1_degrees")'),
        ('pass  # removed eager angle guard', 'pass  # removed use-time angle guard'))
    gate.test_cone_coefficient_outside_declared_angle_domain_is_loud(Fraction(2)**-1074)
    patch.setattr(gate, "adapter", mutant)
    try:
        gate.test_cone_coefficient_outside_declared_angle_domain_is_loud(Fraction(2)**-1074)
    except pytest.fail.Exception as error:
        assert "DID NOT RAISE" in str(error)
        detail = traceback.format_exc()
    else:
        raise AssertionError("angle-domain mutation escaped its original assertion")
after = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
assert before == after
(HERE / "readers_full_followup_mutation.log").write_text(detail, encoding="utf-8")
(HERE / "readers_full_followup_mutation.json").write_text(
    json.dumps(dict(target="test_cone_coefficient_outside_declared_angle_domain_is_loud",
                    input="Fraction(2)**-1074", outcome="DID NOT RAISE ConstructionDomainError",
                    removed_guards=2, source_bytes_restored=True, sha256=after), indent=2) + "\n",
    encoding="utf-8")
print("both actual angle-domain guards removed: original DID NOT RAISE assertion red; source bytes unchanged")
