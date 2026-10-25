# WO-C3L4 ABI / 独立 consumer 交付清单

本文件仅记录 ABI 子任务；不替代整个 WO-C3L4 收尾、所有者新鲜树或非作者对抗验收。

## 实际验证

- root 统一构建已核 C3-L4 ABI：EAB2_C3L4_ABI checks=87 failed=0；C 头生产/静态门由 root 完整 CTest 记录。
- 最小字节隔离 consumer：EAB2_TIA_CONSUMER cases=6 sensitivity=18 mismatch=0。
- 隔离仅 10 个文件，python -I -S，无 src、差分 harness、pybind、姊妹源码或 test DLL；1.7798556999769062 秒。不是 Git 新树。
- PE 门：EAB2_RELEASE_ABI status=PASS exports=31 structures=28 findings=0。
- 定向纯 Python 门：18 passed in 0.09s。pytest 已显式 -p no:cacheprovider 与 --basetemp。
- git diff --check 对本子任务已有跟踪文件通过；无 Git 写操作。

## 关键文件与全部改动路径

| 文件 | 用途 |
|---|---|
| [C ABI 头](file:///D:/eab-wt/cx-c0/eab2/include/eab2/c_api.h) | 新 capability、显式维度/ID/stride 描述符和两个正式入口 |
| [C ABI 实现](file:///D:/eab-wt/cx-c0/eab2/src/c_api.cpp) | typed L3 结果生命周期、完整种子校验、精确传播/批敏感性调用、JSON |
| [ABI C++ 门](file:///D:/eab-wt/cx-c0/eab2/tests/test_c3l4_abi.cpp) | 三通道互异、35 类负输入、快照/句柄/FP/原子失败 |
| [C 头门](file:///D:/eab-wt/cx-c0/eab2/tests/test_c_header.c) | C 编译、L4 capability 与 sizeof 探测 |
| [ABI_CONTRACT](file:///D:/eab-wt/cx-c0/eab2/ABI_CONTRACT.md) | 发布 ABI v1 冻结函数/签名/能力/28 结构字段 offset 表 |
| [独立 consumer](file:///D:/eab-wt/cx-c0/tools/eab2_tia_consumer.py) | 只依赖标准库与公开 C 头，六代表例完整链 |
| [PE 冻结门](file:///D:/eab-wt/cx-c0/tools/eab2_release_abi.py) | 完整 PE export 表与 C 头/冻结表/运行 capability 比较 |
| [旧构建审计](file:///D:/eab-wt/cx-c0/tools/eab2_audit.py) | 原公开入口清单增补 L4 两函数 |
| [Python 负门](file:///D:/eab-wt/cx-c0/tests/test_eab2_release_abi.py) | 手构 PE oracle、7 类坏表、结构/签名/能力漂移和 consumer 隔离 |
| [工作入口草案](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_evidence/entry_abi.md) | 开工时合同及接口协调，不当成验收声明 |
| [唯一 consumer 结果](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_evidence/consumer.json) | 隔离复跑的逐链节点、双三态、导数/方向/标签/有效条件 |
| [隔离清单](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_evidence/consumer_isolation.json) | 完整命令、逐文件 SHA、计时、原始末行 |
| [隔离完整日志](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_evidence/consumer_isolation.log.gz) | UTF-8 输出的唯一压缩原件 |
| [发布 ABI 门结果](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_evidence/release_abi.json) | 31 exports / 28 structs / 0 findings |
| [最小字节副本](file:///D:/eab-wt/cx-c0/eab2/build/tmp/c3l4_consumer_standalone/) | 忽略构建 tmp，不入库，不称 Git 新树 |
| [临时验证目录](file:///D:/eab-wt/cx-c0/reports/codex/C3L4_evidence/tmp/) | 显式 pytest basetemp |

## 边界

没有声称人工使用者签字或完成整个里程碑独立核查。冻结依据是已执行的独立真实调用脚本与发布 DLL，后续所有者验收仍须按主工单完成。资源限额不是整个敏感性算法墙钟保证；非 smooth Jacobian 返回 null，不把单侧斜率伪装为唯一梯度。