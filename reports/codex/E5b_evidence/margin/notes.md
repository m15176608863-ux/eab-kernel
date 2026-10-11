# WO-E5b 裕度层 / 零高度门：实现与证据

## 精确默认与显式窗口

- `body_distance`、`margin_contacts`、`inflated_membership` 新增 `contact_window=None`。`None` / 0 不引入接触分辨率；给定坐标严格贯入仍为哨兵 / INSIDE，真实正间隙不自动钳零。
- 决策使用原坐标构造的 `Fraction` 平方距离。默认最小值及并列比较精确；`delta`、`band`、`atol` 的边界比较不读浮点开方。`atol=None` 为零。
- 非共面源环在默认路径展开为真实确定性三角面；VF/FV 的三角标签为 `('face', source_fi, 'triangle', i, j, k)`。显式窗口保留历史源标签报告，但实际三角表面的平方距离决定接触与成员状态；差异超过构造误差的 Newell 假面见证被替换为真实三角见证。
- `MarginContact.closed` 保存精确布尔值，不读可能下溢成零的显示 `margin_gap`。`2^-1075` 正间隙门验证显示值为零仍为 OUTSIDE / open。
- `entrance_block_convex` 先把原坐标提升为有理数再求 `b-a`；`2^54` 坐标与半单位偏移的支撑函数门能区分先浮点相减的错误。

### 窗口的可重复数学定义

共同入口 `exact_sweep.contact_models(A,B,w)` 给出一个**有限充分证书集合**：

1. 原体 `(A,B)`；
2. `A` 的六个精确平移 `(A ± w e_i, B)`，`i=0,1,2`；
3. 若可证明星核，`(core_w(A),B)` 和 `(A,core_w(B))`。

任一模型精确非贯入，窗口可报告接触。平移模型的位移长度正好为 `w`；星核模型取顶点平均中心 `c`，逐三角面严格内侧认证，令 `R=max_v ||v-c||_1`、`alpha=min(w/R,1/2)`，核心为 `c+(1-alpha)(P-c)`。被去除的径向壳层厚度至多 `alpha R <= w`，核心包含于原体。它证明的是**局部表面浅贯入**，不是全局刚体最短脱开距离。

有限集合未找到证书，不等于真正欧氏贯入深度大于 `w`。这不是完整球形 erosion。互锁在**同一个模型集合**中取精确最早非贯入根的最小值，避免裕度和互锁采用不同窗口模型。早期“任意支持轴欧氏位移上界 OR core”方案已撤回；其单体接触分类虽充分，但与互锁只用 core 的最早窗口根不一致。只保留 core 的探测又使旧 55 格中的 19 格报红，证据见 `core_only_probe.log`；共同有限集合保住全部 55 格，见 `finite_window_probe.log`。

`contact_resolution(A,B)` 仅作为调用方可显式选取的旧窗口公式。DDA / TIA 适配器若仍需要旧分辨率，必须传此值；未传时库不推断理想共面、不吞掉亚分辨率贯入。显式窗口标签/舍入并列仍是报告策略，不能拿旧近似标签反推精确根或分离证书。

## 测试迁移与牙

- E5a2 的 41 个 margin 红格：原全部断言留在显式旧窗口模式；54 个 touch/subtol 全网格另逐格对独立整数四面体并集 SAT 核对默认精确关系。
- E5a2 的 3 个 brute 零高度红格：原 5 个参数格、两种静止/无起伏位移均保留，改核对独立整数动态 SAT 区间并集的精确最早根。显示浮点必须是“不低于根的最小 binary64”。另加同拓扑、共享有理数界面的无抖动体，原两条 `== 0.0` 断言原样保留。
- `assertion_retention.json`：三个被改测试文件的原 128 条 assert 文本无一缺失；原 36 个 test 函数无删除，原参数装饰器未缩减。
- `test_rewrites.json`：44 个原失败 node 的逐条处置、测试改写台账、4 项内部突变。忽略窗口由 `explicit-window` 关系断言抓住；默认偷偷用旧 ctol 由 `default-exact` 关系断言抓住；不钳零与吞贯入分别由原 report-band / sentinel 门抓住。
- 新门还覆盖无穷/负窗口、折叠源环假平面、低于 binary64 的正间隙、精确差点。缓存以原始顶点/面内容及被测实现指针为键；`test_content_cache_is_value_identical_to_the_uncached_exact_path` 对默认/显式、分界、贯入、分离、缩放与工程平移逐值对拍完整输出。

## 验证文件

- `verified.log` / `verified.xml`：较早任意支持轴窗口版本，`640 passed, 50 deselected in 212.41s (0:03:32)`；**不是最终共同窗口版本的验收证据**。
- `models_cache.log`：共同有限窗口 + 缓存的 89 个 targeted 格全绿。
- `final_shared` 首次抓住缓存漏掉 `cover_witness` 注入身份（640 绿、1 红）；补键后临界门与新精确门 15 绿。最终以 `final.log` / `final.xml` 为准。该日志包含全部 margin 文件，以及 invariance 文件的 margin / brute 格；其它互锁格与全仓由主代理统一跑。

## 边界

本分工不声称完成 G6 全套独立退出门。这里的闭合曲面前置条件、三角化规则沿用精确内核契约；没有给非法自交网格定义新的实体意义。窗口是保守有限证书模型，不得写成完整欧氏贯入深度求解器。默认三角对角 EE 的冻结朝向由 frozen 分工补齐，最终全仓结果由主报告汇总。

## 最终子集结果

`641 passed, 50 deselected in 92.85s (0:01:32)`

对应 `final.xml`，原 44 个红 node 全部 PASS，无 skip/xfail。共同有限窗口模型及构造函数缓存失效修补均已包含。主代理随后独占跑全仓；本组件不以子集结果替代全仓验收。
