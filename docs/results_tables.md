# Results tables (copy these into the slides)

> ⚠️ **PLACEHOLDER DATA.** Every number in this file comes from the synthetic demo dataset. Enter the real data and rerun `python main.py` before using it.

Data fingerprint `af6df0a76c`; generated 2026-10-17 09:09.

## 1. Vertices
| Vertex | Name | Short name | Role | Address | Lat, Lon |
| :--- | :--- | :--- | :--- | :--- | :--- |
| V0 | PLACEHOLDER Depot (Red Cross chapter office) | Depot* | depot | PLACEHOLDER - synthetic point | 8.47400, 124.64600 |
| V1 | PLACEHOLDER Hospital A | Hosp A* | stop | PLACEHOLDER - synthetic point | 8.45522, 124.64227 |
| V2 | PLACEHOLDER Hospital B | Hosp B* | stop | PLACEHOLDER - synthetic point | 8.47573, 124.67236 |
| V3 | PLACEHOLDER Hospital C | Hosp C* | stop | PLACEHOLDER - synthetic point | 8.46486, 124.64931 |
| V4 | PLACEHOLDER Hospital D | Hosp D* | stop | PLACEHOLDER - synthetic point | 8.46614, 124.63579 |
| V5 | PLACEHOLDER Hospital E | Hosp E* | stop | PLACEHOLDER - synthetic point | 8.45105, 124.67151 |
| V6 | PLACEHOLDER Hospital F | Hosp F* | stop | PLACEHOLDER - synthetic point | 8.44746, 124.65854 |
| V7 | PLACEHOLDER Hospital G | Hosp G* | stop | PLACEHOLDER - synthetic point | 8.45054, 124.63490 |
| V8 | PLACEHOLDER Hospital H | Hosp H* | stop | PLACEHOLDER - synthetic point | 8.47237, 124.61626 |

## 2. Directed distance matrix (km): row = FROM, column = TO
| from \ to | V0 | V1 | V2 | V3 | V4 | V5 | V6 | V7 | V8 |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **V0** | – | 3.4 | 4.2 | 1.5 | 2.0 | 6.5 | 5.7 | 4.2 | 4.9 |
| **V1** | 3.4 | – | 5.6 | 3.2 | 2.0 | 5.2 | 3.0 | 1.5 | 4.7 |
| **V2** | 4.2 | 5.6 | – | 4.3 | 7.6 | 3.5 | 4.5 | 7.7 | 9.6 |
| **V3** | 1.5 | 1.8 | 5.7 | – | 2.0 | 4.5 | 3.7 | 3.2 | 5.2 |
| **V4** | 2.0 | 2.0 | 6.6 | 2.9 | – | 6.9 | 4.2 | 2.4 | 2.8 |
| **V5** | 5.8 | 4.6 | 4.4 | 4.5 | 6.3 | – | 1.9 | 5.9 | 8.2 |
| **V6** | 4.4 | 3.0 | 4.5 | 2.9 | 4.2 | 1.9 | – | 4.4 | 7.8 |
| **V7** | 4.2 | 2.3 | 9.1 | 3.2 | 2.4 | 5.9 | 3.6 | – | 4.2 |
| **V8** | 4.9 | 4.7 | 9.6 | 5.2 | 2.8 | 8.2 | 7.8 | 5.5 | – |

\* = ASSUMED (not measured). Provenance: 72 PLACEHOLDER. Asymmetric pairs: 14 of 36.

## 3. Simulated Annealing parameters
| Parameter | Value |
|---|---|
| T0 | 14.58 km (average worse move 3.25 km accepted with P = 0.8) |
| α | 0.98 |
| moves per temperature | 200 |
| T_stop | 0.001 km |
| patience | 228 levels (T falls 100×) |
| neighbour | swap |
| seed | 2 |

## 4. Result of the presentation run (seed 2)
- Route: **V0 → V2 → V5 → V6 → V3 → V1 → V7 → V8 → V4 → V0**
- Names: Depot* → Hosp B* → Hosp E* → Hosp F* → Hosp C* → Hosp A* → Hosp G* → Hosp H* → Hosp D* → Depot*
- Total: **24.8 km** (initial random tour 41.0 km: V0 → V6 → V4 → V5 → V2 → V3 → V7 → V8 → V1 → V0)
- 59,000 moves in 295 levels; best found at move 13,277; stopped because: no improvement for 228 temperature levels (T fell 100x); 222 ms.

## 5. Verification (edge by edge)
- ✅ starts at depot (first vertex = 0)
- ✅ ends at depot (last vertex = 0)
- ✅ n + 1 entries (10 entries, expected 10)
- ✅ every stop exactly once (missing=none, repeated=none)

| # | From | To | km | Running km | Data |
| ---: | :--- | :--- | ---: | ---: | :--- |
| 1 | V0 Depot* | V2 Hosp B* | 4.2 | 4.2 | PLACEHOLDER |
| 2 | V2 Hosp B* | V5 Hosp E* | 3.5 | 7.7 | PLACEHOLDER |
| 3 | V5 Hosp E* | V6 Hosp F* | 1.9 | 9.6 | PLACEHOLDER |
| 4 | V6 Hosp F* | V3 Hosp C* | 2.9 | 12.5 | PLACEHOLDER |
| 5 | V3 Hosp C* | V1 Hosp A* | 1.8 | 14.3 | PLACEHOLDER |
| 6 | V1 Hosp A* | V7 Hosp G* | 1.5 | 15.8 | PLACEHOLDER |
| 7 | V7 Hosp G* | V8 Hosp H* | 4.2 | 20.0 | PLACEHOLDER |
| 8 | V8 Hosp H* | V4 Hosp D* | 2.8 | 22.8 | PLACEHOLDER |
| 9 | V4 Hosp D* | V0 Depot* | 2.0 | 24.8 | PLACEHOLDER |

Sum: 4.2 + 3.5 + 1.9 + 2.9 + 1.8 + 1.5 + 4.2 + 2.8 + 2.0 = **24.8 km**

## 6. Optimality evidence
The SA route (24.8 km) is **optimal for this instance**. This is proven by brute force, which checked all 40,320 possible tours and found no shorter one. SA by itself does not guarantee optimality; the proof comes from the exhaustive search.

- Brute force: (9−1)! = 8! = 40,320 tours, optimum 24.8 km (0.05 s). The optimal tour is unique.
- Greedy nearest neighbour: 28.3 km (+14.1%): V0 → V3 → V1 → V7 → V4 → V8 → V6 → V5 → V2 → V0
- Average random tour: 40.46 km; worst tour: 54.0 km.

## 7. 30 independent runs (paper Table 2 format, km)
| Algorithm | Best | Worst | Average | Variance | Std Dev | Avg time | Hit optimum |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| SA (ours) | 24.8 | 24.8 | 24.800 | 0.000 | 0.000 | 0.1726 s | 100% |
| Brute force | 24.8 | 24.8 | 24.800 | 0 | 0 | 0.0492 s | 100% |
| Greedy | 28.3 | 28.3 | 28.300 | 0 | 0 | 0.0000 s | 0% |

Mean gap 0.00%, worst gap 0.00%; variance and std dev are sample statistics (n − 1).

## 8. Cooling-rate sensitivity (100 runs per value)
| α | max levels | moves (mean) | mean km | std | hit optimum | time/run |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.9 | 91 | 12,354 | 24.934 | 0.362 | 86% | 36 ms |
| 0.95 | 187 | 24,120 | 24.814 | 0.098 | 98% | 68 ms |
| 0.98 | 475 | 55,678 | 24.800 | 0.000 | 100% | 168 ms |
| 0.995 | 1913 | 202,126 | 24.800 | 0.000 | 100% | 610 ms |

Paper defaults (T0 = 1000, α = 0.995, 1000 moves/level, T_stop = 1e-08): **5,054,000 moves, 5,054 levels, 15.9 s** → 24.8 km (optimal).

## 9. Neighbour move: swap (paper) vs segment reversal (our extension)
| neighbour | T0 | moves (mean) | mean km | hit optimum | time/run |
| :--- | ---: | ---: | ---: | ---: | ---: |
| swap | 14.58 | 55,678 | 24.800 | 100% | 171 ms |
| 2opt | 12.03 | 54,552 | 24.800 | 100% | 192 ms |

## 10. Hand-worked trace (first moves of the presentation run)
Initial tour cost: d(V0,V6) + d(V6,V4) + d(V4,V5) + d(V5,V2) + d(V2,V3) + d(V3,V7) + d(V7,V8) + d(V8,V1) + d(V1,V0)
= 5.7 + 4.2 + 6.9 + 4.4 + 4.3 + 3.2 + 4.2 + 4.7 + 3.4 = **41.0 km**

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

## 11. Google Maps link for the whole route
https://www.google.com/maps/dir/?api=1&travelmode=driving&origin=8.474000,124.646000&destination=8.474000,124.646000&waypoints=8.475726,124.672361%7C8.451052,124.671514%7C8.447456,124.658543%7C8.464863,124.649306%7C8.455220,124.642271%7C8.450543,124.634897%7C8.472369,124.616260%7C8.466136,124.635788

---
_Generated 2026-10-17 09:09 from data fingerprint `af6df0a76c` by `src/docs_builder.py`. Do not edit by hand; edit `docs/templates/results_tables.md.tmpl` instead._
