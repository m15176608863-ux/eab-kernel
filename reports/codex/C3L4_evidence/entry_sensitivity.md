# C3-L4 敏感性入口只读审计

日期：2026-10-23。源码写入须等待开工四分片基线完成；本文件仅记录基线前检查与工作接口。

## 现状与最小实现

- `eab2/src/opt.hpp` 已有原始有理标准型求解、maximize、原始模型证书验证；`statics.hpp` 已有原始 A/b/c、精确 x/y、basis 及参考点/锚点/荷载/接触快照。
- `critical.hpp` 已有 CriticalBasis2、ThresholdProof2、临界点证书、上下证书基及精确多项式延续证据；L4 不必另造阈值搜索。
- 新增 `sensitivity.hpp/.cpp`，复用 opt 和上述类型；不改变 `src/eab` 数学合同。
- C ABI 结果当前只保存 JSON，必须另外保存 typed LimitResult2/CriticalParameter2，使 L4 引用既有结果 token，而不是解析自产 JSON 或再次求解临界值。

## 私有工作接口

```cpp
namespace eab2::statics {
struct LimitSeed2 { Matrix dA; Vector db, dc; std::string parameter = "mu"; };
using SensitivityLabel2 = std::variant<std::string, ColumnLabel2>;
struct SensitivityOptions2 {
    std::string parameter = "mu";
    std::vector<SensitivityLabel2> tied_labels;
    std::vector<std::string> validity_conditions;
    bool positive_direction_valid = true, negative_direction_valid = true;
    opt::Options lp_options;
};
SensitivityResult2 evaluate_sensitivity2(const LimitResult2&,
    const std::optional<LimitSeed2>& = std::nullopt,
    const SensitivityOptions2& = {});
SensitivityResult2 evaluate_sensitivity2(const CriticalParameter2&,
    const std::optional<LimitSeed2>&,
    const std::optional<LimitSeed2>& threshold_mu_seed = std::nullopt,
    const SensitivityOptions2& = {});
std::string export_exact(const SensitivityResult2&);
}
```

调用方几何传播生成 LimitSeed2。阈值的参数种子及单位 μ 种子须在 `threshold_certificate.problem` 的精确 μ 点生成，不在 mu_max 或二分括号端点生成。缺临界点 problem 时返回未解析及空斜率。

标签必须保留类型：字符串转义为 JSON 字符串，ColumnLabel2 使用现有嵌套数组编码，不能把嵌套数组变成字符串。正式 280 条 sensitivity 中 266 条 ties 为空，14 条为阈值自动列标签，没有调用者字符串 ties。

## 数学实现核对

1. 稳定基检查完整基、秩、严格正基本变量、所有非基约化成本非零，并重新核原始 A/b/c 的原/对偶可行。固定基斜率用原始 maximize exact_y。
2. 不稳定时先核两个最优面回收锥。原侧增设 sum(r)=1；对偶先求 ker(A^T)，再以自由 y 的正负分拆、非负 slack 及 sum(slack)=1 求非零射线。任何射线都独立核非零及锥等式/不等式，再给 singular/possibly_discontinuous，无斜率。
3. Mills/Freund 每方向为一个 max LP；s 分成 s+−s−。三种子同时乘方向符号。分别核 LP 的原/对偶证书，输出右导 D+ 与左导 −D−，只在两侧有效且相等时报 smooth。
4. 闭阈使用 upper improving_ray 基，开阈使用 lower mechanism 基；先查临界矩阵与多项式分母非零、单侧延续及临界点可行。
5. 闭阈 r_B=−B^-1 A_e，B dr_B=−dB r_B−dA_e；开阈 B^T dy=dc_B−dB^T y，对每条越零列 φ=A_k^T y−c_k 求偏导。通过首个非零 Taylor 系数核指定侧越零。所有越零分量逐一处理，不按任意标签选斜率。

## 锚点约定

设计的 do=0 指常量 `reference_point=o`，不是禁止 `dof_anchor=a` 种子，和工单没有冲突。

- 接触力矩导数：`dM_anchor=(dp−da)×g+(p−a)×dg`。
- 荷载力矩导数：`dM_anchor=dM_ref−(a−o)×dF−da×F`。
- 活载始终在 A 的 alpha 列，恒载在负 RHS；两者不能混淆。
- exact_y 和 mechanism 是锚点旋量，不能再当参考点旋量计算虚功。
- `tools/tia2d_readback.py::verify_geometry_seed` 已独立由原顶点和列标签重建上述导数，不导入编码侧 helper；`tools/tia2d_seed.py` 属编码侧，不可作为唯一 oracle。

## quality 的冻结语义解释

实查 `src/eab/kernel2d/sensitivity.py`：dataclass 默认 quality=exact_jet，包含未解析/奇异输出。正式 280 条 sensitivity 全为 exact_jet：smooth 73、one_sided 2、singular 36、unresolved 169。后者原因计数为 finite_optimum_required 63、critical_basis_unavailable 19、threshold_on_domain_boundary_without_proof 78、no_valid_direction 9。

设计 §4.4 列出 quality 枚举，§4.7 规定 double 通道默认 approximate，但未规定空斜率质量降级。因此没有发现必须停工的设计冲突。与冻结 Python 裁判保持一致：quality 在空斜率返回中表示精确算术路径，不单独代表存在可认证导数。**任何非 null 斜率都必须由相应精确证书核验；unresolved/singular 的空斜率不解释成认证 jet。** 工单“只在精确证书成立时给”的限制落实于非空斜率认证，不擅改 Python 默认值或冻结语料。

## 基线前活动边界

本审计只读源码和压缩语料计数字段，未运行求解、测试或构建，未修改源码、Git 状态或任何外部工作树。读取 memory registry 未命中相关历史记录，未据历史作结论。

## 基线通过后的实现与定向结果

开工基线由主执行者确认通过后，新增 `eab2/src/sensitivity.hpp/.cpp` 与 `eab2/tests/test_sensitivity.cpp`。私有数学门最终由统一 build_r2 执行，原样末行为 `sensitivity: 263 checks passed`。具名门覆盖：原始未缩放对偶及三种子、min/max 映射、原/对偶最优面回收射线、G5 滑移/铰接/切换、活载列、方向域/尺寸、G1 开/闭阈、不同/相同越零斜率、后遇零分母时不得保留部分 jet，以及有理随机旋转/锚点剪切/单位变换。

另外新增 `tools/eab2_c3l4_meta.py`，通过发布 DLL 的公开 C ABI 从正式语料原始几何和原始种子执行 24 个变换模型、84 个通道，而非只做私有 LP 行变换。冻结期望只按量纲链式规则变换；不重新调用 Python 敏感性求解器产生期望。独立差分核验器从原始顶点与稳定标签重建 A/b/c、dA/db/dc，并核精确原/对偶或临界分量证书。

- G1 slender 与 unreversed：确定种子的随机 Pythagorean 旋转；先以几何/力单位消除奇数分母，再检查每个 ABI 输入能无损 binary64 表示；平移模长 0、1e3、1e5；长度导数按 1/s。
- G5 滑移与切换：轴掩码仅支持对应自由度轴，故用可精确重排掩码的四分之一转，不冒称任意斜向掩码支持。
- 全部四种原始模型：参考点单独移动、锚点单独移动、非零锚点种子下的零物理导数；末者实际产生非零接触矩阵与活载列导数，不能靠空种子通过。
- 小特征/大坐标角落：G5 几何尺度 1/1024 与平移模长 1e5 同时存在。
- r1 是脚本接线错误：C++ contact export 已是 assembly 索引，不应再套冻结语料 ID 解码器。已修脚本，无生产代码变化；r1 不作有效证据。
- r2 有效记录：`C3L4_META cases=24 channels=84 mismatch=0`，12.748 秒，源码前后哈希一致；暂存 `tmp/public_meta_r2.json` 与同名日志。最终报告引用主执行者整理后的唯一记录。
- 新增输入元门 `tests/test_eab2_c3l4_meta.py` 读回结果：`4 passed in 0.18s`。运行均禁 pytest cacheprovider 并显式 basetemp。

这组公开 API 元门的严格 tied_labels 语义集合比较也全部通过。它不豁免其他语料上非唯一临界基的标签差异，不代替全量差分或独立对抗核查。
