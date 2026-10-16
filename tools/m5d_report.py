"""Build the Chinese WO-M5d report only from complete, verified evidence."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
E = ROOT / "reports/codex/M5d_evidence"


def read(name):
    return json.loads((E / name).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_map(mapping):
    for name, expected in mapping.items():
        path = Path(name)
        if not path.is_absolute():
            path = ROOT / path
        assert path.resolve().is_relative_to(ROOT), name
        assert sha(path) == expected, "report input/source drift: " + name


def fragment(name, heading):
    content = (E / name).read_text(encoding="utf-8")
    lines = content.splitlines()[1:]
    extra = "#" * (len(heading.split(" ", 1)[0]) - 1)
    return heading + "\n" + "\n".join(extra+line if line.startswith("#") else line for line in lines) + "\n"


def main():
    inputs = {name: sha(E / name) for name in (
        "execution_audit.json", "frozen_refresh.json", "admission_rule_sites.json", "suite_delta.json",
        "r3_semantic_evidence.json", "replay_semantic_evidence.json", "c1_summary.json",
        "c1_adversarial.json", "c1_mutations.json", "c1_nonconvex_audit.json", "b_wording_audit.json",
        "review_c1.json", "review_r3.json", "review_integration.json", "review_replay_semantics.json",
        "r3_report_fragment.md", "b_report_fragment.md", "c1_delivery.md")}
    execution, refresh = read("execution_audit.json"), read("frozen_refresh.json")
    admissions, r3 = read("admission_rule_sites.json"), read("r3_semantic_evidence.json")
    c1, adv, wording = read("c1_summary.json"), read("c1_adversarial.json"), read("b_wording_audit.json")
    replay, cm, nonconvex = read("replay_semantic_evidence.json"), read("c1_mutations.json"), read("c1_nonconvex_audit.json")
    assert execution["complete"] and execution["audit"] == "GREEN"
    assert execution["collected"] == execution["executed"] and execution["skip_count"] == 0
    assert not execution["executable_source_drift"] and execution["all_stages_passed"]
    assert refresh["complete"] and refresh["numerical_products_unchanged"]
    assert admissions["complete"] and admissions["policy_bytes_unchanged"]
    assert admissions["admitted_rule_site_net_delta"] == 0
    assert r3["valid"] and r3["mismatches"] == 0 and r3["mutation_count"] == 21
    assert (r3["nominal_configuration_count"], r3["certified_configuration_count"],
            r3["unproved_configuration_count"], r3["perturbation_count"]) == (6, 4, 2, 256), "update narrative after changing experiment size"
    assert replay["complete"] and replay["collected"] == replay["executed"] == 10 and replay["skip_count"] == 0
    assert replay["mutation_count"] == len(replay["mutations"]) == 6
    assert not replay["hash_tripwires_selected"] and not replay["frozen_snapshot_tripwires_selected"]
    check_map(replay["sources"])
    assert cm["complete"] and len(cm["mutations"]) == 6
    assert all(row["outcome"] == "NAMED_SEMANTIC_ASSERTION_RED" for row in cm["mutations"])
    assert not cm["source_hash_tripwires_invoked"] and not cm["frozen_snapshot_assertions_invoked"]
    assert cm["source_sha256"] == sha(ROOT / "src/eab/kernel2d/m5d_exit_certificate.py")
    assert nonconvex["complete"] and nonconvex["counts"] == {"NEGATIVE_SUPPORT_SIDE": 12387}
    assert nonconvex["summary_sha256"] == sha(E / "c1_summary.json")
    assert nonconvex["source_sha256"] == sha(ROOT / "tools/m5d_c1_nonconvex_audit.py")
    check_map(nonconvex["input_hashes"])
    assert c1["complete"] and c1["counts"]["CERTIFIED_UNIQUE_EXIT"] == 4280
    assert c1["counts"]["initial_overlap_pairs"] == 16676 and c1["counts"]["independent_oracle_checks"] == 4280
    assert adv["complete"] and adv["counterexamples"] == 0
    assert (adv["nominal_configurations"], adv["certified_radii"], adv["nonrigid_both_ring_perturbations"]) == (48, 96, 6144)
    assert wording["complete"] and wording["unique_configurations"] == 17
    assert wording["script_sha256"] == sha(ROOT / "tools/m5d_wording_audit.py")
    for name, key in (("review_c1.json", "source_hashes"), ("review_r3.json", "reviewed_hashes"),
                      ("review_integration.json", "source_hashes"), ("review_replay_semantics.json", "reviewed_file_hashes")):
        review = read(name)
        assert review["complete"]
        if name == "review_integration.json":
            assert review["critical_open"] == review["major_open"] == 0
        else:
            assert review["critical"] == review["major"] == 0
        check_map(review[key])
    c1_review = read("review_c1.json")
    assert c1_review["recount"]["references"] == c1["references"]
    assert c1_review["recount"]["mismatches"] == c1_review["adversarial"]["mismatches"] == 0
    for data in (c1, adv):
        assert data["source_hashes"] == data["source_hashes_end"]
        check_map(data["source_hashes"])
        check_map(data.get("input_hashes", {}))
    check_map(r3["sources"])
    check_map(wording["input_hashes"])
    check_map(execution["audit_input_hashes"])
    check_map(refresh["publication_bindings"])
    for row in refresh["publication"]:
        assert sha(ROOT / row["target"]) == row["after_sha256"]
    perf = execution["performance"]
    assert perf["added_over_baseline"] <= 0.05, "new default-test cost exceeds requested approximate 5%"
    delta = read("suite_delta.json")
    content = """# WO-M5d 中文交付报告

## 结论与信任边界

A1–A4、B5–B7 已完成；C1 在已证明的严格凸、跨环非平行、唯一出口子域实现并完成全量回放。
16676 个初态贯入对认证 4280 个，未证 12396 个明确分列。未认证不等于真实不稳健，不向凹环或全时程运动外推。
本报告是工单实现与团队交叉复核交付，**不代替 Claude/所有者的六路 G6 独立退出验收**，不修改 README 声称。

初始基线为干净 `codex-work @ 5b73cc8dfc1ad4f257412392111927d5a7171640`。
仅写当前工作树；其他工作树及姊妹仓库只读，无 commit/push/reset/checkout/stash/worktree/branch 操作，无新依赖。
由于禁止 worktree，基线用只读 `git archive HEAD`，最终用全新字节导出；明确 `fresh_git_checkout=false`，不冒充新克隆。

关键索引：[数值合同与 imports](file:///D:/eab-wt/cx-e2/docs/m5d_numeric_inventory.md)、[交付清单](file:///D:/eab-wt/cx-e2/reports/codex/M5d_evidence/delivery_manifest.md)、[机器执行审计](file:///D:/eab-wt/cx-e2/reports/codex/M5d_evidence/execution_audit.json)。

## A 的变异总账与口径

本单数值主门合计 33 个真实内部变异：R3 21、R1/R2 回放 6、C1 6；另有冻结发布流程 1 个内部变异。
全部通过真实被测函数体编译替换执行，直接调用新具名语义门，未选择源码哈希和冻结摘要快照测试；不是枚举后追加假产物。
其中 R3 12 个是实际错误公共证书，2 个是公共充分条件合同、7 个是内部预算恒等式；C1 2 个穿过公共 API、4 个是内部排序合同。
回放 6 个均穿过实际回放或 R2 生产路径。不能将 33 个全称作已找到物理错误证书。
各变异的实际 AssertionError、输入及断言名分别在 `r3_semantic_evidence.json`、`replay_semantic_evidence.json`、`c1_mutations.json`。

| A1 子条件 | 真实内部改坏 | 具名门（`tests/test_m5d_r3_semantics.py`） |
|---|---|---|
| 早期全窗 | 跳过 / 缩短 / 只查后半段 | `test_r3_complete_early_window_rejects_prebracket_contact` |
| EV 竞争者 | 不枚举 EV | `test_r3_ev_competitor_precedes_nominated_ve` |
| 两侧边内投影 | 分别省略 g / h | `test_r3_both_projection_sides_reject_line_extensions` |
| 末段 | 省略最后子窗 | `test_r3_final_panel_rejects_departed_endpoint` |
| L1 对偶归一 | 用 L∞ 替代 L1 | `test_r3_linf_tube_requires_l1_dual_normalization` |
| 端点扣费 | 末端不扣误差 | `test_r3_endpoint_budget_prevents_actual_out_of_bracket_contact` |
| 边长预算 | 省略 dw·norm(U)，A / B 活动分别构造 | 同上及 `test_r3_bilinear_budgets_include_both_endpoints_and_all_terms` |
| 不等分母 | 错走等分母相减支路 | `test_r3_unequal_p2_denominators_reject_false_time_bracket` |

### A2：R1 必须认证两个名义路径的管

新 `test_replay_r1_requires_p2_tube_even_when_both_nominal_paths_are_separated` 构造 P1 与 P2 名义都不接触、
P1 管可分离而 P2 管有接触的实际回放输入；不靠双盒直判，也不是名义 P2 已接触的简单格子。
A 三角形为 `(10,-1/2),(-5,1),(-5,-1/2)`，P2 转动半角参数 1/20；B 的 x 范围为 `[501/50,401/40]`，y 为 ±1/1000。
ra=1/100，rb=0；P1 最大 x 加管宽只有 10.01。P2 名义顶点范数平方至多 401/4，仍在 B 左侧；
但 s=1/2 时 A 顶点为 `(16030/1601,1/3202)`，允许的端点为零的扰动 `dx(s)=4ra·s(1-s)` 将其送入 B。
把真实 `compare_pair` 的无接触证书接线改成只查 P1，红在 **R1 both-path tube gate**。

### A3：温和 R2 变体

`test_r2_mild_early_truncation_rejects_a_short_prior_penetration` 用窄时间窗轨迹，
真实早接触位于括区之前，省略最后 1% 或 0.1% 的早期窗口都会签错，而完整生产 R2 拒签。
`test_replay_single_cover_keeps_both_tubes_and_the_full_radius_at_the_threshold` 选 P1 速度 2.001、P2 速度 2，
公共括区 `(519929/1048576,528385/1048576)`，半径 `16392071/2097152000`：P1 可证、P2 不可证。
两条名义首标签相同不能掩盖 P2 管内首时刻越过上界。真实 `all→any`、只查 P1、半径乘 0.99 三种接线变异均红在具名语义断言。
这两组加 R1 共 10 节点 / 6 内部变异；独立期望为 Fraction 恒等式，不调用生产几何原语。

"""
    content += fragment("r3_report_fragment.md", "### A1 / A4：完整语义门和阈值对抗结果")
    content += fragment("b_report_fragment.md", "## B：措辞、19/68 子集与 legacy 槽语义")
    content += fragment("c1_delivery.md", "## C：C1 定理、实现、全量计数与最小例")
    content += """
## 独立性、元门及数值合同登记

主 oracle import 清单和每个具名门见 `docs/m5d_numeric_inventory.md`；R3 主 oracle 只 import Fraction/lru_cache/comb，
平移辅助 oracle 仅 Fraction；C1 主 oracle 仅 Fraction；B 槽对照不 import 生产几何或姊妹模块。
输入适配器一致性不冒充 oracle。团队另用独立闭式旋转根 `4−2√3` 核 R3，用穷举支撑半平面第三路径核 C1，均零失配。
元门含非轴向有理旋转、工程坐标大平移、单位缩放及标签置换/产物互异；L∞ 盒旋转按诱导范数保守扩张，
不要求边缘处充分条件的最大认证半径旋转不变。所有新几何判据精确有理，无无关绝对阈值。

## 冻结绑定：真实重算而非改哈希

`tools/m5b_robust_replay.py` 的改动只是 raw ID 注释，但它位于冻结运行时闭包，仍按规则完整重算。
实际新 robust 批次 `robust_full_m5d_r1` 重新计算所有 64010 个步—块对；research 批次 `research_full_m5d_r1`
遍历同一全量、重解全部 68 个候选。联合发布逐项比较 64010 个 P1/P2 精确观察，连接全部 68 个研究结果。
最小例、研究最小例和 523 次初态见证试探都重新调用真实计算（3 对找到见证，65 对在八偏移内未找到），比较完数值产物才发布七个冻结文件；原字节保留备份。
原 M5c combined 的 C 未认证口径是其历史阶段，当前 C1 独立证据不偷偷改写旧阶段的含义。
发布器统一封印 source/input/inherited/candidate/backup，发布前后每阶段复核。
强制终止不是跨文件原子事务；外部编辑目标/备份时拒绝不安全覆盖，不保证强杀后自动恢复。中断批次作废，不拼接。

"""
    content += f"实际 robust 用时 {refresh['robust_seconds']:.3f}s；research 用时 {refresh['research_seconds']:.3f}s。发布数 {len(refresh['publication'])}，完整绑定与前后哈希见 `frozen_refresh.json`。\n\n"
    content += "## 最终四分片、静态与准入\n\n四片最后一行原样如下（不是计划执行数）：\n\n```text\n"
    content += "\n".join(row["last_line"] for row in execution["shards"])
    content += "\n```\n\n"
    content += f"收集 = 执行 = **{execution['collected']}**，0 skip；每个节点 setup/call/teardown 各一次且全部 passed。相对基线新增 {delta['added_count']} 节点、移除 {delta['removed_count']} 节点。\n"
    content += "静态末行原样：`" + execution["static_last_line"] + "`。最终源码导出执行前后文件集合/字节均未变，当前可执行文件与执行导出零漂移。\n\n"
    old_count, new_count = admissions["baseline"]["effective_rule_site_count"], admissions["current"]["effective_rule_site_count"]
    content += f"逐站反事实准入：**{old_count} → {new_count}，净增 0**；policy 字节未改。口径是禁用准入后实际诊断的 `(path,function,rule,line,AST column)` 差集，不是 JSON 行数。\n\n"
    content += f"新节点 call 耗时 {perf['added_call_seconds']:.3f}s / 基线全部 call {perf['baseline_call_seconds']:.3f}s = **{100*perf['added_over_baseline']:.3f}%**，在约 5% 约束内。"
    content += f"基线/最终墙钟 {perf['baseline_wall_seconds']:.3f}s / {perf['final_wall_seconds']:.3f}s；有并行证据任务和静态门，不能把墙钟差冒称受控性能基准。长回放及大规模对抗不进 pytest。\n\n"
    content += """## 审查发现闭环与遗留

团队交叉复核覆盖 R3、回放语义、C1、冻结/集成；完整过程见 `review_r3.md`、`review_replay_semantics.md`、`review_c1.md`、`review_integration.md`。
发现并关闭发布漂移窗口 1 major；另修复 W/V 同 L1 长度掩盖预算混用的弱门，以及 PowerShell 管道损坏中文理论草稿的问题。
R3 理论当前文件是编码修复后的重写字节，不冒称这份字节文件早于实现；理论合同沿用并核查了 M5c 定理。C1 边界存续证明先落盘后实现。
当前局部审查无未关闭 critical/major；此句话不是六路 G6 通过声明。

遗留/边界：凹环一般 C 证书、跨环平行拆分及原并列集合存续仍未证明，C1 拒签；12396 对不作稳健出口结论。
49 个未证新接触对只给名义对照。4280 个 C1 对仅在初态几何盒内认证，不认证整步名义轨迹出口恒定。
所有者 Claude 的独立验收仍需进行。上述拒签属于本单明确要求的保守边界，未以距离差勉强签发。

## 复跑与交付

所有命令先设 `TEMP=TMP=<本树>/reports/codex/M5d_evidence/tmp`，`PYTHONDONTWRITEBYTECODE=1`，UTF-8；pytest 必须带 `-p no:cacheprovider --basetemp <新目录>`。
关键脚本：`tools/m5d_r3_evidence.py --count 32`、`tools/m5d_replay_teeth_evidence.py`、`tools/m5d_c1_replay.py`、
`tools/m5d_c1_adversarial.py`、`tools/m5d_wording_audit.py`、`tools/m5d_refresh_frozen.py`、`tools/m5d_audit_admissions.py`。
全套采用 `tools/m5d_run_gates.py --name <新目录>` 后调用 `tools/m5d_finalize_evidence.py <同名目录>`；不得复用中断批次。
本报告可用 `python tools/m5d_report.py` 重建；最终清单用 `python tools/m5d_delivery_manifest.py` 重建，包含 SHA256、大小、可点击链接及编码/换行检查。
大日志和逐节点记录在 ignored tmp，待提交路径不含超过 1 MB 的本单文件。

M5d_DONE
"""
    target = ROOT / "reports/codex/M5d_report.md"
    assert all(sha(E / name) == expected for name, expected in inputs.items()), "evidence changed while report was built"
    target.write_text(content, encoding="utf-8", newline="\n")
    bindings = {(E / name).relative_to(ROOT).as_posix(): value for name, value in inputs.items()}
    (E / "report_build.json").write_text(json.dumps({"complete": True, "input_hashes": bindings,
        "script_sha256": sha(Path(__file__)), "report_sha256": sha(target)}, ensure_ascii=False, indent=2)+"\n",
        encoding="utf-8", newline="\n")
    print("M5D_REPORT_WRITTEN", target)


if __name__ == "__main__":
    main()
