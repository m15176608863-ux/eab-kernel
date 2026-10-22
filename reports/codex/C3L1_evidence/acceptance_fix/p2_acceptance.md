# C3-L1 P2 逐查询耗时汇总（仅报告，不设性能门）

全部逐查询数据见 [差分原始记录](file:///D:/eab-wt/cx-c0/reports/codex/C3L1_evidence/acceptance_fix/diff_acceptance.json.gz)。

Python 核是单次生产函数；Python 总时间另含 dataclass/JSON 编解码；C++ 时间含 ABI、ctypes、JSON 解码。
两侧均不含进程/DLL 启动及输入解码；一阶可动性均使用预先装配的接触集。没有把包装层计时冒充 C++ 核计时。

| 输入组 | 查询族 | 数量 | C++总秒 | Python查询+JSON秒 | Python核秒 | C++/Python总时间 |
|---|---|---:|---:|---:|---:|---:|
| T1b_frozen_projection | assembly | 36 | 0.795838 | 0.990151 | 0.944273 | 0.804 |
| T1b_frozen_projection | first_order | 36 | 51.823910 | 101.262815 | 101.210750 | 0.512 |
| exact_transform | assembly | 36 | 0.052488 | 0.091750 | 0.081845 | 0.572 |
| exact_transform | first_order | 36 | 0.040728 | 0.079932 | 0.075891 | 0.510 |
| exact_transform | lock | 54 | 0.124330 | 0.171645 | 0.144385 | 0.724 |
| tia2d-2_formal | assembly | 114 | 3.342917 | 4.135996 | 4.000809 | 0.808 |
| tia2d-2_formal | first_order | 114 | 15.818412 | 24.637197 | 24.563443 | 0.642 |
| tia2d-2_formal | lock | 350 | 15.676877 | 25.283732 | 19.963491 | 0.620 |

## 边界

- 单次顺序观测，机器并行负载未控制；不作统计加速比或生产性能结论。
- 这是每个新查询状态的冷调用，不是新进程冷启动；没有重新生成冻结数学证据。
- 本表不包含 LP 内部主元/位长统计；另见 LP 差分报告。
- 源记录 SHA-256：`711feaf00fe01bdeaa4aa51cce7b4e4cf5b28af9bd494a60b54a2a011e13a60a`。
