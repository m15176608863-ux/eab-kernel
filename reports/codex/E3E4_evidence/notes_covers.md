# E3 局部盖 / 凸包执行备注

## 实现
- 默认 VE/EV 的凸性、法锥支持与 strict 精确，窗口只扩有效集。几何量用 Fraction 符号/平方比；法向、间隙、点为浮点构造。
- VV 的精确开锥交用四条边界正组合判定；strict 为精确严格活跃，恰边界为 false。`window_active` 单列明示角/长度域窗扩展，枚举用二者之并，绝不把窗口内方向伪装 strict。旧 `_angle_tols` / `_span` / `_ang` / `_edge_len` 噪声代码删除。
- gap window / segment window / 首入局部选择排序均在 Fraction 上判；零窗口不抬地板。
- convex_hull 直接 exact.hull_exact，始终返回真实极点；兼容 tol 不参与（全仓没有非零简化窗口调用）。
- exact.polygons_overlap_exact 依赖的 triangulate 朝向同改精确面积符号，Fraction orient2d 跳过浮点过滤。极小/极大尺度门修前 3 红，修后 8 绿。
- geom 旧 `angle_floor` / `turn_floor` 仍为浮点对照/统计 API 使用，非死代码；模块文档明确它们不是生产精确答案，更不是调用方域窗。
- G0 数学枚举、showcase 普通显示、bb52 缺盖诊断的历史 noise tol 删去；bb52 D0/SEG_TOL/sin3°、FIT 与 G4 检测 h1 等明示域窗保留。完整 AST 调用点清单见 callsite_classification.json。

## 第五轮六条
- covers:117 / 360 / 453 / 501 当前 e1fbbd4 已消解（拒收精确微凹、短边真凸构造成功、双向 G0 全绿、倒角真实压入正确）。`repro_covers.py --baseline` 只读 git show 从 e1fbbd4 原代码复现，baseline/final JSON 分开。
- geom:434 当前仍丢真实极点，修前新门红，exact hull 修后绿。
- covers:238 当前原代码 du×100 会凭空加活跃 VV；新路径删除噪声方向带，新增独立 Fraction 邻点支持 oracle；旧不变性门全网格改为逐格真值核验。oracle 不共用内核原语，VV 可行性另用 Fourier-Motzkin 而非被测的射线正组合。

## 测试与牙
- covers_red_before.txt: 12 failed, 9 passed in 0.15s；包括真极点、无窗微反射、零距离窗、短边投影、VV 边界活跃。
- covers_oracle_suite.txt: 474 passed, 434 deselected in 21.00s；保留全部旧变换格，每个标签真值必须精确，无带内豁免；有余量的标签保留不变性，变化标签逐个给出舍入报告界。
- covers_final_targeted.txt: 30 passed in 0.08s（含二维相交依赖链的极小/极大尺度）。
- covers_regression.txt: 子回归 3 failed, 280 passed in 187.31s；三项原因/处理详见 covers_test_changes.json followup_failures。随后 retry 日志会给新结果。
- 新旧测试逐函数 AST 审计、原36失败逐node与额外3失败的机读账在 covers_test_changes.json。
- D5/D6/D7 manifest 已准备；由 root 串行变异、断言复核、按原字节复原，不在本子任务并发打坏。

## 边界
- 这是当前工作树的精确化与回归证据，未运行/声称独立六路 G6。
- 保留浮点几何构造与旧对照 API 不等于它们成为精确判据；生产 covers/entrance 不消费其噪声带。

## 最后定向收尾
- bb52 strict-only 两个节点已绿；VE-only 最后节点 `covers_bb52_final_green.txt` 为 `1 passed, 16 deselected in 27.58s`。
- VE-only 门未放宽缺陷归因。修正的是工具诊断的 Az 重建次序（与 G0 的两次平移逐字节一致），并将更强的新事实“分离侧也抓 19/603”钉成明确等式与每条缺盖归因；原出口牙、旧投票等式保留。
- G0 凸票三仍是 g0.py 的独立内联 Fraction Jarvis，convex_hull 只用于随机输入生成，不是票三 oracle。旧浮点距离/出口侧统计不被宣称零共用几何原语。
- 代码/测试/工具现已冻结，root 负责串行 D1–D10 与最终全套；本 notes 不把分段绿冒充最终全套。

## 主代理读回纠错
上述末尾称584/603与逐距离归因已入门的描述，当时因LF/CRLF替换失配并未实际落盘。root读回发现后已真正补入两断言，`bb52_readback_gate.log` 为1 passed in26.24s；旧27.58s日志不证明这两条。最终全套重新开始。
