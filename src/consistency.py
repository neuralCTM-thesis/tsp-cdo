"""
consistency.py - prove that the graph, the table, the code input and the reported
results all come from the SAME data (PIT: "ensure that the graph, data, Python
inputs, and reported results are consistent").

    python main.py --check-consistency

Every output carries the data fingerprint (a hash of the three CSV files). This
check recomputes the fingerprint and the key numbers from the CSVs and compares
them with every figure, table, map and document in outputs/ and docs/.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

from PIL import Image

from src import config
from src.baselines import brute_force
from src.data_loader import distance_matrix, validate_dataset
from src.graph_model import tour_cost

OUT, DOCS = config.OUTPUT_DIR, config.DOCS_DIR


def _png_fingerprint(path: Path) -> str | None:
    text = Image.open(path).info.get("Description", "")
    return text.split("=", 1)[1] if text.startswith("fingerprint=") else None


def _gif_fingerprint(path: Path) -> str | None:
    comment = Image.open(path).info.get("comment", b"").decode(errors="ignore")
    return comment.split("=", 1)[1] if comment.startswith("fingerprint=") else None


REAL_DATA_CHECK = "real data (not the placeholder dataset)"


def _report(results: list[tuple[bool, str]]) -> bool:
    print("\nCONSISTENCY CHECK")
    print("=" * 78)
    for ok, msg in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {msg}")
    failed = [msg for ok, msg in results if not ok]
    print("=" * 78)
    if not failed:
        print("ALL CONSISTENT - ready to record")
    elif failed == [REAL_DATA_CHECK]:
        print("CONSISTENT, but built from PLACEHOLDER data - not ready to record")
    else:
        print("INCONSISTENT - rerun `python main.py` (and `--experiments`) with the current data")
    return not failed


def run_consistency_check(force_placeholder: bool = False) -> bool:
    from main import select_dataset  # same data-selection rule as the main program
    ds = select_dataset(force_placeholder)
    rep = validate_dataset(ds)
    results: list[tuple[bool, str]] = [(rep.ok, f"data in {ds.data_dir.name}/ is valid")]
    if not rep.ok:
        return _report(results)
    fp, D = ds.fingerprint, distance_matrix(ds)
    results.append((not ds.is_placeholder, REAL_DATA_CHECK))

    summary_path = OUT / "results_summary.json"
    if not summary_path.exists():
        results.append((False, "outputs/results_summary.json exists"))
        return _report(results)
    s = json.loads(summary_path.read_text(encoding="utf-8"))
    results.append((s["fingerprint"] == fp, f"results_summary.json fingerprint {s['fingerprint']}"
                                            f" == data fingerprint {fp}"))
    results.append((s["matrix"] == D, "matrix used by the code == data/distance_matrix.csv"))
    route = s["sa"]["route"]
    recomputed = tour_cost(route[:-1], D)
    results.append((math.isclose(recomputed, s["sa"]["cost"], abs_tol=config.FLOAT_TOL),
                    f"reported SA total {s['sa']['cost']:.4f} km == route recomputed from CSV "
                    f"{recomputed:.4f} km"))
    edges_ok = all(math.isclose(e["km"], D[e["from_id"]][e["to_id"]])
                   for e in s["verification"]["edges"])
    results.append((edges_ok, "every km in the verification table == the matrix entry"))
    optimum = brute_force(D).optimal_cost
    results.append((math.isclose(optimum, s["brute_force"]["optimal_cost"]),
                    f"brute-force optimum recomputed now ({optimum:g} km) == reported"))

    for png in sorted(OUT.glob("fig*.png")):
        got = _png_fingerprint(png)
        results.append((got == fp, f"{png.name} fingerprint {got}"))
    gif = OUT / "fig6_sa_animation.gif"
    if gif.exists():
        results.append((_gif_fingerprint(gif) == fp, f"{gif.name} fingerprint {_gif_fingerprint(gif)}"))
    html = OUT / "route_map.html"
    if html.exists():
        results.append((fp in html.read_text(encoding="utf-8"), "route_map.html carries the fingerprint"))
    for csv_file in sorted(OUT.glob("*.csv")):
        last = csv_file.read_text(encoding="utf-8").strip().splitlines()[-1]
        results.append((fp in last, f"{csv_file.name} carries the fingerprint"))
    exp = OUT / "experiments.json"
    if exp.exists():
        efp = json.loads(exp.read_text(encoding="utf-8"))["fingerprint"]
        results.append((efp == fp, f"experiments.json fingerprint {efp}"))
    else:
        results.append((False, "experiments.json exists (run `python main.py --experiments`)"))
    docs = [DOCS / f"{d}.md" for d in ("slides_outline", "narration_script", "demo_checklist",
                                        "results_tables")] + [config.PROJECT_ROOT / "REFERENCES.md"]
    for path in docs:
        ok = path.exists() and f"`{fp}`" in path.read_text(encoding="utf-8")
        results.append((ok, f"{path.relative_to(config.PROJECT_ROOT)} generated from this data"))
    return _report(results)
