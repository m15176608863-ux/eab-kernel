"""Read-only gzip input relocation; compression and decoding stay in stdlib.

The shim preserves reviewed test-function bodies while moving their immutable
input files. Write/append/create modes are delegated with the original path.
"""
import gzip as _gzip
import os
from pathlib import Path

from frozen_evidence import data_path

ROOT = Path(__file__).resolve().parents[1]


def open(filename, mode="rb", compresslevel=9, encoding=None, errors=None, newline=None):
    if mode in ("r", "rb", "rt") and isinstance(filename, (str, bytes, os.PathLike)):
        filename = data_path(ROOT, os.fsdecode(filename))
    return _gzip.open(filename, mode, compresslevel, encoding, errors, newline)
