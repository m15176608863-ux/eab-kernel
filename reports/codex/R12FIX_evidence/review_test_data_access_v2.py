"""Site-specific finite review of attribute/format/modulo admissions in tests.

No field spelling is globally approved. Every candidate includes its exact
module, helper, expression and surrounding source; policy must pin its full
context and src/tests/tools dependency graph. This script never writes policy.
"""
import ast
import collections
import hashlib
import json
from pathlib import Path

BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[2]
notes={}
exempt=set()


def put(file, functions, note, *, exception=False):
    path='tests/'+file+'.py'
    for fn in functions.split('|'):
        notes[path,fn]=note
        if exception:exempt.add((path,fn))


LIFT='Reads the supplied Polyhedron/raw-ring coordinate and face-index fields, not a cached displayed normal or witness. This helper lifts those supplied scalar coordinates to Fraction before its independent determinant/Gram/squared-distance arithmetic.'
POSE='Reads the fixed test-shape vertex/face record to build a supplied pose/shape. Resulting floating coordinates define the actual test input; this helper does not claim recovery of an unrounded ideal pose or construct an exact expected norm from display coordinates.'
TOPO='Reads existing input vertex/face topology or source labels to compare/reindex the actual model. It does not construct a new numeric coordinate, root or norm.'
OUTPUT='Reads a completed API result field for a direct assertion, identity/count comparison, or actual-result record. It is not a source of the independent expected numerical answer and does not hide a conversion before constructing that answer.'
HARNESS='Reads implementation/source/module metadata only for controlled internal mutation or fixture execution. This is explicitly a fault-injection harness, not a correct-value oracle; the defect must be rejected by independent assertions.'
IO='Reads pathlib/stat/import or fixture-reader metadata for paths, byte-size, row identity or loading. No numerical geometry result is constructed from this access.'

put('e5a2_entrance_oracle','_model|assert_supporting_surface','The receiver is a Fraction produced by explicit F lifting; denominator is the exact positive integer used to clear common denominators. int(x*lcm) is exact integer embedding, not truncation of a floating value.')
put('e5a2_surface_oracle','_tetrahedra',LIFT)
put('e5a2_surface_oracle','star_overlap','The receiver is a Fraction in the independently constructed tetrahedra. Its exact positive integer denominator builds the common integer SAT embedding; no float conversion occurs.')
put('e5a_convex_oracle','assert_raw_coordinate_view',TOPO+' Both actual and expected records expose raw coordinates, face rings and source_vertices/source_faces index maps.')
put('e5a_cover_oracle','dot|_minor','The numerator/denominator receivers are Fraction/int values: dot guards the rational path with type checks, and _minor is only used for that rational cross path. These exact integer components implement rational common-denominator arithmetic, not a displayed-value conversion.')
put('e5a_cover_oracle','_model|cover_labels|_margin_witness_distance|margin_witness_squared',LIFT)
put('e5a_cover_oracle','margin_selection',LIFT+' Its final contact/selection policy is the declared historical floating window comparison, distinct from exact squared-distance construction.',exception=True)
put('e5a_g2_oracle','assert_exact_hull|construction',LIFT)
put('e5a_g2_oracle','assert_comparison',TOPO+' blocks[hb] is a loaded block record; faces/verts decode legacy references and malformed-triangle labels, not an expected root.')
put('e5b_frozen_oracle','surface',LIFT)
put('e5b_frozen_oracle','distance_squared','a/b are SimpleNamespace records returned by the reviewed surface helper; verts are Fraction tuples and faces are index rings. Exact point/triangle and edge/edge squared distances consume them without display conversion.')
put('e5b_margin_oracle','cover_squared',LIFT)
put('e5b_margin_oracle','check_exact_margin',OUTPUT+' label/closed/distance are actual margin-record fields; Fraction squared expected values and midpoint certificates are generated independently.')
put('e5b_wall_oracle','triangles',LIFT)
put('e5b_wall_oracle','_earliest|_star_root','The receiver is a Fraction coordinate from the independent rational triangles/tetrahedra. denominator is an exact integer and only participates in common-denominator clearing before integer swept SAT.')
put('perf_cover_oracle_reference','_model|cover_labels',LIFT)
put('perf_cover_oracle_reference','margin_selection',LIFT+' The final historical floating selection policy is explicitly not an exact-boundary theorem.',exception=True)
put('e5a_escape_oracle','candidates','Reads the supplied vertices/faces to form immutable cache keys and retained rational local models. The surrounding noise/window/candidate policy is an explicitly historical floating comparison, not the principal exact earliest-escape oracle.',exception=True)
put('perf_escape_oracle_reference','candidates','Reads the supplied vertices/faces for a frozen performance-reference cache. Its rounded translation and noise/window policy are explicitly a legacy-equivalence scope, not an exact earliest-escape oracle.',exception=True)
put('perf_sweep_reference','reference_events','The receiver e is a SurfaceEvent storing exact Fraction time and tuple label. Attribute reads are solely the deterministic sort key for event equality; no numerical conversion is introduced.')

put('test_bb52_g1','_retired_vote','c is a two-dimensional cover result; kind and gap feed the explicitly retired diagnostic vote, not a principal independent exact-membership oracle.',exception=True)
put('test_bb52_g1','_rounded_distance_audit','rep is the audit result; draws/samples/failures are integer coverage and failure counters, used only to assert that the rounding audit exercised cases.')
put('test_contact_record','_rec','Enum constants define a synthetic ContactRecord input. They are labels/modes, not numeric constructors.')
put('test_covers3_e5a','_ray_oracle.edges',LIFT)
put('test_covers3_membership','_rotated',POSE)
put('test_covers3_membership','_raw_support_classification',LIFT+' x.denominator belongs to the explicitly lifted Fraction coordinate and forms an exact integer SAT scale.')
put('test_covers3_membership','_assert_exact_facet_counts.coordinates',TOPO+' The tested canonical view is used only to decode actual label coordinates; independent expected supports were built from original coordinates first.')
put('test_covers3_membership','_assert_exact_facet_counts|_assert_exact_rotated_vote_counts',OUTPUT+' rep fields are integer facet/vertex/probe counters checked against independently generated exact sets; av/bv.verts provide only enumeration bounds.')
put('test_covers3_strict_lowdim','_ridge_and_spike|_ridge_and_spike.mv',POSE)
put('test_doc_pointers','_files|_resolve',IO)
put('test_e5a2_covers','_ring_normal|_distance2_oracle',LIFT)
put('test_e5a2_covers','_transform|_folded_pair',POSE)
put('test_e5a2_integer_arithmetic','_eager_ee|_fraction_membership',LIFT+' This is a frozen arithmetic-equivalence reference where declared; it is not represented as a primitive-independent proof.')
put('test_e5a2_interlock_bridge','_profile|_profile_data','Reads supplied Polyhedron coordinates to extract the prescribed profile/knots. _profile_data lifts scalar data with Fraction and _profile is the historical profile model; no displayed witness is used to reconstruct a distance.')
put('test_e5a2_surface','placed|roof',POSE)
put('test_e5b_polyhedron_cache','_noncanonical_translation_check','Reads the original Polyhedron vertex list to build an independent Fraction translated expectation for the actual returned view; no rounded witness is consumed.')
put('test_edge_arc_per_side','_chamfered_on_box',POSE)
put('test_end_to_end_cb2','_scaled',POSE)
put('test_end_to_end_cb2','_capacity','c.in_extent is a completed cover boolean used to select supplied mechanical contacts. It does not erase a numeric quantity or reconstruct an exact geometry output.')
put('test_entrance3','_rot',POSE)
put('test_entrance3_exact','_rational_motion',LIFT+' The resulting motion is retained as exact rational supplied geometry.')
put('test_entrance3_g2','_centroid','Reads original supplied input vertices to compute the input model center used by the G2 setup; it does not consume displayed cover points.')
put('test_fixture_provenance','_check|_fixture_files',IO)
put('test_frozen_ee_sign','_line_parameters_and_gap',LIFT)
put('test_frozen_ee_sign','_check_ee_exact',OUTPUT+' params/strict/in_extent/normal are compared to independent rational Gram/arc outputs; displayed normal is used only for a final direction-agreement dot product, not another exact distance.')
put('test_frozen_ee_sign','_xf|_corner_pair|_wedge_pair',POSE)
put('test_frozen_lowdim','_check_one','g is the returned Dual; v and e expose its primal and derivative channels for explicit value/derivative checks. The derivative norm and finite-difference tolerance are supplementary floating sensitivity checks, not an exact geometric construction claim.',exception=True)
put('test_frozen_surface_diagonal','_pair|_pair.move',POSE)
put('test_g03_two_rulers','_move|_yaw|_chamfered_box|_truncated_cube',POSE)
put('test_g03_two_rulers','_ok',OUTPUT+' r fields are audit booleans, counts and diagnostic mismatch records, not geometry reconstruction.')
put('test_g2_bdda3d','_fake_case',IO)
put('test_g2_bdda3d','_vf.make|_low_dim.make|_inject|_mutant_g2',HARNESS)
put('test_g2_bdda3d','_row_digest.canon','The loaded host block face-index list canonicalizes actual comparison keys; only source-label topology is read, not an exact distance input.')
put('test_geom3_e5a','_placed',POSE)
put('test_geom3_face_polygon','Frame.__call__','The Frame stores fixed rotation matrix R, scale s and origin o for test-input placement. Reads construct supplied binary64 points, not an unrounded exact-geometry expectation.')
put('test_geom3_merge','_face_set|_assert_exact_merge',TOPO+' Vertex equality and support/face identity are checked before and after merge.')
put('test_geom3_overlap_witness','OBB.moved|OBB.poly','OBB fields c/u/h are the fixed input center, axes and half sizes used to create supplied test geometry. This input-generation boundary is not a construction of an exact expected root.')
put('test_geom3_overlap_witness','_sat_sigma','EXPLICIT APPROXIMATE-REFERENCE SCOPE: OBB c/u/h fields feed the older floating SAT comparison, including normalized axes. Tests retain their existing separation-band filters; this is not admitted as a Fraction or arbitrary-input exact SAT proof. Exact surface assertions use separate rational oracles.',exception=True)
put('test_geom3_overlap_witness','_rigid|_rotz',POSE)
put('test_hull_robustness','_exact_worst_outside|_assert_exact_hull',LIFT)
put('test_hull_robustness','_worst_outside','EXPLICIT LEGACY DIAGNOSTIC SCOPE: this unused historical helper computes a floating support residual from hull coordinates. It is not the exact _exact_worst_outside oracle and must not be claimed as such.',exception=True)
put('test_hull_robustness','_rotated',POSE)
put('test_interlocking','_scaled_pair',POSE)
put('test_interlock_escape','_check_escape',OUTPUT+' sol.height/cover_label are compared against the independent declared analytic escape and tie-label reference.')
put('test_interlock_exact','_assert_exact_wall|_assert_interval_proof',OUTPUT+' exact_height is rational and interval_certificate contains rational endpoints and states; independent wall/root checks do not rebuild them from rounded display height.')
put('test_interlock_sensitivity','_steep_two_branches_in_report_band',POSE)
put('test_interlock_walls','_key|_place',POSE)
put('test_invariance_2d','_bb52_blocks',IO)
put('test_invariance_2d','_covers',OUTPUT+' Cover kind/index/strictness/gap are only normalized into an actual observable snapshot for metamorphic comparison, not an exact distance reconstructed from rounded points.',exception=True)
put('test_invariance_2d','_facet_set',TOPO+' The completed entrance-block facets are sorted/compared as labels, not used to form an expected numerical witness.')
put('test_invariance_geom','Motion.vec|Motion.point|Motion.poly',POSE+' self.R/self.s/self.t are the fixed placement parameters.')
put('test_invariance_geom','Motion.dist_tol','self.s/self.tmag are fixed input placement magnitudes used only for the declared relative display-comparison tolerance, not a branch predicate in the geometry implementation.',exception=True)
put('test_invariance_geom','_slab|_pair_tetra_box_vv',POSE)
put('test_invariance_geom','_base','EXPLICIT DISPLAY-REFERENCE SCOPE: completed cover point_a/point_b displays and flags determine historical observable witness/tie snapshots. math.dist of displayed points is not claimed as the exact distance oracle; the independent d truth is separately analytic or brute-feature geometry.',exception=True)
put('test_invariance_geom','_raw_coordinate_views',TOPO+' Original coordinates are saved before tested canonicalization.')
put('test_invariance_geom','_support_gap_oracle',LIFT)
put('test_invariance_interlock','_rigid|_yawed_stack',POSE)
put('test_invariance_interlock','_mag','Reads supplied vertex magnitudes solely to budget observable floating comparison tolerance; not a constructed geometric answer.',exception=True)
put('test_invariance_interlock','_escape','sol.cover_label chooses the actual frozen path; z.v/z.e are returned Dual channels compared under rigid-motion/unit transformations. This sensitivity observable is not an exact geometry reconstruction.',exception=True)
put('test_invariance_interlock','_margin_ref','EXPLICIT DISPLAY-REFERENCE SCOPE: actual cover flags and displayed point_a/point_b select historical metamorphic tie labels using a floating distance band. This is not the principal exact-distance oracle and does not justify arbitrary rounded-point reconstruction.',exception=True)
put('test_invariance_limit','Case.size','contacts is the fixed test-case input table and dim is an integer dimension. size is an input scale used for output comparison tolerance, not an exact geometric distance theorem.',exception=True)
put('test_invariance_limit','_cases','Case.name is a fixed test identifier; it is read only as the case dictionary key. fstrings create contact labels from integer indices.')
put('test_invariance_limit','_transform','Case dim/contacts/dead/live are declared input geometry/material/load tables used to build a transformed supplied mechanical model. They are not returned rounded geometry witnesses.')
put('test_invariance_limit','_reference','Case dim/k are integer model dimension/cone-discretization inputs passed to the solver under test; no approximate geometry is recovered from an output.')
put('test_invariance_limit','_dual_residuals','Case fields are fixed input load/contact tables and integer dimensions. The helper evaluates an explicitly floating residual/power comparison of returned dual values; it is not an exact LP certificate checker.',exception=True)
put('test_invariance_limit','_map_back','Case.dim is an integer dimension selecting the mechanical twist transformation formula; no numeric value is extracted from an opaque object for geometry construction.')
put('test_invariance_limit','_rtol','Case.size is the input-scale property for the stated relative floating output tolerance, not an exact predicate or geometry constructor.',exception=True)
put('test_kernel2d_exact','_probe_points','Reads exact entrance-block vertices and facet start/direction data to construct explicit supplied boundary/probe inputs. Final scalar_exact conversion occurs only at that test-input boundary, not before an expected norm.')
put('test_kernel2d_review','_load_both',IO+' Loaded StepGeometry blocks/poly/vidx/alias fields are returned for reader-vs-reader input identity checks, not recomputed geometry.')
put('test_kernel3d_geom','_placed|_placed_exact',POSE+' _placed_exact additionally retains Fraction motion coordinates.')
put('test_limit','_interlock_capacity','Cover in_extent/normal fields define the supplied mechanical contact model at the explicit geometry-to-LP interface. This test does not claim the cone/normal generation itself is an independent geometric oracle.')
put('test_limit','_flat_block_ratio',OUTPUT+' status and alpha are the actual solve status/capacity compared with the declared closed form.')
put('test_limit_arch','Arch.__init__|Arch.joint','Reads fixed arch input angle/radius/count/vertex tables to generate supplied contacts and load geometry. The trigonometric shape is the actual floating input model, not an exact ideal-circle oracle.')
put('test_limit_arch','Arch.problem','Arch weights/cents/crown/crown_body/n are fixed input data used to assemble mechanical loads and contacts; wrench construction has its own checked exact-derived boundary.')
put('test_limit_arch','Arch.hinge_mechanisms','Reads fixed arch input fields, then explicitly lifts joint points, normals, weights and centroids to Fraction before the independent hinge compatibility and power quotient solve. No rounded solve output is reused as its expected value.')
put('test_limit_contacts','_hovering_block|_cb2_covers','Cover in_extent/normal and local import-path metadata define supplied test contact records. These are mechanical input assembly sites, not an independent exact geometry proof.')
put('test_limit_duality','_assert_duality',OUTPUT+' alpha is the actual primal/dual objective under comparison; no root or norm is reconstructed.')
put('test_limit_fuzz','_genuinely_unresolvable','Reads supplied LimitContact.point to size deliberate random load perturbations. This uncertainty/probe generator is not an exact geometric-distance oracle; independent perturbed LP states are checked separately.',exception=True)
put('test_limit_multi','_mutant_module',HARNESS)
put('test_limit_scale','_scaled',POSE)
put('test_limit_scale','_interlock_covers','Completed cover normal and in_extent define the supplied mechanical contact model, not an exact expected geometry reconstruction.')
put('test_limit_scale','_capacity_ratio',OUTPUT)
put('test_limit_selfcheck','_utm_block',OUTPUT+' r.status only checks solve classification before independent equilibrium verification.')
put('test_lp_certificates','_old_formulation','C columns/row_of/n_rows are the declared generated polygonal cone model copied into the historical LP input formulation. This is an explicit supplied LP-model boundary, not a primitive-independent cone geometry claim.')
put('test_lp_certificates','_exact_limit_lp','C columns/owner/row_of/n_rows provide the declared cone discretization and integer bookkeeping; contact point/cohesion/area are original inputs. After choosing the actual centroid convention, coordinates/forces are independently lifted to Fraction before lever arms, load shift and cohesive caps. No displayed moment is reused as the exact expected moment.')
put('test_lp_certificates','_assert_same_exact_limit_result',OUTPUT+' result.alpha.exact is the retained rational objective certificate compared to an independent Fraction LP answer; result.alpha itself is only checked at final display/inf boundaries.')
put('test_lp_scale','_certify','Reads completed LP x/y/obj/status for explicitly relative floating residual checks. This supplementary historical checker is not the exact certificate oracle in test_lp_certificates.',exception=True)
put('test_m4_bdda_adapter','_key_from_label|_record_key','Reads Bdda BlockGeom block/vidx and ContactRecord cover/block/feature.index fields solely to reconstruct source-identity keys. Enum.value is a text label, not numeric coercion.')
put('test_m4_bdda_adapter','_assert_matches_independent_oracle','Reads StepGeometry.blocks and BlockGeom.poly as original supplied polygons; Bdda2DWindow d0/cone_tol/seg_tol are explicit model inputs. These are passed to independent Fraction neighbor-support/elimination; rec.extra only checks final observable metadata, never constructs the expected geometry.')
put('test_m4_bdda_shadow','_legacy_identity_gate','ContactRecord step/contact_index/raw_cover and extra dictionary are compared directly to independently parsed legacy CSV integer identities. There is no geometric construction.')
put('test_m4_bdda_vv_reader','_bb52_gate','ContactRecord cover/feature.index/extra are enum/integer identity fields checked against known raw VV corners. No numerical norm, root or rounding recovery occurs.')
put('test_margin','_lipschitz_probe_points','Reads supplied input body vertices to generate sample positions for the historical Lipschitz observable check. It is not an exact-distance constructor from returned witnesses.',exception=True)
put('test_margin_exact','_signed_gap',LIFT)
put('test_margin_exact','_assert_window_contract|_assert_default_contract',OUTPUT+' Margin constants are enum-like classification labels; actual contact closed/distance fields are checked against independently lifted scalar interval separation.')
put('test_margin_penetration','_convex_case|_nested_case',POSE)
put('test_margin_resolution','_assert_margin_consistent',OUTPUT+' distance and label fields are actual margin records checked for consistency, not a shared expected constructor.')
put('test_margin_resolution','_small_pair|_motion',POSE)
put('test_near_parallel_edges','_move',POSE)
put('test_perf_contact_window','_pose|_bilateral',POSE)
put('test_perf_contact_window','_intervals|_assert_axis_certificate|_assert_thick_bilateral_overlap_rejected','Reads raw supplied vertices for independently formed exact Cartesian interval certificates. Actual classification constants are only compared as labels; no displayed cover coordinate is fed into these intervals.')
put('test_perf_contact_window','_mutant',HARNESS)
put('test_perf_edge_frame','_normal|_frame',LIFT)
put('test_perf_edge_frame','_queries','Reads face-index rings to generate explicit feature query parameters; no numerical expected construction is performed by the field access.')
put('test_perf_integer_geometry','_move|sat_cases',POSE)
put('test_perf_integer_geometry','_sat_input',LIFT+' This is the declared shared-primitive Fraction performance reference, not an independent geometry proof.')
put('test_perf_interlock','_cases.move',POSE)
put('test_perf_surface_witness','_transform',POSE)
put('test_r10_initial_boundary','_assert_axis_aligned_label_has_closed_source_intersection.coordinates','Reads supplied axis-aligned source vertices/faces only to extract the finite source-feature coordinate sets and verify exact interval intersections; no displayed witness or normal is consumed.')
put('test_r6fix_dual_lp','_assert_exact_optimal_certificate',OUTPUT+' exact_x/exact_y are retained rational certificates whose equality, nonnegativity and complementary slackness are independently checked; status is a string label.')
put('test_r6fix_dual_lp','_mutant_function',HARNESS)
put('test_r6fix_geom3','_triangulated_box|_exact_boxes',POSE)
put('test_r6fix_geom3','_assert_returned_view_isolation|_assert_face_hints_do_not_change_convex_membership',TOPO+' These helpers deliberately mutate local input/view vertex or face containers to verify isolation, without constructing an expected numeric root.')
put('test_r6fix_geom3','_assert_exact_concavity',LIFT)
put('test_r8fix_gate_teeth','convex_view_mutant|reject_z_inside_cone_filter|all_branch_convex_view_mutant',HARNESS)
put('test_r8fix_gate_teeth','interval_union_pair|interval_union_pair.distance2',LIFT+' These are Fraction input interval-union fixtures and exact squared Cartesian separations, not injected post-output fake data.')
put('test_r8fix_initial_state','_assert_tight_seam_exit',OUTPUT+' got.kind is an entrance/escape state label.')
put('test_r8fix_initial_state3','_transform',POSE)
put('test_r8fix_margin_gap_gate','_arithmetic_fault_inside_margin_contacts',HARNESS)
put('test_r8fix_margin_gap_gate','_ordinary_binary64_midpoint_gap_gate|_large_gap_gate','B.verts is an explicit binary64 input-fixture edit; returned exact_distance_squared is checked against an independent interval-product Fraction value. distance/margin_gap/closed are actual fields certified by midpoint inequalities and exact expected values, never reused to form the expected radical.')
put('test_r9fix_construction','_separated_cubes',POSE)
put('test_r9fix_cover_parameters','_assert_parameters','Source verts are lifted to Fraction before independent Gram parameters. Returned kind/feature indices decode the actual feature; exact_params/in_extent/params are checked against that independent answer, and displayed params are only checked for visible underflow.')
put('test_r9fix_entrance_domain','_assert_contact_labels',OUTPUT+' label/tied_labels are fed to independent finite-feature membership using original input geometry; actual point_a/point_b are directly compared for coincidence, not normed to form an expected distance.')
put('test_r9fix_g03_construction','_bad_witness_report',HARNESS+' Report passed/failure/sample fields prove the injected defect was recorded, not silently accepted.')
put('test_r9fix_topology','_join',TOPO+' Existing shell indices are offset and concatenated to build the explicit input fixture.')
put('test_readers_roundtrip','_swapped|_assert_step_keys_unique|_primary_unique_records|_key_not_swap_symmetric','ContactRecord block/feature/step/contact_index/extra fields are identity and metadata for reader round-trip/swap determinism. No numeric expected geometry value is constructed.')
put('test_tf_reader','_census|_assert_rows_agree|_assert_modes_follow_their_own_columns','Reads actual parser result scalar/vector/enum/count/metadata fields and compares them with independent raw TSV column decoding. Float values are the declared parsed input records; no geometry norm or root is reconstructed from them. Nested enum.value gives a string, not a numeric callable.')
put('test_tf_reader','_mutant_reader',HARNESS)

format_notes={
 ('tests/test_fixture_provenance.py','_check'):'Assertion diagnostic text interpolates only the fixture path. The string is not parsed into a number.',
 ('tests/test_g2_bdda3d.py','_fake_case'):'Formats a pathlib stem into a local mutant fixture filename; not numerical data.',
 ('tests/test_geom3_merge.py','_call_with_timeout'):'Timeout assertion message formats a callable name and a time budget. No formatted output participates in geometry.',
 ('tests/test_invariance_limit.py','_cases'):'Creates contact label strings c/l/r plus the integer enumeration index. No numerical quantity is rounded into an expected result.',
 ('tests/test_kernel2d_review.py','_verts_csv'):'Writes original supplied binary64 x/y fixture coordinates with repr into a CSV for two independent readers. This is the explicit serialized input boundary; the round-trip string is not an intermediate exact derived quantity used by a norm.',
 ('tests/test_limit_duality.py','_asym_cohesive_block'):'Creates a contact identity label from an integer enumeration index, not a numeric construction.',
 ('tests/test_perf_contact_window.py','_assert_axis_certificate'):'Creates the expected classification-dictionary key from a literal axis name and sign; no formatting result becomes a geometry scalar.',
 ('tests/test_r9fix_g03_construction.py','_bad_witness_report'):'Controlled mutation harness formats a caught error into a diagnostic AssertionError message; the string never becomes expected numerical data.',
}

scan=BASE/'final_raw_scan_v2.json'
if scan.exists():
    raw=json.loads(scan.read_text())
    selected=[r[:5] for r in raw if r[0].startswith('tests/') and r[3] in ('closed-data-attribute','closed-modulo','closed-syntax')]
else:
    raw=json.loads((BASE/'test_new_attribute_inventory.json').read_text())
    selected=[[p,l,f,{'attr':'closed-data-attribute','mod':'closed-modulo','fstring':'closed-syntax'}[t],c] for p,l,f,t,c in raw]

cache={}
out=[]
for path,line,fn,rule,code in selected:
    if path not in cache:
        source=(ROOT/path).read_text(encoding='utf-8-sig'); tree=ast.parse(source); defs={}
        def walk(n,stack=()):
            if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):
                stack=(*stack,n.name);defs['.'.join(stack)]=n
            for child in ast.iter_child_nodes(n):walk(child,stack)
        walk(tree);cache[path]=source,defs
    source,defs=cache[path]
    key=(path,fn);reason=None;exception=key in exempt
    if rule=='closed-data-attribute':
        reason=notes.get(key)
    elif rule=='closed-syntax':
        reason=format_notes.get(key)
    elif rule=='closed-modulo':
        if key==('tests/test_geom3_face_polygon.py','_star'):
            reason='Floating angle modulo 2*pi only generates supplied random star input coordinates. The float pose is the model; this is not an exact-construction oracle.'
        elif key==('tests/test_geom3_face_polygon.py','_star_inside') and 'atan2' in code:
            reason='EXPLICIT APPROXIMATE-REFERENCE SCOPE: floating atan2 modulo 2*pi selects the ray sector in the existing polar-star comparison. Its caller retains the pre-existing margin>=1e-6 filter. This is not a principal exact predicate/construction proof.';exception=True
        elif 'struct.unpack' in code:
            reason='The >Q unpack result is an unsigned integer binary64 bit pattern; integer %2 checks RN-even parity. No float formatting, conversion or arithmetic modulus is used.'
        elif code.replace(' ','')=='hits%2':
            reason='hits is an integer ray-intersection counter; %2 is exact parity for the independently computed rational crossing count, not float/string formatting.'
        elif key==('tests/test_bb52_g1.py','_drop_ve_subset'):
            reason='ia is the integer source vertex index; %7 selects the controlled subset for an internal mutation, not a numerical oracle.'
        elif key in {('tests/test_perf_2d_directions.py','direction_cases'),('tests/test_perf_covers.py','_samples'),('tests/test_perf_integer_geometry.py','distance_cases'),('tests/test_perf_integer_geometry.py','sat_cases')}:
            reason='The left operand is the integer range/enumeration counter; remainder chooses a deterministic test-input pattern, not an exact numerical construction.'
        else:
            # Exact inventory sites were individually printed/read: all these
            # remaining remainders wrap range/enumeration face/ring indices.
            prior=json.loads((BASE/'test_new_attribute_inventory.json').read_text())
            exact={(p,f,c) for p,l,f,t,c in prior if t=='mod'}
            if (path,fn,code) in exact:
                reason='At this exact reviewed site, the operands are an integer range/enumeration vertex/component index and an integer ring/face length (or literal 3/4/5/6). Modulo wraps topology/component indexing; it is neither string interpolation nor a floating numerical constructor.'
    scope=defs.get(fn)
    lines=source.splitlines();context='\n'.join(lines[max(0,line-4):line+3])
    out.append(dict(path=path,line=line,function=fn,rule=rule,code=code,
        reason=('Access '+code+': '+reason) if reason else 'NEEDS_REVIEW: no source-scoped justification assigned; do not auto-admit.',
        status='reviewed_candidate' if reason else 'needs_review',needs_review=not bool(reason),scope_exemption=exception,
        source_context=context,scope_ast_sha256=hashlib.sha256(ast.dump(scope,include_attributes=False).encode()).hexdigest() if scope else None,
        review_boundary='Human site candidate only; full module AST and src/tests/tools graph must stay pinned. No global field-name admission.'))

for name,data in [('test_data_access_review_v2.json',out),('test_data_access_needs_review_v2.json',[r for r in out if r['needs_review']]),('test_data_access_scope_exemptions_v2.json',[r for r in out if r['scope_exemption']])]:
    (BASE/name).write_text(json.dumps(data,ensure_ascii=True,indent=2)+'\n',encoding='utf-8')
print('source',scan.name if scan.exists() else 'preliminary inventory')
print('count',len(out),'by rule',collections.Counter(r['rule'] for r in out),'status',collections.Counter(r['status'] for r in out))
print('needs review',collections.Counter((r['path'],r['function']) for r in out if r['needs_review']))
