"""G6F original inputs replayed with repaired truth assertions (old repro preserved)."""
from pathlib import Path
import sys,io,contextlib,json
ROOT=Path(__file__).resolve().parents[2]
rows=[]
for n,ident in [('solid_convex_cache_alias','G6F-01'),('solid_convex_face_hint','G6F-02'),('solid_hidden_convexity','G6F-03'),('root_margin_projection','G6F-08'),('geom3_nominal_translation_loss','G6F-09')]:
 p=ROOT/'review/repro'/f'{n}.py';s=p.read_text(encoding='utf-8-sig')
 s='\n'.join(line for line in s.splitlines() if not (line.lstrip().startswith('print(') and 'CONFIRMED' in line))
 if ident in ('G6F-01','G6F-02'):
  s=s.replace(')==-1',')==1')
 elif ident=='G6F-03':
  s=s.replace('assert P.is_convex(tol=0) and P.reflex_edges(tol=0)==[]',"assert not P.is_convex(tol=0) and P.reflex_edges(tol=0)==[(3,8)]")
  s=s.replace('assert not P.manifold_issues() and P.is_convex(tol=0) and not P.reflex_edges(tol=0)',"assert not P.manifold_issues() and not P.is_convex(tol=0) and P.reflex_edges(tol=0)==[(3,8)]")
 elif ident=='G6F-08':
  s=s.replace("assert rows[-1]['reported_distance']==0 and rows[-1]['reported_normal'] is None", "assert all(r['reported_distance']==r['expected_distance'] and r['reported_normal']==(-1.,0.,0.) for r in rows)")
 elif ident=='G6F-09':
  s=s[:s.index('try:')]+"float_zero=escape_height_covers(A,B,(0.,0.,0.))\nprint('offset float zero exact_height',float_zero.exact_height)\nassert float_zero.exact_height==expected\n"
 output=io.StringIO()
 with contextlib.redirect_stdout(output):exec(compile(s,str(p),'exec'),{'__file__':str(p),'__name__':'__main__'})
 rows.append(dict(id=ident,status='已修',assertions='原复现全部输入以正确真值重新断言通过',output=output.getvalue()))
 print(ident,'已修\n'+output.getvalue())
(ROOT/'review/notes/geom3_g6f_afterfix.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
