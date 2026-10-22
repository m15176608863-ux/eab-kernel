# eab2 C3-L3：精确二维接触与 profile1 极限分析（工作版本）

范围以 [设计 §8.2/§8.5](../docs/eab2_design.md) 为准。Python `src/eab` 为独立裁判；本目录不导入、调用或修改姊妹引擎。当前不是完整力学接触引擎；C1 增加二维一般凹简单环 E/O 与局部查询，C3-L1 增加横切精确 LP、完整点接触装配、局部平移锁定证书与一阶法向可动性；C3-L3 增加 profile1 静力装配、极限载荷三态证书和 μ 临界参数（有理基多项式与单侧 Sturm 证明）。不含 L4 完整敏感性、一般代数根引擎、浮点过滤或宿主接入。

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
- `eab2.dll`：生命周期/能力、C1 body/E/双三态/精确结果/0 处局部及 C3-L1/C3-L3 接口；**不导出 numeric_batch、query2_exact_batch 、covers2_exact 或 opt_solve_exact**。
- `eab2_test.dll`：另加测试专用 numeric_batch、query2_exact_batch、covers2_exact 与 opt_solve_exact，不能作为稳定发布 ABI。
- `eab2_test_abi.exe`：DLL ABI/坏 FP 环境测试；`eab2_test_c_header.exe` / `eab2_test_c_header_static.exe`：纯 C 头及正式 DLL/静态链接验证。

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
- LP 已输出精确 OPTIMAL/Farkas/UNBOUNDED 证书；几何与 L1 可输出 OVERLAP/UNPROVED/MECHANICAL_UNRESOLVED。NO_EVENT 路径与 L4 完整敏感性仍未实现；L3 仅支持具名门守护的 profile1，不支持 profile2/非关联摩擦。
- `scalar_algebraic` 只有精确比较器→RN 边界，不是代数根引擎；无代数根 CertifiedValue 或 Dual 可选项。
- 内部缺陷注入是实现者的测试敏感性检查，不能代替 Claude 安排的非作者独立对抗核查。
- 本树/字节导出验证不能代替所有者安排的新鲜 worktree/克隆复现。最终工单状态和实际证据见 [C3L3_report.md](../reports/codex/C3L3_report.md)。


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
