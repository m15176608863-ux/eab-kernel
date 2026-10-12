"""Documentation-only UTF-8 repair; run after the frozen full-suite audit."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
p = HERE / "kernel/coverage.json"
rows = json.loads(p.read_text(encoding="utf-8"))
for row in rows:
    api = row["api"]
    if api in ("eab.kernel2d.g0.g0_distance_completeness", "eab.kernel2d.g0.g0_exit_completeness"):
        row["proof"] = ("正常报告完整字段加真实内部投影缺陷后的非零报告逐值核对。"
                        "投影构造内部x坐标减s，真实枚举产生distance got=4s/truth=3s/error=s，"
                        "exit t=1/witness=s；完整非空failure元组独立核对，不追加假盖。")
        row["limits"] = "三档有限解析输入族与具体内部缺陷；不声称所有失败原因/任意拓扑完备。"
    elif api == "eab.kernel3d.g03.g0_distance_completeness3":
        row["proof"] = ("正常报告完整字段；构造内部坐标偏移导致distance got=4s/truth=3s/error=s，"
                        "逐值核全部failures/construction_failures。另在真实vf_cover调用位置遗漏face3，"
                        "剩余真实盖最短5s，独立核completeness_failures=(x,25s²,9s²)、error=2s及其余字段。")
        row["scales"] = ["正常报告: 2^-400 / 1 / 2^397", "非零与完整性失败报告: 2^-400 / 1 / 2^395"]
        row["limits"] = "失败子族最高坐标为24s，s=2^395保持各坐标低于2^400；不把参数指数与最大坐标指数混淆。"
    elif api == "eab.kernel3d.exact_sweep.surface_events":
        row["proof"] = ("盒z向事件全集t={2,5,8}，每条normal由标签源点内联叉积；非二进制时刻{2/21,11/21,20/21}。"
                        "另由独立xy消元及平行投影端点入射，严格逐(label,time)核对完整集合，时间跨标签交换变异被捕获。")
assert not any("??" in json.dumps(row, ensure_ascii=False) for row in rows)
p.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("Repaired four metadata rows; production and test files untouched.")
