"""M5d counterfactual emitted-diagnostic x AST rule-site audit; no waivers."""
from pathlib import Path
import m5c_audit_admissions as audit

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports/codex/M5d_evidence"


def main():
    audit.OUT = OUT
    baseline = OUT / "tmp/baseline_suite_export"
    if not baseline.is_dir():
        raise ValueError("fresh HEAD archive baseline required")
    old = audit.audit(baseline, "baseline")
    new = audit.audit(ROOT, "current")
    delta = new["effective_rule_site_count"]-old["effective_rule_site_count"]
    result = dict(schema="eab.m5d-counterfactual-admissions.v1", complete=True,
                  baseline_revision="5b73cc8dfc1ad4f257412392111927d5a7171640",
                  counting_contract=audit.__doc__, baseline=old, current=new,
                  admitted_rule_site_net_delta=delta,
                  policy_bytes_unchanged=old["policy_sha256"] == new["policy_sha256"])
    audit.write(OUT / "admission_rule_sites.json", result)
    print("M5D_COUNTERFACTUAL_ADMISSIONS", old["effective_rule_site_count"], new["effective_rule_site_count"], "delta", delta, flush=True)


if __name__ == "__main__":
    main()
