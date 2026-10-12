from pathlib import Path
import subprocess,sys,os,json
root=Path('D:/eab-wt/g6h'); out=root/'review/agents/docs_gates';out.mkdir(parents=True,exist_ok=True)
rows=[]
for name in ['docs_residual_claims.py','docs_tight_cavity_pd.py','docs_g6e50.py','docs_replay_extra.py','docs_g6e_36.py']:
 s=(Path('D:/eab-wt/g6g/review/repro')/name).read_text(encoding='utf-8-sig').replace("ROOT/'review/notes/","ROOT/'review/agents/docs_gates/")
 p=root/'review/repro'/name;p.write_text(s,encoding='utf-8')
 cmd=[sys.executable,'-X','utf8',str(p)]
 r=subprocess.run(cmd,cwd=root,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PYTHONIOENCODING':'utf-8'},capture_output=True,text=True,encoding='utf-8',errors='replace')
 log=root/'review/logs'/('docs_replay_'+name.removesuffix('.py')+'.log');log.write_text(r.stdout+r.stderr,encoding='utf-8')
 rows.append({'script':str(p.relative_to(root)),'exit_code':r.returncode,'verified_output':r.stdout+r.stderr,'log':str(log.relative_to(root))})
 print(name,r.returncode,(r.stdout+r.stderr)[-500:])
(out/'replay_raw.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
