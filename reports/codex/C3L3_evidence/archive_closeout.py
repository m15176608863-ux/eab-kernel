"""Append-only WO-C3L3 local archive; no deletion, no Git writes."""
import gzip,hashlib,json,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/"reports/codex/C3L3_evidence"
ARCHIVE=Path("D:/eab-evidence/reports/codex/C3L3_evidence/run_20261023")
def sha(data):return hashlib.sha256(data).hexdigest()
def main():
    for name in ("baseline","final_fast","final_full"):
        summary=json.loads((OUT/name/"summary.json").read_text("utf-8"))
        assert summary["audit"]=="GREEN" and summary["complete"],name
    assert not ARCHIVE.exists(),"append-only archive destination already exists"
    ARCHIVE.mkdir(parents=True,exist_ok=False)
    rows=[]
    sources=[]
    for name in ("baseline","final_fast","final_full"):
        sources.extend(p for p in (OUT/"tmp"/name).iterdir() if p.is_file() and p.suffix in (".txt",".json"))
    sources.extend(p for p in (OUT/"tmp/superseded_diff_before_checker_strengthening").rglob("*") if p.is_file())
    sources.extend(p for p in (OUT/"tmp/rollback").rglob("*") if p.is_file())
    for name in ("statics","critical"):
        folder=ROOT/f"eab2/build/tmp/c3l3_{name}_final"
        sources.extend(p for p in folder.rglob("*") if p.is_file() and p.suffix in (".cpp",".hpp",".bat",".log",".json"))
    sources.extend(p for p in (OUT/"tmp/scale").iterdir() if p.is_file())
    for source in sorted(set(sources)):
        relative=source.relative_to(ROOT).as_posix()
        target=ARCHIVE/(relative+".gz")
        target.parent.mkdir(parents=True,exist_ok=True)
        original=source.read_bytes();packed=gzip.compress(original,compresslevel=9,mtime=0)
        with target.open("xb") as stream:stream.write(packed)
        readback=target.read_bytes()
        assert gzip.decompress(readback)==original and source.read_bytes()==original
        rows.append(dict(original=relative,archive=target.as_posix(),bytes=len(original),sha256=sha(original),archive_bytes=len(readback),archive_sha256=sha(readback),verified_decompression=True))
    source_dir=OUT/"tmp/final_full/source"
    manifest=json.loads((OUT/"tmp/final_full/source_manifest.json").read_text("utf-8"))
    target=ARCHIVE/"final_full_tested_source.zip"
    with zipfile.ZipFile(target,"x",compression=zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
        for item in manifest:
            data=(source_dir/item["path"]).read_bytes()
            assert sha(data)==item["sha256"]
            archive.writestr(item["path"],data)
    with zipfile.ZipFile(target) as archive:
        assert sorted(archive.namelist())==sorted(item["path"] for item in manifest)
        for item in manifest:assert sha(archive.read(item["path"]))==item["sha256"]
    result=dict(schema="eab2.c3l3.archive.v1",base_commit="1b6b4f32ff3c5716f8e3a24ad73dd3cf6081f39c",archive_root=ARCHIVE.as_posix(),local_archive_not_remote_backup=True,no_sources_deleted=True,files=rows,tested_source_zip=dict(path=target.as_posix(),bytes=target.stat().st_size,sha256=sha(target.read_bytes()),members=len(manifest),all_members_sha256_verified=True,fresh_git_checkout=False),raw_file_count=len(rows),raw_bytes=sum(r["bytes"] for r in rows))
    encoded=json.dumps(result,ensure_ascii=False,indent=2)+"\n"
    (OUT/"archive_manifest.json").write_text(encoded,encoding="utf-8")
    with (ARCHIVE/"archive_manifest.json").open("x",encoding="utf-8") as stream:stream.write(encoded)
    print(f"C3L3_ARCHIVE_OK files={len(rows)} source_members={len(manifest)} verified=true")
if __name__=="__main__":main()
