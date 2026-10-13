# Original raw finding index 40; current HEAD replay, no repair.
import sys;sys.path.insert(0,'src')
from eab.kernel2d.covers import convex_entrance_block,membership_convex
from eab.kernel2d.g0 import g0_convex
A=[(0.,0.),(.1,0.),(.1,.1),(0.,.1)]
def B(d,h):return [(0.,0.),(1.,0.),(1.,1.),(0.,1.),(0.,.5+h),(d,.5)]
P=B(.5e-6,1e-4)
try:convex_entrance_block(A,P,(0.,0.),1e-6);print('ERROR: accepted reflex polygon')
except ValueError as e:print('exact convex rejection:',e)
for d in [1e-5,1e-4]:print('fallback depth',d,'membership',membership_convex(A,P,(-.1+d,.2)))

