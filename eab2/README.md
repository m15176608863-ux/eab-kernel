# eab2 C0：精确数值核心（工作版本）

范围以 [设计 §8.4](../docs/eab2_design.md) 为准。Python `src/eab` 为独立裁判；本目录不导入、调用或修改姊妹引擎。当前不是完整接触引擎，不包含 E/O、LP、Sturm、浮点过滤或宿主接入。

## 构建与复跑

在本工作树根目录的 PowerShell 中：

```powershell
cmd /c eab2\build_eab2.bat
python -X utf8 tools/eab2_diff.py --dll D:/eab-wt/cx-c0/eab2/build/eab2_test.dll --output reports/codex/C0_evidence/diff.json
python -X utf8 tools/eab2_audit.py --output reports/codex/C0_evidence/delivery_audit.json
```

仅支持 VS2022 Community、MSVC 工具目录 14.44.35207 x64、VS 自带 CMake≥3.21/Ninja。实际编译器补丁版本、ISA、Boost、CRT 和 FP 选项由 `get_abi_info` 返回；最终实际命令由 `build/compile_commands.json` 和构建脚本的 Ninja commands 输出提供。脚本不下载、不安装、不删除目录，所有编译产物在被忽略的 `build/`。

产物：

- `eab2_core.lib`：同工具链内部数值静态核心；`eab2_test_numeric.exe` 直接链接该库。
- CMake target `eab2_static`（`eab2_static.lib` + 传递链接 `eab2_core`）：静态 C 生命周期接口。手工链接时须同时提供两个 `.lib`，使用 CMake target 则自动传递。
- `eab2.dll`：正式 C0 生命周期/能力接口；**不导出 numeric_batch**。
- `eab2_test.dll`：另加测试专用 numeric_batch，不能作为发布数值 ABI。
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
- UNPROVED、NO_EVENT、OVERLAP、INFEASIBLE、UNBOUNDED 仅冻结独立状态表示，C0 不实现产生它们的几何/力学接口。
- `scalar_algebraic` 只有精确比较器→RN 边界，不是代数根引擎；无 CertifiedValue、Dual 或 Body2 可选项。
- 内部缺陷注入是实现者的测试敏感性检查，不能代替 Claude 安排的非作者独立对抗核查。
- 本树/字节导出验证不能代替所有者安排的新鲜 worktree/克隆复现。最终工单状态和实际证据见 [C0_report.md](../reports/codex/C0_report.md)。
