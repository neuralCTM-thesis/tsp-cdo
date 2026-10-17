"""
report.py - everything printed to the console and every table written to outputs/.

Console text is kept under ~100 characters wide so it stays readable in a
screen recording. Every exported file carries the data fingerprint.
"""
from __future__ import annotations

import csv
import json
import math
from datetime import datetime
from pathlib import Path

from src import config
from src.data_loader import Dataset, ValidationReport
from src.graph_model import route_labels, route_names

ARROW = " → "


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------
def fmt_km(x: float) -> str:
    """41.2 -> '41.2', 41.25 -> '41.25', 41.0 -> '41.0' (at most 2 decimals = 10 m)."""
    s = f"{x:.2f}"
    return s[:-1] if s.endswith("0") else s


def format_table(headers: list[str], rows: list[list], align: str | None = None) -> str:
    """Plain-text table. ``align`` is one char per column: 'l' or 'r'."""
    cells = [[str(c) for c in headers]] + [[str(c) for c in row] for row in rows]
    widths = [max(len(r[k]) for r in cells) for k in range(len(headers))]
    align = align or "l" * len(headers)

    def line(row: list[str]) -> str:
        return "  ".join(c.rjust(w) if a == "r" else c.ljust(w)
                         for c, w, a in zip(row, widths, align)).rstrip()

    rule = "  ".join("-" * w for w in widths)
    return "\n".join([line(cells[0]), rule] + [line(r) for r in cells[1:]])


def section(title: str) -> None:
    print("\n" + "=" * 78)
    print(f" {title}")
    print("=" * 78)


def placeholder_banner() -> str:
    bar = "!" * 78
    return (f"\n{bar}\n!!  PLACEHOLDER DATA IN USE - these are NOT real road distances.{'':12}!!\n"
            f"!!  Fill in data/*.csv (see docs/data_collection_guide.md) before you record.  !!\n"
            f"!!  Every figure is watermarked 'PLACEHOLDER DATA' while this is the case.  {'':1}!!\n"
            f"{bar}\n")


def pretty_route(route: list[int], ds: Dataset) -> str:
    return route_labels(route, ds).replace(" -> ", ARROW)


# ---------------------------------------------------------------------------
# Console sections
# ---------------------------------------------------------------------------
def print_validation(rep: ValidationReport, ds: Dataset) -> None:
    section("DATA VALIDATION")
    print(f"Data folder      : {ds.data_dir}")
    print(f"Data fingerprint : {ds.fingerprint}   (stamped on every output file)")
    print(f"Vertices         : {ds.n}  (1 depot + {ds.n - 1} hospitals)")
    print(f"Directed arcs    : {ds.n * (ds.n - 1)}  (n(n-1), complete digraph)")
    counts = ", ".join(f"{k}={v}" for k, v in sorted(rep.status_counts.items())) or "-"
    print(f"Edge provenance  : {counts}")
    if rep.ok:
        print(f"Asymmetric pairs : {len(rep.asymmetric_pairs)} of {ds.n * (ds.n - 1) // 2} "
              f"(d(i,j) != d(j,i), e.g. one-way streets)")
    for msg in rep.errors:
        print(f"  ERROR   {msg}")
    for msg in rep.warnings:
        print(f"  WARNING {msg}")
    print("Result           : " + ("PASS - data is valid" if rep.ok else
                                    f"FAIL - {len(rep.errors)} error(s)"))


def print_inputs(ds: Dataset, D: list[list[float]]) -> None:
    section("INPUT 1 - VERTICES (data/locations.csv)")
    rows = [[loc.label, loc.short_name, loc.role, f"{loc.latitude:.5f}", f"{loc.longitude:.5f}"]
            for loc in ds.locations]
    print(format_table(["Vertex", "Location", "Role", "Latitude", "Longitude"], rows, "lllrr"))
    section("INPUT 2 - DIRECTED DISTANCE MATRIX in km (row = FROM, column = TO)")
    header = ["from\\to"] + ds.labels
    body = []
    for i in range(ds.n):
        cells = []
        for j in range(ds.n):
            mark = "*" if ds.edge_status(i, j) == "ASSUMED" else ""
            cells.append("-" if i == j else fmt_km(D[i][j]) + mark)
        body.append([ds.labels[i]] + cells)
    print(format_table(header, body, "l" + "r" * ds.n))
    print(f"  * = ASSUMED value (not measured); all others ACTUAL ({ds.source_label})"
          if not ds.is_placeholder else "  (all values are PLACEHOLDER)")


def print_params(params: config.SAParams, neighbor: str, seed: int, mean_uphill: float | None,
                 runs: int) -> None:
    section("SIMULATED ANNEALING PARAMETERS (src/config.py)")
    rows = [
        ["T0 (initial temperature)", f"{params.t0:g} km",
         f"auto: P(accept avg worse move of {mean_uphill:.2f} km) = "
         f"{params.target_initial_acceptance}" if mean_uphill else "fixed"],
        ["alpha (cooling rate)", f"{params.alpha}", "T <- alpha * T after each level"],
        ["moves per temperature", f"{params.iterations_per_temperature}", "inner loop"],
        ["T_stop", f"{params.t_stop:g} km", "stop when T <= T_stop"],
        ["patience", "off" if params.patience_levels is None else
         f"{params.patience_levels} levels", f"stop if no new best while T falls "
                                             f"{params.patience_drop_factor:g}x"
         if params.patience_drop_factor else "rule switched off"],
        ["max total moves", f"{params.max_total_iterations:,}", "safety cap"],
        ["neighbour move", neighbor, "swap = paper; 2opt = our extension"],
        ["random seed", f"{seed}", f"multi-run statistics use seeds "
                                    f"{config.FIRST_RUN_SEED}..{config.FIRST_RUN_SEED + runs - 1}"],
    ]
    print(format_table(["Parameter", "Value", "Meaning"], rows))


def _describe_move(step, ds: Dataset, neighbor: str) -> str:
    i, j = sorted(step.positions)
    a, b = ds.labels[step.current_tour[i]], ds.labels[step.current_tour[j]]
    if neighbor == "swap":
        return f"swap positions {i} and {j}  ({a} <-> {b})"
    return f"reverse positions {i}..{j}  ({a} ... {b})"


def format_trace_step(step, ds: Dataset, neighbor: str) -> str:
    """Every number of one move, written like a hand calculation."""
    cur, new = step.current_tour + [0], step.new_tour + [0]
    lines = [
        f"--- Move {step.iteration}  (level {step.level}, T = {step.temperature:.4f} km) ---",
        f"  current tour : {pretty_route(cur, ds)}  = {fmt_km(step.current_cost)} km",
        f"  proposed move: {_describe_move(step, ds, neighbor)}",
        f"  new tour     : {pretty_route(new, ds)}  = {fmt_km(step.new_cost)} km",
        f"  Δ = {fmt_km(step.new_cost)} - {fmt_km(step.current_cost)} = {step.delta:+.2f} km",
    ]
    if step.delta < 0:
        lines.append("  Δ < 0 → new tour is SHORTER → ACCEPT (Alg 2.5 steps 6-7, no random number)")
        return "\n".join(lines)
    lines.append(f"  P = e^(-Δ/T) = e^(-{step.delta:.2f}/{step.temperature:.4f}) = "
                 f"{step.probability:.4f}   (Alg 2.5 step 9)")
    verdict = "r < P → ACCEPT the worse tour" if step.accepted else "r ≥ P → REJECT (keep current)"
    lines.append(f"  r = {step.r:.4f}  →  {verdict}")
    return "\n".join(lines)


def print_trace(trace, ds: Dataset, neighbor: str) -> None:
    section(f"TRACE - the first {len(trace)} moves in full (also in outputs/trace.csv)")
    for step in trace:
        print(format_trace_step(step, ds, neighbor))


def print_sa_result(res, ds: Dataset) -> None:
    section("SIMULATED ANNEALING RESULT")
    print(f"Initial random tour : {pretty_route(res.initial_tour + [0], ds)}  "
          f"= {fmt_km(res.initial_cost)} km")
    print(f"Best tour found     : {pretty_route(res.route, ds)}")
    print(f"                      {route_names(res.route, ds).replace(' -> ', ARROW)}")
    print(f"TOTAL DISTANCE      : {fmt_km(res.best_cost)} km")
    print(f"Moves evaluated     : {res.iterations:,} over {res.levels} temperature levels "
          f"(best first found at move {res.best_found_at:,})")
    print(f"Stopped because     : {res.stop_reason}")
    print(f"Runtime             : {res.runtime_s:.3f} s")


def print_verification(vr, ds: Dataset) -> None:
    section("VERIFICATION - route rules and an edge-by-edge recount (src/verify.py)")
    for c in vr.checks:
        print(f"  [{'PASS' if c.passed else 'FAIL'}] {c.name:<26} {c.detail}")
    rows = [[e.step, f"{ds.labels[e.from_id]} {ds.display_name(e.from_id)}",
             f"{ds.labels[e.to_id]} {ds.display_name(e.to_id)}", fmt_km(e.km),
             fmt_km(e.cumulative_km), e.status] for e in vr.edges]
    print()
    print(format_table(["#", "From", "To", "km", "Running km", "Data"], rows, "rllrrl"))
    print(f"\n  {'Recomputed sum of the ' + str(len(vr.edges)) + ' edges':<34} = "
          f"{fmt_km(vr.recomputed_km)} km")
    print(f"  {'Total reported by SA':<34} = {fmt_km(vr.reported_km)} km")
    print(f"  [{'PASS' if vr.total_matches else 'FAIL'}] totals are equal")


def print_comparison(sa_cost: float, bf, greedy, ds: Dataset) -> None:
    from src.baselines import gap_percent, is_optimal
    section("OPTIMALITY CHECK - brute force (Alg 2.3) and greedy (Alg 2.7) on the same matrix")
    rows = [
        ["Simulated Annealing (this run)", fmt_km(sa_cost), f"{gap_percent(sa_cost, bf.optimal_cost):.2f}%"],
        [f"Brute force: all {bf.tours_evaluated:,} tours", fmt_km(bf.optimal_cost), "0.00%"],
        ["Greedy nearest neighbour", fmt_km(greedy.cost),
         f"{gap_percent(greedy.cost, bf.optimal_cost):.2f}%"],
        ["Average random tour", fmt_km(bf.mean_cost),
         f"{gap_percent(bf.mean_cost, bf.optimal_cost):.2f}%"],
        ["Worst possible tour", fmt_km(bf.worst_cost),
         f"{gap_percent(bf.worst_cost, bf.optimal_cost):.2f}%"],
    ]
    print(format_table(["Method", "Total km", "Gap to optimum"], rows, "lrr"))
    print(f"\n  Brute force optimum: {pretty_route(bf.route, ds)}  ({bf.runtime_s:.2f} s)")
    if len(bf.optimal_tours) > 1:
        print(f"  Note: {len(bf.optimal_tours)} different tours tie for the optimum.")
    print(f"  Greedy route       : {pretty_route(greedy.route, ds)}")
    if is_optimal(sa_cost, bf.optimal_cost):
        print("\n  CONCLUSION: the SA route is OPTIMAL FOR THIS INSTANCE - proven by exhaustive")
        print("  search over every possible tour, not by SA itself (SA gives no guarantee).")
    else:
        print("\n  CONCLUSION: the SA route is an APPROXIMATE solution "
              f"({gap_percent(sa_cost, bf.optimal_cost):.2f}% above the proven optimum).")


def table2_rows(label: str, summary: dict) -> list[str]:
    return [label, fmt_km(summary["best"]), fmt_km(summary["worst"]), f"{summary['mean']:.3f}",
            f"{summary['variance']:.3f}", f"{summary['std']:.3f}",
            f"{summary['mean_runtime_s']:.4f} s", f"{summary['hit_rate_pct']:.0f}%"]


TABLE2_HEADERS = ["Algorithm", "Best", "Worst", "Average", "Variance", "Std Dev", "Avg time",
                  "Hit optimum"]


def print_run_statistics(summary: dict, optimum: float, greedy_cost: float, bf_time: float,
                         greedy_time: float) -> None:
    section(f"{summary['runs']} INDEPENDENT SA RUNS - same format as paper Table 2 (km)")
    rows = [table2_rows("SA (ours)", summary),
            ["Brute force", fmt_km(optimum), fmt_km(optimum), f"{optimum:.3f}", "0.000", "0.000",
             f"{bf_time:.4f} s", "100%"],
            ["Greedy", fmt_km(greedy_cost), fmt_km(greedy_cost), f"{greedy_cost:.3f}", "0.000",
             "0.000", f"{greedy_time:.4f} s",
             "100%" if abs(greedy_cost - optimum) <= config.FLOAT_TOL else "0%"]]
    print(format_table(TABLE2_HEADERS, rows, "lrrrrrrr"))
    print(f"\n  SA reached the proven optimum in {summary['hit_rate_pct']:.0f}% of runs; "
          f"mean gap {summary['mean_gap_pct']:.2f}%, worst gap {summary['max_gap_pct']:.2f}%.")
    print("  (Variance/Std Dev are sample statistics, n-1. Brute force and greedy are "
          "deterministic.)")


# ---------------------------------------------------------------------------
# CSV / JSON exports
# ---------------------------------------------------------------------------
def write_csv(path: Path, headers: list[str], rows: list[list], fingerprint: str) -> Path:
    """Write a CSV whose last line records the data fingerprint."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(headers)
        writer.writerows(rows)
        writer.writerow([f"# data fingerprint {fingerprint}"])
    return path


def export_trace(trace, ds: Dataset, out: Path) -> Path:
    rows = [[s.iteration, s.level, f"{s.temperature:.6f}", pretty_route(s.current_tour + [0], ds),
             fmt_km(s.current_cost), f"{s.positions[0]}-{s.positions[1]}",
             pretty_route(s.new_tour + [0], ds), fmt_km(s.new_cost), f"{s.delta:.4f}",
             f"{s.probability:.6f}", "" if s.r is None else f"{s.r:.6f}",
             "ACCEPT" if s.accepted else "REJECT"] for s in trace]
    return write_csv(out / "trace.csv",
                     ["move", "level", "T_km", "current_tour", "current_km", "positions",
                      "new_tour", "new_km", "delta_km", "P", "r", "decision"], rows, ds.fingerprint)


def export_history(hist, out: Path, fingerprint: str) -> Path:
    rows = zip(hist.iteration, hist.level, hist.temperature, hist.current_cost, hist.best_cost,
               hist.delta, hist.probability, hist.accepted)
    return write_csv(out / "sa_history.csv",
                     ["move", "level", "T_km", "current_km", "best_km", "delta_km", "P",
                      "accepted"],
                     [[a, b, f"{c:.6f}", f"{d:.4f}", f"{e:.4f}", f"{f:.4f}", f"{g:.6f}", int(h)]
                      for a, b, c, d, e, f, g, h in rows], fingerprint)


def export_verification(vr, ds: Dataset, out: Path) -> Path:
    rows = [[e.step, ds.labels[e.from_id], ds.locations[e.from_id].name, ds.labels[e.to_id],
             ds.locations[e.to_id].name, fmt_km(e.km), fmt_km(e.cumulative_km), e.status]
            for e in vr.edges]
    rows.append(["", "", "", "", "TOTAL (recomputed)", fmt_km(vr.recomputed_km), "", ""])
    rows.append(["", "", "", "", "TOTAL (reported by SA)", fmt_km(vr.reported_km), "", ""])
    return write_csv(out / "verification_table.csv",
                     ["step", "from", "from_name", "to", "to_name", "km", "running_km",
                      "data_status"], rows, ds.fingerprint)


def export_runs(records, out: Path, ds: Dataset, name: str = "sa_runs.csv") -> Path:
    rows = [[r.seed, fmt_km(r.cost), f"{r.gap_pct:.3f}", "yes" if r.hit_optimum else "no",
             f"{r.runtime_s:.5f}", r.iterations, r.levels, r.best_found_at, r.stop_reason,
             pretty_route(r.tour + [0], ds)] for r in records]
    return write_csv(out / name, ["seed", "best_km", "gap_pct", "hit_optimum", "runtime_s",
                                  "moves", "levels", "best_found_at_move", "stop_reason",
                                  "route"], rows, ds.fingerprint)


def export_table2(summary: dict, optimum: float, greedy, bf, out: Path, fp: str) -> Path:
    rows = [table2_rows("SA (ours)", summary),
            ["Brute force", fmt_km(optimum), fmt_km(optimum), f"{optimum:.3f}", "0.000", "0.000",
             f"{bf.runtime_s:.4f} s", "100%"],
            ["Greedy", fmt_km(greedy.cost), fmt_km(greedy.cost), f"{greedy.cost:.3f}", "0.000",
             "0.000", f"{greedy.runtime_s:.4f} s",
             "100%" if abs(greedy.cost - optimum) <= config.FLOAT_TOL else "0%"]]
    return write_csv(out / "table2_style_results.csv", TABLE2_HEADERS, rows, fp)


def export_vertices(ds: Dataset, out: Path) -> Path:
    rows = [[l.label, l.name, l.short_name, l.role, l.address, l.latitude, l.longitude,
             l.google_maps_url] for l in ds.locations]
    return write_csv(out / "table_vertices.csv", ["vertex", "name", "short_name", "role",
                                                  "address", "latitude", "longitude",
                                                  "google_maps_url"], rows, ds.fingerprint)


def export_data_quality(rep: ValidationReport, ds: Dataset, out: Path) -> Path:
    rows = [["asymmetric", f"{ds.labels[i]}<->{ds.labels[j]}", fmt_km(a), fmt_km(b),
             f"{a - b:+.2f}"] for i, j, a, b in rep.asymmetric_pairs]
    rows += [["assumed", f"{ds.labels[i]}->{ds.labels[j]}", fmt_km(ds.matrix[i][j]), "", ""]
             for i, j in rep.assumed_edges]
    rows += [["triangle", f"{ds.labels[i]}->{ds.labels[k]} via {ds.labels[j]}", fmt_km(dik),
              fmt_km(via), f"{dik - via:+.2f}"] for i, j, k, dik, via in rep.triangle_violations]
    return write_csv(out / "data_quality.csv",
                     ["type", "edge", "km (i->j or direct)", "km (j->i or via)", "difference"],
                     rows, ds.fingerprint)


def write_json(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=_json_default), encoding="utf-8")
    return path


def _json_default(obj):
    if isinstance(obj, float) and math.isnan(obj):
        return None
    if hasattr(obj, "__dict__"):
        return obj.__dict__
    return str(obj)


def timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")
