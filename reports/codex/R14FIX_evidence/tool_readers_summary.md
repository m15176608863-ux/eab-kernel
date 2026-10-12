# R14FIX 同类扫描：工具层物理数值读取/导出

## 新发现与修法

| 真实入口 | 修前缺陷 | 修法 |
|---|---|---|
| `tools/g2_bdda3d.py::load_case_full` | 裸 JSON 把 `1e-400` 顶点坐标读成 0 | `numeric_decode.loads` 精确解析，再 `decode_tree` 转回原 binary64 连续量模型 |
| `tools/bb52_g0.py::load_blocks` | CSV x/y 裸 float | 连续坐标 `scalar_rational`，ID 保留直接整数解析 |
| `tools/bb52_g0.py::legacy_contacts` | CSV o2 裸 float | 具名 checked scalar 边界 |
| `tools/g4_multistep.py::read_detparams` | d0/h5/h1/w0 裸 float | 各字段具名 checked scalar 边界 |
| `tools/g4_multistep.py::read_contacts` | 非 ID 字段裸 float | 各连续量具名 checked scalar；整数身份仍精确 |
| `tools/m4_capture_family.py::fixture_summary` | 已有捕获的 detparams 摘要裸 float 吞零 | 摘要各连续量先检查再转换；没有运行 capture |
| `tools/ingest_bdda3d.py::main` | 接收子进程 stdout 时裸 JSON，随后保存了错误零/inf | 精确 JSON 解码及连续量检查先于写入 |
| `tools/ingest_bdda3d.py::CHILD` | 顶点 `map(float,v)` 在输出 JSON 之前已吞零 | 本仓库维护的子脚本内联独立 `checked_vertex`；不 import eab 或姊妹实现来做检查 |

支持域复用读取器契约：连续数值允许舍入，但给定有限非零精确值的 binary64 RN 必须为有限非零；否则具名异常。不是强行套 D400。JSON 整数字面量/整数 ID 不经过 float；普通 0.1 几何最终仍为原来的 binary64 0.1，没有把旧几何数据偷换为精确 1/10。

## 修前红 → 修后绿

- `tool_readers_red.log`：七入口分别测试 `1e-400`、`-1e-400`、`1e400`；末行 `21 failed, 9 passed in 0.39s`。14 个正负下溢格均为真实静默零的拒绝门失败；上溢格包括返回 inf 和未具名底层异常。
- `tool_child_red.log`：子脚本顶点的三个极端输入先红，末行 `3 failed, 30 deselected in 0.14s`。
- `tool_readers_green.log`：新入口、普通输入、精确大 ID、原 binary64 坐标模型、内部变异及既有 ingest 文案门，末行 `44 passed in 0.20s`。
- 没有改写、删减或跳过旧测试。

## 变异牙

`tests/test_r14_tool_readers.py` 为七个实际入口分别撤掉内部 exact decoder，JSON 恢复裸 `json.loads`、CSV 恢复裸 `float`。每个生产调用链重新把 `1e-400` 变成零，相应 `pytest.raises(ConstructionDomainError)` 均以 `DID NOT RAISE` 变红。子脚本把 `checked_vertex` 恢复 `float` 时，`pytest.raises(OverflowError, match="vertex")` 也以 `DID NOT RAISE` 变红。

可重跑脚本 `tool_reader_mutations.py`、原始 traceback `tool_reader_mutations.log` 保存八条 `VERIFIED_RED`；未在返回数据后追加伪造缺陷。

## 隔离与不变范围

- 所有输入均为本树 pytest basetemp 或证据 tmp 中的最小临时文件。
- M4 仅测试 summary，用本地桩替代已另有门看护的几何/ContactRecord；未运行 capture、未运行姊妹 exe。
- ingest 的 subprocess 被本地 stdout 桩替换；CHILD 只在内存假的 `bdda3d` 模块上执行本仓库字符串，无姊妹源码或进程执行。
- 未更改静态分析 policy/manifest 的 JSON 读取；那些不是物理连续数据。
- 已有 fixtures 不变；全仓、M4a 门和冻结证据一致性由主代理总验证。
