"""
docs_builder.py - fill the presentation documents with the numbers of the latest run.

Templates live in docs/templates/*.md.tmpl and use {{key}} placeholders. The values
come from outputs/results_summary.json (and outputs/experiments.json when it was
made from the same data), so the slides, the script and the console always show
identical numbers. Every generated file records the data fingerprint.
"""
from __future__ import annotations

import json
import math
import re
from pathlib import Path

from src import config
from src.report import fmt_km

PLACEHOLDER_RE = re.compile(r"\{\{(\w+)\}\}")
TEMPLATES = ("slides_outline", "narration_script", "demo_checklist", "results_tables")
ROOT_TEMPLATES = ("REFERENCES",)  # rendered into the project root instead of docs/


def _load_json(path: Path) -> dict | None:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def md_table(headers: list[str], rows: list[list], align: str | None = None) -> str:
    align = align or "l" * len(headers)
    rule = ["---:" if a == "r" else ":---" for a in align]
    lines = ["| " + " | ".join(map(str, headers)) + " |", "| " + " | ".join(rule) + " |"]
    lines += ["| " + " | ".join(str(c) for c in row) + " |" for row in rows]
    return "\n".join(lines)


def _labels(summary: dict) -> list[str]:
    return [loc["label"] for loc in summary["locations"]]


def _name(summary: dict, i: int) -> str:
    loc = summary["locations"][i]
    return loc["short_name"] or loc["name"]


def _route_str(summary: dict, route: list[int], names: bool = False) -> str:
    return " → ".join(_name(summary, v) if names else _labels(summary)[v] for v in route)


# ---------------------------------------------------------------------------
# Context pieces
# ---------------------------------------------------------------------------
def data_context(s: dict) -> dict:
    labels, n = _labels(s), s["n"]
    vertex_rows = [[l["label"], l["name"], l["short_name"], l["role"], l["address"] or "–",
                    f"{l['latitude']:.5f}, {l['longitude']:.5f}"] for l in s["locations"]]
    matrix_rows = []
    for i in range(n):
        cells = ["–" if i == j else fmt_km(s["matrix"][i][j]) +
                 ("\\*" if s["edge_status"][i][j] == "ASSUMED" else "") for j in range(n)]
        matrix_rows.append([f"**{labels[i]}**"] + cells)
    counts = s["status_counts"]
    m = s["measurement"]
    dates = ", ".join(m["dates"]) if m["dates"] else "n/a (placeholder data)"
    return {
        "n": n, "n_hospitals": s["n_hospitals"], "n_arcs": s["n_arcs"],
        "n_pairs": n * (n - 1) // 2, "n_tours": f"{s['n_tours']:,}",
        "n_tours_formula": f"({n}−1)! = {n - 1}! = {s['n_tours']:,}",
        "depot_name": s["locations"][0]["name"], "depot_short": _name(s, 0),
        "hospital_list": "\n".join(f"  - **{l['label']}** {l['name']}" for l in s["locations"][1:]),
        "n_squared": n * n, "n_route_entries": n + 1,
        "vertex_table": md_table(["Vertex", "Name", "Short name", "Role", "Address", "Lat, Lon"],
                                 vertex_rows),
        "matrix_table": md_table(["from \\ to"] + labels, matrix_rows, "l" + "r" * n),
        "status_summary": ", ".join(f"{v} {k}" for k, v in sorted(counts.items())),
        "assumed_count": s["assumed_edges"], "asym_pairs": s["asymmetric_pairs"],
        "triangle_breaks": s["triangle_violations"], "measured_dates": dates,
        "measured_times": (f"{m['first_time']}–{m['last_time']}" if m["first_time"]
                           else "n/a"),
    }


def matrix_resolution(matrix: list[list[float]]) -> float:
    """Smallest step the distances are recorded in: 0.1 km (Google Maps) or 0.01 km (OSRM)."""
    values = [v for row in matrix for v in row if v]
    return 0.1 if all(abs(v * 10 - round(v * 10)) < 1e-9 for v in values) else 0.01


def source_context(s: dict) -> dict:
    """How the distances and coordinates were obtained, worded for slides and references."""
    m, label = s["measurement"], s["measurement"]["source_label"]
    when = (f"{', '.join(m['dates'])} ({m['first_time']}–{m['last_time']}, Philippine time)"
            if m["dates"] else "n/a (placeholder data)")
    osm = "OpenStreetMap" in label
    if osm:
        method = (f"the length of the route chosen by the OSRM car router on the OpenStreetMap "
                  f"road network, one request per direction, obtained on {when}")
        dependency = "we depend on OpenStreetMap's road data and on OSRM's choice of route"
    elif "Google" in label:
        method = f"Google Maps driving mode, shortest suggested route, read on {when}"
        dependency = "we depend on Google Maps' route choice"
    else:
        method, dependency = f"synthetic placeholder values ({when})", "the data are synthetic"
    n_osm, n_all = m["coords_from_osm"], m["coords_total"]
    coords = ("OpenStreetMap (Nominatim geocoder and Overpass API)" if n_osm == n_all else
              "Google Maps place pins" if n_osm == 0 else
              f"OpenStreetMap for {n_osm} places and Google Maps pins for "
              f"{n_all - n_osm} (noted per row in `data/locations.csv`)")
    res = matrix_resolution(s["matrix"])
    refs = []
    if osm:
        refs += [f'[14] OpenStreetMap contributors, "OpenStreetMap" road network data, Open '
                 f'Database License. [Online]. Available: https://www.openstreetmap.org/copyright '
                 f'(routing queried {when}).',
                 '[15] D. Luxen and C. Vetter, "Real-time routing with OpenStreetMap data," in '
                 '*Proc. 19th ACM SIGSPATIAL Int. Conf. Advances in Geographic Information '
                 "Systems (GIS '11)*, Chicago, IL, USA, 2011, pp. 513–516, "
                 'doi: 10.1145/2093973.2094062. Service used: OSRM demo server '
                 'https://router.project-osrm.org (car profile).']
        if n_osm:
            refs.append('[16] Nominatim, "OpenStreetMap geocoder." [Online]. Available: '
                        'https://nominatim.org (coordinates of the places marked in '
                        '`data/locations.csv`).')
    if not osm or n_osm < n_all:
        use = "driving distances read on " + when if not osm else "place coordinates"
        refs.append(f'[{14 + len(refs)}] Google LLC, "Google Maps," Cagayan de Oro City. '
                    f'[Online]. Available: https://www.google.com/maps ({use}).')
    return {"distance_source_short": label.replace(" road distances", "").replace(
                " driving distances", ""),
            "distance_method": method, "coord_source": coords, "route_dependency": dependency,
            "resolution_km": f"{res:g}", "data_reference_block": "\n\n".join(refs)}


def t_stop_reason(t_stop: float, resolution: float) -> str:
    p = math.exp(-resolution / t_stop)
    return (f"distances are recorded to {resolution:g} km; at T = {t_stop:g} a {resolution:g} km "
            f"worse move has P = e^−{resolution / t_stop:g} ≈ {p:.1g}")


def sa_context(s: dict) -> dict:
    p, sa = s["params"], s["sa"]
    patience = (math.ceil(math.log(p["patience_drop_factor"]) / -math.log(p["alpha"]))
                if p["patience_drop_factor"] else None)
    levels_planned = math.ceil(math.log(p["t_stop"] / p["t0"]) / math.log(p["alpha"]))
    return {
        "t0": f"{p['t0']:g}", "target_p": p["target_initial_acceptance"],
        "mean_uphill": f"{s['mean_uphill_km']:.2f}" if s["mean_uphill_km"] else "–",
        "alpha": p["alpha"], "ipt": p["iterations_per_temperature"], "t_stop": f"{p['t_stop']:g}",
        "patience_levels": patience if patience else "off",
        "patience_drop": f"{p['patience_drop_factor']:g}" if p["patience_drop_factor"] else "–",
        "max_iter": f"{p['max_total_iterations']:,}", "levels_planned": levels_planned,
        "moves_planned": f"{levels_planned * p['iterations_per_temperature']:,}",
        "seed": s["seed"], "neighbor": s["neighbor"], "runs": s["runs"],
        "sa_route": sa["route_labels"].replace(" -> ", " → "),
        "sa_route_names": sa["route_names"].replace(" -> ", " → "),
        "sa_cost": fmt_km(sa["cost"]), "initial_cost": fmt_km(sa["initial_cost"]),
        "initial_route": sa["initial_route_labels"].replace(" -> ", " → "),
        "iterations": f"{sa['iterations']:,}", "levels": sa["levels"],
        "best_found_at": f"{sa['best_found_at']:,}", "stop_reason": sa["stop_reason"],
        "runtime_ms": f"{1000 * sa['runtime_s']:.0f}",
        "evals_per_move": s["n"],
        "n_swaps": (s["n"] - 1) * (s["n"] - 2) // 2,
        "ipt_ratio": f"{p['iterations_per_temperature'] / ((s['n'] - 1) * (s['n'] - 2) / 2):.0f}",
    }


def verification_context(s: dict) -> dict:
    v = s["verification"]
    rows = [[e["step"], f"{_labels(s)[e['from_id']]} {_name(s, e['from_id'])}",
             f"{_labels(s)[e['to_id']]} {_name(s, e['to_id'])}", fmt_km(e["km"]),
             fmt_km(e["cumulative_km"]), e["status"]] for e in v["edges"]]
    addition = " + ".join(fmt_km(e["km"]) for e in v["edges"])
    checks = "\n".join(f"- {'✅' if c['passed'] else '❌'} {c['name']} ({c['detail']})"
                       for c in v["checks"])
    return {"verification_table": md_table(["#", "From", "To", "km", "Running km", "Data"],
                                           rows, "rllrrl"),
            "verification_sum": f"{addition} = **{fmt_km(v['recomputed_km'])} km**",
            "verification_checks": checks, "verification_passed": "PASS" if v["passed"] else "FAIL"}


def comparison_context(s: dict) -> dict:
    bf, g, sa = s["brute_force"], s["greedy"], s["sa"]
    opt = bf["optimal_cost"]
    if sa["is_optimal"]:
        statement = (f"The SA route ({fmt_km(sa['cost'])} km) is **optimal for this instance**. "
                     f"This is proven by brute force, which checked all {bf['tours_evaluated']:,} "
                     f"possible tours and found no shorter one. SA by itself does not guarantee "
                     f"optimality; the proof comes from the exhaustive search.")
    else:
        statement = (f"The SA route ({fmt_km(sa['cost'])} km) is an **approximate solution**, "
                     f"{sa['gap_pct']:.2f}% longer than the proven optimum of {fmt_km(opt)} km.")
    ties = (f"{bf['n_optimal_tours']} different tours tie for the optimum: "
            + "; ".join(r.replace(" -> ", " → ") for r in bf["optimal_routes"])
            if bf["n_optimal_tours"] > 1 else "The optimal tour is unique.")
    return {
        "optimal_cost": fmt_km(opt), "optimal_route": bf["optimal_routes"][0].replace(" -> ", " → "),
        "n_optimal": bf["n_optimal_tours"], "ties_note": ties,
        "bf_runtime": f"{bf['runtime_s']:.2f}", "greedy_cost": fmt_km(g["cost"]),
        "greedy_gap": f"{g['gap_pct']:.1f}", "greedy_route": g["route_labels"].replace(" -> ", " → "),
        "mean_random": fmt_km(bf["mean_cost"]), "worst_tour": fmt_km(bf["worst_cost"]),
        "save_vs_random_km": fmt_km(bf["mean_cost"] - sa["cost"]),
        "save_vs_random_pct": f"{100 * (bf['mean_cost'] - sa['cost']) / bf['mean_cost']:.0f}",
        "save_vs_greedy_km": fmt_km(g["cost"] - sa["cost"]),
        "save_vs_greedy_pct": f"{100 * (g['cost'] - sa['cost']) / g['cost']:.1f}",
        "optimality_statement": statement,
        "sa_vs_optimum_spoken": (
            "That is exactly our Simulated Annealing result, so our route is optimal for this "
            "instance, and the proof is the exhaustive search." if sa["is_optimal"] else
            f"Our route is {fmt_km(sa['cost'] - opt)} kilometres longer, so it is an approximate "
            f"solution."),
        "optimal_claim_spoken": (
            "Because brute force checked every possible tour, this route is proven optimal for "
            "this instance. The proof comes from the exhaustive search, not from Simulated "
            "Annealing itself." if sa["is_optimal"] else
            f"Brute force found a tour {fmt_km(sa['cost'] - opt)} km shorter, so our route is an "
            f"approximate solution, {sa['gap_pct']:.2f}% above the optimum."),
        "gap_pct": f"{sa['gap_pct']:.2f}",
    }


def stats_context(s: dict) -> dict:
    r, bf, g = s["run_summary"], s["brute_force"], s["greedy"]
    opt = bf["optimal_cost"]
    rows = [["SA (ours)", fmt_km(r["best"]), fmt_km(r["worst"]), f"{r['mean']:.3f}",
             f"{r['variance']:.3f}", f"{r['std']:.3f}", f"{r['mean_runtime_s']:.4f} s",
             f"{r['hit_rate_pct']:.0f}%"],
            ["Brute force", fmt_km(opt), fmt_km(opt), f"{opt:.3f}", "0", "0",
             f"{bf['runtime_s']:.4f} s", "100%"],
            ["Greedy", fmt_km(g["cost"]), fmt_km(g["cost"]), f"{g['cost']:.3f}", "0", "0",
             f"{g['runtime_s']:.4f} s", "100%" if g["gap_pct"] == 0 else "0%"]]
    hits = round(r["hit_rate_pct"] * r["runs"] / 100)
    return {"table2": md_table(["Algorithm", "Best", "Worst", "Average", "Variance", "Std Dev",
                                "Avg time", "Hit optimum"], rows, "lrrrrrrr"),
            "hit_rate": f"{r['hit_rate_pct']:.0f}", "hits": hits, "runs_n": r["runs"],
            "mean_gap": f"{r['mean_gap_pct']:.2f}", "max_gap": f"{r['max_gap_pct']:.2f}",
            "mean_runtime_ms": f"{1000 * r['mean_runtime_s']:.0f}",
            "mean_moves": f"{r['mean_iterations']:,.0f}"}


def trace_context(s: dict) -> dict:
    """Hand-worked example of the first moves (same numbers as the --trace output)."""
    labels, D = _labels(s), s["matrix"]
    steps = s["trace"]
    if not steps:
        return {"trace_example": "_(no trace recorded)_", "initial_cost_calc": ""}
    first = steps[0]["current_tour"] + [0]
    terms = [D[a][b] for a, b in zip(first[:-1], first[1:])]
    initial_calc = (" + ".join(f"d({labels[a]},{labels[b]})" for a, b in zip(first[:-1], first[1:]))
                    + "\n= " + " + ".join(fmt_km(t) for t in terms)
                    + f" = **{fmt_km(sum(terms))} km**")
    blocks = []
    for st in steps:
        i, j = sorted(st["positions"])
        cur, new = st["current_tour"] + [0], st["new_tour"] + [0]
        head = (f"**Move {st['iteration']}** (T = {st['temperature']:.4f} km): swap positions "
                f"{i} and {j} ({labels[cur[i]]} ↔ {labels[cur[j]]})" if s["neighbor"] == "swap"
                else f"**Move {st['iteration']}** (T = {st['temperature']:.4f} km): reverse "
                     f"positions {i}..{j}")
        body = [f"- current: {_route_str(s, cur)} = {fmt_km(st['current_cost'])} km",
                f"- new: {_route_str(s, new)} = {fmt_km(st['new_cost'])} km",
                f"- Δ = {fmt_km(st['new_cost'])} − {fmt_km(st['current_cost'])} = "
                f"{st['delta']:+.2f} km"]
        if st["delta"] < 0:
            body.append("- Δ < 0 → shorter tour → **ACCEPT** (Alg 2.5 steps 6–7; no random number)")
        else:
            body.append(f"- P = e^(−Δ/T) = e^(−{st['delta']:.2f} / {st['temperature']:.4f}) = "
                        f"**{st['probability']:.4f}** (Alg 2.5 step 9)")
            verdict = ("r < P → **ACCEPT** the worse tour" if st["accepted"]
                       else "r ≥ P → **REJECT**, keep the current tour")
            body.append(f"- r = {st['r']:.4f} → {verdict}")
        blocks.append(head + "\n" + "\n".join(body))
    return {"trace_example": "\n\n".join(blocks), "initial_cost_calc": initial_calc}


def experiments_context(s: dict, e: dict | None) -> dict:
    if not e or e.get("fingerprint") != s["fingerprint"]:
        missing = "_Not run yet for this data — run `python main.py --experiments`._"
        return {"alpha_table": missing, "neighbor_table": missing, "paper_defaults": missing,
                "paper_defaults_short": missing,
                "sens_runs": "–", "alpha_choice_reason": missing}
    rows = [[r["alpha"], r["planned_levels"], f"{r['mean_iterations']:,.0f}",
             f"{r['mean']:.3f}", f"{r['std']:.3f}", f"{r['hit_rate_pct']:.0f}%",
             f"{1000 * r['mean_runtime_s']:.0f} ms"] for r in e["alpha_sensitivity"]]
    nrows = [[r["neighbor"], r["t0"], f"{r['mean_iterations']:,.0f}", f"{r['mean']:.3f}",
              f"{r['hit_rate_pct']:.0f}%", f"{1000 * r['mean_runtime_s']:.0f} ms"]
             for r in e["neighbor_comparison"]]
    p = e["paper_defaults"]
    paper = (f"Paper defaults (T0 = {p['t0']:g}, α = {p['alpha']}, {p['iterations_per_temperature']} "
             f"moves/level, T_stop = {p['t_stop']:g}): **{p['iterations']:,} moves, "
             f"{p['levels']:,} levels, {p['runtime_s']:.1f} s** → {fmt_km(p['cost'])} km "
             f"({'optimal' if p['hit_optimum'] else 'not optimal'}).")
    chosen = next((r for r in e["alpha_sensitivity"] if r["alpha"] == s["params"]["alpha"]), None)
    reason = (f"α = {s['params']['alpha']} reached the optimum in {chosen['hit_rate_pct']:.0f}% of "
              f"{e['runs_per_setting']} runs in {1000 * chosen['mean_runtime_s']:.0f} ms per run; "
              f"see the table for the faster/slower alternatives." if chosen else "")
    return {"alpha_table": md_table(["α", "max levels", "moves (mean)", "mean km", "std",
                                     "hit optimum", "time/run"], rows, "rrrrrrr"),
            "neighbor_table": md_table(["neighbour", "T0", "moves (mean)", "mean km",
                                        "hit optimum", "time/run"], nrows, "lrrrrr"),
            "paper_defaults": paper, "sens_runs": e["runs_per_setting"],
            "paper_defaults_short": (f"one run took **{p['iterations']:,} moves and "
                                     f"{p['runtime_s']:.1f} s** → {fmt_km(p['cost'])} km "
                                     f"({'optimal' if p['hit_optimum'] else 'not optimal'})."),
            "alpha_choice_reason": reason}


def build_context(summary: dict, experiments: dict | None) -> dict:
    ctx = {"fingerprint": summary["fingerprint"], "generated_at": summary["generated_at"],
           "gmaps_url": summary.get("google_maps_route_url", ""),
           "data_banner": ("> ⚠️ **PLACEHOLDER DATA.** Every number in this file comes from the "
                           "synthetic demo dataset. Enter the real data and rerun "
                           "`python main.py` before using it.\n" if summary["is_placeholder"]
                           else "")}
    for part in (data_context(summary), source_context(summary), sa_context(summary),
                 verification_context(summary),
                 comparison_context(summary), stats_context(summary), trace_context(summary),
                 experiments_context(summary, experiments)):
        ctx.update(part)
    ctx.update(library_versions())
    ctx["t_stop_reason"] = t_stop_reason(summary["params"]["t_stop"],
                                         float(ctx["resolution_km"]))
    interp = config.TEMPLATES_DIR / "interpretation.md"
    ctx["interpretation"] = (interp.read_text(encoding="utf-8").strip() if interp.exists() else
                             "_To be written once the real data are in (which neighbourhoods "
                             "the route groups together, and why that order avoids "
                             "back-tracking)._")
    return ctx


def library_versions() -> dict:
    from importlib.metadata import PackageNotFoundError, version
    out = {}
    for pkg in ("networkx", "matplotlib", "numpy", "folium", "pillow"):
        try:
            out[f"v_{pkg}"] = version(pkg)
        except PackageNotFoundError:
            out[f"v_{pkg}"] = "n/a"
    return out


def render(template: str, ctx: dict) -> str:
    missing = sorted({k for k in PLACEHOLDER_RE.findall(template) if k not in ctx})
    if missing:
        raise KeyError(f"template keys without a value: {missing}")
    return PLACEHOLDER_RE.sub(lambda m: str(ctx[m.group(1)]), template)


def build_docs(out_dir: Path = config.OUTPUT_DIR, docs_dir: Path = config.DOCS_DIR) -> list[Path]:
    summary = _load_json(out_dir / "results_summary.json")
    if summary is None:
        print("(docs not built: run `python main.py` first to create results_summary.json)")
        return []
    ctx = build_context(summary, _load_json(out_dir / "experiments.json"))
    written = []
    targets = [(name, docs_dir) for name in TEMPLATES] + \
              [(name, config.PROJECT_ROOT) for name in ROOT_TEMPLATES]
    for name, folder in targets:
        template = (config.TEMPLATES_DIR / f"{name}.md.tmpl").read_text(encoding="utf-8")
        footer = (f"\n\n---\n_Generated {ctx['generated_at']} from data fingerprint "
                  f"`{ctx['fingerprint']}` by `src/docs_builder.py`. Do not edit by hand; "
                  f"edit `docs/templates/{name}.md.tmpl` instead._\n")
        path = folder / f"{name}.md"
        path.write_text(render(template, ctx).rstrip() + footer, encoding="utf-8")
        written.append(path)
    print(f"\nDocs updated with these numbers: {', '.join(p.name for p in written)}")
    return written
