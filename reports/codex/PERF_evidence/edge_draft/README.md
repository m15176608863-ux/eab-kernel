# 第二轮棱 frame 整数化草案（未应用、未执行）

当前冻结期间仅写此目录；没有修改 `src/`、`tests/`、`tools/`，没有运行测试或基准。

## 方案

`edge_functions.py` 提供新增 `_integer_ray` 及两个待替换函数。原 `_qedge_frame_cached` 的五项参数、`maxsize=8192`、几何内容与实现身份签名保持原样，仅缓存载荷从 `(convex,h1,h2)` 改为 `(convex,t_integer,h1_integer,h2_integer)`；唯一调用者同步解包。没有新缓存、浮点过滤或误差界。

对于每个有理向量，取分母正最小公倍数 `D` 和整数分量的非负公因子 `g`，输出 `(D/g)*v`。非零向量的比例严格为正，零向量保持零。因此：

- 叉积/点积推导的正、负、零，以及 strict 条件不变；不会将反方向并为同一条无向轴。
- 窗口判据 `dot(a,b)^2 > tol^2*dot(a,a)*dot(b,b)` 两侧同时乘相同正因子平方，负、零、正 `tol` 的完整状态不变。
- `_outside_dot_band` 现有交叉乘分子分母表达式可直接读取 int 的 `.numerator/.denominator`，不需要弱化判据或改旧门。
- 点积和范数转为纯整数，避免每次创建/约分 Fraction；方向转换每次只处理三个分量。实际收益尚未测量，不作速度保证。

## 新门草案

`test_perf_edge_frame.py`：48 个参数格 + 4 个命题/变异门，共预计 52 格。

- axis/skew/folded/flat_seam/open/reversed，精确与实际圆整输入，原点/1e6工程坐标/大小单位/次正规；每格随机方向、零向量、面法向、双法向和带微小轴向分量的方向，`tol<0/=0/>0`。
- Oracle 手写有理 Newell 面环、棱遍历、点/叉积，不借用被测几何原语；比较完整 `-1/0/1`，退化零棱比较显式异常。
- 独立闭式立方体棱看护方向正负、`3/5` 窗口边界两侧、次正规轴向误差，以及全状态产品互异。
- 在同一个 Polyhedron 中改顶点和面环后复核，防止载荷被不相关几何串用。
- 内部变异一：将查询方向逐分量取绝对值；由闭式方向/窗口状态断言报红。
- 内部变异二：整数化遗漏各分量分母；由闭式薄侧向窗口状态断言报红。

## 解冻后执行

仅 root 明确解除首轮冻结后：

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -X utf8 reports/codex/PERF_evidence/edge_draft/apply_after_unfreeze.py
python -X utf8 -m pytest -q -p no:cacheprovider tests/test_perf_edge_frame.py tests/test_covers3_e5a.py tests/test_e5a2_integer_arithmetic.py tests/test_e5b_polyhedron_cache.py --basetemp reports/codex/PERF_evidence/tmp/edge_round2
python -X utf8 reports/codex/PERF_evidence/edge_draft/benchmark_after_unfreeze.py
```

安装脚本保留源文件换行，不覆盖任何已有测试，不触碰旧缓存失效门的硬钉字符串；防止重复应用。若新门或微基准不合预期，修订或放弃草案，不宣称成功。
