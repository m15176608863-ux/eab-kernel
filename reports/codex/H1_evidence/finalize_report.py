"""Finalize H1 only after both complete full suites and the fast tier are green."""
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[3]
E = ROOT / "reports/codex/H1_evidence"


def read(name):
    return json.loads((E / name).read_text("utf-8"))


def link(label, name):
    return f"[{label}]({(ROOT / name).as_uri()})"


def main():
    baseline, fast, final = (read(name + "/summary.json") for name in ("baseline", "fast_verified", "final"))
    for record in (baseline, fast, final):
        assert record["complete"] and record["audit"] == "GREEN"
        assert all(s["exit_code"] == 0 and s["node_sets_equal"] and s["skip_count"] == 0
                   and s["collected"] == s["executed"] for s in record["shards"])
        assert not record.get("export_changed") and not record.get("live_tree_changed")
    assert len(baseline["shards"]) == len(final["shards"]) == 4
    assert baseline["static"]["exit_code"] == final["static"]["exit_code"] == 0
    assert fast["module_coverage_complete"] and final["module_coverage_complete"]
    assert fast["elapsed_seconds"] < 300
    delta, archive, attribution = read("node_delta.json"), read("archive_validation.json"), read("attribution_validation.json")
    policy, projection, p3 = read("policy_rekey.json"), read("policy_projection_teeth.json"), read("p3_verification.json")
    definitions = policy["production_definition_proof"]
    functions = read("p1_function_relocation.json")
    assert delta["complete"] and delta["old"]["node_count"] == baseline["collected"] == 13877
    assert delta["new"]["node_count"] == final["collected"] == 13907
    assert delta["counts"]["retired_observed"] == 12 and delta["counts"]["new_observed"] == 42
    assert archive["status"] == "passed" and archive["all_fixture_sha256_verified"]
    assert policy["old_count"] == policy["new_count"] == 3522
    assert definitions["equal_definitions"] == 1074 and definitions["equal_mapping_tables"] == 6
    assert len(functions) == 134 and all(row["source_unchanged"] for row in functions)
    assert projection["whole_policy_roundtrip_equal"] and all(row["killed"] for row in projection["mutations"])
    assert all(row["status"] == "KILLED" for row in p3["mutation_results"])
    evidence = lambda label, name: link(label, "reports/codex/H1_evidence/" + name)
    baseline_lines = "\n".join(s["last_line"] for s in baseline["shards"])
    final_lines = "\n".join(s["last_line"] for s in final["shards"])
    report = f"""# WO-H1 执行报告（2026-10-19）

完成 P0、P1；P2 已实施并验证，历史来源元数据缺项如实保留；P3 做二维对称门与指定三门。未合入 m5e-wip，未实现 C++/TIA 二维新功能，未做全量回放或重算冻结数值。

## P0 · 归属订正

| 文件 | 改动 |
|---|---|
| `docs/shi_attribution.md` | 新增 39 行、互斥五类，43 个具名门引用存在；无门明确标出，原文直接英文引用 0 处 |
| `docs/canon_errata_20261019.md` | 14 条原说法/出处/原文实际/改法；外部 00/01/03 未写入 |
| `canon_map` / `m3_global_entrance_design` / `m3b_boundary3d_design` / `m5a_se2_design` | 分别订正 24 / 9 / 2 / 1 处归属，共 36 处；另有机械路径更新 |
| `README.md` / `AGENTS.md` | 分别重写为 {attribution['readme_lines']} / {attribution['agents_lines']} 行；原文件逐字节存入 `docs/history/` |
| `M5a_report.md` / `M3_evidence/theory_audit.md` | 各加一行勘误指针；历史正文原字节不变，后者随证据外移 |

{link('归属总表', 'docs/shi_attribution.md')} · {link('14 条勘误', 'docs/canon_errata_20261019.md')} · {evidence('逐处修改与验证', 'attribution_changes.json')}。文档局部门 `31 passed in 0.42s`。

## P1 · 只搬家，不改数学

| 函数/对象 | 新位置或保留位置 | 理由 |
|---|---|---|
| interlock 的逃逸、候选、剪胀函数及私有实现 | `adapters/tia3d.py` | TIA 的 L5 域问题 |
| DDA 路径、z/槽位解析；`model_robustness.dda_paths` | `adapters/bdda2d_motion.py` | 引擎输入/锚定路径解释 |
| `DDAAffineMotion` | `adapters/bdda2d_affine.py` | DDA 路径专属；`AffineFit/fit_affine` 仍为核心原对象 |
| 六张 BDDA/BDDA3D/TF 表 | `adapters/bdda2d.py`、`bdda3d.py`、`tf.py` | 域码不属于 ContactRecord |
| 通用文本数值解码 | `eab/numeric_decode.py` | 切断内核传递进入 readers 的依赖 |
| 通用路径代数、R1/R2/R3/C1 证书 | 原 kernel2d 模块 | 与域无关，数学原样保留 |

{evidence('完整 134 项函数留/搬理由表', 'P1_relocation.md')}：60 搬、74 留，134/134 函数/类源码相同；扩展验算 **1074/1074 定义 AST、6/6 映射表等同**。不留内核转发模块。
纯度门 6 节点：AST 词表、非 docstring 字符串、传递 import 图；真实副本中插入 adapter import 或 `mtype` 均命中对应断言。唯一非路径生产文案改动是 `geom3.Polyhedron.edge_dir` 零长边异常提示改为通用 input boundary；异常类型、条件和数学输出不变，不声称异常文字逐字相同。

## P2 · 验证减负

- **准入冻结**：3522 → 3522，114 行重键、142 个明确字段映射；648 imports、432 members、106 renewals 数量不变。相同 AST 站点与函数源码逐一核验；两处模块级上下文因搬表/import 改变单列。历史指纹常量不变，反向投影恢复完整旧策略，真实扫描仍用新策略；实际 JSON 理由篡改、错路径、新增准入三牙均报红。{evidence('重键对应表', 'policy_rekey.csv')} · {link('全部字段映射', 'tools/exact_construction_relocations.json')} · {evidence('投影牙', 'policy_projection_teeth.json')}。
- **绊线退役**：删除 12 个源绑定节点，新增 4 个真实小子集/数据完整性节点；同次运行前后稳定性、数据 SHA 和静态准入授权保留。固定小子集逐项重算状态、标签、精确时间与计数，不刷新旧数值。{link('逐条退役与替代门', 'docs/frozen_evidence.md')}。
- **归档**：43 目录、{archive['archive_files']:,} 文件、{archive['archive_bytes']:,} 字节；其中跟踪文件 {archive['tracked_archive_files']:,} 个、{archive['tracked_archive_bytes']:,} 字节。含旧 ignored 沙箱；逐文件 SHA 清单只存仓库外。测试输入 **136 搬 + 1 原字节复制**，共 137 文件、12,445,253 字节；复制项的外档原件保留。{link('归档映射及 43 份清单', 'reports/EVIDENCE_ARCHIVE.md')} · {evidence('归档校验', 'archive_validation.json')}。
- **大文件门**：单文件上限 1,000,000 bytes，唯一例外为冻结静态策略 JSON；真实超限文件注入报红。当前门全绿。
- **快慢档**：以完整基线 `--durations=0` 和逐阶段实际记录选择 222 个慢函数；当前快 7947 / 慢 5960。正式快档 `{fast['shards'][0]['last_line']}`，运行器总耗时 **{fast['elapsed_seconds']:.3f}s**，单进程小于 5 分钟；55/55 模块导入，48 个函数模块真实调用、7 个声明模块在测试中执行模块代码，收集期导入不冒充覆盖。{evidence('分档依据', 'tier_selection.json')} · {evidence('快档及执行核对', 'fast_verified/summary.json')} · {evidence('逐模块见证', 'fast_verified/module_coverage.json')}。
- **纪律**：G6 多路复审退役，改由 Claude 安排一路对抗核查；保留 A–F 实质，事故叙事存 history。运行器需 Python 3.12+，全档四片、进度落盘、超时失效，禁止拼接。

过程记录：首轮快档 profile 的 24 个失败为 18 项输入接线与 6 项历史策略比较；分别定向 `21 passed in 2.07s`、`86 passed in 4.41s`，之后上述完整快档全绿。未把 profile 当验收绿。耗时为本机共享环境实测，不作为内核性能提升证据。

## P3 · 已做 / 未做

二维对称定理 24 个非凸/刚体/单位格子 + 1 个产物互异门；从 `5e3ba68` 只摘指定三道语义门；C1 的 4283/4280/102 粗下界、16 段约 2728、特征改变 44 已订正。四项内部数学变异均由目标语义断言杀死。{evidence('P3 记录', 'p3_verification.json')}。未加三维对称门；未摘变异框架、台账或充分性门。

## 两次全档（每片最后一行原样）

开工：
```text
{baseline_lines}
```
收尾：
```text
{final_lines}
```

两次均收集=派发=实际 call，多重集合相等、0 skip、0 failed；静态均 `exact construction AST gate: 0 violation(s)`。收尾导出副本与现场文件集合/字节均未漂移，55/55 模块执行核对通过。{evidence('基线总账', 'baseline/summary.json')} · {evidence('收尾总账', 'final/summary.json')}。
节点：**13877 − 12 + 42 = 13907**；新增 42 = 纯度 6 + P3 28 + 大文件 3 + 语义/数据 4 + 声明模块执行 1。11 对等量改名（3 名称、5 参数、3 历史 README 路径），搬家 0 增量；无未解释差异。{evidence('逐节点差异账', 'node_delta.md')}。

## 遗留与边界

1. 历史产物未记录可确认的生产提交/工具版本，137 项均如实标 unknown；23 项仅可核对源码等价提交，不冒充产物生成记录。
2. 旧全量 CLI 的历史 reports 输入路径需按归档映射准备；本单未运行或重新验收这些全量分支，当前 pytest 无外档依赖。
3. 验证用受控字节导出，**不是新鲜 Git worktree/克隆**；遵守本单禁 Git 写操作。Claude 负责暂存、提交、新鲜 Git 验收及一路对抗核查；本报告不冒充其独立验收。
4. 未修改姊妹仓库和外部正本；未提交、切分支或合入封存分支。完整成果链接见 {evidence('交付清单', 'DELIVERABLES.md')}。

H1_DONE
"""
    target = ROOT / "reports/codex/H1_report.md"
    target.write_text(report, encoding="utf-8", newline="")
    (E / "completion.json").write_text(json.dumps(dict(status="H1_DONE", baseline=13877, final=13907,
        fast=7947, slow=5960, module_count=55, report=str(target), no_git_writes=True,
        fresh_git_checkout=False, independent_claude_acceptance=False), ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    names = subprocess.check_output(["git", "ls-files", "--modified", "--others", "--exclude-standard", "-z"], cwd=ROOT).decode("utf-8").split("\0")
    existing, absent = [], []
    for name in sorted(set(filter(None, names))):
        if name == "reports/codex/H1_evidence/DELIVERABLES.md":
            continue  # The index does not report its own changing byte count.
        path = ROOT / name
        if path.is_file():
            existing.append(name)
        else:
            absent.append(name)
    lines = ["# H1 交付清单", "", "所有链接指向当前本机成果；大日志/节点清单仅在 ignored tmp。", "",
             link("主报告", "reports/codex/H1_report.md"),
             link("外部归档及逐文件 SHA 清单索引", "reports/EVIDENCE_ARCHIVE.md"),
             link("运行副本、大日志及逐节点原始记录", "reports/codex/H1_evidence/tmp"), "",
             f"现有新增/修改文件 {len(existing)} 个；旧位置不再存在 {len(absent)} 个（归档/搬家，详见上述索引及 P1 表）。", "",
             "| 当前文件 | bytes |", "|---|---:|"]
    lines += [f"| {link(name, name)} | {(ROOT/name).stat().st_size:,} |" for name in existing]
    (E / "DELIVERABLES.md").write_text("\n".join(lines)+"\n", encoding="utf-8", newline="")

    print(target.as_uri())


if __name__ == "__main__":
    main()
