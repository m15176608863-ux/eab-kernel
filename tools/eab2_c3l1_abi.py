"""ctypes transport only for C3-L1; never used by the Python expected side."""
from __future__ import annotations
import ctypes as C
import hashlib
import struct
from pathlib import Path
from eab2_c3l1_diff import read_json, require

U32, U64 = C.c_uint32, C.c_uint64
HEADER = [("struct_size", U32), ("abi_version", U32)]


class Handle(C.Structure):
    _fields_ = [("owner", U64), ("id", U64), ("generation", U64), ("type", U32), ("reserved", U32)]


class Options(C.Structure):
    _fields_ = HEADER + [("flags", U32), ("reserved", U32)]


class Text(C.Structure):
    _fields_ = [("data", C.c_char_p), ("length", U64)]


class AbiInfo(C.Structure):
    _fields_ = HEADER + [("requested_capabilities", U64), ("supported_capabilities", U64),
                        ("unsupported_capabilities", U64)] + [(name, U32) for name in
                        ("context_size", "context_options_size", "error_info_size", "binary64_bits", "pointer_bits", "reserved")] + [("build_identity", C.c_char * 192)]


class Point(C.Structure):
    _fields_ = [("x_bits", U64), ("y_bits", U64)]


class BodyInput(C.Structure):
    _fields_ = HEADER + [("vertex_count", U64), ("vertex_stride", U64), ("vertices", C.POINTER(Point)), ("flags", U32), ("reserved", U32)]


class AssemblyBody(C.Structure):
    _fields_ = HEADER + [("body", Handle), ("body_id", Text), ("reference_point", Point), ("dof_anchor", Point), ("boundary_type", U32), ("dof_mask", U32)]


class Pair(C.Structure):
    _fields_ = [("a", U64), ("b", U64)]


class AssemblyInput(C.Structure):
    _fields_ = HEADER + [("flags", U32), ("profile", U32), ("body_count", U64), ("body_stride", U64), ("bodies", C.POINTER(AssemblyBody)), ("pair_count", U64), ("pair_stride", U64), ("pairs", C.POINTER(Pair))]


class LockInput(C.Structure):
    _fields_ = HEADER + [("moving_index", U64), ("neighbor_count", U64), ("neighbor_stride", U64), ("neighbors", C.POINTER(U64))]


class ExactResult(C.Structure):
    _fields_ = HEADER + [("call_status", U32), ("mathematical_status", U32), ("result", Handle), ("data", C.c_void_p), ("byte_count", U64)]


class C3Info(C.Structure):
    _fields_ = HEADER + [(name, U32) for name in ("assembly_body2_size", "assembly2_input_size", "pair2_size", "lock2_input_size", "string_size", "reserved")]


class OptInput(C.Structure):
    _fields_ = HEADER + [("sense", U32), ("reserved", U32), ("rows", U64), ("columns", U64), ("max_pivots", U64), ("value_count", U64), ("value_stride", U64), ("values", C.POINTER(Text))]


def initialized(cls):
    result = cls()
    result.struct_size, result.abi_version = C.sizeof(cls), 1
    return result


def point(values):
    return Point(*(struct.unpack(">Q", struct.pack(">d", float(v)))[0] for v in values))


def mathematical_status(value):
    if value is None:
        return 0
    special = {"OVERLAP": 4, "UNPROVED": 2, "MECHANICAL_UNRESOLVED": 7,
               "INFEASIBLE": 5, "UNBOUNDED": 6}
    value = value.upper()
    if value in special:
        return special[value]
    require(value in {"RESOLVED", "REMOVABLE_TRANSLATION", "NOT_CONTACT",
                      "NOT_SEPARABLE_TRANSLATION", "ZERO_CONE", "NONZERO_CONE", "OPTIMAL"},
            "unknown mathematical status: " + value)
    return 1


class Dll:
    def __init__(self, path):
        path = Path(path)
        require(path.is_absolute() and path.is_file(), "--dll requires existing absolute path")
        self.path = path.resolve()
        self.sha256 = hashlib.sha256(self.path.read_bytes()).hexdigest()
        self.lib = C.CDLL(str(self.path))
        signatures = {
            "get_abi_info": [C.POINTER(AbiInfo)], "get_c3l1_abi_info": [C.POINTER(C3Info)],
            "context_create": [C.POINTER(Options), C.POINTER(Handle)], "context_destroy": [Handle],
            "body2_create": [Handle, C.POINTER(BodyInput), C.POINTER(Handle)], "body2_destroy": [Handle, Handle],
            "assembly2_create": [Handle, C.POINTER(AssemblyInput), C.POINTER(Handle)], "assembly2_destroy": [Handle, Handle],
            "assemble_contact_set2": [Handle, Handle, C.POINTER(Handle)], "contact_set2_destroy": [Handle, Handle],
            "contact_set2_export_exact": [Handle, Handle, C.POINTER(ExactResult)],
            "first_order_mobility": [Handle, Handle, C.POINTER(ExactResult)],
            "query_lock": [Handle, Handle, C.POINTER(LockInput), C.POINTER(ExactResult)],
            "result_destroy": [Handle, Handle]}
        if hasattr(self.lib, "eab2_opt_solve_exact"):
            signatures["opt_solve_exact"] = [Handle, C.POINTER(OptInput), C.POINTER(ExactResult)]
        for name, args in signatures.items():
            function = getattr(self.lib, "eab2_" + name)
            function.argtypes, function.restype = args, U32
            setattr(self, name, function)
        info = initialized(AbiInfo)
        info.requested_capabilities = 1 | 4 | 512 | 1024 | 2048 | 4096
        self.check(self.get_abi_info(C.byref(info)), "get_abi_info")
        require(info.unsupported_capabilities == 0 and info.supported_capabilities & info.requested_capabilities == info.requested_capabilities, "C3-L1 capabilities missing")
        self.identity = bytes(info.build_identity).decode("ascii")
        info3 = initialized(C3Info)
        self.check(self.get_c3l1_abi_info(C.byref(info3)), "get_c3l1_abi_info")
        for name, cls in (("assembly_body2", AssemblyBody), ("assembly2_input", AssemblyInput), ("pair2", Pair), ("lock2_input", LockInput), ("string", Text)):
            require(getattr(info3, name + "_size") == C.sizeof(cls), "C3-L1 size mismatch: " + name)
        self.context = Handle()
        options = initialized(Options)
        self.check(self.context_create(C.byref(options), C.byref(self.context)), "context_create")

    @staticmethod
    def check(status, name):
        require(status == 0, f"{name}: call_status={status}")

    def close(self):
        self.check(self.context_destroy(self.context), "context_destroy")

    def body(self, ring):
        array = (Point * len(ring))(*(point(p) for p in ring))
        request = initialized(BodyInput)
        request.vertex_count, request.vertex_stride, request.vertices = len(ring), C.sizeof(Point), array
        handle = Handle()
        self.check(self.body2_create(self.context, C.byref(request), C.byref(handle)), "body2_create")
        return handle

    def assembly(self, value):
        handles, ids, entries = [], [], []
        try:
            for b in value.bodies:
                body = self.body(b.original_vertices or b.vertices)
                handles.append(body)
                entry = initialized(AssemblyBody)
                name = b.body_id.encode("utf-8")
                ids.append(name)
                entry.body, entry.body_id = body, Text(name, len(name))
                entry.reference_point, entry.dof_anchor = point(b.reference_point), point(b.dof_anchor)
                entry.boundary_type = {None: 0, "FIXED_BODY": 1, "FORCE_CONTROLLED_PLATE": 2}[b.boundary_type]
                entry.dof_mask = sum(int(v) << k for k, v in enumerate(b.dof_mask))
                entries.append(entry)
            request = initialized(AssemblyInput)
            array = (AssemblyBody * len(entries))(*entries)
            request.flags = int(value.completeness == "complete") | (2 if value.pairs is not None else 0)
            request.profile = 1
            request.body_count, request.body_stride, request.bodies = len(entries), C.sizeof(AssemblyBody), array
            pairs = (Pair * len(value.pairs or ()))(*(Pair(*p) for p in value.pairs or ()))
            request.pair_count, request.pair_stride, request.pairs = len(pairs), C.sizeof(Pair), pairs
            result = Handle()
            self.check(self.assembly2_create(self.context, C.byref(request), C.byref(result)), "assembly2_create")
            return result
        finally:
            for handle in handles:
                self.check(self.body2_destroy(self.context, handle), "body2_destroy")

    def contacts(self, assembly):
        result = Handle()
        self.check(self.assemble_contact_set2(self.context, assembly, C.byref(result)), "assemble_contact_set2")
        return result

    def exact(self, function, *args):
        result = initialized(ExactResult)
        self.check(function(self.context, *args, C.byref(result)), function.__name__)
        try:
            self.check(result.call_status, "exact result")
            require(bool(result.data) and result.byte_count > 0, "empty exact result")
            payload = read_json(C.string_at(result.data, result.byte_count))
            state = payload.get("mathematical_status", payload.get("status"))
            require(result.mathematical_status == mathematical_status(state),
                    "ABI/JSON mathematical_status mismatch")
            return payload
        finally:
            self.check(self.result_destroy(self.context, result.result), "result_destroy")

    def query(self, assembly, contacts, source, query):
        if query["kind"] == "assembly":
            return self.exact(self.contact_set2_export_exact, contacts)
        if query["kind"] == "first_order":
            return self.exact(self.first_order_mobility, contacts)
        ids = [b.body_id for b in source.bodies]
        request = initialized(LockInput)
        request.moving_index = ids.index(query["moving_body"])
        array = (U64 * len(query["fixed_neighbors"]))(*(ids.index(b) for b in query["fixed_neighbors"]))
        request.neighbor_count, request.neighbor_stride, request.neighbors = len(array), C.sizeof(U64), array
        return self.exact(self.query_lock, assembly, C.byref(request))

    def opt(self, problem):
        request = initialized(OptInput)
        request.sense = int(problem.get("maximize", False))
        request.rows, request.columns, request.max_pivots = len(problem["b"]), len(problem["c"]), 100000
        raw = [v for row in problem["A"] for v in row] + problem["b"] + problem["c"]
        keep = [v.encode("ascii") for v in raw]
        array = (Text * len(keep))(*(Text(v, len(v)) for v in keep))
        request.value_count, request.value_stride, request.values = len(array), C.sizeof(Text), array
        return self.exact(self.opt_solve_exact, C.byref(request))
