# 第二轮棱 frame 整数化：已应用与验证

## 变更

- 生产：`src/eab/kernel3d/covers3.py` 新增 `_integer_ray`；只调整 `_qedge_contains` 与原有 `_qedge_frame_cached` 的载荷。
- 新门：`tests/test_perf_edge_frame.py`，52 个节点；未修改任何既有测试或断言。
- **无新浮点过滤、无新缓存、无缓存签名更改**。原五参数缓存仍以 t/n1/n2 精确内容、cross/dot 实现身份为键，容量仍 8192。仅载荷增加正比例整数化后的 t，替换两个 h 向量的表示。

## 等价依据

每个非零向量 `v` 被换成 `alpha*v`，其中 `alpha=D/g>0`；D 是该向量所有分母的 lcm，g 是整数坐标的非负 gcd。零向量保持零。正负号、零谓词、strict 结果不变。

对于显式角窗口，`dot(a,b)^2 > tol² dot(a,a) dot(b,b)` 的左右两侧同乘 `alpha² beta²`，因此严格与闭边界判断相同。`tol<=0` 分支同样只读原符号，完整返回状态 -1/0/1 保持，不只是接受/拒绝相同。

## 验证

1. 首次针对性运行：**149 passed in 1.90s**，`gates.xml`。
2. 扩展 G2 与第一轮整数单纯形相关门：**316 passed in 7.97s**，`gates_final.xml`。命令：

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -X utf8 -m pytest -q -p no:cacheprovider tests/test_perf_covers.py tests/test_perf_edge_frame.py tests/test_g2_bdda3d.py tests/test_covers3_e5a.py tests/test_e5a2_integer_arithmetic.py tests/test_e5b_polyhedron_cache.py --basetemp reports/codex/PERF_evidence/tmp/edge_round2_final --junitxml=reports/codex/PERF_evidence/edge_draft/gates_final.xml
```

独立 oracle 不使用生产几何原语：测试内自行遍历面环、构造 Fraction Newell 法向并算点/叉积。覆盖随机方向、精确与圆整几何、凹折、平缝、开边、反向面环、零向量/零棱、原位几何变化、工程坐标 1e6、单位尺度 1e-8/1e3 与次正规；每个输入包含负、零、正窗口。

## 内部突变

|内部变异|检测门|失败的专用断言|
|---|---|---|
|查询方向逐分量取绝对值，丢失朝向|`test_integer_edge_direction_sign_mutation_has_teeth`|`analytic edge direction/window state`：立方体棱的负 x 方向不应落入正 x/z 法锥|
|整数化遗漏每个分量分母，变成各向异性缩放|`test_integer_edge_anisotropic_rescaling_mutation_has_teeth`|`analytic edge direction/window state`：-1/100 的薄侧向分量在 1/50 窗口内，错误变成 -1 后应被抓住|

旧 `test_cache_vertex_signature_mutation_is_caught` 保留并通过；没有改动其硬钉源码针。

## 微基准

`benchmark_after_unfreeze.py` 载入 c194dbb 字节快照旧实现，并在完全相同的 1152 个输入上与当前实现及独立 oracle 逐状态对拍。原有 frame/norm 缓存均已暖，7 轮交错执行，取中位数：

|旧秒|新秒|倍数|
|---:|---:|---:|
|0.008915899991|0.007018199991|1.27039697×|

全状态集合确为 `[-1,0,1]`。逐轮数值、源哈希见 `edge_benchmark.json`。这是局部微基准，不保证全套同比加速；全套仍需 root 最终独占计时。

本 agent 的生产/测试修改已冻结，后续仅写报告证据。
