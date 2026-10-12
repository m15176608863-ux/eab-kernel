exec(open('reports/codex/R13FIX_evidence/events/probe_extremes.py',encoding='utf-8-sig').read().split('for exponent')[0])
import traceback
def slab(low,high):return Polyhedron([(-1,-1,low),(1,-1,low),(1,1,low),(-1,1,low),(-1,-1,high),(1,-1,high),(1,1,high),(-1,1,high)],faces)
for exponent in [-1070,0,1018]:
 s=F(2)**exponent;a=slab(-3*s/4,max(1,s));b=slab(-max(1,s),0)
 for name,fn in [('escape',lambda:escape_height_covers(a,b,(F(1,4),0,0))),('candidates',lambda:escape_candidates(a,b,(F(1,4),0,0))),('profile',lambda:dilatancy_profile(a,b,deltas=[-F(1,4),0,F(1,4)]))]:
  try:r=fn();print(exponent,name, getattr(r,'height',r))
  except Exception:traceback.print_exc()
