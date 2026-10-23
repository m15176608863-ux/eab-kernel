"""Persistent binary64 input subset of the accepted T1b thickness diagnostics.

Only input geometry is regenerated, using the existing adapter. Threshold
expectations are read from a byte-identical tests/data copy of the T1b summary, never
computed from either solver by this module. No external archive or Temp path
is a runtime dependency. The 7 sample records and 18 controls intentionally
retain their source identities; six models occur in both groups (19 unique).
"""
from __future__ import annotations

import argparse
from fractions import Fraction as Q
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from eab.adapters.tia2d import g1_morphology

SUMMARY = ROOT / "tests/data/eab2_c3l3_thickness_summary.json"
SOURCE_SUMMARY = "reports/codex/T1b_evidence/acceptance_fix/thickness_summary.json"
SUMMARY_SHA256 = "64b39696af3b91b459726d6ac58515c7edc67264669196ada32216c35bb1a920"
SAMPLE_NAMES = (
    "thickness_00_07.json.gz", "thickness_00_08.json.gz",
    "thickness_01_07.json.gz", "thickness_02_07.json.gz",
    "thickness_03_07.json.gz", "thickness_04_02.json.gz",
    "thickness_05_02.json.gz",
)
FAMILIES = (
    ("1/64", 1, "1/2"), ("1/128", 1, "1/4"),
    ("1/256", 2, "1/2"), ("1/256", 2, "1/4"),
    ("1/64", 2, "1/2"), ("1/64", 2, "1/4"),
)
CONTROL_RATIOS = ("3/16", "1/4", "1/2")


def canonical(value):
    value = Q(value)
    return f"{value.numerator}/{value.denominator}"


def binary64_exact(value):
    """Reject rounding/overflow; the ABI receives the original value or nothing."""
    value = Q(value)
    try:
        displayed = float(value)
    except OverflowError:
        return False
    return math.isfinite(displayed) and Q(displayed) == value


def input_domain_failures(model):
    """Inspect every scalar actually transported to the binary64 assembly ABI."""
    failures = []
    for body in model.bodies:
        vertices = body.original_vertices or body.vertices
        fields = [(f"vertices[{i}][{k}]", value)
                  for i, point in enumerate(vertices) for k, value in enumerate(point)]
        fields += [(f"{name}[{i}]", value)
                   for name in ("reference_point", "dof_anchor", "dead", "live")
                   for i, value in enumerate(getattr(body, name))]
        for field, value in fields:
            if not binary64_exact(value):
                failures.append(dict(body_id=body.body_id, field=field, exact=canonical(value)))
    if not binary64_exact(model.mu):
        failures.append(dict(body_id=None, field="mu", exact=canonical(model.mu)))
    return failures


def input_fingerprint(model):
    """Canonical exact input identity, not a solver or contact-output identity."""
    bodies = []
    for body in model.bodies:
        bodies.append(dict(body_id=body.body_id,
            vertices=[[canonical(v) for v in p] for p in (body.original_vertices or body.vertices)],
            boundary_type=body.boundary_type, dof_mask=body.dof_mask,
            reference_point=list(map(canonical, body.reference_point)),
            dof_anchor=list(map(canonical, body.dof_anchor)),
            dead=list(map(canonical, body.dead)), live=list(map(canonical, body.live))))
    value = dict(bodies=bodies, pairs=model.pairs, completeness=model.completeness,
                 profile=model.profile, mu=canonical(model.mu))
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                    ensure_ascii=True).encode("utf-8")).hexdigest()


def _load_summary():
    raw = SUMMARY.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SUMMARY_SHA256:
        raise ValueError("T1b thickness frozen summary integrity mismatch")
    value = json.loads(raw)
    if value.get("format") != "tia2d.t1b.thickness.summary.v1" or value.get("complete") is not True:
        raise ValueError("incomplete or unsupported T1b thickness source")
    if len(value["rows"]) != 39 or len(value["thick_controls"]) != 18:
        raise ValueError("T1b thickness source entry count mismatch")
    return value


def _parameters(row):
    ratio = Q(row["ratio"])
    return dict(family="sawtooth", height=2 * ratio,
                amplitude=2 * ratio * Q(row["relative_amplitude"]),
                tilt=Q(3, 32), periods=row["periods"], phase=Q(0),
                asymmetry=Q(row["asymmetry"]))


def _metadata(row, group, source_name, fingerprint):
    threshold = canonical(row["exact_threshold"])
    if row["attained"] is not True:
        raise ValueError("selected thickness source must have a certified closed threshold")
    return dict(source_group=group, source_name=source_name,
        source_summary=SOURCE_SUMMARY, input_fixture=SUMMARY.relative_to(ROOT).as_posix(),
        source_summary_sha256=SUMMARY_SHA256,
        source_revision="e757883", input_sha256=fingerprint,
        parameters={name: row[name] for name in ("ratio", "relative_amplitude", "periods", "asymmetry")},
        expected_threshold=threshold, expected_attained=True)


def _records():
    summary = _load_summary()
    entries, rejected = [], []
    for row in summary["rows"]:
        model = g1_morphology(**_parameters(row)).assembly
        failures = input_domain_failures(model)
        if failures:
            rejected.append(dict(source_name=row["case"], ratio=row["ratio"],
                                 reason="non_binary64_exact_input", failed_fields=len(failures),
                                 first_failure=failures[0]))
            continue
        metadata = _metadata(row, "sample", row["case"], input_fingerprint(model))
        entries.append(("thickness/sample/" + row["case"].removesuffix(".json.gz"), model, metadata))
    if tuple(item[2]["source_name"] for item in entries) != SAMPLE_NAMES or len(rejected) != 32:
        raise ValueError("binary64 thickness sample partition changed")
    for index, row in enumerate(summary["thick_controls"]):
        expected_family = FAMILIES[index // 3]
        actual_family = (row["relative_amplitude"], row["periods"], row["asymmetry"])
        if actual_family != expected_family or row["ratio"] != CONTROL_RATIOS[index % 3]:
            raise ValueError("thick-control parameter grid changed")
        if Q(row["exact_threshold"]) != 0 or row.get("certificate_arithmetic") is not True:
            raise ValueError("thick-control archived closed-zero certificate missing")
        model = g1_morphology(**_parameters(row)).assembly
        if input_domain_failures(model):
            raise ValueError("selected thick control is not binary64 exact")
        source_name = f"thick_controls.json.gz#/{index}"
        metadata = _metadata(row, "thick_control", source_name, input_fingerprint(model))
        entries.append((f"thickness/control/{index:02d}", model, metadata))
    if len(entries) != 25 or len({row[2]["input_sha256"] for row in entries}) != 19:
        raise ValueError("thickness selected/unique input count mismatch")
    return entries, rejected


def thickness_cases():
    """Yield (case_id, Assembly2, queries) for fresh_case(..., 'thickness', ...).

    Three exact binary64 limit inputs and one critical query per source entry.
    All threshold expectations come from the accepted archived T1b summary.
    This function neither calls a solver nor reads the external evidence store.
    """
    entries, _ = _records()
    for name, model, metadata in entries:
        queries = [dict(kind="limit", mu=mu, thickness_source=metadata)
                   for mu in ("0/1", "1/64", "1/4")]
        queries.append(dict(kind="critical", mu_max_bits="3ff0000000000000", max_steps=64,
                            expected_threshold=metadata["expected_threshold"],
                            expected_attained=metadata["expected_attained"], thickness_source=metadata))
        yield name, model, queries


def thickness_inventory():
    """Inspectable source/domain audit only, not a numerical solver validation."""
    entries, rejected = _records()
    return dict(format="eab2.c3l3.thickness.inputs.v1", source_summary=SOURCE_SUMMARY,
        input_fixture=SUMMARY.relative_to(ROOT).as_posix(),
        source_summary_sha256=SUMMARY_SHA256, source_samples=39,
        binary64_samples=7, outside_binary64_domain=32, thick_controls=18,
        selected_source_entries=25, unique_models=19, duplicate_source_models=6,
        limit_queries=75, critical_queries=25,
        selected=[dict(case_id=name, **metadata) for name, _, metadata in entries], excluded=rejected)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    print(json.dumps(thickness_inventory(), ensure_ascii=False, indent=2))
