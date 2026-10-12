# R12FIX 独立设计审查与同类形态扫描

## 边界

本代理仅阅读生产、门和测试代码，生成此审查与候选清单；未修改生产代码或扫描器。此记录不是 G6 退出审查，不声称确认了新的生产数值缺陷。输入只有 G6L-01 一条 major；工单中的 6 条/11 条应按模板残留处理。

## 已向实施者反馈的设计风险

1. 旧扫描器未知调用返回空 rounding/callable 来源，是默认接受而不是默认拒绝；根因在未知路径丢失来源，而非只有 map/iter/pop 四种表面语法。
2. 只允许“静态直接函数名”仍不够：helper 可以返回 vector_rational 的舍入输出；另一个 identity helper 可以洗掉带入的舍入来源。必须保守传播未知返回，或拒绝无法求摘要的数值调用。测试代理已增加两类红门。
3. 不能按方法尾名允许任意对象方法，不能按“导入过该模块”就允许任意新成员；已建议固定完整成员清单、未知成员拒绝。
4. 逐点白名单不能仅冻结调用文本。当前函数、模块初始化绑定以及跨函数/模块依赖均可能改变调用语义。认可实施者采用更保守的完整 module AST 与受保护源依赖摘要锁；任意依赖改动后旧批准必须失效。
5. builtin sorted/min/max 的 key= 接口若传入未解析参数，也应默认拒绝；“未知 Name 不是已知 callable”不能当作已证明该参数不是 callable。
6. 测试豁免需要诚实描述：独立 oracle/helper 按闭集门检查；test_* 驱动函数中的动态变异、断言与内联数值表达式若明确划出保证范围，仍受旧舍入门及数值测试，但不能称所有测试正文都有新闭集静态证明。

## 同类语法盘点

`higher_order_inventory.json` 保存逐项路径、函数、行号与代码。扫描时其他代理已经开始加入新测试，故 test 计数是当时工作树快照，不是原 HEAD 的唯一基线。

| 形态 | src/eab | tests |
|---|---:|---:|
| map | 90 | 88 |
| lambda | 58 | 199 |
| getattr | 5 | 22 |
| setattr | 1 | 224 |
| pop | 17 | 7 |
| next | 24 | 45 |
| iter | 3 | 1 |
| 参数作为直接调用目标 | 22 | 26 |
| 计算表达式作为调用目标 | 1 | 18 |
| exec | 0 | 84 |

这些是语法形态而非数值缺陷计数。当前生产里唯一非 Name/Attribute 的调用目标是 covers3 的 implementations[0]。

## 现有例外的逐点分类

`src_waiver_review_candidates.json` 针对实施者 `strict_scan.json` 中 1007 个 src closed-* 节点，给出逐项英文理由、类别和源码站点；`src_waiver_review_pending.json` 为零项。它们仅是批准候选，最终是否纳入以及 hash 锁由主执行者决定。

分类依据与边界：

- Fraction/精确向量 map：不转换为浮点；不能清除输入已有的 rounding 来源。
- scalar_rational map：只批准当前最终显示点边界；其结果必须保持 rounded，不能赋予 clean 返回摘要。
- 容器、标签、类型对象、异常类、空容器工厂：只针对当前明确数据用途；不能按相同函数尾名推广。
- 排序 lambda 与比较函数：当前函数中没有“构造器先舍入后 norm/root”的表达式，旧门仍检查其正文；上下文和依赖必须冻结。
- Polyhedron 方法：只批准当前受控类型 dispatch；得到显示/诊断输出不等于它是精确中间量，后续舍入来源规则不豁免。
- LP 方法：浮点只给候选，原始数据精确证书负责最终状态；不因此给任何返回值 clean 摘要。
- covers3/interlock/margin 的 callable 缓存键：固定具名实现进入 cache key 是为了 monkeypatch 变异不命中旧缓存；调用者、被调函数和依赖必须一起冻结。实际受控实现仍独立扫描。
- dual.central_difference 的任意用户回调：明确是诊断 API 例外，不属于精确构造 oracle 保证；不声称任意 f 被静态证明。
- oracle_construction 的 Decimal.sqrt：只是候选，独立 Fraction midpoint 证书确认后才接受，否则做 bit search。

## 结论

可有限收敛的方案是：有限可分析子集 + 保守未知来源 + 精确逐点、依赖冻结的人工审查例外 + 其余默认拒绝。白名单与源摘要锁是保证边界的重要部分，不是证明任意 Python 程序数值正确的捷径。上述分类不替代完整测试、变异复验或后续独立复审。


## 第二次独立 soundness 检查

新增确认的门内漏网均已经向主执行者报告，并以真实断言修前红保存：

- 本地函数名遮蔽受信 passthrough：abs/tuple/get/copy/values/items/Fraction/from_float 各定义一个返回 vector_rational 的函数，再调用 norm_rational(该函数(p))，原新门仍返回零违例。8 个新增参数化测试均在修前报红；日志 `pre_fix_shadow_red.log`，探针 `audit_passthrough_shadow.json`。
- 舍入参数跨过程进入 root：finish(p) 内调用 norm_rational(p)，bad(q) 调用 finish(vector_rational(q))。仅把未知返回标为 rounded 不足，因为 root 已藏在 callee 中。源码与测试helper两路径均修前红；日志 `pre_fix_argument_red.log`，探针 `audit_interproc_argument.json`。
- **kwargs 隐藏回调端口：sorted(p, **options)，options 内 key 指向未知参数 fn，绕过只看显式 key= 的检查。已报告要求未知参数展开默认拒绝；证据 `audit_unpacked_callback.json`。

`src_numeric_waiver_review.json` 对 strict_scan 中 204 个非 closed 来源保守误报给出站点理由。明确区分 Fraction/整数、集合差、认证过滤器、实际给定浮点数据运算，以及近似诊断的范围豁免。没有把 _orth/_tri_axes/_gordan_direction/_ray_directions/_inward_vertex_direction、face_noise/manifold诊断、显示见证比较、有限差分等冒称为精确构造。

## 最终候选负向审计与闭包补足

这是本工单内部独立子代理的负向检查，不是所有者约定的外部 G6 退出审查。没有修改生产数值代码；以下真实漏报均先保存 `issues=[]` 与运行错误答案，再加入永久门，由主执行者修改 scanner。

共同的独立数值证据：`q = Fraction(1, 2**1075)`，两个分量的平方范数为 `2*q*q`；它严格位于最小正次正规数 `u = 2**-1074` 的两个平方舍入中点之间。因此正确构造应为 `u`，而下列提前舍入路径实际返回 `0.0`。

| 新确认路径 | 修前永久门 | 采取的封闭边界 |
|---|---|---|
| 模块/函数 annotation 执行 vector 构造后，从 `__annotations__` 回取；从函数 `__globals__` 或类 `__dict__` 回取 | `pre_fix_annotation_red.log`：8 failed | 标注中构造调用默认拒绝；反射不得假装普通类型信息 |
| 函数 `__defaults__` / `__kwdefaults__` 回取 | `pre_fix_default_reflection_red.log`：4 failed | 所有 dunder 属性均默认拒绝，不再枚举少数反射名 |
| 内建生成器 `gi_frame.f_locals` 与异常对象 `args` 回取 | `pre_fix_attributes_format_red.log`：其中 4 failed | 未证明数据属性读取也逐点默认拒绝，不能按字段名普遍放行 |
| `%g` 隐式浮点格式化 / f-string 格式化后重新 Fraction 解析 | 同日志另外 4 failed | 格式化语法/未证明取模默认拒绝；纯整数字面量取模另有正面类型证明 |
| int/int 真除法、负整数幂、Fraction×float 字面量/参数、sum 混合 float 元素/初值 | `pre_fix_implicit_arithmetic_red.log`：12 failed | 无类型证据算术与 sum reduction 默认拒绝；仅递归纯整数字面量精确运算可直接准入 |

上述最终 32 格已独立复跑绿色：`audit_final_negative_green.log` 最后一行原样为 `32 passed, 80 deselected in 0.80s`。此前同名遮蔽、跨过程参数与主策略撤销变异 14 格亦已绿色，见 `audit_added_teeth_green.log`。全套、policy 最终 manifest 与副本门由主执行者统一收口。

### 明确不冒称的保证

- `int(Fraction(...))` 的显式整数截断属于算法意图，不是隐藏 binary64 边界；静态门不能证明任意数值算法选择了正确数学公式。
- 普通默认参数捕获四格（位置、keyword-only、全局别名、容器元素）已有旧来源分析的 `rounded-vector` 拒绝，不是新增漏洞，见 `audit_default_escape.json`。
- 静态子集仍以声明的 builtin 标量/容器及固定受审 record 模型为前提，不证明任意外部对象的重载运算/属性协议，也不证明运行时外部 monkeypatch。
- 手工白名单只是完整源码图冻结下的具体站点批准，不是 callee 名称摘要。异常构造器在真实 `raise` 站点可被批准，并不意味着异常对象不能存储数值或所有 `.args` 读取天然安全。
- `src_final_waiver_review.json` 保存 admission_scan 之后 4042 条新增源站点候选。理由按实际 callee、所在精确/候选/显示/诊断模型区分；旧站点相同表达式复用已审理由。未赋予这些调用普遍 clean-return 语义，不能把证据目录的分类脚本当作自动批准工具。

### 最终正面子集扫描新增站点

`src_positive_subset_review.json` 针对 `final_raw_scan_v2.json` 相对前一快照的 **3873** 个新增 src 站点：未证明算术 2405、数据属性 1202、取模 89、格式化语法 88、sum 85、dunder 协议 4。对应 pending 文件为空。理由保持实际数学模型边界，未通过“名字看起来是 exact”批准新代码。

特别核对了几个易被错误统一描述的类别：

- `_Revised.optimize` 的取模是 **float 候选扰动**，不是整数取模；只影响候选搜索，后面的原数据精确证书必须保留。
- `limit_load` / `limit_multi._centroid` 的浮点平均只选取内部参考点；后续 Fraction 力矩平移保留原数据，并不宣称该平均是精确几何形心。
- `_tangents` 中 t₂ 使用已返回 binary64 t₁ 是明确给定模型；不能以“Fraction 运算”掩盖这一模型选择，也不能把同类提前舍入普遍放行。
- geom 的 add/sub/mul/dot/cross 是参数泛型，浮点调用不普遍精确；需完整固定调用图，精确构造路径使用 Fraction 数据。不能将站点批准升级为这些函数的 clean-return 摘要。
- 4 个 dunder 站点只涉及固定 Dual 算术方法及保留精确 witness 的 wrapper 分配/初始化，不读取函数、生成器或异常的隐藏数值储存。
