"""G6J real-path in-memory mutation: nominal bands cannot select exact root.

Tracked bytes are never edited. A product-box first-lift oracle says h=17/10.
Each replacement is restored in finally and cache keys include callable identity.
"""
from pathlib import Path
from fractions import Fraction as F
import sys,json
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src'))
from eab.kernel3d import interlock as I
from eab.kernel3d.geom3 import Polyhedron
from geom2j_initial_boundary3 import box_vertices,FACES

def main():
    A=Polyhedron(box_vertices((0,0,0)),FACES);B=Polyhedron(box_vertices((0,0,0)),FACES)
    offset=(F(1,10),F(1,5),F(3,10))
    base=I.escape_height_covers(A,B,offset)
    assert base.exact_height==F(17,10), 'Cartesian z interval first-lift oracle'
    old=I._cover_escape_z;calls=[0]
    def no_nominal_root(*args,**kwargs):
        calls[0]+=1;return None
    try:
        I._cover_escape_z=no_nominal_root
        none=I.escape_height_covers(A,B,offset)
        assert calls[0]>0 and none.n_candidates==0
        assert (none.exact_height,none.exact_offset,none.height,none.interval_certificate,none.nonpenetrating_state)==(
            base.exact_height,base.exact_offset,base.height,base.interval_certificate,base.nonpenetrating_state)
    finally:I._cover_escape_z=old
    old_cluster=I._escape_solution;cluster_calls=[0]
    def wrong_report_height(*args,**kwargs):
        cluster_calls[0]+=1
        return I.EscapeSolution(-999,base.cover_label,999,base.tied_labels)
    try:
        I._escape_solution=wrong_report_height
        wrong=I.escape_height_covers(A,B,offset)
        assert cluster_calls[0]>0,'must traverse actual nominal cluster seam'
        assert (wrong.exact_height,wrong.exact_offset,wrong.height,wrong.interval_certificate,wrong.nonpenetrating_state)==(
            base.exact_height,base.exact_offset,base.height,base.interval_certificate,base.nonpenetrating_state)
        assert wrong.height!=-999
    finally:I._escape_solution=old_cluster
    print(json.dumps({'status':'PASS','exact_root':'17/10','nominal_suppression_calls':calls[0],
                     'nominal_candidate_count_after_suppression':none.n_candidates,
                     'wrong_nominal_cluster_height':-999,'cluster_path_calls':cluster_calls[0],
                     'returned_actual_display':wrong.height,'same_exact_root_offset_state_and_interval_certificate':True,
                     'tracked_edit':False},indent=2))

if __name__=='__main__':main()
