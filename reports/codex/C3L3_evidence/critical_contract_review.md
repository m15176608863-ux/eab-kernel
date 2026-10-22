# WO-C3L3：critical_parameter 合同核查素材

日期：2026-10-23。范围：正式工作树中的 `eab2/src/critical.hpp`、`critical.cpp`、`tests/test_critical.cpp`，以及关联 ABI、差分和突变入口的只读核查。**这是实现者的定向自检，不是 Claude 安排的独立对抗核查，也不是全输入域证明。** 本次仅新增本文；未修改源码、未重跑 Python 全档。

依据为 [eab2 设计](file:///D:/eab-wt/cx-c0/docs/eab2_design.md) §4.6.4、§5.4、§8.2 C3-L3 行。实读设计 SHA-256 与工单一致：`6d174ecc4f1326d5bac21c56c8d333485fb50bbaef3a12150e94eaff14cb4dac`。Python 口径为 `src/eab/kernel2d/statics.py::critical_parameter/_finish_critical` 和 `src/eab/kernel2d/critical.py`；没有改动 Python 数学合同。

## 1. 正式文件与已执行证据

| 文件 | SHA-256 |
|---|---|
| `eab2/src/critical.hpp` | `ed45ebd3ddd0bebf5a49236ed2683bf397e3d1c66e1bed3be322f2e0a24d2460` |
| `eab2/src/critical.cpp` | `c90fbbce747d58157e141dc0ccd31d630f38660158003871fdff3354e4e285c5` |
| `eab2/tests/test_critical.cpp` | `f9a8affced3ade30d39a3d9dc28e42804a8d2b24e2e755ff20a49b373eecebc5` |
| `tools/eab2_c3l3_critical_mutations.py` | `32c49693a91a467bc11074f740719648b7290df874fe9b71a62f683f8096757f` |

正式构建的 [C++ 执行摘要](file:///D:/eab-wt/cx-c0/reports/codex/C3L3_evidence/cpp_tests.json) 已记录 `build_exit_code=0` 和 `100% tests passed, 0 tests failed out of 12`。正式 [critical 单测原始日志](file:///D:/eab-wt/cx-c0/reports/codex/C3L3_evidence/eab2_test_critical.log) 最后一行原样为：

```text
C3L3_CRITICAL_OK checks=322
```

其中具名 CTest 为 `critical_static`；内部可定位门为 `binary_grid()`、`polynomial_guards()`、`threshold_contracts()`、`invariant_thresholds()`、`unavailable_contracts()`、`private_integer_budget()`。

## 2. μ 定义与 binary64 括号合同

定义保持为连续实数参数域上的 `mu_crit = inf {mu in [0, mu_max] : L3 UNBOUNDED}`。仅接受 `param="mu"`；其他参数报 `UNSUPPORTED / only_mu_is_monotone`，没有假定几何参数单调。`mu_max` 必须非负且有限 binary64 可精确表示；C++ 私有层也检查，不仅依赖 ABI 位模式输入。

- 内部 `mu_lo/mu_hi` 用 `Rational` 存储；每个已填端点均通过精确可表示性判断。JSON 同时输出规范有理串和十六位 `mu_lo_bits/mu_hi_bits`，没有将显示舍入值回灌 LP。
- 中点能精确表示时直接查询；否则在中点所在 binary64 网格向下取整，必要时前进一格，只接受严格内点。没有内点时保留双端证书并报告 `input_resolution_limit`，不降级为 `UNPROVED`。
- `reason` 与 `bisection_termination` 保存二分退出原因；随后证得开/闭阈时，另置 `threshold_proof_reason="exact_basis_continuation"`，不覆盖退出原因。
- `attained` 为三态：只有阈值处状态及所需延拓证据齐备才填 `true/false`；普通括号保留 `null`。括号宽度、某个上端为无界或采样第一次无界都不替代阈值证明。

具名门：`binary_grid()` 验证最小次正规、次正规/正规交界、正常指数交界、最大有限数、相邻端点无内点以及需要 54 位的精确中点；`threshold_contracts()` 验证 `max_steps=0/1`、有理非 binary64 阈值 `11/48` 与 binary64 端点分离，并验证仅最后允许一步耗尽分辨率时两个原因字段仍分离。

### 端点特殊分支

| 分支 | 输出与保留证据 | 具名门 |
|---|---|---|
| μ=0 已无界 | `lo=hi=0`、`attained=true`、零点无界证书；不伪造下端机构或延拓证明 | `threshold_contracts()` |
| μ_max 处有界 | `mu_hi=null`、`reason=bounded_on_domain`、μ_max 机构证书；不声称域外永久有界 | `threshold_contracts()` |
| μ_max 处不可行 | `mathematical_status=INFEASIBLE`、`infeasible_on_domain`、Farkas 证书 | `unavailable_contracts()` |
| 未解析接触或 completeness 未知 | `UNPROVED` 与真实原因；不制造端点 | `unavailable_contracts()` |
| 缺任一必需的查询证书 | 保持 `UNPROVED` 的对应原因；不推定已证阈值 | 生产分支只读核查；已有未解析/缺完整性具体门，不声称注入覆盖所有服务失败路径 |

## 3. 开阈、闭阈与多项式证书

固定几何、荷载后从 μ=0、1 的装配结果精确形成 `A(mu)=A0+mu*A1`。没有另实现 LP 求解器；所有端点及阈值处 LP 均调用现有 `statics -> eab2::opt`。

`CriticalBasis2` 保存 `kind`、基列编号、进入列、行列式、分子多项式、列标签、样本参数与精确样本值。系数按常数项到最高次排列。

1. **下侧机构基**：从精确最优对偶的活动列选取满秩基；以 `y=B^-T c_B` 得到所有列松弛 `A_j^T y-c_j` 的有理函数。使用加边行列式生成分子，并核样本处全部松弛非负。
2. **上侧改进射线基**：令唯一目标列 α 进入且 `r_alpha=1`；优先选取实际无界射线正分量对应接触列，补足独立列；以 Cramer 规则计算 `r_B=-B^-1 A_alpha`，并核样本处非负。
3. **多项式运算**：Q[μ] 上 Bareiss 消元，每次多项式除法必须余数为零。延拓证明先去除两端因子并保存重数，再作精确 Sturm 零计数。分母必须无内部根；非零分子若有内部根也保守拒绝，即使偶重根不变号亦不强行分类。零分子作为恒活动约束保留。
4. **候选不是结论**：只考察下端、上端及括号中的简单有理候选；非零候选须是某个非零证书多项式的根，再进行候选处精确 LP 查询。

闭阈接受条件：候选处为 `UNBOUNDED`，并且候选为 0 或有下侧机构延拓证据，排除更早无界。开阈接受条件：候选处为 `OPTIMAL`、恒载右端 `b=0`、上侧归一化改进射线可延拓且候选小于上端；此时 `x0=0` 在上侧始终可行。它不推广成非零恒载下的一般开阈判定。

具名门 `polynomial_guards()` 用独立因式分解标量多项式验证内部根、分母极点、双端重根、负比值、零分子和恒奇异分母；还故意传入错误对偶候选，确认负松弛不能成为机构基。`threshold_contracts()` 采用 G1 三取向的手工代入闭式，包含 `11/48` 闭阈、`3/16` 开阈、`5/16` 闭阈、`191/2048` 闭阈、零开阈和零闭阈，分别验证阈值与 `attained`。

## 4. 独立核证路径与 P0 对照

C++ `verify(LimitResult2)` 使用 opt 原始模型证书检查器，属于直接数学重核，但复用了 C++ opt 检查原语，不能冒充独立 Python oracle。真正跨实现独立核证由 [差分工具](file:///D:/eab-wt/cx-c0/tools/eab2_c3l3_diff.py) 提供：

- `rebuilt_problem()/checked_problem()` 从原始几何、冻结参考点、DOF 锚点和荷载重建 A、b、c；
- `verify_limit()` 核 x/y/机构、Farkas 或可行点加归一化改进射线，不要求非唯一解逐字相同；
- `verify_branch()` 按原矩阵核基行列式及 Cramer 多项式恒等式；`branch_signs()/verify_critical()` 独立核 Sturm 及阈值开闭；
- `compare()/semantic()` 对端点、状态、阈值、attained 和分字段原因作精确比较；非唯一 basis、查询计数与可替代证书不作字节相等门。

| 工单项 | 正式实现/具名门 | 本文结论边界 |
|---|---|---|
| P0-1/2 静力装配与三态证书 | `test_statics.cpp::matrix_and_certificates()`；critical 的端点 `verify()` | critical 只消费 statics 的三态证书；没有把 UNBOUNDED 读成有限容量或锁定 |
| P0-3 μ 临界参数 | `binary_grid()`、`threshold_contracts()`、`polynomial_guards()`、`unavailable_contracts()` | 上述已实现分支有具名门；未实现完整代数阈值求解 |
| P0-4 正式语料与 T1b | `formal_cases()`、`t1b_cases()`、`regression_cases()`、`verify_critical()` | 本文不替最终差分报告宣布计数或 0 失配；以权威完整运行末行为准 |
| P0-4 必须的形貌分类 | `t1b_cases()` 显式列三个有理闭阈、两个开阈、八个无理括号的必需索引及期望 | 有理闭阈为 `131009/2097408`、`98283/2097664`、`326839/6291456`；开阈为 `1/16`、`7/128`；无理括号仍要求 exact_threshold/attained 为 null |
| P0-5 ABI | `test_c3l3_abi.cpp::contract()/unresolved()/resource_limit()`；CTest `c3l3_abi_production_dll` | 正式 C++ 执行摘要已有 `EAB2_C3L3_ABI checks=128 failed=0`；资源失败输出原子性由 ABI 门守护 |

## 5. P1 元门的实际范围

`invariant_thresholds()` 对 G1 开、闭两种取向使用固定种子的 Pythagorean 有理随机旋转，配合平移分量幅值 `{0,1e3,1e5,1e6}` 和单位缩放 `8`、`1/1024`；最后一组包含大坐标下小特征尺度。另将参考点移动 `(13/7,-5/3)` 而保持物理 DOF 锚点固定，并同步变换荷载力矩，核 μ 阈值及开闭不变。

这是**私有精确有理层**的刚体/单位元门。非轴向 Pythagorean 旋转系数一般不是 binary64，不能写成“所有这些变换都通过 binary64 ABI 无损输入”。荷载/端板锚点和有效蕴含的其他门由 `test_statics.cpp::rigid_units_and_anchor_translation()`、`valid_implications_and_reverse_counterexample()` 覆盖，不由本文重复认领全部证明。

## 6. 资源边界与有牙自检

`critical_parameter` 私有入口建立 `GeometryWorkScope` 和 `IntegerLimitScope`，后者贯穿域检查、二分、候选构造和多项式证明，不在端点 LP 返回后失效。`private_integer_budget()` 包含两种定位：

- 16 位预算、预先构造的 `2^200` 域上界和未解析接触：不会进入任何 LP，仍应在私有入口的参数算术触发 `ResourceLimit`；
- 128 位预算下 μ=0/1 两个 LP 均有证，但 `max_steps=0` 的后续多项式延拓超出预算，应如实失败；退出后线程局部预算必须恢复。

**不能称统一算术工作预算。** geometry 工作量计数覆盖其已埋点路径，LP 另有 `opt::Options::max_pivots`；多项式的每一步有理算术没有逐项记入 `geometry.step`。整数保守位长预算限制每步整数工作规模，但不是墙钟上限或整个证明运算次数上限。ABI 另拒绝 `max_steps>4096`；私有 C++ 接口的步数由调用者提供。

可复跑 [critical 突变工具](file:///D:/eab-wt/cx-c0/tools/eab2_c3l3_critical_mutations.py) 只向 `eab2/build/tmp` 的新子目录写入；先全源重编并执行正常基线，再在生产源内部依次注入五个缺陷，记录原/变体 SHA、精确替换、编译命令与目标语义断言。不依赖历史临时 obj/lib，不改生产源码。

已执行的[正式源码权威自检摘要](file:///D:/eab-wt/cx-c0/reports/codex/C3L3_evidence/critical_mutations.json) 与本节正式 critical 源码、测试和 runner 的 SHA 相同；它记录 `sources_unchanged=true`，最后一行原样为：

```text
C3L3_CRITICAL_MUTATIONS_OK caught=5 escaped=0
```

五个内部缺陷分别是跳过分子 Sturm、跳过分母 Sturm、抹掉末步分辨率退出原因、允许非 binary64 域上界、删除私有入口整数作用域。均由对应语义断言报红，不是哈希不符或输出后追加假记录。摘要留在本单证据目录，原始日志和隔离变体另有[逐文件归档映射](file:///D:/eab-wt/cx-c0/reports/codex/C3L3_evidence/archive_manifest.json)；不能将本自检升级为独立对抗审查通过。

## 7. 未实现与不能据此宣称的事项

1. 没有完整代数根求解、无理精确阈值对象或无理阈值处 attained 自动分类；保存基多项式与有证 binary64 括号符合本阶段边界。
2. 有理候选枚举和基延拓是保守认证器，不保证找到每个可表达有理阈值；缺基、缺延拓或内部零点时保留原括号和 null，而非猜测。
3. 不对 μ 之外的参数声明单调；不把有限试例、公式族或语料差分等同于所有几何/荷载证明。
4. 不给出姊妹力学轨迹等价、工程承载安全性或锁定结论。profile1 的关联流动口径及 UNBOUNDED 非有限承载力边界不变。
5. 本文没有重跑 Python 全档、没有安排新鲜 worktree，也没有完成 Claude 独立对抗核查；这些退出要求须由主报告分别据实记录。

结论：正式 critical 实现与具名门支持本节所列合同；无新增设计冲突。最终 WO-C3L3 完成状态仍由完整差分、Python 收尾门、证据卫生和所有者独立核查共同决定。
