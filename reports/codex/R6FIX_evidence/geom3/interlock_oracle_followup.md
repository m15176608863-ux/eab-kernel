# 首轮全套 4 个互锁候选门失败：根因与返修

## 根因不是生产删掉真实 EE，而是 oracle 输入位形未同步

G6F-09 要求 nominal 平移不能先把有效微体舍成零长棱，因此生产 nominal 报告已经改为对原始 scalar 先 `Fraction` 再相加。`tests/e5a_escape_oracle.py::move` 仍是 `p[k] + offset[k]`，会先以 float 舍入，形成**另一套**源棱/面法向。

先做隔离实验，不改任何生产函数或 oracle 几何原语：仅临时切换 oracle 的输入平移，结果见 [interlock_oracle_probe.log](interlock_oracle_probe.log)，可重跑 [interlock_oracle_probe.py](interlock_oracle_probe.py)。

| 原失败格 `(t,s)` | 首个失败 offset | 旧 oracle 多出的 EE | 旧/精确平移不等顶点数 | 仅修 oracle 平移后候选对称差 |
|---|---|---|---:|---|
| `(0, .001)` | `(-.41,-.12,0)` | `(15,21)/(6,8)` | 20 | 空 |
| `(0, 1)` | `(.4,0,0)` | `(21,27)/(30,32)`、`(21,27)/(32,34)` | 18 | 空 |
| `(0, 1000)` | `(.23,.07,0)` | `(27,33)/(32,34)` | 32 | 空 |
| `(1000, 1000)` | `(-.41,-.12,0)` | `(15,21)/(6,8)` | 18 | 空 |

四格旋转均为 z0.7。旧 oracle 没有生产缺失之外的反向差；精确输入后每一格是**完整候选集合**相等，不是只删指定 EE。

## 最小修复与独立性

只改 oracle `move` 为 `F(p[k]) + F(offset[k])` 并更新注释。完整 source-feature 枚举、循环 Newell、Gram cone/最近线参数、extent 与 reporting windows 原样保留。

没有调用生产 `translate_exact`、cover、候选、normal 或成员谓词。oracle 及其 `e5a_cover_oracle` 的静态导入列表见 [interlock_oracle_imports.log](interlock_oracle_imports.log)，只有标准库和独立测试 oracle。

## 红/牙与测试改写台账

- 新增 `test_independent_escape_oracle_translation_preserves_exact_affine_data`：`2^-40` 点加 float `1e8`，期望有理 `109951162777600000001/1099511627776`。修前实际 `100000000.0`，`oracle-exact-affine-input` 报红，见 [interlock_oracle_before_red.log](interlock_oracle_before_red.log)（`1 failed, 575 deselected in 0.22s`）。
- 新增内部变异：重新把 oracle `move` 换成旧 float 加法，同一 `oracle-exact-affine-input` 断言报红。
- 既有 `test_independent_escape_candidate_gate_catches_a_dropped_exact_edge_cover` 不动：仍在真实 `ee_cover` 内删一个指定 label，确认独立完整 oracle 正确捕获缺失。
- **原 `test_escape_tied_set_is_invariant_up_to_the_declared_resolution` 的 18 参数格 × 4 offset、所有集合相等、候选高度、tied labels、基准格与附加标签分辨率断言均未修改。** 没有缩网格、放大容差、skip 或 xfail。
- 修改文件仅 `tests/e5a_escape_oracle.py` 与 `tests/test_invariance_interlock.py`；无生产源码返修。

## 验证

1. 整组原 18 格 + 原删盖牙 + 新 2 门：
   `21 passed, 555 deselected in 120.42s (0:02:00)`，见 [interlock_oracle_after_green.log](interlock_oracle_after_green.log)。该进程在主代理最后一次 covers gap 构造升级前启动。
2. 其余引用此 oracle 的等价性与敏感性门：
   `49 passed in 48.42s`，见 [interlock_oracle_dependents.log](interlock_oracle_dependents.log)。
3. 主代理最后一次 covers gap 构造升级后的 4 个原失败格 + 3 道独立 oracle 门另行复跑：`7 passed in 49.02s`，见 [interlock_latest_green.log](interlock_latest_green.log)；最终全套由主报告给出。

命令（所有命令均 `PYTHONDONTWRITEBYTECODE=1`，本树 basetemp，无 pytest cache）：

```powershell
python -X utf8 -m pytest -q -p no:cacheprovider tests/test_invariance_interlock.py -k 'tied_set_is_invariant or independent_escape' --basetemp=reports/codex/R6FIX_evidence/tmp/geom3_interlock_oracle_green --durations=5
python -X utf8 -m pytest -q -p no:cacheprovider tests/test_perf_oracle_algebra.py tests/test_interlock_sensitivity.py --basetemp=reports/codex/R6FIX_evidence/tmp/geom3_interlock_oracle_dependents
```
