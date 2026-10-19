"""P0 diagnostic tables, NOT an eab2.case.v1 export or C++ performance set.

Creates a new immutable run directory; an interrupted run is invalid and may
not be resumed. Exact threshold claims come only from critical_parameter,
never from the separately labelled actual-vertex closed-form reference.
"""
from dataclasses import replace
import argparse
import csv
from fractions import Fraction as Q
import hashlib
import json
from pathlib import Path
import platform
import sys
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from eab.adapters.tia2d import (audit_binary64_chain, g1, g1_reference_from_vertices,
                              g5, g5_reference_from_vertices, g5_seed)
from eab.kernel2d.contacts import assemble_contact_set2
from eab.kernel2d.lock import translation_lock_certificate
from eab.kernel2d.mobility import first_order_free_twists
from eab.kernel2d.statics import critical_parameter, limit_load_ideal_exact_2d
from eab.kernel2d.sensitivity import evaluate_sensitivity2
from tia2d_cases import wire
from tia2d_provenance import git_provenance


def case_specs(tier="p0"):
    specs = []
    for ih, h in enumerate((Q(1), Q(3, 2), Q(2))):
        for it, t in enumerate((Q(0), Q(1, 32), Q(1, 8), Q(1, 4), Q(17, 64))):
            specs.append(dict(case_id=f"g1_koureas_h{ih}_t{it}", family="TIA-G1",
                              kwargs=dict(t=t, height=h, mu=Q(0))))
    for orientation in ("unreversed", "reverse_i1"):
        for it, t in enumerate((Q(0), Q(1, 32), Q(1, 4), Q(17, 64))):
            specs.append(dict(case_id=f"g1_{orientation}_t{it}", family="TIA-G1",
                              kwargs=dict(t=t, height=Q(1), orientation=orientation, mu=t)))
    specs.append(dict(case_id="g1_slender", family="TIA-G1",
                      kwargs=dict(t=Q(1, 4), height=Q(1, 4), mu=Q(15, 128))))
    for n in (3, 5, 7):
        for im, mu in enumerate((Q(0), Q(1, 4), Q(1), Q(2))):
            specs.append(dict(case_id=f"g5_n{n}_mu{im}", family="TIA-G5", kwargs=dict(n=n, mu=mu)))
    for ih, height in enumerate((Q(3, 8), Q(3, 2))):
        for im, mu in enumerate((Q(1, 4), Q(2))):
            specs.append(dict(case_id=f"g5_height{ih}_mu{im}", family="TIA-G5", kwargs=dict(height=height, mu=mu)))
    for ip, pressure in enumerate((Q(1, 4), Q(2))):
        for im, mu in enumerate((Q(1, 4), Q(2))):
            specs.append(dict(case_id=f"g5_pressure{ip}_mu{im}", family="TIA-G5", kwargs=dict(pressure=pressure, mu=mu)))
    specs.append(dict(case_id="g5_unequal", family="TIA-G5",
        kwargs=dict(height=Q(1, 2), pressure=Q(2), widths=(Q(1), Q(1, 2), Q(1)), mu=Q(3, 4))))
    for name, mask, anchor, expected in (("y_free", (1, 1, 0), None, Q(2, 3)),
                                        ("rotation_free_mid", (1, 0, 1), None, Q(4, 3)),
                                        ("rotation_free_origin", (1, 0, 1), (0, 0), Q(1, 3))):
        specs.append(dict(case_id="g5_" + name, family="TIA-G5",
            kwargs=dict(mu=Q(2), dof_mask=mask, dof_anchor=anchor), counterexample_expected=expected))
    if tier == "small":
        selected = {"g1_koureas_h0_t1", "g1_slender", "g5_n3_mu1", "g5_rotation_free_mid"}
        specs = [spec for spec in specs if spec["case_id"] in selected]
    elif tier != "p0":
        raise ValueError("unknown diagnostic tier")
    return tuple(specs)


def _timed(function, *args, **kwargs):
    start = time.perf_counter()
    result = function(*args, **kwargs)
    return result, time.perf_counter() - start


def _limit_summary(result):
    return dict(call_status=result.call_status, mathematical_status=result.mathematical_status,
        display_status=result.display_status, value=wire(result.exact_value), reason=result.reason,
        has_exact_point=result.feasible_point is not None, has_exact_ray=result.improving_ray is not None,
        has_exact_dual=result.exact_y is not None, has_farkas=result.farkas is not None)


def _mobility_summary(result):
    return dict(call_status=result.call_status, mathematical_status=result.mathematical_status,
        cone_is_zero=result.cone_is_zero, exact_rank=result.exact_rank, free_dofs=len(result.dofs),
        normalized_value=wire(result.normalized_value), ray_count=len(result.rays),
        lineality_dimension=len(result.lineality), zero_certificate_count=len(result.zero_certificates),
        interpretation=result.interpretation, reason=result.reason)


def _g5_sensitivities(limit, reference):
    if not reference["applicable"]:
        return dict(status="unsupported", reason="released_plate_mask", parameters={}), {}, {}
    mu, pressure, height = reference["mu"], reference["pressure"], reference["h"]
    arm = reference["L"] - reference["b"]
    slide = {"mu": 2 * pressure, "P": 2 * mu, "h": Q(0)}
    hinge = {"mu": Q(0), "P": 4 * height / arm, "h": 4 * pressure / arm}
    records, certificates, timings = {}, {}, {}
    for parameter in ("mu", "P", "h"):
        seed = g5_seed(limit.problem, parameter)
        answer, seconds = _timed(evaluate_sensitivity2, limit, seed, parameter=parameter,
            tied_labels=("sliding", "hinging") if reference["mode"] == "tie" else (),
            negative_direction_valid=not ((parameter == "mu" and mu == 0) or (parameter == "P" and pressure == 0)))
        if reference["mode"] == "tie":
            left, right = max(slide[parameter], hinge[parameter]), min(slide[parameter], hinge[parameter])
        else:
            left = right = (slide if reference["mode"] == "sliding" else hinge)[parameter]
        expected_singular = mu == 0
        matches = (answer.differentiability == "singular" and answer.reason == "possibly_discontinuous"
                   and answer.left_derivative is None and answer.right_derivative is None) if expected_singular else (
                   answer.left_derivative == left and answer.right_derivative == right)
        records[parameter] = dict(call_status=answer.call_status, mathematical_status=answer.mathematical_status,
            differentiability=answer.differentiability, quality=answer.quality, method=answer.method,
            reason=answer.reason, left_derivative=wire(answer.left_derivative), right_derivative=wire(answer.right_derivative),
            tied_labels=list(answer.tied_labels), validity_conditions=list(answer.validity_conditions),
            closed_form_left_reference=wire(left), closed_form_right_reference=wire(right),
            singular_contract_expected=expected_singular, contract_and_reference_match=matches)
        certificates[parameter] = dict(seed=wire(seed), result=wire(answer))
        timings[parameter] = seconds
    return dict(status="computed", parameters=records), certificates, timings


def build_diagnostic(spec, *, critical_steps=10):
    model = (g1 if spec["family"] == "TIA-G1" else g5)(**spec["kwargs"])
    reference = (g1_reference_from_vertices if spec["family"] == "TIA-G1" else g5_reference_from_vertices)(model)
    audit, audit_time = _timed(audit_binary64_chain, model)
    contacts, contact_time = _timed(assemble_contact_set2, model)
    first, first_time = _timed(first_order_free_twists, model, contacts)
    limit, limit_time = _timed(limit_load_ideal_exact_2d, model, contacts)
    critical, critical_time = _timed(critical_parameter, model, contact_set=contacts,
                                    max_steps=critical_steps, mu_max=1.0 if spec["family"] == "TIA-G1" else 4.0)
    sensitivities, sensitivity_certificates, sensitivity_times = (
        _g5_sensitivities(limit, reference) if spec["family"] == "TIA-G5" else
        (dict(status="not_requested", reason="G1_threshold_sensitivity_separate", parameters={}), {}, {}))
    singles = []
    for i, body in enumerate(model.bodies):
        if not any(body.dof_mask):
            continue
        neighbors = tuple(b.vertices for j, b in enumerate(model.bodies) if j != i)
        lock, lock_time = _timed(translation_lock_certificate, body.vertices, neighbors)
        bodies = tuple(b if j == i else replace(b, boundary_type="FIXED_BODY", dof_mask=(0, 0, 0),
                       dead=(Q(0),) * 3, live=(Q(0),) * 3) for j, b in enumerate(model.bodies))
        single_model = replace(model, bodies=bodies)
        single, single_time = _timed(first_order_free_twists, single_model)
        singles.append(dict(body_id=body.body_id, fixed_neighbor_ids=[b.body_id for j, b in enumerate(model.bodies) if j != i],
            lock=dict(call_status=lock.call_status, mathematical_status=lock.mathematical_status,
                      refinement=lock.refinement, radius=wire(lock.radius), separation_ray=wire(lock.separation_ray),
                      seam_ray=wire(lock.seam_ray), cell_count=len(lock.local_cells), angular_strata=len(lock.arcs)),
            first_order=_mobility_summary(single), wallclock=dict(lock=lock_time, first_order_including_assembly=single_time)))
    checks = dict(binary64_subset=audit["binary64_subset"], contact_resolved=contacts.status == "RESOLVED",
                  geometry_and_statics_share_contact_set=first.contact_set is contacts and limit.problem is not None and limit.problem.contact_set is contacts)
    if spec["family"] == "TIA-G5":
        checks["closed_form_applicable"] = reference["applicable"]
        checks["closed_form_match"] = limit.exact_value == reference["capacity"] if reference["applicable"] else None
        checks["sensitivity_contract_match"] = (all(r["contract_and_reference_match"] for r in sensitivities["parameters"].values())
            if reference["applicable"] else None)
    else:
        checks["certified_threshold_matches_reference"] = (critical.exact_threshold == reference["threshold"]
            and critical.attained == reference["attained"]) if critical.exact_threshold is not None else None
    if "counterexample_expected" in spec:
        checks["counterexample_match"] = limit.exact_value == spec["counterexample_expected"]
    points = [dict(a=model.bodies[p.a].body_id, b=model.bodies[p.b].body_id,
                   point=wire(p.point), fp_type=p.fp_type, sources=wire(p.sources)) for p in contacts.points]
    record = dict(case_id=spec["case_id"], family=spec["family"], requested_parameters=wire(spec["kwargs"]),
        input_version="tia2d-diagnostic-input-1", profile="profile1", reference=wire(reference),
        assembly=dict(completeness=model.completeness, mu=wire(Q(model.mu)),
            bodies=[dict(body_id=b.body_id, vertices=wire(b.vertices), boundary_type=b.boundary_type,
                         dof_mask=list(b.dof_mask), reference_point=wire(b.reference_point), dof_anchor=wire(b.dof_anchor),
                         dead=wire(b.dead), live=wire(b.live)) for b in model.bodies]),
        input_audit=wire(audit), contact_set=dict(call_status=contacts.call_status, mathematical_status=contacts.mathematical_status,
            point_count=len(points), points=points, constraint_count=len(contacts.constraints), segment_count=len(contacts.segments),
            profile_applicable=contacts.status == "RESOLVED", completeness=contacts.completeness),
        first_order=_mobility_summary(first), limit=_limit_summary(limit), single_body_queries=singles, sensitivity=sensitivities,
        critical=dict(call_status=critical.call_status, mathematical_status=critical.mathematical_status,
            mu_lo=None if critical.mu_lo is None else wire(Q(critical.mu_lo)),
            mu_hi=None if critical.mu_hi is None else wire(Q(critical.mu_hi)), attained=critical.attained,
            exact_threshold=wire(critical.exact_threshold), reason=critical.reason,
            queries=critical.queries, basis_polynomial_count=len(critical.critical_polynomials)),
        wallclock=dict(clock="perf_counter", scope="in_process_diagnostic_not_cpp_performance_target",
            input_audit=audit_time, assembly=contact_time, first_order_excluding_assembly=first_time,
            limit_excluding_assembly=limit_time, critical_excluding_assembly=critical_time,
            sensitivity_excluding_limit=sensitivity_times), checks=checks)
    certificates = dict(schema="tia2d.diagnostic-certificates.v1", case_id=spec["case_id"],
        critical=wire(critical), query_limit=wire(limit), query_problem=wire(limit.problem),
        sensitivity=sensitivity_certificates,
        endpoint_problems={name: wire(getattr(critical, name).problem) for name in
            ("lower_certificate", "upper_certificate", "threshold_certificate") if getattr(critical, name) is not None})
    return record, certificates


def _write_json(path, value):
    data = (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")
    if len(data) > 1_000_000:
        raise ValueError("diagnostic JSON exceeds 1 MB; do not discard certificate fields")
    path.write_bytes(data)
    return dict(path=path.name, bytes=len(data), sha256=hashlib.sha256(data).hexdigest())


def _source_hashes():
    return {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in (
        "src/eab/adapters/tia2d.py", "src/eab/kernel2d/assembly.py", "src/eab/kernel2d/critical.py",
        "src/eab/kernel2d/contacts.py", "src/eab/kernel2d/lock.py",
        "src/eab/kernel2d/mobility.py", "src/eab/kernel2d/statics.py", "src/eab/kernel2d/sensitivity.py",
        "tools/tia2d_dataset.py", "tools/tia2d_cases.py")}


def run_dataset(directory, *, tier="p0", critical_steps=10, _output_root=None):
    """Write a diagnostic run; tests may inject an isolated output root.

The default output boundary remains ROOT. Source paths, hashes and Git
provenance always use ROOT, independently of the private test I/O boundary.
"""
    out = Path(directory).resolve()
    output_root = ROOT if _output_root is None else Path(_output_root).resolve()
    if not out.is_relative_to(output_root) or out.exists():
        raise ValueError("choose a NEW diagnostic directory inside this worktree")
    out.mkdir(parents=True)
    specs = case_specs(tier)
    records, manifest = [], []
    start = time.perf_counter()
    source_hashes = _source_hashes()
    try:
        _write_json(out / "progress.json", dict(status="RUNNING", completed=0, total=len(specs)))
        for spec in specs:
            record, certificates = build_diagnostic(spec, critical_steps=critical_steps)
            evidence = _write_json(out / (spec["case_id"] + "_certificates.json"), certificates)
            record["critical"]["certificate_reference"] = dict(**evidence, json_pointer="/critical")
            record["limit"]["certificate_reference"] = dict(**evidence, json_pointer="/query_limit")
            record["sensitivity"]["certificate_reference"] = dict(**evidence, json_pointer="/sensitivity")
            manifest.append(evidence)
            records.append(record)
            _write_json(out / "progress.json", dict(status="RUNNING", completed=len(records), total=len(specs),
                                                    last_case=spec["case_id"], seconds=time.perf_counter() - start))
        if _source_hashes() != source_hashes:
            raise ValueError("source_changed_during_diagnostic_run")
        summary = dict(schema="tia2d.diagnostic.v1", formal_case_export=False, schema_approval="pending",
            tier=tier, tool_version="tia2d-dataset-1", python=platform.python_version(),
            profile_statement="profile1: rigid, infinitesimal, unlimited compression, no cohesion, constant mu, associated flow; unsafe-side upper bound relative to Coulomb; no gravity",
            limitations=["Not eab2.case.v1", "Not a C++ performance target set", "Closed forms are references, not certificates",
                         "G1/G5 have no claimed single-block interlock", "Finite sampling is not a full-domain proof"],
            design_sha256=hashlib.sha256((ROOT / "docs/eab2_design.md").read_bytes()).hexdigest(),
            source_sha256=source_hashes,
            **git_provenance(ROOT),
            source_state="uncommitted_files_identified_by_source_sha256",
            critical_steps=critical_steps, cases=records, elapsed_seconds=time.perf_counter() - start)
        manifest.append(_write_json(out / "diagnostics.json", summary))
        columns = ("case_id", "family", "mu", "limit_status", "capacity", "reference_capacity", "reference_threshold",
                   "certified_threshold", "attained", "critical_reason", "first_order", "binary64_subset",
                   "dmu_status", "dmu_left", "dmu_right", "dP_status", "dP_left", "dP_right", "dh_status", "dh_left", "dh_right")
        with (out / "table.csv").open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=columns)
            writer.writeheader()
            for record in records:
                reference = record["reference"]
                sensitivity_columns = {}
                for parameter in ("mu", "P", "h"):
                    answer = record["sensitivity"]["parameters"].get(parameter, {})
                    sensitivity_columns.update({"d" + parameter + "_status": answer.get("differentiability"),
                        "d" + parameter + "_left": answer.get("left_derivative"), "d" + parameter + "_right": answer.get("right_derivative")})
                writer.writerow(dict(case_id=record["case_id"], family=record["family"], mu=record["assembly"]["mu"],
                    limit_status=record["limit"]["mathematical_status"], capacity=record["limit"]["value"],
                    reference_capacity=reference.get("capacity"), reference_threshold=reference.get("threshold"),
                    certified_threshold=record["critical"]["exact_threshold"], attained=record["critical"]["attained"],
                    critical_reason=record["critical"]["reason"], first_order=record["first_order"]["mathematical_status"],
                    binary64_subset=record["input_audit"]["binary64_subset"], **sensitivity_columns))
        lines = ["# TIA-G1 / TIA-G5 P0 诊断表", "", "本目录不是 eab2.case.v1 批量导出，schema 待确认；墙钟仅为本次 Python 诊断，不作为正式 C++ 性能目标。",
                 "", "profile1：刚体、小变形、无限抗压、无黏聚、恒定摩擦、关联流动；相对非关联库仑模型为不安全侧上界。无自重；G5 有显式端板预压。",
                 "闭式均从实际顶点及明确荷载重算，只作参考；认证阈值来自精确 LP 基证书。UNBOUNDED 不等于锁定，非零一阶锥不证明有限可动。",
                 "", "| 算例 | μ | L3 | 承载力 | 认证 μcrit / 原因 | 开闭 | 多体一阶锥 |", "|---|---|---|---|---|---|---|"]
        for r in records:
            threshold = r["critical"]["exact_threshold"] or r["critical"]["reason"]
            attained = r["critical"]["attained"]
            lines.append(f"| {r['case_id']} | {r['assembly']['mu']} | {r['limit']['mathematical_status']} | {r['limit']['value']} | {threshold} | {attained} | {r['first_order']['mathematical_status']} |")
        lines += ["", "每例的实际边界、掩码、锚点、参考点、荷载、xy_bits、逐点 F_p、单体平移分类、单/多体一阶锥及分查询墙钟见 [diagnostics.json](diagnostics.json)。",
                  "完整 LP 点/射线/机构与临界基多项式见各 *_certificates.json；摘要以文件 SHA256 和 JSON Pointer 引用。", ""]
        lines += ["## TIA-G5 有限承载力敏感性", "", "μ = 0 的一般裁判按双侧最优面回收锥给 singular / possibly_discontinuous，不输出斜率；表内闭式单侧参照不是裁判斜率。", "",
                  "| 算例 | 参数 | 可微性 | 左导数 | 右导数 | 方法 |", "|---|---|---|---|---|---|"]
        for record in records:
            for parameter, answer in record["sensitivity"]["parameters"].items():
                lines.append(f"| {record['case_id']} | {parameter} | {answer['differentiability']} | {answer['left_derivative']} | {answer['right_derivative']} | {answer['method']} |")
        lines += ["", "局部共享高度种子同时传播接触点、未归一化切向、力矩与端板死载；参考点固定，L1 接触骨架不变。", ""]
        (out / "README.md").write_text("\n".join(lines), encoding="utf-8", newline="\n")
        for name in ("table.csv", "README.md"):
            data = (out / name).read_bytes()
            manifest.append(dict(path=name, bytes=len(data), sha256=hashlib.sha256(data).hexdigest()))
        _write_json(out / "manifest.json", manifest)
        _write_json(out / "progress.json", dict(status="COMPLETE", completed=len(records), total=len(specs),
                                                seconds=time.perf_counter() - start))
        return summary
    except BaseException:
        _write_json(out / "progress.json", dict(status="INVALIDATED", completed=len(records), total=len(specs),
                                                reason="interrupted_or_failed_run_do_not_resume"))
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--tier", choices=("small", "p0"), default="p0")
    parser.add_argument("--critical-steps", type=int, default=10)
    args = parser.parse_args()
    result = run_dataset(args.out, tier=args.tier, critical_steps=args.critical_steps)
    print(f"diagnostic COMPLETE: {len(result['cases'])} cases; {result['elapsed_seconds']:.3f}s; NOT formal C++ performance data")


if __name__ == "__main__":
    main()
