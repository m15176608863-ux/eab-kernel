"""WO-INT1 wrapper for the existing immutable four-shard gate orchestration.

Usage: python tools/int1_run_gates.py --name NAME [--baseline-head]
All raw node lists and execution journals go to ignored INT1 evidence tmp.
"""
from pathlib import Path
import m5a2_run_gates as runner


def main():
    runner.EVIDENCE = Path(__file__).resolve().parents[1] / "reports/codex/INT1_evidence"
    return runner.main()


if __name__ == "__main__":
    raise SystemExit(main())
