"""Hand-built wedge whose critical friction solves mu^2 + 2 mu - 1 = 0 (mu* = sqrt2 - 1)."""
import sys, struct, json
from fractions import Fraction as Q
from pathlib import Path
ROOT = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT / "tools")); sys.path.insert(0, str(Path(__file__).parent))
import eab2_c3l3_diff as D
from eab.kernel2d.assembly import Body2, Assembly2
from eab.kernel2d.contacts import assemble_contact_set2
from eab.kernel2d.statics import critical_parameter
import irr_lib as L


def wedge(mask, slope=1):
    floor = Body2.from_vertices("floor", ((-4, -1), (8, -1), (8, 0), (-4, 0)), boundary_type="FIXED_BODY", dof_mask=(0, 0, 0))
    # ceiling edge on y = 2 - slope*x ; block top edge from (1, 2-slope) to (0, 2)
    ceil = Body2.from_vertices("ceiling", ((Q(3, 2), 2 - slope * Q(3, 2)), (Q(3, 2), 4), (-1, 4), (-1, 2 + slope)),
                               boundary_type="FIXED_BODY", dof_mask=(0, 0, 0))
    ref = (Q(1, 2), Q(1, 2))
    kw = dict(reference_point=ref, live=(-1, 0, 0))
    if mask != (1, 1, 1):
        kw.update(boundary_type="FORCE_CONTROLLED_PLATE", dof_mask=mask, dof_anchor=ref)
    block = Body2.from_vertices("block", ((0, 0), (1, 0), (1, 2 - slope), (0, 2)), **kw)
    return Assembly2((floor, ceil, block), ((0, 1), (0, 2), (1, 2)), "complete", "profile1", Q(0))


dll = D.C3L3Dll(sys.argv[2])
for mask in ((1, 1, 0), (1, 1, 1)):
    m = wedge(mask)
    cs = assemble_contact_set2(m)
    print("mask", mask, "contacts", cs.status, len(cs.constraints))
    if cs.status != "RESOLVED":
        continue
    for steps in (48, 64, 3):
        py = critical_parameter(m, "mu", mu_max=1.0, max_steps=steps, contact_set=cs)
        ah = dll.assembly(m); ch = dll.contacts(ah)
        r = dll.l3_query(ch, m, dict(kind="critical", max_steps=steps))
        dll.check(dll.contact_set2_destroy(dll.context, ch), "d"); dll.check(dll.assembly2_destroy(dll.context, ah), "d")
        cw = D.exact_wire(cs)
        D.verify_critical(m, cw, r)
        lo, hi = D.endpoint(r, "mu_lo"), D.endpoint(r, "mu_hi")
        same = (py.mathematical_status == r["mathematical_status"] and (py.mu_lo is None or Q(py.mu_lo) == lo)
                and (py.mu_hi is None or Q(py.mu_hi) == hi) and py.attained == r["attained"]
                and (py.exact_threshold is None) == (r["exact_threshold"] is None) and py.reason == r["reason"]
                and py.queries == r["queries"])
        info = dict(steps=steps, status=r["mathematical_status"], lo=float(lo) if lo is not None else None,
                    hi=float(hi) if hi is not None else None, t=r["exact_threshold"], att=r["attained"], reason=r["reason"],
                    lc=(r["lower_certificate"] or {}).get("mathematical_status"), py_same=same)
        if lo is not None and hi is not None and r["exact_threshold"] is None:
            facs = []
            for b in r["critical_polynomials"]:
                for p in [b["determinant"]] + b["numerators"]:
                    p = [D.rational(x) for x in p]
                    if any(p):
                        rr = L.roots_in(p, lo, hi)
                        if rr and rr[1]:
                            sq = rr[0]
                            # strip linear rational factors anywhere: test quadratic mu^2+2mu-1 divides
                            qd = L.pdiv(sq, [Q(-1), Q(2), Q(1)])
                            facs.append((b["kind"], len(sq) - 1, not any(qd[1]), L.rational_root(sq, *rr[1][0])))
            info["root_factors(kind,sqdeg,divisible_by_mu2+2mu-1,rational_root)"] = facs
            info["contains_sqrt2_minus_1"] = lo < Q(0.41421356237309503) or True
        print(json.dumps(info, default=str), flush=True)
dll.close()
