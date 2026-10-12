# R14FIX 定量文字—测试语义交叉复核

本次是修复团队内的只读交叉检查，不是独立 G6。范围：README、`docs/plan_20260921.md`、`docs/canon_map.md`、`docs/exact_predicates_plan.md`、`docs/r14fix_design_sync.md`；检索 cos / inradius / 相对短缺 / 相对误差 / 夹逼 / 倍数 / 上下界，随后读对应测试断言，而非只确认测试文件存在。行号以后续指针工具结果为准。

## 逐项结果

| 声称 | 现行/历史/限定族 | 检查了什么 | 结论 |
|---|---|---|---|
| README L3 的一般相对短缺 ≤1−cos | 原错误一般推论；本轮已撤回 | `test_limit.py` 固定 `_LIN_AMP=.25, _LIN_MU=.2`；确实断相对短缺，但不是全 μ。新 `test_r14_cone.py::test_nonlinear_capacity_has_no_universal_cosine_relative_error_bound` 对 μ=1.8 给精确静力证书反例 | 已订正；不能再把旧固定格说成一般定理 |
| 理想正 k 棱锥 `C(μcos)≤C_k≤C(μ)` | 当前数学陈述，明确理想模型、相同几何/荷载/黏聚模型 | 单个接触凸锥包含按积集与线性平衡约束保持，容量目标单调；不需要容量对 μ 线性 | 推论成立；实际向内修正 binary64 射线只逐条认证上包含，README/设计已明确不继承理想内半径 |
| `docs/plan_20260921.md` 原计划的“误差≤1−cos、大 k 更小” | 09-21 历史计划 | 顶部 R14 注释已声明只能作固定低摩擦格断言；`test_limit.py` 实际只比较 `(14,18,22)` 与 `(5,6)` 包络，没有断每一步 k 单调 | 历史保留合理，不可当当前普遍误差定理；现行非单调措辞吻合 |
| canon_map A.9 的 `cos(π/k)*full ≤ α ≤ full` | 历史命令与限定纯滑动族 | `_cohesive_block` 的四个水平接触、活载在基面、无倾覆；`full=μW+ΣcA`，圆盘能力相加，正多边形径向界适用。测试实际含 `1e-9` 裕量 | 不属于 N05 的一般互锁容量错误；实际舍入模型只在这个已测族/容差内通过，不能推广成逐位等式 |
| README 两块叠放 `min(μW₂,W₂,(W₁+W₂)/h)` | 指定二维叠放几何族 | `_stack_2d` 还写了 `μ(W₁+W₂)`，对非负 W₁ 该项不小于 μW₂，可删；`test_two_stacked_blocks_match_the_closed_form` 用同一 min 逐格比较 α，含倾覆与滑动换支 | README 数学省略正确；不是仅核 selfcheck |
| README cb2 `μW / W / √2W`、单位缩放不变 | 真夹具几何、指定荷载族 | `test_end_to_end_cb2.py` 相应门直接比较闭式，边界 μ=1 与 μ=√2，单位门比较 α（恒活荷载同时缩放），不是误除 load_scale | 当前声称与断言一致；README 明示 1e-9，而非逐位相等 |
| README 五/七块拱的最优四铰上限 | 指定 ARCH5/ARCH7、高摩擦参数族 | `test_high_friction_arch_collapses_by_the_best_hinge_mechanism` 的参考来自 Fraction 链相容方程与虚功，比较 α 与枚举最小者；另核机构容许 | 当前限定比较成立；“480/2240、10/28”是记录的枚举计数，不应冒充被当前测试逐个断死（计数门只要求 ≥2） |
| canon_map 膨胀法向 Lipschitz ≤2/δ | 凸集且离集距离≥δ 的数学上界 | 文档明确用坚定非扩张推出 I−P 非扩张，再用单位化不等式；`test_margin.py` 实际断局部/闭环/全局商上界与局部≥.9/δ | 文档推导成立；有限探针是实现回归，不是全域数学证明。文档已说实际探针紧值约1/δ，2/δ是松界，没有错称2/δ紧 |
| D400 差≤2^401、双线性项≤2^800、三次项可到2^1200 | 输入盒的代数计数 | 各自只指原始输入一次差/单项乘积；文档另外明示相消、除法、派生量不由盒自动保障 | 计数正确，不是“盒内任何输出可表达”承诺；R14 分项优先注已覆盖 μ/角度/文本 |
| face_noise 正规误差界 `(2u+u²)abs(R)` | 当前纸面误差推导 | 每条正边长53位近似、精确和、精确比例、最终RN，纸面两阶段 `(1+u)^2−1` 推导成立；原命名测试实际给 `delta=3u*4` 的更宽独立根式包围 | 曾缺原句常数门；本轮新增 `test_r14_claims.py::test_face_noise_obeys_the_documented_two_rounding_relative_bound`，保留三个原尺度，以 Fraction 两侧有理平方直接断原句；8u内部偏置变异确实击中该严格常数。缺口已闭合，旧宽门未动 |
| μ≤2^20、μeps≤2^-32 与安全圆锥 | 当前分项合同 | 新门包括精确超界分数、普通/高摩擦、非轴法向、最终方向有理不等式、独立叉积checker与移除关键步骤变异 | 界是分辨率政策，不是单独安全证明；设计明确另需精确证书，措辞与实现一致 |

## 不应过度解释的部分

- `test_limit.py` 原纯滑动 181 方向门有上下端采样分辨率断言，不只是 “大 k 更准”；该限定族的数学径向界可以保留，不能跨到一般互锁/倾覆容量函数。
- 当前文档仍含大量带日期的失败格数、误差倍数、旧提交复跑输出；它们是历史证据，不宜根据当前行为静默重写。README 的 2.12 倍旧错误属于明确的 M0 前历史，不是当前误差上界。
- README 当前已明确独立 G6 待复审；本文件不把通过回归门等同于独立退出。
- 本检查未逐一重新证明全部几何定理或枚举无限参数。没有发现新的已复现数学反例；发现的 face_noise 常数—门不匹配已经补门，不用“未发现数值反例”掩盖曾有的证据缺口。

## face_noise 原句补门证据

对解析直角等腰三角形，令 `r=face_noise/2^-46`、精确目标 `T=2+√2`、`d=2u+u²`。
原句 `|r−T|≤dT` 等价于 `r/(1+d)≤T≤r/(1−d)`。两端都是有理数，减去2后在正确符号侧平方与2比较；整个 oracle 不调用生产根、范数或几何原语。

- [严格门输出](file:///D:/eab-wt/cx-e2/reports/codex/R14FIX_evidence/quantitative_claim_tests.txt)：`4 passed in 0.05s`。
- [内部偏置变异输出](file:///D:/eab-wt/cx-e2/reports/codex/R14FIX_evidence/mechanics_mut_noise_constant.txt)：`1 failed in 0.06s`；失败正是 `documented 2u+u^2 relative bound: lower side`，不是环境或收集错误。
- 生产实现未为此改动；旧宽界测试未删除/改写，新门只增强验证。

## 可复核入口

- [力学详细证据](file:///D:/eab-wt/cx-e2/reports/codex/R14FIX_evidence/mechanics_summary.md)
- [N05 精确反例输出](file:///D:/eab-wt/cx-e2/reports/codex/R14FIX_evidence/mechanics_n05_certificate.txt)
- [现行分项设计合同](file:///D:/eab-wt/cx-e2/docs/r14fix_design_sync.md)
