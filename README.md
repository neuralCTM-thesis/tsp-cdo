# Simulated Annealing for a Real-Life TSP: Blood Deliveries in Cagayan de Oro City

A Philippine Red Cross Misamis Oriental courier (illustrative scenario) leaves the chapter office, delivers blood units to **8 hospitals**, each exactly once, and returns. We minimise the total **driving distance (km)** with **Simulated Annealing (SA)**, following Algorithm 2.5 and the Appendix 4.5 code of

> R. Luna-Garcia, T. M. C. Candano, R. L. Caga-anan, "Performance Analysis of Classical Algorithms for the Traveling Salesman Problem," *The Mindanawan Journal of Mathematics* 6(2):79–111, 2024. doi:10.62071/tmjm.v6i2.716

We then **prove** whether the result is optimal: brute force runs on the same matrix, the route is recounted edge by edge, and SA is run with 30 seeds.

> **Data status.** `data/*.csv` hold real data: OpenStreetMap coordinates for all 9 places and 72 directed OSRM car-route distances, fetched with `python main.py --fetch-osm` on 2026-10-17. Three places (the Red Cross chapter, Maria Reyna-Xavier University Hospital and J.R. Borja) were found on OpenStreetMap under alternate names; `locations.csv` notes the source of each. If `data/*.csv` are emptied, the program falls back to a clearly labelled **PLACEHOLDER** dataset (`data/placeholder/`). See [`docs/data_collection_guide.md`](docs/data_collection_guide.md).

---

## Quick start

```bash
# 1. create an environment (once)
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # macOS / Linux
python -m pip install -r requirements.txt

# 2. check that everything works
python -m pytest                # 57 tests

# 3. run it
python main.py --trace          # full run + the first 5 SA moves in full
python main.py --experiments    # parameter study (about 3 min); run once per dataset
python main.py --check-consistency
```

Results land in `outputs/`. The presentation documents in `docs/` and `REFERENCES.md` are regenerated with the new numbers after every run.

Prefer a notebook? Open **`demo.ipynb`** (`jupyter notebook demo.ipynb`). It runs the same functions step by step, with large fonts for recording.

## Command reference

| Command | What it does |
|---|---|
| `python main.py` | validate data → print inputs → SA → verification → brute force + greedy → 30 runs → figures → docs |
| `--trace` | also print the first 5 SA moves (tour, swap, Δ, T, P = e^(−Δ/T), r, ACCEPT/REJECT) |
| `--seed N` | seed of the presentation run (default in `src/config.py`) |
| `--runs N` | number of independent runs for the statistics (default 30) |
| `--neighbor swap\|2opt` | swap = the paper's move (default); 2opt = segment reversal, our extension |
| `--placeholder` | force the placeholder dataset |
| `--no-figures` | skip figures (faster) |
| `--experiments` | α sensitivity, swap vs 2-opt, one run with the paper's defaults |
| `--validate` | only check the CSV files |
| `--prepare-sources` | write the 72 rows of `data/data_sources.csv` (after `locations.csv` is filled) |
| `--build-matrix` | build `data/distance_matrix.csv` from `data/data_sources.csv` |
| `--fetch-osm` | fill blank coordinates (Nominatim) and all 72 directed distances (OSRM car router, OpenStreetMap) |
| `--find-demo-seed` | suggest a seed whose first moves show every case of the acceptance rule |
| `--check-consistency` | confirm every figure, table, map and doc comes from the current data |

## Project structure

```
tsp_sa_cdo/
  data/                    THE DATASET (separate from the code)
    locations.csv          V0..V8: name, short name, role, address, lat, lon, map link
    distance_matrix.csv    9 x 9 DIRECTED matrix in km (row = from, column = to)
    data_sources.csv       one row per directed edge: ACTUAL/ASSUMED, date, time, route
    placeholder/           synthetic demo data (never present it)
  src/
    config.py              every parameter in one place
    data_loader.py         load + validate the CSVs (square, zero diagonal, positive, ids...)
    graph_model.py         networkx DiGraph and the tour-cost function
    simulated_annealing.py THE ALGORITHM (comments map lines to Alg 2.5 steps)
    baselines.py           brute force (Alg 2.3, exact) and greedy (Alg 2.7)
    verify.py              tour validity + independent edge-by-edge recount
    experiments.py         30-run statistics, α sensitivity, neighbour comparison
    visualize.py           charts and the GIF
    maps.py                folium HTML map + static PNG map
    report.py              console tables, CSV/JSON exports
    osm_data.py            OpenStreetMap coordinates + OSRM directed distances (--fetch-osm)
    docs_builder.py        fills docs/templates with the numbers of the latest run
    consistency.py         data-fingerprint check across all outputs
  main.py                  single entry point
  demo.ipynb               notebook version for the video
  tests/                   pytest suite
  tools/make_placeholder_data.py   regenerates the placeholder data and blank templates
  outputs/                 generated figures, tables, logs
  docs/                    slides outline, narration script, checklists, guides
  README.md  REFERENCES.md  requirements.txt
```

## The algorithm in one screen

| Alg 2.5 | Step | Code |
|---|---|---|
| 1 | input: distance matrix D | `simulated_annealing(D, ...)` |
| 2 | random tour + its length (depot fixed first) | `random_tour`, `tour_cost` |
| 3 | high initial temperature T0 | `calibrate_initial_temperature` (P ≈ 0.8 for an average worse move) |
| 4 | swap two cities | `swap_two_cities` |
| 5 | length of the new tour | `tour_cost` (full O(n) recount, as in Theorem 2.5) |
| 6–10 | accept if shorter, else with P = e^(−Δ/T) | `metropolis` |
| 11 | T ← αT | `T *= params.alpha` |
| 12 | stop: T ≤ T_stop, no improvement, or max moves | three `stop_reason`s |
| 13 | output the best tour found | best-so-far kept separately from the current tour |

Algorithm 2.5 hides one detail that Appendix 4.5 shows: an **inner loop** of `iterations_per_temperature` moves at each temperature, then one cooling step.

**Parameters** (`src/config.py`): T0 auto (calibrated from the data), α = 0.98, 200 moves per level, T_stop = 0.001 km (distances are recorded to 0.01 km; at T = 0.001 a 10 m detour has P ≈ e^−10), patience = no new best while T falls 100×. Why not the paper's T0 = 1000 / α = 0.995 / 1000 moves / T_stop = 1e-8? They ignore the km scale and need about 5 million moves per run. `python main.py --experiments` measures this.

**Optimality.** SA is a heuristic and guarantees nothing; theoretical convergence needs logarithmic cooling. We only call the route "optimal for this instance" when it equals the **brute-force** optimum over all (n−1)! = 40,320 tours.

## Outputs (what to show for which rubric item)

| File | Content |
|---|---|
| `fig0_locations_map.png` | the 9 locations on an OpenStreetMap base map, no route (slide A3) |
| `fig1_graph.png`, `fig1b_route_on_graph.png` | labelled directed graph; the route on it with km per leg |
| `fig2_weight_matrix.png` | weight matrix in km, assumed cells hatched |
| `route_map.html`, `fig3_route_map.png` | route on a real map, numbered stops, arrows, Google Maps links |
| `fig4_convergence.png` | current vs best tour length, and the temperature (two panels, shared x-axis) |
| `fig5_acceptance.png` | P = e^(−Δ/T) of every worse move; acceptance rate vs T |
| `fig6_sa_animation.gif` | the search in motion |
| `fig7_runs_vs_optimum.png`, `fig8_search_space.png` | 30 runs vs brute force vs greedy; all 40,320 tours |
| `fig9_alpha_sensitivity.png`, `fig10_neighbor_comparison.png` | parameter study (from `--experiments`) |
| `trace.csv`, `sa_history.csv` | step-by-step numbers |
| `verification_table.csv` | edge-by-edge recount |
| `table2_style_results.csv`, `sa_runs.csv` | paper Table 2 format, per-run details |
| `results_summary.json`, `experiments.json` | everything, machine-readable (feeds `docs/`) |

Every file carries the **data fingerprint** (a hash of the three CSVs). `--check-consistency` uses it to prove that the graph, table, inputs and results all match.

## Modifications to the paper's code
See `REFERENCES.md` → "How our code relates to [1] Appendix 4.5": directed matrix input, fixed depot, calibrated and tuned parameters, the extra stopping rules, trace/history, verification, and an optional 2-opt neighbour.

## Limitations
Static distances (no traffic or time of day), no time windows, a single vehicle, dependence on the map data and the router's route choice, and a small n (needed so brute force can prove optimality).

## Troubleshooting
- **Δ or → print as `?` on Windows:** run in Windows Terminal or VS Code. `main.py` already switches the console to UTF-8.
- **"basemap tiles unavailable"**: the static map PNG needs internet for OpenStreetMap tiles; without it, the PNG uses a plain background. The HTML map always works online.
- **The validator stops the run:** read the ERROR lines; `docs/data_collection_guide.md` explains each one.
