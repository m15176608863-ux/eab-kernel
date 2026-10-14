"""Runner I/O regression: inject Windows sharing failures inside Path.replace.

The real host writer and exec'd real plugin progress function are both used.
Only filesystem replacement and sleeping are intercepted, never their output.
All scaffolding stays inside the test driver; no static waiver is needed.
"""
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import m4c_run_gates as runner


@pytest.mark.parametrize("writer_kind", ("host", "plugin"))
@pytest.mark.parametrize("failure_mode", ("first_two", "permanent_permission", "other_error"))
def test_progress_atomic_replace_retries_only_permission_errors(monkeypatch, tmp_path, writer_kind, failure_mode):
    target = tmp_path / "progress.json"
    target.write_text('{"previous": true}', encoding="utf-8")
    expected = {"status": "replacement", "count": 2}
    if writer_kind == "host":
        temporary = target.with_name(target.name + ".writing")
        def invoke():
            runner.write_json(target, expected)
    else:
        temporary = target.with_suffix(".writing")
        monkeypatch.setenv("M4C_NODE_PROGRESS", str(target))
        namespace = {}
        exec(compile(runner.PLUGIN, "<real M4c progress plugin>", "exec"), namespace)
        namespace["collected"].append("tests/example.py::test_one")
        namespace["reports"].append(dict(nodeid="tests/example.py::test_one", when="call", outcome="passed", duration=0.01))
        def invoke():
            namespace["progress"](complete=True)

    original_replace = Path.replace
    attempts = []
    delays = []
    failure = (FileNotFoundError("not a sharing violation") if failure_mode == "other_error"
               else PermissionError(5, "simulated Windows delete-sharing denial"))

    def injected_replace(source, destination):
        assert source == temporary and destination == target, "inject inside the actual atomic replacement"
        attempts.append((source, destination))
        if failure_mode != "first_two" or len(attempts) <= 2:
            raise failure
        return original_replace(source, destination)

    monkeypatch.setattr(Path, "replace", injected_replace)
    monkeypatch.setattr(runner.time, "sleep", delays.append)
    if failure_mode == "first_two":
        invoke()
        assert len(attempts) == 3 and delays == [0.01, 0.02], "transient sharing denial must recover on third replace"
        result = json.loads(target.read_text(encoding="utf-8"))
        if writer_kind == "host":
            assert result == expected
        else:
            assert result["complete"] and result["collected"] == result["calls"] == 1
            assert result["failed"] == result["skipped"] == 0
            assert result["last"] == namespace["reports"][-1]
        assert not temporary.exists(), "successful atomic replacement consumes temporary file"
        assert not target.read_bytes().startswith(b"\xef\xbb\xbf")
    else:
        with pytest.raises(type(failure)) as caught:
            invoke()
        assert caught.value is failure, "exhaustion or other I/O failure must remain loud"
        if failure_mode == "permanent_permission":
            assert len(attempts) == 12 and len(delays) == 11, "persistent failure must end at finite retry bound"
            assert delays == [min(0.01 * n, 0.1) for n in range(1, 12)]
        else:
            assert len(attempts) == 1 and delays == [], "non-permission exceptions must not be retried"
        assert json.loads(target.read_text(encoding="utf-8")) == {"previous": True}
        assert temporary.exists(), "failed replacement keeps the pending payload for diagnosis"
