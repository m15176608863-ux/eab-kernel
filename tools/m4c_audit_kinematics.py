"""Read-only source/data audit for M4c; all copies and evidence stay in this tree.

No sibling executable or Python module is executed/imported.  The Markdown
template is intentionally in this UTF-8 source, not sent through a shell pipe.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import csv
from fractions import Fraction
import hashlib
import json
import os
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = Path("D:/eab-wt/m02-int/reports/codex/M4b_evidence/replay_sources_final.json")
SOURCE_RELS = ("geom/moments.hpp", "driver/run.hpp", "driver/main.cpp",
               "io/detect_snapshot.hpp", "stepper/open_close.hpp", "core/blocks.hpp")
TUPLE_COLUMNS = ("mtype", "p1", "p2", "p3", "m4", "m5", "m6")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def copy_input(source, target):
    require(target.resolve().is_relative_to(ROOT), "copy must remain inside workspace")
    target.parent.mkdir(parents=True, exist_ok=True)
    require(not target.exists() or not os.path.samefile(source, target), "input/output alias")
    shutil.copyfile(source, target)
    require(sha(source) == sha(target), "copy hash mismatch")
    return {"source": str(source), "copy": str(target),
            "bytes": target.stat().st_size, "sha256": sha(target)}


def read_csv(path):
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        return reader.fieldnames, list(reader)


def audit_case(case, source, temporary):
    source = Path(source)
    dst = temporary / case
    files = {name: copy_input(source.parent / name, dst / name)
             for name in ("shadow.jsonl", "geom.csv", "state.csv", "out.csv")}
    records = [json.loads(line, parse_float=Fraction)
               for line in (dst / "shadow.jsonl").read_text(encoding="utf-8").splitlines()]
    header, end, frames = records[0], records[-1], records[1:-1]
    n = len(frames)
    require([frame["step"] for frame in frames] == list(range(1, n + 1)), "step discontinuity")
    require(end == {"kind": "end", "completed_steps": n, "status": "ok"}, "bad end record")
    require(header["requested_steps"] == n, "requested/completed disagreement")
    geoms = defaultdict(dict)
    _, geom_rows = read_csv(dst / "geom.csv")
    for row in geom_rows:
        kind = row["kind"]
        if kind.startswith("step") or kind in ("initial", "final"):
            index = int(row["idx"])
            require(index not in geoms[kind], "duplicate geometry index")
            geoms[kind][index] = Fraction(row["x"]), Fraction(row["y"])
    require({k for k in geoms if k.startswith("step")} == {f"step{k}" for k in range(n + 1)},
            "missing geometry time slice")
    require(geoms["initial"] == geoms["step0"], "initial geometry mismatch")
    require(geoms["final"] == geoms[f"step{n}"], "final geometry mismatch")
    signature = tuple((row[0], row[1]) for row in frames[0]["geometry"])
    checks = 0
    for frame in frames:
        require(tuple((row[0], row[1]) for row in frame["geometry"]) == signature,
                "block/vertex topology changed")
        for block, index, x, y in frame["geometry"]:
            require((Fraction(x), Fraction(y)) == geoms[f"step{frame['step'] - 1}"][index],
                    f"geometry mismatch {case} {frame['step']} {index}")
            require(index in geoms[f"step{n}"], "terminal vertex missing")
            checks += 1
    blocks = len({row[0] for row in frames[0]["geometry"]})
    columns, state_rows = read_csv(dst / "state.csv")
    states = defaultdict(list)
    for row in state_rows:
        states[int(row["step"])].append(row)
    require(set(states) <= set(range(1, n + 1)), "state step outside run")
    for step, rows in states.items():
        require(len({Fraction(row["tt"]) for row in rows}) == 1, "inconsistent dt in step")
        require(Fraction(rows[0]["tt"]) > 0, "nonpositive dt")
        require([tuple(int(row[k]) for k in TUPLE_COLUMNS) for row in rows]
                == [tuple(row) for row in frames[step - 1]["post_df06"]], "Tuple7 mismatch")
    _, displacement_rows = read_csv(dst / "out.csv")
    displacements = defaultdict(set)
    for row in displacement_rows:
        step, block = int(row["step"]), int(row["block"])
        require(block not in displacements[step], "duplicate displacement block")
        displacements[step].add(block)
        for key in ("z1", "z2", "z3", "z4", "z5", "z6"):
            Fraction(row[key])
    require(set(displacements) == set(range(1, n + 1)), "missing displacement step")
    expected_blocks = {row[0] for row in frames[0]["geometry"]}
    require(all(value == expected_blocks for value in displacements.values()), "displacement block mismatch")
    return {"case": case, "steps": n, "snapshot_frames": n,
            "motion_intervals_without_terminal": n - 1, "motion_intervals_with_geom_terminal": n,
            "blocks": blocks, "snapshot_geometry_rows": len(signature),
            "geometry_snapshot_exact_decimal_rows_compared": checks, "geometry_snapshot_mismatches": 0,
            "stable_block_vertex_identity": True, "end_record": end, "geom_step_k_range": [0, n],
            "geom_final_equals_stepN": True, "state_columns": columns, "state_steps": len(states),
            "state_missing_step_numbers": sorted(set(range(1, n + 1)) - set(states)),
            "state_nonconverged_steps": sorted(s for s, rows in states.items()
                                               if {r["conv"] for r in rows} != {"1"}),
            "state_ratio_gt2_steps": sorted(s for s, rows in states.items()
                                            if any(Fraction(r["ratio"]) > 2 for r in rows)),
            "state_tt_distinct": sorted({rows[0]["tt"] for rows in states.values()}),
            "state_contains_explicit_initial_velocity": False,
            "out_csv_per_block_six_dof_steps": len(displacements),
            "state_post_df06_tuple_mismatches": 0, "files": files}


def render_markdown(audit):
    rows = "\n".join("| {case} | {steps} | {motion_intervals_without_terminal} | "
                     "{motion_intervals_with_geom_terminal} | "
                     "{geometry_snapshot_exact_decimal_rows_compared} |".format(**case)
                     for case in audit["cases"])
    return """# M4c 运动学与全时程输入只读审计

日期：2026-10-14。仅本树写入证据和数据副本；没有在姊妹树运行程序、导入姊妹模块、写文件或执行 Git。源码审计不等于重新运行其数值门。

## 1. 结论与观测边界

- **bdda2 有有限转动端点后修正**。装配和开闭判定位移对六未知量线性，实际顶点推进另用 cos(r0)、sin(r0)，不能称为六未知量的严格线性函数。
- 相邻快照直线插值是**已计算端点之间的事后弦轨迹**，不是已证的求解器连续时内轨迹。即使没有回退或拓扑变化，也不能把弦轨迹说成真实连续旋转。
- 15 例共 1810 个步初快照，仅邻帧形成 1795 个运动区间。同次运行的 geom.csv 提供每例 stepN=final 终端，补齐可得 1810 区间；无需重跑求解器。
- state.csv 的 tt 是时间步；快照 hh、状态 hh_cur/g7 是接触罚刚度量，**不是时间步**。现有输出没有显式步初六分量速度。
- 从第 2 步起可用上一已接受位移构造事前预测。第一步缺少历史，必须标为不可用，不得伪造零运动。

机器证据：[kinematics_audit.json](kinematics_audit.json)。本树副本：[tmp/kinematics_inputs](tmp/kinematics_inputs/)。

## 2. 六自由度线性装配与非线性端点更新

`D:/b-DDA/bdda2/geom/moments.hpp:40-46` 的 displacement_matrix 对 `d=(u0,v0,r0,ex,ey,gxy)` 定义：

```text
dx=x-cx; dy=y-cy
T_x=(1,0,-dy,dx,0,dy/2)
T_y=(0,1, dx,0,dy,dx/2)
```

同文件 `:49-62` 的 update_block_vertices 实际执行：

```text
x_new=x+(u0+ex*dx+gxy*dy/2)+(dx*(cos(r0)-1)-dy*sin(r0))
y_new=y+(v0+ey*dy+gxy*dx/2)+(dy*(cos(r0)-1)+dx*sin(r0))
```

端点变换对空间位置仿射、对转角非线性。独立 binary64 舍入后，各顶点的精确有理坐标未必满足统一的精确仿射矩阵，故 M4c 应定义逐顶点线性轨迹，而非额外假设输入存在精确块内仿射矩阵。

`driver/run.hpp:391-403` 在下一步入口应用上一解；`:410-431` 在求解前检测、df06 并捕获快照；`:498-501` 确定本步时间步；`:768-776` 步末更新速度、位移及历史。因此快照 step=k 是第 k 步步初，不是其步末。

若另外人为定义 r(s)=s*r0 的连续转动，弦仍不等于圆弧：纯转动弦中段到形心距离一般减小，圆弧则不变。本审计没有来源证明求解器采用这种连续插值；端点不足以恢复唯一连续路径。小角度近似不提供接触盖必然一致的证书。

## 3. 回退、重算和拓扑

`run.hpp:32-48` 登记自动时步、位移比大于 2 的步内重做、迭代上限重做为未实现边界。`:70-83` 的 stop_on_boundary 默认 false；`:670-675` 默认仅记录位移比超限，不回退重算。`:498-501` 的时间步调整使用前一步位移比作用于下一步，不是同一物理步的重试。

`stepper/open_close.hpp:163-190` 在固定步初几何上重装配、求解、判锁，不重新推进快照几何。`run.hpp:224-236,390-403` 的块数和顶点范围在本次调用中固定。

实测本数据所有 end.status=ok、所有步 conv=1、ratio>2 为 0，所有帧 (block,vidx) 身份序列一致。但 snapshot version 1 缺 attempt_id/is_accepted/topology_revision，不能认证任意未来生产者的回退或开挖语义；步跳跃、倒序、重复和拓扑变化必须报红。

## 4. 末帧补齐和逐值核对

`run.hpp:778-791` 循环结束后用末步解再推进一次，生成 geom_final；`driver/main.cpp:126-149` 导出 initial/final/range/step0..stepN，明确 stepN=final。

审计先复制每例 shadow.jsonl、geom.csv、state.csv、out.csv 至本树 tmp，再解析；源和副本哈希一致。核对以下条件：

1. header requested_steps、连续 step=1..N 和 end completed_steps 相同，end.status=ok。
2. geom 时间面齐全，initial=step0，final=stepN。
3. 188320 条顶点记录按 Fraction(decimal_text) 比较：snapshot step k 等于 geom step(k-1)，失配 0。
4. 块/顶点身份序列恒定，末帧所有所需顶点存在。
5. state 全部 1810 步有行，tt 为正且每步一致；有序 Tuple7 与 post-df06 完全相等。
6. out.csv 每步每块恰一组六自由度位移，未缺失、重复或错位。

| 算例 | 快照帧 | 仅邻帧区间 | 补末帧区间 | 精确坐标记录核对 |
|---|---:|---:|---:|---:|
""" + rows + """
| 合计 | 1810 | 1795 | 1810 | 188320 |

这些是输入可用性结论，不表示运动结果已经核验。冻结前 30 帧只给 29 区间；若要冻结 30 步运动，应额外保存源哈希绑定的 step30 终端，不能把 450 帧直接算成 450 个运动区间。

## 5. 事前运动与字段提案

`main.cpp:76-81` 的 out.csv 有 step,block,z1..z6，是本步求解后的位移；第 k 步事前只能用第 k-1 步的量。`:109-121` 的 state.csv 含 hh_cur,g7,tt,iters,conv,ratio，但无步初速度、形心或接受尝试编号。state 按接触输出，未来无接触步可能没有行；本数据恰好全步有行，不等于格式保证。

`run.hpp:265-289` 从材料 a0[11:14] 初始化平移/转动速度；`:768-772` 递推 `v_next=2*z/tt-db.gg*v_prev`。仅 out+state 仍缺初速度与 db.gg，不应由前两帧猜测速度。

最小事前版本：第 k>=2 步取 `x_pred(s)=x_k+s*(x_k-x_(k-1))`，明确称“上一位移外推”。若用 dt 比例缩放，必须另名报告，不得与原预测器混算或事后择优。

只提案、不改 b-DDA：独立每步表增加 run_id,accepted_step_id,attempt_id,is_accepted,time_start,dt_used,topology_revision,boundary_status,converged；每块增加 block_id,centroid_start,velocity_start_6dof,previous_displacement_6dof；若在迭代中选盖，再加 iteration_id,current_trial_displacement_6dof。几何输出标注持久 vertex_id、起止时间面和 motion_model。在线 hook 尚未定步长时应记录未定，不得拿 hh 代填 dt。

## 6. 可复核性与限制

审计 6 个源码文件在 D:/b-DDA/bdda2 与 D:/bdda-wt/shadow/bdda2 逐字节相同，SHA256 见 JSON；这不替代当时二进制的构建溯源，仍由 M4b 原证据承担。

复跑（只执行本树工具）：

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:TEMP='D:\\eab-wt\\cx-e2\\reports\\codex\\M4c_evidence\\tmp'
$env:TMP=$env:TEMP
python -X utf8 tools/m4c_audit_kinematics.py
```

本报告最初经 PowerShell 管道写入时中文被替换为问号，已改为本 UTF-8 工具模板重建，并检查 CJK 字符与无 BOM；JSON 原字段为 ASCII，数值与哈希重新审计，不使用中断产物拼接。
"""


def run(manifest, output):
    require(output.resolve().is_relative_to(ROOT), "evidence output must remain in workspace")
    output.mkdir(parents=True, exist_ok=True)
    temporary = output / "tmp" / "kinematics_inputs"
    local_manifest = temporary / "replay_sources_final.json"
    copy_input(manifest, local_manifest)
    sources = json.loads(local_manifest.read_text(encoding="utf-8-sig"))
    audit = {"schema": "eab.m4c.kinematics-audit.v1", "source_manifest": str(manifest),
             "source_manifest_sha256": sha(manifest), "cases": []}
    for case, source in sources.items():
        result = audit_case(case, source, temporary)
        audit["cases"].append(result)
        print(case, result["steps"], "complete intervals; source/copy hashes verified")
    cases = audit["cases"]
    audit["totals"] = {"cases": len(cases), "snapshot_frames": sum(c["steps"] for c in cases),
                       "adjacent_snapshot_intervals": sum(c["steps"] - 1 for c in cases),
                       "intervals_with_terminal_geom": sum(c["steps"] for c in cases),
                       "geometry_rows_exact_decimal_compared": sum(c["geometry_snapshot_exact_decimal_rows_compared"] for c in cases),
                       "geometry_snapshot_mismatches": 0,
                       "state_missing_steps": sum(len(c["state_missing_step_numbers"]) for c in cases),
                       "state_nonconverged_steps": sum(len(c["state_nonconverged_steps"]) for c in cases),
                       "state_ratio_gt2_steps": sum(len(c["state_ratio_gt2_steps"]) for c in cases)}
    audit["source_files"] = []
    for relative in SOURCE_RELS:
        first, second = Path("D:/b-DDA/bdda2") / relative, Path("D:/bdda-wt/shadow/bdda2") / relative
        audit["source_files"].append({"path": str(first), "sha256": sha(first),
                                     "shadow_tree_source_path": str(second),
                                     "shadow_tree_source_sha256": sha(second),
                                     "byte_equal_across_trees": sha(first) == sha(second)})
    audit["conclusions"] = {"finite_rotation_endpoint_correction": True,
                            "linear_vertex_interpolation_is_chord_not_solver_continuous_trajectory": True,
                            "hh_is_time_step": False, "state_tt_is_time_step": True,
                            "state_csv_explicit_step_initial_velocity": False,
                            "prior_displacement_prediction_available_from_step": 2,
                            "trajectory_attempt_metadata_exported": False,
                            "need_solver_rerun_for_this_dataset": False}
    require(audit["totals"]["cases"] == 15 and audit["totals"]["snapshot_frames"] == 1810,
            "this report is defined for the frozen 15-case, 1810-step dataset")
    require(audit["totals"]["geometry_rows_exact_decimal_compared"] == 188320, "geometry inventory drift")
    require(not any(audit["totals"][key] for key in
                    ("state_missing_steps", "state_nonconverged_steps", "state_ratio_gt2_steps")),
            "source boundary: do not emit the nominal Markdown conclusions")
    require(all(row["byte_equal_across_trees"] for row in audit["source_files"]), "source trees drifted")
    json_path = output / "kinematics_audit.json"
    if json_path.exists():
        previous = json.loads(json_path.read_text(encoding="utf-8"))
        require(previous["totals"] == audit["totals"], "prior audit totals differ")
        old_hashes = {c["case"]: {k: v["sha256"] for k, v in c["files"].items()} for c in previous["cases"]}
        new_hashes = {c["case"]: {k: v["sha256"] for k, v in c["files"].items()} for c in cases}
        require(old_hashes == new_hashes, "prior input hashes differ")
        if "proposed_fields" in previous:
            audit["proposed_fields"] = previous["proposed_fields"]
    audit["rerunnable_tool_sha256"] = sha(Path(__file__))
    json_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown = output / "kinematics_audit.md"
    markdown.write_text(render_markdown(audit), encoding="utf-8")
    require(not markdown.read_bytes().startswith(b"\xef\xbb\xbf"), "unexpected BOM")
    count = sum("\u4e00" <= c <= "\u9fff" for c in markdown.read_text(encoding="utf-8"))
    require(count > 1000, "Chinese report encoding damaged")
    print(json.dumps(audit["totals"], sort_keys=True))
    print(f"UTF8_NO_BOM CJK_COUNT={count}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--out", type=Path, default=ROOT / "reports/codex/M4c_evidence")
    args = parser.parse_args()
    run(args.manifest, args.out)
