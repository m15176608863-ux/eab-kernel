# 代表格 cProfile 实测

9 格，退出码 0，带 profiler 墙钟 6.645 s。此耗时不可代替未插桩全套验收。

|生产函数|调用|自身秒|累计秒|
|---|---:|---:|---:|
|`src/eab/kernel3d/covers3.py:576::enumerate_covers3`|23|0.006155|2.774138|
|`src/eab/margin.py:336::_resolved`|45|0.000158|2.764850|
|`src/eab/margin.py:344::_resolved_cached`|14|0.000176|2.764692|
|`src/eab/margin.py:295::_resolve`|14|0.000552|2.764510|
|`src/eab/margin.py:170::_witnesses`|17|0.000193|2.327553|
|`src/eab/margin.py:352::body_distance`|12|0.000126|2.189803|
|`src/eab/kernel3d/covers3.py:366::cones_intersect_relint`|1416|0.003045|1.343525|
|`src/eab/kernel3d/covers3.py:377::_cone_relint_cached`|856|0.005235|1.340480|
|`src/eab/kernel3d/covers3.py:311::_qclosest_hull`|792|0.005129|1.288730|
|`src/eab/kernel3d/covers3.py:522::vv3_cover`|1304|0.001982|1.262843|
|`src/eab/kernel3d/covers3.py:290::_qclosest_simplex`|2158|0.011533|1.036579|
|`src/eab/kernel3d/geom3.py:61::dot`|268692|0.079319|0.998641|
|`src/eab/rational3.py:19::dot`|191618|0.370609|0.811777|
|`src/eab/kernel3d/covers3.py:146::_qedge_contains`|18361|0.065260|0.794954|
|`src/eab/kernel3d/covers3.py:451::ee_cover`|4446|0.016972|0.699245|
|`src/eab/kernel3d/covers3.py:262::_qclosest_triangle`|3091|0.008170|0.578857|
|`src/eab/margin.py:438::inflated_membership`|23|0.000076|0.575909|
|`src/eab/kernel3d/g03.py:119::g0_convex3`|2|0.000833|0.551188|
|`src/eab/kernel3d/covers3.py:494::ve3_cover`|4740|0.013239|0.487616|
|`src/eab/kernel3d/geom3.py:812::brute_feature_distance`|14|0.003994|0.372042|

节点与全部生产函数见 JSON，原始 profile 见 `.pstats`。
