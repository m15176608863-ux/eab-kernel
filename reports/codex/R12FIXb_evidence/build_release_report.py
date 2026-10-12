"""Produce the Chinese report only from a passing, unchanged release run."""
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def read(name):
    return json.loads((HERE / name).read_text(encoding="utf-8-sig"))


def put(path, value):
    if path.exists():
        path.read_text(encoding="utf-8-sig")
    path.write_text(value, encoding="utf-8", newline="")


def dump(name, value):
    put(HERE/name, json.dumps(value, ensure_ascii=False, indent=2)+"\n")


def link(label, rel):
    return f"[{label}]({(ROOT/rel).as_uri()})"


def ev(label, rel):
    return link(label, "reports/codex/R12FIXb_evidence/"+rel)


def main():
    suite = read("full_suite_release/summary.json")
    assert suite["status"] == "PASS" and all(suite["checks"].values())
    assert suite["tests_collected"] == suite["tests_executed"] == 11508
    frozen = read("full_suite_release/before_snapshot.json")
    assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in frozen.items())
    static = read("static_gate_release_run.json")
    assert static["exit_code"] == 0 and static["last_line"] == "exact construction AST gate: 0 violation(s)"
    policy_path = ROOT/"tools/exact_construction_policy.json"
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    policy_hash = hashlib.sha256(policy_path.read_bytes()).hexdigest()
    receipt = read("reason_encoding_repair_receipt.json")
    assert policy_hash == receipt["policy_sha256"]
    assert hashlib.sha256((HERE/"local_review_decisions_release.json").read_bytes()).hexdigest() == receipt["ledger_sha256"]
    ledger = read("local_review_decisions_release.json")
    stats = read("local_manifest_statistics_release.json")
    assert len(policy["waivers"]) == len(ledger["decisions"]) == stats["waivers"] == 2365
    assert dict(Counter(r["category"] for r in policy["waivers"])) == stats["by_category"]
    assert stats["by_category"] == {
        "STRUCTURAL_DATA_OR_PROTOCOL_REVIEW":276,"INPUT_MODEL_OR_OUTPUT_BOUNDARY":639,
        "PROOF_GAP_MANUAL_EXCLUSION":642,"APPROXIMATE_OR_NOMINAL_SCOPE_EXCLUSION":467,
        "PUBLIC_DIAGNOSTIC_CALLBACK":5,"TEST_EXECUTION_OR_INTENTIONAL_DEFECT":320,
        "UNFINISHED_NUMERICAL_DYNAMIC_REWRITE":16}
    assert not any("dependenc" in k or "snapshot" in k for k in policy)
    assert not any(r["reason"].count("?")>=5 or "\ufffd" in r["reason"] for r in policy["waivers"])
    locality = read("real_policy_locality_probe.json")
    assert locality["status"] == "REAL_POLICY_LOCALITY_PASS" and locality["manifest_sha256"] == policy_hash

    baseline = {r["path"]:r["sha256"] for r in read("baseline_inventory.json")}
    paths = set(baseline)
    paths.update(p.relative_to(ROOT).as_posix() for f in ("src","tests","tools") for p in (ROOT/f).rglob("*.py"))
    changes = []
    for rel in sorted(paths):
        path = ROOT/rel
        current = hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None
        old = baseline.get(rel)
        if old != current:
            changes.append({"path":rel,"before_sha256":old,"after_sha256":current,
                            "status":"added" if old is None else "deleted" if current is None else "modified",
                            "url":path.as_uri(),
                            "backup_url":(HERE/"baseline"/(rel+".txt")).as_uri() if old else None})
    dump("changed_files.json",changes)
    table = "\n".join(f"| {r['status']} | {link(r['path'],r['path'])} |" for r in changes)
    put(HERE/"CHANGE_INDEX.md",
        "# 本轮相对执行前字节备份的变更\n\n不是相对 HEAD 的混合 R12FIX diff。\n\n"
        f"共 {len(changes)} 个源码／测试／工具／文档条目；报告和证据另见交付索引。\n\n"
        f"{ev('前后 SHA 清单','changed_files.json')} · {ev('恢复锚点','baseline/')}。\n\n"
        "回退须逐文件核对，不应批量覆盖原已接受的 R12FIX 或后续用户改动。\n\n"
        "| 状态 | 文件 |\n|---|---|\n"+table+"\n")

    pending = defaultdict(list)
    for r in ledger["decisions"]:
        if r["category"] == "UNFINISHED_NUMERICAL_DYNAMIC_REWRITE":
            pending[(r["path"],r["function"])].append(r["id"])
    assert len(pending)==8 and len({path for path,fn in pending})==4
    replacements = {
        "@@POLICY_SHA@@":policy_hash,
        "@@PYTEST_LINES@@":"\n".join("    "+r["last_line"] for r in suite["runs"]),
        "@@WALL@@":f"{suite['wall_seconds']:.6f}",
        "@@COLLECT@@":f"{suite['collection_seconds']:.6f}",
        "@@SUM@@":f"{suite['sum_pytest_process_seconds']:.6f}",
        "@@STATIC_WALL@@":f"{static['wall_seconds']:.7f}",
        "@@PENDING@@":"\n".join(f"- {link(path,path)} {fn}：{', '.join(ids)}。" for (path,fn),ids in pending.items()),
    }
    report = (HERE/"report_template.md").read_text(encoding="utf-8")
    for key,value in replacements.items():
        assert report.count(key)==1
        report = report.replace(key,value)
    assert "@@" not in report
    report_path = ROOT/"reports/codex/R12FIXb_report.md"
    put(report_path,report)
    marker = report.splitlines()[-1]
    assert marker.startswith("R12FIXb_PARTIAL")
    validation = {
        "status":"PARTIAL","all_tests_green":True,"original_nodes":11368,"final_nodes":11508,"added_nodes":140,
        "waivers":2365,"target_maximum":200,"pending_dynamic_rule_rows":16,"static_violations":0,
        "policy_sha256":policy_hash,"full_suite_checks":suite["checks"],
        "requirements":{"1_locality":"PASS","2_subset_and_200":"PARTIAL","3_dynamic_rewrite":"PARTIAL",
                        "4_listed_teeth":"PASS","5_maintenance":"PASS","6_full_suite_and_docs":"PASS"},
        "scope_hash_renewals":0,"independent_g6":False,"early_system_temp_scope_deviation":True,
        "changed_code_document_files":len(changes),"final_marker":marker}
    dump("final_validation.json",validation)
    index = "\n".join([
        "# R12FIXb 交付索引\n",
        "## 当前有效交付\n",
        "- "+link("主报告","reports/codex/R12FIXb_report.md"),
        "- "+link("当前 policy","tools/exact_construction_policy.json"),
        "- "+ev("最终逐站点账本","local_review_decisions_release.json")+" · "+ev("最终统计","local_manifest_statistics_release.json"),
        "- "+ev("最终全套 11508 节点","full_suite_release/summary.json")+" · "+ev("分片日志和逐节点审计","full_suite_release/"),
        "- "+ev("最终静态 CLI","static_gate_release.log")+" · "+ev("真实清单可维护性","real_policy_locality_probe.json"),
        "- "+ev("安装机制复核（非 G6）","final_installed_manifest_review.md")+" · "+ev("复核机器结果","final_installed_manifest_review_verified.json"),
        "- "+ev("最终验收状态","final_validation.json")+" · "+ev("源码／文档变更","CHANGE_INDEX.md"),
        "\n## 改写、恢复及其余材料\n",
        "- "+ev("数值改写","dynamic_rewrites.md")+" · "+ev("测试 helper 改写","test_helper_rewrite_changes.json")+" · "+ev("factory 等价","test_factory_data_equivalence.json"),
        "- "+ev("机制红绿","final_mechanism_review.md")+" · "+ev("执行前字节副本","baseline/")+" · "+ev("前后 SHA","changed_files.json"),
        "- "+ev("全部其余材料目录","")+"：包含早期失败日志、审核、临时副本；不是每项都代表最终通过。",
        "\n## 历史材料，不能当最终绿\n",
        "- full_suite 是首轮失败；唯一最终全套是 full_suite_release。",
        "- local_review_decisions.json、local_review_decisions_final.json 为中间版；当前为 local_review_decisions_release.json。",
        "- 统计当前为 local_manifest_statistics_release.json，其他同前缀是历史版。",
        "- final_static_gate.log 为 168 违例；final_static_gate_r2.log 是编码修复前的绿；最终为 static_gate_release.log。",
        "- raw_* 为原始研究清单，不是准入报告。scan_candidates.py 的 Expr 反找节点错误已记录；准确 payload 捕获为 capture_actual_fingerprints.py。",
        "- 初装和明确纠正脚本只供迁移审计，不是自动批量续签工具。不要用旧初装器重装 release。",
        "- "+ev("165 条绑定更正","fingerprint_extraction_corrections.json")+" · "+ev("独立绑定复核","fingerprint_binding_review.json"),
        "- "+ev("39 条 metadata 安装回执","local_manifest_amendments_applied.json")+" · "+ev("5 条编码修复回执","reason_encoding_repair_receipt.json"),
        "- "+ev("TEMP 越界披露","dynamic_temp_scope_deviation.json"),
        "\n当前 policy SHA-256："+policy_hash+"\n"])
    put(HERE/"DELIVERY_INDEX.md",index)
    checked = []
    for file in (report_path,HERE/"CHANGE_INDEX.md",HERE/"DELIVERY_INDEX.md"):
        text = file.read_text(encoding="utf-8")
        assert "\ufffd" not in text and "@@" not in text
        for url in re.findall(r"\]\((file:///[^)]+)\)",text):
            parsed = unquote(urlparse(url).path)
            path = Path(parsed[1:] if re.match(r"^/[A-Za-z]:/",parsed) else parsed)
            assert path.exists(),(file,url)
            checked.append(url)
    dump("report_artifact_qa.json",{"status":"PASS","markdown_links_checked":len(checked),
                                 "category_sum":sum(stats["by_category"].values()),
                                 "no_unfilled_placeholders":True,"final_report_last_line":marker,
                                 "report_sha256":hashlib.sha256(report_path.read_bytes()).hexdigest()})
    print(json.dumps(validation,ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
