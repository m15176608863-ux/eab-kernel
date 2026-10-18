"""Five requested H1-fix mutants in a disposable source copy, never live src."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
E = ROOT / "reports/codex/H1_evidence/fix_p3"
TEMP = ROOT / "reports/codex/H1_evidence/tmp/fix_p3_mutations"
sys.path.insert(0, str(ROOT / "tools"))
import h1_run_gates as runner

GE = "src/eab/kernel2d/global_entrance.py"
C1 = "src/eab/kernel2d/m5d_exit_certificate.py"
PARTS = "self.parts_a, self.parts_b = tuple(_triangulate(self.A)), tuple(_triangulate(self.B))"
MUTATIONS = (
    ("G4_convexify_A", GE, PARTS, "self.parts_a, self.parts_b = (_hull(self.A),), tuple(_triangulate(self.B))", 24,
     "E state disagrees with independent overlap oracle"),
    ("G5_convexify_both", GE, PARTS, "self.parts_a, self.parts_b = (_hull(self.A),), (_hull(self.B),)", 24,
     "E state disagrees with independent overlap oracle"),
    ("G8_topology_membership", GE, "        if state != 0:\n            return state\n        cones, rays",
     "        if True:\n            return state\n        cones, rays", 24,
     "E topology disagrees with independent exterior oracle"),
    ("G9_no_clockwise_normalization", GE, "p = p if area > 0 else tuple(reversed(p))", "p = p", 24,
     "valid clockwise rings must retain the displacement contract"),
    ("C1e_A_convexity_uses_B_radius", C1, '(("A", a, ra), ("B", b, rb))',
     '(("A", a, rb), ("B", b, rb))', 1,
     "C1 A convexity must use A radius even when B radius is zero"),
)


def main():
    assert not TEMP.exists(), "mutation runs use a new immutable directory"
    TEMP.mkdir(parents=True)
    E.mkdir(parents=True, exist_ok=True)
    source = TEMP / "source"
    manifest = runner.snapshot(source)
    (TEMP / "source_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8",
               TEMP=str(TEMP), TMP=str(TEMP),
               PYTHONPATH=os.pathsep.join((str(source / "src"), str(source / "tools"))))

    def run(name, expected_failures=0, marker=None):
        record = TEMP / (name + "_execution.json")
        progress = E / (name + "_progress.json")
        command = [sys.executable, "-X", "utf8", "-m", "pytest", "-q", "-rf", "--tb=short",
                   "-p", "no:cacheprovider", "-p", "h1_execution_plugin", "--basetemp", str(TEMP / name),
                   "tests/test_h1_entrance_symmetry.py", "tests/test_h1_adopted_semantics.py"]
        local = dict(env, H1_EXECUTION=str(record), H1_PROGRESS=str(progress))
        result = subprocess.run(command, cwd=source, env=local, capture_output=True, timeout=120)
        log = result.stdout + result.stderr
        (TEMP / (name + ".log")).write_bytes(log)
        text = log.decode("utf-8", errors="replace")
        data = json.loads(record.read_text("utf-8"))
        calls = [r for r in data["reports"] if r["when"] == "call"]
        failed = [r["nodeid"] for r in calls if r["outcome"] == "failed"]
        assert data["complete"] and len(calls) == len(data["collected"]) == 29
        assert not any(r["outcome"] == "skipped" for r in data["reports"])
        assert len(failed) == expected_failures, (name, failed, text)
        assert result.returncode == (1 if expected_failures else 0), text
        assert marker is None or marker in text, (name, "wrong failure assertion", text)
        return dict(name=name, command=command, last_line=text.splitlines()[-1],
                    collected=29, executed=len(calls), failed_nodes=failed,
                    expected_assertion=marker, status="KILLED" if expected_failures else "GREEN")

    results = [run("pristine")]
    for name, relative, old, new, count, marker in MUTATIONS:
        path = source / relative
        original = path.read_bytes()
        text = original.decode("utf-8")
        assert text.count(old) == 1, (name, text.count(old))
        path.write_bytes(text.replace(old, new, 1).encode("utf-8"))
        try:
            results.append(run(name, count, marker))
        finally:
            path.write_bytes(original)
        assert path.read_bytes() == original
        (E / "verification.json").write_text(json.dumps(dict(complete=False, results=results), indent=2)+"\n", encoding="utf-8")
    results.append(run("pristine_after"))
    assert all(hashlib.sha256((source/r["path"]).read_bytes()).hexdigest() == r["sha256"] for r in manifest)
    (E / "verification.json").write_text(json.dumps(dict(complete=True, results=results,
        source_restored=True, live_source_mutated=False, test_of_test_nodes=1), indent=2)+"\n", encoding="utf-8")
    print(json.dumps([(r["name"], r["last_line"]) for r in results], ensure_ascii=False))


if __name__ == "__main__":
    main()
