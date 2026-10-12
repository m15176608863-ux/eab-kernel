# R13FIXb reader / oracle / adapter 子任务

## 范围与结论

本子任务修改 6 个生产文件与 1 个新测试文件。覆盖清单见 `coverage.json`：

- 原 138 项缺口中本组 **24 项**：17 项三档差分门，7 项不产生构造量的逐项源码证明及数值保真门。
- 额外发现旧清单把 `Bdda2DWindow.cone_tol` / `metadata` 分类为无主构造，但它们包含实际 sine 构造。额外 2 项已有三档独立有理级数平台门与角度支持域门，**没有证明跨平台、全输入 libm 误差界**，不冒充完全闭环。
- `detect_step` 非零角度窗口继承显式 legacy binary64 libm 系数模型；本组的严格有理几何三档差分取 h1=0。不要把此门推成任意超越函数精度定理。
- 主三档为 `s ∈ {2^-390, 1, 2^390}`（乘数均不越工程 ±400 界）；oracle / 纯读取另验 `2^-1000` / `2^900` 等扩展档，纯字符串搬运和重复顶点判定验 `2^±1200`。

## 实现与域内真错

1. `readers/bdda_df.py`、`tf_probe.py` 原 `float(decimal text)` 可将非零下溢静默成 0、上溢成 inf。现在在真正构造位置（或同一不可变 token 被转换前）调用集中 `scalar_rational(..., quantity=...)`，保持最终正确舍入并附字段名异常。原 mutation 字符串锚保留。
2. `readers/bdda3d.py`、`bdda_geom.py`、`adapters/bdda2d.py::load_window` 最终构造亦经该检查边界。**不套 ±400 输入限制**：已能正确处理的全 binary64 可表达范围保留。
3. `read_contacts_csv` 的整数身份字段原先先 `float` 后转 `int`，`2^54+1` 在域内丢 1。现直接按整数解析；三档物理字段及大整数 ID 都有门。
4. `strip_duplicate_vertices` 原 `abs(p-q)` 在 binary64 早舍入；`1 - (-2^-53)` 误舍成 1，在 `dup_tol=1` 把不同点合并。现先 `Fraction` 精确差分；用于此**判定**的 `c·eps·C` 也保持有理数，避免为不输出构造量的 API 人为限制输入域。
5. `read_df18_csv` **仅搬运原始字符串**，不施加构造支持域检查；`load_records` 真正把其字段构造成 binary64 时才验界。raw strings / extra strings 保真。
6. `oracle_construction.py` 原有独立有理中点核验与位模式搜索不变，仅输出越界异常升级为 `ConstructionDomainError`；仍保留全可表达域。
7. `cone_tol` 对非零 `h1_degrees` 加集中 `[2^-400,2^400]` 输入检查，并保留原 `[0,90)` 角窗限制，禁止最小次正规角度在 radians 中静默变 0。低/常规/高角度档为 `2^-400, 3, 89`，独立 100 位 π + 70 项有理正弦级数在当前平台验证误差 ≤ 4 ulp；该观察不是普适 libm 定理。

## 独立性与逐值要求

测试 oracle 只用 test-owned Fraction、输入 token、binary64 相邻值构成的精确中点，以及解析解 tip/slab；不调用生产几何原语构造期望结果。

- 原 oracle 模块在本测试中是**被测对象**，参考中点证书在测试文件内独立实现。
- reader 的数值字段、坐标、特征 ID、params、转移/状态字段、30 个系数、所有 extra 数值/字符串均有独立值断言，不以非空/结构/最终通过率充数。
- 数据访问器 / 过滤器的不构造证明逐项写在 `coverage.json`，源码哈希在 `source_hashes.json`。

## 真实内部变异（均命中指定数值断言或专用异常门）

| 类别 | 内部恢复缺陷 | 红的门 / 原因 |
|---|---|---|
| 有理比值 | ratio 内先 float numerator/denominator | `midpoint certificate` |
| 根式 | sqrt 内恢复 `math.sqrt(float(value))` | 根式中点有理证书，非其他脆断言 |
| 几何读取分支 | duplicate 内恢复 raw `p-q` | `exact duplicate branch` |
| adapter 长度 | `_record` 内边差恢复 raw `q-p` | `exact adapter edge length`（混合 int/float，真值 5，变异为 4） |
| reader 域门 | `_rows` 内去掉 checked boundary | 域外 `time=1e400` 未抛专用异常，`DID NOT RAISE` |
| angular 域门 | `cone_tol` 内移除 `check_input` | `2^-1074` 静默返回 0，专用异常门 `DID NOT RAISE` |

## 验证与静态审查

定向运行：

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:TEMP='D:/eab-wt/cx-e2/reports/codex/R13FIXb_evidence/tmp'
$env:TMP=$env:TEMP
python -X utf8 -m pytest -q tests/test_r13fixb_readers_oracles.py tests/test_m4_bdda_vv_reader.py tests/test_m4_bdda_adapter.py tests/test_tf_reader.py tests/test_readers_roundtrip.py --tb=short
```

`targeted.log` 保留输出（已统一 UTF-8 编码），最后一行原样：

```text
308 passed in 6.84s
```

全套与静态最终 0 门由主代理统一执行，本组没有改静态分析器或政策。`static_review.json` 逐 scope 说明 127 条局部诊断（含失效 pin），真实近似风险仅明确落在 libm/metadata/adapter 传递处；不能用手工豁免掩盖这个 residual。

补充独立审查 root 负责的 mixed raw / face_noise 修改：`root_crosscheck.json` 的 1600 次 raw 有理逐值对拍与 120 个非对称面的独立 180 位 Decimal 根式比较均无失败；face_noise 最大观察相对误差 `1.2071e-16` 小于 `2u+u²`。这是补充抽查，不是以高精度近似替代正式有理证书。脚本保留在 `../tmp/readers_oracles_crosscheck.py`。

本组状态：原 24 项已逐项处置；额外 2 个 sine 构造 API 的跨平台全输入误差证明未闭合。
