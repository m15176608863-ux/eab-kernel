# WO-C0 工作合同与执行计划

- 目标：按 `docs/eab2_design.md` 第二版 r3b §8.4 实现 MSVC x64 精确数值 C0；Python 为独立裁判。
- 设计 SHA-256：`6d174ecc4f1326d5bac21c56c8d333485fb50bbaef3a12150e94eaff14cb4dac`，入口实测一致。
- 写域：仅 `D:/eab-wt/cx-c0`；产品代码在 `eab2/`，辅助工具在 `tools/`，证据在本目录，报告在上级 `C0_report.md`。
- 回滚锚：入口工作树干净；`eab2-c0 @ 7f9510502ba265e53b5be8de4be22308dfe65f9a`。保留原提交内容；未运行 Git 写操作。撤销新增文件或逐文件审阅差异由所有者决定，不自动 reset。
- 不做：工单全部非目标与可选项；不修改 Python 数学合同；不下载、安装或写外部目录。
- 成功检查：MSVC 编译；静态核心及 DLL/C 头单测；坏 FP 环境拒绝；独立 ctypes 与 Python 全选定语料逐位/状态差分；Python 快档与四分片全档；静态构造、纯度和大文件门。
- 退出边界：Claude 安排的非作者对抗核查和获准新鲜树复现仍由所有者安排，本轮不得替代或冒称完成。
- 时间估计：历史 H1 快档约 5 分钟、全档约 40–45 分钟；最终冻结源文件后执行全档一次。无性能门。

## 计划（单一活动阶段）

1. 只读核验、Boost 准入与 Python 快档基线：已完成。
2. 精确数值、ABI、自检、差分工具：已完成（同一工单分工，不创建其他工作线）。
3. 定向、内部缺陷注入与 H1 快档/四分片全档：已完成，全部通过。
4. 中文报告与交付清单：已完成；本轮停止源代码编辑。

实施者可执行事项已完成。里程碑仍为 C0_PARTIAL：独立对抗核查与获准新鲜树复现待所有者安排，不能将计划完成误读为 C0_DONE。

## 复跑入口

```powershell
cmd /c eab2\build_eab2.bat
python -X utf8 tools/eab2_diff.py --dll D:/eab-wt/cx-c0/eab2/build/eab2_test.dll --output reports/codex/C0_evidence/diff.json
python -X utf8 tools/h1_run_gates.py --name c0_fast --evidence-root reports/codex/C0_evidence
python -X utf8 tools/h1_run_gates.py --name c0_final --runslow --evidence-root reports/codex/C0_evidence
```

H1 名称必须每次新建，已完成/中断目录不复用。全部 pytest 禁用 cacheprovider，显式 basetemp；本单进程 TEMP/TMP 指向本目录 tmp 子树。
