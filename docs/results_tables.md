# Results tables (copy these into the slides)


Data fingerprint `c652b67ace`; generated 2026-10-17 19:10.

## 1. Vertices
| Vertex | Name | Short name | Role | Address | Lat, Lon |
| :--- | :--- | :--- | :--- | :--- | :--- |
| V0 | Philippine Red Cross Misamis Oriental-Cagayan de Oro Chapter | PRC | depot | Red Cross Building, Capitol Compound, Brgy. 27, Cagayan de Oro City | 8.48477, 124.64926 |
| V1 | Allied Care Experts (ACE) Medical Center - Cagayan de Oro | ACE | stop | Sta. Cruz 1, Pimentel St., Brgy. Lapasan, Cagayan de Oro City | 8.48092, 124.65929 |
| V2 | Polymedic Medical Plaza | PMP Kausw | stop | Kauswagan Highway, Kauswagan, Cagayan de Oro City | 8.49828, 124.63043 |
| V3 | Cagayan de Oro Polymedic General Hospital | PGH Velez | stop | Don Apolinar Velez St., Cagayan de Oro City | 8.48243, 124.64564 |
| V4 | Sabal Hospital, Inc. (Doctors Sabal Hospital) | Sabal | stop | 292 Don Apolinar Velez St., Cagayan de Oro City | 8.48615, 124.64787 |
| V5 | Maria Reyna-Xavier University Hospital | MRXUH | stop | Hayes St., Cagayan de Oro City | 8.47631, 124.65520 |
| V6 | Madonna and Child Hospital | Madonna | stop | J.V. Seriña St., Brgy. Carmen, Cagayan de Oro City | 8.47721, 124.63523 |
| V7 | Northern Mindanao Medical Center | NMMC | stop | Capitol Compound, Capitol Road, Cagayan de Oro City | 8.48539, 124.64964 |
| V8 | J.R. Borja General Hospital | JRBGH | stop | J.V. Seriña St., Brgy. Carmen, Cagayan de Oro City | 8.48171, 124.62809 |

## 2. Directed distance matrix (km): row = FROM, column = TO
| from \ to | V0 | V1 | V2 | V3 | V4 | V5 | V6 | V7 | V8 |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **V0** | – | 1.67 | 2.81 | 0.6 | 0.23 | 1.62 | 2.46 | 0.14 | 3.23 |
| **V1** | 1.87 | – | 4.22 | 2.2 | 1.69 | 1.26 | 4.06 | 1.89 | 4.63 |
| **V2** | 2.94 | 4.35 | – | 3.25 | 2.74 | 4.58 | 3.57 | 3.0 | 3.71 |
| **V3** | 0.82 | 2.36 | 3.37 | – | 0.73 | 1.96 | 1.85 | 1.03 | 2.37 |
| **V4** | 0.23 | 1.68 | 2.63 | 0.51 | – | 1.91 | 2.37 | 0.29 | 3.05 |
| **V5** | 1.66 | 1.21 | 4.48 | 1.63 | 1.95 | – | 2.71 | 1.63 | 3.22 |
| **V6** | 2.43 | 4.01 | 3.35 | 1.85 | 2.33 | 2.62 | – | 2.62 | 1.0 |
| **V7** | 0.14 | 1.62 | 2.87 | 0.8 | 0.29 | 1.62 | 2.66 | – | 3.29 |
| **V8** | 3.23 | 4.65 | 3.63 | 2.37 | 3.03 | 3.21 | 1.04 | 3.29 | – |

\* = ASSUMED (not measured). Provenance: 72 ACTUAL. Asymmetric pairs: 29 of 36.

## 3. Simulated Annealing parameters
| Parameter | Value |
|---|---|
| T0 | 6.61 km (average worse move 1.47 km accepted with P = 0.8) |
| α | 0.98 |
| moves per temperature | 200 |
| T_stop | 0.001 km |
| patience | 228 levels (T falls 100×) |
| neighbour | swap |
| seed | 1 |

## 4. Result of the presentation run (seed 1)
- Route: **V0 → V7 → V1 → V5 → V3 → V6 → V8 → V2 → V4 → V0**
- Names: PRC → NMMC → ACE → MRXUH → PGH Velez → Madonna → JRBGH → PMP Kausw → Sabal → PRC
- Total: **14.1 km** (initial random tour 16.32 km: V0 → V4 → V7 → V2 → V6 → V8 → V1 → V5 → V3 → V0)
- 56,200 moves in 281 levels; best found at move 10,506; stopped because: no improvement for 228 temperature levels (T fell 100x); 101 ms.

## 5. Verification (edge by edge)
- ✅ starts at depot (first vertex = 0)
- ✅ ends at depot (last vertex = 0)
- ✅ n + 1 entries (10 entries, expected 10)
- ✅ every stop exactly once (missing=none, repeated=none)

| # | From | To | km | Running km | Data |
| ---: | :--- | :--- | ---: | ---: | :--- |
| 1 | V0 PRC | V7 NMMC | 0.14 | 0.14 | ACTUAL |
| 2 | V7 NMMC | V1 ACE | 1.62 | 1.76 | ACTUAL |
| 3 | V1 ACE | V5 MRXUH | 1.26 | 3.02 | ACTUAL |
| 4 | V5 MRXUH | V3 PGH Velez | 1.63 | 4.65 | ACTUAL |
| 5 | V3 PGH Velez | V6 Madonna | 1.85 | 6.5 | ACTUAL |
| 6 | V6 Madonna | V8 JRBGH | 1.0 | 7.5 | ACTUAL |
| 7 | V8 JRBGH | V2 PMP Kausw | 3.63 | 11.13 | ACTUAL |
| 8 | V2 PMP Kausw | V4 Sabal | 2.74 | 13.87 | ACTUAL |
| 9 | V4 Sabal | V0 PRC | 0.23 | 14.1 | ACTUAL |

Sum: 0.14 + 1.62 + 1.26 + 1.63 + 1.85 + 1.0 + 3.63 + 2.74 + 0.23 = **14.1 km**

## 6. Optimality evidence
The SA route (14.1 km) is **optimal for this instance**. This is proven by brute force, which checked all 40,320 possible tours and found no shorter one. SA by itself does not guarantee optimality; the proof comes from the exhaustive search.

- Brute force: (9−1)! = 8! = 40,320 tours, optimum 14.1 km (0.02 s). The optimal tour is unique.
- Greedy nearest neighbour: 15.37 km (+9.0%): V0 → V7 → V4 → V3 → V6 → V8 → V5 → V1 → V2 → V0
- Average random tour: 20.79 km; worst tour: 25.52 km.

## 7. 30 independent runs (paper Table 2 format, km)
| Algorithm | Best | Worst | Average | Variance | Std Dev | Avg time | Hit optimum |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| SA (ours) | 14.1 | 14.1 | 14.100 | 0.000 | 0.000 | 0.0881 s | 100% |
| Brute force | 14.1 | 14.1 | 14.100 | 0 | 0 | 0.0221 s | 100% |
| Greedy | 15.37 | 15.37 | 15.370 | 0 | 0 | 0.0000 s | 0% |

Mean gap 0.00%, worst gap 0.00%; variance and std dev are sample statistics (n − 1).

## 8. Cooling-rate sensitivity (100 runs per value)
| α | max levels | moves (mean) | mean km | std | hit optimum | time/run |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.9 | 84 | 12,720 | 14.150 | 0.092 | 71% | 73 ms |
| 0.95 | 172 | 25,042 | 14.110 | 0.041 | 93% | 112 ms |
| 0.98 | 436 | 57,042 | 14.100 | 0.000 | 100% | 234 ms |
| 0.995 | 1755 | 205,076 | 14.100 | 0.000 | 100% | 692 ms |

Paper defaults (T0 = 1000, α = 0.995, 1000 moves/level, T_stop = 1e-08): **5,054,000 moves, 5,054 levels, 14.2 s** → 14.1 km (optimal).

## 9. Neighbour move: swap (paper) vs segment reversal (our extension)
| neighbour | T0 | moves (mean) | mean km | hit optimum | time/run |
| :--- | ---: | ---: | ---: | ---: | ---: |
| swap | 6.61 | 57,042 | 14.100 | 100% | 217 ms |
| 2opt | 5.02 | 54,372 | 14.100 | 100% | 319 ms |

## 10. Hand-worked trace (first moves of the presentation run)
Initial tour cost: d(V0,V4) + d(V4,V7) + d(V7,V2) + d(V2,V6) + d(V6,V8) + d(V8,V1) + d(V1,V5) + d(V5,V3) + d(V3,V0)
= 0.23 + 0.29 + 2.87 + 3.57 + 1.0 + 4.65 + 1.26 + 1.63 + 0.82 = **16.32 km**

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

## 11. Google Maps link for the whole route
https://www.google.com/maps/dir/?api=1&travelmode=driving&origin=8.484769,124.649264&destination=8.484769,124.649264&waypoints=8.485392,124.649638%7C8.480921,124.659294%7C8.476308,124.655197%7C8.482427,124.645639%7C8.477215,124.635234%7C8.481707,124.628092%7C8.498281,124.630430%7C8.486151,124.647875

---
_Generated 2026-10-17 19:10 from data fingerprint `c652b67ace` by `src/docs_builder.py`. Do not edit by hand; edit `docs/templates/results_tables.md.tmpl` instead._
