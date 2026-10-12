# covers 精确最终 gap 构造后的 G2 oracle 同步

## 确认问题与修复

主代理修复 covers 的同类构造问题后，定向 broad 运行报告 6 个 G2 元门失败（原始日志 `../construction/cover_broad.log`）。例如 `cb2_locked-s1000_t0` 的 `VE3(vertex 3, edge 1–3)`，生产由精确平方距最后开方得到 `gap=1000`，旧 oracle 先把各分量转 float、再平方相加得到略大于 1000 的值，故错误地把它排除在 `band=1000` 之外。

`tests/e5a_g2_oracle.py::construction` 的原分支是：

- VE3/VV3：`sqrt(sum(float(component)**2))`，会平方中间量下溢/溢出。
- VF/EE：先 float 单位法向和 difference，再点乘，斜面小 gap 会被大分量抵消。

现在该独立 oracle 保留原先的全三元组支持面、Newell、Gram、Gordan、标签和 extent 全部公式；统一先计算有理 `dot(n,difference)**2 / dot(n,n)`，最后通过**测试内部独立 Decimal 平方根**转成 binary64，符号由有理分子读取。Decimal 精度随分子/分母 bit-length 增加，并预留 binary64 subnormal 的界限位数；没有导入生产 `construction.sqrt_rational` 或其他生产几何原语。

## 红 → 绿与牙

新增 [test_r6fix_g2_oracle.py](../../../../tests/test_r6fix_g2_oracle.py)：

1. `2^-600` 尺度 VV3，真 gap=`3*2^-600` 可表达，旧 oracle 报 0。
2. `2^600` 尺度 VV3，真 gap=`3*2^600` 可表达，旧 oracle 报 inf。
3. 3–4–5 有理旋转面，沿面坐标 `1e8`，真法向 gap=`2^-100`；旧 oracle 报 0。

先红原样：`3 failed in 0.12s`，见 [g2_oracle_before_red.log](g2_oracle_before_red.log)。

新增变异把测试内部最终开方器回退 `math.sqrt(float(squared))`，确认 `g2-oracle-final-distance-rounding` 看护断言报红；没有向最终记录中追加假差异。

完整 G2 文件和新增 4 门：`129 passed in 6.46s`，见 [g2_oracle_after_green.log](g2_oracle_after_green.log)。

## 测试改写台账

- **未修改 `tests/test_g2_bdda3d.py`。** 原 27 参数格、每格所有字段、集合、band/penetration、legacy 差异清单、原内部删盖牙全部保留。
- 修改的只是独立 oracle 构造量定义，与 production 已修正的“精确数据最后舍入”公开契约相符；不是按 actual 输出反推 expected。
- 不放宽 tol，不缩窗口/网格，不增 skip/xfail。
- 本次仅修改 `tests/e5a_g2_oracle.py`，新增 `tests/test_r6fix_g2_oracle.py`；生产 G2 未动。

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -X utf8 -m pytest -q -p no:cacheprovider tests/test_g2_bdda3d.py tests/test_r6fix_g2_oracle.py --basetemp=reports/codex/R6FIX_evidence/tmp/g2_oracle_green --durations=5
```

源码/测试再次冻结；最终全套由主报告统一记录。
