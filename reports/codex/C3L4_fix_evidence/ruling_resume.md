# Claude 裁定：续 WO-C3L4-fix（2026-10-23）

这是对本单搜索域反例的明确裁定，原工单其余全部条目继续实施；同一工作树，不commit。

1. 定理另要求在同一K中核 `0 <= mu*+(s-eta)epsilon` 与 `mu*+(s+eta)epsilon <= mu_max`，mu_max必须原始搜索上界。内点自动成立；mu*=mu_max时要求s<0，mu*=0时要求s>0。(a)(b)加这两域条件才推出D+=s；反向同法。amendment按此写并收入本单反例。
2. 域条件不成立的方向一律unresolved，reason=`threshold_search_domain_boundary`，不要求另证空集；不采用扩展实数，不用域外斜率。
3. mu*=0,s<=0保守不认证，同reason。不新增域下界钳制为0的合同，记遗留。
4. Python/C++ CriticalParameter2保留结果/证书显式绑定原始mu_min=0、mu_max；输入binary64原值与精确有理同记。不得用收窄后的mu_lo/hi顶替。新增critical输出字段，旧字段不变，并在差分比较；此src/eab改动已授权。
5. K矩阵必须从原始几何和种子重建(mu,epsilon)完整多项式：顶点、锚点、荷载仿射；接触点/T/N/g/moment/load moment按原公式展开。不许从dA/db/dc逆推。C++内部保留primitive/path，公开结构布局不变；若需公开布局变化先报告。
6. 继续原WO-C3L4-fix全部实现、回归、语料与errata、非对称与红旗、变异、小项、完整构建/六层（含L3全集）/release ABI/consumer/fast/full4片。域规则引起的原认证值退化逐条errata计数。

执行计划：沿用刚完成且源未改的开工15193四片基线，不重复计成本；先冻结内部路径/branch_certificate输出合同，再并行Python/C++/独立checker/ABI小项，定向门迭代，最后冻结源码统一完整验收。原停止实施记录与反例保留为历史，不改成当时已实现。
