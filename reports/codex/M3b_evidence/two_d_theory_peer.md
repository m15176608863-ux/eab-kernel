# M3b 二维 T2a/T2b 窄审：证明与邻面探针合同

日期：2026-10-15。复核者：三维 boundary 子任务执行者；**非 G6**。
只读范围：`docs/m3_global_entrance_design.md` 的 M3b 新节、`kernel2d/global_entrance.py`
的凸合并/完整 raw 接触安排/compact 竖直剖分/side_probes，及对应新旧门与扫描入口。
本轮没有修改生产源码、测试、工具、policy 或设计文档。

## 1. 结论分开陈述

1. **T2a 普遍弱覆盖证明未发现缺口。** 在明列的全维、紧、正则闭、有限简单 CCW 环、无零边/回折域内，
   平直顶点、非严格有效、共线及 VV 闭包处理成立，不需要一般位置。
2. **T2b 等价完整语义剖分本体未发现缺口。** 面积证书只用于内部不交的原体片；raw 接触安排先完全切分，
   再分别保留 0 边及所有 0 顶点；孤立紧配点进入事件墙并显式切分，不能从保留边反推顶点。
3. **发现真实实现/证据缺口：compact 的双侧点未必位于相邻开面。** 只用保留 contact edges 的
   支撑线限步，既遗漏孤立 0 点，又可能沿接触缝支撑线走到缝端点。
   这不是“删去 state1 人工内缝仍同标签”的无害差别，而会把邻面应有的贯入 1 采成接触 0。
   已向主执行者报告，二维子任务随后最小修复；本代理的修后旁路结果见 §6，
   bb52 全量及450格/最终四片仍由各自完整冻结执行记录确认。

因此，修复前 bb52 的 7113 次记录证明“实际所取查询点与 oracle 零失配”，
**不能单独证明所有相邻开面双侧采样合同正确**。T2a/T2b 数学剖分的正确性与这条程序探针缺口不可混为一谈。
也撤回本代理较早 `boundary_peer_review.md` 中未附此限制的邻面探针背书。

## 2. T2a：隐含前提与退化分支逐条核对

- T1 给出有限满维凸并，保证 E 的边界是非零闭线段并、没有只能靠孤立 E 点承担的边界分量。
  有限 VV 差点集合删除后，在这些边界线段上仍稠密；这一步依赖满维/正则闭，正文已写出。
- 非贯入闭交若有一点在一体内部，另一体的正则闭性给出逼近该点的内部点，立即产生体内交。
  所以接触点确实位于双方边界。非平行棱相对内部横截的两局部内半平面相交成开扇区，亦矛盾。
- 排除 VV 后，共线正长度闭区间交至少有端点严格位于另一边内部；零长度共线交只能是 VV。
  因而能回到 VE/EV 的局部半平面论证，而不是假设一般位置后漏掉共线。
- 顶点局部实体若有点严格进入对方边的内半平面，正则闭性再次迫使内点进入，违反不贯入。
  所以 `-n(e)` 属于正确的闭支撑锥。符号与 `ve_side_exact/ev_side_exact` 一致。
- 平直顶点的局部实体是半平面，其非零法锥仅为正确朝向的单射线；代码的反向点积排除相反射线。
  平直环点在耳切时可能移除，但保存在原始 `self.A/self.B`，局部盖仍枚举这些原始点。
- `>=0` 是闭有效；`>0` 会删除方块平行接触等必要盖。有限闭盖并取闭包补回 VV/端点，
  不需要微扰、严格角度或浮点阈值。反射顶点无非零支撑向量，排除它与局部半平面论证相容。

这是一份针对所列输入域的证明，未扩展到自交环、零面积对象或本 API 未表达的多环洞边界。

## 3. T2b：完整语义粗化不是原 overlay 的字面缩减

### 3.1 原体凸合并

原始耳片内点互不交，且 CCW；合并后由 hull 保持 CCW。若 `H=conv(P∪Q)` 中有不在闭并 P∪Q 的点，
它在 H 的相对邻域有正面积（即便该点在 H 边界）。因此精确面积相等排除遗漏，得 H=P∪Q。
归纳保持其他原片内部不交。至少两个共有顶点仅为候选剪枝，可能少合并，不会多合并。
**此证书不能直接用于互相重叠的配置胞**；文档和实现未如此使用。

### 3.2 全 raw 接触骨架与标签恒定

O 是开集且 closure(O)=E，故 `boundary(O)=E\O`。每个 raw VE/EV 段中的配置都有真实共同点，
所以 Γ 全部包含于 E；非贯入接触的 VE/EV/共线/VV 分类又给 E\O⊆Γ。
标签变化不能凭空出现在 raw 原子段内部：沿该段运动时，非平行边的交/不交拓扑要变化，必须发生
新的有限顶点—边关联；共线区间的重叠端点顺序要变化，必须发生端点重合。
前者是另一 raw 段的交，后者是重叠段端点/VV，均已被完整安排切开。
所以保留 0 段、删去 1 开段合法；不能在安排前只取某些局部有效盖代替全部 raw 段。

代码确实从 **arranged** 的全部端点取 `contact_points`，而非只从 `contacts` 取端点。
孤立 0 点的 x 坐标加入 xs，使该点落在完整上下贯通的事件墙上；末尾显式用全部 contact_points
再次切墙，故它成为 0 维胞。删除所有邻接 1 开段不会删除这个点。

### 3.3 竖直剖分覆盖

每两个连续 x 事件之间，接触线段的次序不能改变，否则已有被漏掉的交点事件；各层构成凸梯形或三角形。
加 ymin/ymax 后每条开条带完整覆盖矩形内全部高度，边界墙再完全切分；孤立点只能在事件墙，不会藏进开面。
E 的坐标极值位于 ∂E⊆E\O，因此从保留 contact_points 得到的矩形确实包住 E；矩形外统一 −1 合法。
各开面不交 ∂O，实体标签恒定。人工墙在全部保留事件点处分段后也不跨标签变化。

“等价粗化”应按 **E/O 标签语义相同**理解：人工墙可以与旧安排不同，甚至切开某些旧人工胞；
不是声称新每胞必定等于若干旧胞的字面并，更不是原三角胞 overlay 的所有内缝均被扫描。
当前冻结摘要明确写 `complete_contact_skeleton_vertical_coarsening_not_triangle_pair_overlay`，口径正确。

## 4. 已执行的独立有理反例：共线紧配缝端点

重现时 `src/eab/kernel2d/global_entrance.py` SHA256 为
`e5a80af8833c239e05e4e55fc1d8f4fe8e6401110c1ff2b695604bcfd3b9d0e5`，执行前后一致。
使用原始有理输入（与既有 PIN/U 相同），二者同时作 R(x,y)=(-y,x)：

```python
PIN = [(0, 1/2), (1, 1/2), (1, 3/2), (0, 3/2)]
U = [(-1,-1), (2,-1), (2,2), (1,2), (1,0), (0,0), (0,2), (-1,2)]
# 实际执行中的 1/2、3/2 均为 Fraction，不经过 binary64。
g = GlobalEntrance2(R(PIN), R(U), merge_convex=True, compact_subdivision=True)
sub = g.subdivision
edge = ((Fraction(5,2), -1), (Fraction(5,2), 1))
g.side_probes(*edge)
# ((Fraction(1,2), 0), (Fraction(9,2), 0))
```

这条边确为最终 subdivision 的一条边，中点 m=(5/2,0)，内侧法向 d=(-2,0)。
内部接触缝为 y=0、x∈[-3/2,1/2]。它与探针射线共线，故支撑线的 h=slope=0，不产生非零根。
剩下 x=-3/2 的外边界给事件参数2，半步1恰好把内侧点送到缝端点 (1/2,0)。

独立裁判只调用 `g0_oracle.translate/overlap/boundary_has_exterior`（Fraction 整数绕数/相交），
不调用被测 hull、耳切、裁剪、安排或法向原语生成期望。实际输出：

| 查询点 | 独立实体 oracle | 独立接触拓扑 | 说明 |
|---|---:|---|---|
| (1/2,0)，实际内侧返回 | 0 | 没有外部方向，即 int(E) | 命中紧配缝端点，不是相邻开面 |
| (9/2,0)，实际外侧返回 | −1 | 外部 | 外侧正常 |
| (9/4,0) | 1 | 内部 | 靠近 m 的真实内侧开面 |
| (3/4,0) | 1 | 内部 | 缝端点之前仍贯入 |
| (1/4,0) | 0 | int(E) | 越过端点沿缝继续接触 |

二维子任务另独立发现：PLUG/POCKET 保留孤立原点，在 POCKET 顶边加入平直点 (10/3,6) 后，
竖墙 `((-5/3,-5),(-5/3,5))` 的内侧探针恰为原点 0。这个独立报告用于说明第二种缺陷来源；
本文件上表是本代理实际执行且由独立 oracle 复核的第一种反例。

## 5. 证据解读与修复后旁路检查计划

旧门在 side_probes 返回点上逐点调用 oracle，能发现错误标签，却不检查返回点是否在正确邻开面，
所以本例仍可零失配。Euler 校验与全部胞样本也不检验该邻面合同。
修复应由最终剖分的全部边支撑线限步（含事件墙），或给出等价的完整事件论证；
只删除 state1 人工内缝本身无问题，但不能顺带丢掉真实低维接触事件或跨越最终相邻面。

发现缺陷时制定的修后旁路方案是，用测试外自持 Fraction 行列式：
按每条最终边中点独立确定两侧相邻 face，要求两个返回点严格位于对应开 face；矩形外侧要求严格在矩形外。
再对返回点与相邻 face 的内部样本分别调用独立原体 oracle 对账。
计划覆盖原点孤立例、平直新增点例、90°紧配缝例及一般有理旋转/尺度/大平移。
现已执行的旁路结果见 §6；修复后扫描与450格等相关冻结证据也需完整重跑，不能用此旁路代替。

局部弱覆盖实验本身也须保持准确口径：有理区间并检查使用独立 oracle 行列式，但待覆盖的 `g.boundary`
仍来自被测全局构造，不是独立重建整个真边界。独立原体边界中点/射线出口门提供另一路有限检查；
普遍结论来自 T2a/T2，不来自把同一实现的两个路径称作完全独立的全域 oracle。

## 6. 修后独立相邻开面旁路：36 格 / 4542 双侧点通过

最小修复在 compact 的最终 subdivision 已构造后，采用其**全部最终边支撑线**限步，包含竖直事件墙；
`_contact_edges` 仍保持原接触骨架，默认未选择 compact 的路径不改变。

此处不再用生产步长公式生成“期望”重复对拍，而是：

1. 用测试外自持 Fraction 行列式，找出每条最终原子边中点两侧的实际相邻凸开面。
2. 要求返回点严格位于对应开面；矩形边界外侧则严格在包围矩形外。跨越人工墙即使实体标签未变也失败。
3. 用独立原体 `g0_oracle` 分别计算返回点与邻面内部样本标签，要求相等；同时核生产成员查询。

三家庭为孤立接触、顶边插入平直点的孤立接触、PIN/U 紧配缝。
各取四个旋转 `(cos,sin)=(1,0),(0,1),(3/5,4/5),(5/13,12/13)`，与三档
`(exponent,shift)=(-400,0),(0,1000),(400,100000)` 组合，共36格。
A平移 `(t,-3t)`、B平移 `(-2t,5t)`，不仅把两者做相消的公共平移。

| 家庭 | 四个旋转各自的最终边数（每档相同） | 三档全部双侧点 |
|---|---|---:|
| isolated | 20 / 24 / 98 / 98 | 1440 |
| flat_isolated | 26 / 26 / 112 / 112 | 1656 |
| seam | 19 / 22 / 91 / 109 | 1446 |
| 合计 | 36 格；每边两点全执行 | **4542** |

整次执行结果：**0失配、0skip；5.393858300012653 s**。
独立 oracle 的全部 face 样本亦额外核对；4542只计双侧点，不把这些辅助检查混入计数。
执行前后两文件哈希不变：

```text
src/eab/kernel2d/global_entrance.py
341ac55fff28a6e4af428dfa4842e802bbb1231cf0d773233229600bcd34ca40
src/eab/kernel2d/g0_oracle.py
7810fd3593589e8e2d4c101dc17e637bb3161647b73b03f10fee5401bf806f03
```

这份结果关闭本代理发现的邻面采样反例在上述有限变换族的复现；不证明不存在其他实现错误，亦不是 G6。
以下为实际通过 `PYTHONDONTWRITEBYTECODE=1 python -X utf8 -` 执行的完整旁路程序，
TEMP/TMP 定向 `reports/codex/M3b_evidence/tmp/review`；程序只读源/输入，不覆写现有冻结扫描。

```python
import sys, hashlib, json, time
from pathlib import Path
from fractions import Fraction as F
sys.path.insert(0, 'src')
from eab.kernel2d.global_entrance import GlobalEntrance2
from eab.kernel2d import g0_oracle as O

sources=['src/eab/kernel2d/global_entrance.py','src/eab/kernel2d/g0_oracle.py']
hashes=lambda:{p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in sources}
before=hashes()
plug=((1,1),(5,1),(5,5),(1,5))
pocket=((0,0),(6,0),(6,2),(5,2),(5,1),(1,1),(1,5),(5,5),(5,4),(6,4),(6,6),(0,6))
flat=pocket[:-1]+((F(10,3),6),)+pocket[-1:]
pin=((0,F(1,2)),(1,F(1,2)),(1,F(3,2)),(0,F(3,2)))
u=((-1,-1),(2,-1),(2,2),(1,2),(1,0),(0,0),(0,2),(-1,2))
families=(('isolated',plug,pocket),('flat_isolated',plug,flat),('seam',pin,u))
rotations=((F(1),F(0)),(F(0),F(1)),(F(3,5),F(4,5)),(F(5,13),F(12,13)))
def determinant(a,b,p):
    return (b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0])
def contains(poly, p, strict):
    values=[determinant(a,b,p) for a,b in zip(poly,poly[1:]+poly[:1])]
    return (all(v>0 for v in values) or all(v<0 for v in values)) if strict else (all(v>=0 for v in values) or all(v<=0 for v in values))
def sign(x):
    return (x>0)-(x<0)
rows=[]
start=time.perf_counter()
for family,A,B in families:
    for rotation,(c,s) in enumerate(rotations):
        for exponent,shift in ((-400,0),(0,10**3),(400,10**5)):
            scale=F(2)**exponent
            def transform(P,tx,ty):
                return tuple((scale*(c*x-s*y)+tx,scale*(s*x+c*y)+ty) for x,y in P)
            av=transform(A,F(shift),F(-3*shift))
            bv=transform(B,F(-2*shift),F(5*shift))
            model=GlobalEntrance2(av,bv,merge_convex=True,compact_subdivision=True)
            sub=model.subdivision
            lo=tuple(min(cell.sample[k] for cell in sub.vertices) for k in range(2))
            hi=tuple(max(cell.sample[k] for cell in sub.vertices) for k in range(2))
            for face in sub.faces:
                assert contains(face.vertices,face.sample,True),'face sample must independently lie in open convex face'
                assert face.state==O.overlap(O.translate(av,face.sample),bv),'independent face oracle label'
            checked=0
            for edge in sub.edges:
                a,b=edge.vertices
                middle=tuple((a[k]+b[k])/2 for k in range(2))
                adjacent={}
                for face in sub.faces:
                    if contains(face.vertices,middle,False):
                        assert not contains(face.vertices,middle,True),'complete subdivision edge cannot lie inside a face'
                        side=sign(determinant(a,b,face.sample))
                        assert side and side not in adjacent,'unique independent adjacent open face'
                        adjacent[side]=face
                assert 1<=len(adjacent)<=2,'every rectangle edge has one or two adjacent open faces'
                for p in model.side_probes(a,b):
                    side=sign(determinant(a,b,p))
                    assert side,'probe is strictly on a geometric side'
                    if side in adjacent:
                        face=adjacent[side]
                        assert contains(face.vertices,p,True),('probe must lie in actual adjacent open face',family,rotation,exponent,a,b,p,face.vertices)
                        expected=O.overlap(O.translate(av,face.sample),bv)
                    else:
                        assert any(p[k]<lo[k] or p[k]>hi[k] for k in range(2)),'bounding-edge outside probe lies strictly outside rectangle'
                        expected=-1
                    actual=O.overlap(O.translate(av,p),bv)
                    assert actual==expected==model.membership(p),'adjacent open-face independent oracle label'
                    checked+=1
            assert checked==2*len(sub.edges)
            rows.append(dict(family=family,rotation=rotation,exponent=exponent,shift=shift,edges=len(sub.edges),adjacent_face_probes=checked))
            print(json.dumps(rows[-1]),flush=True)
assert before==hashes(),'source changed during independent peer audit'
print(json.dumps(dict(status='COMPLETE',cases=len(rows),adjacent_face_probes=sum(r['adjacent_face_probes'] for r in rows),mismatches=0,skipped=0,source_sha256=before,source_unchanged=True,elapsed_seconds=time.perf_counter()-start),sort_keys=True),flush=True)

```
