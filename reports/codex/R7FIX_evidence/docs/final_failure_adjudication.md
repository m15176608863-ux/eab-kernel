# 全套首轮 18 红中的 16 个 margin 距离失败：独立裁决

## 结论

16 格失败不是 4 ULP 阈值太严，也不是当前生产距离算错。旧 `e5a_cover_oracle.margin_selection` 对浮点刚体变换后的非共面源四边形仍采用 Newell 锚平面的显示点距离；当前 margin 对该源面返回实际确定性三角曲面的距离。两者是不同几何对象。

独立复核覆盖原网格 2 族 × 2 旋转 × 2 大平移 × 3 尺度，共 24 格，恰有 16 格、29 个 VF/FV 触发旧期望差异。**29 个生产 `exact_distance_squared` 均与独立有理真值严格相等；生产显示距离全部 0 ULP 误差。** 16 格的名称与首轮全套失败清单一致。

因此，支持只修 `margin_selection` 的非平面 VF/FV 距离 oracle；保留源面描述符用的 `witness_distance`、原全部网格、标签集合/个数断言及原 **4 ULP** 断言，不允许放宽或删门。

## 独立性与算法

- 输入仍由原测试生成，受测值仍从实际 margin API 读取；原测试 helper 只用于还原“旧期望值”，**不用来证明新真值**。
- 从给定原始坐标转 Fraction，先以混合积证明源四边形确实非共面，再以精确二维转向证明 Newell 主投影严格凸。
- 由确定性源序第一耳规则，独立得两个三角形 `(3,0,1)`、`(1,2,3)`，无需调用任何生产或既有测试耳切函数。
- 自写 Fraction Gram 系统求点到三角形的无约束投影；满足三角域重心约束时取该投影，否则求三条闭线段的受限最小值；两个三角平方距离取小值。
- 最后用 100 位 Decimal 开平方作显示值。未借用生产几何原语或既有测试几何 helper。
- 这是对失败构造值的独立审查，不另宣称独立证明了盖枚举完备性；枚举集合/个数由原未变门继续看护。

样例：

| 格子 / 标签 | 旧 Newell 显示距离 | 独立三角真值 = 生产 | 误差 |
|---|---:|---:|---:|
| sep_vf / q4 / t=1000 / s=.001 / VF(v0,f3) | .00044199999997935105 | .00044200000000164843 | 0 ULP |
| ilock_sep / q4 / t=100000 / s=1 / VF(v11,f2) | .16914100196211354 | .16914100195926587 | 0 ULP |
| 同格 / FV(f5,v12) | .16914100196211354 | .16914100196092527 | 0 ULP |

## 贯入守卫变异门：无弱化裁决

复读 root 改后的 `test_guard_is_not_a_vertex_inside_check`：

1. 保留真实内部 `polyhedra_overlap` → 仅查顶点包含的变异，以及交叉方条的独立区间证据。
2. 增加公共 API 必须提前抛出 `margin self-check failed`，其中距离入口要求信息明确真表面距离为 0.0；这比要求生成错误安全输出更强。
3. 为避免新的第二道自校验掩蔽原第一道守卫的牙，另在内存编译的真实 `brute_feature_distance` 内删除交面关键一步，再**原样保留**旧 `.05 / EE`、`margin_contacts == []`、主贯入门 `AssertionError` 与旧顶点内控制组断言。
4. 没有把正常贯入 API 的哨兵义务改成“可以抛错”；只约束有意破坏后的运行。因此属于追加防线和双层变异，未减弱原门。
5. 建议把 `inflated_membership` 也加入早期异常检查，以守公共成员入口未来不绕过共享自校验；已反馈 root，由 root 决定并执行。

## 复跑与证据

命令：`PYTHONDONTWRITEBYTECODE=1 python -X utf8 reports/codex/R7FIX_evidence/docs/verify_folded_margin_gram.py`。

原样输出：

```text
24 cells checked; 16 affected cells; 29 affected contacts
29/29 exact squared distances equal independent Gram oracle; max error = 0 ULP
```

- [独立可重跑脚本](file:///D:/eab-wt/cx-e2/reports/codex/R7FIX_evidence/docs/verify_folded_margin_gram.py)
- [29 条精确输入、三角平方距离、生产对照与源码 SHA](file:///D:/eab-wt/cx-e2/reports/codex/R7FIX_evidence/docs/independent_folded_margin_gram.json)
- [守卫变异定向复跑日志](file:///D:/eab-wt/cx-e2/reports/codex/R7FIX_evidence/docs/guard_strength_review.log)

本次仅写证据文件，未改任何源文件或测试文件。不是新增独立六路 G6 的验收结论。
