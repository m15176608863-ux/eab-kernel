# 未应用草案：陡坡竖向并列窗突变牙

**状态：仅 evidence 草案；live source/tests 未修改，旧牙仍失败。** 为保持本次完整失败运行的源稳定性，以及不把 E5b 扩进本单，不应用此迁移。

## 定向复现

原门：`tests/test_interlock_sensitivity.py::test_steep_gate_has_teeth_vertical_tie_window`。

结果原行：`1 failed in 4.90s`。失败断言是 `pytest.raises(AssertionError, match="另一支")` 的 `DID NOT RAISE`，见 `steep_tooth_before.log`。

原因：精确实体判定接入后，略贯入的低支候选不再被 geom_tol 当边界接收。同一个内部竖向窗突变现在可能遗漏应报告的另一支，但选中真支、给出正确单侧斜率，因此原先“可微但给另一支斜率”的特定症状不再必现。原 `_steep_check` 允许“可微且斜率正确”，并只要求全部点中至少一处不可微，所以没有抓住此报告带漏支。

## 不弱于原门的迁移建议

保留原 `_steep_check` 所有断言，包括高度、所在支导数、不可微区间、带外可微、至少一处不可微，以及全部 `4 × 2 × 9 = 72` 个原输入。只增加充分条件：

1. 根据解析剖面，两个相邻分支分别是上块底面 `i=0`、`i=1` 对下块端点 `i=nx,j=0`，即源标签 `FV(face 10,vertex 30)` 和 `FV(face 12,vertex 30)`。
2. 用 `e5a_escape_oracle` 自有 Fraction 循环 Newell、顶点锥、投影与 face-extent 原语，独立重算这两个源特征的有效性、各自名义根及根处在程。
3. 报告带独立计算，不调用生产 `effective_geom_tol`、生产盖或候选：
   - `L = min_P max_v ||v-v0||`；
   - `r = 64·eps·max(C,L)`；
   - `band = max(1e-9·L,r)`。
4. 两支须都在各自 extent 带内，且 `|z_branch - h_analytic|·nz < band/2`。这里仅钉住法向带的严格内部，不对带边缘作额外断言。
5. 满足时必须 `differentiable_by['tan_psi'] == False`，否则明确报“带内漏支”。原后续区间断言继续核对两支解析斜率。

**必须同时检查 extent。** 曾试验仅用解析高度差乘单位法向分量判断：正侧 `e=5e-10` 虽在 normal 带内，另一支自己的投影却已超出 extent 带。该简化草案在未突变代码上误报，已弃用，不作为证据或建议。

## 牙与验证

`steep_tooth_draft.py` 读取 live 测试文本，添加上述门并只在进程内编译执行；不会写回 source/tests。

- 未突变：原四个尺度/平移格，每格 18 个原偏移和全部旧断言，加上新断言，全部通过。
- 突变：仍是原 `monkeypatch` 逻辑，将 **生产 `_escape_solution` 内部**并列规则改成 `1e-9·max(1,|z|)` 竖向窗；没有向产出后加假数据。
- 目标断言确实失败，原异常消息：`(2e-10, (-0.5068809109773142, -0.5068809109773142), '带内漏支')`。
- 草案建议原牙匹配新目标消息“带内漏支”，不靠意外异常或别的断言报红。
- 总草案验证耗时 23.8199 秒；完整新增文本、live 测试 SHA256、72 格记录与真实突变异常保存在 `steep_tooth_draft.json` / `.log`。

这不是已应用的测试改写，不进入“本单已改写台账”；应以未完成建议交给后续 E5b。最终全套仍须原样报告当前 live 旧牙失败，不能用草案通过代替。

本子任务完成后无运行中的 CPU 任务。
