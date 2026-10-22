# C3-L3 验收：静力路

**C3-L3 statics lens (commit c8718bb): verdict close.** I found 0 critical, 0 major and 0 minor defects; two info-level notes are at the end. I built my own exact LP and my own profile1 assembly straight from the original geometry, without importing any eab or eab2 code, and compared the C++ DLL against them through my own ctypes binding. Every C++ certificate was checked on my own matrices.

**Build:** a clean archive of c8718bb, built with `cmd /c eab2\build_eab2.bat`, passed all 12 C++ tests. The test binaries print `C3L3_STATICS_OK checks=3916`, `C3L3_CRITICAL_OK checks=322` and `EAB2_C3L3_ABI checks=128 failed=0`.

**How the checker works**
- **LP:** two-phase exact simplex on Fractions with Bland's rule. On 3000 random problems every certificate it returned verified (509 optimal, 1583 infeasible, 908 unbounded).
- **Assembly:**
  - Contact points are taken from vertex-on-boundary incidences at t=0. Each point's free cone F_p is computed from the two material sectors with my own exact pseudo-angle code, not by sampling directions.
  - The flat-interior rule for maximal collinear segments is my own implementation.
  - Generators are g± = N ± μT with N pointing into body a, applied +g to a and −g to b, with moments taken directly about each body's anchor.
  - Plate rows are masked, and the twist-space test for true-VV redundancy is my own LP.
- **Matching C++ columns to mine:** C++'s tangent is recomputed from my geometry using its edge label, and the column must be a positive multiple of mine. The mapping must be one-to-one, and the C++ A, b and c must equal my columns times that scale exactly.
- **Certificates checked:**
  - OPTIMAL: x ≥ 0, Ax = b, Aᵀy ≥ c, bᵀy equal to the value, mechanism = y with drive ≥ 1.
  - INFEASIBLE: Aᵀf ≤ 0 and bᵀf = 1.
  - UNBOUNDED: x0 feasible, plus a ray r ≥ 0 with Ar = 0 and α component exactly 1. No value, x or y may be present.
- **Critical-parameter checks:** endpoint bits equal the canonical rationals, each endpoint certificate verifies on my matrices, and my LP is bounded at μ_lo and unbounded at μ_hi. When an exact threshold t is claimed, my LP at t must agree with `attained`, be bounded at t − 2⁻²⁰⁰ and unbounded at t + 2⁻²⁰⁰. The `input_resolution_limit` reason requires adjacent binary64 endpoints, and the zero-unbounded, bounded-on-domain and infeasible-on-domain branches are checked separately.
- **The checker catches bad output:** 41 of 41 deliberate corruptions of C++ results were rejected (value, x, y, moment entry, column sign, ray scaling, Farkas sign, attained flag, threshold, endpoint bits, missing certificates, dropped or duplicated constraints, wrong VV kind, VV multipliers, witness twist).

**Results**

| Item | Scope | Result |
|---|---|---|
| Formal corpus tia2d-2 | 114 limit + 114 critical queries, including the unsupported `h` parameter | 0 failures. The C++ problem matched the corpus problem exactly in all 110 resolvable limits. The `h` parameter returns UNSUPPORTED (3) with the output untouched. |
| T1b morphology | 36 cases × 4 μ limits + criticals at 48 and 64 steps | 0 failures: 26 closed, 2 open, 8 irrational. Required indices match: 13 → 131009/2097408 (closed), 16 → 98283/2097664 (closed), 30 → 326839/6291456 (closed), 8 → 1/16 (open), 17 → 7/128 (open). Irrational cases have a null threshold and bracket width ≤ 2⁻⁴⁰. |
| T1b thickness | 7 samples whose geometry is binary64-exact, plus 18 thick controls rebuilt with the Python generator | 0 failures; thresholds equal the archived values. The other 32 thickness samples use non-dyadic rational geometry, which the binary64-only ABI cannot accept. |
| Regression (d) | G5 flush corner, N=3, L=3, h=P=1 | μ=0 → 0 and μ=1/4 → 1/2, C++ and mine agree. |
| Plate counterexamples | μ=2, anchor at face midpoint | Releasing vertical [1,1,0] → 2/3; releasing rotation [1,0,1] → 4/3. Same with nonsymmetric reference points. |
| G5 closed form F = min(2μP, 4Ph/(L−b)) | 30 configurations × 6 values of μ | All equal, including unequal symmetric widths such as [1/2,1,3,1,1/2] and [3/4,1/4,3/4], n=1/3/5/7, and random reference points. |
| G1 closed forms | 24 formal G1 thresholds | All match (Koureas form, unreversed open, reversed closed). |
| New configurations | 368 (see list below) | 0 disagreements with my assembly and LP. Totals: 662 OPTIMAL, 325 UNBOUNDED, 22 INFEASIBLE and 24 MECHANICAL_UNRESOLVED limits; critical results 156 bounded-on-domain, 37 exact closed, 56 input-resolution-limit, 13+ iteration-limit, 6 infeasible-on-domain. |
| Python referee, new configurations | 1178 limit + 276 critical queries | Every compared field equal, and query counts equal. |
| Scale | 61 rows × 1433 columns (unbounded) and 61 × 1345 (optimal 27/86 at μ=1/4) | Contact sets equal mine; certificates verify on my matrices. |
| True VV | 20 provably redundant and 10 unresolved points | Every redundant point has a certificate that verifies on my rows (multipliers ≥ 0, Hᵀw = 0, positive weight on a forbidden-cone row). No force constraints sit at VV points. Every unresolved point has a witness twist that verifies on my rows; those sets are refused with MECHANICAL_UNRESOLVED and carry no value or certificates. `true_vv_excluded_from_statics` appears exactly when a redundancy proof exists. |
| ABI status mapping | all checked queries | OPTIMAL→1, INFEASIBLE→5, UNBOUNDED→6, MECHANICAL_UNRESOLVED→7, UNPROVED→2, OVERLAP→4, CERTIFIED→1. Failed calls leave the output byte-identical; `max_steps` 4097 returns RESOURCE_LIMIT. |

The 368 new configurations cover:
- G5 sweeps;
- plates with all 8 masks and 5 anchors, including off-face anchors;
- towers, one closed form min(μW, Ww/2H) of them, plus offset stacks and a top-block plate;
- keystones (the horizontal-load threshold comes out exactly μ_crit = s, closed);
- the VV family, including twist redundancy that depends on the plate mask;
- infeasible and degenerate cases, and a clamp with an open threshold at 0;
- 90/180/270° rotations, reflections, scales from 2⁻³⁰⁰ to 2⁴⁰ and translations up to 2⁵⁰, with capacity and critical results unchanged;
- moved reference points, body permutations, clockwise and rotated-start vertex input, far anchors on free bodies;
- collinear (flat) vertices, L-shapes, three-body junctions;
- duplicate or reversed pairs (constraints are not duplicated) and incomplete pair lists (UNPROVED);
- `max_steps` of 0/1/2/7, μ_max of 0, subnormal and 2¹⁰⁰⁰;
- fixed–fixed VV contacts, which are correctly proved redundant.

**Info notes (no fix needed)**
1. **Free-body rows:** a free body's three equilibrium rows use the moment moved to its `dof_anchor`, not the literal moment about the reference point described in §4.5 and the work order. The LP is equivalent and values and statuses are identical, but `exact_y` and `mechanism` are anchor twists. This matches the Python referee and is documented in `statics.hpp`; C3-L4 sensitivity code reading y must use the same convention.
2. **Thickness coverage:** the C3L3 differential covers only the 36 T1b morphology cases. Most thickness samples are outside the binary64 ABI input domain; it would be worth stating that in the report.

All files are in `C:/Users/m1517/AppData/Local/Temp/claude/C--Agent--claude/659f270b-c2f6-43a9-9717-6dc28c605be4/scratchpad/c3l3_accept/statics/`:
- **Build:** `src/` (archived source and build), `build.log`
- **Checker core:** `work/mylp.py`, `work/myasm.py`, `work/mycapi.py`, `work/check.py`, `work/gen.py`, `work/teeth.py`
- **Run scripts:** `work/run_formal.py`, `work/run_t1b.py`, `work/run_new.py`, `work/run_extra.py`, `work/ref_compare.py`, `work/run_thick.py`, `work/run_thick_controls.py`, `work/scale_check.py`, `work/abi_status.py`, `work/probe_misc.py`
- **Outputs:** `work/run_new.out`, `work/ref_compare.out`, `work/scale.out`, `work/scale_hang.out`

Nothing was written under `D:/eab-wt`, no git writes were made, and no processes were killed.

# C3-L3 验收：临界参数 / ABI / 门 / 卫生路

**C3-L3 adversarial check, critical_parameter / ABI / gates / hygiene lens (commit c8718bb)**

**Verdict: not_close.** I found one MAJOR gate-teeth gap and two MINOR items. I found no production correctness defect: no false certified result from the unmutated C++ on any input I tried.

All work was in `C:/Users/m1517/AppData/Local/Temp/claude/C--Agent--claude/659f270b-c2f6-43a9-9717-6dc28c605be4/scratchpad/c3l3_accept/critical`, using copies made with `git archive c8718bb`. `D:/eab-wt/cx-c0` is still clean at HEAD c8718bb. I made no git writes, ran no installs, and stopped only processes I had started.

**Reproduction**
- Build: `cmd /c eab2\build_eab2.bat` gives `100% tests passed, 0 tests failed out of 12`.
- Author's differential on my build: `C3L3_DIFF limit=217 critical=171 mismatch=0`.
- `EAB2_DELIVERY_AUDIT status=PASS findings=0`.
- Harness pytest: `21 passed`.

**(1) critical_parameter semantics**
- **Strict field-by-field comparison** (`scripts/adv.py`): 171 of 171 corpus critical queries are identical between C++ and Python. That covers formal 114 (including the one UNSUPPORTED call), T1b 36, closed G1 9 and metamorphic 12. The comparison includes fields the author's tool ignores: query counts, threshold-proof header/intervals/reason, which proof sides are present, polynomial kinds, validity conditions and certificate statuses.
- **Same bisection path:** query counts match on all 171, so both sides bisected identically, and only in μ.
- **Independent role checks, all passed:**
  - every endpoint is binary64 and its bits equal its canonical rational;
  - the lower certificate is OPTIMAL or INFEASIBLE; the upper is UNBOUNDED with r_α = 1;
  - `input_resolution_limit` occurs exactly when the endpoints are adjacent binary64 values (checked with nextafter); `iteration_limit` otherwise;
  - attained=true always carries an UNBOUNDED certificate at the threshold, attained=false an OPTIMAL one with t < hi, and a null threshold carries no proof fields;
  - `reason` always equals `bisection_termination`, and `threshold_proof_reason` is never overwritten.
- **Required T1b thresholds:**

  | index | exact_threshold | attained |
  |---|---|---|
  | 13 | 131009/2097408 | true |
  | 16 | 98283/2097664 | true |
  | 30 | 326839/6291456 | true |
  | 8 | 1/16 | false |
  | 17 | 7/128 | false |

  At max_steps=100 all five also reach `input_resolution_limit` with the proof still present, so the two fields coexist correctly.
- **The eight irrational brackets** (width 2^-48; `scripts/irr.py`): in each bracket, the lower-end basis and the upper-end basis share a polynomial factor of degree 3–5. Its root in the bracket is not rational (checked with a denominator-bound test). So μ* is irrational and a null threshold/attained is correct.
- **Hand-built irreducible-quadratic case** (`scripts/quad.py`): a block wedged between a floor and a 45° ceiling, pulled outward. Its critical polynomial is μ²+2μ−1, so μ* = √2−1.
  - At 64 steps C++ and Python both return [0.41421356237309503, 0.4142135623730951] with `input_resolution_limit` and null/null.
  - Same result for the plate mask (1,1,0) and for the fully free block.
- **59 new adversarial queries:**
  - Thresholds that are not binary64 while all vertices are: G1 t=1/3, h=3/8 open and closed at 1/3; koureas 11/48. These reach adjacent endpoints and still carry a proof.
  - mu_max exactly at the threshold (closed 1/4 proven at hi; open 1/4 gives `bounded_on_domain`), the binary64 neighbours on each side, 0, −0, subnormal and DBL_MAX.
  - max_steps 0 and 1.
  - Farkas lower-end brackets, which the author's corpus never exercises: incline cases with open thresholds at 0 and at 1/13. C++ and Python agree.
  - All agree except two max_steps=0 cases (MINOR-1).

**(2) Mutation teeth** (`scripts/mutate.py`; results in `mut/out` and `mut2/out`). Each mutant was rebuilt and run through ctest, the author's differential, and my adversarial set.

| Mutant | Result |
|---|---|
| Closed threshold accepted without lower-side continuation | **Escapes** ctest, differential and my set (MAJOR-1) |
| Open threshold accepted without upper-side ray | Caught by critical_static ("endpoint state does not replace opposite-side continuation"); differential shows 0 mismatches |
| Open threshold without the zero-dead-load check | Escapes; logically equivalent to the original (see note below) |
| UNBOUNDED probe treated as finite | Caught: critical_static, differential 104 mismatches |
| Statics UNBOUNDED reported as OPTIMAL | Caught: statics_static and both c_header tests, differential 322 |
| Normal flipped | Caught: statics_static and critical_static, differential 428 |
| Friction y-sign flipped | Caught: statics_static "g minus then g plus sign convention", differential 268 |
| No reaction on body b / no action on body a | Caught: statics_static and critical_static, differential 370 / 428 |
| Plate mask applied at reference point instead of anchor | Caught: statics_static "released plate physical-anchor counterexample", differential 22 |
| Alpha column dropped | Caught: statics_static and critical_static, differential 424 |
| Dead-load sign flipped | Caught: statics_static and c3l3_abi_production_dll, differential 96 |
| attained always true | Caught: critical_static, differential 50 |
| `reason` overwritten | Caught: critical_static, differential 72 |

Note on the escaped zero-dead-load mutant: the `!nonzero(zero.b)` guard is redundant once the threshold point is OPTIMAL. Feasibility only grows with μ, so the feasible point at the threshold stays feasible above it. Removing the guard therefore cannot produce a false claim; it only makes the result less conservative than Python's.

**(3) ABI**
- **Export split:** production `eab2.dll` has 29 exports, including the three C3-L3 entries. `eab2_test.dll` adds only the test-only symbols; none leak into production.
- **Capability bits:** 16384 and 32768 were unallocated at 1b6b4f3. Production reports them; RHO/SE2/LP2 are still unsupported.
- **Input handling:** headers and atomic outputs follow the C0/C1/C3-L1 contract; the ABI tests check all of the following:
  - `reserved` must be 0;
  - `parameter` ≠ 1 returns UNSUPPORTED;
  - max_steps above 4096 returns RESOURCE_LIMIT;
  - NaN, Inf and negative inputs are rejected; −0 is accepted as 0, matching Python.

  The 4096 cap is ABI-only and is documented.
- **Static library:** `c_header_static` passes.

**(4) Hygiene**
- Net tracked growth over 1b6b4f3 is 732,574 B (77 files added, 10 modified, 0 removed), matching the report's 0.73 MB.
- The largest new file is `differential.json` at 178,960 B. The only file over 1 MB is `tools/exact_construction_policy.json`, whose blob is unchanged from 1b6b4f3.
- There is one authoritative `differential.json`; the baseline / final_fast / final_full folders are distinct runs.
- No TEMP files are committed. `build/tmp` paths appear only inside recorded command lines in the evidence.

**Defects**

1. **MAJOR-1: no gate covers the closed-threshold lower-side condition.** Dropping `(candidate == 0 || below.has_value())` at `critical.cpp:361` passes every shipped gate, yet produces false certified closed thresholds on legal ABI inputs. I brute-forced the original DLL against this mutant over 2310 G1 queries with wide brackets (`scripts/m_compare.py`) and found 15 false claims. Examples:
   - koureas t=3/32, h=1/16, mu_max=0.75, max_steps=4: the mutant claims 3/32 closed. The truth is 2039/32768; Python and the original C++ both return the bracket [3/64, 3/32] with null.
   - koureas t=3/8, h=1/4, mu_max=0.375, max_steps=1: the mutant claims 3/8; the truth is 119/512.

   The author's own checker `verify_critical` rejects both outputs ("closed threshold needs bounded continuation"). So the gap is corpus coverage, not the checker. The same family would also put the open-threshold mutant under differential coverage, which today relies on critical_static alone.

   **Fix:**
   - add these two cases as named regressions in `test_critical.cpp::threshold_contracts` (expect a null threshold);
   - add a wide-bracket differential family: G1 in all three orientations × max_steps 0–6 × mu_max from 0.125 to 4, plus the incline Farkas cases;
   - add both continuation mutants to `tools/eab2_c3l3_critical_mutations.py`.

2. **MINOR-1: C++ and Python disagree on attained/exact_threshold for wide brackets.** In a 592-query sweep, 20 queries (all with max_steps ≤ 2) have C++ proving a valid open threshold where Python returns null. Examples: G1 t=0 in all three orientations with max_steps=0; unreversed t=1/4, h=1/2, max_steps=2.
   - **Cause:** the two LPs return different (equally valid) improving rays, so they pick different bases. Python's own `branch_signs2` accepts the C++ basis, and `verify_critical` passes on the C++ output.
   - **Impact:** no false claim, and I never saw Python prove where C++ did not. But §7.4 compares status fields exactly and §7.5 needs a recorded disposition.
   - **Fix:** in the harness, require equality only when both sides are non-null; allow null against non-null only when the non-null proof passes `verify_critical`. Register the correction in the report. The same wide-bracket runs also show 10 benign query-count differences.

3. **MINOR-2: report overclaims.**
   - §4 lists attained among the "unique fields compared exactly". That holds only on the shipped corpus, which never ends in a wide bracket or a Farkas lower end.
   - §6's mutation self-check omits the two continuation conditions.
   - Everything else I checked in the report is accurate: counts, last lines, T1b indices, G1 closed forms, ABI and hygiene.

Everything is in `C:/Users/m1517/AppData/Local/Temp/claude/C--Agent--claude/659f270b-c2f6-43a9-9717-6dc28c605be4/scratchpad/c3l3_accept/critical`:
- `scripts/` — `adv.py`, `mutate.py`, `m_compare.py`, `irr.py`, `irr_lib.py`, `quad.py`, `dbg_steps0.py`, `m1_probe.py`
- `out/` — `differential.json`, `adv_corpus.json`, `adv_adv.json`, `adv_sweep.json`, `delivery_audit.json`
- `mut/out/mutation_results.json`
- `mut2/out/mutation_results.json`
