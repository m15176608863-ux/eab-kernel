"""Independent stdlib ctypes TIA consumer; run with python -I.

Only public C-header declarations, release eab2.dll and frozen original inputs
are used. No src/eab, sibling, pybind or differential-harness import is allowed.
Frozen expected values are assertions, never inputs to the solver.
"""
from __future__ import annotations
import argparse
import ctypes as C
from fractions import Fraction
import gzip
import hashlib
import json
from pathlib import Path
import re
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASES = ("g1_unreversed_t1", "g1_slender", "g5_n3_mu0",
                 "g5_n3_mu1", "g5_n3_mu2", "g5_n3_mu3")
CONDITION_ERRATA_VERSION = "WO-C3L4-fix/20261023/branch-proof-v1"
SUPERSEDED_SINGLE_BASIS_CONDITIONS = ("临界证书基非奇异", "所列越零分量及方向保持有效")


def require(value, message):
    if not value:
        raise AssertionError(message)


def read_json(raw):
    def unique(pairs):
        out = {}
        for key, value in pairs:
            require(key not in out, "duplicate JSON key: " + key)
            out[key] = value
        return out
    return json.loads(raw, object_pairs_hook=unique)


class PublicHeader:
    """Strict reader for the deliberately small public C type vocabulary."""
    def __init__(self, path):
        self.raw = Path(path).read_bytes()
        text = re.sub(r"/\*.*?\*/|//[^\n]*", "", self.raw.decode("utf-8"), flags=re.S)
        self.types = {"uint32_t": C.c_uint32, "uint64_t": C.c_uint64, "char": C.c_char}
        self.aliases = {alias: source for source, alias in re.findall(r"typedef\s+(\w+)\s+(\w+)\s*;", text)}
        require(self.aliases.get("eab2_call_status") == "uint32_t", "public call_status must be uint32_t")
        self.structs = []
        for name, body, alias in re.findall(r"typedef\s+struct\s+(\w+)\s*\{(.*?)\}\s*(\w+)\s*;", text, re.S):
            require(name == alias, "unsupported public struct alias")
            self.types[name] = type(name, (C.Structure,), {"_fields_": [
                self.declaration(field) for field in body.split(";") if field.strip()]})
            self.structs.append(name)
        self.functions, self.return_types = {}, {}
        occurrences = re.findall(r"\b(eab2_\w+)\s*\(", text)
        for prefix, name, args in re.findall(r"([^;{}]*?)\b(eab2_\w+)\s*\(([^;{}]*?)\)\s*;", text, re.S):
            prefix = re.sub(r"^\s*#.*$", "", prefix, flags=re.M).strip()
            require(prefix.split() == ["EAB2_API", "eab2_call_status"],
                    "public prototype requires EAB2_API eab2_call_status: " + name)
            require(name not in self.functions, "duplicate public prototype: " + name)
            self.functions[name] = ([] if args.strip() == "void" else
                                    [self.declaration(arg)[1] for arg in args.split(",")])
            self.return_types[name] = "eab2_call_status"
        require(sorted(occurrences) == sorted(self.functions), "unparsed public prototype")
        require(len(self.functions) >= 31, "public sensitivity declarations absent")
        self.constants = {}
        for name, expression in re.findall(r"^\s*#define[ \t]+(EAB2_\w+)([^\n]*)", text, re.M):
            if name in {"EAB2_API", "EAB2_C_API_H"}:
                continue
            match = re.fullmatch(r"\s*UINT(32|64)_C\(\s*(0[xX][0-9a-fA-F]+|\d+)\s*\)\s*", expression)
            require(match is not None, "unsupported public integer constant: " + name)
            width, literal = match.groups()
            value = int(literal, 16 if literal.lower().startswith("0x") else 10)
            require(name not in self.constants and value < 2**int(width), "invalid/duplicate public integer constant: " + name)
            self.constants[name] = {"type": "uint" + width + "_t", "value": value}
        self.capabilities = {name: entry["value"] for name, entry in self.constants.items() if name.startswith("EAB2_CAP_")}
        require("EAB2_ABI_VERSION" in self.constants, "public ABI version absent")

    def resolve(self, name):
        if name not in self.types:
            require(name in self.aliases, "unknown public C type: " + name)
            self.types[name] = self.resolve(self.aliases[name])
        return self.types[name]

    def declaration(self, text):
        match = re.fullmatch(r"\s*(?:const\s+)?(\w+)\s*(\*)?\s*(\w+)\s*(?:\[\s*(\d+)\s*\])?\s*", text)
        require(match is not None, "unsupported public declaration: " + text)
        base, pointer, name, length = match.groups()
        kind = self.resolve(base)
        if pointer:
            kind = C.POINTER(kind)
        if length:
            kind = kind * int(length)
        return name, kind

    def new(self, short):
        out = self.resolve("eab2_" + short)()
        if hasattr(out, "struct_size"):
            out.struct_size, out.abi_version = C.sizeof(out), self.constants["EAB2_ABI_VERSION"]["value"]
        return out


class Consumer:
    def __init__(self, dll, header):
        self.path = Path(dll).resolve()
        require(self.path.is_file() and self.path.name.lower() == "eab2.dll", "only release eab2.dll is allowed")
        self.header, self.lib = PublicHeader(header), C.CDLL(str(self.path))
        self.functions = {}
        for name, args in self.header.functions.items():
            function = getattr(self.lib, name)
            function.argtypes, function.restype = args, C.c_uint32
            self.functions[name[5:]] = function
        for name in ("numeric_batch", "query2_exact_batch", "covers2_exact", "opt_solve_exact", "test_context_rendezvous"):
            require(not hasattr(self.lib, "eab2_" + name), "test export leaked: " + name)
        self.call("self_test")
        info = self.new("abi_info")
        info.requested_capabilities = sum(value for key, value in self.header.capabilities.items()
                                          if not key.startswith("EAB2_CAP_TEST_") and key not in
                                          {"EAB2_CAP_RHO", "EAB2_CAP_SE2", "EAB2_CAP_LP2"})
        self.call("get_abi_info", C.byref(info))
        require(info.supported_capabilities == info.requested_capabilities and info.unsupported_capabilities == 0,
                "production capability set differs")
        self.capability_mask, self.identity = info.supported_capabilities, bytes(info.build_identity).decode("ascii")
        self.sizes = {}
        for short in ("context", "context_options", "error_info"):
            size = C.sizeof(self.header.resolve("eab2_" + short))
            require(getattr(info, short + "_size") == size, "base ABI size mismatch: " + short)
            self.sizes["eab2_" + short] = size
        require(info.binary64_bits == 64 and info.pointer_bits == C.sizeof(C.c_void_p)*8, "base scalar/pointer domain mismatch")
        for family in ("c1", "c3l1", "c3l3", "c3l4"):
            descriptor = self.new(family + "_abi_info")
            self.call("get_" + family + "_abi_info", C.byref(descriptor))
            for field, _ in descriptor._fields_:
                if field.endswith("_size") and field != "struct_size":
                    name = "eab2_" + field[:-5]
                    size = C.sizeof(self.header.resolve(name))
                    require(getattr(descriptor, field) == size, "C ABI size mismatch: " + name)
                    self.sizes[name] = size
        self.context, options = self.new("context"), self.new("context_options")
        self.call("context_create", C.byref(options), C.byref(self.context))

    def new(self, short):
        return self.header.new(short)

    def call(self, name, *args):
        status = self.functions[name](*args)
        require(status == 0, f"{name}: call_status={status}")

    def close(self):
        self.call("context_destroy", self.context)

    def array(self, short, values):
        cls = self.header.resolve("eab2_" + short)
        return (cls * len(values))(*values)

    def text(self, value, keep):
        data = value.encode("utf-8")
        buffer = C.create_string_buffer(data)
        keep.append(buffer)
        return self.header.resolve("eab2_string")(C.cast(buffer, C.POINTER(C.c_char)), len(data))

    def texts(self, values, keep):
        array = self.array("string", [self.text(v, keep) for v in values])
        keep.append(array)
        return self.header.resolve("eab2_string_array")(len(array), C.sizeof(array._type_), array)

    def point(self, values):
        return self.header.resolve("eab2_point2_bits")(*(int(v, 16) for v in values))

    def exact(self, name, *args, retain=False):
        out = self.new("exact_result")
        self.call(name, self.context, *args, C.byref(out))
        try:
            require(out.call_status == 0 and out.byte_count and bool(out.data), "invalid owned result")
            payload = read_json(C.string_at(out.data, out.byte_count))
            return (payload, out.result) if retain else payload
        finally:
            if not retain:
                self.call("result_destroy", self.context, out.result)

    def build(self, source, expected_pairs):
        handles, ids, entries, keep, pair_results = [], [], [], [], []
        try:
            for body in source["bodies"]:
                require(body["vertex_ids"] == list(range(len(body["vertices_xy_bits"]))), "original vertex IDs must be input indices")
                vertices = self.array("point2_bits", [self.point(p) for p in body["vertices_xy_bits"]])
                request = self.new("body2_input")
                request.vertex_count, request.vertex_stride, request.vertices = len(vertices), C.sizeof(vertices._type_), vertices
                handle = self.new("body2")
                self.call("body2_create", self.context, C.byref(request), C.byref(handle))
                handles.append(handle)
                ids.append(body["body_id"])
                entry = self.new("assembly_body2")
                entry.body, entry.body_id = handle, self.text(body["body_id"], keep)
                entry.reference_point, entry.dof_anchor = self.point(body["reference_point_bits"]), self.point(body["dof_anchor_bits"])
                entry.boundary_type = {None: 0, "FIXED_BODY": 1, "FORCE_CONTROLLED_PLATE": 2}[body["boundary_type"]]
                entry.dof_mask = sum(v << i for i, v in enumerate(body["dof_mask"]))
                entries.append(entry)
            for expected in expected_pairs:
                entrance, options = self.new("entrance2"), self.new("entrance2_options")
                self.call("entrance2_create", self.context, handles[ids.index(expected["a"])], handles[ids.index(expected["b"])],
                          C.byref(options), C.byref(entrance))
                try:
                    request, out = self.new("query2_input"), self.new("query2_output")
                    points = self.array("point2_bits", [self.point(["0000000000000000"] * 2)])
                    items = self.array("query2_item", [self.new("query2_item")])
                    request.point_count, request.point_stride, request.points = 1, C.sizeof(points._type_), points
                    out.item_capacity, out.item_stride, out.items = 1, C.sizeof(items._type_), items
                    self.call("query2_batch", self.context, entrance, C.byref(request), C.byref(out))
                    require(out.item_count == 1 and items[0].call_status == 0 and items[0].mathematical_status == 1, "entrance query failed")
                    require(("OUTSIDE", "CONTACT", "OVERLAP")[items[0].body_state] == expected["state"], "raw geometry entrance mismatch")
                    pair_results.append(dict(a=expected["a"], b=expected["b"], body_state=expected["state"],
                                             topology_state=("OUTSIDE", "BOUNDARY", "INTERIOR")[items[0].topology_state]))
                finally:
                    self.call("entrance2_destroy", self.context, entrance)
            request = self.new("assembly2_input")
            array = self.array("assembly_body2", entries)
            pairs = self.array("pair2", [self.header.resolve("eab2_pair2")(ids.index(a), ids.index(b)) for a, b in source["adjacency"]])
            require(source["completeness"] == "complete" and source["profile"] == "profile1", "complete profile1 required")
            request.flags, request.profile = 3, 1
            request.body_count, request.body_stride, request.bodies = len(array), C.sizeof(array._type_), array
            request.pair_count, request.pair_stride, request.pairs = len(pairs), C.sizeof(pairs._type_), pairs
            assembly, contacts = self.new("assembly2"), self.new("contact_set2")
            self.call("assembly2_create", self.context, C.byref(request), C.byref(assembly))
            self.call("assemble_contact_set2", self.context, assembly, C.byref(contacts))
            return assembly, contacts, pair_results
        finally:
            for handle in handles:
                self.call("body2_destroy", self.context, handle)

    def l3(self, source, contacts, query):
        loads = []
        for body in source["bodies"]:
            load, raw = self.new("body_load2"), body["load_source"]
            require(raw["kind"] == "explicit_wrench_about_reference", "unsupported original load source")
            for k in range(3):
                load.dead_bits[k], load.live_bits[k] = int(raw["dead_bits"][k], 16), int(raw["live_bits"][k], 16)
            loads.append(load)
        array = self.array("body_load2", loads)
        finite = query["kind"] == "limit"
        request = self.new("limit2_input" if finite else "critical_parameter_input")
        request.body_count, request.body_stride, request.loads = len(array), C.sizeof(array._type_), array
        if finite:
            request.mu_bits = int(query.get("mu_bits", source["mu_bits"]), 16)
        else:
            request.mu_max_bits = int(query.get("mu_max_bits", "3ff0000000000000"), 16)
            request.max_steps, request.parameter = query.get("max_steps", 64), 1
        return self.exact("solve_limit2" if finite else "critical_parameter", contacts, C.byref(request), retain=True)

    def sensitivity(self, base, queries):
        keep, channels = [], []
        first = queries[0]["geometry_seed"]
        for query in queries:
            seed = query["geometry_seed"]
            require(seed["body_ids"] == first["body_ids"] and seed["vertex_ids"] == first["vertex_ids"] and len(seed["parameters"]) == 1,
                    "frozen geometry seed identity mismatch")
            channel = self.new("sensitivity_channel2")
            channel.parameter = self.text(seed["parameters"][0], keep)
            channel.positive_direction_valid, channel.negative_direction_valid = int(query["direction_domain"]["positive"]), int(query["direction_domain"]["negative"])
            channel.validity_conditions = self.texts(query["declared_validity_conditions"], keep)
            channel.tied_labels = self.texts(query.get("tied_labels", []), keep)
            channels.append(channel)
        request = self.new("sensitivity2_input")
        request.parameter_count = request.channel_count = len(channels)
        request.output_count = 1
        request.body_count, request.vertex_count = len(first["body_ids"]), len(first["vertex_ids"])
        array = self.array("sensitivity_channel2", channels)
        request.channel_stride, request.channels = C.sizeof(array._type_), array
        request.body_ids = self.texts(first["body_ids"], keep)
        vertices = self.array("sensitivity_vertex2", [self.header.resolve("eab2_sensitivity_vertex2")(self.text(body, keep), vertex)
                                                   for body, vertex in first["vertex_ids"]])
        request.vertex_stride, request.vertex_ids = C.sizeof(vertices._type_), vertices
        for name in ("vertices", "dead", "live", "dof_anchor"):
            setattr(request, name, self.texts([v for q in queries for row in q["geometry_seed"][name][0] for v in row], keep))
        request.mu = self.texts([q["geometry_seed"]["mu"][0] for q in queries], keep)
        return self.exact("evaluate_sensitivity2", base, C.byref(request))


def cases(directory, selected):
    manifest, seen = read_json((directory / "manifest.json").read_bytes()), set()
    for item in manifest["cases"]:
        if item["case_id"] not in selected:
            continue
        source, audit, queries = None, None, {}
        for part in item["parts"]:
            raw = gzip.decompress((directory / (part["path"] + ".gz")).read_bytes())
            require(len(raw) == part["bytes"] and hashlib.sha256(raw).hexdigest() == part["sha256"], "frozen fragment integrity")
            record = read_json(raw)
            require(source is None or source == record["assembly"], "fragment source mismatch")
            source, audit = record["assembly"], record["input_audit"]
            for index, query in zip(part["query_indices"], record["queries"], strict=True):
                require(index not in queries, "duplicate query fragment")
                queries[index] = query
        require(set(queries) == set(range(item["query_count"])), "incomplete frozen case")
        seen.add(item["case_id"])
        yield item["case_id"], source, audit, [queries[i] for i in sorted(queries)]
    require(seen == set(selected), "requested case absent")


def compare(actual, expected, fields, where):
    for field in fields:
        require(actual.get(field) == expected.get(field), f"{where}.{field}: {actual.get(field)!r} != {expected.get(field)!r}")


def compare_derived_seed(channel, query, where):
    require("derived_seed" in channel and "seed" in query, where + ": missing derived seed field")
    actual, expected = channel["derived_seed"], query["seed"]
    require((actual is None) == (expected is None), where + ": derived seed presence mismatch")
    if actual is not None:
        compare(actual, expected, ("parameter", "dA", "db", "dc"), where)


def as_set(values):
    return sorted(json.dumps(v, sort_keys=True, ensure_ascii=True, separators=(",", ":")) for v in values)


def compare_validity_conditions(result, expected, threshold):
    actual, frozen = result["validity_conditions"], expected["validity_conditions"]
    if as_set(actual) == as_set(frozen):
        return None
    revised = [value for value in frozen if value not in SUPERSEDED_SINGLE_BASIS_CONDITIONS]
    require(threshold and result.get("method") == "branch_certificate" and as_set(actual) == as_set(revised),
            f"validity_conditions {actual!r} != {frozen!r}")
    return dict(version=CONDITION_ERRATA_VERSION, old=frozen, new=actual,
                rationale="K bracket replaces single-basis implicit assumptions; all other conditions remain exact")


def compare_threshold_labels(result, expected, critical):
    """Check internal certificate consistency, NOT an independent K proof.

    Full raw-geometry polynomial verification is the independent L4 harness's
    separate gate. This stdlib consumer records basis-dependent differences.
    """
    certificate = result.get("branch_certificate")
    if certificate is None:
        require(as_set(result["tied_labels"]) == as_set(expected["tied_labels"]), "sensitivity set mismatch: tied_labels")
        return None
    require(certificate["version"] == 1 and certificate["order"] == "epsilon_then_eta", "branch certificate schema")
    require(certificate["search_domain"] == critical["search_domain"], "branch original search domain binding")
    labels = []
    for name, sign, field in (("forward", 1, "right_derivative"), ("reverse", -1, "left_derivative")):
        branch = certificate[name]
        require(branch["status"] in ("certified", "unresolved"), "branch status")
        if branch["status"] == "unresolved":
            require(result[field] is None, "unproved direction must be null")
            continue
        slope = Fraction(branch["s"])
        require(result[field] is not None and Fraction(result[field]) == sign * slope, "branch slope sign mapping")
        require(branch["lower"] is not None and branch["upper"] is not None, "both bracket witnesses required")
        require(branch["upper"]["point"] is not None and branch["upper"]["ray"] is not None, "upper primal point/ray required")
        for candidate in branch["candidate_branches"]:
            seen = set()
            for component in candidate["components"]:
                label = component["label"]
                identity = (component["index"], as_set([label])[0])
                require(identity not in seen, "duplicate branch crossing component")
                seen.add(identity)
                require(Fraction(component["s"]) == slope, "branch crossing slope inconsistent")
                if candidate.get("singular", False):
                    coefficients = list(map(Fraction, component["leading_polynomial"]))
                    order = component["leading_epsilon_order"]
                    require(type(order) is int and order >= 0 and len(coefficients) >= 2
                            and coefficients[-1] == 1, "singular candidate polynomial metadata")
                    require(sum(value * slope**i for i, value in enumerate(coefficients)) == 0,
                            "singular candidate polynomial root inconsistent")
                else:
                    partial_mu = Fraction(component["partial_mu"])
                    require(partial_mu != 0 and -Fraction(component["partial_parameter"]) / partial_mu == slope,
                            "branch crossing slope inconsistent")
                if label not in labels:
                    labels.append(label)
    require(as_set(result["tied_labels"]) == as_set(labels), "branch tied labels differ from matching candidate components")
    if as_set(labels) != as_set(expected["tied_labels"]):
        return dict(frozen=expected["tied_labels"], actual=labels,
                    policy="basis_dependent; internal component consistency only; independent K proof belongs to L4 gate")
    return None


def run_case(client, name, source, audit, queries):
    started = time.perf_counter()
    assembly, contacts, pair_results = client.build(source, audit["exact_pair_states"])
    bases, results, checks = {}, {}, []
    try:
        for query in queries:
            kind, expected = query["kind"], query["result"]
            if kind == "sensitivity":
                continue
            if kind == "assembly":
                result = client.exact("contact_set2_export_exact", contacts)
                compare(result, expected, ("mathematical_status", "completeness", "reason"), name + ".contacts")
                require(as_set([x["label"] for x in result["constraints"]]) == as_set([x["label"] for x in expected["constraints"]]), "labelled contact skeleton mismatch")
            elif kind == "first_order":
                result = client.exact("first_order_mobility", contacts)
                compare(result, expected, ("mathematical_status", "cone_is_zero", "exact_rank", "reason"), name + ".first_order")
            elif kind == "lock":
                ids = [b["body_id"] for b in source["bodies"]]
                request = client.new("lock2_input")
                request.moving_index = ids.index(query["moving_body"])
                array = (C.c_uint64 * len(query["fixed_neighbors"]))(*(ids.index(v) for v in query["fixed_neighbors"]))
                request.neighbor_count, request.neighbor_stride, request.neighbors = len(array), C.sizeof(C.c_uint64), array
                result = client.exact("query_lock", assembly, C.byref(request))
                compare(result, expected, ("mathematical_status", "status", "refinement", "reason"), name + ".lock")
            else:
                require(kind in ("limit", "critical"), "unsupported consumer query")
                result, bases[kind] = client.l3(source, contacts, query)
                results[kind] = result
                fields = ("mathematical_status", "exact_value", "reason") if kind == "limit" else ("mathematical_status", "exact_threshold", "attained", "reason")
                compare(result, expected, fields, name + "." + kind)
            checks.append(dict(kind=kind, observable=query["observable"], moving_body=query.get("moving_body"),
                               mathematical_status=result.get("mathematical_status"), refinement=result.get("refinement"), status="PASS"))
        slopes = []
        for target, binding in (("limit", "limit_query_ref"), ("critical", "threshold_query_ref")):
            group = [q for q in queries if q["kind"] == "sensitivity" and binding in q]
            if not group:
                continue
            require(all(q[binding] == target for q in group), "unexpected base query binding")
            payload = client.sensitivity(bases[target], group)
            require((payload["parameter_count"], payload["output_count"], payload["channel_count"]) == (len(group), 1, len(group)), "channel dimensions")
            require(payload["jacobian_shape"] == [1, len(group)] and payload["jacobian_layout"] == "output_major_channel_minor", "Jacobian layout")
            require(len(payload["channels"]) == len(group) == len(payload["jacobian"]), "channel length")
            for i, (channel, query) in enumerate(zip(payload["channels"], group, strict=True)):
                result, expected = channel["result"], query["result"]
                compare(result, expected, ("differentiability", "quality", "parameter", "sensitivity_model", "reason",
                                          "directional_derivative", "right_derivative", "left_derivative"), name + ".sensitivity")
                condition_errata = compare_validity_conditions(result, expected, target == "critical")
                disposition = compare_threshold_labels(result, expected, results["critical"]) if target == "critical" else None
                if target != "critical":
                    require(as_set(result["tied_labels"]) == as_set(expected["tied_labels"]), "sensitivity set mismatch: tied_labels")
                compare_derived_seed(channel, query, name + ".propagation")
                directions = {"D_plus": result["right_derivative"], "D_minus": None}
                if result["left_derivative"] is not None:
                    value = -Fraction(result["left_derivative"])
                    directions["D_minus"] = f"{value.numerator}/{value.denominator}"
                require(directions == query["directional_values"], "signed directional values mismatch")
                require(payload["jacobian"][i] == (result["directional_derivative"] if result["differentiability"] == "smooth" else None), "incorrect/uncertified Jacobian")
                slopes.append(dict(observable=query["observable"], differentiability=result["differentiability"], quality=result["quality"],
                                   directional_values=directions, derivative=result["directional_derivative"], reason=result["reason"],
                                   tied_labels=result["tied_labels"], validity_conditions=result["validity_conditions"],
                                   tied_label_disposition=disposition, condition_errata=condition_errata, status="PASS"))
        row = dict(case_id=name, status="PASS", pair_queries=len(audit["exact_pair_states"]), chain_checks=len(checks), sensitivity_queries=len(slopes),
                   limit_status=results["limit"]["mathematical_status"], exact_value=results["limit"]["exact_value"],
                   exact_threshold=results["critical"]["exact_threshold"], attained=results["critical"]["attained"],
                   entrance=pair_results, chain=checks, sensitivity=slopes, seconds=time.perf_counter()-started)
        print(f"{name}: value={row['exact_value']} threshold={row['exact_threshold']} attained={row['attained']} sensitivity={len(slopes)} PASS", flush=True)
        for slope in slopes:
            print(f"  {slope['observable']}: {slope['differentiability']} D+={slope['directional_values']['D_plus']} "
                  f"D-={slope['directional_values']['D_minus']} reason={slope['reason']}", flush=True)
            if slope["condition_errata"] is not None:
                print("    condition_errata=" + slope["condition_errata"]["version"], flush=True)
        return row
    finally:
        for token in bases.values():
            client.call("result_destroy", client.context, token)
        client.call("contact_set2_destroy", client.context, contacts)
        client.call("assembly2_destroy", client.context, assembly)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dll", type=Path, required=True)
    parser.add_argument("--header", type=Path, default=ROOT / "eab2/include/eab2/c_api.h")
    parser.add_argument("--fixtures", type=Path, default=ROOT / "fixtures/eab2_cases/tia2d-2/formal_20261019_02/binary64")
    parser.add_argument("--case", action="append")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    require(args.dll.is_absolute(), "--dll must be absolute")
    client = Consumer(args.dll, args.header)
    try:
        rows = [run_case(client, *item) for item in cases(args.fixtures, args.case or DEFAULT_CASES)]
        report = dict(status="PASS", consumer="independent_stdlib_ctypes", python_isolated=bool(sys.flags.isolated),
                      imports_contract="No src/eab, pybind, sibling or differential-harness imports",
                      dll=str(client.path), dll_sha256=hashlib.sha256(client.path.read_bytes()).hexdigest(),
                      header_sha256=hashlib.sha256(client.header.raw).hexdigest(), build_identity=client.identity,
                      capability_mask=client.capability_mask, structures=client.sizes, cases=rows,
                      sensitivity_queries=sum(row["sensitivity_queries"] for row in rows), mismatch=0)
    finally:
        client.close()
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"EAB2_TIA_CONSUMER cases={len(rows)} sensitivity={report['sensitivity_queries']} mismatch=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
