# E5a2：interlock 最小桥接说明

## 1. 范围与原因

A1 把给定坐标上的实体内部相交保持为 `1`，正 `tol` 仅改变分离侧 `-1/0` 距离报告；这暴露了既有逃逸候选层对舍入簇复用状态的依赖，不是精确表面谓词应吞掉的误差。

原始复现（`interlock_probe.json`）：offset = `(-0.21140068220020514, -0.20949049564529884, 0)`；同一旧舍入簇中较低候选 `0.18028294516552315` 真贯入，而已有较高候选 `0.1802829451655232` 不贯入。不能拿前一个候选的精确状态代表后一个不同的 float 输入。

仅修改 `src/eab/kernel3d/interlock.py` 与新增 `tests/test_e5a2_interlock_bridge.py`。原 `test_interlock_escape.py` / `test_interlock_candidates_contract.py` 无删改，全部参数格保留。

## 2. 修正与证明边界

1. 同簇只允许完全相同的候选高度复用答案；不同高度逐个精确核验。
2. 若一簇没有可验收的名义候选，按原 `r/nz` 法向舍入报告尺度构造一次向上候选 `nextafter(z+r/nz, +inf)`。**实际返回的高度本身**必须令 `A.translated((off_x, off_y, off_z + height))` 经精确谓词得到非内部相交；绝不只验高处而返回未验证低处，不把任何真贯入改标接触。
3. 直接从原 A 做调用方一致的一次平移；不先平移 offset 再平移 height，避免两次 float 舍入改变实际被验对象。
4. 仅查询 `state == 1` / `state != 1` 的所有 interlock 调用改传零 tol。由 A1 的语义，正 tol 与零 tol 的内部布尔完全相同，故省掉分离侧欧氏距离带计算是逐值答案不变的优化。`geom_tol` API 参数保留；brute 仍执行其数值转换，但不再虚称其改变贯入判定。
5. winner / ties 保留旧 nominal 候选簇的报告政策，不是返回位置实际 active-contact 证书，不是精确最小高度或精确最早候选的证明。特别是 nominal 零簇，既有 `_candidates` 对 z<=0 未核 extent，标签不能解释为已认证的面内接触。浅 nz 的上探可能越过后一个很近的名义簇；返回的安全性仍核验，但全局精确最早根仍属 E5b。

这只是 A1 严格拓扑与旧 interlock 构造层间的最小正确适配；未完成一般折面法锥、候选完备性、margin/entrance/frozen 的 E5b 迁移。

## 3. 独立门

新门的 oracle 只读原顶点坐标：按 x 重建挤出体上下折线，在两体节点共同划分的每个区间内，以 Fraction 解两组严格仿射不等式，并取独立分段线性根。没有调用生产 membership、normal、cover、ray、distance、triangulation 或其内部辅助。

- 12 格：零位移、原同簇失败、需上探的非对称位移，各乘尺度/坐标 `(1,0) / (1e-3,0) / (1e3,0) / (1,1e6)`；检验返回实际浮点平移确实不贯入、构造根误差在声明的尺度/舍入报告范围内、真初始贯入不得报零。
- 1 门：独立解析 boxes 的 `-2^-80 / 0 / +2^-80 / 0.1` 输入，零/正 tol 的内部布尔逐个对拍。
- 1 内部缺陷注入门：把活代码中的 `lifted=nextafter(z+r/nz,+inf)` 改成 `lifted=z`。只接受明确的 `candidate set incomplete` ValueError，或指定的独立 oracle 安全性/根精度断言；不接受任意偶然 ValueError。此附加牙并非 A1 共面证书牙的替代。

## 4. 验证证据

| 证据 | 结果 |
|---|---|
| `interlock_repair.log` | 原 escape 文件 19 passed in 67.03s（零 tol 提速前） |
| `interlock_bridge.log` | 新14 + 原 escape19 + 原 candidates14，47 passed in 45.89s |
| `interlock_bridge_final.log` | 文档清理误删 dataclass 字段产生 8 failed / 6 passed；故意保留失败日志 |
| `interlock_bridge_final2.log` | 恢复原 `n_candidates` 字段后，14 passed in 6.34s；生产/测试随后冻结 |
| `../a3/interlock_candidates_reprobe.log` | 另代理原 candidates 全14格复跑绿 |
| `../a3/interlock_bridge_audit.json` | 另代理4格只读安全审查，含工程坐标/旋转；不是 G6 |
| `../brute_zero_tol_diagnostic.json` | 性能代理同40帧二分输入、布尔、最终高度逐个相同，9.81659s → 1.91113s |

最终全套由 root 在源冻结并修正文档指针后独占运行；本报告不把以上局部门冒充全套/G6。

## 5. 复跑

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -X utf8 -m pytest -q tests/test_e5a2_interlock_bridge.py tests/test_interlock_escape.py tests/test_interlock_candidates_contract.py -p no:cacheprovider --basetemp=reports/codex/E5a2_evidence/tmp/interlock_bridge_rerun
```
