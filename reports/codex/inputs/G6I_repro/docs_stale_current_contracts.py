"""Confirm surviving current-prose contradictions without changing documents."""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "tests")]

def line(path, number):
    return (ROOT / path).read_text(encoding="utf-8-sig").splitlines()[number-1]

canon93 = line("docs/canon_map.md", 93)
canon73 = line("docs/canon_map.md", 73)
assert "\u4f9d\u8d56\u547d\u9898 7\u30018\uff0c\u5747\u672a\u5b9e\u73b0" in canon93
assert "first_entrance" in canon73 and "first_entrance3" in canon73
from eab.kernel2d.entrance import first_entrance
from eab.kernel3d.entrance3 import first_entrance3
assert callable(first_entrance) and callable(first_entrance3)

readme106 = line("README.md", 106)
canon25 = line("docs/canon_map.md", 25)
assert "canon_map\uff08\u672a\u7ecf G6\uff09" in readme106
assert "G6 \u7b2c\u4e8c\u81f3\u7b2c\u4e94\u8f6e\u7684\u72ec\u7acb\u91cd\u5ba1" in canon25

import test_invariance_2d as T
assert "19 \u4e2a\u683c\u5b50\u53ea\u65ad\u8a00\u5939\u903c" in T.__doc__
assert "\u4e0d\u518d\u9489\u65e7\u566a\u58f0\u7b97\u6cd5\u7684 19 \u683c" in T.test_cover_invariance_unresolvable_cells_are_explained_by_measured_near_parallel_edges.__doc__
print(json.dumps([
    {"location": "docs/canon_map.md:93", "old_statement": canon93,
     "counterevidence": "current first_entrance/first_entrance3 exist; same mapping row73 explicitly implements proposition7"},
    {"location": "README.md:106", "old_statement": "canon_map unreviewed by G6 / its source correspondence not accepted",
     "counterevidence": canon25},
    {"location": "tests/test_invariance_2d.py:17-22", "old_statement": "19 cells only bracketed / relative noise-floor correction",
     "counterevidence": "same module current named gate explicitly no longer pins old19, per-cell exact oracle now checked"}
], ensure_ascii=False, indent=2))
print("CONFIRMED: three stale current-contract descriptions, one deduplicated documentation finding")
