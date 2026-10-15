"""Publish small M5a replay evidence from one completed, hash-bound batch."""
from collections import Counter
from fractions import Fraction as F
import gzip
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))
import m5a_se2_replay as replay


def main():
    evidence = Path(__file__).resolve().parent
    batch = evidence / "tmp/replay/full_r1"
    summary = json.loads((batch / "summary.json").read_text(encoding="utf-8"))
    replay.require(summary["complete"] and summary["steps"] == 1810 and summary["code_hashes"] == replay.code_hashes(), "only the complete current-source 1810 run may be published")
    replay.require(summary["stats"]["chord_new_contacts"] == 68 and summary["stats"]["m4c_20_subset"] == 20, "M4c question denominator changed")
    selections = {}
    maximum = None
    contact_comparison = Counter()
    pair_coverage = {name: {phase: Counter() for phase in replay.PHASES} for name in ("rigid_new_contacts", "chord_new_contacts", "m4c_20_subset")}
    for case in replay.CASES:
        path = batch / case / "normalized.jsonl.gz"
        replay.require(replay.file_hash(path) == summary["cases"][case]["normalized_sha256"], "normalized source hash mismatch")
        with gzip.open(path, "rt", encoding="utf-8") as stream:
            for row in map(json.loads, stream):
                pairs = {tuple(p["pair"]): p for p in row["pairs"]}
                phase_pairs = {phase: {} for phase in replay.PHASES}
                for phase in replay.PHASES:
                    for reference in row["phases"][phase]["records"]:
                        phase_pairs[phase].setdefault(tuple(reference["pair"]), []).append(reference)
                for pair in pairs.values():
                    if pair.get("m4c_translation_discrepancy_contact"):
                        selections.setdefault("Q1_rotation_versus_chord", (case, row, pair))
                    if pair["initial_state"] != -1:
                        continue
                    cohorts = []
                    if pair["rigid"]["status"] == "contact":
                        cohorts.append("rigid_new_contacts")
                    if pair["chord"]["status"] == "contact":
                        cohorts.append("chord_new_contacts")
                        label = "status_drop_to_no_contact" if pair["rigid"]["status"] != "contact" else "same_complete_cover" if pair["same_chord_status_and_cover"] else "contact_but_cover_changed"
                        contact_comparison[label] += 1
                        contact_comparison["exact_time_equal"] += pair["same_chord_time"]
                    if pair.get("m4c_translation_discrepancy_contact"):
                        cohorts.append("m4c_20_subset")
                    for cohort in cohorts:
                        for phase in replay.PHASES:
                            references = phase_pairs[phase].get(tuple(pair["pair"]), [])
                            primary = any(r["category"] == "FIRST_COVER_MATCH" for r in references)
                            secondary = any(r["secondary_category"] == "FIRST_COVER_MATCH" for r in references)
                            old_hit = any(r["chord_category"] == "FIRST_COVER_MATCH" or r["chord_secondary_category"] == "FIRST_COVER_MATCH" for r in references)
                            count = pair_coverage[cohort][phase]
                            count["total_pairs"] += 1
                            count["legacy_pair_absent"] += not references
                            count["primary_first_cover_hit_pairs"] += primary
                            count["secondary_first_cover_hit_pairs"] += secondary
                            count["any_reference_first_cover_hit_pairs"] += primary or secondary
                            count["references_present_no_first_cover_hit_pairs"] += bool(references) and not (primary or secondary)
                            count["chord_any_reference_first_cover_hit_pairs"] += old_hit
                for phase in replay.PHASES:
                    for reference in row["phases"][phase]["records"]:
                        if reference["chord_category"] == "FIRST_COVER_MATCH" and reference["category"] != "FIRST_COVER_MATCH":
                            selections.setdefault("Q2_legacy_reference", (case, row, pairs[tuple(reference["pair"])]))
                for block, fit in row["blocks"].items():
                    delta = F(fit["delta_linf"])
                    if maximum is None or delta > maximum[0]:
                        maximum = delta, case, row, int(block)
    _, case, row, block = maximum
    pair = next((p for p in row["pairs"] if block in p["pair"]), None)
    if pair is None:
        # Every pair omitted by the completed run has a strict swept-projection
        # no-contact proof. Retain one such pair to reproduce the maximum-fit
        # block without pretending it was an explicitly enumerated event.
        other = min(int(b) for b in row["blocks"] if int(b) != block)
        keys = sorted((block, other))
        delta = sum(F(row["blocks"][str(b)]["delta_linf"]) for b in keys)
        pair = {"pair": keys, "initial_state": -1, "rigid": replay._empty(), "chord": replay._empty(), "pd": None,
                "delta_linf_sum": str(delta), "certificate": "CERTIFIED_RIGID_ENDPOINT_MODEL" if delta == 0 else "UNCERTIFIED_NONRIGID_ENDPOINTS",
                "path": "OMITTED_PROVEN_SWEPT_SEPARATION", "same_chord_status_and_cover": True}
    selections["Q3_maximum_endpoint_residual"] = case, row, pair
    examples = {}
    loaded = {}
    for name, (case, row, pair) in selections.items():
        if case not in loaded:
            source, terminal, _ = replay._paths(case, "full")
            _, frames, _ = replay.chord.snapshot.read_snapshot(source)
            loaded[case] = frames, terminal
        frames, terminal = loaded[case]
        step = row["step"]
        start = frames[step-1]
        end = frames[step] if step < len(frames) else {**start, "geometry": replay.chord.load_geometry_csv(terminal, frames)}
        sg, eg = replay.chord.snapshot.geometry_from_frame(start), replay.chord.snapshot.geometry_from_frame(end)
        a, b = pair["pair"]
        examples[name] = {"case": case, "step": step, "comparison": pair,
                          "A0": sg.blocks[a].poly, "A1": eg.blocks[a].poly, "B0": sg.blocks[b].poly, "B1": eg.blocks[b].poly,
                          "A_ids": list(sg.blocks[a].vidx), "B_ids": list(sg.blocks[b].vidx),
                          "legacy": {p: [r for r in row["phases"][p]["records"] if r["pair"] == pair["pair"]] for p in replay.PHASES}}
    examples_path = evidence / "minimal_examples.json"
    replay.write_json(examples_path, {"schema": "eab.m5a-minimal-examples.v1", "source_summary_sha256": replay.file_hash(batch / "summary.json"), "examples": examples})
    reproduced = evidence / "minimal_examples_reproduced.json"
    if reproduced.exists():
        previous = json.loads(reproduced.read_text(encoding="utf-8"))
        replay.require(previous["complete"] and previous["source_sha256"] == replay.file_hash(examples_path)
                       and previous["code_hashes"] == replay.code_hashes(), "existing minimal-example evidence does not bind the exact same completed examples")
    else:
        replay.reproduce_examples(examples_path, reproduced)
    shutil.copyfile(batch / "summary.json", evidence / "full_summary.json")
    frozen = json.loads((ROOT / "fixtures/m5a_se2/expected.json").read_text(encoding="utf-8"))
    stats = Counter()
    for case in frozen["cases"].values():
        stats.update(case["stats"])
    replay.write_json(evidence / "frozen_summary.json", {"complete": True, "steps": 450, "cases": 15, "stats": dict(sorted(stats.items())),
                                                       "fixture_manifest_sha256": replay.file_hash(ROOT / "fixtures/m5a_se2/expected.json"),
                                                       "source_summary_sha256": replay.file_hash(batch / "summary.json"),
                                                       "scope": "Frozen prefix of one full 1810 computational run; pytest checks all450 certificates and independently reexecutes fits plus three real rotating event pairs."})
    answers = {"complete": True, "scope": "Prescribed rational SE2 endpoint model only; no physical b-DDA trajectory certification.",
               "question_1": {"chord_new_contact_pairs": 68, "translation_different_subset": 20,
                              "se2_same_chord_status_and_cover": summary["stats"].get("m4c_20_se2_chord_same", 0),
                              "se2_different_chord_status_or_cover": summary["stats"].get("m4c_20_se2_chord_different", 0),
                              "all_rigid_model_new_contacts": summary["stats"].get("rigid_new_contacts", 0),
                              "full_68_contact_cohort": dict(sorted(contact_comparison.items())),
                              "initial_separated_comparison_denominator": 17603,
                              "se2_chord_different": summary["stats"]["separated_chord_different"],
                              "translation_chord_different_historical": 790,
                              "pair_records": summary["m4c_20_subset"]},
               "question_2": {"reference_row_counts": summary["counts"], "secondary_reference_row_counts": summary["secondary_counts"], "reference_row_transitions": summary["transitions"],
                              "pair_level_cohort_coverage": {name: {phase: dict(sorted(count.items())) for phase, count in phases.items()} for name, phases in pair_coverage.items()}},
               "question_3": {"block_residual_distribution": summary["residuals"],
                              "certified_step_pairs": summary["stats"].get("CERTIFIED_RIGID_ENDPOINT_MODEL", 0),
                              "uncertified_step_pairs": summary["stats"].get("UNCERTIFIED_NONRIGID_ENDPOINTS", 0),
                              "maximum_residual": {"case": maximum[1], "step": maximum[2]["step"], "block": maximum[3], "exact": str(maximum[0])}},
               "examples": {k: {"case": e["case"], "step": e["step"], "pair": e["comparison"]["pair"]} for k, e in examples.items()}}
    replay.write_json(evidence / "three_answers.json", answers)
    q1, q3 = answers["question_1"], answers["question_3"]
    lines = ["# M5a 影子回放结果（中文证据摘要）", "", "## 范围与认证边界", "",
             f"一个完整新批次覆盖 15 例、1810 个区间、{summary['stats']['all_pairs']} 个步—无序块对。未分类为红，未分类数为 0。",
             "仅对本单选定的两条有理 SE(2) 插值轨迹计算；不声称恢复 b-DDA 步内真实轨迹。δ=0 仅认证拟合端点兼容该刚体模型；δ>0 一律未认证。",
             "M4c 的弦模型结果、相同初态特征及冻结 PD_closed 作为逐文件/逐帧哈希绑定的历史数据复用，不冒充本批次重算。旧 M4c 另有完整 450 帧新鲜重算，详见 m4c_frozen_revalidation.json。", "",
             "## 问题 1：68 对中的 20 对", "",
             f"M4c 弦模型新接触 68 对，其中平移替身状态或首盖改变 20 对。这 20 对中，刚体模型与弦模型的状态及完整首盖集合一致 {q1['se2_same_chord_status_and_cover']} 对，不同 {q1['se2_different_chord_status_or_cover']} 对。",
             f"完整 68 对群组中：完整首盖集合一致 {contact_comparison['same_complete_cover']} 对，仍接触但首盖集合改变 {contact_comparison['contact_but_cover_changed']} 对，降为窗口无接触 {contact_comparison['status_drop_to_no_contact']} 对；精确时刻相等 {contact_comparison['exact_time_equal']} 对。",
             f"刚体模型全时程共给出 {q1['all_rigid_model_new_contacts']} 个新接触步—块对。不能把这个数解释为精度提高：端点应变/舍入被替换，全部认证标签必须另看 δ。逐对记录见 three_answers.json。", "",
             "在同一 17603 个初态分离候选对分母下，SE(2) 与弦模型的状态/首盖差异为 937，平移替身与弦模型差异为 790。不能从“加入转动”推出一定更接近弦模型；刚体拟合同时移除了应变，且所有真实拟合 δ>0。两者都不因此成为物理错误判定。", "",
             "## 问题 2：legacy 参考是否为刚体模型首盖", "", "| 类别 | raw_df05 | post_df06 |", "|---|---:|---:|"]
    position = lines.index("## 问题 2：legacy 参考是否为刚体模型首盖")
    table = ["20 对逐对转移（弦模型均为 contact，全部 δ>0 未认证）：", "",
             "| 例 | 步 | 块对 | 平移替身 | SE(2) | SE(2)/弦完整首盖集合 |", "|---|---:|---|---|---|---|"]
    for record in summary["m4c_20_subset"]:
        pair_name = ",".join(map(str, record["pair"]))
        match = "同" if record["same_chord_status_and_cover"] else "异"
        table.append(f"| {record['case']} | {record['step']} | {pair_name} | {record['translation']['status']} | {record['rigid']['status']} | {match} |")
    lines[position:position] = table+[""]
    for category in sorted(set(summary["counts"]["raw_df05"]) | set(summary["counts"]["post_df06"])):
        lines.append(f"| {category} | {summary['counts']['raw_df05'].get(category,0)} | {summary['counts']['post_df06'].get(category,0)} |")
    lines += ["", "仅 FIRST_COVER_MATCH 回答分离初态下的首盖成员关系。初始相触和初始贯入另列；后者比较步初冻结 PD_closed，不伪造首入时刻。VV 双参考分别计数，完整次参考及相对 M4c 的类别转移见 three_answers.json。", "",
              "上表计数单位是参考行，不是块对。下面按无序步—块对去重；首盖命中包含主参考或 VV 次参考的并集，三个分区“命中 / 有参考但不命中 / legacy 无该对”之和等于该群组对数。", "",
              "| 群组 | 阶段 | 对数 | 任一参考首盖命中 | 有参考但不命中 | legacy 无该对 | 其中次参考命中 |", "|---|---|---:|---:|---:|---:|---:|"]
    for name, phases in pair_coverage.items():
        for phase, count in phases.items():
            replay.require(count["total_pairs"] == count["any_reference_first_cover_hit_pairs"]+count["references_present_no_first_cover_hit_pairs"]+count["legacy_pair_absent"], "pair-level legacy coverage partition failed")
            lines.append(f"| {name} | {phase} | {count['total_pairs']} | {count['any_reference_first_cover_hit_pairs']} | {count['references_present_no_first_cover_hit_pairs']} | {count['legacy_pair_absent']} | {count['secondary_first_cover_hit_pairs']} |")
    lines += ["",
              "## 问题 3：残差与认证计数", "",
              f"逐块拟合 {summary['residuals']['count']} 次：δ=0 有 {summary['residuals']['zero']} 次，δ>0 有 {summary['residuals']['nonzero']} 次。认证步—块对 {q3['certified_step_pairs']}，未认证 {q3['uncertified_step_pairs']}。",
              "残差为端点最大 L∞ 顶点误差，精确有理值随结果保留；包含应变、拟合近似与快照舍入的合效应，不能单凭该值分解三者。", "",
              "| 分位 | 显示值（精确值见 JSON） |", "|---|---:|"]
    lines += [f"| {key} | {value:.17g} |" for key, value in summary["residuals"]["quantiles_display"].items()]
    lines += ["", "## 最小复现与冻结门", "",
              "三个问题分别有独立小例，保存原始两端顶点、持久编号、拟合及参考比较。minimal_examples_reproduced.json 已通过实际 SE(2) 路径再执行。",
              "```powershell", "$env:PYTHONDONTWRITEBYTECODE='1'", "$env:TEMP='D:/eab-wt/cx-e2/reports/codex/M5a_evidence/tmp/replay'", "$env:TMP=$env:TEMP",
              "python -X utf8 tools/m5a_se2_replay.py reproduce --examples D:/eab-wt/cx-e2/reports/codex/M5a_evidence/minimal_examples.json --out D:/eab-wt/cx-e2/reports/codex/M5a_evidence/tmp/replay/example_fresh.json", "```", "",
              "冻结来自同一完整批次的 15×30 前缀，不拼接中断运行。pytest 检查全部 450 帧证书、分区闭合、保守剔除守恒、残差认证与 15 个真实拟合，并重算 3 个真实非零转角事件对；不声称 pytest 重算了全部 450 帧根隔离。", "",
              "## 运行纪律与遗留", "",
              "全时程大记录位于被忽略的 tmp/replay/full_r1，不纳入提交；永久摘要及每个冻结文件均小于 1 MB。",
              "revalidate-m4c 子命令使用绝对 --out 路径。第一次用相对路径的完整计算在发布元数据时失败，已整批作废并从头重跑 r2；未拼接、未改旧夹具。",
              "PARTIAL：一般 δ>0 首盖稳定性证书未实现；真实 DDA 连续运动未恢复；单环和单步每块≤90° 的模型域不泛化到材料多环、近π大转角或SE(3)。", ""]
    (evidence / "replay_report.md").write_text("\n".join(lines), encoding="utf-8")
    for name in ("full_summary.json", "frozen_summary.json", "three_answers.json", "minimal_examples.json", "minimal_examples_reproduced.json", "replay_report.md"):
        replay.require((evidence / name).stat().st_size < 1_000_000, "published evidence exceeds size cap: "+name)
    print("M5A_REPLAY_DELIVERY_GREEN", q1["se2_same_chord_status_and_cover"], q1["se2_different_chord_status_or_cover"])


if __name__ == "__main__":
    main()
