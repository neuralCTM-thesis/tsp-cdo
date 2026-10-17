# Narration script, about 12:45


How to read this script:
- **[SHOW]** is what is on screen.
- **[TYPE]** is what you type during the live part.
- Plain paragraphs are spoken. At roughly 140 words a minute, each block fits its time slot.
- If you are presenting as a team, split it by section (A–E).
- Every number here comes from the run with data fingerprint `c652b67ace`. Rerun `python main.py` after any data change and this file updates itself.

---

## A. Introduction, problem, objective (0:00–2:30)

**0:00 [SHOW] Slide A1, title**

Good day. We are Hans Matthew Del Mundo, Vin Marcus Gerebise, Gerald Helbiro Jr. and Ira Chloie Narisma, and our assigned algorithm is Simulated Annealing, from the paper "Performance Analysis of Classical Algorithms for the Traveling Salesman Problem" by Luna-Garcia, Candano and Caga-anan. We use it to solve a real routing problem here in Cagayan de Oro City.

**0:15 [SHOW] Slide A2, the problem**

Our scenario is illustrative but realistic. A courier of the Philippine Red Cross Misamis Oriental chapter leaves the chapter office with blood units. The courier must deliver to 8 hospitals in the city, visit each hospital exactly once, and come back to the office. That is exactly the Traveling Salesperson Problem: one vehicle, a fixed set of stops, a closed tour, and a total length we want as small as possible. A shorter route means the blood arrives sooner and the vehicle uses less fuel.

**1:00 [SHOW] Slide A3, the locations**

These are our 9 locations. V0 is the starting point, Philippine Red Cross Misamis Oriental-Cagayan de Oro Chapter. V1 to V8 are the hospitals. The coordinates come from OpenStreetMap (Nominatim geocoder and Overpass API), and each place is recorded in our data file with its address and a Google Maps link.

**1:45 [SHOW] Slide A4, objective, assumptions, constraints**

Our objective is measurable: minimise the total driving distance in kilometres. The constraints are that the route starts and ends at the depot, visits every hospital exactly once, and travels on roads only. We assume one vehicle with no capacity limit, we ignore the time spent at each stop, and we use driving distances from OpenStreetMap/OSRM, obtained on 2026-10-17. One deliberate change from the paper: the paper uses straight-line distances between points. In a real city, one-way streets and bridges make the road distance very different from the straight line, and sometimes different in each direction. So we use real driving distances.

---

## B. The algorithm (2:30–5:15)

**2:30 [SHOW] Slide B1, origin**

Simulated Annealing comes from metallurgy. When a metal is heated and then cooled slowly, its atoms settle into a stable, low-energy structure. Metropolis and colleagues gave the rule for random moves at a temperature in 1953. Kirkpatrick, Gelatt and Vecchi turned it into an optimisation method in 1983, and Černý applied it to the TSP. In our problem a state is a tour, its energy is the tour's length in kilometres, and the temperature controls how willing we are to accept a longer tour.

**3:00 [SHOW] Slide B2, Algorithm 2.5 line by line**

Here is Algorithm 2.5 from the paper, next to our code. Line 1: the input is the distance matrix. Line 2: we start from a random tour and compute its total distance; we keep the depot fixed in front. Line 3: we set a high starting temperature, 6.61 kilometres. Line 4: we make a small change by swapping two hospitals. Line 5: we compute the new total. Lines 6 to 10 are the acceptance rule: a shorter tour is always accepted, and a longer one is accepted with probability P equals e to the minus delta over T. Line 11 cools the temperature, T becomes alpha times T. Line 12 stops when T is low enough, when there has been no improvement for a while, or at a maximum number of moves. Line 13 returns the best tour ever seen.

**3:45 [SHOW] Slide B3, the hidden loop**

One detail the pseudocode hides: in the paper's own Python code there are two loops. At each temperature we try 200 moves, and only then do we cool. Our run used 281 temperature levels, which is 56,200 moves in total.

**4:05 [SHOW] Slide B4, worked example**

Here is the rule on our real data, taken from the trace of our run. [Read the first two or three moves from the slide. For an accepted worse move, say:] Delta is positive, so the tour got longer. P is e to the minus delta over T, and r is a random number. Since r is less than P, we accept the worse tour anyway. That is how the method escapes local optima. [For a rejected move:] Here r is larger than P, so we keep the current tour.

**4:35 [SHOW] Slide B5, advantages and limitations**

The advantages: it escapes local optima, it is simple, it is fast, about 90 milliseconds per run here, and it works directly with one-way distances. The limitations: it depends on its parameters, its answer can change from run to run, and in practice it does not guarantee the optimum. Convergence is only proven for logarithmically slow cooling, which nobody can wait for.

**4:55 [SHOW] Slide B6, optimality and complexity**

So Simulated Annealing is an approximate, heuristic method. Theorem 2.5 says the running time is O(n cubed): each move costs O(n) to recompute the tour, and there are I moves. But I equals n squared is the authors' assumption. In reality the number of moves is set by the parameters. Our run made 56,200 moves, and the paper's own default parameters make about five million moves whatever n is.

---

## C. Graph model, data, methodology (5:15–7:45)

**5:15 [SHOW] Slide C1, fig1_graph.png**

We model the city as a complete directed weighted graph. There are 9 vertices and 72 directed arcs, one for every ordered pair, because driving from A to B is a different trip from B to A. Each arc weight is the driving distance in kilometres. In our data, 29 of the 36 pairs have different distances in the two directions, which is why the graph is directed.

**6:05 [SHOW] Slide C2, fig2_weight_matrix.png**

This is the weight matrix: row is "from", column is "to". The source is the length of the route chosen by the OSRM car router on the OpenStreetMap road network, one request per direction, obtained on 2026-10-17 (18:15–18:18, Philippine time). Our data-sources file marks every entry as actual or assumed: 72 ACTUAL. Before anything runs, our validator checks that the matrix is square, the diagonal is zero, all distances are positive, and the labels match the locations file.

**6:55 [SHOW] Slide C3, parameters and fig9_alpha_sensitivity.png**

How did we choose the parameters? The starting temperature is calibrated to our units: an average worse move of 1.47 kilometres is accepted with probability 0.8 at the start. We stop at 0.001 kilometres, where even a 100-metre detour is essentially never accepted. For the cooling rate we compared several values on the same seeds. α = 0.98 reached the optimum in 100% of 100 runs in 234 ms per run; see the table for the faster/slower alternatives. The paper's defaults also work, but they take about five million moves.

---

## D. Live Python run and results (7:45–11:30)

**7:45 [SHOW] VS Code or terminal, font at least 18 pt. Open `data/locations.csv`, then `data/distance_matrix.csv`.**

This is our input data, exactly as collected: the locations with their coordinates, and the directed distance matrix in kilometres.

**8:10 [TYPE]** `python main.py --trace`

**8:15 [SHOW] scroll slowly through the console output**

First the program validates the data and prints its fingerprint, `c652b67ace`, which is also stamped on every figure. Then it prints the inputs and the parameters. Here is the trace of the first five moves: the current tour, the swap, the new tour, delta, the temperature, the probability, the random number and the decision. These are the numbers from our worked example.

**9:00 [SHOW] "SIMULATED ANNEALING RESULT" block**

The best tour found is V0 → V7 → V1 → V5 → V3 → V6 → V8 → V2 → V4 → V0, a total of **14.1 kilometres**. The random starting tour was 16.32 kilometres.

**9:15 [SHOW] "VERIFICATION" block**

Now we check the answer independently. The route starts and ends at the depot, has 10 entries (9 stops plus the return), and visits every hospital exactly once: all pass. Then we add the route up edge by edge from the graph's weights: 0.14 + 1.62 + 1.26 + 1.63 + 1.85 + 1.0 + 3.63 + 2.74 + 0.23 = **14.1 km**. That equals the total that Simulated Annealing reported.

**9:45 [SHOW] "OPTIMALITY CHECK" and "30 INDEPENDENT SA RUNS" blocks**

Is it optimal? Simulated Annealing cannot tell us. So we ran brute force on the same matrix, checking all 40,320 possible tours. The shortest possible tour is 14.1 kilometres. That is exactly our Simulated Annealing result, so our route is optimal for this instance, and the proof is the exhaustive search. For comparison, the greedy nearest-neighbour route is 15.37 kilometres, and an average random order is 20.79 kilometres. We also ran Simulated Annealing 30 times with different seeds, in the same format as the paper's Table 2: it reached the optimum 30 out of 30 times.

**10:25 [SHOW] open `outputs/route_map.html` in the browser; then `fig4_convergence.png`, `fig5_acceptance.png`, and the GIF**

Here is the route on the map. The numbers are the visiting order and the arrows show the direction. This link opens the same route in Google Maps. The convergence plot shows the current tour jumping around while the temperature is high and settling as it cools. The best tour reached 14.1 kilometres at move 10,506. The acceptance plot shows the share of worse moves accepted falling from about 0.8 to zero, exactly as e to the minus delta over T predicts.

**11:15 [SHOW] `src/simulated_annealing.py`, the main loop**

Briefly, the code: the inner loop makes the moves, `metropolis` applies the acceptance rule, `T *= alpha` cools, and every line is commented with its step number from Algorithm 2.5.

---

## E. Conclusion and references (11:30–12:45)

**11:30 [SHOW] Slide E1**

So the courier should drive PRC → NMMC → ACE → MRXUH → PGH Velez → Madonna → JRBGH → PMP Kausw → Sabal → PRC, a total of 14.1 kilometres. That is 6.69 kilometres shorter than an average random order and 1.27 kilometres shorter than the greedy route. The route makes sense on the map: it visits each part of the city once and never doubles back. It leaves the Capitol compound through NMMC, next door, swings east to ACE in Lapasan and south to Maria Reyna in Camaman-an, then comes back through downtown at Polymedic on Velez Street. It then crosses the river to Carmen, where Madonna and J.R. Borja are only 1 kilometre apart on the same street, continues north to Polymedic in Kauswagan, the most remote stop, and returns to Sabal, beside the Red Cross office, for the last 0.23 kilometres. The greedy route does the opposite: it takes the nearest hospitals first and leaves Kauswagan for last, so it has to drive 4.22 kilometres from ACE on the east side to reach it. Because brute force checked every possible tour, this route is proven optimal for this instance. The proof comes from the exhaustive search, not from Simulated Annealing itself.

**12:00 [SHOW] Slide E2**

Our limitations: distances are static, with no traffic or time windows; there is one vehicle; we depend on OpenStreetMap's road data and on OSRM's choice of route; and the instance is small. Natural next steps are minimising travel time with live traffic, adding time windows for urgent hospitals, using several vehicles, combining Simulated Annealing with 2-opt, and using the Google Distance Matrix API to scale up.

**12:25 [SHOW] Slide E3, references**

Our references are on screen: the assigned paper, whose Appendix code is the basis of ours, the original Simulated Annealing papers, the Python libraries we used, and OpenStreetMap/OSRM as our data source. Thank you.

**12:45 End.**

---
_Generated 2026-10-17 18:56 from data fingerprint `c652b67ace` by `src/docs_builder.py`. Do not edit by hand; edit `docs/templates/narration_script.md.tmpl` instead._
