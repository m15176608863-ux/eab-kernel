"""Read relocated historical data without changing embedded provenance keys.

This resolver is for reads only. Producers keep their explicit reports/output
destinations. Synthetic test roots and newly generated data continue to use
their original paths when no frozen counterpart exists.
"""
import hashlib
from pathlib import Path


def data_path(root, name):
    """Resolve a reports/... input to fixtures/frozen/... when it exists."""
    root = Path(root).resolve()
    original = Path(name)
    if not original.is_absolute():
        original = root / original
    try:
        relative = original.resolve().relative_to(root)
    except ValueError:
        return original
    if relative.parts and relative.parts[0] == "reports":
        frozen = root / "fixtures" / "frozen" / Path(*relative.parts[1:])
        if frozen.exists():
            return frozen
    return original


def historical_name(root, path):
    """Keep old report-relative keys in byte-preserved JSON hash inventories."""
    name = Path(path).resolve().relative_to(Path(root).resolve()).as_posix()
    if name.startswith("fixtures/frozen/"):
        return "reports/" + name[len("fixtures/frozen/"):]
    return name


def assert_data_entry(root, row):
    """Check immutable input bytes, not source-code or numerical truth."""
    data = (Path(root) / row["path"]).read_bytes()
    assert len(data) == row["bytes"], "H1 frozen data byte count changed"
    assert hashlib.sha256(data).hexdigest() == row["sha256"], "H1 frozen data SHA256 changed"
