"""Render saved diagnostic data only; never import or run a mechanical solver."""
import argparse
import csv
from fractions import Fraction
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from frozen_evidence import data_path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports/codex/T1a_figures"
P0 = ROOT / "reports/codex/T1a_evidence/p0_diagnostic_20261019_01/diagnostics.json"
MORPH = ROOT / "reports/codex/T1a_evidence/resume2/morphology_scan"
COLORS = ("#3976A8", "#8365A4", "#BD7D3C")


def _read(path):
    return json.loads(data_path(ROOT, path).read_text(encoding="utf-8"))


def _number(value):
    return None if value is None else float(Fraction(value))


def _hash(path):
    return hashlib.sha256(data_path(ROOT, path).read_bytes()).hexdigest()


def _rational(value):
    q = Fraction(value)
    return str(q.numerator) + "/" + str(q.denominator)


def _save(fig, name):
    records = []
    for extension in ("png", "svg", "pdf"):
        path = OUT / (name + "." + extension)
        fig.savefig(path, dpi=240, facecolor="white")
        if extension == "svg":
            # Matplotlib's path lines have trailing spaces; strip only those
            # insignificant text bytes before recording the artifact digest.
            text = path.read_text(encoding="utf-8")
            path.write_text("\n".join(line.rstrip() for line in text.splitlines()) + "\n",
                            encoding="utf-8", newline="\n")
        assert path.stat().st_size < 1_000_000, str(path)
        records.append(dict(path=path.name, bytes=path.stat().st_size, sha256=_hash(path)))
    plt.close(fig)
    return records


def _g5(cases):
    fig, axes = plt.subplots(2, 2, figsize=(7.2, 5.6))
    fig.subplots_adjust(left=.10, right=.98, bottom=.14, top=.88, wspace=.28, hspace=.42)
    source = []
    ax = axes[0, 0]
    for n, color in zip((3, 5, 7), COLORS):
        rows = [r for r in cases if r["case_id"].startswith("g5_n" + str(n) + "_mu")]
        rows.sort(key=lambda r: Fraction(r["assembly"]["mu"]))
        reference = rows[0]["reference"]
        P, h, length, b = (_number(reference[k]) for k in ("pressure", "h", "L", "b"))
        switch = 2 * h / (length - b)
        xx = [0, switch, 2.05]
        ax.plot(xx, [min(2 * mu, 4 * h / (length - b)) for mu in xx], color=color, lw=1.5, label=f"N = {n}")
        for row in rows:
            mu, capacity = _number(row["assembly"]["mu"]), _number(row["limit"]["value"])
            ax.plot(mu, capacity / P, "o", ms=4, color=color, mec="white", mew=.55, zorder=4)
            source.append(dict(panel="a", case_id=row["case_id"], quantity="F/P", x=row["assembly"]["mu"],
                               exact_value=_rational(Fraction(row["limit"]["value"]) / Fraction(reference["pressure"])),
                               side="value", status=row["limit"]["mathematical_status"], N=n,
                               P=reference["pressure"], h=reference["h"], L=reference["L"], b=reference["b"]))
    ax.set(xlabel=r"Friction coefficient $\mu$", ylabel=r"Capacity $F/P$", xlim=(-.05, 2.08), ylim=(-.07, 2.22))
    ax.legend(fontsize=7, loc="upper left", bbox_to_anchor=(.02, .99))
    ax.text(.16, 1.0, "sliding", fontsize=7, rotation=42, color=COLORS[0])
    ax.text(1.32, 1.85, "hinging (N = 3)", fontsize=7, color=COLORS[0])
    primary = sorted([r for r in cases if r["case_id"].startswith("g5_n3_mu")], key=lambda r: Fraction(r["assembly"]["mu"]))
    ref = primary[0]["reference"]
    P, h, length, b = (_number(ref[k]) for k in ("pressure", "h", "L", "b"))
    switch = 2 * h / (length - b)
    for panel, ax, parameter, ylabel in zip("bcd", (axes[0, 1], axes[1, 0], axes[1, 1]),
            ("mu", "P", "h"), (r"$\partial F/\partial\mu$", r"$\partial F/\partial P$", r"$\partial F/\partial h$")):
        if parameter == "P":
            ax.plot([0, switch, 2.05], [0, 2 * switch, 4 * h / (length - b)], color="#5A6067", lw=1.3)
        else:
            left = 2 * P if parameter == "mu" else 0
            right = 0 if parameter == "mu" else 4 * P / (length - b)
            ax.plot([0, switch], [left, left], color="#5A6067", lw=1.3)
            ax.plot([switch, 2.05], [right, right], color="#5A6067", lw=1.3)
        for row in primary:
            mu = _number(row["assembly"]["mu"])
            answer = row["sensitivity"]["parameters"][parameter]
            for side in ("left", "right"):
                value = answer[side + "_derivative"]
                source.append(dict(panel=panel, case_id=row["case_id"], quantity="dF/d" + parameter,
                    x=row["assembly"]["mu"], exact_value=value, side=side, status=answer["differentiability"], N=3,
                    P=ref["pressure"], h=ref["h"], L=ref["L"], b=ref["b"]))
            if answer["differentiability"] == "singular":
                assert answer["left_derivative"] is None and answer["right_derivative"] is None
                continue
            left, right = _number(answer["left_derivative"]), _number(answer["right_derivative"])
            if left == right:
                ax.plot(mu, right, "o", color=COLORS[0], ms=4, zorder=4)
            else:
                ax.plot(mu, left, "<", mfc="white", mec=COLORS[0], ms=6, zorder=5)
                ax.plot(mu, right, ">", mfc=COLORS[0], mec=COLORS[0], ms=6, zorder=5)
                if parameter == "h":
                    ax.annotate(r"$h^-: 2$", (mu, left), xytext=(mu + .16, left + .13),
                                fontsize=7, color=COLORS[0])
                    ax.annotate(r"$h^+: 0$", (mu, right), xytext=(mu + .16, right + .15),
                                fontsize=7, color=COLORS[0])
        ax.axvline(switch, color="#BBBFC5", lw=.7, ls=":", zorder=0)
        ax.set(xlabel=r"Friction coefficient $\mu$", ylabel=ylabel, xlim=(-.05, 2.08), ylim=(-.12, 2.3))
    for panel, ax in zip("abcd", axes.flat):
        ax.text(-.16, 1.06, panel, transform=ax.transAxes, fontsize=10, weight="bold")
        ax.tick_params(direction="out", length=3)
    fig.suptitle("TIA-G5: finite capacity and exact sensitivity", fontsize=11, y=.98)
    handles = [Line2D([], [], color="#5A6067", label="Closed-form reference"),
               Line2D([], [], color=COLORS[0], marker="o", ls="", label="Exact LP / sensitivity"),
               Line2D([], [], color=COLORS[0], marker="<", mfc="white", ls="", label="Left derivative"),
               Line2D([], [], color=COLORS[0], marker=">", ls="", label="Right derivative")]
    fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(.53, .945), ncol=4, fontsize=6.5, handlelength=1.4, columnspacing=1.1)
    fig.text(.5, .045, r"b–d: N = 3, h = P = 1.  At $\mu=0$: singular contract; no certified slope is plotted.", ha="center", fontsize=7)
    fig.text(.5, .015, "profile1 / associated flow / no gravity / diagnostic data, not a C++ performance set", ha="center", fontsize=6.5, color="#666666")
    return _save(fig, "g5_capacity_sensitivity"), source


def _morphology(rows):
    fig, axes = plt.subplots(3, 3, figsize=(7.2, 6.3))
    fig.subplots_adjust(left=.14, right=.99, bottom=.13, top=.88, wspace=.24, hspace=.40)
    amplitudes = ("0/1", "1/16", "1/8", "1/4")
    wavelengths = ("1/2", "1/1", "2/1")
    source = []
    palette = ListedColormap(["#F0F2F4", "#B2CDE1", "#77A5C5", "#3976A8"])
    for i, (family, segments) in enumerate(zip(("TIA-G2", "TIA-G3", "TIA-G4"), (2, 8, 8))):
        selected = { (r["amplitude"], r["wavelength"]): r for r in rows if r["family"] == family }
        assert len(selected) == 12
        grids = [[], [], []]
        for wavelength in wavelengths:
            lines = [[], [], []]
            for amplitude in amplitudes:
                row = selected[(amplitude, wavelength)]
                assert row["contact_status"] == "RESOLVED" and row["declared_segment_count"] == segments
                assert all(s in ("ZERO_CONE", "NONZERO_CONE") for s in row["first_order_single"])
                first = sum(s == "ZERO_CONE" for s in row["first_order_single"])
                lock = sum(s == "TRANSLATION_IMMOBILE" for s in row["lock_refinements"])
                threshold = _number(row["exact_threshold"])
                assert threshold is not None and row["attained"] in (True, False)
                for line, value in zip(lines, (first, lock, threshold)):
                    line.append(value)
                source.append(dict(case_id=row["case_id"], family=family, amplitude=amplitude, wavelength=wavelength,
                    segments=segments, first_order_zero_count=first, translation_immobile_count=lock,
                    exact_threshold=row["exact_threshold"], attained=row["attained"],
                    derivative_status=row["derivative_status"], derivative=row["derivative"]))
            for grid, line in zip(grids, lines):
                grid.append(line)
        for j, (ax, grid) in enumerate(zip(axes[i], grids)):
            if j < 2:
                ax.imshow(grid, cmap=palette, vmin=0, vmax=3, aspect="auto", origin="lower")
            else:
                # The actual scan is constant zero: no invented color trend.
                assert all(v == 0 for row in grid for v in row)
                ax.imshow(grid, cmap=ListedColormap(["#F0F2F4"]), vmin=0, vmax=1, aspect="auto", origin="lower")
            for y, wavelength in enumerate(wavelengths):
                for x, amplitude in enumerate(amplitudes):
                    value = grid[y][x]
                    label = str(value) if j < 2 else "0\n" + ("closed" if selected[(amplitude, wavelength)]["attained"] else "open")
                    ax.text(x, y, label, ha="center", va="center", fontsize=6.8,
                            color="white" if j < 2 and value == 3 else "#30343B")
            ax.add_patch(Rectangle((-.5, -.5), 1, 3, fill=False, hatch="//", edgecolor="#AAAAAA", lw=.5))
            ax.set_xticks(range(4), ("0", "1/16", "1/8", "1/4"), fontsize=6.5)
            ax.set_yticks(range(3), ("1/2", "1", "2"), fontsize=6.5)
            ax.set_xlabel("Amplitude A", fontsize=7)
            if j == 0:
                ax.set_ylabel(f"{family} ({segments} segments)\nBlock height $\\lambda$ (one profile)", fontsize=7)
            else:
                ax.set_ylabel(r"Block height $\lambda$", fontsize=7)
            ax.tick_params(length=0)
            ax.text(-.12, 1.07, chr(97 + 3 * i + j), transform=ax.transAxes, fontsize=9, weight="bold")
    for ax, title in zip(axes[0], ("Single-body zero cones\n(count / 3 bodies)", "Translation immobility\n(count / 3 bodies)", "Certified friction threshold\n$\\mu_{crit}$ and attainment")):
        ax.set_title(title, fontsize=8, pad=16)
    fig.suptitle("TIA-G2–G4: degenerate same-phase polygon grid", fontsize=11, y=.985)
    fig.text(.5, .064, "Hatched A = 0: skeleton change. All thresholds are zero; no shape-design trend is established.", ha="center", fontsize=6.7)
    fig.text(.5, .033, "2 / 8 / 8-segment polygons only: circular-grid refinement can retain false smooth-interface locking.", ha="center", fontsize=6.4)
    fig.text(.5, .008, "Associated-flow positive thresholds are unsafe-side lower bounds; no smooth-curve convergence is certified.", ha="center", fontsize=6.3, color="#555555")
    return _save(fig, "g2_g4_design_grid"), source


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-only", action="store_true", help="verify saved source rows and artifact hashes without rendering")
    args = parser.parse_args()
    assert (OUT / "figure_contract.md").exists(), "write the figure contract first"
    status = _read(MORPH / "run_status.json")
    assert status["valid"] is True and status["state"] == "complete" and status["cases"] == 36
    for entry in _read(MORPH / "manifest.json"):
        assert _hash(MORPH / entry["path"]) == entry["sha256"]
    if args.check_only:
        source, qa = _read(OUT / "source_data.json"), _read(OUT / "qa.json")
        lookup = {row["case_id"]: row for row in _read(P0)["cases"]}
        for point in source["g5"]:
            case = lookup[point["case_id"]]
            if point["quantity"] == "F/P":
                expected = _rational(Fraction(case["limit"]["value"]) / Fraction(case["reference"]["pressure"]))
            else:
                answer = case["sensitivity"]["parameters"][point["quantity"][4:]]
                expected = answer[point["side"] + "_derivative"]
                if Fraction(point["x"]) == 0:
                    assert point["status"] == "singular" and expected is None
            assert point["exact_value"] == expected
        for point in source["morphology"]:
            case = _read(MORPH / (point["case_id"] + ".json"))
            assert point["first_order_zero_count"] == sum(x["result"]["cone_is_zero"] is True for x in case["first_order_single"])
            assert point["translation_immobile_count"] == sum(x["result"]["refinement"] == "TRANSLATION_IMMOBILE" for x in case["lock"])
            assert point["exact_threshold"] == case["critical"]["exact_threshold"]
            assert point["attained"] is case["critical"]["attained"]
        assert len(source["g5"]) == 36 and len(source["morphology"]) == 36
        for name, digest in source["input_sha256"].items():
            assert _hash(ROOT / name) == digest
        for item in qa["figures"]:
            path = OUT / item["path"]
            assert path.stat().st_size == item["bytes"] < 1_000_000 and _hash(path) == item["sha256"]
        assert qa["editable_svg_text"] and qa["solver_runs"] == 0
        print("figure semantic gate: 36 G5 source rows + 36 morphology cases + 6 artifact hashes verified; 0 solver runs")
        return
    input_paths = (P0, MORPH / "summary.json", MORPH / "run_status.json", MORPH / "manifest.json")
    hashes = {p.relative_to(ROOT).as_posix(): _hash(p) for p in input_paths}
    plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Arial", "DejaVu Sans"],
        "font.size": 8, "axes.titlesize": 9, "axes.labelsize": 8, "xtick.labelsize": 7, "ytick.labelsize": 7,
        "svg.fonttype": "none", "pdf.fonttype": 42, "axes.spines.top": False, "axes.spines.right": False,
        "axes.linewidth": .7, "legend.frameon": False})
    g5_files, g5_source = _g5(_read(P0)["cases"])
    morph_files, morph_source = _morphology(_read(MORPH / "summary.json"))
    for filename, rows in (("g5_source_data.csv", g5_source), ("g2_g4_source_data.csv", morph_source)):
        with (OUT / filename).open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    assert hashes == {p.relative_to(ROOT).as_posix(): _hash(p) for p in input_paths}
    source = dict(format="tia2d.figure-source.v1", formal_case_export=False, solver_runs=0,
        input_sha256=hashes, script_sha256=_hash(Path(__file__)), g5=g5_source, morphology=morph_source)
    (OUT / "source_data.json").write_text(json.dumps(source, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
    qa = dict(status="awaiting_visual_inspection", backend="Python/matplotlib", matplotlib_version=matplotlib.__version__,
        solver_runs=0, inputs_unchanged=True, g5_source_rows=len(g5_source), morphology_cases=len(morph_source),
        editable_svg_text=all("<text" in (OUT / item["path"]).read_text(encoding="utf-8") for item in g5_files + morph_files if item["path"].endswith(".svg")),
        figures=g5_files + morph_files, statistical_uncertainty="not_applicable_deterministic_exact_cases")
    (OUT / "qa.json").write_text(json.dumps(qa, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print("figures rendered from saved inputs only: 2 figures, 6 exports; all < 1 MB")


if __name__ == "__main__":
    main()
