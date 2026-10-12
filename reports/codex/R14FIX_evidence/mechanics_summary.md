# R14FIX 力学分工证据（N04 / N05 与同类扫描）

## 范围与边界

本分工只改本工作树 `src/eab/limit.py`、`tests/test_r14_cone.py`、两份既有力学门的明确契约处。没有改姊妹树、没有 Git 写操作。`limit_multi.py` 无需改代码：它经单体生成器与独立列核验共用新契约。N05 的 README 正文与文档变异由主代理完成。

## N04：高摩擦方向舍入

根因：对完整分量做正确 RN-even 舍入，不等于向量整体保留库仑圆锥包含关系。旧生成器中法向分量会被巨大切向量舍掉；旧自校验只证明同一错误生成锥的 LP 正确。

- [修前红日志](file:///D:/eab-wt/cx-e2/reports/codex/R14FIX_evidence/mechanics_red.txt)：`43 failed, 20 passed in 0.26s`。其中 16 格是四个公开入口对精确超界 μ 未拒收，27 格是最终生成元严格圆锥包含失败，覆盖一般三分量法向、普通 μ、上界 μ、奇偶 k。
- 代表断言：`assert _cone_ok(ct.normal,g,mu), (j,"exact circular cone containment",g)`；oracle 只用测试侧 Fraction 多项式，不调用生产几何/构造/认证函数。
- μ 在 `LimitContact`、`friction_generators`、`contacts_from_covers`（空 covers 也检查）用 `check_mu` 精确比较 `0 ≤ μ ≤ 2^20`；多体适配继承。`2^20 + 2^-40` 不许先舍成上界再接受。已存在的非有限/负输入 `ValueError` 兼容保留。
- 最终二/三维方向逐条精确核 `n·g > 0` 与 `||n||²||g||² ≤ (1+μ²)(n·g)²`；不假定存储的浮点法向严格单位长。安全候选保持不动。最终版二维先在原 RN 候选的九个逐分量 one-ulp 邻点中，筛选有限、保留非零分量符号且精确安全者，按有理欧氏距离平方选最近者；找不到才沿原有限次内缩回退。三维内缩路径未改。不通过则具名异常。
- `u=2^-53` 时 `μu≤2^-33`、`μeps≤2^-32`。内缩单步为 `16u(1+μ)`，上界约 `2^-29`，最多八步。该估计只是分辨率依据，不代替最终精确证书。理想正 k 边形内切半径不自动成为实际内缩模型的精确下界。
- 独立自校验对实际列另用叉积平方 `||n×g||²≤μ²(n·g)²`，不是复用生成器圆锥谓词。生成器证书被删除/说谎时仍拒绝。
- `μ=2^20`、`n=(1,2,3)`、活载 `(2,-1,0)` 的独立有理容量上界通过；不会把有限圆锥容量报为无界。

## N05：非线性容量不服从一般 cos 相对界

- 初次 PowerShell stdin 写入的中文断言被编码成问号，不能算 N05 红证据；已用 `apply_patch` 修正，单独重跑得到真正目标红，完整保留并在此披露。
- [N05 真正修前红](file:///D:/eab-wt/cx-e2/reports/codex/R14FIX_evidence/mechanics_n05_doc_red.txt)：`1 failed in 0.09s`，目标断言拒绝 README 原句“承载比的相对短缺 ≤ 1−cos(π/k)”。
- [独立证书复现](file:///D:/eab-wt/cx-e2/reports/codex/R14FIX_evidence/mechanics_n05_certificate.txt) 与 [可重跑脚本](file:///D:/eab-wt/cx-e2/reports/codex/R14FIX_evidence/replay_n05_certificate.py)：与原门同一 `amp=.25` 几何，μ=1.8。候选来自 μ=1.7/k=4 的 LP，但只有测试侧确认 64 接触压缩/圆锥约束、六维精确平衡才接受为真实圆锥容量下界，不信任候选 LP 的标签。
- 认证圆锥容量下界/N=`6.865248226950123`，有限投影上界/N=`23.000000000000007`；k=5/6/7 的实际离散容量/N=`4.4094435091284128 / 4.2153362209181857 / 6.1281784305906921`。其对认证下界之比分别严格小于 `4/5,4/5,9/10`，这三个有理数又严格低于相应 cos。不存在“LP 候选本身就是 oracle”的循环。
- 正确一般陈述是理想圆锥与正 k 棱锥容量函数的 `C(μcos(π/k)) ≤ C_k(μ) ≤ C(μ)`；一般不能替换成 `C_k(μ) ≥ cos(π/k)C(μ)`。实际认证 binary64 模型只声称安全上包含。
- 原 `tests/test_limit.py` 数值断言的确断言了相对短缺，但仅在 `_LIN_MU=.2` 固定族；全部数值断言与 k 网格原样保留，只订正其 docstring 的错误一般推论。模块文档中“默认刚体旋转后 α 在 [cos,1] 相对区间变动”同类泛化也撤回。

## 同类扫描与修复

1. **二维最终舍入亦可能出锥**：新增一般法向/普通摩擦格先红，再接入同一最终物理认证。
2. **黏聚方向的舍入会引入法向力或超单位圆盘**：先红；改为内部有理正交投影，并用有理内缩保留 `n·d=0, ||d||²≤1`。黏聚 LP 旋量也保留有理系数，不再各分量浮点转换破坏切向。独立自校验另核这两条约束。
3. **黏聚上限中间显示乘积**：`_build_columns` 的 `c*A` 改为 Fraction 完整乘积，与最终 LP 精确上限一致，避免中间显示溢出/归零。
4. [同类修前红](file:///D:/eab-wt/cx-e2/reports/codex/R14FIX_evidence/mechanics_scan_red.txt)：`13 failed, 5 passed, 66 deselected in 0.16s`，4 格二维、9 格黏聚。
5. 后续入口扫描另发现空 covers 的非法 cohesion、以及调用方修改已有接触的 cohesion/area 后重验缺口，经主代理确认同属本轮范围后先红再修。新增 `_check_material`，在构造、空 covers 转接与每次 LP 列组装时重验，不替用户修改值。[修前红](file:///D:/eab-wt/cx-e2/reports/codex/R14FIX_evidence/mechanics_material_red.txt)：`11 failed, 1 passed, 85 deselected in 0.18s`。此缺口现已关闭。

## 变异：必须红在守护目标

[可重跑变异脚本](file:///D:/eab-wt/cx-e2/reports/codex/R14FIX_evidence/run_mechanics_mutations.py) 在内存中编译真实生产函数并替换关键语句，不改磁盘生产文件，不在输出后塞假值。

| 变异 | 真正失败断言 | 日志 |
|---|---|---|
| 去除 μ 域检查 | `pytest.raises(ConstructionDomainError)` 未抛 | [mu_guard](file:///D:/eab-wt/cx-e2/reports/codex/R14FIX_evidence/mechanics_mut_mu_guard.txt) |
| 最终圆锥认证恒 True | `exact circular cone containment` | [cone_guard](file:///D:/eab-wt/cx-e2/reports/codex/R14FIX_evidence/mechanics_mut_cone_guard.txt) |
| 独立静力叉积认证删除 | 注入生成器证书说谎后，静力检查未抛 | [selfcheck_guard](file:///D:/eab-wt/cx-e2/reports/codex/R14FIX_evidence/mechanics_mut_selfcheck_guard.txt) |
| 黏聚投影删除 | `cohesive force must be exactly tangential` | [cohesion_projection](file:///D:/eab-wt/cx-e2/reports/codex/R14FIX_evidence/mechanics_mut_cohesion_projection.txt) |
| 黏聚独立核验删除 | 投影注入失效后，检查器未抛 | [cohesion_selfcheck](file:///D:/eab-wt/cx-e2/reports/codex/R14FIX_evidence/mechanics_mut_cohesion_selfcheck.txt) |
| 材料使用时重验删除 | 可变接触被改成负 cohesion 后未抛 | [material_recheck](file:///D:/eab-wt/cx-e2/reports/codex/R14FIX_evidence/mechanics_mut_material_recheck.txt) |

全部变异 pytest exit=1，且是指定目标断言，不是导入/收集失败。N05 README 旧句恢复变异由主代理记录。

## 既有测试改写台账

- `test_r13fix_mechanics_differential.py` 两个摩擦门：保留全部 μ/k 原格。`μ=2^1022` 格改成按所有者新分项域严格拒收，不删格；其余原始完整分量候选的独立有理与 RN-even 门仍逐值断言；新增最终方向最小认证收缩的独立逐值参考、安全不等式与偏移上界。既有“提前舍入乘积”真实函数内变异仍捕获目标断言。
- `test_limit.py` 只改 docstring；没有改任何原数值断言。
- 没有 skip/xfail、删门、放松容差或缩参数网格。

## 验证

- [573 项力学门](file:///D:/eab-wt/cx-e2/reports/codex/R14FIX_evidence/mechanics_green3.txt)：`573 passed in 58.71s`。覆盖 R14/R13 力学差分、limit、contacts、exact_selfcheck、multi、scale、selfcheck。
- [最后定向门](file:///D:/eab-wt/cx-e2/reports/codex/R14FIX_evidence/mechanics_final.txt)：`148 passed in 1.48s`，包含后加黏聚独立 checker 门以及去除 map 的等价改写。
- [第一轮源码冻结验证](file:///D:/eab-wt/cx-e2/reports/codex/R14FIX_evidence/mechanics_freeze.txt)：`247 passed in 2.67s`，包含空 adapter 与可变 material 重验及 R14/R13 力学、contacts、multi 既有门；其后完整仓库运行发现的二维近自锁退步及最终修复见下一节，不能用本定向绿遮盖它。
- 所有 Python 命令使用 `PYTHONDONTWRITEBYTECODE=1 python -X utf8`，pytest 禁 cacheprovider，basetemp 位于本树证据目录。
- 本分工绿不是全仓退出证书；全仓、指针同步、README 变异与最终状态以主报告为准。
- [定量文字交叉复核](file:///D:/eab-wt/cx-e2/reports/codex/R14FIX_evidence/quantitative_claim_review.md) 另查 README/设计的现行与历史推论；补 face_noise 原句 `(2u+u²)` 严格门 `tests/test_r14_claims.py`，旧门不动。[4 项通过](file:///D:/eab-wt/cx-e2/reports/codex/R14FIX_evidence/quantitative_claim_tests.txt)，并有 [8u 内部偏置目标红](file:///D:/eab-wt/cx-e2/reports/codex/R14FIX_evidence/mechanics_mut_noise_constant.txt)。

## 完整回归后的二维精度返修（最终版）

第一轮全仓发现两条既有近自锁闭式精度门失败：`test_lp_certificates.py::test_near_self_locking_is_certified_within_its_reported_uncertainty_or_loud` 的 margin=`1e-8,1e-9`、旋转 `.37` / 平移 `(30000,-2000)` 格。初版统一 `16u(1+μ)` 内缩虽然保证安全，却在二维近自锁分母上引入过大的保守偏差；原状态和精确 LP 证书正确，但误差超出旧门要求。没有改旧门、提高 uncertainty、skip 或以“安全就够”掩盖精度退步。

仅把步长改小的内存实验虽通过原28格，但小 μ 下逐分量不变，5000随机格中56格在有限步后响亮拒答，故未采用。最终方案仅改变二维：对原 RN 候选每一分量枚举本值、`nextafter(-inf)`、`nextafter(+inf)`，在最多九个组合中用精确圆锥证书筛选，再选距离平方最小者。非有限值、把原非零分量变零或反号者排除；没有安全邻点才用原回退。距离参照的是原 **RN** 候选，因二维调用方在进入认证函数之前已做完整表达式单次 RN。三维仍传精确候选并使用原认证内缩，三维全部原独立逐值参考未变。

- [新24格修前红](file:///D:/eab-wt/cx-e2/reports/codex/R14FIX_evidence/two_d_neighbor_red.log)：`6 failed, 18 passed, 98 deselected in 0.16s`，其中5格旧输出不是最近安全邻点，1格旧粗步无法分辨小 μ 而拒答。
- 新 oracle 使用直接 Fraction 二维行列式 `det(n,g)²≤μ²(n·g)²` 与独立候选表达式，不调用生产认证或切向构造；逐值核选中的最近 one-ulp 邻点，补齐二维最终值的严格参考。
- [修后相关356格](file:///D:/eab-wt/cx-e2/reports/codex/R14FIX_evidence/two_d_neighbor_green.log)：`356 passed in 22.32s`，覆盖所有旧28近锁格、新R14、原R13力学差分、整份 LP certificates。
- [内存实验数据](file:///D:/eab-wt/cx-e2/reports/codex/R14FIX_evidence/two_d_neighbor_experiment.json)：5000一般法向/μ格全部有精确安全结果、无拒答；原两失败格相对误差降为 `3.236038390133251e-9 / 3.2645067698293085e-8`，原 uncertainty 仍约 `6.27306e-8 / 6.27306e-7`，没有放大。
- [删除邻点分支的变异](file:///D:/eab-wt/cx-e2/reports/codex/R14FIX_evidence/two_d_neighbor_mutation.log)：`1 failed in 0.12s`；红在原 `assert abs(r.alpha - exact) <= (r.uncertainty + 1e-9) * exact`。新增变异门沿最后 traceback 读源码语句并确认该原断言，不能把状态或 uncertainty 的偶然失败算成功。

最终源/测试已再次冻结，完整重跑与耗时以主报告为准。
