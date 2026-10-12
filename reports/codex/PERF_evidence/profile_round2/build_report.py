from pathlib import Path
import json

BASE = Path(__file__).resolve().parent
junit = json.loads((BASE / 'junit_top20.json').read_text(encoding='utf-8'))
profiles = json.loads((BASE / 'profile_summary.json').read_text(encoding='utf-8'))
bench = json.loads((BASE / 'oracle_benchmark.json').read_text(encoding='utf-8'))
lines = ['# WO-PERF 第二轮：真实测试 profile 与独立 oracle 等价提速', '',
         '第一轮全套 JUnit 有 8,451 个节点，累计节点时间 1,233.483 s。该轮为 1 failed / 8450 passed，不能作为最终绿单；失败项及最终全套由总报告记录。这里针对原测试实际执行 profile，不仅测生产代表调用。', '',
         '## 1. JUnit 前 20 文件', '', '| 文件 | 格数 | 累计秒 |', '| --- | ---: | ---: |']
for row in junit['top20_files']:
    lines.append(f"| `{row['file']}` | {row['count']} | {row['seconds']:.3f} |")
lines += ['', '## 2. JUnit 前 20 节点', '', '| 节点 | 秒 |', '| --- | ---: |']
for row in junit['top20_tests']:
    lines.append(f"| `{row['file']}::{row['name']}` | {row['seconds']:.3f} |")
lines += ['', '## 3. 三条原测试的真实 cProfile', '',
          '所有命令都是 `PYTHONDONTWRITEBYTECODE=1 python -X utf8 -m cProfile -o ... -m pytest -q <原完整nodeid>`，保持原测试主体与断言。cProfile 本身显著增加开销，以下 profile 时间不是全套验收秒数；累计时间有调用包含关系，不能相加。', '',
          '| profile | 原节点 | 总秒 | 主要归因 |', '| --- | --- | ---: | --- |',
          '| invariance_ties | tied_set[I-0.0-0.001] | 34.977 | 测试独立 candidates 23.668 s，占 67.7%；其中 arc 15.263 / dot 13.019（相互包含）。生产 escape_height_covers 10.642 s。 |',
          '| invariance_height | escape_height[z0.7-0.0-0.001] | 18.216 | 生产 escape_height_covers 17.503、exact_escape 11.422、polyhedra_overlap 10.321；测试 oracle 不是主因。 |',
          '| interlocking_distance | distance_completeness_teeth[0.001] | 56.188 | 生产 enumerate_covers3 37.199，brute_feature_distance 12.894；ve3_cover 11.965、ee_cover 10.489。 |', '',
          '每条的完整前20自身耗时、生产累计耗时、独立oracle累计耗时见同名 `.json`；原始 `.pstats` 可用标准 pstats 复读。', '',
          '## 4. 等价优化，原门及原网格不动', '',
          '确实改动了两个旧测试 helper，不能声称“所有旧 helper 零改”。旧 `test_*` 门主体、参数格、断言均未改。', '',
          '- `tests/e5a_cover_oracle.py::dot/cross`：对 int/Fraction 项独立建立乘积分子分母，D取分母最小公倍数，先整数求和/差再一次构造Fraction。代数恒等式 `Σ n_i/d_i = Σ n_i(D/d_i)/D` 精确；未 import 生产 rational3 或几何原语。非有理输入保留原浮点操作顺序，新增逐位门。',
          '- `vertex`：outside 在 value≤0 时恒假，不再构造不会影响分支的范数量；同一个 d 的平方范数仅计算一次。',
          '- `arc`：保留原独立投影与 Gram 系数 aa/ab/bb、alpha/beta 的严格性判定，绝未替换成生产边锥算法。把原来必检查的 sa/sb 精确拒绝提前，在明确拒绝时不构造随后无用的 Gram 系数；重复 td/dd/tn1/tn2 只算一次。',
          '- `tests/e5a_escape_oracle.py::facet`：EE的原Gram线参数和见证，只在两侧原锥判据都接受后才构造；输入、枚举、完整输出完全不变。',
          '- 无新浮点过滤、无新缓存，故没有新误差界或新缓存签名需要突变；原 dropped-edge 缺陷牙仍执行。', '',
          '完整未优化 helper 随门保存在 `tests/perf_cover_oracle_reference.py` 和 `tests/perf_escape_oracle_reference.py`。前者逐字节等于基线，后者仅将 import 指向前者；`reference_audit.json` 记录哈希及同源校验。回归门不依赖 reports、旧工作树、姊妹源码或生产几何oracle。', '',
          '新增 `tests/test_perf_oracle_algebra.py`：随机有理数、零向量/平行退化、工程坐标、单位缩放、最小次正规；dot/cross逐值对拍、float分支逐位对拍、全部顶点/棱精确三态、完整cover标签/strictness与完整escape候选四元组逐值对拍。当前独立门：`8 passed in 1.49s`。', '',
          '## 5. 优化前后', '',
          '第一版 dot/cross 与 arc/vertex 优化后，同一原 tied-set 节点 cProfile 34.977→25.856 s；其中独立 oracle candidates 23.668→14.937 s（-36.9%），生产 escape 10.642→10.217 s 基本不变。这个 profile 早于最后一项 EE 见证延迟，因此不把它冒充最终整套秒数。', '',
          '| 冷缓存候选微基准 | 优化前秒 | 优化后秒 | 倍率 | 完整输出 |', '| --- | ---: | ---: | ---: | --- |']
for row in bench['rows']:
    case = f"R={row['rotation']}, t={row['translation']}, s={row['scale']}, off={row['offset']}"
    lines.append(f"| {case} | {row['before_seconds']:.4f} | {row['after_seconds']:.4f} | {row['speedup']:.3f} | 相同 |")
lines += [f"| 合计 | {bench['before_total_seconds']:.4f} | {bench['after_total_seconds']:.4f} | {bench['before_total_seconds']/bench['after_total_seconds']:.3f} | 全相同 |", '',
          '微基准由同一进程交替测未优化reference及优化helper，每次清其既有内容缓存；当时另有原门验证进程运行，所以只将其作为局部配对证据，独占最终全套才是验收。可复跑 `python -X utf8 reports/codex/PERF_evidence/profile_round2/benchmark_oracle.py`。', '',
          '## 6. 本目录证据', '',
          '- `junit_top20.json`：第一轮全套文件/节点前20。',
          '- `*.pstats` / 对应 `.json` / `.log`：三条原节点及第一版优化后节点。',
          '- `oracle_equivalence.xml/log`：8格新增等价门。',
          '- `ties_grid.xml/log`：全部18个原并列不变性格及原 dropped-edge 牙。',
          '- `oracle_benchmark.json`：6个冷缓存完整候选配对。',
          '- `reference_audit.json`：独立未优化reference基线核对。', '',
          '本分项不宣称最终全套≤900s，也不替代独立G6。']
(BASE / 'profile_round2_report.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
print('wrote', BASE / 'profile_round2_report.md')
