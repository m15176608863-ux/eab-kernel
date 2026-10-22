"""Brute-force: original C++ DLL vs mutant DLL on wide-bracket critical queries.
A differing (exact_threshold, attained) is checked against the G1 closed form."""
import sys, struct, json, itertools
from fractions import Fraction as Q
from pathlib import Path
ROOT = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT / "tools"))
import eab2_c3l3_diff as D
from eab.adapters.tia2d import g1, g1_threshold

orig, mut = D.C3L3Dll(sys.argv[2]), D.C3L3Dll(sys.argv[3])


def hexbits(x):
    return "%016x" % struct.unpack(">Q", struct.pack(">d", float(x)))[0]


def q(dll, m, **kw):
    ah = dll.assembly(m); ch = dll.contacts(ah)
    try:
        return dll.l3_query(ch, m, dict(kind="critical", **kw))
    finally:
        dll.check(dll.contact_set2_destroy(dll.context, ch), "d"); dll.check(dll.assembly2_destroy(dll.context, ah), "d")


n = diff = wrong = 0
rows = []
ts = [(Q(0), Q(1)), (Q(1, 8), Q(1)), (Q(3, 16), Q(1)), (Q(1, 4), Q(1)), (Q(1, 4), Q(1, 2)), (Q(1, 3), Q(3, 8)),
      (Q(1, 3), Q(3, 16)), (Q(3, 32), Q(1, 16)), (Q(1, 2), Q(1)), (Q(3, 8), Q(1, 4)), (Q(5, 16), Q(1, 2))]
mus = [0.125, 0.25, 0.375, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0]
for orient in ("koureas", "unreversed", "reverse_i1"):
    for t, h in ts:
        try:
            m = g1(t=t, height=h, orientation=orient)
        except ValueError:
            continue
        truth, att = g1_threshold(t=t, height=h, orientation=orient)
        for mm in mus:
            for steps in range(0, 7):
                a = q(orig, m, mu_max_bits=hexbits(mm), max_steps=steps)
                b = q(mut, m, mu_max_bits=hexbits(mm), max_steps=steps)
                n += 1
                ka = (a.get("exact_threshold"), a.get("attained"), a.get("reason"), a.get("mathematical_status"))
                kb = (b.get("exact_threshold"), b.get("attained"), b.get("reason"), b.get("mathematical_status"))
                if ka != kb:
                    diff += 1
                    false_claim = False
                    if b.get("exact_threshold") is not None:
                        tb = D.rational(b["exact_threshold"])
                        in_dom = truth <= Q(mm)
                        false_claim = (not in_dom) or tb != truth or b["attained"] != att
                    wrong += false_claim
                    rows.append(dict(case=f"{orient}/{t}/{h}", mu_max=mm, steps=steps, orig=ka, mut=kb,
                                     truth=(str(truth), att), false_claim=false_claim))
for r in rows[:30]:
    print(json.dumps(r))
print(f"MCOMPARE queries={n} differ={diff} false_claims={wrong}")
orig.close(); mut.close()
