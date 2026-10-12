# WO-PERF：互锁优化证据补充

## 范围与回滚锚点

仅修改 `src/eab/kernel3d/interlock.py`、`src/eab/kernel3d/exact_sweep.py`；新增等价门和可复跑微基准。基线来自本树 `reports/codex/PERF_evidence/baseline/`，对应 c194dbb。未运行任何 Git 写命令。未修改任何旧测试断言、网格、skip 或 xfail。

## 事前定位

对 nx=5、ny=2、amp=.3、phase=1 的互锁体，依次运行两个 offset 的 `escape_height_covers` 与同输入 `escape_candidates`。原始 cProfile：`before.pstats`；累积/独占前 20：`before_top20.txt`。

总 cProfile 时间 6.156 s；`_candidates` 3.000 s，`_exact_escape` 3.161 s，其内 overlap 1.768 s、surface_events 1.378 s。cProfile 具有插桩开销，不与全套 pytest 无插桩耗时混比。

## 等价性证明

### 1. 名义盖候选完整内容缓存

`_candidates_uncached` 保留 c194dbb 原始计算顺序。新 `_candidates` 冻结 A/B 的全部顶点坐标、全部有序面环、offset、tol、extent_tol；另区分数字类型（float 与等值 Fraction 的平移构造可能不同），并包含枚举/局部盖/报告计算入口身份。

缓存值只含 immutable 元组；每次返回重新分配的列表，不允许调用者修改污染后续调用。源 Polyhedron 容器内直接改坐标或面环会改变内容签名。缓存仅加速名义报告，逃逸精确根和证书路径不变。

### 2. 仿射事件的精确静止轴排除与棱预构造

当速度分量 d[k]=0 时，接触特征在第 k 个坐标必须有共同投影。VF 中移动顶点必须落在三角形的闭区间；EE 中两棱的闭区间必须相交。所有坐标与边界比较均为精确有理数；只在 `ahi < blo` 或 `bhi < alo` 时排除，端点相等/切触仍保留。非零运动分量不用于该排除。

B 的每条棱向量和静止轴区间每次调用只构造一次；`-direction` 每次调用只构造一次。没有新增任何浮点过滤、误差界、容差或缓存。

## 对拍门

- `test_static_axis_pruning_matches_unpruned_all_event_values`：冻结 c194dbb 原始 event 算法，逐项比较 SurfaceEvent 的 time、label、normal（含法向大小）和顺序；随机平移、随机 dyadic tetra、一般三向速度、轴向速度、零速度、严格时间区间、平行切触、1e6 工程坐标、1e-300 薄片。
- `test_candidate_content_cache_matches_uncached_values`：原始计算顺序 vs 冷/热缓存；随机/退化/工程坐标；两组 offset、两组角度与长度报告带，严格 `==`。
- `test_candidate_cache_mutable_results_and_source_content_are_isolated`：返回列表编辑、顶点原位变更、面环原位变更均与原计算逐值一致。
- `test_candidate_cache_does_not_hide_a_cover_implementation_mutation`：分别把枚举模块 EE 入口、本地 extent 检查 EE 入口改成返回 None，确保缓存不屏蔽内部缺陷。

这些是优化等价参考，不冒充零共用原语的独立几何 oracle。原来的独立 oracle 门完整保留。

## 内部突变

| 优化 | 内部突变 | 看护断言 |
|---|---|---|
| 完整内容缓存 | `_candidates` 的 signature 删除 offset 项，但 actual arguments 仍保留真实 offset；先灌入 offset 1 再查询 offset 2 | `test_candidate_cache_has_teeth_when_signature_omits_offset`：`offset content must not alias` 报红；预先断言两组本来就产生不同结果 |
| 精确闭区间排除 | `_events_cached` 内 `ahi<blo or bhi<alo` 改为 `<=` | `test_exact_aabb_pruning_keeps_tangent_events_and_detects_strict_bound_mutation`：`tangent events must survive` 报红 |

无新浮点过滤，因此“误差界缩小 10 倍”不适用。

## 复跑

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; $env:PYTHONPATH='src'
python -X utf8 -m pytest -q tests/test_perf_interlock.py --junitxml reports/codex/PERF_evidence/interlock/equivalence.xml --basetemp reports/codex/PERF_evidence/tmp/interlock_equiv
python -X utf8 tools/perf_interlock_benchmark.py
```

新门最后一行：`99 passed in 2.34s`。微基准按同一当前基础几何实现对比两条互锁路径，避免把其他并行优化混入本项收益；候选缓存项明确报告 warm-cache。详见 `microbench.json`、`after.pstats`、`after_top20.txt`。

## 最终互锁局部验收与微基准

旧门子集（exact / walls / escape / sensitivity / bridge + 旧 EE 内核注入）：`108 passed in 165.25s (0:02:45)`，JUnit `targeted.xml`。

| 优化 | 输入类 | 未优化 / s | 优化 / s | 比值 |
|---|---|---:|---:|---:|
| 精确静止轴区间排除 | 一般互锁 nx5 | 0.191559 | 0.0230915 | 8.30x |
| 精确静止轴区间排除 | 网格对齐退化 | 0.246863 | 0.0553095 | 4.46x |
| 精确静止轴区间排除 | 1e6坐标、1e-3尺度 | 0.196453 | 0.0241241 | 8.14x |
| 内容缓存（明确为 warm） | 一般互锁 nx5 | 0.187981 | 0.00001450 | 12964x |
| 内容缓存（明确为 warm） | 网格对齐退化 | 0.185958 | 0.00001380 | 13475x |
| 内容缓存（明确为 warm） | 1e6坐标、1e-3尺度 | 0.177241 | 0.00001550 | 11435x |

候选缓存倍率只代表相同内容热缓存查询，不能作为整个求解加速倍数。相同代表操作序列（两次 escape + 两次 candidates）的 cProfile：6.156 s → 3.481 s；这是插桩测量，且 after 共用其他并行 exact_geom 优化，最终验收以无插桩全套为准。
