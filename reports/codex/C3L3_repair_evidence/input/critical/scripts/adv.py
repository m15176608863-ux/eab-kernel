"""Non-author strict critical comparator + adversarial cases (C3-L3 lens: critical/ABI).

Usage: python -X utf8 adv.py <src_root> <dll> <mode> <out.json>
mode: corpus | adversarial | all
"""
import json, math, struct, sys, time, traceback
from fractions import Fraction as Q
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))
import eab2_c3l3_diff as D  # noqa: E402
from eab.kernel2d.contacts import assemble_contact_set2  # noqa: E402
from eab.kernel2d.assembly import Body2, Assembly2  # noqa: E402
from eab.adapters.tia2d import g1, g1_morphology, g5  # noqa: E402

DLL = sys.argv[2]
MODE = sys.argv[3]
OUT = Path(sys.argv[4])


def hexbits(x):
    return "%016x" % struct.unpack(">Q", struct.pack(">d", float(x)))[0]


def fnext(x, d):
    return math.nextafter(float(x), d)


def adjacent(lo, hi):
    return lo < hi and Q(math.nextafter(float(lo), math.inf)) == hi


def rq(v):
    return None if v is None else D.rational(v)


def status(c):
    return None if c is None else c.get("mathematical_status")


def strict_view(r):
    """Every field I consider semantically unique, incl. ones the author's tool drops."""
    if r.get("abi_call_status") is not None:
        return dict(abi=r)
    lo, hi = D.endpoint(r, "mu_lo"), D.endpoint(r, "mu_hi")
    proof = r.get("threshold_proof")
    pv = None
    if proof is not None:
        pv = dict(t=rq(proof["exact_threshold"]), attained=proof["attained"],
                  li=tuple(map(D.rational, proof["lower_interval"])), ui=tuple(map(D.rational, proof["upper_interval"])),
                  reason=proof["reason"], ls=proof["lower_signs"] is None, us=proof["upper_signs"] is None,
                  lb=None if proof["lower_basis"] is None else proof["lower_basis"]["kind"],
                  ub=None if proof["upper_basis"] is None else proof["upper_basis"]["kind"])
    return dict(call=r["call_status"], math=r["mathematical_status"], lo=lo, hi=hi, attained=r.get("attained"),
                reason=r.get("reason"), t=rq(r.get("exact_threshold")), bt=r.get("bisection_termination"),
                tpr=r.get("threshold_proof_reason"), queries=r.get("queries"),
                vc=sorted(r.get("validity_conditions") or []),
                lc=status(r.get("lower_certificate")), uc=status(r.get("upper_certificate")),
                tc=status(r.get("threshold_certificate")),
                lcv=rq((r.get("lower_certificate") or {}).get("exact_value")),
                polys=sorted(b["kind"] for b in r.get("critical_polynomials") or []), proof=pv)


def role_checks(r, mu_max, max_steps, cpp=True):
    """Independent semantic checks of the critical contract (design 4.6.4)."""
    errs = []
    if r.get("abi_call_status") is not None:
        return errs
    lo, hi = D.endpoint(r, "mu_lo"), D.endpoint(r, "mu_hi")
    for name in ("mu_lo", "mu_hi"):
        b = r.get(name + "_bits")
        if cpp and (r.get(name) is None) != (b is None):
            errs.append(name + " bits/presence disagree")
    att, t = r.get("attained"), rq(r.get("exact_threshold"))
    reason, bt, tpr = r.get("reason"), r.get("bisection_termination"), r.get("threshold_proof_reason")
    lc, uc, tc = status(r.get("lower_certificate")), status(r.get("upper_certificate")), status(r.get("threshold_certificate"))
    if r["mathematical_status"] in ("UNPROVED",):
        if lo is not None and reason != "query_certificate_unavailable":
            errs.append("UNPROVED carries endpoints")
        return errs
    if reason == "bounded_on_domain":
        if not (hi is None and lo == mu_max and lc == "OPTIMAL" and att is None and t is None and uc is None):
            errs.append("bounded_on_domain shape")
        return errs
    if reason == "infeasible_on_domain":
        if not (hi is None and lo == mu_max and lc == "INFEASIBLE" and att is None and r["mathematical_status"] == "INFEASIBLE"):
            errs.append("infeasible_on_domain shape")
        return errs
    if lo == hi == 0 and att is True and r.get("lower_certificate") is None:
        if not (uc == "UNBOUNDED" and tc == "UNBOUNDED" and t == 0 and bt is None and tpr is None):
            errs.append("zero-unbounded shape")
        return errs
    # bracket
    if lo is None or hi is None or not (0 <= lo < hi <= mu_max):
        errs.append("bracket order/domain")
        return errs
    if lc not in ("OPTIMAL", "INFEASIBLE"):
        errs.append("lower certificate role %s" % lc)
    if uc != "UNBOUNDED":
        errs.append("upper certificate role %s" % uc)
    ray = (r.get("upper_certificate") or {}).get("improving_ray")
    if ray is None or D.rational(ray[-1]) != 1:
        errs.append("upper ray alpha != 1 (alpha is last column)")
    if bt not in ("iteration_limit", "input_resolution_limit") or reason != bt:
        errs.append("bisection_termination/reason")
    if bt == "input_resolution_limit" and not adjacent(lo, hi):
        errs.append("input_resolution_limit but endpoints not adjacent binary64")
    if bt == "iteration_limit" and adjacent(lo, hi):
        errs.append("iteration_limit but endpoints adjacent")
    if t is None:
        if att is not None or tpr is not None or tc is not None:
            errs.append("null threshold must keep null attained/proof")
    else:
        if tpr != "exact_basis_continuation":
            errs.append("proof reason missing")
        if not (lo <= t <= hi):
            errs.append("threshold outside bracket")
        if att is True and tc != "UNBOUNDED":
            errs.append("closed threshold not unbounded at t")
        if att is False and tc != "OPTIMAL":
            errs.append("open threshold not bounded at t")
        if att is False and t == hi:
            errs.append("open threshold equals hi")
    return errs


class Runner:
    def __init__(self):
        self.dll = D.C3L3Dll(DLL)
        self.rows = []
        self.fail = 0

    def run(self, name, model, query, expected=None, contacts_wire=None, extra=None):
        t0 = time.perf_counter()
        ah = ch = None
        row = dict(case=name, query={k: v for k, v in query.items() if k != "result"})
        try:
            if contacts_wire is None:
                contacts_wire = D.exact_wire(assemble_contact_set2(model))
            if expected is None:
                expected = D.exact_wire(D.python_result(model, query, assemble_contact_set2(model)))
            ah = self.dll.assembly(model)
            ch = self.dll.contacts(ah)
            actual = self.dll.l3_query(ch, model, query)
            mu_max = Q(D.double_bits(query.get("mu_max_bits", "3ff0000000000000")))
            if expected.get("call_status") != "OK":
                row["expected_call"] = expected.get("call_status")
                row["actual"] = actual
                ok = expected["call_status"] == "UNSUPPORTED" and actual.get("abi_call_status") == 3
                row["errors"] = [] if ok else ["call error mapping"]
            else:
                # author checker (certificate maths) on both sides
                D.verify_critical(model, contacts_wire, expected)
                D.verify_critical(model, contacts_wire, actual)
                sv_e, sv_a = strict_view(expected), strict_view(actual)
                diffs = {k: (str(sv_e[k]), str(sv_a[k])) for k in sv_e if sv_e[k] != sv_a.get(k)}
                errs = role_checks(actual, mu_max, query.get("max_steps", 64))
                errs += ["python:" + e for e in role_checks(expected, mu_max, query.get("max_steps", 64), cpp=False)]
                if extra:
                    errs += extra(actual)
                row.update(diffs=diffs, errors=errs,
                           actual=dict(math=sv_a["math"], lo=str(sv_a["lo"]), hi=str(sv_a["hi"]), attained=sv_a["attained"],
                                       t=str(sv_a["t"]), reason=sv_a["reason"], bt=sv_a["bt"], tpr=sv_a["tpr"],
                                       queries=sv_a["queries"], lc=sv_a["lc"], uc=sv_a["uc"], polys=sv_a["polys"]))
        except Exception as e:
            row["errors"] = ["EXC " + type(e).__name__ + ": " + str(e)]
            row["trace"] = traceback.format_exc()[-1500:]
        finally:
            if ch is not None:
                self.dll.check(self.dll.contact_set2_destroy(self.dll.context, ch), "cs destroy")
            if ah is not None:
                self.dll.check(self.dll.assembly2_destroy(self.dll.context, ah), "as destroy")
        row["seconds"] = round(time.perf_counter() - t0, 3)
        bad = bool(row.get("errors")) or bool(row.get("diffs"))
        self.fail += bad
        row["bad"] = bad
        self.rows.append(row)
        print(json.dumps(dict(case=name, bad=bad, diffs=row.get("diffs"), errors=row.get("errors"),
                              a=row.get("actual"), s=row["seconds"]), default=str), flush=True)


def corpus(R):
    for name, family, model, contacts, sel in D.formal_cases():
        for i, q, r in sel:
            if q["kind"] == "critical":
                R.run("formal/" + name, model, q, expected=r, contacts_wire=contacts)
    for name, family, model, contacts, queries in D.t1b_cases():
        for i, q, _ in queries:
            if q["kind"] == "critical":
                R.run(name, model, q, contacts_wire=contacts)
    for name, family, model, contacts, queries in D.regression_cases():
        for i, q, _ in queries:
            if q["kind"] == "critical":
                R.run(name, model, q, contacts_wire=contacts)
    for name, family, model, contacts, queries in D.metamorphic_cases():
        for i, q, _ in queries:
            if q["kind"] == "critical":
                R.run(name, model, q, contacts_wire=contacts)


def incline(slope_num, slope_den, live=(1, -4, 0), dead=(0, -1, 0)):
    """Fixed wedge y = (n/d) x on [0, 4d]; a vertical-sided parallelogram rests on it."""
    s = Q(slope_num, slope_den)
    x0, x1 = Q(3, 4) * slope_den, Q(9, 4) * slope_den
    wedge = Body2.from_vertices("wedge", ((0, 0), (4 * slope_den, 0), (4 * slope_den, 4 * slope_num)),
                                boundary_type="FIXED_BODY", dof_mask=(0, 0, 0))
    p0, p1 = (x0, s * x0), (x1, s * x1)
    verts = (p0, p1, (x1, s * x1 + 1), (x0, s * x0 + 1))
    c = ((x0 + x1) / 2, (s * x0 + s * x1) / 2 + Q(1, 2))
    block = Body2.from_vertices("block", verts, reference_point=c, dead=dead, live=live)
    return Assembly2((wedge, block), ((0, 1),), "complete", "profile1", Q(0))


def adversarial(R):
    crit = lambda **kw: dict(kind="critical", **kw)
    third = Q(1, 3)
    # (a) non-dyadic thresholds with dyadic vertices: need > 53 bits -> adjacent endpoints
    for orient, att in (("unreversed", False), ("reverse_i1", True)):
        m = g1(t=third, height=Q(3, 8), orientation=orient)
        for steps in (64, 200):
            R.run(f"adv/g1_{orient}_1/3_steps{steps}", m, crit(max_steps=steps),
                  extra=lambda a, att=att: [] if (D.rational(a["exact_threshold"]) == third and a["attained"] is att
                                                    and a["bisection_termination"] == "input_resolution_limit") else ["expected 1/3 %s with resolution limit" % att])
    m = g1(t=third, height=Q(3, 16), orientation="koureas")
    R.run("adv/g1_koureas_11/48", m, crit(max_steps=80),
          extra=lambda a: [] if D.rational(a["exact_threshold"]) == Q(11, 48) and a["attained"] is True else ["expected 11/48 closed"])
    # (b) mu_max exactly at / adjacent to threshold
    for orient in ("unreversed", "reverse_i1"):
        m = g1(t=Q(1, 4), height=Q(1), orientation=orient)
        for label, mm in (("at", 0.25), ("below", fnext(0.25, 0)), ("above", fnext(0.25, 1)), ("zero", 0.0),
                          ("subnormal", 5e-324), ("max", sys.float_info.max)):
            R.run(f"adv/g1_{orient}_1/4_mumax_{label}", m, crit(mu_max_bits=hexbits(mm), max_steps=64))
    # non-dyadic threshold, mu_max = binary64 just above/below 1/3
    m = g1(t=third, height=Q(3, 8), orientation="reverse_i1")
    for label, mm in (("below", float(third) if Q(float(third)) < third else fnext(float(third), 0)),
                      ("above", float(third) if Q(float(third)) > third else fnext(float(third), 1))):
        R.run(f"adv/g1_reverse_1/3_mumax_{label}", m, crit(mu_max_bits=hexbits(mm), max_steps=64))
    # (c) mu_max = 0 and max_steps = 0
    for orient, t in (("koureas", Q(1, 4)), ("koureas", Q(0)), ("unreversed", Q(0)), ("reverse_i1", Q(1, 4))):
        m = g1(t=t, height=Q(1), orientation=orient)
        R.run(f"adv/g1_{orient}_{t}_mumax0", m, crit(mu_max_bits=hexbits(0.0), max_steps=64))
        R.run(f"adv/g1_{orient}_{t}_mumax_negzero", m, crit(mu_max_bits="8000000000000000", max_steps=64))
        R.run(f"adv/g1_{orient}_{t}_steps0", m, crit(max_steps=0))
        R.run(f"adv/g1_{orient}_{t}_steps1", m, crit(max_steps=1))
    # (d) Farkas lower end (dead load cannot be carried at small mu); slope 1/4 and 1/3
    for n, d in ((1, 4), (1, 3)):
        m = incline(n, d)
        R.run(f"adv/incline_{n}/{d}_limit_mu0", m, dict(kind="critical", max_steps=64))
        R.run(f"adv/incline_{n}/{d}_steps0", m, dict(kind="critical", max_steps=0))
        R.run(f"adv/incline_{n}/{d}_mumax_at", m, dict(kind="critical", max_steps=64, mu_max_bits=hexbits(float(Q(n, d)))))
    # dead load zero: open/closed proof from mechanism lower basis
    m = incline(1, 3, dead=(0, 0, 0), live=(0, -1, 0))
    R.run("adv/incline_1/3_nodead_gravitylive", m, dict(kind="critical", max_steps=64))
    # (e) irrational-type morphologies: new parameter points not in the T1b scan
    for kw in (dict(tilt=Q(5, 64), amplitude=Q(1, 512), phase=Q(1, 4)),
               dict(tilt=Q(3, 32), amplitude=Q(3, 4096), phase=Q(1, 2)),
               dict(family="kinked", tilt=Q(7, 64), amplitude=Q(1, 512)),
               dict(tilt=Q(11, 128), asymmetry=Q(1, 8))):
        m = g1_morphology(**kw).assembly
        R.run("adv/morph_" + "_".join(f"{k}={v}" for k, v in kw.items()), m, crit(max_steps=64))
    # T1b required indices at higher refinement: resolution limit + proof coexisting
    from tia2d_t1b_morphology import scan_parameters
    params = scan_parameters()
    for i in (13, 16, 30, 8, 17, 1, 2, 5, 10, 11, 14, 19, 22):
        m = g1_morphology(**params[i]).assembly
        R.run(f"adv/t1b{i:02d}_steps100", m, crit(max_steps=100))


def sweep(R):
    crit = lambda **kw: dict(kind="critical", **kw)
    combos = []
    for orient in ("koureas", "unreversed", "reverse_i1"):
        for t, h in ((Q(0), Q(1)), (Q(1, 8), Q(1)), (Q(3, 16), Q(1)), (Q(1, 4), Q(1, 2)), (Q(1, 3), Q(3, 8)), (Q(1, 3), Q(3, 16)), (Q(3, 32), Q(1, 16))):
            combos.append((f"g1/{orient}/{t}/{h}", g1(t=t, height=h, orientation=orient)))
    for n in (3, 5):
        for mu in (Q(0),):
            combos.append((f"g5/{n}", g5(n=n, height=1, pressure=1, width=1, mu=mu)))
    from tia2d_t1b_morphology import scan_parameters
    params = scan_parameters()
    for i in (0, 3, 13, 8, 17, 1, 24, 30):
        combos.append((f"t1b/{i}", g1_morphology(**params[i]).assembly))
    for name, m in combos:
        heavy = name.startswith("t1b")
        for mm in ((1.0, 0.5, 4.0) if not heavy else (1.0,)):
            for steps in ((0, 1, 2, 3, 5, 8, 13, 64) if not heavy else (0, 1, 3, 6, 10)):
                R.run(f"sweep/{name}/mumax={mm}/steps={steps}", m, crit(mu_max_bits=hexbits(mm), max_steps=steps))


def main():
    R = Runner()
    try:
        if MODE in ("corpus", "all"):
            corpus(R)
        if MODE in ("adversarial", "all"):
            adversarial(R)
        if MODE == "sweep":
            sweep(R)
    finally:
        R.dll.close()
    OUT.write_text(json.dumps(dict(rows=R.rows, fail=R.fail, total=len(R.rows)), default=str, indent=1), encoding="utf-8")
    print(f"ADV mode={MODE} total={len(R.rows)} bad={R.fail}")


if __name__ == "__main__":
    main()
