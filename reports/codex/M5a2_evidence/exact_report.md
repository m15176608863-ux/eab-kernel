# M5a2 精确边界子报告

## 范围与结论

本子任务覆盖 A2、A4、A6 的独立 oracle 输入类型及公共代数数闭下端点，另负责修改内核后的 450 帧回放重验证。没有改动姊妹仓库、旧冻结夹具或既有 PROVENANCE 条目。

- 新增门：`tests/test_m5a2_exact.py`，24 项；独立运行 `24 passed in 0.28s`。
- 新旧精确边界联合门最后一行：`103 passed in 5.34s`。
- 旧回放门最后一行：`49 passed in 2.76s`。
- 6 个真实内部函数体变异：control 均 exit 0，mutant 均 exit 1，红在命名的新语义断言；运行前均屏蔽 `code_hashes/file_hash`。
- 450 帧完整重验证：`M5A2_REVALIDATION_GREEN steps=450 seconds=67.69928809998964`。15 个算例各 30 步，全部 JSON 字段一致，允许的首入证书表示变化实际为 0。

以上计数与最后一行是已完成的分项运行原始证据，不是最终四分片计数，不替代主工单的全套四分片、静态门及 G6。整单最终验证只以全新 `final_suite_r3` 的完整结果为准；`final_suite_r1`（审查中断）与 `final_suite_r2`（换行保真修正）已作废，不拼接使用。这不影响名称不同的 `exact_mutations_r2` 等独立分项证据。

## A2：任意严格正残差均不认证

用单位正方形及端点映射 `x'=(1+2δ)x, y'=y` 构造精确残差。四顶点形心平移为 `(δ,0)`，拟合转动为 0，故每个顶点横向误差绝对值严格等于 δ，非浮点近似。

三个 δ 分别为 `Fraction(1,2**1074)`、`Fraction(1,10**100)`、`Fraction(1,2**52)`。测试先断言实际 `fit.delta == δ`，再断言 `UNCERTIFIED_NONRIGID_ENDPOINTS`；另直接检查 `RigidFit` 的正残差认证分支。原实现已经正确，本项只增加真正覆盖极小残差的语义门。

最小复现：`test_every_exact_positive_residual_stays_uncertified`。真实内部变异把 `self.delta == 0` 换成 `self.delta <= F(1,2**52)`；红在 `strictly positive exact residual must remain UNCERTIFIED`。

## A4：SE(2) 出口统一有理时刻

选择工单允许的“出口规范化”方案，不修改 `QuadraticTime`，也不改变一般 `RealAlgebraic` 不可 hash 的既有协议。新增 `RealAlgebraic.as_rational()`：精确认出有理根后，`se2_first_entrance` 统一返回 `QuadraticTime(rational)`。一般无理根仍保留原代数数容器。

### 有理重构的精确依据

1. 先处理已经退化为点的区间。二次式用整数 `isqrt` 核对判别式的分子与分母是否均为完全平方，不用近零阈值。
2. 一般有理系数多项式清分母并除整系数公因子，设首项系数绝对值为 B。由有理根定理，有理根分母不超过 B。
3. 对不整除首项系数的几个小素数，如果约化多项式在该有限域没有根，则原多项式没有有理根。这只是安全的提前排除；没有排除则继续精确重构。
4. 精确二分直到隔离区间宽度小于 `1/(2 B²)`。不同分母不超过 B 的有理数间隔至少 `1/B²`；真实有理根距区间中点小于 `1/(4 B²)`，因此 `limit_denominator(B)` 的最近有理数必为该根。
5. 最后同时检查候选在选定闭区间内且代回多项式精确为零。区间内只有一个根，所以不能误拿同一多项式的其他有理根。

全部推导针对给定有理数据；不调用显示值、不分解巨大整数、无固定容差。最坏分母界很大时二分可能更贵，因此保留二次式、小素数和快速候选三条精确捷径。新增 24 项门总计约 0.28 秒；全套性能由主报告记录，不把局部计时当作 5% 总性能结论。

### 最小闭式与守门

杠杆顶点 `(5,0)` 绕原点按 `u=1` 转动，水平障碍底边 `y=3`。接触方程 `10s/(1+s²)=3`，即 `(3s-1)(s-3)=0`，闭窗口内首根为 `1/3`。其他顶点严格低于障碍，接触点横坐标为 4，位于障碍边内。

`test_rational_lever_time_has_one_container_mixed_equality_hash_and_sorting` 检查：与 `QuadraticTime(1/3)` 双向相等、与 Fraction 同 hash、集合去重以及 Fraction/整数/旧容器混排。另含随机种子生成的有理旋转、`10^-9 / 1 / 10^8` 尺度与 `10^3 / 10^6` 平移的不变性门。

高次识别门使用已知因式 `(x-r)(x²+1)(x²+2)`，其中 `r=1/3` 或 `1/100000000000000000039`；无理拒绝门使用独立有理根定理可直接排除的多项式。额外反例 `(x-1)(x²-2)` 在 `[11/10,3/2]` 上选的是无理根，不得错拿区间外的有理根 1。

三个真实变异分别绕过出口规范化、绕过一般有理重构、删掉候选区间检查，均命中新语义断言。

## A6：输入合同与闭下端点

- `m5a_independent_oracle.first_contact` 在任何几何或事件计算前，断言所有顶点、半角参数、平移和参考点坐标只能是 `int/Fraction`，且拒绝 bool。删除该内部断言后，布尔半角参数被悄悄按整数使用，新入口类型门明确报 `DID NOT RAISE`。
- 公共构造器使用 `(3x-1)(x-2)` 及闭区间 `[1/3,1]`，断言根严格等于下端点 `1/3`、证书退化为 `[1/3,1/3]`、精化保持根。覆盖两个端点均为根的 `[1/3,2]` 拒绝分支。原生产逻辑已正确；将 `upper=lower` 变为 `lower=upper` 后，红在根语义而非哈希。

## 独立 oracle import 清单

新增数值期望只用 `fractions.Fraction`、整数因式分解/代入和解析杠杆公式；随机不变性只用 `random.Random`。生产 API 在测试中仅作为被测对象。

独立首入 oracle 的依赖仍为 `fractions.Fraction`、`functools.cmp_to_key/lru_cache`、独立 `eab.kernel2d.g0_oracle.overlap`；后者传递依赖 `math.lcm` 及仅含显示边界的 `eab.oracle_construction`，本路径不调用显示函数。没有导入生产 `se2/algebraic/motion/exact/global_entrance/construction` 作为数值 oracle。`inspect/textwrap/unittest.mock/pytest` 只用于变异及断言编排。

## 450 帧重验证与哈希绊线

`tools/m5a2_revalidate_replay.py` 用 4 个独立子进程运行原生产 `replay_case`，不调用会重设旧 TEMP 路径的 `run_batch`。TEMP/TMP 全程为本单 `reports/codex/M5a2_evidence/tmp/`。每个算例有 3600 秒超时；每步及每个子进程完成后落盘进度，必须全批完成且前后输入、生产代码、重验证脚本及独立 oracle 哈希不变才写最终 manifest。中断批次不能续接。

递归比较每个冻结 JSON 字段。只有 `rigid.time` 的证书表示差异可以申请豁免，而且必须由独立 oracle 的根比较精确证同；本次没有发生任何表示差异。新摘要 `fixtures/m5a2/revalidation.json` 绑定 62 个旧输入文件哈希、当前生产闭包、脚本/独立 oracle、全部 450 步完成状态和每算例 counts/stats。旧夹具字节未改。

`tests/test_m5a_replay.py` 最末源哈希门现在要求这份当前重验证摘要；不是删除源哈希断言。它逐个复核旧输入/脚本哈希、旧 expected 源闭包与当前源闭包、15×30 完成和每算例 counts/stats。

此结果只代表旧冻结前缀 450 步在新代码下完整重算，不声称重算了 1810 步全时程。

## 证据与重跑

- [精确门源码](file:///D:/eab-wt/cx-e2/tests/test_m5a2_exact.py)
- [内部变异运行器](file:///D:/eab-wt/cx-e2/tools/m5a2_exact_mutations.py)
- [最新变异摘要](file:///D:/eab-wt/cx-e2/reports/codex/M5a2_evidence/exact_mutations_r2/summary.json)
- [450 帧重验证脚本](file:///D:/eab-wt/cx-e2/tools/m5a2_revalidate_replay.py)
- [450 帧冻结重验证摘要](file:///D:/eab-wt/cx-e2/fixtures/m5a2/revalidation.json)

```powershell
$env:TEMP = "$PWD/reports/codex/M5a2_evidence/tmp"
$env:TMP = $env:TEMP
$env:PYTHONDONTWRITEBYTECODE = '1'
python -m pytest -q -p no:cacheprovider --basetemp=reports/codex/M5a2_evidence/tmp/pytest_exact_rerun tests/test_m5a2_exact.py tests/test_m5a_algebraic.py tests/test_m5a_se2.py tests/test_m5a_oracle.py
python tools/m5a2_exact_mutations.py --name exact_mutations_fresh
```

重验证脚本要求目标 manifest 不存在，防止在已有证据上静默覆盖；若需独立重验，应先由所有者明确归档旧 manifest，再用全新 run name 启动。无需修改旧 M5a 夹具。
