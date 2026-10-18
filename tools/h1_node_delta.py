"""Account for every WO-H1 pytest node change, rejecting unknown differences.

Only the two supplied collect-only logs are read.  UTF-8 and PowerShell UTF-16
logs are accepted; no collection, execution, or source rewriting is performed.
The declared node sets are deliberately exact rather than prefix allowlists.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_OLD_COUNT = 13877
EXPECTED_NEW_COUNT = 13907

RETIRED = frozenset({
    "tests/test_m4c_fix_replay.py::test_frozen_hash_scope_is_exact_replay_import_closure_with_posix_keys",
    "tests/test_m5c_combined_evidence.py::test_combined_join_rejects_incomplete_or_inconsistent_evidence_without_publishing[research_wrong_sources-hash mismatch]",
    "tests/test_m5c_policy_binding.py::test_changing_any_transitive_source_file_in_a_scratch_copy_is_rejected[m5b_endpoint_replay]",
    "tests/test_m5c_policy_binding.py::test_changing_any_transitive_source_file_in_a_scratch_copy_is_rejected[m5b_robust_replay]",
    "tests/test_m5c_policy_binding.py::test_frozen_summaries_bind_every_runtime_transitive_source_at_both_ends[m5b_endpoint_replay-endpoint_summary.json]",
    "tests/test_m5c_policy_binding.py::test_frozen_summaries_bind_every_runtime_transitive_source_at_both_ends[m5b_robust_replay-robust_summary.json]",
    "tests/test_m5c_policy_binding.py::test_new_runtime_import_after_start_invalidates_the_sealed_closure",
    "tests/test_m5c_policy_binding.py::test_runtime_source_closure_matches_independent_import_origins_and_kills_omission[False-m5b_endpoint_replay]",
    "tests/test_m5c_policy_binding.py::test_runtime_source_closure_matches_independent_import_origins_and_kills_omission[False-m5b_robust_replay]",
    "tests/test_m5c_policy_binding.py::test_runtime_source_closure_matches_independent_import_origins_and_kills_omission[True-m5b_endpoint_replay]",
    "tests/test_m5c_policy_binding.py::test_runtime_source_closure_matches_independent_import_origins_and_kills_omission[True-m5b_robust_replay]",
    "tests/test_m5c_policy_binding.py::test_source_binding_rejects_parent_traversal_even_with_matching_content",
})

ADDED_BY_CATEGORY = {
    "hash_data_and_semantics": frozenset({
        "tests/test_h1_frozen_data.py::test_frozen_data_hashes_are_preserved_without_current_source_pins",
        "tests/test_h1_frozen_data.py::test_frozen_data_integrity_rejects_an_actual_same_size_input_edit",
        "tests/test_h1_frozen_semantics.py::test_fixed_real_r3_subset_kills_an_internal_radius_budget_defect",
        "tests/test_h1_frozen_semantics.py::test_fixed_real_r3_subset_reexecutes_exact_certificate_labels_and_counts",
    }),
    "kernel_purity": frozenset({
        "tests/test_kernel_purity.py::test_kernel_domain_purity",
        "tests/test_kernel_purity.py::test_kernel_domain_vocabulary_covers_required_tokens_and_spelling",
        "tests/test_kernel_purity.py::test_kernel_purity_follows_transitive_imports",
        r"tests/test_kernel_purity.py::test_kernel_purity_rejects_actual_source_mutations[from eab.adapters import bdda2d\n-forbidden import path]",
        r"tests/test_kernel_purity.py::test_kernel_purity_rejects_actual_source_mutations[mtype = 0\n-domain token mtype]",
        "tests/test_kernel_purity.py::test_only_real_docstrings_are_exempt",
    }),
    "p3_adopted_semantics": frozenset({
        "tests/test_h1_adopted_semantics.py::test_c1_b_ring_convexity_uses_b_radius_when_a_is_exact",
        "tests/test_h1_adopted_semantics.py::test_c1_ranking_must_include_other_feature_family_competitors",
        "tests/test_h1_adopted_semantics.py::test_replay_box_shortcut_adds_independent_radii_before_certifying_separation",
    }),
    "p3_entrance_symmetry": frozenset({
        "tests/test_h1_entrance_symmetry.py::test_shi_reference_point_reflection_identity_for_nonconvex_global_entrance"
        f"[rotation{rotation}-translation{translation}-scale{scale}]"
        for rotation in range(2)
        for translation in range(4)
        for scale in range(3)
    } | {
        "tests/test_h1_entrance_symmetry.py::test_symmetry_parameter_cells_produce_distinct_reference_geometries",
    }),
    "repository_size": frozenset({
        "tests/test_repository_size.py::test_every_tracked_or_deliverable_file_is_at_most_one_megabyte_except_frozen_policy",
        "tests/test_repository_size.py::test_export_ignores_only_declared_runtime_outputs_and_keeps_other_evidence",
        "tests/test_repository_size.py::test_no_git_export_gate_reads_actual_files_and_catches_oversized_candidate",
    }),
    "fast_declarative_module_execution": frozenset({
        "tests/test_h1_module_execution.py::test_declarative_modules_execute_in_fast_test",
    }),
}

RENAMED = [
    {
        "category": "test_name",
        "old": "tests/test_m4c_replay.py::test_frozen_full_computation_is_bound_to_current_production_sources",
        "new": "tests/test_m4c_replay.py::test_frozen_full_computation_retains_historical_coverage",
        "reason": "退役当前源码 pin，保留历史覆盖及既有真实首帧回归",
    },
    {
        "category": "test_name",
        "old": "tests/test_m5a_replay.py::test_frozen_family_products_are_distinct_and_bound_to_current_source",
        "new": "tests/test_m5a_replay.py::test_frozen_family_products_are_distinct_and_retain_historical_revalidation",
        "reason": "退役当前源码 pin，保留历史族互异性与复核数据",
    },
    {
        "category": "test_name",
        "old": "tests/test_m5c_combined_evidence.py::test_frozen_combined_summary_has_complete_cohorts_current_sources_and_bound_upstream_summaries",
        "new": "tests/test_m5c_combined_evidence.py::test_frozen_combined_summary_has_complete_cohorts_and_bound_upstream_data",
        "reason": "退役当前源码 pin，保留完整 cohort 与上游数据绑定",
    },
]
_PUBLICATION = "tests/test_m5d_frozen_publication.py::test_publication_closure_drift_rejects_and_restores_every_written_target"
for _stage in ("0", "1", "3", "None", "after_final_check"):
    RENAMED.append({
        "category": "publication_parameter",
        "old": f"{_PUBLICATION}[source_hashes-{_stage}]",
        "new": f"{_PUBLICATION}[inherited_stream_hashes-{_stage}]",
        "reason": "以输入数据漂移替代历史源码漂移；同一发布阶段原子回滚门仍在",
    })
_README_PARAMETER = (
    r"\u968f\u540e\u5df2\u7ecf\u8fc7 G6 \u7b2c\u4e8c\u81f3\u7b2c\u4e94\u8f6e\u72ec\u7acb\u91cd\u5ba1-"
    r"canon_map\uff08\u672a\u7ecf G6\uff09-required1-canon map has historical independent review, not current M0 exit"
)
for _function in (
    "test_current_contract_gate_rejects_deleted_current_boundary",
    "test_current_contract_gate_rejects_reintroduced_old_text",
    "test_current_contracts_do_not_repeat_superseded_status",
):
    RENAMED.append({
        "category": "readme_history_path",
        "old": f"tests/test_r9fix_docs.py::{_function}[README.md-{_README_PARAMETER}]",
        "new": f"tests/test_r9fix_docs.py::{_function}[docs/history/README_through_20261019.md-{_README_PARAMETER}]",
        "reason": "原 README 原样移入历史文档，旧边界核查继续指向原文",
    })


def read_collection(path: Path) -> tuple[set[str], dict]:
    """Read strict text and retain counts/encoding/hash without copying the log."""
    payload = path.read_bytes()
    if payload.startswith((b"\xff\xfe", b"\xfe\xff")):
        encoding = "utf-16"
    elif b"\0" in payload:
        encoding = "utf-16-le" if payload[1::2].count(0) > payload[::2].count(0) else "utf-16-be"
    else:
        encoding = "utf-8-sig"
    lines = payload.decode(encoding).splitlines()
    nodes = [line.strip() for line in lines if line.startswith("tests/") and "::" in line]
    counts = Counter(nodes)
    totals = [int(match.group(1)) for line in lines
              if (match := re.fullmatch(r"\s*(\d+) tests? collected in .+", line))]
    errors = [line for line in lines if re.search(r"(?:ERROR collecting|collection interrupted|errors? during collection)", line, re.I)]
    return set(nodes), {
        "path": str(path.resolve()),
        "encoding": encoding,
        "sha256": hashlib.sha256(payload).hexdigest(),
        "bytes": len(payload),
        "node_count": len(nodes),
        "unique_node_count": len(counts),
        "reported_collection_totals": totals,
        "duplicate_nodes": sorted(node for node, count in counts.items() if count != 1),
        "collection_errors": errors,
    }


def account(old_path: Path, new_path: Path) -> dict:
    old, old_meta = read_collection(old_path)
    new, new_meta = read_collection(new_path)
    removed, added = old - new, new - old
    expected_added = frozenset().union(*ADDED_BY_CATEGORY.values())
    old_renamed = {row["old"] for row in RENAMED}
    new_renamed = {row["new"] for row in RENAMED}
    expected_removed = RETIRED | old_renamed
    expected_arrivals = expected_added | new_renamed
    issues = []
    for label, meta, expected in (("old", old_meta, EXPECTED_OLD_COUNT), ("new", new_meta, EXPECTED_NEW_COUNT)):
        if meta["node_count"] != expected:
            issues.append(f"{label} node count {meta['node_count']} != expected {expected}")
        if meta["duplicate_nodes"]:
            issues.append(f"{label} collection contains duplicate nodes")
        if meta["reported_collection_totals"] != [meta["node_count"]]:
            issues.append(f"{label} collection summary is absent, ambiguous, or inconsistent")
        if meta["collection_errors"]:
            issues.append(f"{label} collection reported errors")
    unmatched = {
        "unknown_removed": sorted(removed - expected_removed),
        "unknown_added": sorted(added - expected_arrivals),
        "missing_expected_removals": sorted(expected_removed - removed),
        "missing_expected_additions": sorted(expected_arrivals - added),
    }
    for category, nodes in unmatched.items():
        if nodes:
            issues.append(f"{category}: {len(nodes)}")
    declaration_valid = (
        len(RETIRED) == 12 and len(expected_added) == 42 and len(RENAMED) == 11
        and len(old_renamed) == 11 and len(new_renamed) == 11
        and not (RETIRED & old_renamed) and not (expected_added & new_renamed)
        and sum(map(len, ADDED_BY_CATEGORY.values())) == len(expected_added)
        and EXPECTED_NEW_COUNT == EXPECTED_OLD_COUNT - len(RETIRED) + len(expected_added)
    )
    if not declaration_valid:
        issues.append("internal expected-node declaration is inconsistent")
    return {
        "schema": "eab.wo_h1.node_delta.v1",
        "complete": not issues,
        "scope": "Exact collect-only node accounting; this is not evidence of execution or passing tests.",
        "old": old_meta,
        "new": new_meta,
        "counts": {
            "unchanged": len(old & new),
            "raw_removed": len(removed),
            "raw_added": len(added),
            "retired_expected": len(RETIRED),
            "retired_observed": len(RETIRED & removed),
            "new_expected": len(expected_added),
            "new_observed": len(expected_added & added),
            "renamed_expected": len(RENAMED),
            "renamed_observed": sum(row["old"] in removed and row["new"] in added for row in RENAMED),
            "net_change": len(new) - len(old),
        },
        "retired": [{"node": node, "observed": node in removed,
                     "reason": "退役历史源码/当前源码绑定；替代门见 docs/frozen_evidence.md"}
                    for node in sorted(RETIRED)],
        "added_categories": {
            category: [{"node": node, "observed": node in added} for node in sorted(nodes)]
            for category, nodes in ADDED_BY_CATEGORY.items()
        },
        "renamed": [dict(row, old_removed=row["old"] in removed, new_added=row["new"] in added)
                    for row in RENAMED],
        "unmatched": unmatched,
        "issues": issues,
    }


def render_markdown(result: dict) -> str:
    counts = result["counts"]
    lines = [
        "# H1 逐节点数量差异账", "",
        f"状态：{'完整匹配' if result['complete'] else '未完整匹配（不可作为收尾通过证据）'}。",
        "只核收集节点，不声称执行、通过或无 skip；全档运行记录另列。", "",
        f"- 原收集：{result['old']['node_count']}；新收集：{result['new']['node_count']}。",
        f"- 退役 {counts['retired_observed']}/{counts['retired_expected']}；新增 {counts['new_observed']}/{counts['new_expected']}；等量改名 {counts['renamed_observed']}/{counts['renamed_expected']} 对。",
        f"- 原始集合差：删 {counts['raw_removed']}、增 {counts['raw_added']}；净变化 {counts['net_change']:+d}。",
        "- 预期：13877 − 12 + 42 = 13907；11 对改名净变化 0。",
        "- 新增：纯度 6 + P3 28 + 大小 3 + 冻结数据/语义 4 + 模块执行烟测 1 = 42。", "",
        "## 输入", "",
    ]
    for key in ("old", "new"):
        meta = result[key]
        lines.append(f"- {key}：`{meta['path']}`；编码 `{meta['encoding']}`；SHA256 `{meta['sha256']}`。")
    lines += ["", "## 退役 12 个节点", "", "| 节点 | 已观察 |", "|---|---|"]
    lines += [f"| `{row['node']}` | {row['observed']} |" for row in result["retired"]]
    lines += ["", "替代语义门、退役原因逐条见 [冻结证据说明](../../../docs/frozen_evidence.md)。", "", "## 新增 42 个节点"]
    for category, rows in result["added_categories"].items():
        lines += ["", f"### {category}（{len(rows)}）", "", "| 节点 | 已观察 |", "|---|---|"]
        lines += [f"| `{row['node']}` | {row['observed']} |" for row in rows]
    lines += ["", "## 等量改名 11 对（净 0）", "", "| 分类 | 原节点 | 新节点 | 理由 | 已观察两端 |", "|---|---|---|---|---|"]
    for row in result["renamed"]:
        lines.append(f"| {row['category']} | `{row['old']}` | `{row['new']}` | {row['reason']} | {row['old_removed'] and row['new_added']} |")
    lines += ["", "## 未匹配项", ""]
    if result["issues"]:
        lines += [f"- {issue}" for issue in result["issues"]]
        for category, nodes in result["unmatched"].items():
            if nodes:
                lines += ["", f"### {category}", ""] + [f"- `{node}`" for node in nodes]
    else:
        lines.append("无；未使用前缀白名单或忽略未知节点。")
    lines += ["", "## 复跑", "", "```powershell", "python tools/h1_node_delta.py --old <基线收集文件> --new <收尾收集文件>", "```", "", "未知变化、预期缺失、重复节点、收集数不符或收集错误均返回非零状态。", ""]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--old", required=True, type=Path)
    parser.add_argument("--new", required=True, type=Path)
    parser.add_argument("--out-dir", type=Path, default=ROOT / "reports/codex/H1_evidence")
    args = parser.parse_args()
    result = account(args.old, args.new)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    with (args.out_dir / "node_delta.json").open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    with (args.out_dir / "node_delta.md").open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(render_markdown(result))
    print(json.dumps({"complete": result["complete"], "counts": result["counts"], "issues": result["issues"]}, ensure_ascii=True))
    return 0 if result["complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
