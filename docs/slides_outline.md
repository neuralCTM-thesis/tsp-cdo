# Slides outline: Simulated Annealing for a Real-Life TSP in Cagayan de Oro City

> ⚠️ **PLACEHOLDER DATA.** Every number in this file comes from the synthetic demo dataset. Enter the real data and rerun `python main.py` before using it.

Target length **12–13 min** (PIT allows 10–15). Section timing follows the PIT guide:

| Section | Slides | Time |
|---|---|---|
| A. Introduction, problem, objective | A1–A4 | 0:00–2:30 |
| B. Assigned algorithm (Simulated Annealing) | B1–B6 | 2:30–5:15 |
| C. Graph model, data, methodology | C1–C3 | 5:15–7:45 |
| D. Python execution and results (live) | D1–D4 | 7:45–11:30 |
| E. Conclusion and references | E1–E3 | 11:30–12:45 |

Figures are in `outputs/`. Every figure, table and number below comes from the same data (fingerprint `af6df0a76c`).

---

## A. Introduction, problem and objective (2:30)

### A1 · Title (0:00–0:15)
- **Simulated Annealing for the Traveling Salesperson Problem: Routing Blood Deliveries in Cagayan de Oro City**
- [Your names] · [Course / section] · [Instructor] · [Date]
- Assigned algorithm: Simulated Annealing (Luna-Garcia, Candano & Caga-anan, TMJM 6(2), 2024, §2.5)

### A2 · The real-life problem (0:15–1:00)
- Illustrative scenario: a **Philippine Red Cross Misamis Oriental** courier leaves the chapter office with blood units, delivers to **8 hospitals** in Cagayan de Oro City, **each exactly once**, and returns to base.
- Why this is a TSP: one vehicle, a fixed set of stops, a closed tour, and a total length to minimise.
- Why it matters: shorter routes mean blood reaches hospitals sooner and the vehicle uses less fuel.
- Visual: `outputs/route_map.html` (screenshot showing only the markers) or `fig3_route_map.png`.

### A3 · Locations (vertices) (1:00–1:45)
- Start and end: **V0 = PLACEHOLDER Depot (Red Cross chapter office)** (depot).
- Hospitals:
  - **V1** PLACEHOLDER Hospital A
  - **V2** PLACEHOLDER Hospital B
  - **V3** PLACEHOLDER Hospital C
  - **V4** PLACEHOLDER Hospital D
  - **V5** PLACEHOLDER Hospital E
  - **V6** PLACEHOLDER Hospital F
  - **V7** PLACEHOLDER Hospital G
  - **V8** PLACEHOLDER Hospital H
- Area: Cagayan de Oro City proper. Coordinates: Google Maps place pins (`data/locations.csv`).

### A4 · Objective, assumptions and constraints (1:45–2:30)
- **Objective:** minimise the total **driving distance (km)**:
  `min  d(V0,π1) + d(π1,π2) + … + d(π8,V0)` over every order π of the hospitals.
- **Constraints:** start and end at V0; visit every hospital exactly once; travel on roads only.
- **Assumptions:** a single vehicle with no capacity limit; time spent at each stop is ignored; distances are *driving* distances: synthetic placeholder values (n/a (placeholder data)). The distances are fixed (no traffic).
- **Deliberate improvement over the paper:** the paper uses straight-line (Euclidean) distance between (x, y) points. Real roads, one-way streets and bridges make straight-line distance unrealistic, so we use measured road distances, and these can differ by direction.

---

## B. Assigned algorithm: Simulated Annealing (2:45)

### B1 · Origin and idea (2:30–3:00)
- **Annealing** in metallurgy: heat a metal, then cool it slowly so its atoms settle into a low-energy, stable structure.
- **Metropolis et al. (1953):** a rule for accepting random moves at temperature T.
- **Kirkpatrick, Gelatt & Vecchi (1983, *Science*)** turned it into an optimisation method; **Černý (1985)** applied it to the TSP independently.
- The analogy:

| Physics | Our TSP |
|---|---|
| state of the atoms | a tour (order of the hospitals) |
| energy | total km of the tour |
| temperature T | how willing we are to accept a longer tour |
| slow cooling | T ← αT |
| ground state | the shortest tour |

### B2 · The procedure: Algorithm 2.5, line by line (3:00–3:45)

| Alg 2.5 | What it does | Our code (`src/simulated_annealing.py`) |
|---|---|---|
| 1 | Input: cities and pairwise distances | distance matrix `D` (row = from, column = to) |
| 2 | Random tour and its total distance | `random_tour()`, `tour_cost()`; depot fixed at position 0 |
| 3 | Set a high initial temperature T | `T = params.t0` = **14.58 km** (calibrated, see C3) |
| 4 | Small change: swap two cities | `swap_two_cities()` (the depot never moves) |
| 5 | Total distance of the new tour | `tour_cost(new_tour, D)`: O(n) |
| 6–7 | If shorter: accept | `metropolis()`: Δ < 0 → accept |
| 8–9 | Else accept with P = e^(−Δ/T) | draw r ∈ [0,1); accept if r < P |
| 10 | end if | – |
| 11 | Cool: T ← αT, 0 < α < 1 | `T *= params.alpha` (α = **0.98**) |
| 12 | Stop when T is low / no improvement / max iterations | T ≤ 0.001 km · 228 levels without a new best · 2,000,000 moves |
| 13 | Output the shortest tour found | best-so-far tour, kept separately from the current tour |

### B3 · The loop that Algorithm 2.5 does not show (3:45–4:05)
- Algorithm 2.5 lists the steps once. The paper's Python code (Appendix 4.5) actually has **two nested loops**:

```
T ← T0                                         # step 3
while T > T_stop:                              # step 12 (outer loop)
    repeat 200 times:                          # inner loop: many moves at the SAME temperature
        new ← swap two cities of current       # step 4
        Δ ← cost(new) − cost(current)          # step 5
        if Δ < 0 or random() < e^(−Δ/T):       # steps 6–10
            current ← new; update best
    T ← α·T                                    # step 11
return best                                    # step 13
```
- Our run used **295 temperature levels × 200 moves = 59,000 moves**.

### B4 · The acceptance rule on our data (hand-worked, from `outputs/trace.csv`) (4:05–4:35)
Initial random tour cost (Alg 2.5 step 2):
`d(V0,V6) + d(V6,V4) + d(V4,V5) + d(V5,V2) + d(V2,V3) + d(V3,V7) + d(V7,V8) + d(V8,V1) + d(V1,V0)
= 5.7 + 4.2 + 6.9 + 4.4 + 4.3 + 3.2 + 4.2 + 4.7 + 3.4 = **41.0 km**`

**Move 1** (T = 14.5800 km): swap positions 5 and 8 (V3 ↔ V1)
- current: V0 → V6 → V4 → V5 → V2 → V3 → V7 → V8 → V1 → V0 = 41.0 km
- new: V0 → V6 → V4 → V5 → V2 → V1 → V7 → V8 → V3 → V0 = 39.2 km
- Δ = 39.2 − 41.0 = -1.80 km
- Δ < 0 → shorter tour → **ACCEPT** (Alg 2.5 steps 6–7; no random number)

**Move 2** (T = 14.5800 km): swap positions 4 and 5 (V2 ↔ V1)
- current: V0 → V6 → V4 → V5 → V2 → V1 → V7 → V8 → V3 → V0 = 39.2 km
- new: V0 → V6 → V4 → V5 → V1 → V2 → V7 → V8 → V3 → V0 = 45.6 km
- Δ = 45.6 − 39.2 = +6.40 km
- P = e^(−Δ/T) = e^(−6.40 / 14.5800) = **0.6447** (Alg 2.5 step 9)
- r = 0.0357 → r < P → **ACCEPT** the worse tour

**Move 3** (T = 14.5800 km): swap positions 3 and 4 (V5 ↔ V1)
- current: V0 → V6 → V4 → V5 → V1 → V2 → V7 → V8 → V3 → V0 = 45.6 km
- new: V0 → V6 → V4 → V1 → V5 → V2 → V7 → V8 → V3 → V0 = 40.1 km
- Δ = 40.1 − 45.6 = -5.50 km
- Δ < 0 → shorter tour → **ACCEPT** (Alg 2.5 steps 6–7; no random number)

**Move 4** (T = 14.5800 km): swap positions 7 and 8 (V8 ↔ V3)
- current: V0 → V6 → V4 → V1 → V5 → V2 → V7 → V8 → V3 → V0 = 40.1 km
- new: V0 → V6 → V4 → V1 → V5 → V2 → V7 → V3 → V8 → V0 = 42.5 km
- Δ = 42.5 − 40.1 = +2.40 km
- P = e^(−Δ/T) = e^(−2.40 / 14.5800) = **0.8482** (Alg 2.5 step 9)
- r = 0.7230 → r < P → **ACCEPT** the worse tour

**Move 5** (T = 14.5800 km): swap positions 5 and 6 (V2 ↔ V7)
- current: V0 → V6 → V4 → V1 → V5 → V2 → V7 → V3 → V8 → V0 = 42.5 km
- new: V0 → V6 → V4 → V1 → V5 → V7 → V2 → V3 → V8 → V0 = 46.5 km
- Δ = 46.5 − 42.5 = +4.00 km
- P = e^(−Δ/T) = e^(−4.00 / 14.5800) = **0.7601** (Alg 2.5 step 9)
- r = 0.9357 → r ≥ P → **REJECT**, keep the current tour

- The key idea: at high T, even clearly worse tours are often accepted, so the search can climb out of local optima. As T drops, worse tours are almost never accepted.

### B5 · Advantages and limitations (4:35–4:55)
**Advantages**
- Escapes local optima by sometimes accepting worse tours (unlike greedy or pure hill-climbing).
- Simple: the whole method is one short function (`simulated_annealing()`), with no gradients and no problem-specific rules.
- Fast in practice: about 173 ms per run on our data (30-run mean).
- Works directly on a distance matrix, including **asymmetric** (one-way) distances.

**Limitations**
- Sensitive to its parameters (T0, α, moves per level, stopping rule); see the α experiment in C3.
- Stochastic: different seeds can give different answers, so we report 30 runs.
- **No optimality guarantee in practice.** Convergence to the optimum is proven only for logarithmic cooling (T_k ≈ c / log k; Geman & Geman 1984; Hajek 1988), which is far too slow to use.

### B6 · Optimality and time complexity (Theorem 2.5) (4:55–5:15)
- **SA is an approximate (heuristic) method.** It returns the best tour it *found*, not a proven optimum.
- **Theorem 2.5:** T(n) = O(n³). The reasoning: each move costs O(n) (swap O(1) + recompute the n arcs), and I moves give **O(I · n)**.
- **I = O(n²) is the authors' assumption, not a property of SA.** In practice I is set by T0, α, T_stop and moves per level:
  - our run: I = 59,000 moves, while n² = 81
  - the paper's own defaults: I ≈ 5,054 levels × 1,000 = **5,054,000** moves, for *any* n.

---

## C. Graph model, data and methodology (2:30)

### C1 · Graph model (5:15–6:05)
- **G = (V, A)**, a complete **directed** weighted graph.
- **V** = {V0, …, V8}: 9 vertices (1 depot + 8 hospitals).
- **A** = every ordered pair (i, j), i ≠ j: **72 arcs** = the drive from i to j.
- **Weight w(i, j)** = driving distance **in km** (PLACEHOLDER DATA).
- **Why directed:** 14 of the 36 pairs have d(i,j) ≠ d(j,i) (one-way streets, U-turn rules, bridges).
- Visual: `fig1_graph.png` (vertex labels only; the weights are on the next slide).

### C2 · Weight matrix and data sources (6:05–6:55)
- Visual: `fig2_weight_matrix.png` (row = FROM, column = TO).
- **Sources:** synthetic placeholder values (n/a (placeholder data)). Coordinates: Google Maps place pins.
- **Actual vs assumed:** 72 PLACEHOLDER (`data/data_sources.csv`). Assumed cells are hatched and marked * in the matrix.
- The validator checks: square matrix, zero diagonal, positive distances, ids match `locations.csv`, matrix = `data_sources.csv`.

### C3 · Methodology and parameter choice (6:55–7:45)
- Pipeline: CSVs → validator → graph (networkx) → **SA** → verification → brute force + greedy (same matrix) → 30 runs → figures.
- Parameters (`src/config.py`):

| Parameter | Value | Why |
|---|---|---|
| T0 | 14.58 km | auto: an average worse move (3.25 km) is accepted with P = 0.8 at the start |
| α | 0.98 | sensitivity study below |
| moves per level | 200 | about 7× the 28 possible swaps of 8 hospitals |
| T_stop | 0.001 km | distances are recorded to 0.1 km; at T = 0.001 a 0.1 km worse move has P = e^−100 ≈ 4e-44 |
| patience | 228 levels | no new best while T falls 100× |
| seed | 2 | reproducible run for the video |

- Why not the paper's defaults (T0 = 1000, α = 0.995, 1000 moves/level, T_stop = 1e-8)? T0 = 1000 ignores the units (km), and on our data one run took **5,054,000 moves and 15.9 s** → 24.8 km (optimal).
- α sensitivity (100 runs per value, same seeds): `fig9_alpha_sensitivity.png`

| α | max levels | moves (mean) | mean km | std | hit optimum | time/run |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.9 | 91 | 12,354 | 24.934 | 0.362 | 86% | 36 ms |
| 0.95 | 187 | 24,120 | 24.814 | 0.098 | 98% | 68 ms |
| 0.98 | 475 | 55,678 | 24.800 | 0.000 | 100% | 168 ms |
| 0.995 | 1913 | 202,126 | 24.800 | 0.000 | 100% | 610 ms |

---

## D. Python execution and results (3:45, mostly the live screen recording)

### D1 · Live run (7:45–9:45): see `docs/narration_script.md`
1. Show `data/locations.csv` and `data/distance_matrix.csv` (the input).
2. `python main.py --trace`: validation, input tables, the first 5 SA moves, the result.
3. Show the verification table and the brute-force check in the console.
4. Open `outputs/route_map.html` and the figures.

### D2 · Result route (9:45–10:25)
- **Route:** V0 → V2 → V5 → V6 → V3 → V1 → V7 → V8 → V4 → V0
- **Names:** Depot* → Hosp B* → Hosp E* → Hosp F* → Hosp C* → Hosp A* → Hosp G* → Hosp H* → Hosp D* → Depot*
- **Total distance: 24.8 km** (the initial random tour was 41.0 km)
- Verification (PASS): 4.2 + 3.5 + 1.9 + 2.9 + 1.8 + 1.5 + 4.2 + 2.8 + 2.0 = **24.8 km**
- Visual: `fig3_route_map.png` (or the live `route_map.html`) and `fig1b_route_on_graph.png`.

### D3 · Is it optimal? (10:25–11:00)
- The SA route (24.8 km) is **optimal for this instance**. This is proven by brute force, which checked all 40,320 possible tours and found no shorter one. SA by itself does not guarantee optimality; the proof comes from the exhaustive search.
- The optimal tour is unique.
- Same matrix, other methods: greedy nearest neighbour **28.3 km** (+14.1%); average random tour **40.46 km**; worst tour 54.0 km.
- 30 independent runs (paper Table 2 format), with SA reaching the optimum in **30/30** runs:

| Algorithm | Best | Worst | Average | Variance | Std Dev | Avg time | Hit optimum |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| SA (ours) | 24.8 | 24.8 | 24.800 | 0.000 | 0.000 | 0.1726 s | 100% |
| Brute force | 24.8 | 24.8 | 24.800 | 0 | 0 | 0.0492 s | 100% |
| Greedy | 28.3 | 28.3 | 28.300 | 0 | 0 | 0.0000 s | 0% |

- Visuals: `fig7_runs_vs_optimum.png`, `fig8_search_space.png` (all 40,320 tours).
- Honest note: at n = 9, brute force takes 0.05 s and one SA run about 173 ms, so exhaustive search is still cheap at this size. SA earns its place as n grows: with 20 stops brute force would need 19! ≈ 1.2 × 10¹⁷ tours, while SA's work grows only with the number of moves × n.

### D4 · How SA got there (11:00–11:30)
- `fig4_convergence.png`: the current tour jumps around at high T, then settles; the best tour reaches 24.8 km at move 13,277. The current tour can end above the best one, which is why line 13 returns the best-so-far tour.
- `fig5_acceptance.png`: the share of worse moves accepted falls from about 0.8 to 0 as T drops, matching the theory e^(−Δ/T).
- `fig6_sa_animation.gif`: the search in motion.
- Swap vs segment reversal (our extension, off by default):

| neighbour | T0 | moves (mean) | mean km | hit optimum | time/run |
| :--- | ---: | ---: | ---: | ---: | ---: |
| swap | 14.58 | 55,678 | 24.800 | 100% | 171 ms |
| 2opt | 12.03 | 54,552 | 24.800 | 100% | 192 ms |

---

## E. Conclusion and references (1:15)

### E1 · Conclusion (11:30–12:00)
- The courier's route: **Depot* → Hosp B* → Hosp E* → Hosp F* → Hosp C* → Hosp A* → Hosp G* → Hosp H* → Hosp D* → Depot* = 24.8 km**.
- That is 15.66 km (39%) shorter than an average random order, and 3.5 km (12.4%) shorter than the greedy route.
- _To be written once the real data are in (which neighbourhoods the route groups together, and why that order avoids back-tracking)._
- Because brute force checked every possible tour, this route is proven optimal for this instance. The proof comes from the exhaustive search, not from Simulated Annealing itself.

### E2 · Limitations and improvements (12:00–12:25)
- Limitations: distances are static (no traffic, time of day, or road closures); no time windows; one vehicle; the data are synthetic; small n.
- Improvements: minimise travel *time* with traffic; time windows for urgent hospitals; several vehicles (VRP); an SA + 2-opt hybrid; adaptive cooling; the Google Distance Matrix API to collect larger n automatically.

### E3 · References (12:25–12:45)
See `REFERENCES.md` (the paper, Metropolis 1953, Kirkpatrick 1983, Černý 1985, Hajek 1988, NetworkX, Matplotlib, Folium, and the data sources with access dates).

---
_Generated 2026-10-17 09:09 from data fingerprint `af6df0a76c` by `src/docs_builder.py`. Do not edit by hand; edit `docs/templates/slides_outline.md.tmpl` instead._
