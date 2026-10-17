"""
baselines.py - methods we compare Simulated Annealing against (same distance matrix).

* brute_force             paper Algorithm 2.3 (exact). Fix the depot, try all (n-1)!
                          orders of the hospitals. This is the PROOF of optimality.
* greedy_nearest_neighbor paper Algorithm 2.7. From the current vertex always drive
                          to the nearest unvisited vertex (outgoing distance D[cur][j]).
"""
from __future__ import annotations

import itertools
import math
import statistics
import time
from dataclasses import dataclass

from src import config
from src.graph_model import closed_route, tour_cost


@dataclass
class BruteForceResult:
    optimal_cost: float
    optimal_tours: list[list[int]]   # every tour that ties for the optimum
    worst_cost: float
    mean_cost: float                 # = expected cost of a uniformly random tour
    all_costs: list[float]
    tours_evaluated: int
    runtime_s: float

    @property
    def route(self) -> list[int]:
        return closed_route(self.optimal_tours[0])


@dataclass
class GreedyResult:
    tour: list[int]
    cost: float
    runtime_s: float

    @property
    def route(self) -> list[int]:
        return closed_route(self.tour)


def brute_force(D: list[list[float]]) -> BruteForceResult:
    """Exhaustive search over all (n-1)! tours that start at the depot (Alg 2.3)."""
    n = len(D)
    if n > config.BRUTE_FORCE_MAX_N:
        raise ValueError(f"n = {n}: (n-1)! = {math.factorial(n - 1):,} tours is too many.")
    started = time.perf_counter()
    best_cost, best_tours, all_costs = math.inf, [], []
    for perm in itertools.permutations(range(1, n)):     # Alg 2.3 step 3: all (n-1)! orders
        tour = [config.DEPOT, *perm]
        cost = tour_cost(tour, D)                         # Alg 2.3 step 5: cost of P_j
        all_costs.append(cost)
        if cost < best_cost - config.FLOAT_TOL:           # Alg 2.3 step 7: keep the minimum
            best_cost, best_tours = cost, [tour]
        elif abs(cost - best_cost) <= config.FLOAT_TOL:
            best_tours.append(tour)                       # ties: several optimal tours
    return BruteForceResult(optimal_cost=best_cost, optimal_tours=best_tours,
                            worst_cost=max(all_costs), mean_cost=statistics.fmean(all_costs),
                            all_costs=all_costs, tours_evaluated=len(all_costs),
                            runtime_s=time.perf_counter() - started)


def greedy_nearest_neighbor(D: list[list[float]], start: int = config.DEPOT) -> GreedyResult:
    """Alg 2.7: repeatedly travel to the nearest unvisited vertex, then return to start.
    Ties are broken by the smaller vertex id so the result is deterministic."""
    started = time.perf_counter()
    tour, unvisited = [start], set(range(len(D))) - {start}
    while unvisited:                                      # Alg 2.7 steps 3-6
        here = tour[-1]
        nearest = min(unvisited, key=lambda j: (D[here][j], j))
        tour.append(nearest)
        unvisited.remove(nearest)
    return GreedyResult(tour=tour, cost=tour_cost(tour, D),   # Alg 2.7 step 7: return home
                        runtime_s=time.perf_counter() - started)


def gap_percent(cost: float, optimum: float) -> float:
    """How much longer than the optimum, in percent (0.0 = optimal)."""
    return 100.0 * (cost - optimum) / optimum


def is_optimal(cost: float, optimum: float) -> bool:
    return abs(cost - optimum) <= config.FLOAT_TOL
