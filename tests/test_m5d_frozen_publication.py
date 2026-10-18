"""Publication semantics: changed closures never leave a half-published set.

The oracle is literal original/new file bytes in a workspace pytest sandbox;
no geometry primitives, frozen summary snapshots or external source hashes
provide an expected answer. Mutation edits the actual publisher function body.
"""
import json
from pathlib import Path
import sys

import pytest

from mutation_support import replace_module_callable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import m5d_refresh_frozen as publisher


@pytest.mark.parametrize("change_point", (None, 0, 1, 3, "after_final_check"))
@pytest.mark.parametrize("dependency_kind", ("input_hashes", "inherited_hashes", "inherited_stream_hashes"))
def test_publication_closure_drift_rejects_and_restores_every_written_target(
        tmp_path, monkeypatch, change_point, dependency_kind, mutate=False):
    executable = tmp_path / "tools/m5d_refresh_frozen.py"
    executable.parent.mkdir()
    executable.write_bytes((ROOT / "tools/m5d_refresh_frozen.py").read_bytes())
    monkeypatch.setattr(publisher, "ROOT", tmp_path)
    monkeypatch.setattr(publisher, "__file__", str(executable))
    dependencies = {}
    for key in ("input_hashes", "inherited_hashes", "inherited_stream_hashes"):
        path = tmp_path / (key+".txt")
        path.write_bytes(b"original dependency\n")
        dependencies[key] = path
    metadata = {key: {path.name: publisher.sha(path)} for key, path in dependencies.items()}
    # H1: publisher pins evidence data; old source bytes are not an input.
    metadata["complete"] = True
    publication = []
    original = []
    new = []
    for index in range(3):
        target, candidate, backup = (tmp_path / (name+str(index)+".json")
                                     for name in ("target", "candidate", "backup"))
        before = ("original output "+str(index)+"\n").encode("utf-8")
        # A pure diagnostic list is a valid sealed product, not metadata.
        after = json.dumps(dict(metadata, observation=index) if index < 2 else [1, 2, 3]).encode("utf-8")
        target.write_bytes(before)
        backup.write_bytes(before)
        candidate.write_bytes(after)
        original.append(before)
        new.append(after)
        publication.append(dict(target=target.name, candidate=candidate.name, backup=backup.name,
                                before_sha256=publisher.sha(target), after_sha256=publisher.sha(candidate)))
    bindings = publisher.seal_candidates(publication)
    changed = dependencies[dependency_kind]
    atomic = publisher.atomic_copy
    verify = publisher.verify_seal
    writes, checks = [], []

    def injected_copy(source, target):
        atomic(source, target)
        writes.append(target)
        if change_point in (1, 3) and len(writes) == change_point:
            changed.write_bytes(b"changed after a completed output write\n")

    def injected_verify(mapping):
        verify(mapping)
        checks.append(True)
        if change_point == "after_final_check" and len(checks) == 1+2*len(publication):
            changed.write_bytes(b"changed after the final per-item check\n")

    monkeypatch.setattr(publisher, "atomic_copy", injected_copy)
    monkeypatch.setattr(publisher, "verify_seal", injected_verify)
    if change_point == 0:
        changed.write_bytes(b"changed before publication\n")
    if mutate:
        replace_module_callable(monkeypatch, publisher, "publish_sealed", [(
            "        verify_seal(bindings)\n    except BaseException:",
            "        pass  # missing final closure verification\n    except BaseException:",
        )])
    refused = False
    try:
        publisher.publish_sealed(publication, bindings)
    except AssertionError:
        refused = True
    if change_point is None:
        assert not refused, "M5d unchanged closure must publish the complete new set"
        assert [(tmp_path / r["target"]).read_bytes() for r in publication] == new
    else:
        assert refused, "M5d changed closure must be refused before claiming a complete publication"
        assert [(tmp_path / r["target"]).read_bytes() for r in publication] == original, \
            "M5d closure drift must not leave half-old half-new published targets"
    assert [(tmp_path / r["backup"]).read_bytes() for r in publication] == original
    assert not list(tmp_path.glob("*.m5d_writing"))


def test_missing_final_publication_verification_mutant_fails_the_named_semantic_assertion(tmp_path, monkeypatch):
    with pytest.raises(AssertionError, match="M5d changed closure must be refused"):
        test_publication_closure_drift_rejects_and_restores_every_written_target(
            tmp_path, monkeypatch, "after_final_check", "input_hashes", mutate=True)
