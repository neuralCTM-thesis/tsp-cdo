# Slides outline: Simulated Annealing for a Real-Life TSP in Cagayan de Oro City


Target length **12–13 min** (PIT allows 10–15). Section timing follows the PIT guide:

| Section | Slides | Time |
|---|---|---|
| A. Introduction, problem, objective | A1–A4 | 0:00–2:30 |
| B. Assigned algorithm (Simulated Annealing) | B1–B6 | 2:30–5:15 |
| C. Graph model, data, methodology | C1–C3 | 5:15–7:45 |
| D. Python execution and results (live) | D1–D4 | 7:45–11:30 |
| E. Conclusion and references | E1–E3 | 11:30–12:45 |

Figures are in `outputs/`. Every figure, table and number below comes from the same data (fingerprint `c652b67ace`).

---

## A. Introduction, problem and objective (2:30)

### A1 · Title (0:00–0:15)
- **Simulated Annealing for the Traveling Salesperson Problem: Routing Blood Deliveries in Cagayan de Oro City**
- Hans Matthew Del Mundo · Vin Marcus Gerebise · Gerald Helbiro Jr. · Ira Chloie Narisma
- Computer Science CS4A · CS414 Graph Theory · [Instructor] · [Date]
- Assigned algorithm: Simulated Annealing (Luna-Garcia, Candano & Caga-anan, TMJM 6(2), 2024, §2.5)

### A2 · The real-life problem (0:15–1:00)
- Illustrative scenario: a **Philippine Red Cross Misamis Oriental** courier leaves the chapter office with blood units, delivers to **8 hospitals** in Cagayan de Oro City, **each exactly once**, and returns to base.
- Why this is a TSP: one vehicle, a fixed set of stops, a closed tour, and a total length to minimise.
- Why it matters: shorter routes mean blood reaches hospitals sooner and the vehicle uses less fuel.
- Visual: `outputs/route_map.html` (screenshot showing only the markers) or `fig3_route_map.png`.

### A3 · Locations (vertices) (1:00–1:45)
- Start and end: **V0 = Philippine Red Cross Misamis Oriental-Cagayan de Oro Chapter** (depot).
- Hospitals:
  - **V1** Allied Care Experts (ACE) Medical Center - Cagayan de Oro
  - **V2** Polymedic Medical Plaza
  - **V3** Cagayan de Oro Polymedic General Hospital
  - **V4** Sabal Hospital, Inc. (Doctors Sabal Hospital)
  - **V5** Maria Reyna-Xavier University Hospital
  - **V6** Madonna and Child Hospital
  - **V7** Northern Mindanao Medical Center
  - **V8** J.R. Borja General Hospital
- Area: Cagayan de Oro City proper. Coordinates: OpenStreetMap (Nominatim geocoder and Overpass API) (`data/locations.csv`).

### A4 · Objective, assumptions and constraints (1:45–2:30)
- **Objective:** minimise the total **driving distance (km)**:
  `min  d(V0,π1) + d(π1,π2) + … + d(π8,V0)` over every order π of the hospitals.
- **Constraints:** start and end at V0; visit every hospital exactly once; travel on roads only.
- **Assumptions:** a single vehicle with no capacity limit; time spent at each stop is ignored; distances are *driving* distances: the length of the route chosen by the OSRM car router on the OpenStreetMap road network, one request per direction, obtained on 2026-10-17 (18:15–18:18, Philippine time). The distances are fixed (no traffic).
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
| 3 | Set a high initial temperature T | `T = params.t0` = **6.61 km** (calibrated, see C3) |
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
- Our run used **281 temperature levels × 200 moves = 56,200 moves**.

### B4 · The acceptance rule on our data (hand-worked, from `outputs/trace.csv`) (4:05–4:35)
Initial random tour cost (Alg 2.5 step 2):
`d(V0,V4) + d(V4,V7) + d(V7,V2) + d(V2,V6) + d(V6,V8) + d(V8,V1) + d(V1,V5) + d(V5,V3) + d(V3,V0)
= 0.23 + 0.29 + 2.87 + 3.57 + 1.0 + 4.65 + 1.26 + 1.63 + 0.82 = **16.32 km**`

**Move 1** (T = 6.6100 km): swap positions 6 and 8 (V1 ↔ V3)
- current: V0 → V4 → V7 → V2 → V6 → V8 → V1 → V5 → V3 → V0 = 16.32 km
- new: V0 → V4 → V7 → V2 → V6 → V8 → V3 → V5 → V1 → V0 = 15.37 km
- Δ = 15.37 − 16.32 = -0.95 km
- Δ < 0 → shorter tour → **ACCEPT** (Alg 2.5 steps 6–7; no random number)

**Move 2** (T = 6.6100 km): swap positions 7 and 8 (V5 ↔ V1)
- current: V0 → V4 → V7 → V2 → V6 → V8 → V3 → V5 → V1 → V0 = 15.37 km
- new: V0 → V4 → V7 → V2 → V6 → V8 → V3 → V1 → V5 → V0 = 15.61 km
- Δ = 15.61 − 15.37 = +0.24 km
- P = e^(−Δ/T) = e^(−0.24 / 6.6100) = **0.9643** (Alg 2.5 step 9)
- r = 0.2100 → r < P → **ACCEPT** the worse tour

**Move 3** (T = 6.6100 km): swap positions 1 and 8 (V4 ↔ V5)
- current: V0 → V4 → V7 → V2 → V6 → V8 → V3 → V1 → V5 → V0 = 15.61 km
- new: V0 → V5 → V7 → V2 → V6 → V8 → V3 → V1 → V4 → V0 = 17.34 km
- Δ = 17.34 − 15.61 = +1.73 km
- P = e^(−Δ/T) = e^(−1.73 / 6.6100) = **0.7697** (Alg 2.5 step 9)
- r = 0.8933 → r ≥ P → **REJECT**, keep the current tour

**Move 4** (T = 6.6100 km): swap positions 4 and 7 (V6 ↔ V1)
- current: V0 → V4 → V7 → V2 → V6 → V8 → V3 → V1 → V5 → V0 = 15.61 km
- new: V0 → V4 → V7 → V2 → V1 → V8 → V3 → V6 → V5 → V0 = 20.87 km
- Δ = 20.87 − 15.61 = +5.26 km
- P = e^(−Δ/T) = e^(−5.26 / 6.6100) = **0.4512** (Alg 2.5 step 9)
- r = 0.6074 → r ≥ P → **REJECT**, keep the current tour

**Move 5** (T = 6.6100 km): swap positions 1 and 6 (V4 ↔ V3)
- current: V0 → V4 → V7 → V2 → V6 → V8 → V3 → V1 → V5 → V0 = 15.61 km
- new: V0 → V3 → V7 → V2 → V6 → V8 → V4 → V1 → V5 → V0 = 16.7 km
- Δ = 16.7 − 15.61 = +1.09 km
- P = e^(−Δ/T) = e^(−1.09 / 6.6100) = **0.8480** (Alg 2.5 step 9)
- r = 0.4454 → r < P → **ACCEPT** the worse tour

- The key idea: at high T, even clearly worse tours are often accepted, so the search can climb out of local optima. As T drops, worse tours are almost never accepted.

### B5 · Advantages and limitations (4:35–4:55)
**Advantages**
- Escapes local optima by sometimes accepting worse tours (unlike greedy or pure hill-climbing).
- Simple: the whole method is one short function (`simulated_annealing()`), with no gradients and no problem-specific rules.
- Fast in practice: about 88 ms per run on our data (30-run mean).
- Works directly on a distance matrix, including **asymmetric** (one-way) distances.

**Limitations**
- Sensitive to its parameters (T0, α, moves per level, stopping rule); see the α experiment in C3.
- Stochastic: different seeds can give different answers, so we report 30 runs.
- **No optimality guarantee in practice.** Convergence to the optimum is proven only for logarithmic cooling (T_k ≈ c / log k; Geman & Geman 1984; Hajek 1988), which is far too slow to use.

### B6 · Optimality and time complexity (Theorem 2.5) (4:55–5:15)
- **SA is an approximate (heuristic) method.** It returns the best tour it *found*, not a proven optimum.
- **Theorem 2.5:** T(n) = O(n³). The reasoning: each move costs O(n) (swap O(1) + recompute the n arcs), and I moves give **O(I · n)**.
- **I = O(n²) is the authors' assumption, not a property of SA.** In practice I is set by T0, α, T_stop and moves per level:
  - our run: I = 56,200 moves, while n² = 81
  - the paper's own defaults: I ≈ 5,054 levels × 1,000 = **5,054,000** moves, for *any* n.

---

## C. Graph model, data and methodology (2:30)

### C1 · Graph model (5:15–6:05)
- **G = (V, A)**, a complete **directed** weighted graph.
- **V** = {V0, …, V8}: 9 vertices (1 depot + 8 hospitals).
- **A** = every ordered pair (i, j), i ≠ j: **72 arcs** = the drive from i to j.
- **Weight w(i, j)** = driving distance **in km** (OpenStreetMap/OSRM).
- **Why directed:** 29 of the 36 pairs have d(i,j) ≠ d(j,i) (one-way streets, U-turn rules, bridges).
- Visual: `fig1_graph.png` (vertex labels only; the weights are on the next slide).

### C2 · Weight matrix and data sources (6:05–6:55)
- Visual: `fig2_weight_matrix.png` (row = FROM, column = TO).
- **Sources:** the length of the route chosen by the OSRM car router on the OpenStreetMap road network, one request per direction, obtained on 2026-10-17 (18:15–18:18, Philippine time). Coordinates: OpenStreetMap (Nominatim geocoder and Overpass API).
- **Actual vs assumed:** 72 ACTUAL (`data/data_sources.csv`). Assumed cells are hatched and marked * in the matrix.
- The validator checks: square matrix, zero diagonal, positive distances, ids match `locations.csv`, matrix = `data_sources.csv`.

### C3 · Methodology and parameter choice (6:55–7:45)
- Pipeline: CSVs → validator → graph (networkx) → **SA** → verification → brute force + greedy (same matrix) → 30 runs → figures.
- Parameters (`src/config.py`):

| Parameter | Value | Why |
|---|---|---|
| T0 | 6.61 km | auto: an average worse move (1.47 km) is accepted with P = 0.8 at the start |
| α | 0.98 | sensitivity study below |
| moves per level | 200 | about 7× the 28 possible swaps of 8 hospitals |
| T_stop | 0.001 km | distances are recorded to 0.01 km; at T = 0.001 a 0.01 km worse move has P = e^−10 ≈ 5e-05 |
| patience | 228 levels | no new best while T falls 100× |
| seed | 1 | reproducible run for the video |

- Why not the paper's defaults (T0 = 1000, α = 0.995, 1000 moves/level, T_stop = 1e-8)? T0 = 1000 ignores the units (km), and on our data one run took **5,054,000 moves and 14.2 s** → 14.1 km (optimal).
- α sensitivity (100 runs per value, same seeds): `fig9_alpha_sensitivity.png`

| α | max levels | moves (mean) | mean km | std | hit optimum | time/run |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.9 | 84 | 12,720 | 14.150 | 0.092 | 71% | 73 ms |
| 0.95 | 172 | 25,042 | 14.110 | 0.041 | 93% | 112 ms |
| 0.98 | 436 | 57,042 | 14.100 | 0.000 | 100% | 234 ms |
| 0.995 | 1755 | 205,076 | 14.100 | 0.000 | 100% | 692 ms |

---

## D. Python execution and results (3:45, mostly the live screen recording)

### D1 · Live run (7:45–9:45): see `docs/narration_script.md`
1. Show `data/locations.csv` and `data/distance_matrix.csv` (the input).
2. `python main.py --trace`: validation, input tables, the first 5 SA moves, the result.
3. Show the verification table and the brute-force check in the console.
4. Open `outputs/route_map.html` and the figures.

### D2 · Result route (9:45–10:25)
- **Route:** V0 → V7 → V1 → V5 → V3 → V6 → V8 → V2 → V4 → V0
- **Names:** PRC → NMMC → ACE → MRXUH → PGH Velez → Madonna → JRBGH → PMP Kausw → Sabal → PRC
- **Total distance: 14.1 km** (the initial random tour was 16.32 km)
- Verification (PASS): 0.14 + 1.62 + 1.26 + 1.63 + 1.85 + 1.0 + 3.63 + 2.74 + 0.23 = **14.1 km**
- Visual: `fig3_route_map.png` (or the live `route_map.html`) and `fig1b_route_on_graph.png`.

### D3 · Is it optimal? (10:25–11:00)
- The SA route (14.1 km) is **optimal for this instance**. This is proven by brute force, which checked all 40,320 possible tours and found no shorter one. SA by itself does not guarantee optimality; the proof comes from the exhaustive search.
- The optimal tour is unique.
- Same matrix, other methods: greedy nearest neighbour **15.37 km** (+9.0%); average random tour **20.79 km**; worst tour 25.52 km.
- 30 independent runs (paper Table 2 format), with SA reaching the optimum in **30/30** runs:

| Algorithm | Best | Worst | Average | Variance | Std Dev | Avg time | Hit optimum |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| SA (ours) | 14.1 | 14.1 | 14.100 | 0.000 | 0.000 | 0.0885 s | 100% |
| Brute force | 14.1 | 14.1 | 14.100 | 0 | 0 | 0.0220 s | 100% |
| Greedy | 15.37 | 15.37 | 15.370 | 0 | 0 | 0.0000 s | 0% |

- Visuals: `fig7_runs_vs_optimum.png`, `fig8_search_space.png` (all 40,320 tours).
- Honest note: at n = 9, brute force takes 0.02 s and one SA run about 88 ms, so exhaustive search is still cheap at this size. SA earns its place as n grows: with 20 stops brute force would need 19! ≈ 1.2 × 10¹⁷ tours, while SA's work grows only with the number of moves × n.

### D4 · How SA got there (11:00–11:30)
- `fig4_convergence.png`: the current tour jumps around at high T, then settles; the best tour reaches 14.1 km at move 10,506. The current tour can end above the best one, which is why line 13 returns the best-so-far tour.
- `fig5_acceptance.png`: the share of worse moves accepted falls from about 0.8 to 0 as T drops, matching the theory e^(−Δ/T).
- `fig6_sa_animation.gif`: the search in motion.
- Swap vs segment reversal (our extension, off by default):

| neighbour | T0 | moves (mean) | mean km | hit optimum | time/run |
| :--- | ---: | ---: | ---: | ---: | ---: |
| swap | 6.61 | 57,042 | 14.100 | 100% | 217 ms |
| 2opt | 5.02 | 54,372 | 14.100 | 100% | 319 ms |

---

## E. Conclusion and references (1:15)

### E1 · Conclusion (11:30–12:00)
- The courier's route: **PRC → NMMC → ACE → MRXUH → PGH Velez → Madonna → JRBGH → PMP Kausw → Sabal → PRC = 14.1 km**.
- That is 6.69 km (32%) shorter than an average random order, and 1.27 km (8.3%) shorter than the greedy route.
- The route makes sense on the map: it visits each part of the city once and never doubles back. It leaves the Capitol compound through NMMC, next door, swings east to ACE in Lapasan and south to Maria Reyna in Camaman-an, then comes back through downtown at Polymedic on Velez Street. It then crosses the river to Carmen, where Madonna and J.R. Borja are only 1 kilometre apart on the same street, continues north to Polymedic in Kauswagan, the most remote stop, and returns to Sabal, beside the Red Cross office, for the last 0.23 kilometres. The greedy route does the opposite: it takes the nearest hospitals first and leaves Kauswagan for last, so it has to drive 4.22 kilometres from ACE on the east side to reach it.
- Because brute force checked every possible tour, this route is proven optimal for this instance. The proof comes from the exhaustive search, not from Simulated Annealing itself.

### E2 · Limitations and improvements (12:00–12:25)
- Limitations: distances are static (no traffic, time of day, or road closures); no time windows; one vehicle; we depend on OpenStreetMap's road data and on OSRM's choice of route; small n.
- Improvements: minimise travel *time* with traffic; time windows for urgent hospitals; several vehicles (VRP); an SA + 2-opt hybrid; adaptive cooling; the Google Distance Matrix API to collect larger n automatically.

### E3 · References (12:25–12:45)
See `REFERENCES.md` (the paper, Metropolis 1953, Kirkpatrick 1983, Černý 1985, Hajek 1988, NetworkX, Matplotlib, Folium, and the data sources with access dates).

---
_Generated 2026-10-17 18:49 from data fingerprint `c652b67ace` by `src/docs_builder.py`. Do not edit by hand; edit `docs/templates/slides_outline.md.tmpl` instead._
