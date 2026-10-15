"""WO-M5c fresh byte export, exhaustive four-process execution audit."""
from pathlib import Path
import m5a2_run_gates as runner


def main():
    runner.EVIDENCE = Path(__file__).resolve().parents[1] / "reports/codex/M5c_evidence"
    return runner.main()


if __name__ == "__main__":
    raise SystemExit(main())
