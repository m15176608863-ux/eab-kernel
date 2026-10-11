# E5a2 性能剖析与答案不变优化证据

## 1. 方法与可信边界

- 被 profile 的代码是开始编辑前复制的 HEAD `5b09ea3`：`tmp/profile_baseline/src` / `tests` / `tools`。原始测试与参数网格未减；六个指定文件均完整运行，以下只纳入 returncode=0 的 prof。
- cProfile 会显著放大 Python/Fraction 调用成本；vote2 首份先顺序完成，其余文件并行 profile。这里的累计时间占比用来定位调用树，不能把 profile wall 与最终无 profiler 的整套 wall 混为一谈。累计时间包含下游调用，各行不可相加。
- 每文件 JSON 同时保留全部 src/eab（包括独立 G0 oracle）的前20累计/自身耗时；下表另列排除 g03/g03_exact/g0 验证器之后的核心函数前20。独立 oracle 热点另标，不曾调用被测 rational3 几何算术。
- 原始 `.prof` 可用 `python -X utf8 -m pstats FILE.prof` 重读。完整 profile 运行器为 `tmp/run_profile.py`。所有 pytest `--basetemp` 在本证据目录，禁写 pyc，禁 pytest cacheprovider。
- 编排故障如实保留：初次 runner evidence 根路径选错导致测试前 FileNotFoundError；bb52 两次完整运行均16过、最后文档检查因未复制引用JSON失败；补齐两份JSON并先单跑该门绿后，第三次才纳入最终统计。失败 prof/json/log 保留 `missing_report` / `missing_linked_report` 命名。并行启动竞态造成一个重复 sensitivity 子进程，已仅终止重复实例，未采用其结果。

## 2. 六文件完整基线 profile

| 测试文件 | cProfile wall (s) | 状态 |
|---|---:|---|
| test_invariance_interlock | 1277.295 | 完整通过 |
| test_invariance_geom | 690.946 | 完整通过 |
| test_interlocking | 526.781 | 完整通过 |
| test_interlock_sensitivity | 432.321 | 完整通过 |
| test_covers3_g0_vote2 | 307.313 | 完整通过 |
| test_bb52_g1 | 269.881 | 完整通过 |

### test_invariance_interlock 核心函数前20

| 函数 | 调用次数 | 累计 s | 占 profile wall | 自身 s |
|---|---:|---:|---:|---:|
| `eab/kernel3d/covers3.py:518:enumerate_covers3` | 1885 | 640.939 | 50.18% | 2.044 |
| `eab/kernel3d/interlock.py:211:escape_height_covers` | 231 | 465.342 | 36.43% | 0.069 |
| `eab/kernel3d/covers3.py:435:ee_cover` | 1637483 | 459.483 | 35.97% | 8.114 |
| `eab/kernel3d/interlock.py:156:_candidates` | 305 | 441.223 | 34.54% | 0.462 |
| `eab/margin.py:179:_resolve` | 1982 | 349.717 | 27.38% | 0.076 |
| `eab/kernel3d/covers3.py:131:_qedge_contains` | 5730215 | 293.584 | 22.98% | 26.428 |
| `eab/kernel3d/geom3.py:430:face_polygon_locate` | 3565301 | 280.069 | 21.93% | 5.000 |
| `eab/kernel3d/exact_geom.py:135:polygon_locate` | 3565301 | 273.529 | 21.41% | 49.947 |
| `eab/kernel3d/geom3.py:585:polyhedra_overlap` | 2781 | 268.718 | 21.04% | 0.772 |
| `eab/kernel3d/geom3.py:485:point_in_polyhedron` | 329701 | 235.201 | 18.41% | 11.068 |
| `eab/margin.py:157:_witnesses` | 1574 | 222.998 | 17.46% | 0.020 |
| `eab/margin.py:210:body_distance` | 1226 | 212.701 | 16.65% | 0.007 |
| `eab/kernel3d/geom3.py:60:dot` | 62283793 | 201.320 | 15.76% | 21.133 |
| `eab/margin.py:245:margin_contacts` | 756 | 137.069 | 10.73% | 0.009 |
| `eab/kernel3d/interlock.py:188:escape_candidates` | 74 | 113.562 | 8.89% | 0.009 |
| `eab/kernel3d/covers3.py:407:_qclosest_params` | 1409774 | 109.094 | 8.54% | 2.898 |
| `eab/margin.py:275:inflated_membership` | 756 | 105.999 | 8.30% | 0.012 |
| `eab/kernel3d/geom3.py:64:cross` | 8733897 | 92.288 | 7.23% | 8.411 |
| `eab/kernel3d/covers3.py:92:_outside_dot_band` | 11227871 | 78.789 | 6.17% | 12.609 |
| `eab/kernel3d/exact_geom.py:33:_im` | 31013562 | 77.567 | 6.07% | 23.891 |

含验证 oracle 的调用树首五名：
- `eab/kernel3d/covers3.py:518:enumerate_covers3`：640.939 s / 50.18%。
- `eab/kernel3d/interlock.py:211:escape_height_covers`：465.342 s / 36.43%。
- `eab/kernel3d/covers3.py:435:ee_cover`：459.483 s / 35.97%。
- `eab/kernel3d/interlock.py:156:_candidates`：441.223 s / 34.54%。
- `eab/margin.py:179:_resolve`：349.717 s / 27.38%。

### test_invariance_geom 核心函数前20

| 函数 | 调用次数 | 累计 s | 占 profile wall | 自身 s |
|---|---:|---:|---:|---:|
| `eab/kernel3d/covers3.py:518:enumerate_covers3` | 1674 | 271.291 | 39.26% | 0.575 |
| `eab/margin.py:179:_resolve` | 1492 | 259.311 | 37.53% | 0.049 |
| `eab/margin.py:157:_witnesses` | 1278 | 187.294 | 27.11% | 0.014 |
| `eab/margin.py:210:body_distance` | 792 | 184.606 | 26.72% | 0.004 |
| `eab/kernel3d/geom3.py:60:dot` | 26365244 | 144.018 | 20.84% | 12.058 |
| `eab/kernel3d/covers3.py:350:cones_intersect_relint` | 92960 | 115.342 | 16.69% | 0.400 |
| `eab/kernel3d/covers3.py:361:_cone_relint_cached` | 57400 | 114.942 | 16.64% | 0.496 |
| `eab/kernel3d/covers3.py:502:vv3_cover` | 88624 | 112.284 | 16.25% | 0.164 |
| `eab/kernel3d/covers3.py:295:_qclosest_hull` | 49589 | 111.929 | 16.20% | 0.389 |
| `eab/kernel3d/geom3.py:430:face_polygon_locate` | 1087146 | 98.009 | 14.18% | 1.571 |
| `eab/kernel3d/covers3.py:131:_qedge_contains` | 1393418 | 96.851 | 14.02% | 6.528 |
| `eab/kernel3d/exact_geom.py:135:polygon_locate` | 1087146 | 95.977 | 13.89% | 15.210 |
| `eab/kernel3d/geom3.py:585:polyhedra_overlap` | 2658 | 91.246 | 13.21% | 0.336 |
| `eab/margin.py:275:inflated_membership` | 385 | 91.105 | 13.19% | 0.005 |
| `eab/kernel3d/covers3.py:435:ee_cover` | 225036 | 88.161 | 12.76% | 1.455 |
| `eab/kernel3d/covers3.py:274:_qclosest_simplex` | 132090 | 87.362 | 12.64% | 0.907 |
| `eab/kernel3d/geom3.py:485:point_in_polyhedron` | 294796 | 85.866 | 12.43% | 4.214 |
| `eab/margin.py:245:margin_contacts` | 700 | 74.742 | 10.82% | 0.009 |
| `eab/kernel3d/geom3.py:978:convex_hull_3d` | 2507 | 73.132 | 10.58% | 0.004 |
| `eab/kernel3d/geom3.py:987:convex_hull_3d_eps` | 2507 | 73.128 | 10.58% | 0.006 |

含验证 oracle 的调用树首五名：
- `eab/kernel3d/covers3.py:518:enumerate_covers3`：271.291 s / 39.26%。
- `eab/margin.py:179:_resolve`：259.311 s / 37.53%。
- `eab/margin.py:157:_witnesses`：187.294 s / 27.11%。
- `eab/margin.py:210:body_distance`：184.606 s / 26.72%。
- `eab/kernel3d/geom3.py:60:dot`：144.018 s / 20.84%。

### test_interlocking 核心函数前20

| 函数 | 调用次数 | 累计 s | 占 profile wall | 自身 s |
|---|---:|---:|---:|---:|
| `eab/kernel3d/covers3.py:518:enumerate_covers3` | 200 | 329.373 | 62.53% | 1.009 |
| `eab/kernel3d/covers3.py:435:ee_cover` | 591840 | 125.466 | 23.82% | 2.674 |
| `eab/kernel3d/geom3.py:60:dot` | 38016978 | 115.386 | 21.90% | 13.660 |
| `eab/kernel3d/geom3.py:926:brute_feature_distance` | 197 | 112.152 | 21.29% | 0.941 |
| `eab/kernel3d/geom3.py:430:face_polygon_locate` | 1392537 | 111.460 | 21.16% | 1.950 |
| `eab/kernel3d/exact_geom.py:135:polygon_locate` | 1392537 | 108.872 | 20.67% | 22.175 |
| `eab/kernel3d/covers3.py:131:_qedge_contains` | 2472637 | 95.563 | 18.14% | 9.595 |
| `eab/kernel3d/geom3.py:869:_seg_seg_distance` | 1221552 | 87.169 | 16.55% | 6.945 |
| `eab/kernel3d/covers3.py:474:ve3_cover` | 645840 | 83.235 | 15.80% | 2.003 |
| `eab/kernel3d/geom3.py:585:polyhedra_overlap` | 607 | 83.127 | 15.78% | 0.190 |
| `eab/kernel3d/covers3.py:502:vv3_cover` | 179100 | 79.366 | 15.07% | 0.092 |
| `eab/kernel3d/covers3.py:350:cones_intersect_relint` | 179100 | 78.508 | 14.90% | 1.100 |
| `eab/kernel3d/covers3.py:361:_cone_relint_cached` | 179100 | 77.407 | 14.69% | 1.198 |
| `eab/kernel3d/geom3.py:485:point_in_polyhedron` | 66630 | 76.151 | 14.46% | 3.434 |
| `eab/kernel3d/covers3.py:295:_qclosest_hull` | 112603 | 66.537 | 12.63% | 0.461 |
| `eab/kernel3d/exact_geom.py:339:segment_distance_squared` | 155904 | 63.528 | 12.06% | 3.525 |
| `eab/kernel3d/covers3.py:492:ev3_cover` | 322320 | 41.783 | 7.93% | 0.201 |
| `eab/kernel3d/covers3.py:92:_outside_dot_band` | 5119071 | 41.276 | 7.84% | 6.942 |
| `eab/kernel3d/covers3.py:112:_qvertex_contains` | 968655 | 40.715 | 7.73% | 3.280 |
| `eab/kernel3d/covers3.py:274:_qclosest_simplex` | 164978 | 35.473 | 6.73% | 0.622 |

含验证 oracle 的调用树首五名：
- `eab/kernel3d/g03.py:165:g0_distance_completeness3`：516.746 s / 98.10%。
- `eab/kernel3d/covers3.py:518:enumerate_covers3`：329.373 s / 62.53%。
- `eab/kernel3d/covers3.py:435:ee_cover`：125.466 s / 23.82%。
- `eab/kernel3d/geom3.py:60:dot`：115.386 s / 21.90%。
- `eab/kernel3d/geom3.py:926:brute_feature_distance`：112.152 s / 21.29%。

### test_interlock_sensitivity 核心函数前20

| 函数 | 调用次数 | 累计 s | 占 profile wall | 自身 s |
|---|---:|---:|---:|---:|
| `eab/kernel3d/interlock.py:211:escape_height_covers` | 169 | 296.393 | 68.56% | 0.038 |
| `eab/kernel3d/geom3.py:585:polyhedra_overlap` | 992 | 238.290 | 55.12% | 0.486 |
| `eab/kernel3d/geom3.py:430:face_polygon_locate` | 2897394 | 224.160 | 51.85% | 4.036 |
| `eab/kernel3d/exact_geom.py:135:polygon_locate` | 2897394 | 218.838 | 50.62% | 41.280 |
| `eab/kernel3d/geom3.py:485:point_in_polyhedron` | 140045 | 210.883 | 48.78% | 8.665 |
| `eab/kernel3d/interlock.py:156:_candidates` | 173 | 191.389 | 44.27% | 0.190 |
| `eab/kernel3d/covers3.py:518:enumerate_covers3` | 173 | 180.304 | 41.71% | 0.622 |
| `eab/kernel3d/covers3.py:435:ee_cover` | 674968 | 149.059 | 34.48% | 2.917 |
| `eab/kernel3d/interlock.py:58:escape_height_brute` | 18 | 129.665 | 29.99% | 0.001 |
| `eab/kernel3d/interlock.py:71:intruding` | 642 | 129.660 | 29.99% | 0.038 |
| `eab/kernel3d/covers3.py:131:_qedge_contains` | 2102870 | 82.814 | 19.16% | 8.928 |
| `eab/kernel3d/exact_geom.py:33:_im` | 23568166 | 62.090 | 14.36% | 19.513 |
| `eab/kernel3d/geom3.py:60:dot` | 33015931 | 46.321 | 10.71% | 7.506 |
| `eab/kernel3d/covers3.py:407:_qclosest_params` | 545291 | 38.427 | 8.89% | 1.097 |
| `eab/kernel3d/geom3.py:64:cross` | 3021028 | 29.957 | 6.93% | 3.012 |
| `eab/kernel3d/geom3.py:445:_distance_to_face_polygon` | 287632 | 25.800 | 5.97% | 0.276 |
| `eab/kernel3d/exact_geom.py:29:_is` | 57205186 | 23.844 | 5.52% | 15.038 |
| `eab/kernel3d/covers3.py:383:vf_cover` | 183646 | 21.247 | 4.91% | 0.277 |
| `eab/kernel3d/exact_geom.py:35:<genexpr>` | 117840830 | 20.190 | 4.67% | 14.632 |
| `eab/kernel3d/covers3.py:395:fv_cover` | 184600 | 19.109 | 4.42% | 0.288 |

含验证 oracle 的调用树首五名：
- `eab/kernel3d/interlock.py:211:escape_height_covers`：296.393 s / 68.56%。
- `eab/kernel3d/geom3.py:585:polyhedra_overlap`：238.290 s / 55.12%。
- `eab/kernel3d/geom3.py:430:face_polygon_locate`：224.160 s / 51.85%。
- `eab/kernel3d/exact_geom.py:135:polygon_locate`：218.838 s / 50.62%。
- `eab/kernel3d/geom3.py:485:point_in_polyhedron`：210.883 s / 48.78%。

### test_covers3_g0_vote2 核心函数前20

| 函数 | 调用次数 | 累计 s | 占 profile wall | 自身 s |
|---|---:|---:|---:|---:|
| `eab/kernel3d/covers3.py:674:membership_convex3` | 43900 | 80.403 | 26.16% | 4.595 |
| `eab/kernel3d/geom3.py:60:dot` | 5066567 | 51.597 | 16.79% | 3.441 |
| `eab/kernel3d/covers3.py:350:cones_intersect_relint` | 20383 | 14.428 | 4.69% | 0.053 |
| `eab/kernel3d/covers3.py:361:_cone_relint_cached` | 4856 | 14.375 | 4.68% | 0.046 |
| `eab/kernel3d/covers3.py:295:_qclosest_hull` | 4688 | 13.939 | 4.54% | 0.043 |
| `eab/kernel3d/geom3.py:44:sub` | 2361297 | 12.544 | 4.08% | 1.082 |
| `eab/kernel3d/covers3.py:274:_qclosest_simplex` | 14045 | 10.782 | 3.51% | 0.101 |
| `eab/kernel3d/covers3.py:246:_qclosest_triangle` | 21819 | 6.107 | 1.99% | 0.071 |
| `eab/kernel3d/geom3.py:1224:exact_convex_view` | 92594 | 4.667 | 1.52% | 0.027 |
| `eab/kernel3d/covers3.py:564:local_facets3` | 227 | 4.403 | 1.43% | 0.006 |
| `eab/kernel3d/covers3.py:571:_local_facets_cached` | 83 | 4.099 | 1.33% | 0.052 |
| `eab/kernel3d/covers3.py:251:<genexpr>` | 81784 | 3.899 | 1.27% | 0.082 |
| `eab/kernel3d/geom3.py:978:convex_hull_3d` | 515 | 3.571 | 1.16% | 0.001 |
| `eab/kernel3d/geom3.py:987:convex_hull_3d_eps` | 515 | 3.570 | 1.16% | 0.001 |
| `eab/kernel3d/geom3.py:994:_quickhull` | 515 | 3.569 | 1.16% | 0.019 |
| `eab/kernel3d/geom3.py:64:cross` | 175621 | 3.537 | 1.15% | 0.172 |
| `eab/kernel3d/covers3.py:131:_qedge_contains` | 56018 | 3.197 | 1.04% | 0.218 |
| `eab/kernel3d/geom3.py:1087:merge_coplanar` | 967 | 2.952 | 0.96% | 0.066 |
| `eab/kernel3d/covers3.py:237:_qclosest_segment` | 59300 | 2.730 | 0.89% | 0.150 |
| `eab/kernel3d/geom3.py:1022:_quickhull_once` | 515 | 2.427 | 0.79% | 0.055 |

含验证 oracle 的调用树首五名：
- `eab/kernel3d/g03.py:119:g0_convex3`：302.641 s / 98.48%。
- `eab/kernel3d/g03_exact.py:143:overlap`：193.115 s / 62.84%。
- `eab/kernel3d/g03_exact.py:21:scalar`：126.150 s / 41.05%。
- `eab/kernel3d/covers3.py:674:membership_convex3`：80.403 s / 26.16%。
- `eab/kernel3d/g03_exact.py:22:<genexpr>`：68.835 s / 22.40%。

### test_bb52_g1 核心函数前20

| 函数 | 调用次数 | 累计 s | 占 profile wall | 自身 s |
|---|---:|---:|---:|---:|
| `eab/kernel2d/covers.py:256:enumerate_covers` | 13869 | 231.414 | 85.75% | 2.589 |
| `eab/kernel2d/covers.py:150:_ve_side` | 5145701 | 119.973 | 44.45% | 17.519 |
| `eab/kernel2d/covers.py:174:ve_cover` | 2800804 | 83.350 | 30.88% | 1.149 |
| `eab/kernel2d/covers.py:202:vv_cover` | 2218639 | 68.926 | 25.54% | 2.279 |
| `eab/predicates.py:33:cross2_sign` | 7856900 | 60.182 | 22.30% | 19.669 |
| `eab/kernel2d/covers.py:186:ev_cover` | 2344897 | 55.704 | 20.64% | 1.365 |
| `eab/kernel2d/covers.py:159:_ve_side_directions` | 786812 | 38.370 | 14.22% | 0.936 |
| `eab/kernel2d/geom.py:382:polygons_overlap` | 68571 | 34.313 | 12.71% | 0.759 |
| `eab/kernel2d/covers.py:213:<genexpr>` | 1463633 | 29.240 | 10.83% | 1.072 |
| `eab/kernel2d/covers.py:67:_vsub` | 7772786 | 28.885 | 10.70% | 2.746 |
| `eab/kernel2d/covers.py:198:_open_cone` | 1822088 | 23.831 | 8.83% | 0.574 |
| `eab/kernel2d/covers.py:71:_raw_cone` | 9582979 | 23.220 | 8.60% | 8.961 |
| `eab/kernel2d/geom.py:58:dot` | 4658589 | 22.650 | 8.39% | 2.140 |
| `eab/kernel2d/geom.py:178:_point_in_polygon` | 1078882 | 18.855 | 6.99% | 7.041 |
| `eab/kernel2d/covers.py:135:_project` | 445080 | 14.852 | 5.50% | 1.308 |
| `eab/kernel2d/covers.py:229:_line_data` | 474274 | 13.115 | 4.86% | 0.691 |
| `eab/kernel2d/covers.py:143:_angle_window2` | 466653 | 12.178 | 4.51% | 0.607 |
| `eab/kernel2d/geom.py:168:point_side` | 23045116 | 12.055 | 4.47% | 7.163 |
| `eab/kernel2d/covers.py:235:_in_segment_exact` | 247947 | 11.354 | 4.21% | 0.731 |
| `eab/kernel2d/geom.py:205:segments_properly_cross` | 2103799 | 11.237 | 4.16% | 2.381 |

含验证 oracle 的调用树首五名：
- `eab/kernel2d/covers.py:256:enumerate_covers`：231.414 s / 85.75%。
- `eab/kernel2d/covers.py:150:_ve_side`：119.973 s / 44.45%。
- `eab/kernel2d/covers.py:174:ve_cover`：83.350 s / 30.88%。
- `eab/kernel2d/g0.py:332:g0_exit_completeness`：70.191 s / 26.01%。
- `eab/kernel2d/covers.py:202:vv_cover`：68.926 s / 25.54%。

## 3. 优化前后与逐值对拍

以下为三轮同输入微基准中位数，各次均逐答案比较相等；运行时仍有 baseline profiler 并行，数值仅解释优化因果，**不是全套达标证据**。完整样本/各轮时间见 `optimization_benchmarks.json`。

| 优化 | 优化前 s | 优化后 s | 倍数 |
|---|---:|---:|---:|
| common_denominator_dot_cross | 0.030513 | 0.015727 | 1.94x |
| independent_sat_integer_rows | 0.158552 | 0.012520 | 12.66x |
| deferred_ee_parameters | 0.104673 | 0.058312 | 1.80x |
| membership_integer_plane_rows | 0.061067 | 0.008820 | 6.92x |
| angular_band_integer_comparison | 0.013595 | 0.004232 | 3.21x |

- 另有 root 的二维 Fraction 双线性符号整数化：交错进程CPU中位数、输入逐位不变；详见 `bilinear_benchmark.json` / `test_e5a2_bilinear_integer.py`，不与上述 wall 混排。
- dot/cross：公共分母上整数乘加，一次 Fraction 归约；其他 float / Dual / mixed 类型仍走原表达式。`test_common_denominator_operations_equal_pure_fraction_every_coordinate`：1369 对 × 3 接入层，含随机、有理奇分母、完全退化、工程平移、最大浮点和次正规。
- 独立 G0 SAT：原先每 query 构造 Fraction 投影/区间，改为保存精确上下界的分子分母、每 query 一次公分母整数化。`test_integer_sat_rows_equal_original_fraction_for_random_boundary_engineering`：4 尺度 × 3 退化/一般位置 × 97 query，共1164逐状态对拍；不共享被测几何算术。
- EE 调度：精确法锥先排除不可能盖，再计算原有线参数；B锥失败不求A锥；同一 axial 点积复用。`test_deferred_edge_parameters_preserve_every_eager_fraction_cover`：2592 个完整 Cover/None 与旧 eager Fraction 公式逐字段相等。
- membership：既有支撑平面缓存 payload 增加正齐次整数系数，符号与正 tol 距离平方均在整数上比较；外部 Euclidean 最近点语义不改。`test_integer_membership_rows_equal_fraction_random_boundary_and_corner_band`：774 query逐态对拍，含外角报告带；已有cache的跨对象与顶点list原位修改另有 `test_extended_existing_plane_cache_tracks_objects_and_mutable_coordinates`。
- 角窗：将四个临时 Fraction 乘积改为正分母整数交叉乘，原严格比较不变；`test_integer_angular_band_comparison_equals_fraction_at_and_near_thresholds`：6848 比较，含精确阈值与±2^-60邻格。
- 快路接线门 `test_fraction_geometry_operations_really_dispatch_to_integer_arithmetic` 额外记录两个几何模块确实调用整数算术。初始文本编辑遇混合换行曾仅插入import而漏4函数接线，值对拍对此无牙；现已补真实接线与此spy门。早期 vote2 `95 passed in 19.17s` 尚未享受基础dot/cross加速，不能作为最终计时。

## 4. 缓存、过滤与突变边界

- 本组优化**没有新增浮点过滤，没有新增持久缓存层，也没有改变已有缓存键**。只复用既有 sat_model / support_planes 缓存保存等价整数系数；所以上述优化不存在“新过滤误差界÷10”或“新缓存去掉对象身份”的可执行项，不能伪报这些突变通过。
- 已有 support_planes 缓存按完整坐标/拓扑值寻址，而非对象身份，几何相同安全共享；拓扑或坐标变化会换键。既有 exact_convex_view 对象缓存视对象不可变的历史假设不在本次新增缓存范围；一般非规范视图对象的原地修改仍需调用方谨慎/后续专项。
- `integer_mutations.json` 保存5项真实内部突变，含源函数SHA256与目标日志：dot末项反号、SAT边界改开、平面offset反号、角窗 > 改 >= 均由对应纯Fraction对拍断言报红；整数快路断开由spy接线断言报红（只证明性能接线，不冒充几何声称）。
- 第一次角窗突变日志实际目标断言已红，但驱动只搜索字符串 AssertionError 而漏认 pytest 展开的 `E   assert`，产生一次 false-negative 汇总；修正仅证据解析，未动门，重跑5项均命中。失败驱动日志保留 `integer_mutations_frozen.log`。

## 5. 测试改写与最终验收

- 本性能子任务没有改写/删除任何已有测试、缩小参数格、增加skip/xfail。新增 `tests/test_e5a2_integer_arithmetic.py` 共25个展开测试；root的2D门另计。
- 独占全套时间、最终剩余热点、A1/A3语义迁移后的全套结果由主报告 `reports/codex/E5a2_report.md` 给出。本报告不把子集或并行profile认作900秒/600秒达标。
