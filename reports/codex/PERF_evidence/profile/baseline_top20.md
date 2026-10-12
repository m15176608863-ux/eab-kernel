# E5b 最终 JUnit：基线前 20

来源：`reports/codex/E5b_evidence/final.xml`。文件耗时为节点 `time` 汇总，不含额外进程开销。

## 测试文件

|文件|秒|格数|
|---|---:|---:|
|tests/test_invariance_interlock.py|384.060|574|
|tests/test_invariance_geom.py|199.445|2406|
|tests/test_interlocking.py|143.715|17|
|tests/test_interlock_sensitivity.py|93.656|41|
|tests/test_interlock_walls.py|75.465|12|
|tests/test_bb52_g1.py|70.898|17|
|tests/test_interlock_escape.py|61.974|19|
|tests/test_frozen_lowdim.py|37.837|15|
|tests/test_entrance3.py|35.211|37|
|tests/test_invariance_2d.py|27.406|851|
|tests/test_g4_multistep.py|26.787|7|
|tests/test_limit.py|24.580|67|
|tests/test_frozen_ee_sign.py|22.493|99|
|tests/test_kernel2d_predicates.py|21.372|151|
|tests/test_kernel2d_g0.py|18.802|115|
|tests/test_limit_scale.py|17.832|146|
|tests/test_hull_robustness.py|16.603|185|
|tests/test_covers3_g0_vote2.py|15.415|95|
|tests/test_kernel3d_geom.py|12.666|68|
|tests/test_lp_certificates.py|11.864|171|

## 测试节点

|节点|秒|
|---|---:|
|`tests/test_interlocking.py::test_g0_distance_completeness_gate_is_unit_invariant_and_keeps_its_teeth[1000.0]`|31.034|
|`tests/test_interlocking.py::test_g0_distance_completeness_gate_is_unit_invariant_and_keeps_its_teeth[0.001]`|29.767|
|`tests/test_interlocking.py::test_g0_distance_completeness_gate_is_unit_invariant_and_keeps_its_teeth[1.0]`|25.804|
|`tests/test_interlock_escape.py::test_escape_height_covers_is_complete_off_axis_on_asymmetric_blocks[nx5 amp0.3 phase0]`|22.121|
|`tests/test_interlock_escape.py::test_escape_height_covers_is_complete_off_axis_on_asymmetric_blocks[nx5 amp0.3 phase1.0]`|19.651|
|`tests/test_interlock_walls.py::test_vertical_walls_do_not_hijack_the_escape_height[1000.0-4]`|18.655|
|`tests/test_interlocking.py::test_g0_distance_completeness_on_concave_interlocking_pair[2]`|16.770|
|`tests/test_interlock_walls.py::test_vertical_walls_do_not_hijack_the_escape_height[10000.0-1]`|16.709|
|`tests/test_interlock_sensitivity.py::test_steep_profile_kink_is_flagged_consistently_with_the_predicate[0.001-0.0]`|16.103|
|`tests/test_interlock_walls.py::test_vertical_walls_do_not_hijack_the_escape_height[100000.0-4]`|15.487|
|`tests/test_frozen_lowdim.py::test_every_body_distance_label_enters_the_frozen_path_convex_400`|15.449|
|`tests/test_interlock_sensitivity.py::test_steep_profile_kink_is_flagged_consistently_with_the_predicate[1000.0-100000.0]`|14.708|
|`tests/test_bb52_g1.py::test_g0_exit_completeness_has_teeth[drop_VE_subset]`|14.553|
|`tests/test_interlocking.py::test_g0_distance_completeness_on_concave_interlocking_pair[0]`|14.131|
|`tests/test_interlock_sensitivity.py::test_steep_profile_kink_is_flagged_consistently_with_the_predicate[1.0-100000.0]`|13.556|
|`tests/test_interlocking.py::test_g0_distance_completeness_on_concave_interlocking_pair[1]`|12.599|
|`tests/test_invariance_interlock.py::test_escape_tied_set_is_invariant_up_to_the_declared_resolution[z0.7-0.0-1000.0]`|12.532|
|`tests/test_interlock_sensitivity.py::test_steep_profile_kink_is_flagged_consistently_with_the_predicate[1.0-0.0]`|11.806|
|`tests/test_invariance_interlock.py::test_escape_tied_set_is_invariant_up_to_the_declared_resolution[z0.7-0.0-0.001]`|11.736|
|`tests/test_interlocking.py::test_g0_distance_completeness_on_merged_interlocking_pair`|11.537|
