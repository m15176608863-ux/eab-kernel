# R15FIX 几何分项执行记录（O03 / O05）

## 范围与边界

- 仅修改 `src/eab/margin.py`、`src/eab/kernel3d/interlock.py`；新增 `tests/test_r15fix_geometry.py`。未修改旧测试，未提交、未改姊妹树。
- 正式报告、README、canon_map、设计同步和静态 construction policy 由主执行者汇总。
- 所有运行均设置 `PYTHONDONTWRITEBYTECODE=1`，使用 `python -X utf8`；pytest 关闭 cacheprovider，basetemp 位于本工单 evidence/tmp 内。
- 几何主 oracle 只用测试自列的有理轴向区间或顶面 `z=H+x` 的解析关系，不调用生产 overlap/events/normal/construction 原语获取答案。

## 原发现

|编号|修前红|根因与修法|修后门与变异|
|---|---|---|---|
|O03|同一常规盒，δ=2^-2000，实际 `(margin_gap, _exact_closed, exact_distance_squared)=(0.0,None,None)`；断言 `penetration output must carry exact distance/closed certificates` 报红。正负无穷/NaN原来可发布；巨大δ仅原生溢出。|贯入早返回跳过常规结果证书且 `0.0-delta` 提前转float。δ/band先 `exact_input`；`-delta` 完成后用具名 `scalar_rational(...,allow_underflow=True)`；同时附 exact_distance_squared=0 与 `_exact_closed=(delta>=0)`。下溢的负gap显示为负零但有权威平方距/分类；非有限输入或最终溢出具名失败。|δ含 2^-2000、2^-1075、2^-1074、1/8、0、负tiny，以及4个非有限/溢出格。恢复生产早返回原语句，红在证书断言，不是偶然标签顺序。|
|O05|最大float M附近5格均无 `height_display_overflow` 字段；H=M+1时 `height=inf`，exact_height本来正确。|保留正确的IEEE向上显示，新增 `EscapeSolution.height_display_overflow`。仅RN-even仍有限而向上已无有限binary64时，height=+inf且标记True；exact_height权威。RN-even本身溢出仍抛 `ConstructionDomainError`，绝不拿M伪装向上界。模块API文档逐条写明。|H=M-1、M、M+1、M+2^969、M+2^970-1，另RN溢出中点拒答；在生产返回构造里把标记强制False，红在 `finite exact root needs explicit upward-display overflow marker`。|

## 同类扫描中额外确认并修复

|项|真实路径与修前输入/错误输出|修法与精确oracle|变异红的断言|
|---|---|---|---|
|S-G1|`escape_height_brute` 把O05结果裸返回float，H=M+1得到inf且丢失证书。|裸float兼容API无字段可承载证书，故遇标记True抛具名 `ConstructionDomainError('escape_height_brute.height',...)`；文档引导用完整EscapeSolution。|删除生产overflow检查，原具名异常断言 `DID NOT RAISE`。|
|S-G2|`dilatancy_profile` 只保留h，不带exact_height或overflow标记；三个相同极大根，原斜率甚至是inf-inf产生NaN。|每行增量传播 exact_height/height_display_overflow；相同精确根中心差分为0。|生产字典把标记改False，红在 `profile must propagate exact root and overflow certificate`。|
|S-G3|B顶面z=2^60+x，A右边界x=δ+1/8，δ∈{-1/16,0,1/16}。独立精确根H+δ+1/8应有斜率1；原来对三个相同舍入h作差，报0。|只在精确根/精确δ上完成中心差分，再一次 `scalar_rational` 具名构造；显示h仍向上。|生产差分操作改回用已舍入h，红在 `affine top-plane slope survives common-height cancellation`，实值0≠1。|
|S-G4|同一倾斜盒，δ∈{1/16-2^-100,1/16,1/16+2^-100}。原 `d * direction[i]` 在默认float方向(1,0,0)把三个精确位置合并，精确求根前已丢失信息，斜率仍错报0。|offset每分量先 `F(d)*F(component)` 完成精确乘积，并传给现有精确扫掠。|内部offset构造改回混合乘法，红在 `exact offset product must not collapse distinct sample points`，实值0≠1。|

以上四条是本次同类扫描的具体新增修复，不虚报为审查方原始发现；S-G2/S-G3同一profile输出路径不同失误，分别给出断言。

## 执行证据

- [原代码红日志](file:///D:/eab-wt/cx-e2/reports/codex/R15FIX_evidence/o03_o05_red.log)：`18 failed, 1 passed, 3 deselected in 0.57s`。最初新门不含S-G4；排除变异门，只运行真实回归。
- [S-G4修前红日志](file:///D:/eab-wt/cx-e2/reports/codex/R15FIX_evidence/o03_o05_offset_red.log)：`1 failed, 25 deselected in 0.16s`。
- [最终新门绿日志](file:///D:/eab-wt/cx-e2/reports/codex/R15FIX_evidence/o03_o05_green.log)：`26 passed in 0.58s`。
- [真实内部变异脚本](file:///D:/eab-wt/cx-e2/reports/codex/R15FIX_evidence/o03_o05_mutations.py)、[完整断言JSON](file:///D:/eab-wt/cx-e2/reports/codex/R15FIX_evidence/o03_o05_mutations.json)、[执行日志](file:///D:/eab-wt/cx-e2/reports/codex/R15FIX_evidence/o03_o05_mutations.log)：6个变异全部被对应断言杀死；每个变异前后未变异门均绿。只在内存exec生产函数源码，不改磁盘生产，不在结果后追加假数据。
- [周边针对性合集日志](file:///D:/eab-wt/cx-e2/reports/codex/R15FIX_evidence/o03_o05_targeted.log)：`INTERRUPTED_BY_COORDINATOR`。为避免与正式全套争抢负载，按主执行者要求中止重复合集；没有通过结论，完整周边由正式全套覆盖。

## 同类扫描范围及未改路径

[机器清单](file:///D:/eab-wt/cx-e2/reports/codex/R15FIX_evidence/o03_o05_scan.json) 对 margin 加 kernel3d 共13文件生成61函数、116 return、37下溢/定向舍入候选；这是候选清单，不冒充任意几何全域证明。

全文读核margin与interlock；定向核查covers3带证书的VF/FV/EE/VE3/EV3/VV3构造、entrance3采样brute终态、geom3全特征距离和所有escape消费者。其他候选：

1. `margin._resolve` 贯入距离0是定义的哨兵，内部返回Fraction(0)平方量；修复对象是对外MarginContact漏带证书。
2. `body_distance` 显式接触模型的0是定义的哨兵；真正分离距离使用严格sqrt构造，下溢不会悄悄返回0。
3. `inflated_membership` 早返回是拓扑整数状态，不是物理标量显示。
4. 常规MarginContact早已带精确平方距/closed；本次补齐贯入路径。
5. Cover3显示下溢带exact_gap_squared/sign/direction/params等相应证书；VV3恰零早返回带精确零gap。
6. entrance3 brute的allow_underflow只用于内部停止区间判断；最终裸输出使用严格scalar_rational(up)。
7. geom3全特征距离的交叠零是精确零，非零默认严格；显式allow_underflow由保留平方证书的调用者选择。
8. exact_geom中nextafter至无穷是过滤区间包络，不是对外物理高度；不把它误计为O05同错。
9. tia_sensitivity消费EscapeSolution但自身造型已有D400输入界，本次未构造出可达M级根；不以静态字段使用即宣布新缺陷。

## 测试改写台账与遗留

- 旧测试修改：0；删除/skip/xfail/缩参数：0。新增26格，其中6个真实内部变异。
- 全套、M4a门、canon指针与中心文档同步由主执行者统一完成，本分项不宣称独立G6退出。
