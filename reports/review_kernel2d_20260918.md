# kernel2d 对抗审查与修复记录（2026-09-18）

独立审查员（只读仓库，反例脚本在会话 scratchpad `review_kernel2d/`）对 `covers.py` / `geom.py` 逐项攻击：
**推翻 4 处、边界情形 3 处、未能推翻 4 项**。全部反例已固化为 `tests/test_kernel2d_review.py`。

## 推翻并已修

| # | 缺陷 | 后果 | 修法 |
|---|---|---|---|
| r1 | `normal_cone` 用 sin(转角) 判反射：sin 分不清 θ 与 π−θ | legacy 3° 容差把 178° 窄缝的缝底放行成"凸顶点"，产出穿过实体的严格 VE 盖 | 改用 `turn_angle = atan2(cross, dot)`，反射 ⟺ 角 < −asin(tol) |
| r3 | `vv_cover` 对原始法向做极角区间：数值共线顶点的 n_next 略偏 CW 时区间回绕成 ≈360° | 31% 的数值共线顶点产生 E 根本没有的"活跃 VV"；legacy 模式下 −1° 微凹顶点也伪造 VV | 先算锥宽 `cone_width = atan2(cross, dot)`，宽 ≤ 0（平直/容差内微反射）直接判无 VV；区间 = (ang(n_prev), ang(n_prev)+宽) |
| r6-i | 暴力 oracle `polygons_overlap` 的"形心严格在对方内 → 相交"分支 | 凹多边形形心可在自身外：C 形缺口里的小方块被判相交；**bb52 最大两块的形心都在自身外，之前的真几何 G0 门不能作为 oracle 正确的证据** | 换成 O'Rourke 耳法的 `interior_point`（保证在内） |
| r6-ii | `signed_area` / `centroid` 绝对坐标累加 | 尺寸 1e-4 的多边形放在 1e4 处面积相对误差 100%，形心跳飞 | 相对 `poly[0]` 累加 |

## 边界情形（已处理）

- r4c：`is_convex` 用未归一化叉积、`convex_entrance_block` 的 +2π 修正吞掉 4e-7 rad 的下降 → 微凹输入静默产出非凸 E。修：`is_convex` 改角度口径；合并只吞 ≤1e-9 rad 的舍入下降，更大则 `ValueError`。
- r5：平直顶点 + 对方反平行边时"局部=全局"标签集出现对称差——两边都对，只是全局侧标签不是极大 facet。随机凸包无平直顶点不受影响；定理检验前应剔除平直顶点（记入 docstring）。
- r7：标签集相等对 `outward_normal` 整体反号是盲的（局部条件与合并对整体反号不变）。修：`g0_convex` 加第三票——E 顶点集必须等于 conv{b−a} 顶点集（不经法向/法锥/合并）；G0 采样本就能抓反号，测试用 monkeypatch 反号验证门会红。
- r8：`first_entrance_for_vertex` 取最大间隙在 B 凹且分离时会选到远边（L 形内角）。记入 docstring：适用于 B 凸或已侵入情形；凹块分离取最小正间隙留待 Phase 3。

## 未能推翻

VE/EV 符号约定（686 盖逐一核对 + 2699 恰接触位形推 ±δ）；`convex_entrance_block` 主构造（3000 组随机凸对面积公式误差 ≤1e-15、顶点集 = conv{b−a}+a0、边角单调）；`membership_convex` 三分类（精确有理数分离轴第三方，17 组刁钻形状 × 3000 样本零不一致）；`point_in_polygon` 对 CW/CCW 零不一致；十字交叉/共边/包含情形全部正确。

## 修复后的门

修复不改变 VE/EV 的 gap 与法向（审查已证其自洽），因此 bb52 G1（53/53）与 G4 钉死数字不受影响；bb52 真几何 G0 现在建立在修正后的 oracle 上。
