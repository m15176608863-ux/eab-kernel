"""Fetch/audit the two public Xbloc sources; deliberately NOT a solid decoder.

Standard library only. Writes only reports/codex/M3b_evidence[/tmp/xbloc].
No source code, executable, or installer is downloaded or executed. A changed
upstream file fails its pinned hash instead of silently renewing provenance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from urllib.request import Request, urlopen
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports/codex/M3b_evidence"
RAW = OUT / "tmp/xbloc"
SOURCES = (
    ("source.pdf", "https://www.iadc-dredging.com/wp-content/uploads/2017/03/article-introduction-of-the-xbloc-breakwater-armour-unit-94-01.pdf",
     "b2ebb5fb01383014e289639725baa85adb941eca231b0def4c2fde95e4fc5ec8"),
    ("4cub_xbloc.zip", "https://xbloc.com/beheer/upload/3/Download/4cub_xbloc.zip",
     "3bbbb4883eae3381c9c6a7e27fe79c23e3ccf6dca4298c0fcdbe9172deb5c93d"),
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--download", action="store_true")
    args = parser.parse_args()
    RAW.mkdir(parents=True, exist_ok=True)
    records = []
    for name, url, expected in SOURCES:
        path = RAW / name
        if args.download:
            request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urlopen(request, timeout=40) as response:
                data = response.read()
            actual = hashlib.sha256(data).hexdigest()
            if actual != expected:
                raise ValueError(f"source changed, manual review required: {name}: {actual}")
            path.write_bytes(data)
        data = path.read_bytes()
        actual = hashlib.sha256(data).hexdigest()
        if actual != expected:
            raise ValueError(f"source hash mismatch: {name}: {actual}")
        records.append(dict(name=name, url=url, sha256=actual, bytes=len(data)))
    # The source PDF stores Figure 7's image separately from the text layer.
    # This fixed-source extraction is not a generic PDF parser or a renderer.
    pdf = (RAW / "source.pdf").read_bytes()
    obj = re.search(rb"(?<!\d)21 0 obj\s*(.*?)\s*endobj", pdf, re.S)[1]
    assert b"/DCTDecode" in obj and b"/Width 270 /Height 167" in obj
    length = int(re.search(rb"/Length\s+(\d+)", obj)[1])
    jpeg = obj.split(b"stream", 1)[1].lstrip(b"\r\n")[:length]
    (RAW / "figure7.jpg").write_bytes(jpeg)
    with zipfile.ZipFile(RAW / "4cub_xbloc.zip") as archive:
        members = [dict(path=item.filename, bytes=item.file_size,
                        sha256=hashlib.sha256(archive.read(item.filename)).hexdigest())
                   for item in archive.infolist()]
        wname = next(n for n in archive.namelist() if n.endswith(".w3d"))
        w3d = archive.read(wname)
        assert w3d.startswith(b";; HSF V11.75")
        descriptor = next(n for n in archive.namelist()
                          if "eModel_" in n and n.endswith("descriptor.xml"))
        description = archive.read(descriptor).decode("utf-8")
        for name in archive.namelist():
            if name.endswith((".png", ".jpg")):
                (RAW / Path(name).name).write_bytes(archive.read(name))
    report = dict(
        status="PARTIAL_NO_CERTIFIED_SOLID", date="2026-10-15", sources=records,
        listing="https://xbloc.com/en/design/xbloc-hatching",
        article=dict(authors=["Pieter B. Bakker", "Martijn Klabbers", "J. S. Reedijk"],
                     title="Introduction of the Xbloc Breakwater Armour Unit",
                     journal="Terra et Aqua", issue=94, date="2004-03", figure=7,
                     pdf_page_zero_based=4, printed_page=7,
                     visually_verified_dimensions=["D", "D/3", "r=D/19"],
                     image_sha256=hashlib.sha256(jpeg).hexdigest(),
                     note="Dimension text is a separate PDF text layer; JPEG alone omits the labels."),
        official_model=dict(title="3D Model of 4m3 Xbloc DWF", retrieved=True,
                            decoded_geometry=False, mesh_error_bound=None,
                            archive_members=members, descriptor=description),
        raw_artifacts="reports/codex/M3b_evidence/tmp/xbloc",
        format_references=["https://docs.techsoft3d.com/hoops/visualize-3df/general/hsf/opcodes/TKE_Shell.html",
                           "https://docs.techsoft3d.com/hoops/visualize-3df/general/hsf/opcodes/edgebreaker.html"],
        blockers=["Complete validated standard-library HSF/W3D shell-connectivity decoder not implemented.",
                  "Figure 7 is not a complete oriented rational face incidence or specification of all junction fillets.",
                  "No certified Hausdorff bound for official display tessellation found; binary32 display data is not exact engineering geometry."],
        not_claimed=["No Xbloc-Xbloc or Xbloc-cube zero-mismatch/escape gate executed.",
                     "No full-solid round-direction mutation executed.",
                     "No guessed model fixture or PROVENANCE entry created."],
    )
    (OUT / "xbloc_sources.json").write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print("Xbloc sources: 2 pinned sources verified; certified solid NOT constructed")


if __name__ == "__main__":
    main()
