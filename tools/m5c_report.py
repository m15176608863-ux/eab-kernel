"""Render the Chinese M5c report only from completed, verified evidence."""
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports/codex/M5c_evidence"
READ_HASHES = {}


def read_path(path):
    data = path.read_bytes()
    READ_HASHES[str(path)] = hashlib.sha256(data).hexdigest()
    return json.loads(data.decode("utf-8"))


def read(name):
    return read_path(OUT / name)


def check_sources(summary, require_end=False):
    hashes = summary["source_hashes"]
    assert hashes, "empty source binding"
    if require_end:
        assert hashes == summary["source_hashes_end"], "source start/end mismatch"
    # H1: source hashes remain historical attribution metadata only.
    # Report inputs and semantic counts retain their independent checks.


def validate_claims(suite, model, research, admission, teeth, review, endpoint, base, diagnostics, initial, legacy):
    """Reject stale narrative numbers rather than silently print a canned conclusion."""
    assert all(d["complete"] is True for d in (suite, model, research, admission, teeth, review, endpoint, base, initial, legacy))
    assert suite["audit"] == "GREEN" and suite["skip_count"] == 0
    assert suite["collected"] == suite["executed"] and suite["collected_equals_executed"] and suite["all_stages_passed"]
    assert len(suite["shards"]) == 4 and suite["static_last_line"] == "exact construction AST gate: 0 violation(s)"
    assert not suite["executable_source_drift"] and suite["source_unchanged_during_execution"]
    assert suite["audit_input_hashes"], "execution audit lacks raw bindings"
    for path, expected in suite["audit_input_hashes"].items():
        assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected, "stale raw execution evidence"
        READ_HASHES[path] = expected
    for summary in (model, research, endpoint, base, initial):
        check_sources(summary, require_end=True)
    for summary in (teeth, review):
        check_sources(summary)
    c = model["counts"]
    expected = {"pairs": 64010, "comparison_basis:EXPLICIT_TRAJECTORY": 14079,
                "comparison_basis:CONSTRUCTED_INITIAL_OVERLAP": 16676,
                "comparison_basis:CONSTRUCTED_INITIAL_CONTACT": 213,
                "comparison_basis:CERTIFICATE_DIRECT": 33042,
                "p1_p2_explicit_same": 14079, "explicit_new_contact_pairs": 68,
                "independent_initial_state_evaluations": 30968, "production_initial_state_crosschecks": 14292,
                "ROBUST_SINGLE_FIRST_COVER": 19, "INITIAL_EXIT_ORDER_UNCERTIFIED": 16676}
    assert all(c.get(k, 0) == v for k, v in expected.items()), "narrative comparison/count contract drift"
    assert c.get("p1_p2_explicit_different", 0) == 0
    assert sum(c[k] for k in ("ROBUST_NO_CONTACT", "ROBUST_SINGLE_FIRST_COVER", "MODEL_SENSITIVE_OR_UNPROVED")) == c["pairs"]
    assert research["counts"] == {"traversed_pairs": 64010, "r2_pass": 2, "r3_pass": 19, "certified_union": 19, "recomputed_pairs": 68, "traversed_steps": 1810}
    assert model["exact_observation_pairs_compared"] == 64010 and len(model["candidate_join"]) == 68
    assert sum(row["candidates"] for row in model["by_case"].values()) == 68
    assert sum(row["r2_single_cover"] for row in model["by_case"].values()) == 2
    assert sum(row["certified_union"] for row in model["by_case"].values()) == 19
    assert model["initial_overlap_references"]["pairs"] == 16676
    assert model["initial_overlap_references"]["certified_exit_pairs"] == 0
    assert teeth["collected"] == teeth["executed"] == 49 and teeth["skipped"] == 0
    assert teeth["mutation_count"] == 22 and teeth["hash_guards_selected"] is False
    assert all(row["passed"] for row in teeth["tests"])
    assert review["false_certificates"] == 0
    assert [review[k] for k in ("nominal_cases", "signed", "perturbation_probes", "independent_vertex_affine_probes", "simple_ring_candidates", "simple_ring_signed", "independent_simple_ring_probes", "structural_counterexamples")] == [90, 23, 920, 138, 80, 38, 760, 6]
    assert admission["admitted_rule_site_net_delta"] == 0 and admission["policy_bytes_unchanged"] is True
    for label in ("baseline", "current"):
        assert [admission[label][k] for k in ("effective_rule_site_count", "per_site_or_overlap_count", "shared_marginal_rule_site_count")] == [3391, 3314, 77]
    assert len(diagnostics) == 68 and sum(bool(row["r2_pass"]) for row in diagnostics) == 2
    failed = Counter()
    for row in diagnostics:
        if not row["r2_pass"]:
            trial = row["r2_trials"][-1]
            failed.update(set(trial["p1"]["failed"]) | set(trial["p2"]["failed"]))
    assert failed == {"early_separation": 64, "strict_convexity": 31, "competitor_EV": 5, "endpoint_begin": 5, "endpoint_end": 1}
    assert initial["counts"]["g0_trials"] == 523 and initial["counts"]["initial_contact_witness"] == 3
    assert initial["counts"]["nominal:strict_convex/strict_convex"] == 37 and not initial["certified_counterexamples"]
    refs = model["candidate_references"]["certified_union"]
    for phase in ("raw_df05", "post_df06"):
        def value(name):
            return refs.get(phase+":"+name, 0)
        assert value("FIRST_COVER_MATCH") + value("OTHER_REFERENCE") == 38
        assert value("SECONDARY_FIRST_COVER_MATCH") + value("SECONDARY_OTHER_REFERENCE") == 0
        assert value("SHARED_EDGE_FIRST_COVER_MATCH") + value("SHARED_EDGE_OTHER_REFERENCE") == 25
        assert value("SECONDARY_REFERENCE_TOTAL") == value("UNPROVED_SECONDARY_REFERENCE") == 12
        assert value("ALL_FIRST_COVER_NOT_SELECTED") == value("ROBUST_CONTACT_MISSING_PAIR") == 0
        assert value("FIRST_COVER_MATCH") == (7 if phase == "raw_df05" else 19)
        assert value("ROBUST_FIRST_COVER_NOT_SELECTED") == value("FORMAL_ALL_FIRST_COVER_NOT_SELECTED") == (12 if phase == "raw_df05" else 0)
        assert [legacy["counts"][phase+":"+key] for key in ("primary", "VV_SECONDARY", "VALID_SHARED_EDGE_SLOT", "false_secondary_with_old_m4_guard")] == [141594, 7768, 32075, 49218]
    assert legacy["counts"]["steps"] == 1810 and not legacy["mismatches"] and legacy["production_crosschecked"]
    assert endpoint["block_frames"] == 15220


def main():
    READ_HASHES.clear()
    suite = read("execution_audit.json")
    model = read("combined_summary.json")
    research = read("research_summary.json")
    admission = read("admission_rule_sites.json")
    teeth = read("semantic_teeth.json")
    review = read("review_r3.json")
    endpoint = read_path(ROOT / "reports/codex/M5b_evidence/endpoint_summary.json")
    base = read_path(ROOT / "reports/codex/M5b_evidence/robust_summary.json")
    diagnostics = read("research_diagnostics.json")
    initial = read("research_initial_tube_witnesses.json")
    legacy = read("a5_independent_legacy_audit.json")
    validate_claims(suite, model, research, admission, teeth, review, endpoint, base, diagnostics, initial, legacy)
    old_endpoint = read("endpoint_summary_before.json")
    assert endpoint["maxima_exact"] == old_endpoint["maxima_exact"], "endpoint exact extrema changed"
    c, references = model["counts"], model["candidate_references"]["certified_union"]
    n = c["ROBUST_SINGLE_FIRST_COVER"]
    assert n == research["counts"]["certified_union"] == 19
    case_table = "\n".join(f"| {case} | {row['candidates']} | {row['r2_single_cover']} | {row['certified_union']} | {row['candidates']-row['certified_union']} |"
                           for case, row in sorted(model["by_case"].items()))
    ref_table = "\n".join(f"| {phase} | {n-references.get(phase+':ROBUST_FIRST_COVER_NOT_SELECTED', 0)}/{n} | {n-references.get(phase+':FORMAL_ALL_FIRST_COVER_NOT_SELECTED', 0)}/{n} | {n-references.get(phase+':ALL_FIRST_COVER_NOT_SELECTED', 0)}/{n} | {references.get(phase+':ROBUST_CONTACT_MISSING_PAIR', 0)} |"
                          for phase in ("raw_df05", "post_df06"))
    last_lines = "\n".join(row["last_line"] for row in suite["shards"])
    perf = suite["performance"]
    exit_refs = model["initial_overlap_references"]["references"]
    exit_table = "\n".join(f"| {phase} | {exit_refs.get(phase+':PRIMARY_REFERENCE_TOTAL', 0)} | {exit_refs.get(phase+':SECONDARY_REFERENCE_TOTAL', 0)} | {exit_refs.get(phase+':SHARED_EDGE_SLOT_TOTAL', 0)} |"
                           for phase in ("raw_df05", "post_df06"))
    text = f"""# WO-M5c 中文交付报告

## 0. 结论与范围

**A1–A7 已完成；B 的严格充分条件与全时程扩证完成，稳健单首盖由 2/68 提高到 {n}/68；C 保持 PARTIAL。**

- 基线 `efb0dfe514a1f60c44e6341b69cce77ff5c9ec17`，初态工作树干净。只写本工作树，未执行 commit / push / reset / checkout / stash / worktree / branch。
- 新鲜字节导出四片 **{suite['collected']} 收集 = {suite['executed']} 执行，0 skip，全绿**；静态 0 违例。反事实逐站准入 **{admission['baseline']['effective_rule_site_count']} → {admission['current']['effective_rule_site_count']}，净增 {admission['admitted_rule_site_net_delta']}**，policy JSON 原字节未改。
- 扩大后稳健无接触 {c['ROBUST_NO_CONTACT']}，稳健单首盖 {n}，未证 {c['MODEL_SENSITIVE_OR_UNPROVED']}，总计 {c['pairs']}。68 个新接触里仍有 {68-n} 个未证，不外推。
- 所有认证只针对规定的连续顶点 L∞ 管及 P1/P2/P3 指定族，不是未知真实物理路径、工程验证或求解器切换授权。
- C 未实现边界特征存续核验，16676 个初态贯入对的正半径出口排序仍全部未证；不伪造稳健 PD 子集结论。

关键证据：[交付总清单](file:///D:/eab-wt/cx-e2/reports/codex/M5c_evidence/DELIVERY_INDEX.md)、[完整联合摘要](file:///D:/eab-wt/cx-e2/reports/codex/M5c_evidence/combined_summary.json)、[逐对诊断](file:///D:/eab-wt/cx-e2/reports/codex/M5c_evidence/research_diagnostics.json)、[执行审计](file:///D:/eab-wt/cx-e2/reports/codex/M5c_evidence/execution_audit.json)。

## 1. 理论先行、oracle 与数值合同

先行文档：[A 补牙理论](file:///D:/eab-wt/cx-e2/docs/m5c_teeth_theory.md)、[R3/C1 定理与边界](file:///D:/eab-wt/cx-e2/docs/m5c_research_theory.md)、[数值合同 inventory](file:///D:/eab-wt/cx-e2/docs/m5c_numeric_inventory.md)。

R1/R2 原生产几何公式未改。A 主 oracle 只导入 `fractions.Fraction`，独立枚举刚体平移的线性入射方程、闭边投影与有理复数旋转；不导入生产几何/求根/区间原语。公式预算另用字面向量独立双线性展开。`pytest`、`mutation_support`、Path/JSON 属设施或被测接线，不冒充几何 oracle。

R3 主 oracle 是独立闭式凹环平移；对抗 oracle 使用 Fraction 的线性/二次事件与独立隔离、独立线段相交。随机仅用于构造输入，判定仍精确。主路径不使用 float 阈值；Decimal 只生成诊断显示。元门含非轴有理旋转、大平移至 1e6、极小/极大单位尺度，旋转管按诱导 L∞ 范数保守变换。

## 2. A 逐条完成情况与真实内部变异

| 工单 | 处置与具名门 | 变异结果 |
|---|---|---|
| A1 早期窗口 | `test_r2_complete_early_window_rejects_prior_penetration`：三次往返平移，早期真实首盖与晚期提名标签不同 | skip 与 half-window 均红在首盖语义拒绝断言 |
| A1 全竞争者 | `test_r2_ev_competitor_precedes_nominated_ve`：正确 EV 首时刻 0.3，错误 VE 为 0.5 | 只查 VE、不查 EV 必红 |
| A1 双边内投影 | `test_r2_both_edge_projection_sides_reject_line_extension`，上下两侧各一反例 | 各漏一侧均错误签发并被门杀死 |
| A1 全分段 | `test_r2_final_panel_rejects_departed_edge_endpoint`，真实整窗无接触 | 漏最后一段必红 |
| A2 r2 | `test_replay_endpoint_residual_r2_prevents_false_no_contact`，模型误差其他项为零但端点残差为 1 | 删除 r2 会错误签无接触；语义门红 |
| A3 L1 / 双盒 | `test_r1_linf_tube_uses_dual_l1_normalization`、`test_replay_p2_box_cannot_be_replaced_by_p1_box_only` | L1 改 L∞、只查 P1 两项均红 |
| A4 误差项 / 严格性 | `_event` 两预算各三项、凸性三项；竞争/凸性等号；近阈值接受格 | 九项删减与两项非严格化均由预算/拒绝语义断言杀死 |
| A4 真 oracle | 原恒真断言替换为 oracle 首标签/首时刻核对生产 label/bracket | 内部返回错误 label 与 bracket 均红 |
| A5 口径 | 比较来源四分列、G0 求值/生产交叉核对分列、稳健 reason 清理、主/次/共边槽分列 | 新计数门与真实 bb03/锁长反例门通过 |
| A6 审查域 | 代码固定 13 脚手架规则、4 个既有测试变异文件；活动 review 指纹单独 pin | 扩大规则/生产路径/任意测试路径/路径穿越的追加审查均拒绝；4 个内部 guard 变异均红 |
| A7 闭包 | endpoint {len(endpoint['source_hashes'])} / robust {len(base['source_hashes'])} 个实际运行时传递文件，首尾各采一次 | 每个文件 scratch 字节变异拒绝；独立 `__spec__.origin` 集合 oracle 另杀内部漏依赖变异 |

A1–A4 专项收集=执行={teeth['collected']}，0 skip，**{teeth['mutation_count']} 个真实内部变异全 kill**。仅运行具名语义驱动，源码哈希/冻结摘要绊线未被选入；没有在枚举产出后塞假数据。近阈值端点余量/误差为 `1/199999`。误差项门核对预算表达式，不冒称每次删项都已经构造实际错轨迹。

完整逐项记录：[22 项变异表](file:///D:/eab-wt/cx-e2/reports/codex/M5c_evidence/semantic_teeth.md)、[A6/A7 记录](file:///D:/eab-wt/cx-e2/reports/codex/M5c_evidence/binding_work.md)、[共享/闭包独立复核](file:///D:/eab-wt/cx-e2/reports/codex/M5c_evidence/review_binding.md)。

### 2.1 口径订正后的分母

- **实际 P1/P2 轨迹比较：14079 对，其中 68 对本步新接触，身份/状态差异 0/14079。**
- 构造上由共同初态必然相同：16889 对 = 16676 初态贯入 + 213 初态接触。
- 双盒严格证书直接判定无接触：33042 对。三项互斥相加为 64010，不再宣传“实测 0/64010”。
- 独立 G0 求值 30968 对，其中 **14292 对与两生产入口交叉核对、零失配**；另 16676 由 G0 直接分类，不冒充交叉验证。
- M5b 原 §6.1 已明确 **n=2/68，不可外推**；本次才扩到 19/68。
- bb03 第15步 (8,11)：raw 主参考不是首盖，但**同一 raw 行 m4–m6 共边槽就是首盖**，不能说全部可用槽漏掉首盖。

### 2.2 参考槽修复与真实重算

独立审查抓到本次初版把 `m4>0` 的普通 VE 锁长提示当第二参考的 major。`robust_full_m5c_r1` 整批作废并终止 worker，未发布、未拼接；修复后 `robust_full_m5c_r2` 从头真实运行。

- 正式 VV 二参：`mtype==1 && m4>0`；raw 实顶点编号 ≥1，0 为垫位；正 raw 编号经周期规范化后可以映射到合法边端 ID 0。原“raw 实顶点 ID 0”的理由撤回。
- VE 共边入口槽：`mtype==0 && m6>0`；普通 VE 的零尾锁长提示排除。
- 完整槽再检查：顶点在对块，边为同块相邻、非退化且属当前块对；坏完整槽响亮拒绝。
- 只读核对 `D:/b-DDA/df/df.c`（代码 hash/行号入证据），对全部两阶段 283188 行独立周期 ID oracle 零失配。每阶段主参考141594、VV二参7768、共边槽32075；先前各49218条锁长提示不再伪造二参。

[逐行独立审计](file:///D:/eab-wt/cx-e2/reports/codex/M5c_evidence/a5_independent_legacy_audit.json)；[首轮发现与修后复核](file:///D:/eab-wt/cx-e2/reports/codex/M5c_evidence/review_a5.md)。

## 3. B：诊断、收紧证书与扩大后的答案

### 3.1 为什么原来只有 2/68

68 对中 37 对两环名义严格凸，31 对至少一凹环。原 R2 的失败不只是半径太大：先对绝对顶点分别包络再相减会丢掉共同运动相关性；全局严格凸条件直接排除凹环；有限固定法向与固定粗窗口也会保守。

对原66个未证格，在最窄原候选窗口检查（子条件可重叠，不能相加）：早期分离64、严格凸性31、竞争EV5、起端符号5、终端符号1。全部三个 pad、P1/P2、每个块对的失败条件、扣误差余量和余量/误差比均存于 [68 行诊断表](file:///D:/eab-wt/cx-e2/reports/codex/M5c_evidence/research_diagnostics.json)。`margin_over_error` 是扣费前 margin/error，`surplus` 是扣费后严格余量；误差为0时比值记null，不伪装有限值。名义导数与混合单位简单环门不强造无量纲比。

另做523次独立 G0 管内初态反例查询，3对允许常量管内 s=0 已接触（bb03 step1 (10,11)、bbF038/ bbS038 step1 (1,2)）；19获证对子集无反例。这只反证宽常量管的统一保证，不是实际共享初态 P3 发生差异；65对没搜到反例也不证明稳健。[初态管诊断](file:///D:/eab-wt/cx-e2/reports/codex/M5c_evidence/research_initial_tube_witnesses.json)。

### 3.2 R3 定理与证明状态

1. 先在有理多项式环计算同时间相对向量 `(Np Dq-Nq Dp)/(Dp Dq)`，然后包络；共同平移相关项可精确消去。
2. 每个子窗的固定法向可取该窗中点边法向；所有顶点对投影差的严格下界扣 L1 对偶管预算后为正，证明整窗两凸包分离。中点只生成候选，不用采样代替证明。
3. 在接触括区逐窗证明边不退化、非邻边不交、邻边不倒折，保证任意管内配置为简单环，允许凹环。
4. 端点严格异号、两侧边内投影严格正、所有 VE/EV 竞争事件排除，推出首次接触只能是指定单标签。**不要求扰动可微，不认证唯一根或首时刻不变。**

这比 R2 更紧但仍只是充分条件。近切、VV、并列、零余量、自交、未知初态路径均不强行签发。`δF/m` 若只取根一点导数，没有整个移动走廊下界，就不是证明。

独立对抗：90个名义构造23获证；920条逐顶点常值扰动同时核首标签与括区，138条非刚体首末线性扰动仅核状态/首标签（未另核首时刻括区），均0错；80个简单环候选38获证、760次独立段相交核查，0错；6个结构反例均拒绝。90个名义轨迹的分母均为常量1，不能把这些数冒称非恒定分母P2的完整时刻扰动验证。测试通过是有限核查，连续管结论依据上述定理。[独立复核](file:///D:/eab-wt/cx-e2/reports/codex/M5c_evidence/review_r3.md)。

### 3.3 1810 步的两阶段完整覆盖

第一阶段：新 `robust_full_m5c_r2` 实际从头运行1810步/64010对，{base['seconds']:.3f}秒，完整{len(base['source_hashes'])}文件运行时闭包首尾一致。
第二阶段：研究 `research_recert_r4` 遍历全部1810步/64010对，重新求解全部68个新接触候选的 P1/P2 与 R2/R3，{research['seconds']:.3f}秒。**不是第二次全部块对 P2 求根**。
联合发布器按原始冻结 endpoint 每步块身份核验全组合覆盖，新旧64010对的状态/标签/精确时间逐项相同；新鲜68候选与研究 exact/compact 全连接，再逐对替换分类与参考计数。没有从历史只挑19个阳性来充当全集重跑。

| 算例 | 新接触候选 | 原R2 | R2∪R3 | 仍未证 |
|---|---:|---:|---:|---:|
{case_table}
| 合计 | 68 | 2 | {n} | {68-n} |

### 3.4 重新回答 legacy 命中与漏检

分母均为**19个已认证步—块对**，不是参考行数：

| 阶段 | 主参考命中 | 主参考+正式VV二参命中 | 再含有效共边入口槽命中 | 完全无该块对记录 |
|---|---:|---:|---:|---:|
{ref_table}

这19对的正式 VV 二参为0；68候选全集有12条 VV 二参，均在未证格，不能据其推断稳健命中。19对子集每阶段38条主参考、25条共边槽：raw 主参考7条首盖/31条其他；post 主参考19条首盖/19条其他。raw 有12个块对未把首盖选作主参考，但其有效共边槽命中；**共边槽本身不另作独立弹簧参考；df06 换半后的主参考属于随后 df07 / 弹簧装配所用的表，共边槽还影响换半与接触长度，实际激活仍受开闭状态控制**。该子集0块对漏检，不能外推49个未证新接触或全集。


**M5d 结构与口径订正**：19 个认证步—块对全是两行边—边近平行构型；68 个候选中 12 个含 VV 的块对与 6 个拥挤（多于两行）块对都落在未证部分，两类可重叠。按“算例、无序块对、规范化首特征集合”去重并忽略步号，得到 **17 个特征构型身份**（bb05 第 3、11、20 步归一）；这不是 17 个统计独立样本，也不声称精确几何相等。首盖总在 legacy 保留角候选中，raw 的 12 对由 df06 主/共边换半升为 post 主参考。源码行号与具名门见 [M5d 订正文档](file:///D:/eab-wt/cx-e2/docs/m5d_legacy_semantics.md)。

**49 个未证项仅作名义对照，不作稳健结论**：raw 主 / VV 二参 / 共边单列命中为 31 / 9 / 8，主+VV 为 40，全槽为 48；post 对应 38 / 9 / 1、47、48。唯一名义全槽未命中是 bb51 第 2 步 (3,9)，名义首特征 VE(93;149,153)，两阶段仍各有该块对两条记录；不是 missing-pair。逐对清单与输入绑定见 [M5d B 审计摘要](file:///D:/eab-wt/cx-e2/reports/codex/M5d_evidence/b_wording_audit.json)。

新增最小例：bb05 第3步 (2,3)，首盖 `VE(vertex=18, edge=(11,12))`；raw 主参考不命中、同一行共边槽命中，post 主参考命中。输入、精确证书与真实重执行结果见 [新最小例](file:///D:/eab-wt/cx-e2/reports/codex/M5c_evidence/research_minimal_examples.json)。原 bb03 例仍见 [五例](file:///D:/eab-wt/cx-e2/reports/codex/M5b_evidence/robust_minimal_examples.json)。

## 4. C：已贯入全局最短出口——PARTIAL

C1 是严格但尚未实现的充分条件：两环管内严格凸，所有跨环边叉积严格离零以固定 Minkowski 边法向序/标签；对应端点差的 L∞ 误差为 `r=ra+rb`，故每条闭边的 Hausdorff 欧氏误差 ≤ `sqrt(2) r`。设原点到全部闭边的精确平方距离为 q_i，唯一最优 q 要求：

`q > 2r²`，且对所有竞争边，`h=q_j-q-8r² > 0`、`h² > 32qr²`。

后两式等价于严格距离差 `sqrt(q_j)-sqrt(q)>2sqrt(2)r`，配合边界标签存续给最近边不变；遍历全部闭边的严格间隙已排除端点邻边并列。平行边拆分、原并列集合、凹环遮盖边、新暴露边不得靠距离差单独认证。外部竞争者离并列组很远，只能证明新最优属于该组，不能证明原并列标签集合不变。

**未实现/未跑：** 跨边法向序、全局边界特征存续、距离扰动与并列等距保持的生产检查。因而16676对全部仍 `INITIAL_EXIT_ORDER_UNCERTIFIED`，稳健出口子集n=0，无法回答稳健出口命中率；不是0失配。

仅对这16676对原有记录计数（不是出口认证）：

| 阶段 | 主参考行 | VV二参行 | 有效共边槽 |
|---|---:|---:|---:|
{exit_table}

## 5. 冻结重算、四片与逐站审计

端点 `endpoint_full_m5c_r1` 真实重算15220块帧，{endpoint['seconds']:.3f}秒；全部精确极值与旧摘要相同。{len(endpoint['source_hashes'])}文件运行时闭包替代4个直接文件，输入分片另绑定；旧摘要/最小例原字节在 `_before.json`。稳健全量、研究68、最小例均真实重算，不只改hash。未触及旧M5a/M5a2/M4c实际导入闭包，未无谓改其冻结绑定。

最终有效四片最后一行原样：

```text
{last_lines}
```

静态最后一行原样：

```text
{suite['static_last_line']}
```

所有setup/call/teardown passed；收集=执行={suite['collected']}，唯一节点、分片无重叠、0skip。用户禁止worktree，以新鲜字节导出执行并前后核验，`fresh_git_checkout=false`，不冒称新Git检出。源码/测试/政策/fixture与最终实际执行副本一致。

基线call累计 {perf['baseline_call_seconds']:.3f}s；新增节点call累计 {perf['added_call_seconds']:.3f}s，占基线 **{perf['added_over_baseline']*100:.4f}%**。宿主有并行证据工作，不把墙钟比冒称受控性能测试；完整长回放未塞默认pytest。

准入按**实际反事实诊断集 × AST行/列站点**计数：关闭全部逐站/共享豁免前后差集，基线与当前均3314逐站或重叠贡献+77共享边际贡献=3391，净增0。M5b旧文3618+77是context匹配的AST站点口径，包含未实际释放诊断的项，不能直接当本单反事实分母。新增逐条准入清单为空，policy字节不变。[逐站机器证据](file:///D:/eab-wt/cx-e2/reports/codex/M5c_evidence/admission_rule_sites.json)。

独立交叉复核记录包括R1/R2补牙、A5接线、A6/A7绑定、R3证明/对抗、C1边界与联合发布。发现的锁长槽误计及联合参考总数守恒major已修复并保留首轮证据；不以“测试全绿”替代Claude最终独立验收。

## 6. 复跑、回滚与遗留

所有命令先令 TEMP/TMP 指向本树 `reports/codex/M5c_evidence/tmp`，Python UTF-8；pytest 一律无cacheprovider且显式basetemp。关键命令：

```text
python -X utf8 tools/m5c_mutation_evidence.py
python -X utf8 tools/m5c_independent_review.py
python -X utf8 tools/m5c_audit_legacy_slots.py --check-production
python -X utf8 tools/m5b_endpoint_replay.py --run-name <新目录>
python -X utf8 tools/m5b_robust_replay.py --name <新目录> --publish
python -X utf8 tools/m5c_diagnostics.py --name <新目录> --summary <完整摘要路径>
python -X utf8 tools/m5c_publish_combined.py --name <新目录> --output <新摘要路径>
python -X utf8 tools/m5c_run_gates.py --name <新目录>
```

联合发布器默认拒绝覆盖；历史产物先归档，新增完整批次才能发布。中断整批作废，研究r1–r3与稳健r1均未拼接成有效证据。大逐对流、详细节点及长日志留ignored tmp，公共摘要绑定hash；全部交付文件见清单。回滚依据原HEAD与字节备份；未自动执行Git回滚。

遗留：C1生产边界存续与出口排序尚未实现；49/68新接触仍未证，不把它们称为模型敏感；任意物理步内路径与完整P3超越首根不在本次保证内。Claude最终独立验收仍由所有者执行。

M5c_PARTIAL：C 的正误差管出口特征存续、排序实现及稳健子集命中结论未完成；49/68 新接触仍未证且不外推
"""
    assert all(hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected for path, expected in READ_HASHES.items()), "report inputs changed during rendering"
    (ROOT / "reports/codex/M5c_report.md").write_text(text, encoding="utf-8", newline="\n")
    print("M5C_REPORT_WRITTEN")


if __name__ == "__main__":
    main()
