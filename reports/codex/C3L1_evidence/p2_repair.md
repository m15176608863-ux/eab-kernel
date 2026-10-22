# C3-L1 P2 逐查询耗时汇总（仅报告，不设性能门）

全部逐查询数据见 [差分原始记录](file:///D:/eab-evidence/reports/codex/C3L1_evidence/diff_repair.json)。

Python 核是单次生产函数；Python 总时间另含 dataclass/JSON 编解码；C++ 时间含 ABI、ctypes、JSON 解码。
两侧均不含进程/DLL 启动及输入解码；一阶可动性均使用预先装配的接触集。没有把包装层计时冒充 C++ 核计时。

| 输入组 | 查询族 | 数量 | C++总秒 | Python查询+JSON秒 | Python核秒 | C++/Python总时间 |
|---|---|---:|---:|---:|---:|---:|
| T1b_frozen_projection | assembly | 36 | 0.783536 | 0.926826 | 0.885369 | 0.845 |
| T1b_frozen_projection | first_order | 36 | 50.667509 | 97.931634 | 97.884772 | 0.517 |
| exact_transform | assembly | 36 | 0.046950 | 0.080219 | 0.072095 | 0.585 |
| exact_transform | first_order | 36 | 0.037417 | 0.070695 | 0.067236 | 0.529 |
| exact_transform | lock | 54 | 0.110226 | 0.147085 | 0.124329 | 0.749 |
| tia2d-2_formal | assembly | 114 | 3.961465 | 4.307853 | 4.162018 | 0.920 |
| tia2d-2_formal | first_order | 114 | 16.170277 | 25.513439 | 25.435759 | 0.634 |
| tia2d-2_formal | lock | 350 | 15.015477 | 23.076034 | 19.828864 | 0.651 |

## 边界

- 单次顺序观测，机器并行负载未控制；不作统计加速比或生产性能结论。
- 这是每个新查询状态的冷调用，不是新进程冷启动；没有重新生成冻结数学证据。
- 本表不包含 LP 内部主元/位长统计；另见 LP 差分报告。
- 源记录 SHA-256：`a46061de3a5fe8f38f22be9ff11d3b1db095b5a54740e2c23596b7b7a463fa10`。
