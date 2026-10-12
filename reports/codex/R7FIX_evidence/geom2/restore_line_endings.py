from pathlib import Path
from zipfile import ZipFile
z=ZipFile('reports/codex/R7FIX_evidence/baseline_tracked.zip')
for name in ['src/eab/kernel2d/g0_oracle.py','src/eab/kernel2d/g0.py','src/eab/kernel2d/covers.py','src/eab/kernel2d/geom.py']:
    old=z.read(name);p=Path(name);new=p.read_bytes()
    print(name,'baseline CRLF',old.count(b'\r\n'),'LF',old.count(b'\n'),'new CRLF',new.count(b'\r\n'))
    # Preserve original line terminators for unchanged lines; inserted lines use
    # the dominant original delimiter. This also preserves intentionally mixed files.
    from difflib import SequenceMatcher
    ol=old.splitlines(keepends=True);nl=new.splitlines(keepends=True)
    oa=[v.rstrip(b'\r\n') for v in ol];na=[v.rstrip(b'\r\n') for v in nl]
    ending=b'\r\n' if old.count(b'\r\n')>old.count(b'\n')/2 else b'\n'
    out=[]
    for tag,i,j,k,l in SequenceMatcher(None,oa,na,autojunk=False).get_opcodes():
        if tag=='equal':out.extend(ol[i:j])
        else:out.extend(v+ending for v in na[k:l])
    p.write_bytes(b''.join(out))
