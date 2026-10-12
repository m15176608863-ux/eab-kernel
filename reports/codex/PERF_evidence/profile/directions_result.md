# 二维 VE 方向判定：整数化结果

## 热点依据与范围

root 的 `bb52_small.pstats/txt` 对 `tools.bb52_g0.analyze(samples_per_pair=3, seed=0)` 插桩显示：总 2.003 s，`_ve_side_directions` 30151 次、累计 0.669 s；上层 `_ve_side` 累计 1.091 s。首轮全套中 BB52 文件约 75.5 s。

实际变更限于 `src/eab/kernel2d/covers.py` 的 `_ve_side_directions` 与 `lcm` 导入；原有 `lru_cache(maxsize=32768)` 的五参数键、容量和入口均不变。新增 `tests/test_perf_2d_directions.py` 28 个节点，不改旧断言。

## 等价性

三个向量 `lo/hi/e` 的六个有理坐标使用**同一个正分母 D**清分母，不能各自规范化：长度窗口依赖三向量中的最短边长，各自缩放会改变口径。直接使用整数叉积/点积，而不是把整数重新送入浮点过滤器。

- 精确严格分支中的叉积/点积都乘 D²，符号与零不变。
- 角窗口 `cone_tol` 无量纲，保持原值。
- 当 `cone_tol is None`，长度窗口用 `Fraction(tol) * D` 精确缩放。最短平方长度也乘 D²，因此归一化窗口完全相同。
- `_cone_nonreflex/_cone_accepts/_bisector_positive` 的比较两侧分别同阶乘正因子，所有 -1/0/1 状态不变。
- 不用 `tol * D` 的浮点乘法；次正规浮点窗口配 D=2^1074 的门专门验证不会先溢出或舍入。

没有新增浮点过滤器、误差界或缓存，相关新增过滤/缓存突变义务不适用。

## 对拍与内部突变

测试内冻结旧有理表达式，但自行定义 Fraction 点积、叉积、窗口、锥和角平分线公式，不调用被测几何原语。随机、共线/反向、边界、近反射、悬殊边长；原点、1e6 工程坐标的实际圆整输入、1e-8/1e3 单位变化、次正规均逐完整状态对拍。

独立 3-4-5 射线给出精确 `sin=3/5`，验证长度窗、角窗的边界与两侧；不等长向量的门验证最短长度未被各自归一化吞掉。

|内部变异|检测门|确切失败断言|
|---|---|---|
|删除 `Fraction(tol) * D` 中的 D|`test_integer_ve_length_rescaling_mutation_has_teeth`|`length window retains exact scale and boundary`，s=1/7 的闭边界错误地被拒绝|
|strict 的 `c1>0 and c2>0` 变为 `>=0`|`test_integer_ve_strict_boundary_mutation_has_teeth`|`exact boundary cannot become strict`，锥边界不能标为严格内部|

## 验证结果

初始针对性：`224 passed in 0.64s`，`directions_gates.xml`。

扩大回归最后一行原样：

```text
1664 passed in 134.18s (0:02:14)
```

原始 JUnit：`directions_gates_final.xml`。命令：

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -X utf8 -m pytest -q -p no:cacheprovider tests/test_perf_2d_directions.py tests/test_kernel2d_covers_e3.py tests/test_kernel2d_report_band.py tests/test_kernel2d_g0.py tests/test_kernel2d_exact.py tests/test_kernel2d_entrance.py tests/test_kernel2d_entrance_e3.py tests/test_kernel2d_review.py tests/test_kernel2d_predicates.py tests/test_invariance_2d.py tests/test_bb52_g1.py --basetemp reports/codex/PERF_evidence/tmp/directions_final --junitxml=reports/codex/PERF_evidence/profile/directions_gates_final.xml
```

## 微基准

`benchmark_2d_directions.py` 载入 c194dbb 原文件字节快照。3840 个完全相同输入的 7 轮交错中位（直接 `__wrapped__`，绕过缓存）及实际 BB52 路径 3 轮交错中位（每次清 direction 缓存）：

|路径|旧秒|新秒|倍数|
|---|---:|---:|---:|
|完整 `_ve_side_directions`，3840 输入|0.026464899987|0.016967000003|1.55978664×|
|BB52 analyze(samples_per_pair=3, seed=0)|0.589180700001|0.540044900001|1.09098466×|

BB52 完整报告对象逐值相等；对拍状态集合为 `[-1,0,1]`。逐轮测量与源哈希见 `directions_benchmark.json`。收益不巨大，但在实际端到端路径仍为正，因此保留；不以微基准倍数外推整套时长。

生产/测试已冻结，所有该 agent 后台验证进程均已结束。全套最终计时仍由 root 独占完成。
