"""Runtime source closure binding for fresh M5c replay processes.

Only repository-owned source is bound here; Python/stdlib identity belongs to
runtime metadata, not to a guessed list of direct numerical dependencies. A
fresh replay imports its lazy numerical dependencies before the first snapshot.
Every loaded src/eab or tools Python file (including package initializers and
this binding code) is then bound. A module added or changed during computation
invalidates the run; no historical hashes are rewritten to repair that run.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path


def runtime_source_hashes(root, entrypoint):
    """Hash all currently loaded repository production/replay Python modules."""
    root = Path(root).resolve()
    paths = {Path(entrypoint).resolve(), Path(__file__).resolve()}
    for module in tuple(sys.modules.values()):
        filename = getattr(module, "__file__", None)
        if not filename:
            continue
        path = Path(filename).resolve()
        try:
            relative = path.relative_to(root).as_posix()
        except ValueError:
            continue
        if path.suffix == ".py" and relative.startswith(("src/eab/", "tools/")):
            paths.add(path)
    return {path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(paths)}


def assert_current_sources(root, expected, observed=None):
    """Reject stale bytes, malformed paths or a changed runtime import closure."""
    root = Path(root).resolve()
    if not expected:
        raise ValueError("empty runtime source closure")
    for name, digest in expected.items():
        path = (root / name).resolve()
        if (not path.is_relative_to(root) or path.suffix != ".py"
                or path.relative_to(root).as_posix() != name
                or not name.startswith(("src/eab/", "tools/"))):
            raise ValueError("invalid runtime source path: " + name)
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError("runtime source bytes changed: " + name)
    if observed is not None and observed != expected:
        raise ValueError("runtime source closure changed; discard run and restart")
