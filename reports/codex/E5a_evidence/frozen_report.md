# WO-E5a frozen 最小适配与测试口径台账

## 边界

只修改 `src/eab/kernel3d/frozen.py` 的 EE primal 朝向/构造适配及 `tests/test_frozen_ee_sign.py`。
`margin.py`、一般 frozen 面/低维盖公式、Dual-through EE 算术均未在本子任务改写。

## 先红后绿

- 原门：`5 failed, 48 passed in 15.60s`（`--maxfail=5`，`frozen_before.xml`）。
- 原因一：一般原始面环 EE 标签被送入凸包 canonical `facet_normal3`，两个几何/编号契约被混用。
- 原因二：改成独立精确 oracle 后，原来被近平行噪声带删掉的微交叉 EE 暴露 frozen 的浮点叉积归零/朝向错误。例如 yaw=0.001、seed=4、t=0 的 ea=(0,4)、eb=(2,6)。不能只改测试掩盖。
- 修后全部冻结子集：`113 passed in 82.32s (0:01:22)`；原始 JUnit 为 `frozen_final.xml`。

## 最小生产适配

1. `frozen_ee_sign` 只在 primal 坐标用精确棱向量叉积、两侧精确源面环棱弧挑正负；`tol` 仍是调用者域窗口，不添加法向噪声带。无有效双侧候选时保留原 B 侧方向兼容行为。
2. `ee_normal_generic` 的非 Dual 入口用精确叉积后安全单位化，避免微交叉 float 叉积为零或反号；Dual 入口仍用原算术公式。
3. `_as_float` 保留非 Dual 精确坐标，只对 Dual 提取 primal 值，避免已有 Fraction 数据先被舍入。

## 测试不减弱

详见 `frozen_test_ledger.json` 逐条旧/新口径及理由。全部原输入格保留，不新增 skip/xfail。
一般源面环 EE 对每对棱的存在/不存在、严格性、参数、在程及法向均核独立 Fraction oracle；canonical 严格 facet 另核完整 EE 标签集合和独立法向。
原工程坐标六格、端点十八格全部精确分类，不再用理想刚体的八重并列/端点位置覆盖舍入后事实。
保留物理 gap/frozen signed gap 测量门，另增未作一般运动时的解析八对 gate。
四个正常非退化格新增 primal 与未改 Dual 值及非零导数门。

## WO-E5b 明确保留

微交叉时的 Dual 叉积/归一化仍可能因浮点消去或平方下溢失败；本单只保证新增精确盖能安全进入 primal 冻结路径，**不声称全部 frozen Dual 极端几何已精确化**。
一般面及低维盖泛型构造、`margin` 的整体精确语义仍交 WO-E5b。最终全套与 canon 指针修复由主线程执行。
