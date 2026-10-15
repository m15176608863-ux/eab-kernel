
from pathlib import Path
from collections import Counter, defaultdict
from fractions import Fraction as Q
from itertools import combinations
from math import factorial
import gzip, hashlib, json, time, traceback

ROOT=Path(r"D:/eab-wt/cx-e2")
EV=ROOT/"reports/codex/M5b_evidence"
RUN=EV/"tmp/robust_full_r2"
PHASES=("raw_df05","post_df06")
CLASSES=("ROBUST_NO_CONTACT","ROBUST_SINGLE_FIRST_COVER","MODEL_SENSITIVE_OR_UNPROVED")
ROW_CATEGORIES=("ROBUST_NO_CONTACT_REFERENCE","FIRST_COVER_MATCH","OTHER_REFERENCE","UNPROVED_REFERENCE")

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def nonzero(counter):
    return {k:v for k,v in counter.items() if v}

def same_counts(a,b,label):
    assert nonzero(a)==nonzero(b), (label, nonzero(a),nonzero(b))

def source_hashes():
    paths=list((ROOT/"src/eab").rglob("*.py"))
    paths += [ROOT/"tools/m5b_robust_replay.py",ROOT/"tools/m5b_endpoint_replay.py"]
    return {p.relative_to(ROOT).as_posix():sha(p) for p in sorted(paths)}

def input_hashes():
    return {p.relative_to(ROOT).as_posix():sha(p)
            for directory in (EV/"endpoint_inputs",EV/"legacy_inputs")
            for p in sorted(directory.iterdir()) if p.is_file()}

def eval_poly(poly,x):
    value=Q(0)
    for c in reversed(poly):
        value=value*x+Q(c)
    return value

def normalized_ids(row):
    ring=[tuple(map(Q,p)) for p in row["start"]]
    area=sum(p[0]*q[1]-p[1]*q[0] for p,q in zip(ring,ring[1:]+ring[:1]))
    assert area != 0
    ids=list(row["vertex_ids"])
    return ids if area>0 else list(reversed(ids))

def global_label(label,a,b):
    tag,i,j=label
    ia,ib=normalized_ids(a),normalized_ids(b)
    if tag=="VE":
        assert 0<=i<len(ia) and 0<=j<len(ib)
        return ("VE",ia[i],*sorted((ib[j],ib[(j+1)%len(ib)])))
    assert tag=="EV" and 0<=i<len(ia) and 0<=j<len(ib)
    return ("VE",ib[j],*sorted((ia[i],ia[(i+1)%len(ia)])))

def independent_block_budget(row):
    """Replay wiring oracle: factorial sums, triangle fan, staged complex product.

    Imports no production helpers. The transcendental enclosure is the written
    bits=80 contract, recomputed with direct powers/factorials, not recurrence.
    This audits r2 budget arithmetic; it is not another first-root algorithm.
    """
    points=[tuple(map(Q,p)) for p in row["start"]]
    endpoints=[tuple(map(Q,p)) for p in row["end"]]
    dx,dy,theta,ex,ey,gxy=map(Q,row["z"])
    assert abs(theta)<=1
    x=abs(theta)
    intervals=[]
    for parity in (1,0):
        n=0
        while x**(2*n+parity+2)/factorial(2*n+parity+2)>Q(1,2**84):
            n+=1
        total=sum(((-1)**j*x**(2*j+parity)/factorial(2*j+parity) for j in range(n+1)),Q(0))
        other=total+(-1)**(n+1)*x**(2*n+parity+2)/factorial(2*n+parity+2)
        lower,upper=sorted((total,other))
        if parity and theta<0:
            lower,upper=-upper,-lower
        intervals.append((lower,upper))
    candidates=[s/(1+c) for s in intervals[0] for c in intervals[1]]
    lower,upper=min(candidates),max(candidates)
    grid=2**80
    scaled=(lower+upper)*grid/2
    floor=scaled.numerator//scaled.denominator
    tail=scaled-floor
    nearest=floor+int(tail>Q(1,2) or (tail==Q(1,2) and floor%2!=0))
    u=Q(nearest,grid)
    epsilon=max(abs(u-lower),abs(u-upper))
    origin=points[0]
    area=Q(0); weighted=[Q(0),Q(0)]
    for b,c in zip(points[1:-1],points[2:]):
        weight=(b[0]-origin[0])*(c[1]-origin[1])-(b[1]-origin[1])*(c[0]-origin[0])
        area+=weight
        for k in (0,1):
            weighted[k]+=weight*(origin[k]+b[k]+c[k])
    assert area
    center=tuple(v/(3*area) for v in weighted)
    reach=max(sum(abs(p[k]-center[k]) for k in (0,1)) for p in points)
    residual=Q(0)
    for p,q in zip(points,endpoints):
        lx,ly=p[0]-center[0],p[1]-center[1]
        # (lx+i*ly)*(1+i*u)^2/(1+u^2), staged differently from production.
        re,im=lx-u*ly,ly+u*lx
        rotated=((re-u*im)/(1+u*u),(im+u*re)/(1+u*u))
        candidate=(p[0]+dx+ex*lx+gxy*ly/2+rotated[0]-lx,
                   p[1]+dy+gxy*lx/2+ey*ly+rotated[1]-ly)
        residual=max(residual,abs(candidate[0]-q[0]),abs(candidate[1]-q[1]))
    position=reach*(abs(u)**3/2+2*epsilon)
    endpoint_parameter=2*reach*epsilon
    assert position>=0 and endpoint_parameter>=0 and residual>=0
    return {"radius":position+residual+endpoint_parameter,
            "position":position,"residual":residual,"endpoint_parameter":endpoint_parameter}

minimum={}
certificate_counts=Counter()

def remember(key,value):
    if key not in minimum or value<minimum[key]:
        minimum[key]=value

def check_separation(certificate,left,right):
    assert certificate["kind"]=="ROBUST_NO_CONTACT"
    radius=Q(certificate["radius_sum"])
    assert radius>=0
    witnesses=certificate["witnesses"]
    assert witnesses
    current=left
    gaps=[]
    for witness in witnesses:
        lo,hi=map(Q,witness["window"])
        assert lo==current and lo<=hi<=right
        current=hi
        n=tuple(map(Q,witness["normal"]))
        assert len(n)==2 and sum(abs(v) for v in n)>0
        gap=Q(witness["gap_lower"])
        assert gap>radius, "strict projected separation margin"
        remember("separation_gap_minus_radius",gap-radius)
        gaps.append(gap)
        certificate_counts["separation_panel_witnesses"]+=1
    assert current==right and Q(certificate["gap_lower"])==min(gaps)
    assert Q(certificate["gap_lower"])>radius
    certificate_counts["separation_model_certificates"]+=1
    return radius

def check_time_bracket(certificate,lo,hi):
    if certificate.get("rational") is not None:
        assert lo<Q(certificate["rational"])<hi
    else:
        poly=certificate["polynomial"]
        assert eval_poly(poly,lo)*eval_poly(poly,hi)<0, "stored nominal polynomial crosses certificate bracket"
    certificate_counts["stored_root_bracket_sign_checks"]+=1

def check_result(result,blocks,expected_radius):
    classification=result["classification"]
    assert classification in CLASSES
    p1,p2=result["p1"],result["p2"]
    f1,f2=[tuple(x) for x in p1["features"]],[tuple(x) for x in p2["features"]]
    assert f1==sorted(set(f1)) and f2==sorted(set(f2))
    actual_same=(p1["status"]==p2["status"] and set(f1)==set(f2))
    assert type(result["same"]) is bool and result["same"]==actual_same
    assert type(result["oracle_checked"]) is bool
    for model in (p1,p2):
        assert model["status"] in ("no_contact","contact","initial_overlap")
        if model["status"]!="contact":
            assert model["time"] is None and not model["features"]
        else:
            assert model["time"] is not None
    if classification=="MODEL_SENSITIVE_OR_UNPROVED":
        reason=result["reason"]
        assert reason in ("INITIAL_EXIT_ORDER_UNCERTIFIED","NO_SUFFICIENT_CERTIFICATE","OBSERVED_P1_P2_DIFFERENCE")
        if reason=="INITIAL_EXIT_ORDER_UNCERTIFIED":
            assert p1["status"]==p2["status"]=="initial_overlap" and result["initial_state"]==1
        if reason=="OBSERVED_P1_P2_DIFFERENCE":
            assert not actual_same
        return
    assert actual_same, "robust subset must agree in status and full first-cover set"
    cert=result["certificate"]
    charged=[Q(cert["radius_sum"])] if isinstance(cert,dict) else [Q(c["radius_sum"]) for c in cert]
    assert charged and all(radius==expected_radius for radius in charged), "every robust certificate charges independent full r2 block-radius sum"
    certificate_counts["independent_pair_radius_checks"]+=1
    if classification=="ROBUST_NO_CONTACT":
        assert p1["status"]==p2["status"]=="no_contact"
        if isinstance(cert,dict):
            radius=Q(cert["radius_sum"])
            gaps=tuple(map(Q,cert["gap_lower"]))
            assert radius>=0 and len(gaps)==2 and min(gaps)>radius
            for gap in gaps:
                remember("separation_gap_minus_radius",gap-radius)
            certificate_counts["axis_fast_pair_certificates"]+=1
        else:
            assert isinstance(cert,list) and len(cert)==2
            radii=[check_separation(c,Q(0),Q(1)) for c in cert]
            assert radii[0]==radii[1]
    else:
        assert p1["status"]==p2["status"]=="contact" and len(f1)==1 and f1[0][0]=="VE"
        assert result["initial_state"]==-1
        assert isinstance(cert,list) and len(cert)==2
        assert cert[0]["bracket"]==cert[1]["bracket"]
        assert cert[0]["radius_sum"]==cert[1]["radius_sum"]
        for nominal,c in zip((p1,p2),cert):
            assert c["kind"]=="ROBUST_SINGLE_FIRST_COVER"
            lo,hi=map(Q,c["bracket"])
            assert Q(0)<=lo<hi<=Q(1)
            radius=Q(c["radius_sum"])
            assert radius>=0 and check_separation(c["early"],Q(0),lo)==radius
            assert global_label(c["label"],blocks[0],blocks[1])==f1[0]
            for field in ("derivative_lower","event_margin_lower","endpoints_margin"):
                value=Q(c[field])
                assert value>0, ("strict-single-cover-margin",field)
                remember("single_cover_"+field,value)
            check_time_bracket(nominal["time"],lo,hi)
            certificate_counts["single_cover_model_certificates"]+=1

def independent_reference_counts(result,selected):
    c=Counter()
    for phase,rows in selected.items():
        state=result["classification"]
        if state=="ROBUST_NO_CONTACT":
            c[phase+":ROBUST_NO_CONTACT_REFERENCE"]=len(rows)
        elif state=="MODEL_SENSITIVE_OR_UNPROVED":
            c[phase+":UNPROVED_REFERENCE"]=len(rows)
        else:
            labels={tuple(x) for x in result["p1"]["features"]}
            hits=sum(tuple(row["primary"]) in labels for row in rows)
            c[phase+":FIRST_COVER_MATCH"]=hits
            c[phase+":OTHER_REFERENCE"]=len(rows)-hits
            c[phase+":ROBUST_CONTACT_MISSING_PAIR"]=int(not rows)
            c[phase+":ROBUST_FIRST_COVER_NOT_SELECTED"]=int(hits==0)
    return c

def audit():
    start=time.perf_counter()
    final_path=RUN/"summary.json"
    frozen_path=EV/"robust_summary.json"
    assert final_path.exists() and frozen_path.exists(), "final r2 summary and published frozen summary required"
    summary=read(final_path)
    assert summary["complete"] is True and summary["full_history"] is True
    assert summary["raw_directory"]==RUN.relative_to(ROOT).as_posix()
    assert final_path.read_bytes()==frozen_path.read_bytes(), "published summary byte identity"
    assert read(RUN/"progress.json")["complete"] is True
    source_before=source_hashes()
    inputs_before=input_hashes()
    assert summary["source_hashes"]==source_before
    assert summary["input_hashes"]==inputs_before
    selected_path=EV/"robust_minimal_examples.json"
    selected_minimals=read(selected_path)
    selected_before=sha(selected_path)
    assert selected_minimals["complete"] is True
    assert selected_minimals["source_hashes"]==source_before
    assert selected_minimals["input_hashes"]==inputs_before
    assert selected_minimals["script_sha256"]==sha(ROOT/"tools/m5b_minimal_examples.py")
    selected_specs={(e["case"],e["step"],tuple(e["pair"])):e for e in selected_minimals["examples"]}
    expected_specs={("bb03",15,(8,11)),("bb12",6,(10,11)),("bb03",1,(1,3)),
                    ("bb03",1,(2,3)),("bb03",1,(1,2))}
    assert len(selected_minimals["examples"])==5 and set(selected_specs)==expected_specs
    selected_verified=[]
    manifest=read(EV/"endpoint_inputs/manifest.json")
    legacy_manifest=read(EV/"legacy_inputs/manifest.json")
    assert manifest["complete"] is True and legacy_manifest["complete"] is True
    assert set(manifest["cases"])==set(legacy_manifest["cases"])==set(summary["cases"])
    frames=defaultdict(lambda:defaultdict(dict))
    for part in manifest["shards"]:
        path=EV/"endpoint_inputs"/part["file"]
        assert sha(path)==part["sha256"]
        assert path.stat().st_size==part["bytes"]<1_000_000
        n=0
        with gzip.open(path,"rt",encoding="utf-8") as stream:
            for line in stream:
                row=json.loads(line)
                case,step,block=row["case"],row["step"],row["block"]
                assert case in manifest["cases"] and 1<=step<=manifest["cases"][case]["steps"]
                assert block not in frames[case][step], "unique frozen block frame"
                frames[case][step][block]=row
                n+=1
        assert n==part["rows"]
    assert sum(len(blocks) for steps in frames.values() for blocks in steps.values())==15220
    block_budgets={(case,step,block):independent_block_budget(row)
                   for case,steps in frames.items() for step,blocks in steps.items() for block,row in blocks.items()}
    budget_nonzero={field:sum(v[field]>0 for v in block_budgets.values())
                    for field in ("position","residual","endpoint_parameter")}
    totals,refs,global_status,secondary=Counter(),Counter(),Counter(),Counter()
    by_case={}
    for case in sorted(manifest["cases"]):
        case_meta=manifest["cases"][case]
        expected=frames[case]
        assert set(expected)==set(range(1,case_meta["steps"]+1))
        assert sum(map(len,expected.values()))==case_meta["block_frames"]
        legacy_path=EV/"legacy_inputs"/(case+".jsonl.gz")
        assert sha(legacy_path)==legacy_manifest["cases"][case]["sha256"]
        legacy={}
        with gzip.open(legacy_path,"rt",encoding="utf-8") as stream:
            for line in stream:
                row=json.loads(line)
                assert row["step"] not in legacy
                legacy[row["step"]]=row
        assert set(legacy)==set(expected)
        selected_by_pair={}
        original_primary=Counter()
        for step,legacy_frame in legacy.items():
            grouped=defaultdict(lambda:{p:[] for p in PHASES})
            allowed=set(combinations(sorted(expected[step]),2))
            for phase in PHASES:
                for row in legacy_frame[phase]:
                    pair=tuple(row["pair"])
                    assert pair in allowed
                    grouped[pair][phase].append(row)
                    original_primary[phase]+=1
                    raw=row["raw"]
                    secondary[phase]+=int(raw[0]==1 and raw[4]>0)
            selected_by_pair[step]=grouped
        directory=RUN/case
        case_summary=read(directory/"summary.json")
        assert case_summary==summary["cases"][case] and case_summary["complete"] is True
        assert read(directory/"progress.json")["complete"] is True
        raw_path=directory/"pairs.jsonl.gz"
        before=sha(raw_path)
        assert before==case_summary["raw_sha256"]
        counts,case_refs,seen,first_examples=Counter(),Counter(),set(),{}
        with gzip.open(raw_path,"rt",encoding="utf-8") as stream:
            for line in stream:
                packed=json.loads(line)
                assert packed["case"]==case
                step,pair=packed["step"],tuple(packed["pair"])
                assert step in expected and len(pair)==2 and pair[0]<pair[1]
                assert all(b in expected[step] for b in pair)
                key=step,pair
                assert key not in seen, "duplicate replay pair"
                seen.add(key)
                result=packed["result"]
                block_rows=[expected[step][b] for b in pair]
                expected_radius=sum((block_budgets[(case,step,b)]["radius"] for b in pair),Q(0))
                check_result(result,block_rows,expected_radius)
                selected=selected_by_pair[step].get(pair,{p:[] for p in PHASES})
                spec=(case,step,pair)
                if spec in selected_specs:
                    example=selected_specs[spec]
                    assert example["blocks"]==block_rows and example["legacy"]==selected
                    assert example["expected"]=={"result":result,"legacy_counts":packed["legacy_counts"]}, "selected single reexecution differs from full-history raw pair"
                    selected_verified.append({"case":case,"step":step,"pair":list(pair)})
                calculated=independent_reference_counts(result,selected)
                same_counts(calculated,packed["legacy_counts"],"raw per-pair primary reference counts")
                case_refs.update(calculated)
                counts["pairs"]+=1
                counts[result["classification"]]+=1
                counts["p1_p2_same" if result["same"] else "p1_p2_different"]+=1
                counts["independent_initial_state_checks"]+=result["oracle_checked"]
                if result["classification"]=="MODEL_SENSITIVE_OR_UNPROVED":
                    counts[result["reason"]]+=1
                global_status["P1:"+result["p1"]["status"]]+=1
                global_status["P2:"+result["p2"]["status"]]+=1
                example_key=result["classification"] if result["classification"]!="MODEL_SENSITIVE_OR_UNPROVED" else result["reason"]
                if example_key not in first_examples:
                    first_examples[example_key]={**packed,"blocks":block_rows,"legacy":selected}
        expected_pairs={(step,pair) for step,blocks in expected.items() for pair in combinations(sorted(blocks),2)}
        assert seen==expected_pairs, "exact all-step/all-pair coverage"
        counts["steps"]=len(expected)
        counts["blocks"]=sum(map(len,expected.values()))
        same_counts(counts,case_summary["counts"],"independent per-case counters")
        same_counts(case_refs,case_summary["references"],"independent per-case primary ledger")
        assert first_examples==case_summary["examples"], "minimal witness row/input/legacy matches first occurrence"
        assert sum(counts[k] for k in CLASSES)==counts["pairs"]
        for phase in PHASES:
            assert sum(case_refs[phase+":"+category] for category in ROW_CATEGORIES)==original_primary[phase], "primary row conservation"
        assert sha(raw_path)==before, "raw file changed during independent audit"
        totals.update(counts); refs.update(case_refs)
        by_case[case]={"counts":dict(counts),"references":dict(case_refs),"raw_sha256":before,
                       "first_witness_keys":sorted(first_examples),"primary_rows":dict(original_primary)}
        print("AUDITED",case,counts["pairs"],flush=True)
    assert (totals["pairs"],totals["steps"],totals["blocks"])==(64010,1810,15220)
    same_counts(totals,summary["counts"],"independent full counts")
    same_counts(refs,summary["references"],"independent full primary reference ledger")
    primary_totals={phase:sum(v["primary_rows"][phase] for v in by_case.values()) for phase in PHASES}
    assert primary_totals=={phase:141594 for phase in PHASES}
    assert dict(secondary)=={phase:7768 for phase in PHASES}
    assert len(selected_verified)==5
    assert sha(selected_path)==selected_before, "selected minimal witnesses changed during audit"
    assert source_hashes()==source_before and input_hashes()==inputs_before
    assert sha(final_path)==sha(frozen_path), "summary changed during review"
    return {"schema":"eab.m5b-independent-model-execution-review.v1","status":"PASS",
            "critical":0,"major":0,"minor":0,"run":"robust_full_r2",
            "summary_sha256":sha(final_path),"source_files_checked":len(source_before),
            "audit_script_sha256":sha(Path(__file__)),
            "selected_minimal_examples_sha256":selected_before,"selected_minimal_examples_verified":selected_verified,
            "input_files_checked":len(inputs_before),"counts":dict(totals),"references":dict(refs),
            "model_statuses":dict(global_status),"primary_rows_total":primary_totals,
            "secondary_rows_present_but_not_classified":dict(secondary),
            "certificate_checks":dict(certificate_counts),"minimum_strict_margins":{k:str(v) for k,v in minimum.items()},
            "independent_block_budgets_checked":len(block_budgets),"positive_budget_components":budget_nonzero,
            "cases":by_case,"seconds":time.perf_counter()-start,
            "oracle_imports":["pathlib","collections","fractions.Fraction","itertools.combinations","math.factorial","gzip","hashlib","json","time","traceback"],
            "no_production_imports":True,"roots_resolved_again":False,
            "checked":["full pair-set equality and unique frozen block frames","all raw-to-case-to-global counters",
                       "primary row conservation against frozen legacy records","all robust statuses and complete cover sets agree",
                       "independent triangle-fan/factorial Taylor/complex endpoint r2 budget for every input block; exact radius_sum equality in every robust pair",
                       "every stored strict margin and early-panel coverage","local cover IDs reconstruct frozen global feature",
                       "nominal polynomial sign crossing in stored first-cover bracket (not a new root solve)",
                       "case-summary first witnesses exactly match first raw pair/input blocks/legacy rows","five selected independently rerun minimal examples exactly match corresponding raw results/input/legacy","complete source/input hash set before and after review"],
            "limits":["secondary reference classification not implemented; all reference claims primary-only",
                      "stored certificates audited, no re-evaluation of all geometric inequalities and no repeated root solving",
                      "P3 is certified by model tubes, not a computed transcendental root trajectory",
                      "positive-radius initial exit ordering and historical midpoint scope remain PARTIAL",
                      "execution audit is not a substitute for the full independent G6 exit gate"]}

def write_report(result):
    path=EV/"review_model_execution.json"
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
    if result["status"]!="PASS":
        text="# M5b 全时程执行独立审查\n\n状态：**FAIL / 未通过**。\n\n"+result["error"]+"\n\n见 [review_model_execution.json](review_model_execution.json)。\n"
    else:
        c=result["counts"]; cert=result["certificate_checks"]
        lines=["# M5b 全时程执行独立审查：robust_full_r2",
               "",
               "**PASS；critical 0、major 0、minor 0（以下明确范围内）。** 本审查从冻结输入和逐对 gzip 重新计数，没有 import 生产模块，没有重复求根；不是对本人 P2 核心的独立几何验收，也不是总体 G6 退出声明。",
               "",
               "## 完整性与守恒",
               "",
               f"- 精确集合核对：**{c['pairs']} 步—块对 / {c['steps']} 步 / {c['blocks']} 块帧 / 15 算例**，无重复、无遗漏。",
               f"- 稳健无接触 {c.get('ROBUST_NO_CONTACT',0)}；稳健单首盖 {c.get('ROBUST_SINGLE_FIRST_COVER',0)}；模型敏感或未证 {c.get('MODEL_SENSITIVE_OR_UNPROVED',0)}；三类之和等于全部块对。",
               f"- P1/P2 状态及完整首盖集合一致 {c.get('p1_p2_same',0)}，实际不同 {c.get('p1_p2_different',0)}；未证不算实际不同。",
               f"- 核对 {result['source_files_checked']} 个完整绑定源码、{result['input_files_checked']} 个冻结输入文件，以及全部逐对文件的 SHA256；审查前后不变。发布摘要与运行摘要逐字节相同。",
               "- 每个算例的原始逐对记录→case summary→全局 summary 独立 Counter 一致；case 摘要各分类见证与原始首见记录、输入块、legacy 原行逐值相同。",
               "- 另核对 `robust_minimal_examples.json` 的五个指定独立单例重算：与全时程对应 case/step/pair 的完整 result、账本、输入和 legacy 原行逐值相同。这五例不要求是全 raw 首见。",
               "",
               "## 证书检查",
               "",
               f"- 快速轴包围块对证书 {cert.get('axis_fast_pair_certificates',0)}；详细分离模型证书 {cert.get('separation_model_certificates',0)}，逐子窗证据 {cert.get('separation_panel_witnesses',0)}。",
               f"- 单首盖模型证书 {cert.get('single_cover_model_certificates',0)}，均验证 gap-radius>0、名义导数/事件/端点余量严格正、早期闭窗连续覆盖、P1/P2 括区间与半径一致。",
               f"- 以独立三角扇形心、直接幂/阶乘 Taylor 与分阶段复乘端点，重新计算 {result['independent_block_budgets_checked']} 个块帧的 r2 预算；所有 {cert.get('independent_pair_radius_checks',0)} 个稳健块对的证书 radius_sum 与两块独立预算之和逐值精确相等。",
               "- r2 预算明确包含：P2/P3 全时程界 + P2 至原端点的线性闭合残差 + P3 自身端点闭合所需的额外半角参数项；不把最后一项误当作已包含。",
               "- 每个单首盖的局部 VE/EV 标签独立通过有向面积确定原始顶点顺序，再映射为全局标签，与记录的完整单首盖集合一致。",
               "- 在记录的括区间上仅代入名义多项式检查异号（或有理根严格落入）；没有重新隔离/求解根，亦不声称单靠此检查重新证明了全部几何不等式。",
               "",
               "## 主参考账本",
               "",
               "- 逐对重建两阶段 primary 主参考 MATCH/OTHER/NO_CONTACT/UNPROVED 分类、无 pair 和未选为主参考计数；每阶段四种行类别之和严格等于冻结 legacy 的 **141594** 条原行。",
               f"- 两阶段各存在 {result['secondary_rows_present_but_not_classified'].get('raw_df05',0)} 条带 secondary 的原始行；**secondary 分类仍未实现**。“FIRST_COVER_NOT_SELECTED”在本单仅表示未选作主参考，不表示全部参考都未选。",
               "",
               "## 审查边界与重跑",
               "",
               "- 本次是执行结果完整性/证书字段审查，不重跑全时程几何事件求解；独立数学/语义正确性由对应独立 oracle 门和理论负责。",
               "- P3 为严格管界保证，非超越首根逐轨求解；正扰动下初始出口排序、历史中点口径等原 PARTIAL 不因本审查通过而自动完成。",
               f"- 审查耗时 {result['seconds']:.3f} 秒；完整 JSON 含逐例 Counter、正余量最小值、摘要 hash、import 清单和范围限制。",
               "- 复跑（只读输入与运行产物；重写本审查报告）：`python reports/codex/M5b_evidence/review_model_execution_audit.py`。TEMP/TMP 仍按本单指向 evidence/tmp。",
               "",
               "[机器可读审查](review_model_execution.json) · [标准库独立审查脚本](review_model_execution_audit.py)"]
        text="\n".join(lines)+"\n"
    (EV/"review_model_execution.md").write_text(text,encoding="utf-8",newline="\n")

try:
    result=audit()
except Exception as error:
    result={"schema":"eab.m5b-independent-model-execution-review.v1","status":"FAIL",
            "error":str(error),"traceback":traceback.format_exc(),"run":"robust_full_r2"}
    write_report(result)
    raise
else:
    write_report(result)
    print("INDEPENDENT_MODEL_EXECUTION_REVIEW_PASS",result["counts"],"seconds",result["seconds"],flush=True)

