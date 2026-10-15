"""Rerun M5c A1-A4 semantic tests; freeze small, inspectable JUnit evidence.

The runner itself uses only the standard library. pytest is the repository test
runner, invoked as a subprocess. No hash/provenance tests are selected.
"""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports/codex/M5c_evidence"
TMP = OUT / "tmp"


def main():
    TMP.mkdir(parents=True, exist_ok=True)
    environment = dict(os.environ, TEMP=str(TMP), TMP=str(TMP), PYTHONIOENCODING="utf-8")
    junit = TMP / "semantic_teeth.junit.xml"
    command = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
               "--basetemp", str(TMP / "pytest_semantic_evidence"),
               "--junitxml", str(junit), "tests/test_m5c_robustness.py",
               "tests/test_m5b_robustness.py"]
    completed = subprocess.run(command, cwd=ROOT, env=environment, text=True,
                               encoding="utf-8", errors="replace", capture_output=True)
    (OUT / "semantic_teeth_pytest.txt").write_text(completed.stdout+completed.stderr, encoding="utf-8")
    if completed.returncode:
        raise SystemExit(completed.returncode)
    cases = list(ET.parse(junit).getroot().iter("testcase"))
    rows = [dict(name=case.attrib["name"], seconds=case.attrib.get("time"),
                 passed=not any(child.tag in ("failure", "error", "skipped") for child in case))
            for case in cases]
    mutations = [row for row in rows if row["name"].startswith("test_internal_")]
    assert len(mutations) == 22 and all(row["passed"] for row in rows)
    source_paths = ["tests/test_m5c_robustness.py", "tests/m5c_teeth_oracle.py",
                    "tests/test_m5b_robustness.py", "tests/mutation_support.py",
                    "src/eab/kernel2d/model_robustness.py", "tools/m5b_robust_replay.py"]
    result = dict(complete=True, timestamp=datetime.now(timezone.utc).isoformat(),
                  command=command, returncode=completed.returncode, collected=len(rows),
                  executed=len(rows), skipped=0, mutation_count=len(mutations),
                  hash_guards_selected=False, mutation_method="real internal source-body replacement",
                  oracle_imports=["fractions.Fraction"],
                  semantic_policy="every mutant must raise AssertionError matching its named semantic gate",
                  source_hashes={p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in source_paths},
                  mutations=mutations, tests=rows)
    (OUT / "semantic_teeth.json").write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    table = "\n".join("| `"+row["name"]+"` | 语义 kill |" for row in mutations)
    report = """# M5c A1–A4 语义补牙证据

## 结果与边界

- 完成 A1–A4：四类 R2 结构条件、r2、R1 L1 范数与 P1/P2 双盒、误差式各项、严格等号、近阈值、真实 oracle 核对。
- 收集 = 执行 = {count}，0 skip；新内部变异 {mutations} 项全部由具名语义断言捕获。
- 变异执行未选任何源码哈希/冻结摘要测试（`hash_guards_selected=false`），没有在输出之后伪造数据。
- 全部生产算法保持不变。新增 oracle 仅导入 `fractions.Fraction`，不共享生产几何、求根、区间原语。
- 近阈值接受格端点余量/误差为 `1/199999`（约 5.000025e-6）。标签与括区均由独立平移事件 oracle 检查。
- 大平移及单位格新增 3 格 L1 对偶范数门；既有 R2 有理旋转/大平移/极端单位元门一并运行。
- 早期回返格确实签错首盖：正确 VE(3,0) 在 17/40，错误候选 VE(2,3) 在 3/5；独立闭式点为 (33/32,-2)。EV 删除格也确实签错首盖（正确 EV=.3，错误 VE=.5）。
- 严格凸性与竞争者等号格检查的是充分证书契约；保守界等号不必意味着真实凸性丢失或真实首盖改变。
- 误差删项门以独立展开值检查预算本身，而不是把任何预算降低都冒称找到了真实轨迹反例。

## 变异表

| 真实内部变异 | 结果 |
|---|---|
{table}

## 重跑

`python tools/m5c_mutation_evidence.py`。脚本显式配置本树 TEMP/TMP、`-p no:cacheprovider`、`--basetemp`。
完整 pytest 输出见同目录 `semantic_teeth_pytest.txt`；细目与当前源码哈希见 `semantic_teeth.json`。
先行证明与反例边界见 `docs/m5c_teeth_theory.md`；源码见 `tests/test_m5c_robustness.py` 与 `tests/m5c_teeth_oracle.py`。
""".format(count=len(rows), mutations=len(mutations), table=table)
    (OUT / "semantic_teeth.md").write_text(report, encoding="utf-8")
    print(json.dumps({key: result[key] for key in ("complete", "collected", "executed", "skipped", "mutation_count")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
