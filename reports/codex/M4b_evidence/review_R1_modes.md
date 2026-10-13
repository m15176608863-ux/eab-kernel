# M4b 独立复核 R1：四入口模式与环境隔离

- 复核者：`baseline_gates`，没有实现被审查的 bdda 生产代码（本代理负责基线/验收脚本）。
- 范围：M4b 新增开关，不代表全仓库 G6。
- 结论：**critical = 0，major = 0，minor = 0；本范围通过。**

## 源码核查

1. `bdda2/driver/main.cpp:22–31`：CLI 先解析模式，未设由 `Options` 默认 Legacy；eab/未知值在读输入和开输出之前返回 2。没有未知值回退。
2. `bdda2/driver/run.hpp:61–80,215–221`：库默认 Legacy、显式 Options 注入，不读进程环境。直接传 Eab 或非法 enum 也拒绝，不仅 CLI 字符串拒绝。
3. `studio/engine2.py:49,178`：桥的 `run_forward(..., detect="legacy", shadow_path=...)` 明确透传；`_env()` 先删除宿主检测变量，之后只加本次显式设置。eab/非法值返回错误，未偷偷跑 Legacy。
4. `bdda2/studio/engine_bridge.cpp:41,196`：Qt `runForward` 直接给库 Options 设置模式。`pinnedEnv` 清理检测环境变量；不是“Qt 仅依赖 CLI 环境”的假接入。
5. `verify_t0.py/verify_cpp.py/verify_force.py/verify_fast.py` 的 bdda2 调用清理检测变量；Faithful 门同时去掉宿主 solver，Fast 门显式设置 solver。

## 独立动态检查

- 另写探针（不是仅转述作者的测试）运行未设、legacy、eab、空串、SHADOW、Legacy、unexpected 七种模式。
- 未设/legacy：RC 0，原四类 CSV 全部存在；即使宿主指定影子路径，也没有影子文件。
- 后五种：RC 2，无原 CSV 和影子文件；eab 错误明确包含“未获所有者批准”。
- Python/Qt 实际入口由新增测试核查；post-tree 全套 **336 passed, 1 xfailed**，对应原 **319 passed, 1 xfailed + 新增 17**。
- Legacy 配置了会抛异常的 hook 仍调用次数为 0。作者的内部 guard 变异使 **calls==0** 及 **shadow_error.empty()** 两条目标断言红，其他 case 保持绿；不是产物后加假数据。

## 证据与边界

- [独立动态证据](independent_r1_r2_checks.json)
- [post 完整测试](file:///D:/bdda-wt/shadow/bdda2/build/m4b/post/pytest_clean_layout.log)
- [内部路径变异证据](file:///D:/bdda-wt/shadow/bdda2/build/m4b/switch_mutation_evidence.json)
- 本阶段提供桥 API 参数，没有新增 GUI 下拉控件，也没有让反演/力监测路径启用替换检测。便利封装未暴露 shadow 时继续使用 default Legacy，不声称所有界面按钮均可选择 shadow。
- 零影子分配/复制/I/O由分支与陷阱门证明；模式检查本身仍存在，不能把“零影子工作”宣传成“总 CPU 时间严格相等”。

复核探针首轮曾将 `Legacy/legacy` 用作目录名，Windows 不区分大小写导致测试目录冲突；已分类为复核脚本输入错误，改为七个唯一序号目录重新验证，没有修改生产代码。
