# Kernel 清单只读交叉核验（任务内，不是 G6）

范围：`kernel/coverage.json` 的 77 项、新增 `test_r13fixb_kernel_numeric.py` 及相关生产函数；附读 README / exact_predicates_plan 的新支持域节。未修改生产、测试、清单。下述发现针对审阅时快照；主代理已转交 kernel 作者补门，补后必须另核。

## 必须补门或降级的 4 个 API

### KCR-01：三种误差报告只有零误差成功分支的三档值门

影响：

1. `eab.kernel2d.g0.g0_distance_completeness`
2. `eab.kernel2d.g0.g0_exit_completeness`
3. `eab.kernel3d.g03.g0_distance_completeness3`

引用门 `test_g0_success_report_numeric_fields_are_analytic`（审阅时 246–262 行）确实调用各 API，也确实逐字段比较 dataclass；问题不是空测，而是其三个尺度全部只产生 `worst_abs_error=0` / `worst_witness=0` 及空失败列表。因此，返回非零误差的构造表达式和失败 payload 中的数值均未由这些门核对。

例如把内部 `err` 写入报告时错误乘二，或在 `failures.append(...)` 中对调 got/truth、漏转换精确参数，成功门仍无法看见。清单 proof 自己也明确“不外推所有失效报告分支”，所以不宜把 API 标成完整逐值关闭。

建议：三个尺度均通过真实被测路径产生**非零**误差 / 非空失败 payload，使用独立有理值核对每个数值字段；必要的缺陷注入要放在真实内核内部，不在产物之后拼假数据。未补前 status 应为 partial / gap。

### KCR-02：surface_events 的时间与源标签未逐事件绑定

影响：`eab.kernel3d.exact_sweep.surface_events`。

`test_surface_events_each_exact_time_and_normal`（144–159 行）比较 `{e.time} == {2,5,8}`；循环内根据每个 label 核对 normal，但不根据该 label 独立计算其 time。`test_surface_events_non_dyadic_exact_times`（403–406 行）同样仅比较时间集合。

因此，即便将不同标签的 time 互换，保持时间集合、法向与标签各自不变，这两门仍缺少能指认字段错配的断言。这与“逐值”“每个事件量”的要求不符；不是集合不全问题，而是返回数值与来源绑定问题。

建议：对每个 VF/FV 事件独立计算点—平面相交 t；对每个 EE 事件用独立棱向量/叉积关系或解析坐标核 t，并断言 `e.time == expected_for_this_label`。还应保留非二进制时刻，避免整数时刻掩盖早舍入。

## 不计为构造差分缺口的观察

- 20 项 `nonconstructive` 的源码返回值总体与证明吻合：布尔、离散成员状态、标签、源整数索引或拓扑子集。没有发现把距离/法向/坐标等真实构造输出藏进这 20 项。`support_labels` 返回退化数量，是精确离散计数，不是近似几何量；不要仅因 Python 类型是 int 就误判为数值构造缺口。
- `g03_surface_oracle.model` 明确消费清分母后的 integer payload，其三档 `1,7,2^397` 与该 API 输入类型相符；不是把连续量的低端偷偷换成 1。其低端有理坐标经公开距离入口另测。
- `hull/difference_hull` 的 face ring 采用集合比较，不核数组次序/朝向；这是离散拓扑顺序的验收范围，应明确记为集合意义，不应直接按本单浮点构造问题强行加 gap。
- `g0_convex/g0_convex3` 只核成功报告，对失败 mismatch payload 的传递分支未给三档非空示例。其核心实数量是输入/采样坐标的搬运而非新的误差构造，因此本次作为透明范围观察，不与上面的 3 个真实非零误差报告缺口等同计数。
- 主 grid `2^-400,1,2^397` 是实际输入坐标变化。部分时间/参数因几何与速度同缩放保持不变是合理不变量；但不能用三次相同的 t 数值代替逐标签绑定断言，也不能借一个其他 API 的产物互异断言证明所有 API 都有辨别力。

## 支持域文档快审

README 首段与 exact_predicates_plan 新节已明确“合同不是所有实现已闭合”“未证明 API 留缺口”“三点平台误差测量不是普适 libm 定理”，没有发现本轮新增的全 API 已实现承诺。

±400 的推导明确三次项可到 ±1200、Fraction 相消无固定下界，并将输出域定义为 RN-even 舍入胞，口径合理。face_noise 的 `2u+u²` 推导对正边长和精确有理周长成立；仅退化面 inf / 带精确证书 allow_underflow 被列为明确哨兵/显示例外，不冒充有限物理量。

注意：清单/总报告最终数字必须吸收 KCR-01/02 的补门结果，否则正文的谨慎措辞也不能弥补机读清单误报关闭。

结论：审阅时 **4 个 API 必须补门或降级**；无生产行为真错的新断言。本检查仅为任务内交叉核验，不是六路独立 G6 或新的全套运行。
