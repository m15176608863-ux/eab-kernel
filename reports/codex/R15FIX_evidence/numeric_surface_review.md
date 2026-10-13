# R15FIX 同类扫描复核

范围：全 `src/eab` 与 `tools` 的 Python 源码；AST 候选索引由 [scan_numeric_surface.py](file:///D:/eab-wt/cx-e2/reports/codex/R15FIX_evidence/scan_numeric_surface.py) 生成。
[初轮候选清单](file:///D:/eab-wt/cx-e2/reports/codex/R15FIX_evidence/numeric_surface_scan.json) 覆盖 58 模块、2014 个 sum/显示边界/return/float零初值候选（索引采集时 O02/O03 开发中，最终另生成 final 清单）。
这是候选清单加人工逐族复核，不是每个候选均独立证明，更不是静态完整性证明。

## 已确认同根并修复

|族|生产点|处置与看护|
|---|---|---|
|O01 混合精确/float|单体/多体 `raw[j]*C.cols[j][i]` 在求和前已舍入|两边均显式 Fraction 乘积；乘积退回变异分别击中合力断言|
|O01 精确量从float零累加|单体/多体 `forces`|有理零起算，完整选列和最后 checked scalar；两边零初值变异均红|
|O01 汇总前构造失域|两个 force-report 的 fmag|精确平方范数只比较，不输出/舍入中间范数；μ=2^20、W=2^1010 的最终 (-1,W) 可表达，旧路径原生上溢，两边变异均红|
|O02 同一完整坐标|generic配对上块center_z+lz|私有精确jet保留至完整顶点；pair mutation红|
|O02 同一完整导数|sin内先构造cos(angle)*seed|单位seed取得采样导数系数，再精确结合seed/amp/坐标；最终可表达的小/大seed均绿，早seed缩放变异红|
|O03 早返回漏证书|margin贯入输出|distance²0与exact closed同时返回；delta/band在早返回前验有限|
|O04 schema前拒收|JSON parser|词法只解析，分派后逐字段验域；巨整数三种真实入口回归|
|O04 同类schema遗漏|bdda3d nsign/owner|离散身份精确integer；逐字段撤步变异红|
|O04 连续域绕过|bdda3d t1/t2/d1/fa/coh/tens|已知连续字段不依赖token类型/配对存在；六个逐字段撤步变异红|
|O05 证书包装丢失|escape_height_brute、dilatancy_profile|裸float包装具名拒答；profile传播exact root+overflow标记；两变异红|
|O01/O05 汇总前舍入|profile相邻高度差、offset乘积|精确根差和精确delta×direction后才最终显示；两个独立斜平面oracle及对应内部变异|

## 未改候选及判别依据

- `lp.py` 的 float 零初值、浮点累加、`_fl` 是**候选单纯形层或带精确证书的视图**；浮点层不是最终真值，原始有理LP原始/对偶/射线/Farkas核验仍保留。不能为清理字符串 `0.0` 改成 Fraction 并混淆这两个层。精确层的系数、基与行累加从有理零开始。
- `dual.seed` 的 float 零是种子通道的确切零，不是精确量累计器；全局 Dual 每次运算的构造合同不改。O02 仅修具名完整造型。
- `exact_geom._id` 使用 outward interval 运算：零初值后每步 nextafter 扩包络；不是将 Fraction 合力当作普通 float 输出。区间无穷是保守过滤边界，不是物理高度。
- `geom3._inward_vertex_direction` 是无调用点的旧私有候选（全仓引用仅定义）；其输入为已构造面单位法向，逐步使用向量API，并非将现行精确LP量从float零累加。未借本轮删除死代码或声明其一般正确性。
- `limit` / `limit_multi` 形心和臂长用于内部参考坐标/不确定性筛查；原模型用给定参考点精确构造力矩和荷载平移，返回证书独立核验。这里不将既有不确定性报告提升为严格误差界或全域稳定性保证。
- `MarginContact` 常规分支、`Cover3` 的下溢显示有精确平方距/符号/方向字段；`body_distance` 的零是接触哨兵，真正分离距离默认严格构造。详见 [几何扫描](file:///D:/eab-wt/cx-e2/reports/codex/R15FIX_evidence/o03_o05_scan.json) 与 [分项说明](file:///D:/eab-wt/cx-e2/reports/codex/R15FIX_evidence/o03_o05_summary.md)。
- 2D/3D entrance 的初始接触时间零由精确事件合同定义；brute的允许下溢用于内部终止区间，最终裸时间走严格scalar边界，不等于O03遗漏证书。
- reader 的元数据计数/离散身份保留整数；CSV的整数字段仍按已有整数文字格式，不擅自引入JSON指数格式。M4汇总为整数计数；冻结证据、夹具、姊妹输出均不改。
- showcase 绘图中点、机制放大图和 tia_sensitivity 的四位浮点均值使用**已构造的近似显示量**，不是保留精确证书的物理求解输出，未以此承诺完整有理理想值或清洗成新数值模型。它们与已有近似/可视化范围仍在设计边界中。

## 复核限制

没有以搜索“无命中”证明全域正确；也没有把普通浮点可视化批量改成精确API。
新增受支持物理输出缺陷均有红→绿→真实内部变异证据；静态辅助门只是局部准入维护。
未发现新的几何成员或LP精确容量错误，不等于穷尽证明；本次团队交叉核查不是审查方独立G6。

最终补充：首次全套揭示合力严格下溢拒答过窄，现追加 exact_contact_forces 与当且仅当下溢的 contact_force_display_underflow；正负零符号、半最小次正规、可表达次正规和最终上溢分别守门，原容量门原样保留。
