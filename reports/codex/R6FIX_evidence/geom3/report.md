# WO-R6FIX：三维缓存、凸性及 nominal 平移分项报告

本分项负责 G6F-01、02、03、09。修改仅在本工作树；未提交、未改姊妹树、未创建 worktree。基线回滚锚由主代理保存于 `../baseline_tracked.zip`。本分项没有运行全套，不能代替主报告的全套/独立退出审查。

## 1. 红 → 绿与根因

最初新增 20 格后，在对应生产代码尚未修改时运行：`17 failed, 3 passed in 0.30s`，完整输出见 [before_red.log](before_red.log)。收集错误（错误 import membership_convex3）先纠正后才计此有效红证据，未把 collection error 当作缺陷的牙。

| 发现 | 修前红与具体断言 | 根因/修法 | 修后覆盖 |
|---|---|---|---|
| G6F-01 critical | `source-membership-isolated`：源未变而 `assert -1 == 1`；另外五种拓扑 getter 清空返回 list 后再次读取为空 | 非 self 凸视图缓存改不可变 `(vertices, faces, source_vertices, source_faces)` payload；每次读取构造隔离 Polyhedron。有效 canonical self-view 仍允许 `view is source`，源内容签名每次核验；源修改正确失效。所有 list 拓扑 getter 返回隔离副本 | 原点成员=1、内含小盒重叠=1；原有 source 内容失效测试全部保留；edges/vertex_faces/edge_faces/edge_traversals/vertex_edges 五类隔离 |
| G6F-02 major | `convex-point-ignores-face-hints`：反绕顶面返回 -1；交叉顺序顶面曾抛 zero-area | 输入脸的顶点集合相等不足以复用；增加与已算出的 canonical outward ring 的循环同序核验。反绕、交叉提示重建 canonical 凸视图，保持可用源编号映射 | reverse/crossed/cycle/empty 四种提示均与 `conv(vertices)` 区间真值一致；正常盒仍保留原 `is P` 契约 |
| G6F-03 major | `exact-midpoint-concavity`：原点 binary64 2^-50 凹槽与 Fraction 工程坐标凹槽均错误判凸 | 删除隐式 dihedral noise 筛选；以原输入的未归一化有理 Newell 法向和有理棱向量三重积读二面角符号；`tol` 留作兼容参数但不再改变几何 | 精确凹棱 `(3,8)`，2^-300/2^300 尺度、1e8 平移；另加精确有理正交旋转与 1e3/1e5/1e6 平移组合 9 格。oracle 是两屋顶峰的中点高于谷底，不用生产法向 |
| G6F-09 minor | 同值 int/float 零 offset 导致 `ValueError: zero-length edge (0,1)`；直接 `exact-mixed-affine-translation` 显示 1e8 附近微特征被舍去 | `Polyhedron.translated` 遇 Fraction 坐标或 offset 时先有理化再加；进一步发现**全 float 微体 + 大 float offset**也同根，因此 interlock nominal 的四个平移点全部使用 `translate_exact`，不能只给混合类型补丁 | 三种零 offset 均精确根 `7/4000000000`；全 float 2^-40 微体移到 1e8 的精确根仍 `7*2^-40/4`。独立区间端点 oracle |

G6F-09 扩展例修前红见 [nominal_before_red.log](nominal_before_red.log)：仅修混合 Fraction 后，全 float + 大 offset 仍会 zero-length edge，证明第二步确实治同根问题，而非只迎合原复现。

## 2. 变异牙

所有变异在被测函数内部、运行进程内临时替换实现；没有在输出后追加假盖。可重跑 [run_mutations.py](run_mutations.py)，机器清单见 [mutations.json](mutations.json)，完整故障栈见 [mutations.log](mutations.log)。

| 变异 | 实際报红的看护断言 |
|---|---|
| 01：重新把 mutable view 原对象存回源缓存并直接返回 | `source-membership-isolated` |
| 01 同类：edges 重新直接返回缓存 list | `topology-result-isolated` |
| 02：移除 outward 循环绕向核验，仅比较 set | `convex-point-ignores-face-hints` |
| 03：精确符号改回 `dihedral_turn + dihedral_noise` | `exact-midpoint-concavity` |
| 09：混合平移回退 Fraction + float 直接加 | `exact-mixed-affine-translation` |
| 09 同根：nominal 构造重新使用普通 float body translation | `exact-large-offset-escape blocked by nominal construction` |
| norm 同类：回退 `sqrt(dot(a,a))` | `representable-norm` |
| 既有近并行门：内部恢复 float 参数 → 舍入全局投影 → 相减 | `near-parallel-distance-two-ulps` |

运行最后一行：`8 internal mutants killed by the intended assertion`。上述红来自目标不变量断言，不是 source matcher、列顺序或求解器选点偶然性。

## 3. 全仓同类扫描与补修

静态定位命令：`rg -n 'noise_floor|dihedral_noise|_convex_view|@lru_cache|_RAY_DIRS|translated\(' src/eab`；定位快照 [scan_locations.txt](scan_locations.txt)。另外逐个检查缓存返回结构、调用者是否泄漏 mutable 子对象。

### 已发现且补修

1. 五种 Polyhedron 拓扑 getter 返回内部 list（同 01）。原始红包含在 17 failed 中。
2. `_ray_directions` 首次生成直接返回全局缓存 list；改返回副本。
3. `exact_sweep.translate_exact` 返回对象共享源 `faces` list；改复制外层 list，面环保持不可变 tuple。
4. `norm = sqrt(dot(a,a))` 在可表达范数 2^±600 时先平方下溢/溢出：普通 float 用 `hypot`，Fraction 用共享有理平方根。独立单位轴真值，4 格先红见 [norm_before_red.log](norm_before_red.log)。超输出范围的统一行为由主代理负责构造层收口。
5. `_point_segment_distance` 微尺度浮点平方先变零，投影退到端点；改有理投影/平方距。
6. `_seg_seg_distance` 常规支先舍入工程坐标投影再相减：本应 1e-9 报 0；改全程有理平方距、最后开方。
7. `_point_face_distance` 混合 Fraction/float 全局投影使实际面内点跌到面外（None 而非 1e-9）；改有理法向、有理投影与有理 gap²。
8. `brute_feature_distance` 两个严格分离微盒在 1e8 报 0，正确 2e-9；改确定性三角面与全部源棱的精确平方距离枚举，最小值取完才开方。新增显式 `allow_underflow=False`，默认不得静默下溢；margin 内部带精确平方证书的显示调用可显式 True。它与生产共享 exact_geom，只是内部佐证，已删除“独立 G0 oracle”声明；G03 主 oracle 由另一分项单独实现，不调用本 helper。
9. `_segment_closest_points` 原 Ericson 公式的浮点平方/平行窗口也丢微棱或工程坐标投影：改原始数据有理化、精确零判定与有理钳位、返回精确点。3 格先红见 [projection_before_red.log](projection_before_red.log)。

第 2、3、5–8 项六条先红统一在 [scan_before_red.log](scan_before_red.log)：`6 failed, 30 deselected in 0.15s`。

### 扫描判为已隔离或另分项处理

- `predicates` 的 scalar cache、kernel2d/covers 的 Fraction/cone tuples、kernel3d/covers3 的 vectors/normal/cone/planes/local facets、exact_geom 的 polygon/triangulation/integer surface/star tetrahedra、g03/g03_exact 的 hull/SAT：缓存返回 Fraction、tuple、bool、frozenset 等不可变值；公开 local_facets 返回新 set。
- interlock nominal rows 缓存为 tuple，public 结果新 list；exact escape payload 是 tuple + frozen SurfaceEvent，无 mutable 模型外泄。完整 typed source/offset/容差/实现指针纳入 key。
- margin `_surface_view` 与 `_resolved_cached` 曾有私有 mutable payload；已通知主代理，主代理负责不可变 payload + fresh 实例门，本分项未跨文件修改。
- 2D 凹性旧噪声及 G0 oracle 归 g0 分项修复；未重叠编辑。
- geom3 尚保留 `_contact_cone_witness/_active_normals/_gordan_direction` 的历史私有辅助链和旧说明，但 `rg` 没有公共生产入口调用；当前 `polyhedra_overlap` 直接转 exact_geom.surface_overlap。本分项不声称这些无调用的历史辅助是新的精确 oracle。

## 4. 测试改写台账

仅改写一个既有**变异门的注入方法**：`tests/test_geom3_e5a.py::test_g6e_near_parallel_legacy_parameter_mutation_is_killed`。

- 原门依赖匹配被测函数中的 `if a > 0.0 and c > 0.0 and nn <= 1e-8 * a * c:` 并替换为 False。R6 去除整个 float 分支后，该 substring 不存在，最初集成 `1 failed,104 passed` 是过时注入定位器失败，未当作新缺陷红证据。
- 保留相同几何、同一独立 `exact_seg_seg` oracle、同一个 `> 2*ulp(want)` 杀变异标准。
- 新注入在被测 `_seg_seg_distance` 内部调用旧根因算法（float 参数与全局舍入投影），且 monkeypatch 真实入口后执行原回归函数，确认 `near-parallel-distance-two-ulps` 断言失败。
- 原正确路径 `<=2 ulp`、交换 A/B、body_distance 断言全部保留；只给第一条加描述性消息。未删除/放宽/skip/xfail/缩网格。
- 新增门全部在 `tests/test_r6fix_geom3.py`，共 50 格（包含独立旋转/平移/尺度和 7 个捕获变异测试）。

## 5. 本分项验证日志

所有 Python 命令均用 `$env:PYTHONDONTWRITEBYTECODE='1'; python -X utf8`；pytest 均 `-p no:cacheprovider --basetemp=reports/codex/R6FIX_evidence/tmp/geom3_*`。

| 范围 | 原样最后行 | 日志 |
|---|---|---|
| 第一轮相关 geom3/interlocking 旧门与新门 | `160 passed in 84.59s (0:01:24)` | [after_green_initial.log](after_green_initial.log) |
| 同类改造 + R6 + cache + margin_exact | `52 passed in 3.69s` | [scan_after_green.log](scan_after_green.log) |
| 较广 face_polygon/margin/near_parallel + R6 | `210 passed in 21.42s` | [regression.log](regression.log) |
| 最终 R6 + old cache + geom3_e5a，源码/测试冻结时 | `105 passed in 0.79s` | [final_green.log](final_green.log) |

最终命令：

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -X utf8 -m pytest -q -p no:cacheprovider tests/test_r6fix_geom3.py tests/test_e5b_polyhedron_cache.py tests/test_geom3_e5a.py --basetemp=reports/codex/R6FIX_evidence/tmp/geom3_final --durations=3
python -X utf8 reports/codex/R6FIX_evidence/geom3/run_mutations.py
```

源码/测试已交主代理 freeze；全套、指针修复、README/canon/设计同步和最终 R6FIX 状态由主报告统一给出。没有把本分项定向全绿冒充独立 G6 退出审查。
