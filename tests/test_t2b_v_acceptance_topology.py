"""Lemma §2.0: nonadjacent self-contact is not licensed by exact partition area.

The independent two-lobe input has distinct vertices and two CCW triangles.
Their areas add exactly, and interiors do not overlap; only simplicity fails.
No production primitive or external mutation tool is used by this regression.
"""
import json
from pathlib import Path

from t2b_independent_cage_verifier import verify_cage


def test_a13_nonadjacent_self_contact_with_exact_partition_is_rejected():
    directory = Path(__file__).parent / "data/t2b_acceptance"
    instance = json.loads((directory / "topology_A13.instance.json").read_text(encoding="utf-8"))
    certificate = json.loads((directory / "topology_A13.cert.json").read_text(encoding="utf-8"))
    result = verify_cage(instance, certificate)
    assert result["valid"] is False, result
    assert result["condition"] == "V0", result
    assert result["where"]["check"] == "simple_ring", result
