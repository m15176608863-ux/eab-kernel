# eab-kernel

统一接触内核：石根华入口块 E(A,B) 理论（Contact theory, 2015/2021）的实现，以及跨引擎接触记录的公共契约与对账门。

- 设计正本：`D:\E(A, B)\07 程序设计·统一接触内核方案.md`
- 理论正本：`D:\E(A, B)\01 E(A,B) 理论内核·精细版.md`
- 纪律：`AGENTS.md`

## 状态：Phase 0（契约与 oracle 落盘）

已有：
- `src/eab/contact_record.py` — `ContactRecord` 契约（四组字段）、`CoverType`/`Mode` 词汇、各引擎状态码映射表、JSON 往返、典范序键。
- `src/eab/readers/bdda_df.py` — b-DDA 插桩内核 dump（`bdda_debug_contacts/df18/df22/verts.csv`）→ `ContactRecord`。
- `src/eab/readers/bdda3d.py` — 3-b-dda 入口 dict（JSON 导出）→ `ContactRecord`。
- `src/eab/readers/tf_probe.py` — 3DDA tf.cpp 探针（`retry_contact_pair_probe.tsv`、`contact_pair_stage.tsv`）→ `ContactRecord` / `PairStageRow`。
- `tools/ingest_fixtures.py` — 从姊妹仓库的既有导出复制夹具并记录溯源（sha256）。
- `tools/ingest_bdda3d.py` — 在 3-b-dda 自己的环境里把算例入口 dict 导出为 JSON（子进程，零 import）。

运行：

```bash
python tools/ingest_fixtures.py
python tools/ingest_bdda3d.py
python -m pytest -q
```

## 阶段路线

P0 契约与夹具 → P1 二维盖内核（G0 自证 + G1 同构 + G4 活动集实验）→ P2 三维凸内核（G2 对 tf.cpp 探针）→ P3 凹块局部角覆盖 → P4 可微与互补 → P5 接缝与切换。
