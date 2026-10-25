"""Read frozen admission history through the proved H1 namespace relocation.

Historical fingerprints remain unchanged. Only explicitly recorded namespace
and source-context fields can be projected back; reasons, rules, AST nodes and
grant counts cannot be normalized away. The scanner reads the live policy,
never this historical view.
"""
import copy
import json
from pathlib import Path


# T2a owner-approved append: 3522 historical plus 137 reviewed sites; no projection change.
COUNTS = {"imports": 648, "members": 432, "waivers": 3659,
          "renewals": 106, "mutation_instrumentation_reviews": 2}


def allowed_pointer(pointer):
    if pointer[0] in ("imports", "members"):
        return len(pointer) == 2 and isinstance(pointer[1], int)
    if pointer[0] == "waivers":
        return len(pointer) == 3 and pointer[-1] in ("path", "context")
    if pointer[0] == "renewals":
        return len(pointer) == 3 and pointer[-1] == "old_row_sha256"
    if pointer[0] in ("mutation_instrumentation_review", "mutation_instrumentation_reviews"):
        return "scopes" in pointer and pointer[-1] in ("module_context", "module_source_sha256")
    return False


def historical_view(policy, relocation):
    assert relocation["schema"] == "eab.h1-policy-relocation.v1"
    assert relocation["baseline_commit"].startswith("1ce9a91")
    assert {key: len(policy[key]) for key in COUNTS} == COUNTS, "H1 static admissions are frozen"
    result = copy.deepcopy(policy)
    seen = set()
    for row in relocation["changes"]:
        pointer = row["pointer"]
        assert tuple(pointer) not in seen and allowed_pointer(pointer), "unapproved relocation field"
        seen.add(tuple(pointer))
        parent = result
        for key in pointer[:-1]:
            parent = parent[key]
        assert parent[pointer[-1]] == row["new"], "unapproved change to a mechanically relocated field"
        parent[pointer[-1]] = row["old"]
    return result


def accepted_policy(root):
    root = Path(root)
    policy = json.loads((root / "tools/exact_construction_policy.json").read_text("utf-8"))
    relocation = json.loads((root / "tools/exact_construction_relocations.json").read_text("utf-8"))
    return historical_view(policy, relocation)
