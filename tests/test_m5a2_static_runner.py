"""M5a2 callback admission and bounded runner protocol (no numeric oracle).

Imports for expected values: stdlib json/hashlib and literal protocol results.
Static defects are injected inside scan_text; timeout defects are injected
inside a real RealAlgebraic method, not appended to a result or a hash file.
"""
import hashlib
import importlib.util
import inspect
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import check_exact_construction as gate
import m5a2_run_gates as runner


def test_all_3103_legacy_and_117_m5a_admissions_remain_unchanged():
    policy = json.loads((ROOT / "tools/exact_construction_policy.json").read_text(encoding="utf-8"))
    prefix = policy["waivers"][:3220]
    fingerprint = hashlib.sha256(json.dumps(prefix, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    assert len(prefix) == 3220 and fingerprint == "1e513fa6d8f8e7b991750d20060547dadfc434887ea105cf7a97b7fd9f540163", \
        "the 3103 legacy plus 117 M5a site admissions must remain byte-value identical"


@pytest.mark.parametrize("body", (
    "return scalar_algebraic(compare)",
    "return scalar_algebraic(compare=compare)",
    "return scalar_algebraic(holder.compare)",
    "return scalar_algebraic(lambda q: 0)",
    "convert = scalar_algebraic\n    return convert(compare)",
    "return scalar_algebraic.__call__(holder.compare)",
    "from eab.construction import scalar_algebraic as convert\n    return convert(compare)",
))
def test_arbitrary_algebraic_comparator_requires_individual_site_admission(body):
    issues = gate.scan_text("def bad(compare, holder):\n    " + body + "\n")
    assert any(row[3] == "algebraic-comparator-site" for row in issues), \
        "arbitrary comparator must not inherit exactness from the constructor name"


def test_comparator_site_rule_has_internal_mutation_teeth(monkeypatch):
    source = inspect.getsource(gate.scan_text)
    old = 'if "scalar_algebraic" in names:'
    assert source.count(old) == 1
    namespace = dict(vars(gate))
    exec(compile(source.replace(old, "if False:"), "<M5a2 callback rule mutant>", "exec"), namespace)
    monkeypatch.setattr(gate, "scan_text", namespace["scan_text"])
    with pytest.raises(AssertionError, match="arbitrary comparator must not inherit exactness"):
        test_arbitrary_algebraic_comparator_requires_individual_site_admission("return scalar_algebraic(holder.compare)")


def test_per_test_watchdog_terminates_real_internal_nontermination(tmp_path):
    plugin = tmp_path / "m5a2_timeout_plugin.py"
    plugin.write_text(runner.PLUGIN, encoding="utf-8")
    case = tmp_path / "test_nontermination.py"
    case.write_text('''from eab.kernel2d.algebraic import RealAlgebraic
def test_internal_nontermination(monkeypatch):
    def broken_refine(self):
        while True:
            pass
    monkeypatch.setattr(RealAlgebraic, "refine", broken_refine)
    RealAlgebraic.from_rational(1).refine()
''', encoding="utf-8")
    env = dict(os.environ, PYTHONPATH=os.pathsep.join((str(ROOT / "src"), str(tmp_path))),
               M5A2_TEST_TIMEOUT="0.25", M5A2_TIMEOUT_RECORD=str(tmp_path / "timeout.json"),
               M5A2_NODE_PROGRESS=str(tmp_path / "progress.json"),
               M5A2_NODE_JOURNAL=str(tmp_path / "journal.jsonl"),
               M5A2_EXECUTION_RECORD=str(tmp_path / "execution.json"),
               TEMP=str(tmp_path), TMP=str(tmp_path), PYTHONDONTWRITEBYTECODE="1")
    command = [sys.executable, "-X", "utf8", "-m", "pytest", "-q", "-p", "no:cacheprovider",
               "-p", "m5a2_timeout_plugin", str(case), "--basetemp", str(tmp_path / "pytest")]
    result = subprocess.run(command, cwd=tmp_path, env=env, capture_output=True,
                            text=True, encoding="utf-8", errors="replace", timeout=15)
    assert result.returncode == 124, "internal nontermination must be a bounded red exit"
    record = json.loads((tmp_path / "timeout.json").read_text(encoding="utf-8"))
    assert record["when"] == "watchdog" and record["outcome"] == "failed"
    assert record["nodeid"].endswith("::test_internal_nontermination")
    assert not (tmp_path / "execution.json").exists(), "a timed out shard cannot claim completion"


def test_renewal_does_not_admit_a_changed_scope_or_an_unreviewed_site(monkeypatch):
    subset = gate._subset
    text = "def probe(compare):\n    return scalar_algebraic(compare)\n"
    node = "Call(func=Name(id='scalar_algebraic', ctx=Load()), args=[Name(id='compare', ctx=Load())], keywords=[])"
    old = dict(id="old", path="probe.py", function="probe", rule="algebraic-comparator-site",
               node=node, context="historical", reason="old review")
    renewal = dict(old_id="old", old_row_sha256=hashlib.sha256(json.dumps(old, sort_keys=True, ensure_ascii=False).encode()).hexdigest(),
                   new_context=subset.site_contexts(text)["probe"], reason="explicit review of changed scope")
    policy = dict(waivers=[old], renewals=[renewal], imports=[], members=[])
    monkeypatch.setattr(subset, "_policy", lambda: policy)
    assert subset.stale_waiver_issues(text, "probe.py") == []
    assert subset.approved_sites(text, "probe.py") == set(), "retiring an old pin grants no current admission"
    changed = text.replace("scalar_algebraic(compare)", "scalar_algebraic(compare, allow_underflow=True)")
    assert subset.stale_waiver_issues(changed, "probe.py"), "a renewal must expire when its new scope changes"
    renewal["old_row_sha256"] = "forged"
    assert subset.stale_waiver_issues(text, "probe.py"), "renewal must bind the exact immutable old row"


def test_gate_step_deadline_also_covers_collection_and_static_nontermination(tmp_path):
    env = dict(os.environ, M5A2_PROCESS_TIMEOUT="0.2", TEMP=str(tmp_path), TMP=str(tmp_path))
    result = runner.run([sys.executable, "-c", "while True: pass"], tmp_path, env, tmp_path / "step.txt")
    assert result["exit_code"] == 124 and result["process_timed_out"], "a non-test gate step must have a bounded red exit"
    assert result["last_line"] == "M5A2_PROCESS_TIMEOUT: incomplete gate step is RED"


@pytest.mark.parametrize("invalid", ("nan", "inf", "-inf", "0", "-1"))
def test_nonfinite_or_nonpositive_timeouts_are_rejected_before_start(invalid, tmp_path, monkeypatch):
    env = dict(os.environ, M5A2_PROCESS_TIMEOUT=invalid)
    with pytest.raises(ValueError, match="finite and positive"):
        runner.run([sys.executable, "-c", "while True: pass"], tmp_path, env, tmp_path / "unused.txt")
    assert not (tmp_path / "unused.txt").exists()
    monkeypatch.setenv("M5A2_TEST_TIMEOUT", invalid)
    with pytest.raises(ValueError, match="finite and positive"):
        exec(compile(runner.PLUGIN, "<invalid watchdog configuration>", "exec"), {})
    monkeypatch.setattr(sys, "argv", ["m5a2_run_gates.py", "--name", "never_created", "--test-timeout="+invalid])
    with pytest.raises(SystemExit) as error:
        runner.main()
    assert error.value.code == 2


def test_export_integrity_detects_added_deleted_and_changed_source_files(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    known = source / "known.py"
    known.write_bytes(b"x = 1\n")
    manifest = [{"path": "known.py", "sha256": hashlib.sha256(known.read_bytes()).hexdigest()}]
    assert runner.export_mismatches(source, manifest) == []
    added = source / "added.py"
    added.write_bytes(b"x = 2\n")
    assert runner.export_mismatches(source, manifest) == ["added.py"], "new source files invalidate an immutable export"
    known.write_bytes(b"x = 3\n")
    assert runner.export_mismatches(source, manifest) == ["added.py", "known.py"]
    known.unlink()
    assert runner.export_mismatches(source, manifest) == ["added.py", "known.py"]
