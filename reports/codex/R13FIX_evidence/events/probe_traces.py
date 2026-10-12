exec(open('reports/codex/R13FIX_evidence/events/probe_extremes.py',encoding='utf-8-sig').read().split('for exponent')[0])
import traceback
for name,fn in [('enter3_over',lambda:first_entrance3(cube(F(2)**1018,5),cube(F(2)**1018,0),(0,0,0),(0,0,-F(2)**1018),t_max=10)),('escape_under',lambda:escape_height_covers(cube(F(2)**-1070,1),cube(F(2)**-1070,0),(0,0,0)))]:
 print(name)
 try:fn()
 except Exception:traceback.print_exc()
