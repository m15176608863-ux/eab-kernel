# WO-C0 执行报告：eab2 精确数值核心

## 结论与边界

**实现及本树验证通过；里程碑状态为 C0_PARTIAL。** C0 必做实现已落地，C++ / DLL / ctypes / Python 快档与四分片全档均绿。尚未完成设计 §8.4 明定的非作者独立对抗核查与获准新鲜树复现，故不标 C0_DONE，不用实施者自测替代验收。

机器摘要：[C0_acceptance.json](file:///D:/eab-wt/cx-c0/reports/codex/C0_evidence/C0_acceptance.json)；全部交付链接：[C0_delivery_manifest.md](file:///D:/eab-wt/cx-c0/reports/codex/C0_evidence/C0_delivery_manifest.md)。

- 工作树：`D:/eab-wt/cx-c0`，入口干净；分支 `eab2-c0`，回滚锚 `7f9510502ba265e53b5be8de4be22308dfe65f9a`。
- 依据：设计第二版 r3b；入口及收尾 SHA-256 均为 `6d174ecc4f1326d5bac21c56c8d333485fb50bbaef3a12150e94eaff14cb4dac`。
- `src/eab` 与设计共 64 个跟踪文件哈希保持不变，Git diff 为空。见 [python_design_unchanged.json](file:///D:/eab-wt/cx-c0/reports/codex/C0_evidence/python_design_unchanged.json)。
- 只写本工作树。未 commit/push/reset/checkout/stash/worktree/branch；未下载、未安装；外部 vendor、姊妹构建脚本只读。
- 本单没有创建新鲜 Git 树。H1 使用带逐文件哈希、执行节点和模块实际执行核对的**字节导出**；它不替代纪律 D。本次工作树由所有者给定，新增成果尚未提交。

## 1. 构建命令与实际工具链（设计 §3、§8.4.1）

```powershell
cmd /c eab2\build_eab2.bat
python -X utf8 tools/eab2_diff.py --dll D:/eab-wt/cx-c0/eab2/build/eab2_test.dll --output reports/codex/C0_evidence/diff.json
python -X utf8 tools/eab2_audit.py --output reports/codex/C0_evidence/delivery_audit.json
```

实测 VS2022 Community 自带 CMake **3.31.6-msvc6**、Ninja **1.12.1**；指定工具目录 **14.44.35207**，该目录实际编译器报告 **19.44.35227.0**（不是擅换工具集）。纯 ASCII 批处理调用固定 vcvars64，显式 x64，产物位于忽略的 `eab2/build/`。

构建身份原文：

```text
eab2-c0;compiler=MSVC-19.44.35227.0;toolset=14.44;isa=x64-SSE2;boost=1.86.0-et_off;fp=precise-contract_off;crt=MD;cxx=20
```

以下取自最终 `compile_commands.json`，不是凭 CMake 意图抄写：

```text
C:\PROGRA~1\MICROS~4\2022\COMMUN~1\VC\Tools\MSVC\1444~1.352\bin\Hostx64\x64\cl.exe  /nologo /TP -DBOOST_MP_STANDALONE -ID:\eab-wt\cx-c0\eab2\src -ID:\eab-wt\cx-c0\eab2\third_party\boost_multiprecision_1_86_0\include -ID:\eab-wt\cx-c0\eab2\build\generated -ID:\eab-wt\cx-c0\eab2\include /DWIN32 /D_WINDOWS /EHsc /O2 /DNDEBUG -std:c++20 -MD /utf-8 /permissive- /fp:precise /W4 /EHsc /FoCMakeFiles\eab2_core.dir\src\numeric.cpp.obj /FdCMakeFiles\eab2_core.dir\eab2_core.pdb /FS -c D:\eab-wt\cx-c0\eab2\src\numeric.cpp
```

MSVC 的 `-std:c++20` / `-MD` 与 `/std:c++20` / `/MD` 等价；最终实际选项包含 `/O2 /utf-8 /permissive- /fp:precise`，额外 `/EHsc /W4 /DNDEBUG`。C++ 核心与 DLL 没有 `/arch:AVX*`、`/GL`、`/fp:fast` 或 `/fp:contract`；数值和 FP TU 显式 `fp_contract(off)`；编译守卫拒 `_M_FP_FAST / __FAST_MATH__ / _M_FP_CONTRACT`。默认 ISA 为 x64 SSE2，记录在构建身份。

最终审计读取 **9 条**实际编译命令，并核 production/test 导出分离、vendor 哈希、编码及大文件：[delivery_audit.json](file:///D:/eab-wt/cx-c0/reports/codex/C0_evidence/delivery_audit.json)。完整实际命令与单测末行见 [build_final.log](file:///D:/eab-wt/cx-c0/reports/codex/C0_evidence/build_final.log)。没有执行本单排除的负构建矩阵、跨编译器或每 TU 审计工程。

产物包括 `eab2_core.lib`、CMake target `eab2_static`、正式 `eab2.dll`、测试 `eab2_test.dll`；C++ 数值测试直接链接静态核心，C 头分别链接正式 DLL 和静态接口。`eab2_static` 传递链接核心；手工链接须同时给两个 `.lib`。所有二进制仅本地保留，见 [本地构建目录](file:///D:/eab-wt/cx-c0/eab2/build)，不进入待提交文件。

## 2. Boost 来源、复制与准入（设计 §2.5）

- 来源 URL：`https://codeload.github.com/boostorg/multiprecision/tar.gz/refs/tags/Boost_1_86_0`（所有者已提供；本单没有网络下载）。
- 包 SHA-256：`ef23b88cc3ae9c050d18887f7815aabb756c955ee8c64ca0b77690b79c316949`，实际核验一致。
- 先将已解包头临时复制到本单 tmp，在 MSVC 下编译运行 `BOOST_MP_STANDALONE`、`cpp_int` / `cpp_rational`、`et_off` 最小程序；末行原文：`BOOST_STANDALONE_OK cpp_int cpp_rational et_off`。证据：[boost_probe.cpp](file:///D:/eab-wt/cx-c0/reports/codex/C0_evidence/boost_probe.cpp)、[boost_probe.log](file:///D:/eab-wt/cx-c0/reports/codex/C0_evidence/boost_probe.log)。
- 按 `/showIncludes` 实际包含闭包正式复制 **70 个头 + LICENSE = 71 文件**，总计 **1438350 字节**；包含独立模式必需的少量 Boost.Config 头，未复制 doc/test 等目录。
- 每个复制文件均逐字节对照已解包文件与 SHA 钉定压缩包对应条目；没有改动第三方源，保留 BSL-1.0。
- 最大文件 **240279 字节**，无单个超过 1,000,000 字节，不需要新增 H1 大文件豁免。
- 完整复制清单、来源、未修改声明及逐文件 SHA：[PROVENANCE.md](file:///D:/eab-wt/cx-c0/eab2/third_party/boost_multiprecision_1_86_0/PROVENANCE.md)；机器清单：[COPY_MANIFEST.json](file:///D:/eab-wt/cx-c0/eab2/third_party/boost_multiprecision_1_86_0/COPY_MANIFEST.json)。

## 3. 数值条款逐项对照（设计 §2、§8.4.2–3）

所有下列性质仅按具名门和选定语料报告，不把有限测试说成全输入域证明。内核见 [numeric.cpp](file:///D:/eab-wt/cx-c0/eab2/src/numeric.cpp)；封装见 [exact.hpp](file:///D:/eab-wt/cx-c0/eab2/src/exact.hpp)；静态门见 [test_numeric.cpp](file:///D:/eab-wt/cx-c0/eab2/tests/test_numeric.cpp)。

| 条款 | 实现与验证 |
|---|---|
| 私有 Int/Rational | 两个薄包装内部使用 Boost et_off，运算返回拥有值；Boost 类型不越封装边界，不进 C 头；`Int::bit_length` 先守零再 msb。`exact_and_construction`。 |
| binary64 无损解码 | 直接分解 sign/exponent/fraction，整数移位恢复有理数；包括次正规、最大有限值、负数和 -0；静态门独立核多个原始分子/分母公式。ctypes op10 仅位回环，不能单独冒充完整解码证明。 |
| orient2d/cross/dot | 输入差分先精确；符号以 cpp_int 清分母求值；不做浮点过滤、不使用本机 __int128 快路。`predicates_and_aabb` 与独立 Python 参照。 |
| AABB | 内部上下界保存 Rational，包含/相交精确比较；静态微特征门证明不以已 RN 显示界代替；测试桥导出界时另走 RN。 |
| scalar_rational | bit length 求指数、divmod 和余数中点比较，ties-even、打包 bits；次正规/跨 binade/上溢胞均覆盖。最大有限值上方胞内返回 maxfinite；绝对值达到 `2^1024−2^970` 失败。 |
| scalar_algebraic | 精确 compare(real, rational)→正 binary64 位序邻数搜索→有理中点 RN；概念上邻为 `2^1024`，不是 Inf。仅有理和平方根比较语料，不做 Sturm。 |
| ratio_rational | 精确比值后一次 RN；零分母 INVALID_INPUT。 |
| vector_rational | 每分量精确标量构造；空向量返回空。 |
| sqrt_rational | 整数平方根 + `4N` 对 `D(2q+1)^2`；负奇数指数向下取整；负被开方数拒绝；非平方次正规、ties 与溢出胞有门。 |
| norm_rational | 精确求平方和，再一次正确舍入 sqrt；空向量 +0，不先浮点平方/求和。 |
| unit_rational | 分量 `sign·sqrt(v_i²/Σv_j²)`；不先 RN norm；零向量拒绝；norm 中间越界但分量有限的语料覆盖。 |
| normalized_difference_rational | 对整个 `c/sqrt(nn)−offset` 与有理中点精确比较；不先舍入两项；巨大消去、无理消去、ties、极小非零差有门；nn 必须正。 |
| 零与下溢 | 精确零统一 +0；负非零仅显式 allow_underflow 才可返回 -0；默认非零 RN→0 为具名 CONSTRUCTION_RANGE 错误，不静默返回零。 |

八函数全部由 C++ `midpoint_matrix/exact_and_construction` 和独立 ctypes 语料验证；高指数、分界点、非对称输入、尺度变化与精确旋转/平移语料并存，不以整齐轴对齐网格替代覆盖。

## 4. FP 环境自检与真实坏环境（设计 §3.2）

`eab2_self_test` 在 context 创建及每次 numeric_batch 入口调用，检查当前线程：FE_TONEAREST、FTZ/DAZ 关闭、MXCSR 7–12 全屏蔽、binary64、ties-even、signed zero、渐进下溢，以及同 TU noinline `(1+2^-27)*(1−2^-27)−1` 收缩探针。探针输入运行时载入，中间乘积不是 volatile。

先检查屏蔽/控制位，后运行可能置 sticky flag 的探针；不把宿主坏控制模式改好再通过。成功探针只恢复原始 sticky flags，完整 MXCSR/_controlfp_s 调用前后相等。默认 SSE2 无 FMA，有限探针不是任意错误构建的万能识别器。

`test_abi.cpp::environment_matrix` 分别注入 **FTZ、DAZ、3 种非最近舍入、6 个屏蔽位缺失**，逐个检查 self_test/create/batch 拒绝及失败输出不变。最终原始证据：

```text
FP_ENVIRONMENT: FTZ=reject DAZ=reject ROUND_MODES=3_reject MASK_BITS_7_12=6_reject HOST_STATE=unchanged
```

## 5. C0 ABI 合同冻结（设计 §5.4、§7.2）

完整合同见 [ABI_CONTRACT.md](file:///D:/eab-wt/cx-c0/eab2/ABI_CONTRACT.md)；正式头 [c_api.h](file:///D:/eab-wt/cx-c0/eab2/include/eab2/c_api.h)，测试头 [testing.h](file:///D:/eab-wt/cx-c0/eab2/include/eab2/testing.h)。

| 合同 | 落地及测试 |
|---|---|
| 正式五入口 | get_abi_info/self_test/context_create/context_destroy/context_get_error；纯 C 头验证通过，无 bool/STL/Boost/异常/编译器 enum 布局越界。 |
| 能力探测 | 版本、结构尺寸、binary64/x64、构建身份；正式 DLL 仅 CONTEXT，测试 DLL 另 TEST_NUMERIC；rho/SE2/LP2 明确 unsupported；production 无 numeric_batch 导出。 |
| 三状态分离 | call_status / mathematical_status / display_status 独立；UNPROVED 单独编码，不能 false；C0 只产生 VALUE/NOT_COMPUTED，其余数学状态是合同表示而非已实现能力。 |
| 错误分类 | OK=0；INVALID_INPUT=1、INVALID_HANDLE=2、UNSUPPORTED=3、CONSTRUCTION_RANGE=4、RESOURCE_LIMIT=5、FP_CONTRACT=6、INTERNAL_ERROR=7、CANCELLED=8。取消类别预留，不冒称实现取消操作。 |
| 句柄 | 32 字节 owner/id/generation/type token，混合两个 context、错误类型/世代、过期及重复释放均拒收；C0 无子对象，owner=id，id 单调不复用。 |
| 创建/释放 | 创建失败先清零输出，库 RAII 分配与释放；未交出半初始化句柄，不跨 CRT free。 |
| 错误详情 | context-owned code/field/index/message；两阶段消息复制，短 buffer 不写；下一正常批清错、销毁即失效，不用全局 last_error。 |
| 尺寸/stride | 精确 sizeof/abi_version、尺寸乘法溢出、容量/null/reserved/flags 校验；不截断、不补零。 |
| 部分失败 | 先核全部描述符，再暂存，最后提交；结构/环境/批分配错误不改输出；正常批逐项状态，失败 bits 不写且 count=0；输入输出内存仍由调用方拥有。 |
| bits / rational | bits 小写恰 16 位最高位先，-0=`8000000000000000`，NaN/Inf 拒收；有理串 n/d 约分、d>0、零0/1；输出 uint64 位整数由工具固定格式化，与内存字节序无关。 |
| 资源与支持域 | 测试协议上限65536 items/每项65536 values/每文本1048576 bytes，超限 RESOURCE_LIMIT；不伪装几何否定。 |

签名仅冻结 C0 工作接口，不冻结 C3 发布产品 ABI，不做恶意地址、重叠内存或宿主接缝加固；调用方须提供真实有效、足够且不重叠的缓冲区。

## 6. C++ 单测、差分与有牙门（设计 §7、§8.4.6）

最终构建实际运行原始末行：

```text
EAB2_NUMERIC_TESTS checks=544 failed=0
FP_ENVIRONMENT: FTZ=reject DAZ=reject ROUND_MODES=3_reject MASK_BITS_7_12=6_reject HOST_STATE=unchanged
ABI_TESTS: 689 assertions, 0 failures
C_HEADER_PRODUCTION_DLL checks=7 failures=0
C_HEADER_STATIC checks=7 failures=0
```

CTest 四目标全部通过：`100% tests passed, 0 tests failed out of 4`，见 [ctest.log](file:///D:/eab-wt/cx-c0/reports/codex/C0_evidence/ctest.log)。计数是检查/断言数，不冒充独立数学定理数。

独立 `tools/eab2_diff.py` 通过标准库 ctypes 实际加载测试 DLL；未给 DLL 路径退出2硬失败，误用正式 DLL也硬失败，见 [hard_failure_checks.json](file:///D:/eab-wt/cx-c0/reports/codex/C0_evidence/hard_failure_checks.json)。它不在默认 pytest 收集里，Python 裁判不导入或调用 C++ 谓词、舍入和 exact helper 来生成期望值。

固定 seed=`0xEAB2C0`，随机生成器128迭代；共 **4483 样本 / 6003 个输出 bits 比较 / 0 失配**，14 操作与八公共 construction 函数全部覆盖。语料来源计数：

| 来源 | 样本 |
|---|---:|
| `boundary_matrix` | 240 |
| `fixed_seed_random` | 2432 |
| `invariance_exact_transform` | 576 |
| `r8_frozen_projection` | 53 |
| `r9_compound` | 10 |
| `r9_range_policy` | 20 |
| `r9_rounding_cells` | 1056 |
| `r9_subnormal_sqrt` | 48 |
| `r9_vectors` | 48 |

既有 Python construction 测例以数值闭式重建，并标出原文件/函数；不是宣称移植它们的几何/Dual 全套 API。576 个 exact 变换样本以固定种子的有理 SO(2) 旋转、非对称点、尺度 `2^-200/1/2^200`、平移量级0/1e3/1e5/1e6构成；AABB 对变换后点重新求界，不错误声称旋转后盒子不变。精确变换逐位核 Python，不把已舍入浮点旋转说成全域不变证明。

最终墙钟：Python oracle **0.211153s**，ctypes批（含 C ABI/核心）**0.132910s**，写JSON前总计 **0.392777s**。仅观测，不设样本配额或性能门。原始末行：

```text
EAB2_DIFF samples=4483 bits=6003 mismatches=0 status=PASS
```

原始 stdout：[diff.log](file:///D:/eab-wt/cx-c0/reports/codex/C0_evidence/diff.log)；机器结果、来源/操作计数与 DLL 哈希：[diff.json](file:///D:/eab-wt/cx-c0/reports/codex/C0_evidence/diff.json)。

### 内部语义缺陷注入

脚本复制 eab2 源码/vendor 到本单 tmp 的三份隔离副本，各只替换一个产品源码站点；真实重编译后运行同一测试。不是产出后加假记录，不以源码 hash 失败当数值门命中。原树源码及vendor哈希前后相同。三项均由目标语义断言失败，耗时 11.011s：

```text
EAB2_NUMERIC_TESTS checks=17 failed=1 detail=scalar RN cell
EAB2_NUMERIC_TESTS checks=498 failed=1 detail=difference default underflow: did not fail
ABI_TESTS FAILED: DAZ rejected (after 86 assertions)
```

分别对应 scalar ties 奇偶反转、normalized_difference 两项提前 RN 抹掉微小真差、只移除 DAZ 入口检查。见 [mutation_c0_r2.json](file:///D:/eab-wt/cx-c0/reports/codex/C0_evidence/mutation_c0_r2.json) 与 [eab2_mutation_check.py](file:///D:/eab-wt/cx-c0/tools/eab2_mutation_check.py)。**这是作者测试敏感性验证，不是独立对抗核查。**

## 7. Python、静态构造、纯度及大文件门

为遵守成本约束，开工采用快档基线、收尾仅一次四分片全档；没有为文档反复回放冻结证据。所有 pytest 均 `-p no:cacheprovider` 且显式 `--basetemp`；TEMP/TMP 在 `reports/codex/C0_evidence/tmp/` 子树。

H1 运行器仅增可选 `--evidence-root`，默认行为不变；对新证据根作工作树 reports/codex 内部校验、从字节导出中排除自身输出，仍保留节点多重集合、0 skip/failed、实际模块执行、源码未变、静态门全部约束。大文件门仅将新 `eab2` 加入无Git导出的扫描根，并在真实 eab2 文件注入超1MB缺陷测试；没有放宽1MB阈值或豁免表。

```powershell
python -X utf8 tools/h1_run_gates.py --name c0_fast --evidence-root reports/codex/C0_evidence
python -X utf8 tools/h1_run_gates.py --name c0_final --runslow --evidence-root reports/codex/C0_evidence
```

复跑须换全新 name；不覆盖、拼接中断日志。

开工快档原始末行：

```text
8689 passed, 5976 deselected in 235.56s (0:03:55)
```

收尾 H1 快档原始末行（263.062s，完整执行 8690 节点）：

```text
8690 passed in 251.72s (0:04:11)
```

四分片全档原始末行，按 shard1→4 原样保存（总计 14666 节点，runner墙钟 1450.078s）：

```text
3667 passed in 936.99s (0:15:36)
3667 passed in 778.07s (0:12:58)
3666 passed in 1298.96s (0:21:38)
3666 passed in 735.46s (0:12:15)
```

执行节点多重集合=收集节点；0 skip、0 failed；逐模块实际执行 complete；字节导出和冻结工作源码变动集合均为空。见 [summary.json](file:///D:/eab-wt/cx-c0/reports/codex/C0_evidence/c0_fast/summary.json)、[summary.json](file:///D:/eab-wt/cx-c0/reports/codex/C0_evidence/c0_final/summary.json) 与对应 module_coverage.json。

静态构造门原始末行：

```text
exact construction AST gate: 0 violation(s)
```

纯度+大文件定向门原始末行：`42 passed in 7.42s`，见 [focused_gates.log](file:///D:/eab-wt/cx-c0/reports/codex/C0_evidence/focused_gates.log)；它们也包含于最终快/全档。静态准入条目未增改，Python数值及纯度门逻辑未放宽。

## 8. 失败分类、修复记录与保留证据

- 首次配置在 ABI 测试文件仍未生成时启动，报缺源文件：输入未就绪；文件完成后重配。不是数值测试失败。
- 首次实际编译的静态 C ABI 缺 `EAB2_STATIC`，触发 dllimport 定义错误：构建策略错误；补静态 target 宏后通过。
- 交付审计最初将 CMake 的 `-MD/-std` 与8.3编译器路径误判：验证器错误；改为等价switch规范化、解析实际路径，不修改产品 flags。最终九命令审计零发现。
- 缺陷注入首轮 vcvars 嵌套引号失败：环境编排错误；改本单tmp内ASCII setup批处理，新name完整重跑，不拼接旧结果。
- 编译早期的模板名称遮蔽及常量条件警告已在自有代码中消除，未修改Boost；VS helper PATH仅在本次进程补充，不改用户环境。

失败日志保留为历史证据（build_initial/build_r1、delivery_audit_r1、mutation_c0_r1）；最终有效结果明确指向 build_final、delivery_audit、mutation_c0_r2、diff 和 c0_fast/c0_final。没有将失败运行拼成成功。

## 9. 遗留、所有者决定与交付

必做实现本轮没有已知测试失配；仍须由独立核查审视精确差分量/二次舍入、次正规与溢出胞、ties、坏环境拒绝及 ABI 内存释放。**本报告不宣称已取得 0 critical / 0 major。**

1. Claude 安排非作者独立对抗核查并达到 0 critical / 0 major。
2. 所有者按获准流程安排新鲜 worktree/克隆复现；本轮没有擅自建树，也没有用字节副本冒称新鲜 Git 验收。
3. CertifiedValue、Dual<W>、Body2 为工单可选项，全部未做；后续 C1/C3 决定，不阻塞本单必做代码验证。
4. 未做过滤、clang/gcc、负构建矩阵、每TU清单工程、E/O、LP、发布产品ABI/宿主接缝或性能门；不得外推为生产接触/力学可用。

代码入口：[README.md](file:///D:/eab-wt/cx-c0/eab2/README.md)；完整清单：[C0_delivery_manifest.md](file:///D:/eab-wt/cx-c0/reports/codex/C0_evidence/C0_delivery_manifest.md)；证据目录：[C0_evidence](file:///D:/eab-wt/cx-c0/reports/codex/C0_evidence)。

C0_PARTIAL：待Claude安排非作者独立对抗核查0 critical/0 major；待所有者安排获准新鲜树复现
