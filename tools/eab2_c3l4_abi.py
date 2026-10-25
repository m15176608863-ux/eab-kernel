"""C3-L4 ctypes transport; no expected-side arithmetic lives here."""
from __future__ import annotations

import ctypes as C
from fractions import Fraction as Q

from eab2_c3l1_abi import (AbiInfo, ExactResult, Handle, HEADER, Text, U32, U64,
                         initialized)
from eab2_c3l3_diff import (BodyLoad, C3L3Dll, CriticalInput, LimitInput, bits,
                          read_json, require)


class StringArray(C.Structure):
    _fields_ = [("value_count", U64), ("value_stride", U64), ("values", C.POINTER(Text))]


class SensitivityVertex(C.Structure):
    _fields_ = [("body_id", Text), ("vertex_id", U64)]


class SensitivityChannel(C.Structure):
    _fields_ = HEADER + [("parameter", Text), ("positive_direction_valid", U32),
        ("negative_direction_valid", U32), ("validity_conditions", StringArray),
        ("tied_labels", StringArray)]


class SensitivityInput(C.Structure):
    _fields_ = HEADER + [(name, U64) for name in
        ("parameter_count", "output_count", "channel_count", "body_count", "vertex_count", "channel_stride")]
    _fields_ += [("channels", C.POINTER(SensitivityChannel)), ("body_ids", StringArray),
        ("vertex_stride", U64), ("vertex_ids", C.POINTER(SensitivityVertex))]
    _fields_ += [(name, StringArray) for name in ("vertices", "dead", "live", "dof_anchor", "mu")]


class C3L4Info(C.Structure):
    _fields_ = HEADER + [(name, U32) for name in ("string_array_size", "sensitivity_vertex2_size",
        "sensitivity_channel2_size", "sensitivity2_input_size", "reserved", "reserved2")]


def pack_request(queries):
    """Own every backing byte/array until the synchronous ABI call returns."""
    require(bool(queries), "empty sensitivity batch")
    keep = []
    def text(value):
        data = value.encode("utf-8")
        keep.append(data)
        return Text(data, len(data))
    def strings(values):
        array = (Text * len(values))(*(text(value) for value in values))
        keep.append(array)
        return StringArray(len(values), C.sizeof(Text), array)
    first = queries[0]["geometry_seed"]
    jets = [query["geometry_seed"] for query in queries]
    require(all(jet["body_ids"] == first["body_ids"] and jet["vertex_ids"] == first["vertex_ids"]
                and len(jet["parameters"]) == 1 for jet in jets), "batch geometry ID mismatch")
    channels = []
    for query, jet in zip(queries, jets):
        channel = initialized(SensitivityChannel)
        channel.parameter = text(jet["parameters"][0])
        channel.positive_direction_valid = int(query["direction_domain"]["positive"])
        channel.negative_direction_valid = int(query["direction_domain"]["negative"])
        channel.validity_conditions = strings(query["declared_validity_conditions"])
        channel.tied_labels = strings(query.get("declared_tied_labels", []))
        channels.append(channel)
    channel_array = (SensitivityChannel * len(channels))(*channels)
    vertices = (SensitivityVertex * len(first["vertex_ids"]))(*(
        SensitivityVertex(text(body), vertex) for body, vertex in first["vertex_ids"]))
    keep.extend((channel_array, vertices))
    request = initialized(SensitivityInput)
    request.parameter_count = request.channel_count = len(queries)
    request.output_count = 1
    request.body_count, request.vertex_count = len(first["body_ids"]), len(vertices)
    request.channel_stride, request.channels = C.sizeof(SensitivityChannel), channel_array
    request.body_ids = strings(first["body_ids"])
    request.vertex_stride, request.vertex_ids = C.sizeof(SensitivityVertex), vertices
    for name in ("vertices", "dead", "live", "dof_anchor"):
        setattr(request, name, strings([value for jet in jets for row in jet[name][0] for value in row]))
    request.mu = strings([jet["mu"][0] for jet in jets])
    return request, keep


class C3L4Dll(C3L3Dll):
    def __init__(self, path):
        super().__init__(path)
        for name, args in (("get_c3l4_abi_info", [C.POINTER(C3L4Info)]),
            ("evaluate_sensitivity2", [Handle, Handle, C.POINTER(SensitivityInput), C.POINTER(ExactResult)])):
            function = getattr(self.lib, "eab2_" + name)
            function.argtypes, function.restype = args, U32
            setattr(self, name, function)
        info = initialized(AbiInfo)
        info.requested_capabilities = 524288
        self.check(self.get_abi_info(C.byref(info)), "get_abi_info")
        require(info.unsupported_capabilities == 0, "missing C3-L4 capability")
        sizes = initialized(C3L4Info)
        self.check(self.get_c3l4_abi_info(C.byref(sizes)), "get_c3l4_abi_info")
        for name, cls in (("string_array", StringArray), ("sensitivity_vertex2", SensitivityVertex),
                          ("sensitivity_channel2", SensitivityChannel), ("sensitivity2_input", SensitivityInput)):
            require(getattr(sizes, name + "_size") == C.sizeof(cls), "C3-L4 size mismatch: " + name)

    def base_query(self, contacts, model, query):
        """Return a live typed L3 result token, not an already destroyed token."""
        loads = (BodyLoad * len(model.bodies))(*(BodyLoad((U64 * 3)(*(bits(v) for v in body.dead)),
            (U64 * 3)(*(bits(v) for v in body.live))) for body in model.bodies))
        if query["kind"] == "limit":
            request = initialized(LimitInput)
            request.mu_bits = bits(Q(query.get("mu", model.mu)))
            function = self.solve_limit2
        else:
            request = initialized(CriticalInput)
            request.mu_max_bits = int(query.get("mu_max_bits", "3ff0000000000000"), 16)
            request.max_steps = query.get("max_steps", 64)
            request.parameter = 1
            function = self.critical_parameter
        request.body_count, request.body_stride, request.loads = len(loads), C.sizeof(BodyLoad), loads
        output = initialized(ExactResult)
        self.check(function(self.context, contacts, C.byref(request), C.byref(output)), "retained L3 query")
        try:
            self.check(output.call_status, "retained L3 result")
            require(output.data and output.byte_count, "empty retained L3 result")
            value = read_json(C.string_at(output.data, output.byte_count))
            return output.result, value
        except Exception:
            self.check(self.result_destroy(self.context, output.result), "result_destroy")
            raise

    def sensitivity(self, base, queries):
        request, keep = pack_request(queries)
        output = initialized(ExactResult)
        self.check(self.evaluate_sensitivity2(self.context, base, C.byref(request), C.byref(output)),
                   "evaluate_sensitivity2")
        try:
            self.check(output.call_status, "sensitivity result")
            require(output.data and output.byte_count, "empty sensitivity output")
            return read_json(C.string_at(output.data, output.byte_count))
        finally:
            self.check(self.result_destroy(self.context, output.result), "result_destroy")
