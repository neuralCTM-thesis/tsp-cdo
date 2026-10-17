"""
main.py - single entry point of the project.

Simulated Annealing (paper Algorithm 2.5) for an asymmetric TSP: a Philippine Red
Cross courier in Cagayan de Oro City delivers blood units to every hospital once
and returns to the chapter office, minimising total DRIVING distance (km).

Typical use
    python main.py                     full run (input -> SA -> verification -> stats -> figures)
    python main.py --trace             same, plus the first 5 SA moves printed in full
    python main.py --experiments       alpha sensitivity, swap vs 2-opt, paper defaults (~3 min)

Other options
    --seed N  --runs N  --neighbor swap|2opt  --placeholder  --no-figures
    --validate          check the CSV files only
    --prepare-sources   write one row per directed edge into data/data_sources.csv
    --build-matrix      build data/distance_matrix.csv from data/data_sources.csv
    --fetch-osm         fill coordinates + all directed distances from OpenStreetMap (OSRM)
    --find-demo-seed    suggest a seed whose trace shows every case of the acceptance rule
    --check-consistency confirm that every figure, table and doc comes from the current data
"""
from __future__ import annotations

import argparse
import sys
import time
from contextlib import contextmanager
from pathlib import Path

from src import config, report
from src.baselines import brute_force, gap_percent, greedy_nearest_neighbor, is_optimal
from src.data_loader import (Dataset, build_matrix_from_sources, distance_matrix,
                             is_unfilled_template, load_dataset, prepare_sources_template,
                             validate_dataset)
from src.experiments import (alpha_sensitivity, find_demo_seed, neighbor_comparison,
                             paper_defaults_run, run_many, summarize)
from src.graph_model import build_digraph, route_labels, route_names
from src.simulated_annealing import calibrate_initial_temperature, simulated_annealing
from src.verify import verify_solution

OUT = config.OUTPUT_DIR


# ---------------------------------------------------------------------------
# Step 1 - choose, load and validate the data
# ---------------------------------------------------------------------------
def select_dataset(force_placeholder: bool = False) -> Dataset:
    """Real data from data/ unless it is still an empty template (or --placeholder)."""
    if force_placeholder:
        ds = load_dataset(config.PLACEHOLDER_DIR)
    elif is_unfilled_template(config.DATA_DIR):
        print("\nNOTE: data/distance_matrix.csv has no distances yet -> using the "
              "PLACEHOLDER dataset in data/placeholder/.")
        ds = load_dataset(config.PLACEHOLDER_DIR)
    else:
        ds = load_dataset(config.DATA_DIR)
    if ds.is_placeholder:
        print(report.placeholder_banner())
    return ds


def load_and_validate(force_placeholder: bool = False):
    ds = select_dataset(force_placeholder)
    rep = validate_dataset(ds)
    report.print_validation(rep, ds)
    if not rep.ok:
        print("\nFix the errors above (or run with --placeholder). Stopping.")
        sys.exit(1)
    D = distance_matrix(ds)
    report.export_vertices(ds, OUT)
    report.export_data_quality(rep, ds, OUT)
    return ds, rep, D


# ---------------------------------------------------------------------------
# Step 2 - run SA once (the presentation run), verify, compare
# ---------------------------------------------------------------------------
def resolve_sa_params(D, neighbor: str):
    """Calibrate T0 from the data (if config says t0=None) and return (params, mean uphill)."""
    params, mean_uphill = config.SA_DEFAULTS, None
    if params.t0 is None:
        t0, mean_uphill = calibrate_initial_temperature(D, neighbor,
                                                        params.target_initial_acceptance)
        params = params.with_(t0=t0)
    return params, mean_uphill


def run_presentation(ds: Dataset, D, args) -> dict:
    params, mean_uphill = resolve_sa_params(D, args.neighbor)
    report.print_params(params, args.neighbor, args.seed, mean_uphill, args.runs)
    res = simulated_annealing(D, params, args.seed, args.neighbor, record_history=True,
                              trace_steps=config.TRACE_EXPORT_STEPS)
    if args.trace:
        report.print_trace(res.trace[:config.TRACE_PRINT_STEPS], ds, args.neighbor)
    report.export_trace(res.trace, ds, OUT)
    report.export_history(res.history, OUT, ds.fingerprint)
    report.print_sa_result(res, ds)

    G = build_digraph(ds, D)
    vr = verify_solution(res.route, res.best_cost, G)   # raises if anything is wrong
    report.print_verification(vr, ds)
    report.export_verification(vr, ds, OUT)

    bf, greedy = brute_force(D), greedy_nearest_neighbor(D)
    report.print_comparison(res.best_cost, bf, greedy, ds)
    return {"params": params, "mean_uphill": mean_uphill, "res": res, "G": G, "vr": vr,
            "bf": bf, "greedy": greedy}


# ---------------------------------------------------------------------------
# Step 3 - many runs (paper Table 2 format)
# ---------------------------------------------------------------------------
def run_statistics(ds: Dataset, D, ctx: dict, args) -> None:
    seeds = list(range(config.FIRST_RUN_SEED, config.FIRST_RUN_SEED + args.runs))
    records = run_many(D, ctx["params"], seeds, args.neighbor, ctx["bf"].optimal_cost)
    summary = summarize(records)
    report.print_run_statistics(summary, ctx["bf"].optimal_cost, ctx["greedy"].cost,
                                ctx["bf"].runtime_s, ctx["greedy"].runtime_s)
    report.export_runs(records, OUT, ds)
    report.export_table2(summary, ctx["bf"].optimal_cost, ctx["greedy"], ctx["bf"], OUT,
                         ds.fingerprint)
    ctx.update(records=records, summary=summary)


# ---------------------------------------------------------------------------
# Step 4 - figures and maps
# ---------------------------------------------------------------------------
def make_figures(ds: Dataset, D, ctx: dict) -> dict:
    from src import maps, visualize as viz
    viz.apply_style()
    res, bf, greedy = ctx["res"], ctx["bf"], ctx["greedy"]
    started = time.perf_counter()
    files = {
        "graph": viz.plot_graph(ctx["G"], ds, OUT / "fig1_graph.png"),
        "route_graph": viz.plot_route_graph(ctx["G"], ds, res.route, res.best_cost,
                                            OUT / "fig1b_route_on_graph.png"),
        "matrix": viz.plot_matrix(D, ds, OUT / "fig2_weight_matrix.png"),
        "map_html": maps.make_folium_map(ds, res.route, D, res.best_cost, OUT / "route_map.html"),
    }
    files["map_png"], used_tiles = maps.make_static_map(ds, res.route, D, res.best_cost,
                                                        OUT / "fig3_route_map.png")
    files.update({
        "convergence": viz.plot_convergence(res.history, bf.optimal_cost, ds,
                                            OUT / "fig4_convergence.png"),
        "acceptance": viz.plot_acceptance(res.history, ds, OUT / "fig5_acceptance.png"),
        "gif": viz.make_gif(res.history, ds, OUT / "fig6_sa_animation.gif"),
        "runs": viz.plot_runs(ctx["records"], bf.optimal_cost, greedy.cost, ds,
                              OUT / "fig7_runs_vs_optimum.png"),
        "search_space": viz.plot_search_space(bf.all_costs, bf.optimal_cost, res.best_cost,
                                              greedy.cost, bf.mean_cost, ds,
                                              OUT / "fig8_search_space.png"),
    })
    url = maps.route_directions_url(ds, res.route)
    (OUT / "route_google_maps_url.txt").write_text(url + "\n", encoding="utf-8")
    report.section(f"FIGURES written to {OUT} ({time.perf_counter() - started:.1f} s)")
    for path in files.values():
        print(f"  {Path(path).name}")
    print(f"\n  Open the whole route in Google Maps (for viewing):\n  {url}")
    ctx.update(figures={k: Path(v).name for k, v in files.items()}, used_tiles=used_tiles,
               gmaps_url=url)
    return files


# ---------------------------------------------------------------------------
# Step 5 - machine-readable summary (feeds docs/ and the consistency check)
# ---------------------------------------------------------------------------
def build_summary(ds: Dataset, rep, D, ctx: dict, args) -> dict:
    res, bf, greedy, vr, params = ctx["res"], ctx["bf"], ctx["greedy"], ctx["vr"], ctx["params"]
    return {
        "fingerprint": ds.fingerprint, "is_placeholder": ds.is_placeholder,
        "data_dir": str(ds.data_dir.relative_to(config.PROJECT_ROOT)),
        "generated_at": report.timestamp(), "n": ds.n, "n_hospitals": ds.n - 1,
        "n_arcs": ds.n * (ds.n - 1), "n_tours": bf.tours_evaluated,
        "locations": [vars(l) for l in ds.locations],
        "matrix": D,
        "edge_status": [[ds.edge_status(i, j) if i != j else "" for j in range(ds.n)]
                        for i in range(ds.n)],
        "measurement": measurement_info(ds),
        "status_counts": rep.status_counts, "asymmetric_pairs": len(rep.asymmetric_pairs),
        "assumed_edges": len(rep.assumed_edges),
        "triangle_violations": len(rep.triangle_violations),
        "params": vars(params), "mean_uphill_km": ctx["mean_uphill"], "seed": args.seed,
        "neighbor": args.neighbor, "runs": args.runs,
        "sa": {"route": res.route, "route_labels": route_labels(res.route, ds),
               "route_names": route_names(res.route, ds), "cost": res.best_cost,
               "initial_route_labels": route_labels(res.initial_tour + [0], ds),
               "initial_cost": res.initial_cost, "iterations": res.iterations,
               "levels": res.levels, "best_found_at": res.best_found_at,
               "stop_reason": res.stop_reason, "runtime_s": res.runtime_s,
               "is_optimal": is_optimal(res.best_cost, bf.optimal_cost),
               "gap_pct": gap_percent(res.best_cost, bf.optimal_cost)},
        "verification": {"checks": [vars(c) for c in vr.checks],
                         "edges": [vars(e) for e in vr.edges],
                         "recomputed_km": vr.recomputed_km, "reported_km": vr.reported_km,
                         "passed": vr.passed},
        "brute_force": {"optimal_cost": bf.optimal_cost, "n_optimal_tours": len(bf.optimal_tours),
                        "optimal_routes": [route_labels(t + [0], ds) for t in bf.optimal_tours],
                        "worst_cost": bf.worst_cost, "mean_cost": bf.mean_cost,
                        "tours_evaluated": bf.tours_evaluated, "runtime_s": bf.runtime_s},
        "greedy": {"route_labels": route_labels(greedy.route, ds), "cost": greedy.cost,
                   "gap_pct": gap_percent(greedy.cost, bf.optimal_cost),
                   "runtime_s": greedy.runtime_s},
        "run_summary": ctx["summary"],
        "runs_detail": [vars(r) for r in ctx["records"]],
        "trace": [vars(s) for s in res.trace[:config.TRACE_PRINT_STEPS]],
        "figures": ctx.get("figures", {}), "used_basemap_tiles": ctx.get("used_tiles"),
        "google_maps_route_url": ctx.get("gmaps_url", ""),
    }


def measurement_info(ds: Dataset) -> dict:
    """Where and when the distances and coordinates were obtained (slides, REFERENCES)."""
    actual = [s for s in ds.sources.values() if s.status == "ACTUAL"]
    dates = sorted({s.measured_date for s in actual if s.measured_date})
    times = sorted({s.measured_time for s in actual if s.measured_time})
    notes = [loc.notes for loc in ds.locations]
    from_osm = sum("OpenStreetMap" in note for note in notes)
    return {"dates": dates, "first_time": times[0] if times else "",
            "last_time": times[-1] if times else "", "source_label": ds.source_label,
            "sources": sorted({s.source for s in ds.sources.values() if s.source}),
            "coords_from_osm": from_osm, "coords_total": len(notes)}


# ---------------------------------------------------------------------------
# Optional experiments
# ---------------------------------------------------------------------------
def run_experiments(ds: Dataset, D, args) -> dict:
    from src import visualize as viz
    report.section("EXPERIMENTS (same distance matrix; this takes 2-3 minutes)")
    bf = brute_force(D)
    seeds = list(range(config.FIRST_RUN_SEED, config.FIRST_RUN_SEED + config.SENSITIVITY_RUNS))
    alphas = alpha_sensitivity(D, config.SA_DEFAULTS, config.ALPHA_VALUES, seeds, "swap",
                               bf.optimal_cost)
    rows = [[r["alpha"], r["t0"], r["planned_levels"], r["patience_levels"],
             f"{r['mean_iterations']:,.0f}", report.fmt_km(r["best"]), report.fmt_km(r["worst"]), f"{r['mean']:.3f}",
             f"{r['std']:.3f}", f"{r['hit_rate_pct']:.0f}%", f"{1000 * r['mean_runtime_s']:.1f}"]
            for r in alphas]
    headers = ["alpha", "T0", "max levels", "patience", "moves", "best", "worst", "mean", "std",
               "hit opt", "ms/run"]
    print("\nAlpha sensitivity (only alpha changes; same seeds, T0, moves per level, T_stop):")
    print(report.format_table(headers, rows, "r" * len(headers)))
    report.write_csv(OUT / "alpha_sensitivity.csv", headers, rows, ds.fingerprint)

    neigh = neighbor_comparison(D, config.SA_DEFAULTS, seeds, bf.optimal_cost)
    rows = [[r["neighbor"], r["t0"], f"{r['mean_iterations']:,.0f}", report.fmt_km(r["best"]),
             report.fmt_km(r["worst"]), f"{r['mean']:.3f}", f"{r['std']:.3f}",
             f"{r['hit_rate_pct']:.0f}%", f"{1000 * r['mean_runtime_s']:.1f}"] for r in neigh]
    headers = ["neighbour", "T0", "moves", "best", "worst", "mean", "std", "hit opt", "ms/run"]
    print("\nNeighbour move: swap (paper) vs segment reversal (our extension):")
    print(report.format_table(headers, rows, "l" + "r" * (len(headers) - 1)))
    report.write_csv(OUT / "neighbor_comparison.csv", headers, rows, ds.fingerprint)

    print("\nOne run with the paper's Appendix 4.5 defaults (T0=1000, alpha=0.995, "
          "1000 moves/level, T_stop=1e-8) ...")
    paper = paper_defaults_run(D, args.seed, bf.optimal_cost)
    print(f"  {paper['iterations']:,} moves, {paper['levels']:,} levels, "
          f"{paper['runtime_s']:.1f} s -> {report.fmt_km(paper['cost'])} km "
          f"({'optimal' if paper['hit_optimum'] else 'not optimal'})")
    report.write_csv(OUT / "paper_defaults_run.csv", list(paper), [list(paper.values())],
                     ds.fingerprint)
    viz.apply_style()
    viz.plot_parameter_study(alphas, "alpha", "cooling rate α",
                             f"Cooling-rate sensitivity ({len(seeds)} runs per value)", ds,
                             OUT / "fig9_alpha_sensitivity.png")
    viz.plot_parameter_study(neigh, "neighbor", "neighbour move",
                             f"Swap (paper) vs segment reversal ({len(seeds)} runs each)", ds,
                             OUT / "fig10_neighbor_comparison.png")
    payload = {"fingerprint": ds.fingerprint, "generated_at": report.timestamp(),
               "alpha_sensitivity": alphas, "neighbor_comparison": neigh, "paper_defaults": paper,
               "optimum": bf.optimal_cost, "runs_per_setting": len(seeds)}
    report.write_json(OUT / "experiments.json", payload)
    return payload


# ---------------------------------------------------------------------------
# Command line
# ---------------------------------------------------------------------------
def parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Simulated Annealing for the CDO blood-delivery TSP")
    p.add_argument("--seed", type=int, default=config.DEFAULT_SEED, help="seed of the main run")
    p.add_argument("--runs", type=int, default=config.DEFAULT_RUNS, help="independent SA runs")
    p.add_argument("--trace", action="store_true", help="print the first SA moves in full")
    p.add_argument("--placeholder", action="store_true", help="force the placeholder dataset")
    p.add_argument("--neighbor", choices=sorted(("swap", "2opt")), default=config.NEIGHBOR_DEFAULT)
    p.add_argument("--no-figures", action="store_true", help="skip figures and maps")
    p.add_argument("--experiments", action="store_true", help="parameter / neighbour studies")
    p.add_argument("--validate", action="store_true", help="validate the CSV files only")
    p.add_argument("--prepare-sources", action="store_true", help="fill data_sources.csv rows")
    p.add_argument("--build-matrix", action="store_true", help="matrix from data_sources.csv")
    p.add_argument("--fetch-osm", action="store_true",
                   help="coordinates + directed distances from OpenStreetMap (OSRM)")
    p.add_argument("--find-demo-seed", action="store_true", help="suggest a seed for the video")
    p.add_argument("--check-consistency", action="store_true", help="outputs match the data?")
    return p.parse_args(argv)


class Tee:
    """Write console output to the screen and to a log file at the same time."""
    def __init__(self, *streams):
        self.streams = streams

    def write(self, text: str) -> int:
        for stream in self.streams:
            stream.write(text)
        return len(text)

    def flush(self) -> None:
        for stream in self.streams:
            stream.flush()


@contextmanager
def log_console(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        original, sys.stdout = sys.stdout, Tee(sys.stdout, fh)
        try:
            yield
        finally:
            sys.stdout = original


def use_utf8_console() -> None:
    """Windows terminals default to a code page that cannot print Δ or →."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


def main(argv=None) -> None:
    use_utf8_console()
    args = parse_args(argv)
    if args.prepare_sources:
        print(f"wrote {prepare_sources_template(config.DATA_DIR)}")
        return
    if args.build_matrix:
        print(f"wrote {build_matrix_from_sources(config.DATA_DIR)}")
        return
    if args.fetch_osm:
        from src.osm_data import fetch_all
        fetch_all(config.DATA_DIR)
        return
    if args.check_consistency:
        from src.consistency import run_consistency_check
        sys.exit(0 if run_consistency_check(args.placeholder) else 1)

    if args.validate or args.find_demo_seed:
        run(args)  # quick checks: no log file, so the last full-run log is kept
        return
    with log_console(OUT / ("experiments_log.txt" if args.experiments else "run_log.txt")):
        run(args)


def run(args: argparse.Namespace) -> None:
    print("Simulated Annealing for the TSP - Red Cross blood delivery, Cagayan de Oro City")
    ds, rep, D = load_and_validate(args.placeholder)
    if args.validate:
        return
    from src.docs_builder import build_docs
    if args.find_demo_seed:
        params, _ = resolve_sa_params(D, args.neighbor)
        seed = find_demo_seed(D, params, args.neighbor, brute_force(D).optimal_cost)
        print(f"\nSuggested demo seed: {seed}  (set DEFAULT_SEED in src/config.py or use --seed)")
        return
    if args.experiments:
        run_experiments(ds, D, args)
        build_docs()
        return

    report.print_inputs(ds, D)
    ctx = run_presentation(ds, D, args)
    run_statistics(ds, D, ctx, args)
    if not args.no_figures:
        make_figures(ds, D, ctx)
    report.write_json(OUT / "results_summary.json", build_summary(ds, rep, D, ctx, args))
    build_docs()
    if ds.is_placeholder:
        print(report.placeholder_banner())


if __name__ == "__main__":
    main()
