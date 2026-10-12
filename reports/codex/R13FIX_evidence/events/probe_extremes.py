import sys
sys.path[:0]=['src','tests']
from fractions import Fraction as F
from eab.kernel3d.geom3 import Polyhedron
from eab.kernel3d.entrance3 import first_entrance3,shortest_exit3
from eab.kernel3d.interlock import escape_height_covers,escape_candidates,dilatancy_profile
from eab.kernel2d.entrance import first_entrance,shortest_exit
faces=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(3,7,6,2),(0,4,7,3),(1,2,6,5)]
def cube(s,z):return Polyhedron([(s*x,s*y,s*(zz+z)) for x,y,zz in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]],faces)
for exponent in [-1070,0,1018]:
 s=F(2)**exponent; A=cube(s,5);B=cube(s,0);start=(s/4,-s/4,s/2);d=(0,0,-s)
 for name,fn in [('enter3',lambda:first_entrance3(A,B,start,d,t_max=10)),('exit3',lambda:shortest_exit3(cube(s,1),B,(s/4,0,s/4))),('escape',lambda:escape_height_covers(cube(s,1),B,(s/4,0,s/4))),('candidates',lambda:escape_candidates(cube(s,1),B,(s/4,0,s/4))),('profile',lambda:dilatancy_profile(cube(s,1),B,deltas=[-s/4,0,s/4]))]:
  try:r=fn();print(exponent,name,r)
  except Exception as e:print(exponent,name,type(e).__name__,str(e))
 a=[(-s,4*s),(s,4*s),(s,6*s),(-s,6*s)]; b=[(-s,-s),(s,-s),(s,s),(-s,s)]
 for name,fn in [('enter2',lambda:first_entrance(a,b,(s/4,s/2),(0,-s),t_max=10)),('exit2',lambda:shortest_exit([(x,y-4*s) for x,y in a],b,(s/4,s/4)))]:
  try:print(exponent,name,fn())
  except Exception as e:print(exponent,name,type(e).__name__,str(e))
