# References (IEEE style)

> ⚠️ **PLACEHOLDER DATA.** Every number in this file comes from the synthetic demo dataset. Enter the real data and rerun `python main.py` before using it.

## Assigned paper (algorithm and base code)
[1] R. Luna-Garcia, T. M. C. Candano, and R. L. Caga-anan, "Performance analysis of classical algorithms for the traveling salesman problem," *The Mindanawan Journal of Mathematics*, vol. 6, no. 2, pp. 79–111, 2024, doi: 10.62071/tmjm.v6i2.716. Used for §2.5, Algorithm 2.5, Theorem 2.5, Table 2 format, Algorithm 2.3 (brute force), Algorithm 2.7 (greedy) and Appendix 4.5 (SA Python code).

## Simulated Annealing: origin and theory
[2] N. Metropolis, A. W. Rosenbluth, M. N. Rosenbluth, A. H. Teller, and E. Teller, "Equation of state calculations by fast computing machines," *J. Chem. Phys.*, vol. 21, no. 6, pp. 1087–1092, 1953, doi: 10.1063/1.1699114.

[3] S. Kirkpatrick, C. D. Gelatt, and M. P. Vecchi, "Optimization by simulated annealing," *Science*, vol. 220, no. 4598, pp. 671–680, 1983, doi: 10.1126/science.220.4598.671.

[4] V. Černý, "Thermodynamical approach to the traveling salesman problem: An efficient simulation algorithm," *J. Optim. Theory Appl.*, vol. 45, no. 1, pp. 41–51, 1985, doi: 10.1007/BF00940812.

[5] S. Geman and D. Geman, "Stochastic relaxation, Gibbs distributions, and the Bayesian restoration of images," *IEEE Trans. Pattern Anal. Mach. Intell.*, vol. PAMI-6, no. 6, pp. 721–741, 1984, doi: 10.1109/TPAMI.1984.4767596.

[6] B. Hajek, "Cooling schedules for optimal annealing," *Math. Oper. Res.*, vol. 13, no. 2, pp. 311–329, 1988, doi: 10.1287/moor.13.2.311.

[7] Fourmilab, "Simulated annealing: The travelling salesman problem." [Online]. Available: https://www.fourmilab.ch/documents/travelling/anneal/ (cited by [1] as the source of its SA approach).

[8] B. Manthey and J. van Rhijn, "Towards a lower bound for the average case runtime of simulated annealing on TSP," arXiv:2208.11444, 2022 (cited by [1] for Theorem 2.5).

## Software
[9] A. A. Hagberg, D. A. Schult, and P. J. Swart, "Exploring network structure, dynamics, and function using NetworkX," in *Proc. 7th Python in Science Conf. (SciPy 2008)*, Pasadena, CA, USA, 2008, pp. 11–15. Version used: 3.7.

[10] J. D. Hunter, "Matplotlib: A 2D graphics environment," *Comput. Sci. Eng.*, vol. 9, no. 3, pp. 90–95, 2007, doi: 10.1109/MCSE.2007.55. Version used: 3.11.2.

[11] C. R. Harris *et al.*, "Array programming with NumPy," *Nature*, vol. 585, pp. 357–362, 2020, doi: 10.1038/s41586-020-2649-2. Version used: 2.5.4.

[12] Folium contributors, "Folium: Python data, Leaflet.js maps." [Online]. Available: https://python-visualization.github.io/folium/. Version used: 0.20.0.

[13] Pillow contributors, "Pillow (PIL fork)." [Online]. Available: https://python-pillow.org. Version used: 13.0.0 (used for the animated GIF).

## Data sources
[14] Google LLC, "Google Maps," Cagayan de Oro City. [Online]. Available: https://www.google.com/maps (driving distances read on n/a (placeholder data)).

Base-map tiles of `route_map.html` and `fig3_route_map.png`: © OpenStreetMap contributors. One row per distance (source, date, time) is in `data/data_sources.csv`.

## How our code relates to [1] Appendix 4.5
Our `src/simulated_annealing.py` follows the structure of the paper's SA code: a random initial tour, a swap neighbour, the Metropolis acceptance `new < current or random() < exp((current − new)/T)`, geometric cooling `T *= cooling_rate`, two nested loops, and best-so-far tracking. Our modifications:
1. Input is a **directed distance matrix** (driving km, PLACEHOLDER DATA) instead of (x, y) coordinates with Euclidean distance; costs may differ by direction.
2. The **depot is fixed** at position 0; only the hospitals are permuted, and the tour always closes at the depot.
3. **Parameters tuned** to our data: T0 calibrated to the km scale (P ≈ 0.8 for an average worse move), α = 0.98, 200 moves per level, T_stop = 0.001 km, chosen with a sensitivity experiment, against the paper's T0 = 1000, α = 0.995, 1000 moves/level, T_stop = 1e-8.
4. The **extra stopping rules** named in the paper's text (no improvement / maximum iterations).
5. A per-move **history and trace** for the plots and the hand-worked example.
6. **Verification**: an independent edge-by-edge recount, brute force (Alg 2.3) and greedy (Alg 2.7) on the same matrix, and 30 seeded runs.
7. An optional **segment-reversal ("2-opt") neighbour** (our extension, off by default).

---
_Generated 2026-10-17 09:09 from data fingerprint `af6df0a76c` by `src/docs_builder.py`. Do not edit by hand; edit `docs/templates/REFERENCES.md.tmpl` instead._
