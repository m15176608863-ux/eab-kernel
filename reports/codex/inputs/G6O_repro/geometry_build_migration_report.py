from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[2]
rows=json.loads((ROOT/'review/evidence/geometry_migration_assertions.json').read_text(encoding='utf-8'))
proof=json.loads((ROOT/'review/evidence/geometry_migration_probe.json').read_text(encoding='utf-8'))
text='''# WO-G6O 镜头4补审：五个精选几何旧门/新门对照

对象：`03a41b5`，仅本树review输出与进程内变异，未改tracked文件。旧版本为只读 `git show b6126cf:<file>`；每个旧/新函数体与主审 [157项迁移库存](file:///D:/eab-wt/g6o/review/evidence/test_migration_inventory.json)逐字一致，另核 `tests_diff_b6126cf.txt` 的相关hunk。

**不是全部157项完成证明。** 本补审读核五个最容易被误认为“边界豁免放水”的函数、相关helper及一条新增理想同构门。基线只实际直接调用五个当前代表格（不是其完整参数网格pytest）；三处实际生产函数内部进程内变异，全部被当前目标性质断言捕获。

## 结论与计数边界

未确认“旧断言能发现、新门放过”的真实缺陷。三处内部变异中有两处反而是**旧断言体在当前同一helper/SUT上通过、新断言体报红**：严格法锥状态被降级为边界、真实微小逃逸根被夹成零。此证据支持这两格迁移增强，不能外推全部迁移不弱化。

旧断言体实验明确不等于旧commit整模块/整套执行：保留旧函数体，放在**当前helpers与当前SUT**的相同数据上，以隔离断言语义差别；旧helpers/旧生产行为没有一起重演。未把归档环境setup失败当作旧门红。

## 1. `test_cover_enumeration_is_invariant`

旧 `tests/test_invariance_2d.py` 以两份被测枚举（原tol与放大tol）的交/并夹逼变换后标签，允许bb52“不可分辨”格**直接return**；带外强制全标签同一。新门删除整格return，先逐格对测试自写Fraction邻点支持/线性消元oracle精确核标签含strict，再只对有正判据余量的每个标签保留不变性。

- 原隐式tau作为数学模式噪声不再传入；显式legacy `cone_tol` 对应段窗保留。这是政策分离，不是把不准确的默认答案豁免。
- `ref_gaps.keys() & gaps.keys()` 的构造间隙交集比较本身比旧“所有ref gap逐一”窄；但消失标签已经由完整精确标签集断言逐格检查，边界标签可在实际舍入数据中出现/消失，不能对已不存在特征仍强求旧间隙字段。尚未单独对这个gap交集循环穷尽全部构造错误变异。
- 实际生产 `_ve_side_directions` 的 `return 1 if c1>0 and c2>0 else 0` 改为同一严格条件返回0：仍枚举有效盖但strict错误。一般star_pair、s=1/t=0/非轴旋转下，旧断言体PASS，新门在 **当前:154 `assert set(ref_labels) == independent_cover_oracle(...)`** 红。不是因标签为空/异常而碰巧红。

## 2. `test_convex_g0_is_invariant`

旧强制变换后的facet标签及strict/local/global计数与原位完全相同。对精确共线/平行边，逐顶点float刚体变换可改变这组输入的精确平行关系；旧断言实际要求按噪声恢复理想输入，已不属新默认合同。

新门对原位和变换后分别用自写全頂点投影支持oracle核**全部**标签；随后完整G0三票，明确 `band_skipped == hull_vertex_ambiguous == 0`、boundary探针计数与sample计数，按每格实际Fraction SAT核成员。在余量带外仍守状态/标签不变，并以 `stable>=2` 保证稳定性分支不是空执行。

这不是“边界格被删”；当前每个边界格照自己的精确数据判真值。当前squares代表变换格直接执行PASS。没有本补审专属于该函数的“旧能抓、新不能抓”内部反例；主审另有G0内部毒化证据，不能在这里声称自己重新做了全部G0变异。

## 3. `test_hull_defect_threshold_is_pinned_on_an_edge_away_from_the_start`

旧的深度0.5tol必须接受微凹、2tol拒收；接受分支2000探针允许<=200个成员失配，只要求失配点落facet带内。新默认凸前提要求给定数据精确凸，因此这两非零凹深都在0/tol/100tol三种显式report_tol下拒收；同一seed的2000探针与三精确边界邻点走一般多边形路径，逐点与独立闭式 `sign(1+Fraction(x_y))` 零错。

删除0.5tol“必须吞微凹”不是丢失有效性质，它本身就是旧隐式近似政策。独立参考在|x|<1时至少一端高度1进入SQ底边，故只看1+x_y符号，不调用生产耳切/Minkowski/SAT。

进程内改实际 `membership_convex` 凹分支为 `if s==0: return -1`，新门在 **当前:506 `assert got == want`** 精确邻点 `(0.25,-1.0)` 红，得到 `got=-1,want=0`；没有用数据后追加fake cover，也未把新测试的state集合断言作为碰巧红。

## 4. `test_brute_oracle_is_exact_zero_at_rest_and_scales`

旧两条 `escape_height_brute(...rest/y-slide...) == 0.0` 对原float运动后的几何强行要求理想共面；这些输入含真实细微贯入时，“必须0”反而允许夹零错。新保留原五参数格和两offset，但每格核独立整数四面体并集swept SAT的最早精确根，再检查显示值的**最小上取整**（F(display)>=root，前一float<root）；一般off的解析尺度误差断言保留。

原两条零断言另在 `tests/test_invariance_interlock.py:639-662` 理想同构门保留。**这里的补偿不是原z0.7旋转原样保留**：新理想补偿用signed-permutation 90°旋转和Fraction共用同一界面，避免刚体float舍入破坏共面。此实际构造变化已读核，不能仅凭函数注释声称所有旧非轴旋转精确零性质原封不动；原非轴格由上面的逐格精确oracle承担正确性。

实际 `escape_height_covers` 内部在选定精确根后把 `0<root<1e-8` 夹0；rot=z0.7/t=1e5/s=1时，旧完整断言体PASS（包括一般off误差断言），新门在 **当前:312 `assert solution.exact_height == truth_exact`** 红，y-slide offset为 `(-0.1932653061713073,0.22945265618534655,0.0)`。这是真实数值阈值缺陷被当前门拒绝，正是“边界数据变化不等于跳过检查”的强证据。

## 5. `test_near_parallel_ridge_edges_match_the_exact_rational_distance`

此项旧断言AST删除数为0仍可能语义弱化，因为body_distance与inflated_membership调用改为显式contact_resolution窗口。核对后：旧距<=ctol归零和delta=1.5exact的INSIDE原断言全部保留在明确请求的旧窗口；在同一原A/B/θ/gap/half/rotation格**新增默认API check_exact_margin**。

新增helper不是单纯容差近似：测试独立耳切/Newell/Gram/法锥参考求全cover_squared，核最小距离平方与本测试独立全线段距离一致；默认label必须属精确最小集合；距离有RN-midpoint证书；完整margin标签集、closed状态、δ本身/0/相邻浮点两侧成员均严格相等。helper只有实际调用处import生产API，expected-path不调用生产原语。故把旧assert包窗口本身不够，但这条新默认参考把它补上了。

代表θ=1e-9/gap=1e-6/half=.3/rot3直接执行PASS；本补审没有另做该48格全网格或所有近乎平行错误公式变异，不能仅靠本条重新宣布整个helper全域独立。

## 旧/新断言的逐条行号

以下旧行号均以 `b6126cf` 为准；新行号当前 `03a41b5`。JSON保留完整两函数体与每条Assert，不将AST相同误认为语义相同。
'''
for row in rows:
    text += f"\n### `{row['file']}::{row['function']}`\n\n旧函数:{row['old_span'][0]}–{row['old_span'][1]}；新函数:{row['new_span'][0]}–{row['new_span'][1]}；diff文件匹配行:{row['diff_match_lines_1based']}。\n\n"
    for label,key in [('旧','old_assertions'),('新','new_assertions')]:
        text+=label+'断言：\n'
        for item in sorted(row[key],key=lambda x:x['line']):
            flat=' '.join(item['text'].split())
            text+=f"- :{item['line']} `{flat}`\n"
        text+='\n'
text+='''
## 実测输出、复跑与原字节约束

- 五个当前代表格均PASS。
- 三处真实内部变异均触发AssertionError，失败断言为strict精确标签/精确边界分类/独立最早精确根，不是setup/import错误。
- “旧能抓、新放过”的反例本补审未找到。两处实际相反，旧断言体PASS、新断言体FAIL。
- 所有变异仅compile/替换进程内函数，finally恢复各生产和测试别名；未写src/tests，无需磁盘复原。第一次过强“丢所有strict VE/EV”变异只触发空标签护栏，已弃用，最终证据采用strict->boundary，失败精确落在oracle集合断言。不能把那次弱牙当作最终证明。

[直接复跑脚本](file:///D:/eab-wt/g6o/review/repro/geometry_migration_probe.py)、[原始输出](file:///D:/eab-wt/g6o/review/logs/geometry_migration_probe.txt)、[机读实测](file:///D:/eab-wt/g6o/review/evidence/geometry_migration_probe.json)、[完整断言及旧/新源码](file:///D:/eab-wt/g6o/review/evidence/geometry_migration_assertions.json)。脚本exit0表示正常5格通过且3处指定mutant都被目标AssertionError捕获，不表示mutant生产代码正确。

## 外部理论正本：本分审真实读取范围

|原文件|本分审读到什么|仍未自行核的内容|
|---|---|---|
|`D:/E(A, B)/00 石根华 E(A,B)·理论内核与向外发展分析.md`|仅只读文件名/长度定位；通过本树AGENTS/canon_map读到其二手引述，不算已读00正文|**00正文全文件未由本分审自行细读**；谱系/优先性和外部文献验证由主审其他路，不能据本分工认证|
|`D:/E(A, B)/01 E(A,B) 理论内核·精细版.md`|127行全文；尤其凸前提、命题1/3闭集PD、命题4/5退化/relint、命题6外侧/内侧光滑、命题7首入|原文所引用论文/书未重新在线核题录和全文；不将本文自己的文献断言当本轮独立事实核验|
|`D:/E(A, B)/03 广义接触·裕度即接触与理论内核的去岩石化.md`|122行全文：前次读89–122应用/边界，本补审补读1–88，含§1.1球膨胀、§1.2KKT、§1.3凸域正则化、旧G4记录|应用市场/“零先例”/外部论文原话未核，不属当前数值代码正确性认证|
|`D:/E(A, B)/07 程序设计·统一接触内核方案.md`|仅只读文件名/长度定位；本树canon_map第八节条目是二手地图，不算打开正本07正文|**07正文全文件未由本分审自行细读**；主审其他路核原文件和canon's逐条声称|

## 完整性批评 / 未核项

本补审只五个函数，不覆盖剩余152库存条目；其中40条helper/非test函数与剩余112test-like条目也没有逐条数学核验。只读相关case/helper，不是全面逐文件读所有测试。没有完整执行五函数所有参数网格；完整套的通过与计数由主审负责。没有逐项重放E2–PERF历史全部变异；未复审所有近平行/折面oracle的每条路径，未查所有代数合法重写导致的测试盲区。未新增confirmed发现，不调整此前0c/0m/1minor分审计数。

GEOMETRY_MIGRATION_DONE selected=5 internal_mutations=3 confirmed_new_findings=0
'''
(ROOT/'review/evidence/geometry_migration_review.md').write_text(text,encoding='utf-8')
print('wrote geometry_migration_review.md; 5 selected, 3 internal mutations, new confirmed findings=0')
