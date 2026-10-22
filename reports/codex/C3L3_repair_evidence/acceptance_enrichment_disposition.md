# MINOR-1：20 个已知实例的处置

权威运行见 [differential.json.gz](differential.json.gz)。下表仅为该运行的索引，不是第二份差分输出。
每项均先以原始几何重建 A/b/c 核证，再准许证明可用性不同；语义失配均为 0。
Python 均为 exact_threshold=null、attained=null；C++ 均为合法开阈。

| 外部验收实例 ID | C++ 阈值 | 括号 | 处置 |
|---|---|---|---|
| `sweep/g1/koureas/0/1/mumax=0.5/steps=1` | 0/1 | [0/1, 1/4] | 独立核证后接受 |
| `sweep/g1/koureas/0/1/mumax=1.0/steps=0` | 0/1 | [0/1, 1/1] | 独立核证后接受 |
| `sweep/g1/koureas/0/1/mumax=1.0/steps=2` | 0/1 | [0/1, 1/4] | 独立核证后接受 |
| `sweep/g1/koureas/0/1/mumax=4.0/steps=0` | 0/1 | [0/1, 4/1] | 独立核证后接受 |
| `sweep/g1/koureas/0/1/mumax=4.0/steps=1` | 0/1 | [0/1, 2/1] | 独立核证后接受 |
| `sweep/g1/koureas/0/1/mumax=4.0/steps=2` | 0/1 | [0/1, 1/1] | 独立核证后接受 |
| `sweep/g1/unreversed/0/1/mumax=0.5/steps=1` | 0/1 | [0/1, 1/4] | 独立核证后接受 |
| `sweep/g1/unreversed/0/1/mumax=1.0/steps=0` | 0/1 | [0/1, 1/1] | 独立核证后接受 |
| `sweep/g1/unreversed/0/1/mumax=1.0/steps=2` | 0/1 | [0/1, 1/4] | 独立核证后接受 |
| `sweep/g1/unreversed/0/1/mumax=4.0/steps=0` | 0/1 | [0/1, 4/1] | 独立核证后接受 |
| `sweep/g1/unreversed/0/1/mumax=4.0/steps=1` | 0/1 | [0/1, 2/1] | 独立核证后接受 |
| `sweep/g1/unreversed/0/1/mumax=4.0/steps=2` | 0/1 | [0/1, 1/1] | 独立核证后接受 |
| `sweep/g1/unreversed/1/4/1/2/mumax=0.5/steps=1` | 1/4 | [1/4, 1/2] | 独立核证后接受 |
| `sweep/g1/unreversed/1/4/1/2/mumax=1.0/steps=2` | 1/4 | [1/4, 1/2] | 独立核证后接受 |
| `sweep/g1/reverse_i1/0/1/mumax=0.5/steps=1` | 0/1 | [0/1, 1/4] | 独立核证后接受 |
| `sweep/g1/reverse_i1/0/1/mumax=1.0/steps=0` | 0/1 | [0/1, 1/1] | 独立核证后接受 |
| `sweep/g1/reverse_i1/0/1/mumax=1.0/steps=2` | 0/1 | [0/1, 1/4] | 独立核证后接受 |
| `sweep/g1/reverse_i1/0/1/mumax=4.0/steps=0` | 0/1 | [0/1, 4/1] | 独立核证后接受 |
| `sweep/g1/reverse_i1/0/1/mumax=4.0/steps=1` | 0/1 | [0/1, 2/1] | 独立核证后接受 |
| `sweep/g1/reverse_i1/0/1/mumax=4.0/steps=2` | 0/1 | [0/1, 1/1] | 独立核证后接受 |

本次全族共 73 项证明可用性订正，其中上述 20 项逐一复现，其余 53 项由扩展网格发现。
查询次数不等共 28 项，原始两侧次数均保存在权威结果；次数是选基/搜索成本，不当数学等价字段。
