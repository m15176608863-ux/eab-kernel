import pathlib,subprocess,sys,json,os,time
R=pathlib.Path.cwd(); items=['solid_convex_cache_alias','solid_convex_face_hint','solid_hidden_convexity','geom3_nominal_translation_loss','geom2_confirmed','geom3_g0_skip','gates_docs_stale_margin_claim']
rows=[]
for name in items:
 cmd=[sys.executable,'-X','utf8',f'review/repro/{name}.py']; start=time.time()
 p=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',cwd=R,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONIOENCODING='utf-8'))
 out=p.stdout+p.stderr; path=R/f'review/logs/root_confirmation_{name}.log'; path.write_text(out,encoding='utf-8')
 row=dict(script=f'review/repro/{name}.py',exit_code=p.returncode,elapsed_seconds=time.time()-start,verified_output=out,log=str(path.relative_to(R))); rows.append(row)
 print(name,'exit=',p.returncode);print(out)
 assert p.returncode==0,row
(R/'review/notes/root_confirmations.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
