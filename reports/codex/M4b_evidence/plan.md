# WO-M4b 执行与验证合同

日期：2026-10-13。初始 eab HEAD `0810051ddebe07b39f7313e40517cbaf0988ad25`，b-DDA HEAD `cbf3642e31a3d68790fb62446da185b55ee70e63`；两个指定工作树初始 `git status --short` 均为空。

## 边界

- 可写：`D:/eab-wt/cx-m4`、`D:/bdda-wt/shadow`；系统临时目录仅供隔离测试。b-DDA 的编译、运行均在其专用工作树。
- 不做：真正 eab 替代、solver/legacy 接触语义修改、姊妹主树执行或写入、Git 提交/分支/切换/重置/暂存/worktree 操作。
- 回退锚：上述 HEAD、修改前源码副本、修改前编译二进制与输入/产物 SHA256。仅保留回退依据，不自动执行回退。
- 通过条件：逐字节矩阵、b-DDA 原门比较、三入口显式模式与错误隔离、30 步以上 15 例闭集回放及 M4a 对照、输入变异门、eab 全套及静态门。测试绿不冒充六路 G6 或真实替换批准。

## 计划

1. 已完成：读纪律、冻结基线；同源码编译和两次全视界运行证明可复现性；基线完整布局全套 319 passed / 1 xfailed。
2. 已完成：只读 shadow 和四入口传递；只在 shadow 内构建快照，默认原计算次序不动；C++ 156+32 检查、Python/Qt 定向门通过。
3. 已完成：15 例默认全视界（1810 步）× 未设/legacy/shadow，与基线四类既有 CSV 及 stdout/stderr 逐字节比较，全部相同、零排除。
4. 已完成：450 帧 / 两个时间面回放及冻结门；45 帧 M4a 计数全部相同，两条逐记录末位几何差异有独立解释。全默认 1810 帧审计 GREEN，未分类 0。
5. 已完成：两侧最终测试、Qt smoke、格式变异、四分片 eab 全套 12662 passed、静态门 0 违例、六路 M4b 范围独立审查无未关闭 critical/major；停止本轮并发计算后完成 7 次有效样本计时，正常宿主后台活动如实记录。
6. 已完成：中文报告、交付清单、残余风险及后续真正替换所缺条件已保存；最终 QA 核对 243 个本地链接、193 份交付文件哈希、451 份受测代码/测试/夹具无漂移、25 份 b-DDA 日志哈希。两仓库 HEAD 不变且无暂存改动，等待 Claude/所有者验收。

## 可复核入口

- b-DDA：`bdda2/build.bat`、`bdda2/build_studio.bat`、`--smoke`；HANDOFF 中 `verify_t0.py`、`verify_cpp.py --family --engine gen2`、`verify_fast.py --assert`、`verify_force.py` 等；新增 `tools/bdda/verify_m4b_shadow.py`。
- eab：`PYTHONDONTWRITEBYTECODE=1 python -X utf8 -m pytest -q -p no:cacheprovider`；`python -X utf8 tools/check_exact_construction.py`；新增 `tools/m4_shadow_replay.py`。
- 验收环境先清除 `BDDA_DETECT`、`BDDA_DETECT_SHADOW`、`BDDA_SHADOW_PATH`，固定 `BDDA_MAXX=2560`、`BDDA_MAXY=1355`。
- 用户禁止新 worktree，故不执行仓库常驻纪律中的 Git worktree 动作。最终使用无 Git 元数据的新鲜文件导出补做洁净环境检查，并明确其不等于提交后的新克隆 G6。
