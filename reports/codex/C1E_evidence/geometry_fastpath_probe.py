"""Direct convex fast-path differential; existing static core, no DLL/source edits.

Run from the repository with --name NEW_NAME. Compiler options are taken from
the verified test compile command. Artifacts remain under C1E_evidence/tmp.
Python expectations use kernel2d.exact directly, never C++ predicates/helpers.
"""
from __future__ import annotations
import argparse
from fractions import Fraction as F
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
from eab.kernel2d.exact import entrance_block_exact, membership_exact, ve_side_exact, ev_side_exact, signed_area2

CPP = r'''
#include "geometry2.hpp"
#include "numeric.hpp"
#include <iostream>
#include <string>
using namespace eab2::geometry2;
Point read_point() { std::string x,y; std::cin>>x>>y; return {eab2::numeric::parse_rational(x),eab2::numeric::parse_rational(y)}; }
int main() {
    try {
        std::size_t count; std::cin>>count;
        for(std::size_t k=0;k<count;++k) {
            std::size_t na,nb,nq;std::cin>>na>>nb>>nq;
            Polygon a,b;for(std::size_t i=0;i<na;++i)a.push_back(read_point());for(std::size_t j=0;j<nb;++j)b.push_back(read_point());
            const auto exact=entrance_block_exact(a,b);
            std::cout<<"{\"vertices\":"<<polygon_json(exact.vertices)<<",\"facets\":[";
            for(std::size_t i=0;i<exact.facets.size();++i) {if(i)std::cout<<',';const auto& f=exact.facets[i];
                std::cout<<"{\"label\":"<<label_json(f.label)<<",\"start\":"<<point_json(f.start)<<",\"direction\":"<<point_json(f.direction)<<'}';}
            std::cout<<"],\"pairs\":[";
            for(std::size_t i=0;i<exact.pairs.size();++i){if(i)std::cout<<',';std::cout<<'['<<exact.pairs[i][0]<<','<<exact.pairs[i][1]<<']';}
            std::cout<<"],\"membership\":[";
            for(std::size_t i=0;i<nq;++i){const auto p=read_point();if(i)std::cout<<',';std::cout<<membership_exact(exact,p);}
            std::cout<<"],\"ve\":[";
            for(std::size_t i=0;i<na;++i)for(std::size_t j=0;j<nb;++j){if(i||j)std::cout<<',';std::cout<<ve_side_exact(a,i,b,j);}
            std::cout<<"],\"ev\":[";
            for(std::size_t i=0;i<na;++i)for(std::size_t j=0;j<nb;++j){if(i||j)std::cout<<',';std::cout<<ev_side_exact(a,i,b,j);}
            std::cout<<"],\"area2\":[\""<<signed_area2(a).canonical()<<"\",\""<<signed_area2(b).canonical()<<"\"]}\n";
        }
    } catch(const std::exception& e) {std::cerr<<e.what()<<'\n';return 1;}
}
'''

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def ptext(p):
    return [f"{F(v).numerator}/{F(v).denominator}" for v in p]

def corpus():
    bases = [
        ("general", [(0,0),(3,1),(1,4)], [(2,-1),(6,0),(5,3),(1,2)]),
        ("asymmetric", [(0,0),(4,0),(3,2),(-1,3)], [(0,0),(3,1),(1,2)]),
        ("flat", [(0,0),(F(1,2),0),(2,0),(2,3),(0,3)], [(0,0),(1,0),(1,1),(1,4),(0,4)]),
        ("parallel", [(0,0),(2,0),(2,3),(0,3)], [(1,-2),(2,-2),(2,3),(1,3)]),
        ("one_ulp_slope", [(0,0),(1,F(1,2**52)),(0,1)], [(0,0),(1,0),(1,1),(0,1)]),
    ]
    for name,a,b in bases:
        for shift in range(3):
            aa=a[shift%len(a):]+a[:shift%len(a)]
            bb=b[(2*shift)%len(b):]+b[:(2*shift)%len(b)]
            for exponent in (-400,0,400):
                scale=F(2)**exponent
                for quarter in (False,True):
                    def transform(poly, tx,ty):
                        out=[]
                        for x,y in poly:
                            x,y=(F(-y),F(x)) if quarter else (F(x),F(y))
                            p=(scale*(x+tx),scale*(y+ty))
                            assert all(F(float(v))==v for v in p), "fixture must be exactly representable binary64"
                            out.append(p)
                        return out
                    # Avoid adding an offset to the 1-ULP y perturbation: doing
                    # so can make the exact point require more than 53 bits.
                    ta=(0,0) if name=="one_ulp_slope" else (8,-4)
                    yield f"{name}/cycle{shift}/scale{exponent}/q{int(quarter)}",transform(aa,*ta),transform(bb,-4,8)

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--name",required=True);args=parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_-]+",args.name):parser.error("name must be a single ASCII component")
    run=EVIDENCE/"tmp"/f"convex_fastpath_{args.name}";run.mkdir(parents=True,exist_ok=False)
    report_path=EVIDENCE/f"convex_fastpath_{args.name}.json"
    if report_path.exists():raise RuntimeError("refuse existing report")
    core=ROOT/"eab2/build/eab2_core.lib";dll=ROOT/"eab2/build/eab2_test.dll"
    inputs=[ROOT/"eab2/src/geometry2.cpp",ROOT/"eab2/src/geometry2.hpp",ROOT/"eab2/src/exact.hpp",core,dll]
    before={str(p.relative_to(ROOT)):digest(p) for p in inputs}
    source=run/"probe.cpp";source.write_text(CPP,encoding="utf-8",newline="\n")
    database=json.loads((ROOT/"eab2/build/compile_commands.json").read_text(encoding="utf-8"))
    entry=next(r for r in database if Path(r["file"]).name=="test_geometry2.cpp")
    command=entry["command"].replace(entry["file"],str(source));obj=run/"probe.obj";exe=run/"probe.exe"
    command=re.sub(r'/Fo(?:"[^"]+"|\S+)',f'/Fo"{obj.as_posix()}"',command)
    command=re.sub(r'/Fd(?:"[^"]+"|\S+)',f'/Fd"{(run/"probe.pdb").as_posix()}"',command)
    compiler=command.split(" ",1)[0]
    link=f'{compiler} /nologo /MD "{obj}" "{core}" /link /OUT:"{exe}" /INCREMENTAL:NO /MACHINE:X64'
    vs=Path(r"C:\Program Files\Microsoft Visual Studio\2022\Community")
    batch=run/"build.bat"
    batch.write_text(f'@echo off\ncall "{vs}/VC/Auxiliary/Build/vcvars64.bat" -vcvars_ver=14.44.35207 >nul\nif errorlevel 1 exit /b 70\n'
                     f'cd /d "{entry["directory"]}"\n{command}\nif errorlevel 1 exit /b 71\n{link}\nexit /b %errorlevel%\n',encoding="ascii",newline="\r\n")
    env=dict(os.environ);env.update(TEMP=str(EVIDENCE/"tmp"),TMP=str(EVIDENCE/"tmp"),VSLANG="1033")
    env["PATH"]=str(Path(env.get("ProgramFiles(x86)",r"C:\Program Files (x86)"))/"Microsoft Visual Studio/Installer")+os.pathsep+env.get("PATH","")
    started=time.perf_counter();log=run/"build.log"
    with log.open("xb") as out:
        built=subprocess.run([env.get("COMSPEC",r"C:\Windows\System32\cmd.exe"),"/d","/c",str(batch)],env=env,stdout=out,stderr=subprocess.STDOUT,timeout=45,check=False)
    if built.returncode:raise RuntimeError(f"probe build failed {built.returncode}; see {log}")
    cases=list(corpus());payload=[str(len(cases))];expected=[];counts={"membership":0,"facets":0,"side_predicates":0}
    for name,a,b in cases:
        e=entrance_block_exact(a,b)
        samples=list(e.vertices)+[tuple((p[k]+e.vertices[(i+1)%len(e.vertices)][k])/2 for k in (0,1)) for i,p in enumerate(e.vertices)]
        samples+=[tuple(sum(p[k] for p in e.vertices)/len(e.vertices) for k in (0,1)),(max(p[0] for p in e.vertices)+1,max(p[1] for p in e.vertices)+1)]
        payload.append(f"{len(a)} {len(b)} {len(samples)}")
        payload.extend(" ".join(ptext(p)) for p in a+b+samples)
        expected.append({"vertices":[ptext(p) for p in e.vertices],"facets":[{"label":list(f.label),"start":ptext(f.start),"direction":ptext(f.direction)} for f in e.facets],
                         "pairs":[list(p) for p in e.pairs],"membership":[membership_exact(a,b,p,e) for p in samples],
                         "ve":[ve_side_exact(a,i,b,j) for i in range(len(a)) for j in range(len(b))],
                         "ev":[ev_side_exact(a,i,b,j) for i in range(len(a)) for j in range(len(b))],
                         "area2":[ptext((signed_area2(a),signed_area2(b)))[i] for i in (0,1)]})
        counts["membership"]+=len(samples);counts["facets"]+=len(e.facets);counts["side_predicates"]+=2*len(a)*len(b)
    input_path=run/"input.txt";input_path.write_text("\n".join(payload)+"\n",encoding="ascii",newline="\n")
    result=subprocess.run([str(exe)],input=input_path.read_text(encoding="ascii"),capture_output=True,text=True,encoding="utf-8",errors="strict",env=env,timeout=15,check=False)
    if result.returncode:raise RuntimeError(result.stderr)
    actual=[json.loads(row) for row in result.stdout.splitlines()]
    (run/"cpp_output.jsonl").write_text(result.stdout,encoding="utf-8",newline="\n")
    failures=[{"case":cases[i][0],"different_fields":[k for k in expected[i] if expected[i][k]!=row[k]]} for i,row in enumerate(actual) if expected[i]!=row]
    if len(actual)!=len(expected):failures.append({"case":"count","expected":len(expected),"actual":len(actual)})
    unchanged=before=={str(p.relative_to(ROOT)):digest(p) for p in inputs}
    last=f'C1_CONVEX_FASTPATH cases={len(cases)} facets={counts["facets"]} membership={counts["membership"]} side_predicates={counts["side_predicates"]} mismatches={len(failures)} original_unchanged={int(unchanged)}'
    report={"schema":"eab2.c1.convex_fastpath.v1","passed":not failures and unchanged,"scope":"Direct private C++ convex primitive differential; existing static core; no DLL/source edits; not independent review.",
            "source_sha256":before,"case_names":[c[0] for c in cases],"counts":counts,"mismatches":failures,"actual_compile_command":command,"link_command":link,
            "input_sha256":digest(input_path),"output_sha256":digest(run/"cpp_output.jsonl"),"original_unchanged":unchanged,"seconds":time.perf_counter()-started,"last_line":last}
    with report_path.open("x",encoding="utf-8",newline="\n") as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write("\n")
    print(last);return 0 if report["passed"] else 1

if __name__=="__main__":raise SystemExit(main())
