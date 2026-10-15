# M5a 静态准入专题复核（非 G6）

## 1. 范围、作者分工与结论

本次只读复核 `tools/exact_construction_policy.json` 的 M5a 增量、
`static_admissions.json` 逐条说明，以及三个静态工具的 `scalar_algebraic` intrinsic 增量。
原委派为 112 条；执行期间作者追加两个闭式测试辅助函数的 5 条，最终复核 **117 条**。

- 政策、三个 intrinsic 增量及代数数实现作者：`/root/algebra`。
- SE(2) 实现、`square_wall` / `_closed_form_guard` 作者：`/root`。
- 本复核者：`/root/theory_audit`，同时是独立 oracle 的作者；因此其中 42 条 oracle 准入**不是作者独立复核**。
- 专题结果：**在所列静态合同内未发现 critical / major**。这不是完整 Python 数值正确性证明，不是六路独立 G6，也不替代运行时逐值门。
- 没有修改被审工具、政策或数值源码。只在本树 M5a tmp 中生成小样例和复核脚本，在证据目录生成本 Markdown 与 JSON。

机器记录：`reports/codex/M5a_evidence/static_review.json`。本次执行 1.798 秒。

## 2. 旧政策是否被改写

以只读 `git show HEAD:tools/exact_construction_policy.json` 为基线，HEAD 为
`3bf5e955d8ea669846a088f50223e17e76475947`：

1. 旧 **3103 条按原顺序逐项相等**；并非仅比较数量或 ID。
2. 旧文件截至最后一条旧准入末尾的 **3,159,888 字节原始前缀完全一致**；差异是末尾追加条目。
3. `schema`、`review_contract`、`imports`、`members` 等全部非 `waivers` 字段逐值未变。
4. 新增 117 条与 `static_admissions.json` 的 `entries` 逐值、逐序相等；五元组没有重复。
5. 当前政策 SHA-256：`3f3aa811d077fe8518eadef3d7ca489595b371cdf49dd78309fa1f2ca2dbb12b`。
   基线 SHA-256：`e5043fd0ade1be4f7474d9d22c98d05355f10c0dfa8a10ef14498395c5e642a8`。

## 3. 新准入的约束粒度与人工复核

准入匹配的五元组是 `(path, function, rule, AST dump, enclosing-source SHA-256)`，没有通配路径、通配函数或整类规则豁免。
117 条均属于本单新函数 / 新模块；没有把旧函数纳入新豁免。每条 AST 节点当前存在、源上下文哈希有效、理由非空。

| 源文件 | 条数 | 复核内容 |
|---|---:|---|
| `src/eab/construction.py` | 17 | 唯一新函数 `scalar_algebraic` 的精确比较回调、负数回调翻号、异常构造；只最终输出 binary64。不能由静态准入反推任意回调都精确。 |
| `src/eab/kernel2d/algebraic.py` | 28 | 冻结 dataclass 的字面量字段初始化、根证书构造、精确比较代理与区间细化。没有按方法名称无限放行。 |
| `src/eab/kernel2d/se2.py` | 25 | 精确输入记录、事件根、离散标签集合、步初 PD 缓存与证书返回。`_event_times(*polynomials)` 的 `closed-rounded-call` 是当前 Fraction 多项式路径的人工准入，不取消 rounded 污点。 |
| `tests/m5a_independent_oracle.py` | 42 | 私有有理 Root 方法、递归隔离、具体 `cmp_to_key(compare)`、离散集合与证书解码。没有调用被测代数 / 几何原语；作者独立性限制见 §1。 |
| `tests/test_m5a_se2.py` | 5 | 精确方墙夹具的 `SE2Motion(u)` 与被测首入调用；闭式期望方程、区间与标签在辅助函数中直接写出。 |

特别检查的边界：

- `object.__setattr__` 只准入当前节点上的字面量 `polynomial/lower/upper` 或 `u1/translation/center`；没有放开任意反射。
- 只有两个新模块级准入：`from functools import cached_property, lru_cache` 和默认值的精确 `SE2Motion()` 节点。
  它们是新 `se2.py` 内的具体 AST / 模块上下文准入，**不应表述成全部 117 条都以函数体作 pin**。
- 117 条均为 `closed-*` 诊断；没有新增 `rounded-root`、`rounded-vector`、`subtract-rounded` 豁免。
- 其中 11 条 `closed-rounded-call` 的理由针对当前 Fraction / 私有 Root / 离散集合路径，非“rounded 值可以再开方”的许可证。

## 4. 源码陈旧试验：24 个局部范围、117 条全部失效

对每个新准入局部范围，**仅在内存中的文本副本**插入函数体注释；模块范围则追加一个无害语句。
原准入 AST 保持存在，但局部源哈希改变。结果：

- **24 / 24 个范围**触发预期 `closed-stale-waiver`。
- **117 / 117 条**均被报陈旧，同时从 `approved_sites` 移除。
- 向同文件追加一个无关兄弟函数不使原范围陈旧，符合原政策的局部 pin 合同。

这是“源码变化会过期”的**局部词法范围**合同，不是传递依赖哈希。若只改被调函数、导入目标或外部输入，而当前调用者局部源码不改，当前调用者的 pin 不一定过期。
现有 `review_contract` 和静态工具 docstring 已明确该限制；本单没有把它升级宣传为依赖闭包证明。

## 5. 三个 intrinsic 增量与 rounded 来源恶意样例

对三个工具逐字归一化比较：移除新增的一个 `scalar_algebraic` 名称后，各文件与 HEAD 完全一致。
因此本单仅扩充已有构造边界名单，没有改弱 sink 集、未知调用默认拒绝、遮蔽识别或旧污点传播实现。

独立新造 10 个短源程序，均用 `scan_text` 实际走静态路径；失败来自预期语义规则，不是哈希绊线：

| 样例 | 必须出现且实际出现的诊断 |
|---|---|
| `sqrt_rational(scalar_algebraic(compare))` | `rounded-root` |
| 显示量作 `norm_rational` 分量 | `rounded-vector` |
| 显示量作 `unit_rational` 分量 | `rounded-vector` |
| `Fraction(display)` 包裹后开方 | `rounded-root` |
| 局部 callable 别名后开方 | `rounded-root` |
| `from ... import scalar_algebraic as display` 后求范数 | `rounded-vector` |
| 列表与别名取回显示量后开方 | `rounded-root` |
| 两个显示量相减 | `subtract-rounded` |
| 本地同名定义遮蔽 intrinsic | `closed-shadowed-intrinsic` |
| 同名定义内部任意回调 | `closed-unknown-call`，并有遮蔽诊断 |

全部 **10 / 10 EXPECTED_RED**。部分样例还触发 `closed-rounded-construction` / 未证调用，完整规则集合及原始源文本见 JSON。
这支持“新的显示量仍被标为 rounded”，**不支持**“静态工具可证明任意 callback、任意 Python 对象协议、跨库隐式行为正确”。

## 6. 可复核方式与剩余边界

本次脚本留在临时区（不要求入库）：`reports/codex/M5a_evidence/tmp/static_review/run_review.py`。
执行时 `PYTHONDONTWRITEBYTECODE=1`、`PYTHONIOENCODING=utf-8`、`TEMP/TMP` 均指向同目录，使用 `python -X utf8`；无 pytest、无系统 Temp、无只读仓库执行。
JSON 保留全部条目检查、24 个陈旧试验、10 个恶意源文本、源文件与政策哈希，可不依赖临时脚本复查。

本专题没有重证旧 3103 条准入；没有把既有测试 driver / scaffold 豁免扩成新证明；没有替代全仓库零违例记录、三档逐值数值门或完整独立 G6。
在这些明确边界内，未发现需要阻断本单的 critical / major。
