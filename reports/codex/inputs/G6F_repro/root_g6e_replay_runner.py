import pathlib,json,subprocess,sys,os,time
root=pathlib.Path.cwd(); fs=json.loads((root/'reports/codex/inputs/g6e_findings_raw.json').read_text(encoding='utf-8'))['findings']
results=[]
for i in (9,11,20,21,22,45):
 s=fs[i-1]['how_to_reproduce']
 if ' -c "' in s: code=s.split(' -c "',1)[1].split('\n"',1)[0]
 elif "<<'EOF'" in s: code=s.split("<<'EOF'",1)[1].split('\nEOF',1)[0]
 elif '--- F6.py ---' in s: code=s.split('--- F6.py ---',1)[1].split('--- output ---',1)[0]
 else: raise ValueError(i)
 script=root/f'review/repro/root_g6e_{i:02}.py'; script.write_text(code,encoding='utf-8')
 start=time.time(); p=subprocess.run([sys.executable,'-X','utf8',str(script)],cwd=root,capture_output=True,text=True,encoding='utf-8',env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONIOENCODING='utf-8'))
 out=p.stdout+p.stderr; log=root/f'review/logs/root_g6e_{i:02}.log'; log.write_text(out,encoding='utf-8')
 results.append(dict(g6e_id=i,kind='original-input replay, Python body extracted verbatim; current root import',exit_code=p.returncode,elapsed_seconds=time.time()-start,script=str(script.relative_to(root)),log=str(log.relative_to(root)),verified_output=out))
 print('RAW',i,'EXIT',p.returncode); print(out)
(root/'review/notes/root_g6e_replay.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
