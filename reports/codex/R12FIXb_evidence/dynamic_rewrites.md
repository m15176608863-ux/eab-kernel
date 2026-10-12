# R12FIXb 数值动态写法改写证据

## 范围与结果

- 仅改本工作树的 **22 个 `src/eab` 源文件 + 9 个 tests 独立数值 helper**；既有测试驱动只改 `tests/test_lp.py` 一处私有 API 实参及 r6/r7 两处必要源码变异锚点。保留全部既有测试节点、参数化装饰器与断言。
- 消除 **26 处**形参 / 容器 / 本地 alias / 临时对象 dunder 间接执行（原数值路径 20 + `_face_witness` 2 + reader `canon` 2 + `_candidates_cached` 1 + `Dual.__rsub__` 1）；**108 处** `map(命名函数, 数据)` 改为直接调用的 generator comprehension（src 90 + 独立 helper 18）；**15 处**捕获数值函数的 `min/max(..., key=lambda ...)` 改为显式数值 key 数据。另外 oracle 的 2 个整数化 lambda 改成直接调用的命名 helper。
- 未改公开 API。LP 的私有 `_Revised.optimize` / `_certified_optimize` 最后位置参数改为 `None` 或 `(A0, c0, ec)` 数据，不再接收/执行数值回调。
- 原数值表达式的算术次序保持；min/max 的 `(key, 序号, 对象)` 使用唯一枚举序号，使对象永不参与平局比较。min 用正序号，max 用负序号，均保留最先出现者获胜。
- 按 baseline 对齐并恢复原混合换行；例如 `margin.py` 改前/改后均保留原有 9 个 CRLF 行，其余 LF 不统一重写。

## 改写分类

| 类别 | 文件及代表 | 实际改写 |
|---|---|---|
| 缓存中的实现参数 dispatch | `kernel3d/covers3.py` `_qedge_vector_cached`、`_qincident_cached`、`_qnorm2`、`_qvertex_state_cached`、`_qedge_frame_cached` | 参数不再调用；改直接 `_qvector` / `_qedge` / `dot` / `_outside_dot_band` / `cross` 调用 |
| 容器 callable dispatch | `kernel3d/covers3.py` `_cone_relint_cached` | `implementations[0](...)` 改为显式 `source` 布尔分支和两处命名函数调用 |
| 缓存 predicate / event callback | `kernel3d/interlock.py` `_exact_escape_cached` | 改直接 `_nonpenetrating_at` / `surface_events` / `_prior_intervals` 调用 |
| 缓存 resolve callback | `margin.py` `_resolved_cached` | `implementation(...)` 改直接 `_resolve(...)` |
| 排序 key callback | `margin.py` `_tie_groups` | 调用方先形成数值 key 列表，函数只比较索引和数据 |
| LP 无界射线 callback | `lp.py` `_Revised.optimize`、`_float_solve`、`_certified_optimize` | 去掉闭包与常量 lambda；一阶段 `None` 表示不接纳无界射线，二阶段由原始数据直接 `_ray_verifies(...)` |
| face locate 本地 callable alias | `kernel3d/covers3.py` `_face_witness` | 两处 `locate(...)` 改直接 `geom3.face_polygon_locate(...)` |
| reader 条件 callable | `readers/bdda_df.py` `_vv_opposite_vertex`、`load_records` | 取消 boundmethod / identity lambda 选择，改显式条件调用或原 id |
| 独立 oracle callback helper | `tests/e5b_wall_oracle.py` `_earliest`、`_star_root` | `ints=lambda...` 改具名局部 helper，整数表达式及调用顺序不变 |
| 数值反射 | `limit.py` `LimitContact.__post_init__` | `getattr(self, name)` 改显式 `(name, value)` 数据对 |
| Cover3 反射打包 | `margin.py` `_resolved_cached` | `fields/getattr` 改显式 16 字段，保留 immutable cache payload 与重新构造 Cover3 的机制 |
| lambda AABB helper | `kernel3d/geom3.py` `_surfaces_intersect` | 不再构造/调用 lambda，改两个显式 comprehension |
| map / 捕获数值函数的 key lambda | 逐文件见 JSON | 直接函数调用及稳定序号，不使用 callable dispatch |

### 缓存键为何仍含函数对象

缓存 key 仍包含旧有实现身份，用于 monkeypatch 缺陷注入后触发 cache miss；这些对象仅作为 hash / identity 数据，**缓存函数体不从这些参数调用函数**。这与以 callable 形参动态决定数值实现不同。删除身份键会把旧正常结果从缓存取回，破坏既有变异测试的牙，因此不能删除。保留直接命名调用同样能命中被 monkeypatch 的当前实现。

## 必须保留的公开高阶 API

`dual.central_difference(f, theta, h)` 中 `f(tp)` 和 `f(tm)` 两站点保留：它是 G3 公共通用中心差分诊断器，而不是生产几何构造 API。其用途是产生待比较的有限差分导数，不把已经舍入的差分交给 sqrt / norm / unit / 几何差分构造。删除 callable 会取消 API 本来要实现的功能；硬编码已知测试函数亦不可接受。

这不是“任意外部 f 的函数体已被静态证明”的声称：外部 callable 的实现必须由调用方负责。静态门若给予例外，应分别锁这两个调用节点以及本函数源码，并明确其诊断用途。`contact_record.from_dict` 的 `cls(**kw)` 为 dataclass 工厂而非数值构造 callback；contact_record 中余下反射为序列化/字段比较，本次未扩展改动范围。

## 验证

第一轮（主要 dispatch 改写后）：`281 passed in 67.92s (0:01:07)`。

第二轮（含 90 map 和 15 numerical-key 改写；15 个相关测试文件）：

```text
564 passed in 75.44s (0:01:15)
```

子进程 exit code = 0；外层计时 79.416604500002 秒。命令、完整输出分别保存在 `dynamic_targeted_tests.json` / `.log`。覆盖 LP 反循环与失稳注入、缓存隔离、margin 内部缺陷注入、3D cone/edge、G03、精确 interlock 以及敏感度路径。该局部验证不替代总工单的全套运行或独立 G6 审查。

所有源码编辑已冻结，可供父任务静态门清单与最终全套验证使用。


## 追加改写与原变异门兼容

`tests` 范围仅限非 `test_*` 的独立 helper，实际涉及 9 个文件；未改 test_r9 / r10 / r11 / r12 静态缺陷注入源码字符串。逐文件清单在 `dynamic_helper_rewrites.json`。

既有源码变异测试必须跟随被测函数的新文本，故只更新：

1. `test_r6fix_construction.py::test_g6f08_relative_projection_gate_has_teeth`：把旧 `tuple(map(scalar_rational, point))` 锚点和同义替换文本同步到 comprehension。变异仍是**函数内部删除 exact 分支，强制舍入**，红在原守护断言 `exact relative distance`，实测 `0.0 != 1e-09`。
2. `test_r7fix_limit_construction.py::test_limit_normal_early_rounding_mutation_is_caught`：只更新 `source.index` 的 Fraction 转换锚点。变异体（提前缩放并归一）和守护消息 `normal component rounded before final normalization` 原样。

这两节点单独复跑：`2 passed in 0.11s`；完整输出见 `dynamic_mutation_anchor_tests.log`。三个被修改的测试驱动文件均对 baseline 做 AST 核对：所有 test 函数名及 parametrization 装饰器逐项一致。

追加 10 个相关测试文件（含 readers、face-polygon、oracle、原变异门）完整复跑：

```text
456 passed in 103.66s (0:01:43)
```

exit code = 0；外层计时 107.75841600002605 秒。见 `dynamic_append_tests.log/json`。源码、helper 和必要 mutation anchor 均已冻结。


## 最后补齐的缓存动态写法

- `interlock._candidates_cached`：去掉 `snapshot.signature[-1][0]` 的 callable dispatch，改直接 `_candidates_uncached(...)`；实现身份仍保留在缓存 signature。
- `geom3.Polyhedron._sync_geometry_cache`：固定 10 个 cache 字段的 `setattr` 循环改为 10 条直接属性赋值，原有 `_geometry_signature` 写入不变（共 11 条直接写）。
- 定向验证：`116 passed in 7.65s`，exit 0；命令显式使用 `-p no:cacheprovider --basetemp=reports/codex/R12FIXb_evidence/tmp/dynamic_cache_final`。证据 `dynamic_cache_final_tests.log/json`。

## 约束执行偏差（必须披露）

前期定向 pytest 未指定 `--basetemp`；追加 456 节点测试含 tmp_path reader 测试，因此**确实在工作树外创建了测试临时文件**。只读核查确认：系统 `C:/Users/m1517/AppData/Local/Temp/pytest-of-m1517/pytest-1059` 于 2026-10-12 22:55:07 创建，22:56:52 完成，含 42 个临时 CSV fixture；与本次 `dynamic_append_tests.log` 的 22:55:06–22:56:52 对应。未删除、未修改外部文件。该偏差不影响数值测试结果，但违反“只写本树”，不能声称完全遵守。

后续所有本子任务 pytest 已改为显式本树唯一 basetemp 并禁用 cacheprovider。只读核查及时间证据见 `dynamic_temp_scope_deviation.json`。


## structural 审核后的最后 5 处机械简单化

- `Dual.__rsub__`：`(-self).__add__(o)` 改 `-self + o`；支持的 int/float/Dual 输入仍先取负再做加法，公开签名不变。
- `geom3._quickhull_once`：`max(cand,key=off_line)` 改 `(off_line(i),-序号,i)` 预计算 key；局部 exact dot/cross 表达式、每候选求 key 次数及首个平局不变。
- `kernel2d.exact.entrance_membership_exact` / 独立 `g0_oracle.boundary_has_exterior` / `kernel3d.entrance_topology._chamber_directions`：三处 `cmp_to_key` 数值 callback 改各自局部稳定插入排序，仅在原比较器 `compare(previous,new)>0` 时前移位置，原三个精确纯比较器 AST 完全不变；没有引入共享 oracle 几何原语。
- 这些是 callback 消除，不是改几何公式；插入排序为 O(n²) 而原 Timsort O(n log n)，大扇区数性能属于明确残留风险，现有 hull/拓扑定向节点未退化到失败。
- 未编辑任何测试文件。8 个相关测试文件（包括内部缺陷注入牙）：`538 passed in 29.20s`，exit 0，外层 29.909731099993223 秒，显式本树 basetemp/no-cacheprovider。
- 抽取实际源码里的新排序循环，对照原 cmp_to_key 契约：3 处 × 50 随机重排，每次 128 个 Fraction 方向，包含同角不同对象，150 次值序和**平局对象身份序**均一致；比较器 AST 与重写前一致。
- 明细/日志：`dynamic_final_structural_rewrites.json`、`dynamic_final_structural_tests.json/.log`、`dynamic_final_sort_equivalence.json`；只读重跑脚本 `verify_dynamic_final_sort.py`。总计 numerical-key callback 消除 16 处（15 lambda + off_line），另 comparator callback 3 处。
