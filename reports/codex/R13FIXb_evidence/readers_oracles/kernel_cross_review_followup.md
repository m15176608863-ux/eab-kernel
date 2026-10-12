# Kernel 4 项发现补门后复核

只读检查追加的 9 个参数格；没有修改生产、测试或覆盖清单，不是 G6。命令、测试文件前后 SHA256 与实测输出见同名 JSON / log。

| 原 API | 结论 | 证据 |
|---|---|---|
| `kernel2d.g0.g0_distance_completeness` | **关闭** | `_project` 内部表达式注入发生在 scalar/Cover 构造之前；三尺度真实生成非零误差，完整报告与非空失败 payload 逐值按独立解析解核对 |
| `kernel2d.g0.g0_exit_completeness` | **关闭** | 同一真实内部投影缺陷；三尺度核 t=1、非零 witness=s 及全部失败 payload 参数 |
| `kernel3d.exact_sweep.surface_events` | **关闭** | 新门按源面/顶点和独立 xy 消元建立每个 `(label,time)` 对；VF/FV 与 EE 都覆盖，时刻含非二进制值，三尺度核全集，补上原集合门的绑定缺失 |
| `kernel3d.g03.g0_distance_completeness3` | **原问题大部关闭，但留一窄 gap** | 内部 `_float_vector` 注入成功覆盖非零 worst_abs_error、failures、construction_failures；然而 `completeness_failures` 仍被断言为空列表，没有非空 `(x,minimum2,truth2)` 的逐数值参考 |

3D 剩余项不是生产真错断言，而是原“所有数值 payload 已逐值覆盖”口径尚差一条路径。可以保留窄缺口，或从实际枚举/特征选择内部注入缺陷，使最近精确候选平方与独立真距离平方不同，按三尺度逐值核这个 payload；不能在报告产出之后拼数据。

复核开始时机读清单仍只引用旧成功门/旧时间集合门，应加入新引用。作者可能正在更新；本文件不替覆盖清单做改写。
