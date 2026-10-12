"""Read-only confirmation of residual documentary contradictions at d44dd78."""
from pathlib import Path
import json,sys,hashlib
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
def hit(path,fragment):
    rows=Path(path).read_text(encoding='utf-8-sig').splitlines()
    return next((i+1,s) for i,s in enumerate(rows) if fragment in s)
canon=ROOT/'docs/canon_map.md'
open_=hit(canon,'审查 GAP3');closed=hit(canon,'GAP3（正本对代码）已按各轮报告逐条处置')
assert '仍开放' in open_[1]
readme=hit(ROOT/'README.md','仍以暴力 `polygons_overlap` 检验距离/出口完备性')
from eab.kernel2d import geom,g0
real=geom.polygons_overlap
def forbidden(*a,**kw): raise AssertionError('production polygons_overlap was called')
geom.polygons_overlap=forbidden
try:
    square=[(0,0),(1,0),(1,1),(0,1)]
    result=g0.g0_distance_completeness(square,square,[(2,0)])
finally: geom.polygons_overlap=real
assert result.passed and result.samples==1
prior_advice=hit(canon,'对外须限定为')
theory00=next(Path('D:/E(A, B)').glob('00*'))
older=hit(theory00,'首个三维入口块实现')
agents=hit(ROOT/'AGENTS.md','都是更早或同期的实现')
assert 'DDA 圈内 / 本课题组代码里第一份' in prior_advice[1]
out={
    'GAP3_open_claim':open_,'GAP3_closed_claim':closed,
    'README_old_oracle_claim':readme,
    'g0_with_production_polygons_overlap_forbidden':{'passed':result.passed,'samples':result.samples},
    'first_implementation_advice':prior_advice,
    'prior_implementation_in_read_only_00':{'path':str(theory00),'line':older},
    'AGENTS_explicit_correction':agents}
print(json.dumps(out,ensure_ascii=False,indent=2))
(ROOT/'review/notes/docs_residual_claims_output.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
