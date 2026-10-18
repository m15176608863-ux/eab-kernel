"""Schema-aware tool transport of the frozen bdda3d document.

Integer identities/states stay exact even when a JSON decimal denotes an
integer. Known continuous fields use the checked binary64 reader boundary;
unknown metadata retains its existing numeric-tree model, not invented units.
"""
from eab.numeric_decode import decode_tree, integer, loads as loads_exact, scalar


_INTEGER = {"bi", "bj", "nsign", "m0init", "m0_0"}
_REAL = {"t1", "t2", "d1", "area", "fa", "coh", "tens", "o3t"}


def loads(text):
    raw = loads_exact(text)
    out = decode_tree({k:v for k,v in raw.items() if k not in {"step", "verts", "entrances"}}, "bdda3d document metadata")
    out["step"] = integer(raw.get("step", 0), "bdda3d document step")
    out["verts"] = {str(integer(block, "bdda3d document block")):
                    [[scalar(x, quantity="bdda3d document coordinate") for x in point] for point in points]
                    for block, points in raw.get("verts", {}).items()}
    out["entrances"] = []
    for row in raw.get("entrances", []):
        continuous = {k:v for k,v in row.items() if k not in _INTEGER | {"refs", "owner"}}
        entry = decode_tree(continuous, "bdda3d entrance")
        for name in _INTEGER & row.keys():
            if row[name] is not None:
                entry[name] = integer(row[name], "bdda3d entrance " + name)
            else:
                entry[name] = None
        for name in _REAL & row.keys():
            if row[name] is not None:
                entry[name] = scalar(row[name], quantity="bdda3d entrance " + name)
        if "refs" in row:
            entry["refs"] = [[integer(v, "bdda3d reference identity") for v in pair] for pair in row["refs"]]
        if "owner" in row:
            entry["owner"] = [integer(v, "bdda3d owner flag") for v in row["owner"]]
        if row.get("slip_ref") is not None:
            entry["slip_ref"] = [scalar(v, quantity="bdda3d slip_ref") for v in row["slip_ref"]]
        out["entrances"].append(entry)
    return out
