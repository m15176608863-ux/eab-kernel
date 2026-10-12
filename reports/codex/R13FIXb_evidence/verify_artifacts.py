"""Final, rerunnable artifact/set/hash/link and distinct-output verification.

This is an evidence command, not a substitute for the frozen full pytest run.
The reader builders/assertions come from the independent test-owned rational
fixtures; no production geometry is used to compute their expected values.
"""
import ast
from collections import Counter
from fractions import Fraction as F
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))


def load(name):
    return json.loads((HERE / name).read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def distinct_outputs():
    from eab.kernel2d import geom as g2
    from eab.kernel3d import geom3 as g3
    spec = importlib.util.spec_from_file_location("r13b_reader_evidence", ROOT / "tests/test_r13fixb_readers_oracles.py")
    gates = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gates)
    families = {}

    def record(name, value):
        # repr retains every exact Fraction and binary64 value; no decimal
        # tolerance is used for the distinctness assertion.
        families.setdefault(name, []).append(repr(value))

    for exponent in (-400, 0, 396):
        s = F(2)**exponent
        points = [(0, 0), (3*s, 0), (3*s, 4*s), (0, 4*s)]
        p = g3.box(center=(s*F(3, 2), 2*s, 6*s), half=(s*F(3, 2), 2*s, 6*s))
        metrics = p.metrics()
        assert metrics == (12*s, float(13*s), float(3*s))
        assert g2.round_floor(4*s) == float(F(2)**-46*4*s)
        assert g3.noise_floor(12*s) == float(F(2)**-46*12*s)
        for name, value in {
            "2d.coordinate_scale": g2.coord_scale(points),
            "2d.rounding_floor": g2.round_floor(4*s),
            "2d.effective_tolerance": g2.eff_tol(s/2, points),
            "2d.negation": g2.neg(points[2]),
            "2d.reflection": g2.reflect(points),
            "3d.metrics": metrics,
            "3d.coordinate_scale": g3.coord_scale(*p.verts),
            "3d.noise_floor": g3.noise_floor(12*s),
            "3d.negation": g3.neg(p.verts[6]),
            "3d.reflection": p.reflected().verts,
            "3d.exact_vector": g3.exact_vector((float(s), 3*s, 0)),
            "3d.exact_edge": g3.exact_edge_vector(p, (0, 1)),
            "3d.exact_normal": g3.exact_face_normal(p, 0),
            "3d.interior_point": p.interior_point(),
            "3d.tetra": g3.tetra((0, 0, 0), (3*s, 0, 0), (0, 4*s, 0), (0, 0, 12*s)).verts,
            "3d.triangle_intersection": g3.exact_triangle_intersection(points3 := [(0, 0, 0), (3*s, 0, 0), (0, 4*s, 0)], points3),
        }.items():
            record(name, value)
        # Dimensionless constructions should NOT be made artificially distinct.
        assert g2.angle_floor(4*s, 3*s) == float(F(2)**-46*F(4, 3))
        assert g2.turn_floor(points, 0) == float(F(2)**-46*F(4, 3))

    folder = HERE / "tmp" / "artifact_distinctness"
    for i, scale in enumerate(gates.SCALES):
        tmp = folder / str(i)
        tmp.mkdir(parents=True, exist_ok=True)
        for test in (
            gates.test_bdda3d_both_public_readers_preserve_every_numeric_field,
            gates.test_bdda_df_all_numeric_and_raw_fields_match_independent_rationals,
            gates.test_geometry_readers_and_identity_accessors_preserve_values,
            gates.test_tf_both_readers_preserve_all_numeric_fields,
            gates.test_adapter_detection_and_window_have_independent_rational_values,
        ):
            test(tmp, scale)
        c, verts = gates._entrance(scale)
        g = gates.bdda_geom.load_step_geometries(tmp / "verts.csv", dup_tol=0)[13]
        for name, value in {
            "bdda3d.record": gates.bdda3d.record_from_entrance(c, verts=verts),
            "bdda3d.load": gates.bdda3d.load_records(tmp / "entrances.json"),
            "bdda.contacts": gates.bdda_df.read_contacts_csv(tmp / "bdda_debug_contacts.csv"),
            "bdda.df18_text": gates.bdda_df.read_df18_csv(tmp / "bdda_debug_df18.csv"),
            "bdda.df22": gates.bdda_df.read_df22_csv(tmp / "bdda_debug_df22.csv"),
            "bdda.vertices": gates.bdda_df.read_verts_csv(tmp / "verts.csv"),
            "bdda.load": gates.bdda_df.load_records(tmp),
            "geometry.load": g,
            "geometry.vertex_positions": g.vertex_pos(),
            "tf.load": gates.tf_probe.load_records(tmp / "probe.tsv"),
            "tf.stage": gates.tf_probe.read_pair_stage(tmp / "stage.tsv"),
            "adapter.window": gates.adapter.load_window(tmp, 13),
        }.items():
            record(name, value)
    for name, values in families.items():
        assert len(values) == len(set(values)) == 3, name
    return {name: {"distinct_count": len(set(values)), "output_sha256": [hashlib.sha256(v.encode()).hexdigest() for v in values]}
            for name, values in families.items()}


def main():
    run = os.environ.get("R13B_ACCEPTED_RUN", "full_suite_verified")
    suite = load(run + "/summary.json")
    assert suite["status"] == "PASS" and all(suite["checks"].values())
    before = load(run + "/before_snapshot.json")
    # Reuse the frozen runner's exact snapshot scope; compare key unions so
    # additions, not just modifications/deletions, are detected after the run.
    spec = importlib.util.spec_from_file_location("r13b_snapshot_evidence", HERE / "run_full_suite.py")
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    after = runner.snapshot()
    drift = sorted(p for p in before.keys() | after.keys() if before.get(p) != after.get(p))
    assert not drift, drift
    rows = load("remaining_138.json")
    old = json.loads((ROOT / "reports/codex/R13FIX_evidence/construction/public_api_inventory.json").read_text(encoding="utf-8"))
    required = {r["api"] for r in old if r["public"] and r["kind"] == "callable" and r["status"].startswith("未确认")}
    assert {r["api"] for r in rows} == required and len(rows) == len(required) == 138
    assert Counter(r["status"] for r in rows) == {"differential": 107, "nonconstructive": 29, "gap": 2}
    assert "??" not in json.dumps(rows, ensure_ascii=False)
    nodes = set(load(run + "/collection_nodes.json"))
    base_nodes = {n.split("[")[0] for n in nodes}
    for row in rows:
        assert row["proof"] and "limits" in row
        # Empty means no *additional item-specific* caveat, not a waiver of
        # the shared valid-input/output-range contract or a full-domain proof.
        assert isinstance(row["limits"], (str, list))
        if row["status"] == "differential":
            assert row["tests"] and row["scales"], row["api"]
        for test in row["tests"]:
            assert test.split("[")[0] in base_nodes, test
    outputs = distinct_outputs()
    checked_links = []
    for path in (ROOT / "reports/codex/R13FIXb_report.md", ROOT / "docs/r13fix_construction_inventory.md"):
        value = path.read_text(encoding="utf-8")
        assert "\ufffd" not in value and "??" not in value
        for href in re.findall(r"\]\(([^)]+)\)", value):
            if "://" in href or href.startswith("#"):
                continue
            target = (path.parent / unquote(href.split("#")[0])).resolve()
            assert target.is_relative_to(ROOT), (path, href)
            assert target.exists() or target == HERE / "artifact_verification.json", (path, href)
            checked_links.append({"from": str(path.relative_to(ROOT)), "href": href})
    report = (ROOT / "reports/codex/R13FIXb_report.md").read_text(encoding="utf-8")
    assert report.rstrip().splitlines()[-1].startswith("R13FIXb_PARTIAL：")
    result = dict(status="PASS", full_suite_run=run, original_138_exact_set=True,
                  dispositions=dict(Counter(r["status"] for r in rows)), reference_nodes_present=True,
                  source_test_policy_doc_drift=drift, checked_hashes=len(before),
                  distinct_scale_outputs=outputs, dimensionless_outputs="invariant, not falsely required distinct",
                  checked_local_links=checked_links,
                  report_sha256=digest(ROOT / "reports/codex/R13FIXb_report.md"))
    def git(*args):
        return subprocess.check_output(["git", *args], cwd=ROOT).decode("utf-8").strip()
    branch, head = git("branch", "--show-current"), git("rev-parse", "HEAD")
    baseline = load("root/baseline.json")
    assert branch == baseline["branch"] == "codex-work"
    assert head == baseline["head"]
    subprocess.run(["git", "-c", "core.whitespace=cr-at-eol", "diff", "--check"], cwd=ROOT, check=True)
    receipt_path = "reports/codex/R13FIXb_evidence/artifact_verification.json"
    receipt_bytes = (json.dumps(result, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    changed = set(git("diff", "--name-only", "-z").split("\0"))
    changed |= set(git("ls-files", "--others", "--exclude-standard", "-z").split("\0"))
    changed.add(receipt_path)
    entries = []
    for relative in sorted(changed - {"", "reports/codex/R13FIXb_evidence/deliverables.json"}):
        path = ROOT / relative
        assert path.resolve().is_relative_to(ROOT)
        if relative == receipt_path:
            entries.append(dict(path=relative, link=path.as_uri(), bytes=len(receipt_bytes), sha256=hashlib.sha256(receipt_bytes).hexdigest()))
        elif path.is_file():
            entries.append(dict(path=relative, link=path.as_uri(), bytes=path.stat().st_size, sha256=digest(path)))
    manifest = dict(branch=branch, head=head,
                    note="All changed/untracked nonignored deliverables; temporary files excluded by existing gitignore. Manifest does not hash itself.",
                    files=entries)
    (HERE / "deliverables.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    # PASS is published only after every validation above has succeeded.
    (HERE / "artifact_verification.json").write_bytes(receipt_bytes)
    print(f"R13FIXb_ARTIFACTS PASS: 138 exact rows; 2 gaps; {len(outputs)} distinct-scale families; {len(before)} unchanged hashes; {len(checked_links)} local links")


if __name__ == "__main__":
    main()
