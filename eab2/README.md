# eab2 C3-L4：精确二维接触、profile1 极限分析与敏感性

范围以 [设计 §8.2/§8.5](../docs/eab2_design.md) 为准。Python `src/eab` 为参照裁判；本目录不导入、调用或修改姊妹引擎。当前不是完整力学接触引擎；C1 增加二维一般凹简单环 E/O 与局部查询，C3-L1 增加横切精确 LP、完整点接触装配、局部平移锁定证书与一阶法向可动性；C3-L3 增加 profile1 静力装配、极限载荷三态证书和 μ 临界参数（有理基多项式与单侧 Sturm 证明）。C3-L4 已实现精确 LP 敏感性、几何种子传播和 ctypes 全链使用者，发布 ABI v1 的布局技术基线见 [冻结表](ABI_CONTRACT.md#发布-abi-v1-冻结表)。多分支阈值导数的修复及实际验收状态见 [修复轮报告](../reports/codex/C3L4_fix_report.md)，不能把先前 Python/C++ 同错的差分绿当作分支完备性证明。不含一般代数根引擎、浮点过滤或实际宿主集成。

## 构建与复跑

在本工作树根目录的 PowerShell 中：

```powershell
cmd /c eab2\build_eab2.bat
python -X utf8 tools/eab2_diff.py --dll "$PWD/eab2/build/eab2_test.dll" --output eab2/build/tmp/recheck/diff.json
python -X utf8 tools/eab2_audit.py --output eab2/build/tmp/recheck/delivery_audit.json
```

仅支持 VS2022 Community、MSVC 工具目录 14.44.35207 x64、VS 自带 CMake≥3.21/Ninja。实际编译器补丁版本、ISA、Boost、CRT 和 FP 选项由 `get_abi_info` 返回；最终实际命令由 `build/compile_commands.json` 和构建脚本的 Ninja commands 输出提供。脚本不下载、不安装、不删除目录，所有编译产物和 TEMP/TMP 在被忽略的 `eab2/build/`（临时目录 `eab2/build/tmp/`），上述复跑输出同样写到该忽略目录。

产物：

- `eab2_core.lib`：同工具链内部数值静态核心；`eab2_test_numeric.exe` 直接链接该库。
- CMake target `eab2_static`（`eab2_static.lib` + 传递链接 `eab2_core`）：静态 C 生命周期接口。手工链接时须同时提供两个 `.lib`，使用 CMake target 则自动传递。
- `eab2.dll`：生命周期/能力、C1 body/E/双三态/精确结果/0 处局部及 C3-L1/C3-L3/C3-L4 接口；**不导出 numeric_batch、query2_exact_batch 、covers2_exact 或 opt_solve_exact**。
- `eab2_test.dll`：另加测试专用 numeric_batch、query2_exact_batch、covers2_exact 与 opt_solve_exact，不能作为稳定发布 ABI。
- `eab2_test_abi.exe`：DLL ABI/坏 FP 环境测试；`eab2_test_c_header.exe` / `eab2_test_c_header_static.exe`：纯 C 头及正式 DLL/静态链接验证。
- `eab2_test_sensitivity.exe`：默认 CTest 只跑轻量版分支完备性用例（一个共享方向例加一对开阈独立梁，约三分钟）；完整扫描（两种厚度、全部单面、开 / 闭阈成对、三种权重，约二十分钟）用 `eab2_test_sensitivity.exe --branch-sweep` 单独运行，且 L4 `branch` 差分族逐查询覆盖同一组例。

发布 DLL 使用 `/MD`，宿主须已具备 **Microsoft Visual C++ 2015–2022 x64 运行库**（`MSVCP140.dll`、`VCRUNTIME140.dll`、`VCRUNTIME140_1.dll`）。本仓库不自动安装或下载运行库；不是只复制一个 DLL 就保证任意 Windows 主机可运行。

## 已实现且有具名测试守护的边界

有限样本不是全输入域证明。

| 实现 | 具名测试/核验 |
|---|---|
| 私有 `Int/Rational` et_off、binary64 精确解码、零 msb 守卫 | `test_numeric.cpp::exact_and_construction` |
| 八个 construction 函数、一次 RN-even、溢出胞/次正规/ties/整式消去 | `midpoint_matrix`、`exact_and_construction`；`tools/eab2_diff.py::expected/corpus` |
| 整数清分母 orient/cross/dot 符号与精确 AABB 界 | `predicates_and_aabb`；独立 Python 差分中的谓词、变换语料 |
| 严格 bits / 有理文本、非法输入拒收 | `input_and_dispatch`、`test_abi.cpp::numeric_status_matrix` |
| 当前线程 FP 合同、自检无宿主状态净改变 | `test_abi.cpp::environment_matrix` |
| owner/type/generation、过期句柄、部分批次、尺寸/步长、状态分离 | `test_abi.cpp::main/structural_matrix/numeric_status_matrix` |
| 生产不泄漏测试 ABI、实际编译选项、vendor hash、编码与大文件 | `tools/eab2_audit.py`；纯 C 链接测试 |
| ties、整式提前舍入、遗漏 DAZ 检查的真实内部变异被语义门捕获 | `tools/eab2_mutation_check.py`（新名 `--name`，只改本单 tmp 内副本） |

协议与错误分类见 [ABI_CONTRACT.md](ABI_CONTRACT.md)，头文件见 [c_api.h](include/eab2/c_api.h) 与 [testing.h](include/eab2/testing.h)，第三方来源见 [PROVENANCE.md](third_party/boost_multiprecision_1_86_0/PROVENANCE.md)。精确零规范为 +0；输入 −0 的原始 bits 保存在语料中，不改变其精确数值为零的事实；负非零 underflow 只有显式允许才产生 −0。

## 尚未证明 / 无门与退出限制

- 未声称全输入域数值证明、性能预算、跨编译器可复现、任意错误编译配置可由探针识别。
- LP 已输出精确 OPTIMAL/Farkas/UNBOUNDED 证书；几何与 L1 可输出 OVERLAP/UNPROVED/MECHANICAL_UNRESOLVED。NO_EVENT 路径仍未实现；L3/L4 仅支持具名门守护的 profile1，不支持 profile2/非关联摩擦。不能认证的阈值方向必须保留 unresolved，不用单一临界基的斜率替代完整方向证书。
- `scalar_algebraic` 只有精确比较器→RN 边界，不是代数根引擎；无代数根 CertifiedValue 或 Dual 可选项。
- 内部缺陷注入是实现者的测试敏感性检查，不能代替 Claude 安排的非作者独立对抗核查。
- 本树/字节导出验证不能代替所有者安排的新鲜 worktree/克隆复现。历史与当前工单状态分别见 [C3L4_report.md](../reports/codex/C3L4_report.md) 和 [C3L4_fix_report.md](../reports/codex/C3L4_fix_report.md)，待所有者验收。


## C1 与 C0 小项

- C1 工作签名、内存与批次原子性见 [ABI_CONTRACT.md](ABI_CONTRACT.md)，新增 C++ ABI 门 `test_abi.cpp::geometry2_matrix`。
- 精确骨架差分：`python -X utf8 tools/eab2_diff_c1.py --help`；必须指定实际测试 DLL，不允许无 DLL 跳过。局部查询、M3/T1a、近退化与规模的最终完成边界见 [C1E_report.md](../reports/codex/C1E_report.md)，有限案例通过不代表全域证明。
- 允许下溢产生 ±0 时，测试输出显式 `EAB2_DISPLAY_UNDERFLOW_ZERO`；精确零仍 `VALID`。显示分类测试不改 Python 数学合同。
- **ISA identity 指实际受控编译目标 x64-SSE2，不指 DLL 每条指令**：生产和测试两个 DLL 均含 MSVC STL/运行时分派的 AVX2 整数代码；此代码由运行时能力分派，不代表受控几何 TU 采用 AVX。`tools/eab2_audit.py` 将实际编译器 `/Bv` 与 compile_commands、DLL identity 比对；受控源码加 `__AVX__` 编译拒绝。不得据 ISA 字符串声称二进制完全没有 AVX2 字节。
- context/子对象槽位可复用，每次分配推进全局 generation；旧句柄复用后拒收门位于 `test_abi.cpp`。十进制解析增加确定性工作预算，超限 `RESOURCE_LIMIT`，不返回数学 OUTSIDE。

- C1 可配置 context work/elements/integer-bits 限额通过独立 `get_limits2/configure_limits2` 提供，不改变 C0 options 布局；仅无活子对象时可配置。位长采用精确算术前置保守上界，超限 RESOURCE_LIMIT，不冒充整进程内存峰值保证；门见 `test_abi.cpp::limits2_matrix` 与 `test_numeric.cpp::integer_budget_contract`。


## C3-L1 工作接口

- 私有横切 `eab2::opt` 只依赖 exact 数值，不依赖接触装配；默认精确冷启动，候选基必须精确重建核验。三态证书与说谎注入门：`tests/test_opt.cpp`、`tools/eab2_opt_diff.py`。
- `l1.hpp/l1.cpp` 提供 Assembly2/ContactSet2、逐点 F_p、twist 冗余、锁定半径与全覆盖、一阶 DD/零锥证书；只用法向，不引入摩擦剪胀。门：`tests/test_l1.cpp`、`tools/eab2_c3l1_diff.py`。
- C3-L1 ABI 增量见 [ABI_CONTRACT.md](ABI_CONTRACT.md)，生产纯 C 调用和状态/生命周期门为 `test_c_header.c`、`test_c3l1_abi.cpp`；正式 DLL 不导出 `opt_solve_exact` 或并发门测试入口。
- **NO_COMPACT 精确导出仅供诊断**，不承诺未压缩排布的规范接触骨架表示合同；默认 compact 导出才用于完整同构差分。
- `numeric_batch` 除固定输入/解析预算外，每项 evaluate 都使用 context 的 `max_integer_bits` 算术位长预算；超限逐项 RESOURCE_LIMIT，作用域异常退出后复位。仍不是任意算法的统一墙钟/内存保证（详 ABI 合同及 `test_abi.cpp::numeric_compute_budget_matrix`）。
- 完整进度、具名回归、非唯一证书的严格差异计数与独立核证见 [C3L1_report.md](../reports/codex/C3L1_report.md)。有限测试、字节导出和实现者变异门不替代所有者新鲜树及 Claude 指派的独立核查。

DLL 字节不承诺跨树复现（本轮未增加 `/Brepro`）；复现以受测源码 SHA-256、实际工具链/编译选项及语义门为锚。单树 DLL 哈希仅标识该次被测产物，不能据不同树 DLL 哈希不同推断源码或数学结果不同。


## C3-L3 工作接口与已测试性质

| 实现/边界 | 具名门 |
|---|---|
| g±、作用反作用、精确力矩、参考点/端板物理锚点、回归(d)、4/3与2/3 | `test_statics.cpp::g5_closed_form_and_masks/matrix_and_certificates` |
| 原/对偶与驱动机构、Farkas、无界可行点和射线、VV冗余不计力 | `test_statics.cpp::matrix_and_certificates`；差分 `verify_limit` |
| binary64括号、零/有界域、开闭阈、Sturm端点根/内部根、字段拆分 | `test_critical.cpp::binary_grid/polynomial_guards/threshold_contracts`；差分 `verify_critical` |
| 刚体/单位/参考点变换及有效蕴含、G5反向反例 | `test_statics.cpp::rigid_units_and_anchor_translation/valid_implications_and_reverse_counterexample`；`test_critical.cpp::invariant_thresholds`；差分 `metamorphic_cases/implication_cases` |
| 静力与阈值的内部源码缺陷被指定语义红门捕获 | `tools/eab2_c3l3_statics_mutations.py`、`tools/eab2_c3l3_critical_mutations.py`（实现者自检，不是独立核查） |

正式差分：`python tools/eab2_c3l3_diff.py --dll "$PWD/eab2/build/eab2.dll" --output eab2/build/tmp/recheck/c3l3_diff.json`。`tools/eab2_c3l3_scale.py` 只作 P2 冷进程规模/耗时报告，**不设性能门**。未证明全输入域正确性、一般代数根精确值、有限样本以外的性能预算或非关联模型安全性。profile1 的 UNBOUNDED 不等于锁定，也不是有限承载力。

## C3-L4 与发布 ABI 验证入口

| 范围 | 具名门 / 独立入口 |
|---|---|
| 固定基、回收锥与 Mills/Freund，几何种子传播 | `tests/test_sensitivity.cpp`、`tests/test_geometry_seed.cpp`；`tools/eab2_c3l4_diff.py` |
| 阈值纯恒/活载种子与下端不可行的对偶见证 | `test_sensitivity.cpp::branch_pure_load_jet_corpus_regression/branch_infeasible_lower_dual_with_load_jet` |
| certified 方向必须同时携带下端对偶、上端点与射线；缺项不输出值 | `tests/test_threshold_branch.py::test_certified_direction_without_witnesses_is_never_a_value`；`test_sensitivity.cpp::branch_face2_regression` 的 JSON 非空检查 |
| 非对称有限承载的 `asym_limit_dead_live` 通道（有精确有限 limit 时追加） | `tests/test_eab2_c3l4_asymmetric.py::test_asymmetric_case_preparation_does_not_claim_a_referee_or_certified_slope`；`tools/eab2_c3l4_diff.py` 的 asymmetric 族 |
| 种子尺寸/步长、结果生命周期、原子错误 | `tests/test_c3l4_abi.cpp` |
| 全部导出、常量、返回类型、结构字段冻结 | `tools/eab2_release_abi.py`；`tests/test_eab2_release_abi.py` |
| 只用标准库 ctypes 与发布 DLL 的全链 | `tools/eab2_tia_consumer.py`；`test_consumer_derived_seed_presence_is_iff_not_optional` |

发布 ABI 审计可用 `python -I -S tools/eab2_release_abi.py --dll <绝对路径/eab2.dll> --output <ignored目录/release.json>`，不导入 consumer 或差分 harness。consumer 可用同样隔离模式运行；二者不需要 `src/eab`、pybind 或姊妹代码。旧 C3-L4 单基隐函数证明不是本次分支修复的证据，当前各门的实际执行末行以修复轮报告为准。

64b499f 的定向顶点获取、固定探测点及复用基探测一致性机制见 [设计澄清](../docs/eab2_design_amendment_20261023.md#4-输出与独立复核) 与 [接口对账](../reports/codex/C3L4_fix_evidence/cpp_interface_audit.md)。有限候选搜索不保证分支完备，新增能力的全族接受仍等所有者 L4 分片结果，不列为全输入域已证明命题。
