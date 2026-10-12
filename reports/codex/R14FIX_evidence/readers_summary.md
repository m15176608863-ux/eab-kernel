# R14FIX / N03 与同类读取边界修复

## 范围与结论

本读取器子任务的源码修改限于本工作树 `contact_record.py`、`readers/bdda3d.py`、新 `readers/numeric_decode.py`、`adapters/bdda2d.py`；新增 `tests/test_r14_readers.py`。首轮全套后按真实双守卫路径迁移一项旧内部变异，原数值断言与参数网格不动；未删旧测试。未操作任何姊妹树、fixtures、git 状态写操作。静态政策审阅另见 `static_summary.md`。

### N03：真实 JSON 字面量与直接精确数

- 根因：`json.loads` 默认 `parse_float=float` 已把 `1e-400` 变成零，把 `1e400` 变成无穷；后面的 `scalar_rational` 再检查无法恢复丢失的原文。`ContactRecord._decode` 五类向量又存在裸 `float`；五类标量未解码检查。
- 修前：`readers_before.log` 最后一行为 `90 failed, 17 passed in 0.50s`。明确断言为 `with pytest.raises(ConstructionDomainError)`；真实 JSON/直接 Fraction 的 `DID NOT RAISE` 是目标红，直接巨大 Fraction 的裸 `OverflowError` 也不满足具名边界契约。最初因 basetemp 父目录缺失的环境错误已修正并重跑；此日志无 setup error。
- 修法：JSON 小数字面量先 `Fraction` 精确解析并校验有限非零 RN 输出范围，继续保留 Fraction 到字段分派，而非先转 float 后猜字段；这样 `18014398509481985.0` 用作整数身份亦不丢最低位。五类向量、五类标量最终使用具名 `scalar_rational`；JSON NaN/Infinity 非标准 token 明确拒收。
- bdda3d 实际文件加载、直接 dict、参考点/面积/插值参数/转移量与数值 extra 同样检查；extra 的原字符串证据和整数不改成浮点。
- 修后：包含下述同类与变异门的最终相关回归为 `447 passed in 6.79s`（`readers_regression.log`）。包含原 `test_contact_record`、`test_readers_roundtrip`、`test_tf_reader`、M4a adapter/VV、R13FIXb domain 全部指定文件。

### 同类 A：离散身份早截断

`int(Fraction)` 会静默截断（小于 1 可变零）。对 ContactRecord 身份字段、Feature 块号/索引/顶点号、bdda3d 块号/引用号/状态码/step/index、Bdda2DWindow.step 均要求精确分母为 1；任意大整数保留无 binary64 量级界。原 `Feature` 入口三例修前红纳入上述 90 failed。新增 JSON decimal 整数精确保持和各字段分母检查门。

末轮交叉核查另发现：Feature 中的 refs 已精确保留，`extra.refs` 却仍从原始 Fraction 复制并按连续数处理，导致大整数证据失真或溢出。真实 JSON 大整数及直接 `Fraction(2**2000+1)` 两格修前为 `2 failed, 158 deselected in 0.10s`（`readers_refs_before.log`）。现 `extra.refs` 复用已检查整数列表，保证身份与冻结证据一致；去掉该步骤的内部变异命中 `reference evidence must preserve exact integer identity`。

### 同类 B：M4a 窗口构造器过早进入 math.isfinite

`Bdda2DWindow.__post_init__` 对 Fraction `2^-2000` 静默接受，对巨大 Fraction 给未命名原生 OverflowError；原构造器未保证入口可表达性。新增八例修前 `8 failed, 112 deselected in 0.12s`（`readers_adapter_before.log`）。现先精确检查非负/角范围，再具名检查最终可表达性；距离窗口保留原 exact 值供精确几何比较，不人为早舍入。既有非有限 float/负数的 ValueError 契约不变。M4a 原网格未改并绿。

### 同类 C：signed-zero 往返保真

本轮精确解码路径曾把已有 binary64 负零规范化成正零，破坏原读取器往返契约。原 float 与真实 JSON `-0.0` 的连续字段门修前为 `22 failed, 135 deselected in 0.17s`（`readers_zero_before.log`）。现读取器专属 `scalar` 保留已有 float 零的符号，JSON 小数 token 保留负零；整数 token `-0` 仍保持标准 JSON 的既有整数语义。未改变全局有理构造的零语义；撤销专属保真步骤后，断言 `reader must preserve signed binary64 zero` 再次报红。

## 分项支持范围

1. **读取器连续数值**（坐标、法向分量、长度/面积、力、位移/滑移、插值参数及数值 extra）：零，或精确输入 `q` 满足 `2^-1075 < |q| < 2^1024 - 2^970`。这是 binary64 round-to-nearest-ties-to-even 非零且有限的精确开区间，不是“无损表示所有十进制小数”的声称；0.1 正确单次舍入可接受。零胞边界/溢出胞边界均拒绝，域内次正规数、D400 外的 1e±200 仍接受。
2. **整数身份/计数**：普通 JSON 整数 token 与直接精确整数保留任意精度；有限非整数拒绝而不截断。JSON decimal token 先经过第 1 项词法 RN 域检查，再按字段精确保留整数身份，不能把该路径说成支持任意大 decimal token。领域自身负号语义仍由原验证处理。
3. **适配器几何窗口** `d0/seg_tol/fit_tol`：非负，加上述 RN 可表达范围检查；原 exact 输入仍供几何比较。
4. **适配器角度** `h1_degrees`：0 或 `[2^-400, 90)` 度；先查 exact 界，再在小角域按已声明的 binary64/libm 系数模型生成 `sin(radians(h1))`。这不是对任意实数角/一般 libm 的精确认证。已有角度独立有理级数门未改。
5. **纯文本运输**：`read_df18_csv` 返回原始字符串，不构造数；仅在 `load_records` 真正构造数值字段时检查。tf 余项字符串同理，不因静态看见一段文本而擅改冻结证据。

读取域不缩成旧 D400 工程构造域；纯精确代数/predicate 的任意有限 int/Fraction 域也未修改。

## 变异证据

六个变异均改真实被测函数的可执行语句，在内存编译后替换被测路径；不是对产物加假数据。`readers_mutations.py` 可重跑，`readers_mutations.json` 保存目标断言及源码 SHA256 前后相同。

| 变异 | 目标红断言 |
|---|---|
| JSON `parse_float=_decimal` 改回 `float` | `test_real_bdda3d_json_literal_is_checked_before_decoding[1e-400-area]`：`DID NOT RAISE ConstructionDomainError` |
| `_decode` 向量 `scalar_rational` 改回 `float` | `test_contact_dict_rational_rejects_nonzero_zero_or_infinity[value0-normal]`：同上 |
| integer 去掉分母必须 1 | `test_fractional_feature_identifiers_are_rejected_not_truncated[value1]`：同上 |
| 窗口 checked scalar 改裸 float | `test_adapter_window_checks_exact_inputs_before_libm_or_float[value0-d0]`：`DID NOT RAISE` |
| 专属 scalar 去掉保留原 float 零的步骤 | `test_reader_preserves_signed_float_zero_through_json_roundtrip[dict-normal]`：`reader must preserve signed binary64 zero` |
| `extra.refs` 改回复制原数值再连续化 | `test_bdda3d_reference_evidence_keeps_checked_integer_identity[json]`：`reference evidence must preserve exact integer identity` |

## 全目录同类扫描

- `contact_record.py`：已覆盖全部十个连续字段、离散字段、Feature、嵌套 extra、JSON 非标准常量。
- `readers/bdda3d.py`：实际 JSON 入口与直接 dict 全部已检查；正常冻结夹具往返通过。
- `readers/bdda_df.py`：现有 `_read_csv` 对数值列先 checked exact；`read_df18_csv` 原文本运输不转换；`load_records` 所构造 df18 量已有具名检查。后续裸 `float` 位于已检查同一字符串/既成浮点下游，不是新增绕过。未为改变形式重写这些门。
- `readers/bdda_geom.py`：坐标 CSV 使用 checked scalar，身份原 `int(str)` 对非整数字符串本来响亮拒绝；exact 几何/alias 规则不改。
- `readers/tf_probe.py`：所构造 time/gap/area/force/points/normals/shear 全部经 `_rows` 先检查；其他 probe 列仍为字符串证据，不冒充计算输出。
- `adapters/bdda2d.py`：CSV 连续值已 checked；补齐直接构造器与角度入口；未动盖枚举、物理语义、候选窗与特征映射。

## 台账与重跑

### 首轮全套后的兼容性返修

首轮全套保留的 `reader_full_followup_before.log`（原 `full_suite_final/shard_2.log`）记录三条读取器旧门失败：两条域外角输入虽被新增构造器正确拒绝，但异常量名变成 `window.h1_degrees`，不符合既有 `cone_tol.h1_degrees` 合同；原内部变异只去掉 property 守卫，新增构造器仍拦住该输入，因而失去牙齿。

生产仅恢复构造器域检查的既有量名 `bdda2d.cone_tol.h1_degrees`，不改范围。`test_r13fixb_readers_oracles.py::_mutate` 支持两条有明确唯一匹配断言的源码替换；原 `test_cone_coefficient_domain_guard_has_teeth` 在原 `2^-1074` 输入上移除构造时与使用时两个真实角域守卫，其余可表达性检查不移除。两条域外实际门、三个独立 Taylor 级数格及原误差断言全部保持。

- 相关完整组（全部 R13FIXb reader oracle、M4 adapter/shadow/VV、原 reader、R14 reader 和 R13 域）：`549 passed in 15.49s`，见 `readers_full_followup_green.log`。
- 独立重放变异：`readers_full_followup_mutation.py` / `.log` / `.json`；原拒绝断言精确报 `DID NOT RAISE ConstructionDomainError`，源码 SHA 前后相同。

旧测试改写：**1 个文件，仅内部变异注入位置与辅助替换器**；删测试/缩网格/skip/xfail：**0**。本节仅声明上述相关回归，不冒充全仓或新的独立 G6 退出结论。全仓结果由主报告归并。

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -X utf8 -m pytest -q -p no:cacheprovider tests/test_r14_readers.py tests/test_contact_record.py tests/test_readers_roundtrip.py tests/test_tf_reader.py tests/test_m4_bdda_adapter.py tests/test_m4_bdda_vv_reader.py tests/test_r13fixb_domain.py --basetemp=reports/codex/R14FIX_evidence/tmp/readers_rerun
python -X utf8 reports/codex/R14FIX_evidence/readers_mutations.py
```
