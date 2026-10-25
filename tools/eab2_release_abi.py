"""Exact PE export/header/frozen-v1/size/capability gate; stdlib only."""
from __future__ import annotations
import argparse
import ctypes as C
import hashlib
import json
from pathlib import Path
import re
import struct

ROOT = Path(__file__).resolve().parents[1]
START = "<!-- EAB2_RELEASE_ABI_V1_BEGIN -->"
END = "<!-- EAB2_RELEASE_ABI_V1_END -->"


def require(value, message):
    if not value:
        raise AssertionError(message)


class ReleaseHeader:
    """Independent header reader; no consumer, harness, or path import required."""
    def __init__(self, path):
        self.raw = Path(path).read_bytes()
        text = re.sub(r"/\*.*?\*/|//[^\n]*", "", self.raw.decode("utf-8"), flags=re.S)
        self.types = {"uint32_t": C.c_uint32, "uint64_t": C.c_uint64, "char": C.c_char}
        self.aliases = dict((alias, base) for base, alias in re.findall(r"typedef\s+(\w+)\s+(\w+)\s*;", text))
        require(self.aliases.get("eab2_call_status") == "uint32_t", "public call_status must be uint32_t")
        self.structs = canonical_c_fields(self.raw)
        for name, fields in self.structs.items():
            self.types[name] = type(name, (C.Structure,), {"_fields_": [(field, self.ctype(kind)) for field, kind in fields.items()]})
        self.constants = {}
        for line in text.splitlines():
            match = re.match(r"\s*#\s*define\s+(EAB2_\w+)\b(.*)", line)
            if not match or match[1] in {"EAB2_API", "EAB2_C_API_H"}:
                continue
            name, expression = match.groups()
            integer = re.fullmatch(r"\s*UINT(32|64)_C\(\s*(0[xX][\da-fA-F]+|\d+)\s*\)\s*", expression)
            require(integer is not None, "unsupported public integer constant: " + name)
            width, literal = integer.groups()
            value = int(literal, 16 if literal.lower().startswith("0x") else 10)
            require(name not in self.constants and value < 2**int(width), "invalid/duplicate public integer constant: " + name)
            self.constants[name] = dict(type="uint" + width + "_t", value=value)
        require("EAB2_ABI_VERSION" in self.constants, "public ABI version absent")
        self.capabilities = {name: row["value"] for name, row in self.constants.items() if name.startswith("EAB2_CAP_")}
        # Enumerate every function-looking name before recognizing the allowed
        # ABI subset, so adding a void-return or non-exported prototype is red.
        self.functions, self.return_types = {}, {}
        declared = re.findall(r"\b(eab2_\w+)\s*\(", text)
        for statement in re.split(r"[;{}]", re.sub(r"^\s*#.*$", "", text, flags=re.M)):
            if not re.search(r"\beab2_\w+\s*\(", statement):
                continue
            match = re.fullmatch(r"\s*(.*?)\b(eab2_\w+)\s*\((.*?)\)\s*", statement, re.S)
            require(match is not None, "unsupported public prototype")
            prefix, name, args = match.groups()
            require(prefix.split() == ["EAB2_API", "eab2_call_status"], "public prototype requires EAB2_API eab2_call_status: " + name)
            require(name not in self.functions, "duplicate public prototype: " + name)
            self.functions[name] = [] if args.strip() == "void" else [self.ctype(canonical_c_field(a)[1]) for a in args.split(",")]
            self.return_types[name] = "eab2_call_status"
        require(sorted(declared) == sorted(self.functions), "unparsed public prototype")

    def resolve(self, name):
        if name not in self.types:
            require(name in self.aliases, "unknown public C type: " + name)
            self.types[name] = self.resolve(self.aliases[name])
        return self.types[name]

    def ctype(self, kind):
        base = re.sub(r"\bconst\b|\s", "", kind)
        match = re.fullmatch(r"(\w+)(\**)((?:\[\d+\])*)", base)
        require(match is not None, "unsupported public C type: " + kind)
        name, pointers, arrays = match.groups()
        result = self.resolve(name)
        for _ in pointers:
            result = C.POINTER(result)
        for count in reversed(re.findall(r"\[(\d+)\]", arrays)):
            result = result * int(count)
        return result


def runtime_capabilities(dll, header):
    require(Path(dll).name.lower() == "eab2.dll", "release DLL required")
    library = C.CDLL(str(Path(dll).resolve()))
    functions = {}
    for name, args in header.functions.items():
        function = getattr(library, name)
        function.argtypes, function.restype = args, header.resolve(header.return_types[name])
        functions[name] = function
    require(functions["eab2_self_test"]() == 0, "release self-test failed")
    info = None
    version = header.constants["EAB2_ABI_VERSION"]["value"]
    for family in ("", "c1_", "c3l1_", "c3l3_", "c3l4_"):
        descriptor = header.resolve("eab2_" + family + "abi_info")()
        descriptor.struct_size, descriptor.abi_version = C.sizeof(descriptor), version
        require(functions["eab2_get_" + family + "abi_info"](C.byref(descriptor)) == 0, "runtime ABI descriptor rejected: " + family)
        for field, _ in descriptor._fields_:
            if field.endswith("_size") and field != "struct_size":
                require(getattr(descriptor, field) == C.sizeof(header.resolve("eab2_" + field[:-5])), "runtime structure size mismatch: " + field)
        if not family:
            info = descriptor
    require(info.binary64_bits == 64 and info.pointer_bits == C.sizeof(C.c_void_p)*8, "runtime scalar/pointer width mismatch")
    return info.supported_capabilities


def canonical_c_field(declaration):
    """Preserve base const, every pointer/const level, and array dimensions.

    Only the public header's fixed-width/named-type C subset is accepted.
    Parenthesized function/pointer-to-array declarators and bitfields fail
    rather than silently collapsing to a same-sized ctypes representation.
    """
    match = re.fullmatch(
        r"\s*(const\s+)?([A-Za-z_]\w*)(\s+const)?\s*"
        r"((?:\*\s*(?:const\s*)?)*)\s*([A-Za-z_]\w*)\s*"
        r"((?:\[\s*\d+\s*\]\s*)*)", declaration)
    require(match is not None, "unsupported canonical C field: " + declaration)
    before, base, after, pointers, name, arrays = match.groups()
    kind = ("const " if before or after else "") + base
    for qualifier in re.findall(r"\*\s*(const)?\s*", pointers):
        kind += "*" + (" const" if qualifier else "")
    kind += "".join("[" + str(int(n)) + "]" for n in re.findall(r"\[\s*(\d+)\s*\]", arrays))
    return name, kind


def canonical_c_fields(raw):
    text = re.sub(r"/\*.*?\*/|//[^\n]*", "", raw.decode("utf-8"), flags=re.S)
    result = {}
    for name, body, alias in re.findall(r"typedef\s+struct\s+(\w+)\s*\{(.*?)\}\s*(\w+)\s*;", text, re.S):
        require(name == alias and name not in result, "duplicate/anonymous public C structure")
        entries = [canonical_c_field(field) for field in body.split(";") if field.strip()]
        require(len({name for name, _ in entries}) == len(entries), "duplicate public C field")
        result[name] = dict(entries)
    return result


def pe_exports(raw):
    """Read every named/ordinal export, rejecting forwarders and unnamed ones."""
    require(len(raw) >= 64 and raw[:2] == b"MZ", "not a DOS/PE image")
    def u16(at):
        require(0 <= at <= len(raw)-2, "PE uint16 outside image")
        return struct.unpack_from("<H", raw, at)[0]
    def u32(at):
        require(0 <= at <= len(raw)-4, "PE uint32 outside image")
        return struct.unpack_from("<I", raw, at)[0]
    pe = u32(60)
    require(raw[pe:pe+4] == b"PE\0\0" and u16(pe+4) == 0x8664, "expected x64 PE")
    count, optional_size = u16(pe+6), u16(pe+20)
    optional = pe+24
    require(u16(optional) == 0x20b and optional_size >= 120, "expected PE32+ export directory")
    require(u32(optional+108) >= 1, "PE has no export data directory")
    export_rva, export_bytes = u32(optional+112), u32(optional+116)
    require(export_rva and export_bytes >= 40, "PE export directory absent")
    sections = []
    for i in range(count):
        at = optional+optional_size+i*40
        sections.append((u32(at+12), u32(at+8), u32(at+20), u32(at+16)))
    def offset(rva, length=1):
        for va, virtual_size, raw_at, raw_size in sections:
            delta = rva-va
            if 0 <= delta < max(virtual_size, raw_size):
                require(delta+length <= raw_size and raw_at+delta+length <= len(raw), "PE RVA outside raw section")
                return raw_at+delta
        raise AssertionError("PE RVA has no section")
    def cstring(rva):
        at = offset(rva)
        end = raw.find(b"\0", at, min(len(raw), at+4096))
        require(end >= at, "unterminated PE export name")
        offset(rva, end-at+1)
        return raw[at:end].decode("ascii")
    directory = offset(export_rva, 40)
    ordinal_base, functions, names = u32(directory+16), u32(directory+20), u32(directory+24)
    require(functions == names and names <= 65536, "ordinal-only/empty exports are not allowed")
    function_at = offset(u32(directory+28), functions*4)
    name_at, ordinal_at = offset(u32(directory+32), names*4), offset(u32(directory+36), names*2)
    rows = []
    for i in range(names):
        index = u16(ordinal_at+i*2)
        require(index < functions, "export ordinal outside function table")
        rva = u32(function_at+index*4)
        require(rva != 0, "empty function export")
        rows.append(dict(name=cstring(u32(name_at+i*4)), ordinal=ordinal_base+index,
                         forwarded=export_rva <= rva < export_rva+export_bytes))
    require(len({r["name"] for r in rows}) == names and len({r["ordinal"] for r in rows}) == names, "duplicate PE exports")
    require(not any(r["forwarded"] for r in rows), "release ABI may not forward exports")
    return rows


def header_contract(header):
    present = {name: value for name, value in header.capabilities.items()
               if not name.startswith("EAB2_CAP_TEST_") and name not in
               {"EAB2_CAP_RHO", "EAB2_CAP_SE2", "EAB2_CAP_LP2"}}
    structures, field_types = {}, canonical_c_fields(header.raw)
    require(set(field_types) == set(header.structs), "canonical C/ctypes structure inventory differs")
    for name in header.structs:
        kind = header.resolve(name)
        fields = {field: getattr(kind, field).offset for field, _ in kind._fields_}
        require(set(fields) == set(field_types[name]), "canonical C/ctypes field inventory differs")
        structures[name] = dict(size=C.sizeof(kind), abi_version=header.constants["EAB2_ABI_VERSION"]["value"] if "abi_version" in fields else None,
                                fields=fields, field_types=field_types[name])
    return dict(abi_version=header.constants["EAB2_ABI_VERSION"]["value"], platform="MSVC_x64", exports=sorted(header.functions),
                signatures={name: [kind.__name__ for kind in args] for name, args in sorted(header.functions.items())},
                return_types=dict(sorted(header.return_types.items())), constants=dict(sorted(header.constants.items())),
                capabilities={name: dict(value=value, present=name in present) for name, value in sorted(header.capabilities.items())},
                supported_capabilities=sum(present.values()), structures=structures)


def frozen_contract(path):
    text = Path(path).read_text("utf-8")
    require(text.count(START) == text.count(END) == 1, "exactly one release freeze table required")
    block = text.split(START)[1].split(END)[0]
    fence = chr(96)*3
    match = re.fullmatch(r"\s*" + fence + r"json\s*(.*?)\s*" + fence + r"\s*", block, re.S)
    require(match is not None, "release freeze table must be JSON")
    result = json.loads(match.group(1))
    require(result.get("status") == "FROZEN", "release ABI table is not frozen")
    return result


def differences(frozen, actual, exports, supported):
    errors = []
    for key in ("abi_version", "platform", "exports", "signatures", "return_types", "constants", "capabilities", "supported_capabilities", "structures"):
        if frozen.get(key) != actual.get(key):
            errors.append("header/frozen contract mismatch: " + key)
    if sorted(exports) != actual["exports"]:
        errors.append("PE exports differ from complete public declarations")
    if supported != actual["supported_capabilities"]:
        errors.append("runtime capability mask differs from frozen/header set")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dll", type=Path, required=True)
    parser.add_argument("--header", type=Path, default=ROOT / "eab2/include/eab2/c_api.h")
    parser.add_argument("--contract", type=Path, default=ROOT / "eab2/ABI_CONTRACT.md")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    header, frozen = ReleaseHeader(args.header), frozen_contract(args.contract)
    exports = pe_exports(args.dll.read_bytes())
    supported, actual = runtime_capabilities(args.dll, header), header_contract(header)
    errors = differences(frozen, actual, [row["name"] for row in exports], supported)
    result = dict(status="PASS" if not errors else "FAIL", findings=errors, export_count=len(exports), exports=exports,
                  supported_capabilities=supported, structure_count=len(actual["structures"]), constant_count=len(actual["constants"]),
                  header_and_frozen_equal=not errors, dll_sha256=hashlib.sha256(args.dll.read_bytes()).hexdigest(),
                  header_sha256=hashlib.sha256(header.raw).hexdigest(), freeze_consumer_evidence=frozen.get("consumer_evidence"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(f"EAB2_RELEASE_ABI status={result['status']} exports={len(exports)} structures={result['structure_count']} findings={len(errors)}")
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
