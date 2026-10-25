"""WO-T2b entry point for unchanged H1-backed execution and audit logic.

All run products and temporary files stay in the approved T2b evidence root.
Use --baseline to extract baseline_anchor/source.zip instead of live files.
The inherited version t2-h1-external-3 identifies the shared runner, not T2a
evidence; its source/temp paths identify this work order without relabelling
old runs. Byte exports are not fresh Git checkouts.
"""
import os
from pathlib import Path

import t2_run_gates as runner


EVIDENCE = Path("D:/eab-evidence/reports/codex/T2b_evidence")


def main():
    runner.EVIDENCE = EVIDENCE
    for name in ("BDDA_DETECT", "BDDA_DETECT_SHADOW", "BDDA_SHADOW_PATH"):
        os.environ.pop(name, None)
    return runner.main()


if __name__ == "__main__":
    raise SystemExit(main())
