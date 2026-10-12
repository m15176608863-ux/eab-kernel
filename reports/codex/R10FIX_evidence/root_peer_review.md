# R10FIX 父改动独立快速复核（J03/J05）

## 范围与结论

只读检查本树 `src/eab/kernel2d/covers.py` 的 `in_cone` 改动、`src/eab/limit.py`/`limit_multi.py` 的不确定度数据流及 `tests/test_r10_cone_contract.py`/`test_r10_resolution.py`。阅读当前源码和 `git diff`，未修改这些文件。

**在以下阅读和实际探针范围内，未确认需要返修的缺陷。** 本文不是 G6 六路独立复审，不构成 M0 退出认证，也不声称穷尽任意输入。

## J03：微反射法锥

- 新 `cross(lo,hi)>0` 严格门保证微反射输入不可能返回严格内部 1；`_cone_nonreflex` 拒绝超过显式角窗或反向边界射线。
- 对允许的微反射，两侧点积均非正的反方向必被 `_bisector_positive` 拒绝；窗口只能在同向区域产生 0，不再把反向薄扇区视为 strict。
- 非零、非反射凸锥沿用原严格叉积条件；零边界射线新增明确 `ValueError`，而不是用无定义的锥继续分类。
- 实测原始有理射线 `lo=(s,0), hi=(s,-s*h)`：`h∈{1/100,2^-100,1/2}`、`s∈{1e-9,1,1e8}`、全部 `[-4,4]^2` 非零整数方向，合计 **720 格**。逐格断言反射锥不得 strict，双侧点积非正必须 exterior；全部通过。
- 测试文件另外覆盖原复审三位姿、零角窗、微反射同向窗口、普通凸锥边界、退化同向/反向射线、2D 局部单盖及 3D 反射棱/顶点合同。3D 源码不在本次快审逐行范围，仅跑了新增合同门。

## J05：精确见证到显示的边界

- 单体 `_resolvable`、无界 `rmin` 及多体 `_ys` 均通过 `_lp_values` 读取原精确 LP 见证；`exact_y` 不再先被转成 `inf` 后参与 `inf*0`。
- `_wrench_rounding` 只构造尺度在 `[1,sqrt(n)]` 的无量纲范数，噪声预算的量纲缩放留在 Fraction；次正规活荷载对应的更小噪声预算不先显示成零。
- `_live_uncertainty` 在有理层完成分子、分母、比值，最后才 `_fl`；真正无效的数值输入返回 NaN，所有调用方显式将非有限 U 标 `unresolved`。
- 单体/多体邻域荷载扰动保持有理数；两个邻域最优值使用 `exact_x`，差值和相对比完整计算后才显示。最终 overflow 成 inf 时比较不能认证 resolved；原问题 status/alpha 不被邻域状态替换。
- 独立静力探针：两个地面接触、μ=1/2，恒载 `(0,-1,0)`，活载 `((1/2+ε)s,-s,0)`，`s=2^-1074, ε=2^-40`。力平衡直接给 `α=(1/2)/(s ε)`；每次扰动后的活载 `(lx,ly,0)` 给 `α=(1/2)/(lx+ly/2)`。截获真实三次求解的 exact 模型，逐个用此解析式核验，不以 LP 自己结果作 oracle。
- 单体和单动体包装的多体均调用 3 次求解，三次 α 的浮点显示**全部是 inf**，精确值仍成立；完整比值均为 `0.0008297438213806996`，与有理解析差比一致，均报告 `unresolved`。没有 `inf-inf`/NaN 污染。

## 实测日志

- [额外方向/超范围邻域探针](file:///D:/eab-wt/cx-e2/reports/codex/R10FIX_evidence/root_peer_probes.log)：720 格与两条三次求解探针 PASS。
- [父改动新增门复跑](file:///D:/eab-wt/cx-e2/reports/codex/R10FIX_evidence/root_peer_tests.log)：`48 passed in 0.14s`。

命令：

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -X utf8 -m pytest -q tests/test_r10_resolution.py tests/test_r10_cone_contract.py --basetemp=reports/codex/R10FIX_evidence/tmp/j02_peer
```

## 合同边界与建议

- U 始终是沿所选机构的输入舍入一阶**估计**，不是所有对偶最优面的上界，不保证真实工程稳定性。无界且最小可行 α=0 的既有筛查边界未改变，模块文档明确承认它。
- 法锥方向格是有限有理样本；结合源码 guards 说明本次微反射 bug 的必要封堵，不等于任意 Python 数值类型/无效 NaN 参数均认证。
- 半径/形心构造、更高层建模和 LP 全部证明并未在本快审重新穷尽；不能用这次“未确认缺陷”替代下一轮只读新鲜树 G6。
