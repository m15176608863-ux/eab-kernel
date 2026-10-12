"""Restore one defective claim in a real document, run its gate, restore bytes."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
CASES = (
    ("G6G-09", "docs/exact_3d_design.md", "六轴非贯入证书 ⇒ rho ≤ w",
     "六轴脱离证书 ⇒ PD ≤ w",
     "tests/test_r7fix_docs.py::test_g6g09_window_documents_distinguish_closed_separation_infimum[docs/exact_3d_design.md]",
     "axis acceptance does not bound"),
    ("G6G-10", "README.md",
     "使用独立 `kernel2d/g0_oracle.py` 的有理区间裁剪、段距离与事件检查检验距离/出口完备性（不调用生产 `polygons_overlap`）",
     "仍以暴力 `polygons_overlap` 检验距离/出口完备性",
     "tests/test_r7fix_docs.py::test_g6g10_readme_oracle_and_canon_status_are_current",
     "stale production oracle"),
    ("G6G-11", "docs/canon_map.md", "**撤回优先性主张**：改称",
     '**撤回优先性主张**：对外须限定为"DDA 圈内 / 本课题组代码里第一份"；改称',
     "tests/test_r7fix_docs.py::test_g6g11_priority_claim_is_withdrawn_instead_of_narrowed",
     "narrowing priority"),
)


def main():
    rows = []
    for finding, relative, old, new, node, failure in CASES:
        path = ROOT / relative
        before = path.read_bytes()
        old, new = old.encode("utf-8"), new.encode("utf-8")
        assert before.count(old) == 1, (finding, before.count(old))
        try:
            path.write_bytes(before.replace(old, new))
            command = [sys.executable, "-X", "utf8", "-m", "pytest", "-q",
                       "-p", "no:cacheprovider", node,
                       "--basetemp=reports/codex/R7FIX_evidence/tmp/docs_mutation_" + finding]
            result = subprocess.run(command, cwd=ROOT, capture_output=True,
                                    text=True, encoding="utf-8", errors="replace",
                                    env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1",
                                         "PYTHONIOENCODING": "utf-8"})
            log = result.stdout + result.stderr
            (OUT / (finding + "_mutation_red.log")).write_text(log, encoding="utf-8")
            assert result.returncode == 1 and failure in log, (finding, log)
        finally:
            path.write_bytes(before)
        assert path.read_bytes() == before
        row = dict(finding=finding, path=relative, node=node, command=command,
                   exit_code=result.returncode, targeted_assertion=failure,
                   last_line=log.strip().splitlines()[-1], restored=True,
                   restored_sha256=hashlib.sha256(before).hexdigest())
        rows.append(row)
        print(finding, row["last_line"], "restored SHA256", row["restored_sha256"])
    (OUT / "document_mutations.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
