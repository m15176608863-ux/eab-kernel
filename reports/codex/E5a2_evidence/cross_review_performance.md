# WO-E5a2 性能改动内部交叉审查（A1 代理，只读）

## 结论

本次限定审查未发现所查性能改动新增的答案改变、精度降低或几何 oracle 共用被测原语。新增整数化都是正分母上的等价代数运算，并非浮点过滤；因此不新增需要“误差界 ÷10”的过滤界。

**这不是 G6，也不是全仓 0 critical / 0 major 的结论。** 检查发现一项需明确交接的既有非 canonical 对象缓存可变性限制，见第 5 节。没有改生产代码或测试文件。

## 1. 审查范围与数学核对

- `src/eab/rational3.py`：`dot` 用各项乘积分母的 lcm，只在最终和归一；叉积的每个二乘积差用 gcd 构造公分母。分母始终为正，原 Fraction 值严格相同。快路仅接受六个 **builtin Fraction** 分量；float、Dual、混合值仍走原表达式。
- `predicates.cross2_sign / dot2_sign`：全部 Fraction 时直接计算正共同分母上的分子。两个交叉项的分母补因子次序逐项检查正确；非 Fraction 路径的原过滤界、次正规项与原值回退不变。
- `covers3._outside_dot_band`：`value² > tol² |a|² |b|²` 同乘四个正分母，左右 numerator/denominator 位置一致；只省去 Fraction 中间构造，未改变严格 `>` 或 tol<=0 分支。
- `covers3._integer_plane` / membership 整数行：平面 `(n,h)` 统一乘正 lcm 并除正 gcd，不翻朝向；查询点统一分母 D 后，整数残差正好等于 D 乘缩放后的有理残差。距离阈值比较中的 D²、tol 分母、整数法向平方均在正确一侧。源 `(n,p)` 仍留在 payload，给纯 Fraction 对拍使用；外侧正 tol 最终仍由精确最近凸包点决定，而非误用平面距离。
- `covers3.ee_cover`：精确叉积非零已证明两条无限直线不平行；最近参数与法锥可行性无关。先排除不合格的 B/A 法锥再构造参数，只减少无效候选的无副作用计算，不改候选方向顺序、返回特征、strict、extent 或构造点。
- `g03_exact.sat_model / overlap`：原轴集及 independent hull 逻辑保持；区间条件等价为 `bmin-amax <= n·x <= bmax-amin`，清除正分母后 low<0 / high>0 分离，等号边界。该 oracle 未 import geom3 / covers3 / rational3 / predicates 的几何或优化原语，独立性未被提速破坏。

## 2. 门是否真的经过优化路径

- 1369 对三维数据逐项比较 rational3、geom3、exact_geom 与直接 Fraction 乘加/叉积公式，含一般、退化、工程坐标、非二进有理数、最小次正规、近最大有限数。
- `test_fraction_geometry_operations_really_dispatch_to_integer_arithmetic` 明确 trace 两个被测几何模块到 rational3 的调用，要求恰好 `['dot','cross']`，排除了“对拍全绿但优化没接线”。
- 二维整数符号门 2616 对逐个计算真值；另把 `_float_value` 改为响亮抛错，全部 Fraction 对拍仍通过，证明不会悄悄退回旧浮点路径。
- EE 延迟门在每个边对、两个 tol、全部 9 个 scale/offset/skew 格上对比旧 eager 次序，完整 Cover3 相等，而非仅数量相等。
- SAT 与整数 plane 门保留原 Fraction 投影式作为优化等价对照；它们明确只认证此代数变换，不伪称为新的完整几何 oracle。原 G0 的独立几何 oracle 仍是单独实现。
- 审阅内部突变日志：rational3 dot 第三项改负，三条 module 对拍均在值等式报红；SAT 严格界改闭界，四种尺度门均在边界三态等式报红；整数 plane offset 反号，三种工程坐标门均在 membership 等式报红。不是其它偶然断言红。

## 3. 浮点次序与 Dual 通道

除读 diff 确认原 fallback 表达式原样保留，还从 `git show HEAD:<file>` 只读提取原 dot/cross 函数并执行对照：

- geom3：410 个函数调用，float 返回按 IEEE-754 字节比较，Dual 比较 primal 和全部导数通道的字节；全部相同。
- exact_geom：同样 410 个调用；全部相同。
- 输入含一般宽量级随机值、正负零、最小次正规、零 primal 非零导数的 Dual。不存在 val/float 降级或“只检查 primal”的比较。

[机读检查与缓存限制复现](file:///D:/eab-wt/cx-e2/reports/codex/E5a2_evidence/cross_review_performance_checks.json)。

## 4. 缓存 payload 与键

本单未新增缓存装饰器。`_support_planes_cached` 的既有内容寻址键仍含双方全部顶点、全部面环、完整标签集合及实现函数；扩展后额外包含 `_integer_plane` 的实现身份，payload 加入整数平面/法向平方。不同对象只要**完整内容相同**即可安全共用，故没有必要凭空加入对象 id，去掉不存在的 id 也不是有意义的突变。

`g03_exact.sat_model` 既有键仍为双方完整原始坐标 tuple；新查询点 x 不在模型内缓存，而在每次 overlap 单独整数化。二维/三维整数算术均不新增全局缓存。

新增串用门证实 canonical-self 盒对象变更坐标后内容键更新；它不能证明所有上游 Polyhedron 缓存会失效。下一节是确切边界，交付不可省略。

## 5. 发现的既有限制（不是本次整数 payload 新引入）

**`exact_convex_view` 已有 `_convex_view` 对非 canonical 源对象原地修改不失效。** 复现：将 box 的 6 号顶点 z 改为 1.25 后，canonical view 是另一个对象；调用 membership 建立它，再把源顶点整体 x+10。旧源对象在 x=0 返回 1，同样修改后坐标的新对象返回 -1。

该早退代码在 HEAD 已存在，且本次性能改动未改它；新平面缓存接收的 canonical view 本身没有拿到已改的源坐标。因此不能把它归因于整数行键漏数据，但也不能声称“所有可变对象缓存已验证失效”。现有新串用门的注释已经限定为 exactly canonical box，报告也必须保留限定。

建议：本单按已有不可变使用约定报告此限制并交给后续所有者；若要支持任意源对象原地修改，需要为 exact_convex_view 建立内容签名/失效契约，单独补非 canonical 变更和 faces 变更门。这次只读审查未自行扩大范围修复。

## 6. 实跑证据与边界

复跑：

```text
29 passed in 0.71s
```

命令：`PYTHONDONTWRITEBYTECODE=1 python -X utf8 -m pytest -q tests/test_e5a2_integer_arithmetic.py tests/test_e5a2_bilinear_integer.py -p no:cacheprovider --basetemp=reports/codex/E5a2_evidence/tmp/cross_review_performance --tb=short`。

[完整日志](file:///D:/eab-wt/cx-e2/reports/codex/E5a2_evidence/cross_review_performance_tests.log)。这只是限定优化门与额外只读比对，不是完整全套、冻结性能基准或正式独立 G6。
