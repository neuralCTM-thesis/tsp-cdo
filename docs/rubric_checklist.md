# Rubric checklist: where each "evidence expected" item lives

PIT: *Algorithm Discussion and Real-Life Application of the TSP* (100 pts). Assigned algorithm: **Simulated Annealing** (paper §2.5, Algorithm 2.5, Theorem 2.5, Appendix 4.5).
Tick each box after checking it in the **final** recording.

## 1. Assigned algorithm (20 pts)
| Evidence expected | Artifact |
|---|---|
| Accurate explanation | `docs/slides_outline.md` B1 (annealing analogy; Metropolis 1953, Kirkpatrick et al. 1983, Černý 1985); README "Algorithm"; docstring of `src/simulated_annealing.py` |
| Clear procedure | B2 (Alg 2.5 lines 1–13 ↔ code functions); B3 (the two-loop structure of Appendix 4.5); every code line commented with its Alg 2.5 step number |
| Key steps and calculations | B4 hand-worked moves (Δ, T, P, r, decision) from `outputs/trace.csv`; the same moves printed live by `python main.py --trace` |
| Appropriate advantages and limitations | B5, backed by our own evidence: `fig9_alpha_sensitivity.png` (parameter sensitivity) and the 30-run spread (stochastic) |
| Correct statement about optimality | B6: "approximate/heuristic; convergence only proven for logarithmic cooling"; Theorem 2.5 explained, with I = O(n²) flagged as an assumption |

## 2. Problem and objective (10 pts)
| Evidence expected | Artifact |
|---|---|
| Relevant TSP application | A2: Red Cross blood-delivery courier in Cagayan de Oro City (illustrative scenario) |
| Clear locations, place in CDO | A3 + `fig0_locations_map.png` (locations on an OpenStreetMap base map) + `data/locations.csv` (name, address/barangay, coordinates, source, Google Maps link) |
| Starting point | V0 = Red Cross chapter office (`role = depot`) |
| Assumptions and constraints | A4 (single vehicle, no capacity limit, no service time, OpenStreetMap/OSRM driving distances with date and time; start/end at depot, each hospital once, roads only) |
| Measurable objective | A4: minimise total driving distance in km (formula shown) |

## 3. Graph model and data (15 pts)
| Evidence expected | Artifact |
|---|---|
| Clearly defined vertices | `outputs/table_vertices.csv`, A3, C1 |
| Edges and direction | C1: complete **directed** graph, n(n−1) arcs; asymmetric pairs counted (`outputs/data_quality.csv`) |
| Weights and units | km everywhere; `data/distance_matrix.csv`; colour bar labelled "km" |
| Labelled graph | `outputs/fig1_graph.png`, `outputs/fig1b_route_on_graph.png` |
| Matching data table or matrix | `outputs/fig2_weight_matrix.png` + the matrix table in `demo.ipynb` §3 |
| Data sources; actual vs assumed | `data/data_sources.csv` (ACTUAL/ASSUMED, date, time, route), hatched cells in fig2, C2 quality checks (`outputs/data_quality.csv`), REFERENCES [14]–[16] (OpenStreetMap/OSRM/Nominatim, query date) |

## 4. Methodology and Python implementation (25 pts)
| Evidence expected | Artifact |
|---|---|
| Algorithm correctly applied and implemented | `src/simulated_annealing.py`; `tests/` (57 pytest tests, incl. SA = brute force on small instances, the Metropolis rule, geometric cooling) |
| Actual code execution on the application data | live `python main.py --trace` in the video (narration script D, 8:05–11:50); `demo.ipynb` as an alternative |
| Inputs explained | console sections "INPUT 1/2"; narration 8:05 |
| Main code components explained | C3 pipeline; **C4** module table + core loop excerpt; narration 11:35 (main loop live); README "Project structure" |
| Output explained | console result, verification and statistics blocks; D2–D4 |

## 5. Solution and conclusion (20 pts)
| Evidence expected | Artifact |
|---|---|
| Valid closed tour | `src/verify.py` checks (start/end at depot, n+1 entries, each stop once), printed PASS |
| Total correctly calculated and checked | edge-by-edge table `outputs/verification_table.csv`; recomputed sum == SA total (asserted) |
| Results interpreted against the objective | E1: route order, total km, km saved vs random and greedy, geographic interpretation |
| Optimality claims supported | brute force on the same matrix (D3), `fig8_search_space.png`, 30 runs in Table 2 format (`outputs/table2_style_results.csv`, `fig7`) |
| Limitations discussed | E2 + README |

## 6. Presentation quality and duration (5 pts)
| Evidence expected | Artifact |
|---|---|
| Clear narration, logical organisation | `docs/narration_script.md` (timestamps, A→E as in the PIT guide) |
| Readable visuals and code | 15 pt+ figure fonts, high-contrast palette, console under 100 columns |
| 10–15 minutes | planned 13:05; timing in `docs/narration_script.md` |

## 7. Submission and references (5 pts)
| Evidence expected | Artifact |
|---|---|
| Video | you record it (checklist) |
| Runnable Python file or notebook | `main.py`, `demo.ipynb`, `requirements.txt`, README "Quick start" |
| Identifiable dataset | `data/*.csv` (separate from the code; README says where) |
| Algorithm, code and data credited | `REFERENCES.md` + slide E3; code header credits Appendix 4.5 and lists our modifications |

## Consistency (PIT: "graph, data, Python inputs, and reported results are consistent")
`main.py` and `demo.ipynb` read the same `data/*.csv` and call the same functions, so the graph, matrix, inputs and results always agree.
