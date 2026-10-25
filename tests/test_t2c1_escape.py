"""T2c1 proposal orchestration gates, not independent geometry proofs.

The finite audit uses the existing private interpolation/Sturm/G0 oracle;
its primitives differ from production SE2 event construction. Fine-grid
smokes use an analytically unobstructed vertical corridor and exact endpoint
arithmetic. No failed proposal is interpreted as non-escape.
"""
from fractions import Fraction as F
from pathlib import Path
import json
import time

import pytest

import t2c_escape_proposer as proposer


def test_finite_oracle_scope_is_not_escape():
    rows = json.loads((Path(__file__).parent / "data/t2a_escape_replay.json").read_text(encoding="utf-8"))["cases"]
    candidate = next(row for row in rows if row["geometry"]["kind"] == "doorway")
    instance = dict(moving=tuple(tuple(F(x) for x in p) for p in candidate["moving"]),
                    obstacles=tuple(tuple(tuple(F(x) for x in p) for p in ring) for ring in candidate["obstacles"]))
    audit = proposer.audit_proposal(instance, candidate)
    assert audit["status"] == "FINITE_ORACLE_VERIFIED"
    assert audit["production"]["valid"] and audit["production"]["ray_valid"]
    assert audit["production"]["checked_segments"] == 3
    assert audit["production"]["checked_pairs"] == 15
    assert audit["independent"]["se2_pair_checks"] == 15
    assert audit["independent"]["ray_prefix_pair_checks"] == 5
    assert audit["independent"]["first_contact_calls"] == 20
    assert audit["independent"]["infinite_ray_verified"] is False
    assert audit["eligible_new_upper"] is False and audit["pending_owner_scope_ruling"]
    assert all(row["status"] == "FREE" and row["exact_time"] is None
               for row in audit["independent"]["pairs"])


def test_sparse_grid_really_uses_one_over_400_and_exact_source(monkeypatch, tmp_path):
    moving = ((F(0), F(0)), (F(1), F(0)), (F(1), F(1)), (F(0), F(1)))
    obstacles = (((F(10), F(2)), (F(11), F(2)), (F(11), F(3)), (F(10), F(3))),)
    end = tuple((x, y+4) for x, y in moving)
    seed = dict(moving=moving, pieces=[dict(start=moving, end=end, u1=0,
                                          translation=(0, 4), center=(0, 0))])
    monkeypatch.setattr(proposer, "geometry", lambda _: (moving, obstacles))
    result = proposer.propose_escape("k01", F(1, 4), seed,
                                    resources=proposer.EscapeResources(steps=(F(1, 400),),
                                        tube_radius=1, max_cells=100000, max_seconds=20), output=tmp_path)
    assert result["status"] == "PROPOSAL_UNVERIFIED"
    assert result["diagnostic"]["actual_grid_step"] == F(1, 400)
    assert result["attempts"][0]["cells"] > 1000
    assert result["diagnostic"]["grid_nodes"] > 1000
    assert result["pieces"][0]["start"] == moving
    assert result["pieces"][-1]["end"][0][1] > 3
    audit = proposer.audit_proposal(dict(moving=moving, obstacles=obstacles), result)
    assert audit["production"]["valid"] and audit["independent"]["valid"]
    assert not audit["eligible_new_upper"]
    saved = json.loads((tmp_path / "proposal.json").read_text(encoding="utf-8"))
    assert saved["diagnostic"]["actual_grid_step"] == "1/400"


@pytest.mark.parametrize("limit,reason", [("time", "elapsed_time_limit"), ("cells", "guide_node_limit"),
                                          ("path", "path_node_limit")])
def test_proposal_resource_limits_are_unproved(monkeypatch, limit, reason):
    moving = ((F(0), F(0)), (F(1), F(0)), (F(1), F(1)), (F(0), F(1)))
    obstacles = (((F(10), F(2)), (F(11), F(2)), (F(11), F(3)), (F(10), F(3))),)
    seed = dict(moving=moving, pieces=[dict(start=moving, end=tuple((x, y+4) for x, y in moving),
                                          u1=0, translation=(0, 4), center=(0, 0))])
    monkeypatch.setattr(proposer, "geometry", lambda _: (moving, obstacles))
    resources = proposer.EscapeResources(max_seconds=-1 if limit == "time" else 20,
        max_cells=0 if limit == "cells" else 100000,
        max_path_nodes=0 if limit == "path" else 200000, steps=(F(1, 20),), tube_radius=1)
    result = proposer.propose_escape("k01", F(1, 4), seed, resources=resources)
    assert result["status"] == "UNPROVED"
    assert result["attempts"][-1]["reason"] == reason
    assert "pieces" not in result


def test_overdue_candidate_is_discarded(monkeypatch):
    moving = ((F(0), F(0)), (F(1), F(0)), (F(1), F(1)), (F(0), F(1)))
    obstacles = (((F(10), F(2)), (F(11), F(2)), (F(11), F(3)), (F(10), F(3))),)
    seed = dict(moving=moving, pieces=[dict(start=moving, end=tuple((x, y+4) for x, y in moving),
                                          u1=0, translation=(0, 4), center=(0, 0))])
    monkeypatch.setattr(proposer, "geometry", lambda _: (moving, obstacles))
    original = proposer.rationalize
    expired = [False]
    def late_rationalize(path, spec):
        result = original(path, spec)
        expired[0] = True
        return result
    monkeypatch.setattr(proposer, "rationalize", late_rationalize)
    original_clock = time.perf_counter
    monkeypatch.setattr(proposer.time, "perf_counter", lambda: original_clock()+100 if expired[0] else original_clock())
    result = proposer.propose_escape("k01", F(1, 4), seed,
        resources=proposer.EscapeResources(max_seconds=20, steps=(F(1, 20),), tube_radius=1))
    assert result["status"] == "UNPROVED" and "pieces" not in result
    assert result["attempts"][-1]["reason"] == "elapsed_time_limit"


def test_failure_bisection_never_raises_cage_lower_or_changes_upper(monkeypatch):
    seen = []
    def fail(case_id, delta, seed, **kwargs):
        seen.append(delta)
        return dict(status="UNPROVED", attempts=[dict(reason="tube_cell_limit")])
    monkeypatch.setattr(proposer, "propose_escape", fail)
    result = proposer.refine_escape("k01", F(1, 4), F(1, 2), {}, exponent=12, max_probes=3)
    assert seen == [F(3, 8), F(7, 16), F(15, 32)]
    assert result["certified_lower"] == F(1, 4)
    assert result["certified_upper"] == result["exploratory_upper"] == F(1, 2)
    assert result["unproved_search_boundary"] == F(15, 32)
    assert not result["eligible_new_upper"]


def test_finite_verified_candidate_is_not_silently_promoted(monkeypatch):
    candidate = dict(status="PROPOSAL_UNVERIFIED", attempts=[], moving=(), obstacles=())
    monkeypatch.setattr(proposer, "propose_escape", lambda *args, **kwargs: candidate)
    monkeypatch.setattr(proposer, "audit_proposal", lambda *args: {"finite_and_production_valid": True})
    result = proposer.refine_escape("k01", F(1, 4), F(1, 2), {}, exponent=12, max_probes=2)
    assert result["certified_lower"] == F(1, 4) and result["certified_upper"] == F(1, 2)
    assert result["exploratory_upper"] == F(5, 16)
    assert result["status"] == "FINITE_ORACLE_VERIFIED" and not result["eligible_new_upper"]


def test_audit_rejects_geometry_substitution_and_bad_seed_join():
    moving = ((F(0), F(0)), (F(1), F(0)), (F(1), F(1)), (F(0), F(1)))
    seed = dict(moving=moving, obstacles=(), pieces=[dict(start=moving,
        end=tuple((x, y+1) for x, y in moving), u1=0, translation=(0, 1), center=(0, 0))],
        ray_path=((0, 0), (0, 100)))
    with pytest.raises(ValueError, match="geometry differs"):
        proposer.audit_proposal(dict(moving=(), obstacles=()), seed)
    seed["pieces"][0]["end"] = moving
    with pytest.raises(ValueError, match="endpoint differs"):
        proposer._seed_waypoints(seed)
