"""M5d exhaustive audit of final four-shard logs, stages, and export bytes."""
from pathlib import Path
import m5c_finalize_evidence as audit


def main():
    audit.EVIDENCE = Path(__file__).resolve().parents[1] / "reports/codex/M5d_evidence"
    return audit.main()


if __name__ == "__main__":
    raise SystemExit(main())
