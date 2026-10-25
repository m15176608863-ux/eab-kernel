"""Synchronize an authorized count without weakening historical projection.

The literal source fingerprint protects the pre-existing view algorithm and
all other counts. Separate live-data mutations exercise its actual count guard;
these are history-contract checks, not numerical mutation evidence.
"""
import copy
import hashlib
import json
from pathlib import Path

import pytest
from policy_history_view import COUNTS, historical_view

ROOT = Path(__file__).resolve().parents[1]


def test_only_authorized_history_view_count_changes():
    source = (ROOT / "tools/policy_history_view.py").read_text("utf-8")
    t2b_note = "# T2b 所有者 2026-10-26 追认: 3659 historical plus 98 reviewed sites; no projection change.\n"
    assert source.count(t2b_note) == 1 and source.count('"waivers": 3757') == 1
    source = source.replace(t2b_note, "").replace('"waivers": 3757', '"waivers": 3659')
    note = "# T2a owner-approved append: 3522 historical plus 137 reviewed sites; no projection change.\n"
    assert source.count(note) == 1 and source.count('"waivers": 3659') == 1
    original = source.replace(note, "").replace('"waivers": 3659', '"waivers": 3522')
    assert hashlib.sha256(original.encode("utf-8")).hexdigest() == \
        "608ae6c7909a8f8338fa3f918c299eeb92cd8d0e8eed00a284cc3fc3e412386d"
    ledger = json.loads((ROOT / "reports/codex/T2a_evidence/static_admissions.json").read_text("utf-8"))
    t2b_ledger = json.loads((ROOT / "reports/codex/T2b_evidence/static_admissions.json").read_text("utf-8"))
    assert COUNTS == {"imports": 648, "members": 432, "waivers": 3522+ledger["counts"]["total"]+t2b_ledger["counts"]["total"],
                      "renewals": 106, "mutation_instrumentation_reviews": 2}


@pytest.mark.parametrize("append", [False, True])
def test_historical_view_still_rejects_unapproved_live_counts(append):
    policy = json.loads((ROOT / "tools/exact_construction_policy.json").read_text("utf-8"))
    relocation = json.loads((ROOT / "tools/exact_construction_relocations.json").read_text("utf-8"))
    historical_view(policy, relocation)
    changed = copy.deepcopy(policy)
    if append:
        changed["waivers"].append(copy.deepcopy(changed["waivers"][-1]))
    else:
        changed["waivers"].pop()
    with pytest.raises(AssertionError, match="H1 static admissions are frozen"):
        historical_view(changed, relocation)
