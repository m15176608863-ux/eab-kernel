"""G6N local penetration-window audit, independent interval-union certificates.
Six translations certify rho, not general closed-set PD. Independent star core
uses exact axis-plane checks and homothetic interval transformation. All shrink
rays have length <= alpha*max_vertex_L1_radius <= w over the whole surface.
"""
from pathlib import Path
from fractions import Fraction as F
import sys,random,json,time
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT/'review/repro'))
from geometry_union import build,overlap,shift_body
from eab.margin import body_distance

def core_model(cells,boxes,poly,window):
    centre=tuple(sum(v[k] for v in poly.verts)/len(poly.verts) for k in range(3))
    # Each source quad is a known unit-grid cell boundary. Its outward exact
    # Cartesian halfspace must strictly contain the proposed star centre.
    occupied=set(cells)
    for cell in cells:
      for axis in range(3):
        for sign in [-1,1]:
          neighbour=tuple(x+sign if k==axis else x for k,x in enumerate(cell))
          if neighbour in occupied:continue
          plane=boxes[cells.index(cell)][axis][0 if sign<0 else 1]
          if sign*(centre[axis]-plane)>=0:return None,None
    radius=max(sum(abs(v[k]-centre[k]) for k in range(3)) for v in poly.verts)
    alpha=min(window/radius,F(1,2))
    assert 0<alpha<=F(1,2) and alpha*radius<=window
    shrunk=[tuple((centre[k]+(1-alpha)*(lo-centre[k]),centre[k]+(1-alpha)*(hi-centre[k])) for k,(lo,hi) in enumerate(b)) for b in boxes]
    return shrunk,(alpha,alpha*radius)

def run():
    rng=random.Random(1404);fail=[];stats={'cases':0,'axis_accepted':0,'shell_accepted':0,'rejected':0,'shell_radius_checks':0};start=time.time()
    shapes={
       'cube':[(0,0,0)],'L':[(0,0,0),(1,0,0),(0,1,0)],
       'U':[(0,0,0),(1,0,0),(2,0,0),(0,1,0),(2,1,0),(0,2,0),(2,2,0)]}
    for i in range(130):
      na,nb=rng.choice(list(shapes)),rng.choice(list(shapes));cells_a,cells_b=sorted(shapes[na]),sorted(shapes[nb]);scale=rng.choice([F(1,10**9),F(1),F(10**8)]);T=rng.choice([(0,0,0),(F(10**8),F(-10**8),F(10**8))])
      a,aa=build(cells_a,scale,T);b,bb=build(cells_b,scale,T)
      offset=tuple(F(rng.randint(-7,7),4)*scale for _ in range(3));w=rng.choice([F(1,16),F(1,4),F(1),F(2)])*scale
      aa=[tuple((lo+t,hi+t) for (lo,hi),t in zip(cell,offset)) for cell in aa];at=shift_body(a,offset);physical=overlap(aa,bb)
      if physical!=1:continue
      stats['cases']+=1
      axis=any(overlap(aa,bb,tuple(w*sign if k==axis else F(0) for k in range(3)))<=0 for axis in range(3) for sign in [-1,1])
      ca,pa=core_model(cells_a,aa,at,w);cb,pb=core_model(cells_b,bb,b,w)
      stats['shell_radius_checks']+=int(pa is not None)+int(pb is not None)
      shell=(ca is not None and overlap(ca,bb)<=0) or (cb is not None and overlap(aa,cb)<=0)
      accepted=axis or shell
      out=body_distance(at,b,contact_window=w,tol=0)
      actual=out[1]!=('PENETRATING',)
      if actual!=accepted:fail.append({'case':i,'shapes':[na,nb],'offset':str(offset),'w':str(w),'actual':str(out),'expected':accepted})
      stats['axis_accepted' if axis else 'shell_accepted' if shell else 'rejected']+=1
    from eab.kernel3d.geom3 import Polyhedron
    face_ring=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
    def rectangular_solid(boxes):
      vertices=[];faces=[]
      for ranges in boxes:
        (x0,x1),(y0,y1),(z0,z1)=ranges;n=len(vertices)
        vertices += [(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)]
        faces += [tuple(i+n for i in f) for f in face_ring]
      return Polyhedron(vertices,faces)
    for scale in [F(1,10**9),F(1),F(10**8)]:
      for translation in [F(0),F(10**8)]:
        w=scale/64;inside=3*w/4
        aa=[((-scale,scale),(-scale/16,scale/16),(-scale/16,scale/16))]
        bb=[((-2*scale,-scale+inside),(-2*scale,2*scale),(-2*scale,2*scale)),((scale-inside,2*scale),(-2*scale,2*scale),(-2*scale,2*scale))]
        aa=[tuple((lo+translation,hi+translation) for lo,hi in box) for box in aa]
        bb=[tuple((lo+translation,hi+translation) for lo,hi in box) for box in bb]
        alpha=w/(9*scale/8)
        ca=[tuple((translation+(1-alpha)*(lo-translation),translation+(1-alpha)*(hi-translation)) for lo,hi in box) for box in aa]
        assert overlap(aa,bb)==1 and overlap(ca,bb)<=0
        assert not any(overlap(aa,bb,tuple(w*sign if k==axis else F(0) for k in range(3)))<=0 for axis in range(3) for sign in [-1,1])
        assert alpha*(9*scale/8)<=w
        out=body_distance(rectangular_solid(aa),rectangular_solid(bb),contact_window=w,tol=0)
        stats['cases']+=1;stats['shell_accepted']+=1;stats['shell_radius_checks']+=1
        if out[0]!=0 or out[1]==('PENETRATING',):fail.append({'case':'analytic_shell','scale':str(scale),'translation':str(translation),'actual':str(out),'expected':'accepted thin shell'})
    result={'stats':stats,'failures':fail,'seconds':round(time.time()-start,3)}
    (ROOT/'review/evidence/geometry_window_results.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))
if __name__=='__main__':run()
