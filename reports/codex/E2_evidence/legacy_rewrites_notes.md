# E2 旧测试口径改写记录

## 范围与复验

只修改 `tests/test_kernel2d_review.py`、`tests/test_kernel2d_g0.py`、`tests/test_invariance_2d.py` 的凸 E2 路径门。局部盖、legacy 显式容差窗、`geom` 容差 API 的门不变。

命令先设置 `PYTHONDONTWRITEBYTECODE=1`，再运行：

```powershell
python -X utf8 -m pytest -q -p no:cacheprovider tests/test_kernel2d_review.py tests/test_kernel2d_g0.py tests/test_invariance_2d.py --basetemp=reports/codex/E2_evidence/tmp/legacy_rewrites_final
```

原样最后一行：

```text
1007 passed in 32.89s
```

日志 `legacy_rewrites_test_final.log` 已包含 G0 真 Fraction 边界和浮点探针两组；增强前结果为 `1007 passed in 31.69s`，留在 `legacy_rewrites_test.log`。本轮没有跳过，后续汇总以主报告为准。

## 原失败 17 格逐条处置

| 原测试 | 失败格 | 旧口径 | 新口径与强度 |
|---|---:|---|---|
| `test_r7_third_vote_hull_vertices_match_and_catch_sign_flip` | 1 | 法向反号应让 G0 失败 | E2 判定与构造解耦。随机三票保留；各 facet 的 gap 对测试内联边法向公式，反号缺陷仍由构造量断言识别。另在实际 membership 函数体内把边界吞成内部，必须恰有 16 个 `brute=0, cover=1` 失配，而非无关断言或异常。 |
| `test_hull_defect_threshold_is_pinned_on_an_edge_away_from_the_start` | 2 | 深 2tol 拒收、0.5tol 接受，后者允许最多 200 个带内失配 | 两种非零微凹在 0/tol/100tol 下都拒收；每种原 2000 个随机平移加 3 个边界邻点由凹 fallback 回答，对独立 Fraction 闭式 `sign(1+x_y)` 逐点零错，三态均出现。 |
| `test_convex_g0_is_invariant` | 14 | 理想平行边经浮点运动仍强迫原 FF 标签与计数 | 每格全部标签等于独立 Fraction 支撑投影 oracle；每个成员答案等于独立精确 SAT。余量超过舍入预算时仍守刚体不变。边界可因数据舍入改变，但不豁免 oracle。G0 零跳样、零顶点豁免、全边界探针。 |

这些失败均属 (a) 旧容差语义，不以放松核心断言处理。

不变性 14 格：`squares` 的 `rot_s0.001_t0`、`rot_s1_t0`、`rot_s1_t1000`、`rot_s1_t100000`、`rot_s1000_t0`、`rot_s1000_t1000`；`brick_square` 的 `rot_s0.001_t0`、`rot_s0.001_t1000`、`rot_s0.001_t100000`、`rot_s1_t0`、`rot_s1_t1000`、`rot_s1_t100000`、`rot_s1000_t0`、`rot_s1000_t1000`。

## 原绿门的强化

- `test_degenerate_parallel_edges_membership_still_exact`：取消任一票为 0 就跳过；原 500 点加 8 个边界点对精确 SAT 全核，三态均出现。
- 原微倾 ambiguous 门改名 `test_vote_three_keeps_exact_kinks_without_ambiguous_exemptions`：保留 24 格。独立 Fraction 凸包证实每格 5 个严格顶点；原 `ambiguous<=2` 收紧为零豁免、零失配，要求 20 个边界探针、420 总样本与两条严格非 FF facet。

## 独立性

- 新标签 oracle 用测试内联 Fraction 投影，不调库角排序、法锥、凸包。
- 微凹 fallback 用专门几何闭式，不拿 `polygons_overlap_exact` 与它自身对账。
- r7 突变位于真实函数源码内部，仅在测试进程 monkeypatch，未修改磁盘被测文件。
- 本子任务不代表全套最终结果或 G6 退出。
