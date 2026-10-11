# E5a · interlock 下游测试契约适配

## 修改范围与边界

只修改 `tests/test_invariance_interlock.py` 的两个标签门，新增独立 `tests/e5a_escape_oracle.py`；本子任务未修改任何生产代码。
原逃逸高度、胜出标签、解析高度、刚体/单位变换、state、梯度/导数、margin 距离与冻结间隙门保持原样。

## 复现与取舍

1. 首轮下游发现 `_normal_noise` 对精确新增微交叉 EE 的单位棱 float 叉积为零，产生除零；交 geom 代理最小适配。
2. 适配后，sensitivity/walls 全绿；旧 `tied_labels` 运动前后相同断言失败。独立 Fraction oracle 确认 `z0.7`、offset `(0.23,0.07,0)` 的 `EE(edge25,27;edge26,32)` 在运动前无效、运动后有效，候选高度恰为解析高度。不能按噪声删掉它。
3. `z0.7,t=1e5,s=1e-3` 又使三个参考标签不再有效；旧“reference 必是子集”也是假理想几何前提，不保留这一假断言。每格完整候选与完整 tie 清单均核独立实际输入 oracle，identity 基准清单也独立核对，未漏掉/跳过这三条。
4. margin 旧首项标签逐字不变断言在八个已复现格红；改为完整独立盖集合、无重复、每个见证距离、两条入口各自枚举序首项。identity 的原基准首项仍保留。

机读旧/新口径与强度说明见 `invariance_interlock_ledger.json`；原 72 个逃逸 offset 格、162 个 margin 标签格全部保留。

## oracle 与牙

完整候选由原始顶点/面环自行列出所有 VF/FV/EE 对；精确部分为循环 Newell、Gram 法锥系数、Gram 线参数与投影/域窗口距离，均不调用生产几何/盖/互锁方法。
逃逸层噪声与 tie 规则仍是 E5b 范围，本 oracle 显式独立求值这套旧政策，不宣称已将它精确化。
纯 oracle 的模型、噪声、候选结果缓存只由完整坐标/面环/offset 键控，未共享生产缓存，未减参数。
新增牙在生产 `ee_cover` 内部丢掉上述有效 EE，完整独立候选比较必须准确识别该缺失。

## 分段验证证据

- `downstream_fast_adapted`：`5 failed, 73 passed in 225.68s (0:03:45)`，sensitivity/walls 原断言绿，五条旧 tie 标签等值红。
- `downstream_fast_tail`：`8 failed, 438 passed, 36 deselected in 158.86s (0:02:38)`，八条旧 margin 首项标签等值红；期间仅新增未被该子集导入的 oracle 文件，日志如实记录漂移。
- `interlock_margin_labels_exact`：`162 passed in 41.69s`，source drift 空。
- `interlock_ties_exact`：`19 passed in 179.66s (0:02:59)`，最终 18 个完整运动格（每格四个原 offset）和新增真实内部缺盖牙全部绿，wall=186.532 秒，source drift 空。

最终无漂移全套由主线程执行。性能目标不以减少独立 oracle 的输入或跳过候选实现；本子任务不声称达到 600 秒。
