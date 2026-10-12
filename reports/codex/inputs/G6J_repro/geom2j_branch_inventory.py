"""Reproducible branch inventory for the G6J geometry lane (no source edits)."""
from pathlib import Path
import ast,json
ROOT=Path(__file__).resolve().parents[2]
FILES=['src/eab/kernel2d/geom.py','src/eab/kernel2d/exact.py','src/eab/kernel2d/covers.py',
       'src/eab/kernel2d/entrance.py','src/eab/kernel2d/g0.py','src/eab/kernel2d/g0_oracle.py',
       'src/eab/kernel3d/interlock.py','src/eab/kernel3d/frozen.py','src/eab/kernel3d/exact_sweep.py',
       'src/eab/kernel3d/entrance3.py']

def category(path,fn):
    if path.endswith('geom.py'):
        if fn=='orient2d':return '浮点误差过滤；两个浮点决断后存在完整 Fraction 兜底；12000 格独立符号压力零分歧'
        if fn in ('_point_in_polygon','segments_properly_cross','_triangles_overlap','_interiors_overlap','polygons_overlap','reflex_vertices','is_convex'):return '精确 Fraction 谓词或调用方显式 tol 域窗口；无隐式地板'
        if fn in ('turn_floor','angle_floor','round_floor'):return '可分辨性/舍入估计输出；不决定默认几何答案'
        if fn in ('_display_fraction','outward_normal','turn_angle','point_side','vertex_turn','unit','norm','_tri_axes'):return '最终构造可表达性或输入域错误检查；不作隐式几何噪声带'
    if path.endswith('covers.py'):
        if fn=='in_cone':return '缺陷：严格分支漏同侧/非反射约束；见 geom2j_reflex_cone_inverse.py'
        if fn in ('_cross_ge_window','_cone_accepts','_cone_nonreflex','normal_cone','_ve_side_directions','_angle_window2','vv_cover','_in_segment_exact','_in_gap_window','_feature_in_gap_window','enumerate_covers','membership_convex','first_entrance_for_vertex','_in_exact_boundary_band'):return 'Fraction 精确符号/平方判定；正 tol/cone_tol/seg_tol/window 是调用方显式域政策'
    if path.endswith('entrance.py'):
        if fn in ('_floor','shortest_exit','_first_entrance_convex','_first_entrance_concave'):return '权威根/选路/有限域是 Fraction；r 与 tol 仅 near_labels 报告'
        if fn=='first_entrance_brute':return '明示扫描/二分佐证而非独立 oracle；float 相邻停止仅控制显示分辨率'
    if path.endswith('g0.py'):
        if fn=='_construction_error_exceeds':return '独立精确平方限界审核显示见证误差；相对 atol/roundoff 不筛成员真值'
        if fn in ('g0_distance_completeness','g0_exit_completeness'):return '只有实际相交/接触/分离的数学域排除；所有严格微量样本保留'
        if fn=='_minimum_witness_distance':return '所有非有限见证会使门失败；None 跳过仅最短存在性门，未确认为缺陷'
    if path.endswith('interlock.py'):
        if fn in ('_normal_noise','_cover_escape_z','_candidates_uncached','_escape_solution','escape_candidates'):return 'nominal 标签/导数报告带；近竖直抑制不参与 exact_height；最终不可表示仍可响亮失败'
        if fn in ('_exact_escape','_exact_escape_cached','_prior_intervals','escape_height_covers','_nonpenetrating_at'):return '权威 Fraction 全表面事件根/逐区间精确成员；display 上取相邻数仅显示'
        if fn=='dilatancy_profile':return '明确中心有限差分的可视剖面估计；非解析导数或精确事件 oracle'
    if path.endswith('entrance3.py') and fn=='first_entrance3':return 'Fraction 候选/成员，但初态边界未独立返回且 nd>=0 排掉初接触；已确认静默 none 缺陷'
    if path.endswith('entrance3.py') and fn=='first_entrance_brute':return '明确有限扫描/浮点二分佐证，含 gtol 显式报告带和 1e-10*L 停止宽度；不是独立主 oracle，也不被 exact first_entrance3 调用'
    if path.endswith('frozen.py'):return 'Fraction 多项式/jet 与最终有证书构造；type/width/精确零是输入域或不可微点检查'
    if path.endswith('exact_sweep.py'):return 'Fraction 有限域/全部事件/星核充分证书；无 float 否决；窗口只按显式非负政策'
    if path.endswith('geom.py'):return '人工源码核：其余面积/转向/耳切/内部点条件读取 Fraction 或精确 orient2d；循环/顶点数条件为结构/输入域检查'
    if path.endswith('exact.py'):return '人工源码核：Fraction 叉积/点积/精确单元与拓扑扇区条件；len/循环终止为结构检查；没有浮点阈值'
    if path.endswith('covers.py'):return '人工源码核：其余 bisector/局部支撑/标签/精确 gap 选择条件读取 Fraction 符号或精确 predicates；没有默认噪声带'
    if path.endswith('entrance.py'):return '人工源码核：其余输入非零/类型与有限域条件，以及 Fraction 原始特征事件、候选和漏候选自检；不是浮点过滤'
    if path.endswith('g0.py'):return '人工源码核：其余独立 Fraction 投影支撑/Jarvis 真值、集合标签/结构条件；随机探针是采样而非 oracle 几何原语'
    if path.endswith('g0_oracle.py'):return '人工源码核：独立整数绕数/相交和 Fraction 事件/本地补集扇区；所有零/符号/顺序条件精确，不带噪声豁免'
    if path.endswith('interlock.py'):return '人工源码核：其余输入/标签种类/nominal 报告结构条件；escape_height_brute 调精确解仅核 hi 上界，冻结出口仅核盖种类'
    if path.endswith('entrance3.py'):return '人工源码核：其余标签拓扑/来源映射、精确同向/共面和局部平方深度条件；tol 显式传到盖域，不加入隐式舍入地板'
    return 'UNREVIEWED: inventory module outside the ten-module reviewed lane'

def main():
    rows=[]
    for filename in FILES:
        source=(ROOT/filename).read_text('utf-8-sig');tree=ast.parse(source)
        class Collector(ast.NodeVisitor):
            def __init__(self):self.fn='<module>'
            def visit_FunctionDef(self,node):
                old=self.fn;self.fn=node.name;self.generic_visit(node);self.fn=old
            def add(self,node,test,kind):
                rows.append(dict(file=filename,line=node.lineno,function=self.fn,kind=kind,
                                 condition=ast.get_source_segment(source,test),classification=category(filename,self.fn)))
            def visit_If(self,node):self.add(node,node.test,'if');self.generic_visit(node)
            def visit_While(self,node):self.add(node,node.test,'while');self.generic_visit(node)
            def visit_IfExp(self,node):self.add(node,node.test,'if_expression');self.generic_visit(node)
            def visit_comprehension(self,node):
                for test in node.ifs:self.add(test,test,'comprehension_filter')
                self.generic_visit(node)
        Collector().visit(tree)
    target=ROOT/'review/notes/geometry_branch_inventory.json'
    target.write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'files':len(FILES),'branch_records':len(rows),'output':str(target)},ensure_ascii=False))

if __name__=='__main__':main()
