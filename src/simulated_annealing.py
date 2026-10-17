"""
simulated_annealing.py - Simulated Annealing (SA) for our asymmetric TSP.

Faithful to the paper's Algorithm 2.5 and its Python code (Appendix 4.5):
  * start from a random tour, at a high temperature T0
  * neighbour = swap the positions of two cities
  * accept a shorter tour always; accept a longer one with P = e^(-delta/T)
  * cool geometrically, T <- alpha * T, using the two nested loops of Appendix 4.5
    (inner loop: iterations_per_temperature moves at the same T; outer loop: cool)
  * return the best tour seen (tracked separately from the current tour)

Our modifications to the Appendix 4.5 code (credited in REFERENCES.md):
  1. input is a DIRECTED road-distance matrix in km, not (x, y) points
  2. the depot is fixed at position 0; only the hospitals are permuted
  3. T0 is calibrated to the data's units; alpha, T_stop, moves per level tuned
  4. the extra stopping rules named in the paper's text: patience and an iteration cap
  5. a full history and a step-by-step trace for the plots and the slides
  6. optional segment-reversal ("2-opt") neighbour - OUR EXTENSION, off by default
"""
from __future__ import annotations

import math
import random
import statistics
import time
from dataclasses import dataclass, field

from src import config
from src.config import SAParams
from src.graph_model import closed_route, tour_cost


# ---------------------------------------------------------------------------
# Result containers
# ---------------------------------------------------------------------------
@dataclass
class TraceStep:
    """One move, with every number needed to redo it by hand."""
    iteration: int
    level: int
    temperature: float
    current_tour: list[int]
    current_cost: float
    positions: tuple[int, int]
    new_tour: list[int]
    new_cost: float
    delta: float
    probability: float
    r: float | None
    accepted: bool


@dataclass
class SAHistory:
    """Per-move record used by the convergence / acceptance plots and the GIF."""
    iteration: list[int] = field(default_factory=list)
    temperature: list[float] = field(default_factory=list)
    current_cost: list[float] = field(default_factory=list)
    best_cost: list[float] = field(default_factory=list)
    delta: list[float] = field(default_factory=list)
    probability: list[float] = field(default_factory=list)
    accepted: list[bool] = field(default_factory=list)
    level: list[int] = field(default_factory=list)
    snapshots: list[tuple] = field(default_factory=list)  # (iter, T, current, cur_cost, best, best_cost)

    def record(self, it: int, level: int, T: float, cur: float, best: float,
               delta: float, p: float, accepted: bool) -> None:
        self.iteration.append(it)
        self.level.append(level)
        self.temperature.append(T)
        self.current_cost.append(cur)
        self.best_cost.append(best)
        self.delta.append(delta)
        self.probability.append(p)
        self.accepted.append(accepted)


@dataclass
class SAResult:
    best_tour: list[int]
    best_cost: float
    initial_tour: list[int]
    initial_cost: float
    iterations: int
    levels: int
    final_temperature: float
    best_found_at: int
    stop_reason: str
    runtime_s: float
    seed: int
    neighbor: str
    params: SAParams
    history: SAHistory | None
    trace: list[TraceStep]

    @property
    def route(self) -> list[int]:
        """Best tour with the return to the depot written out (n + 1 entries)."""
        return closed_route(self.best_tour)


# ---------------------------------------------------------------------------
# Building blocks
# ---------------------------------------------------------------------------
def random_tour(n: int, rng: random.Random) -> list[int]:
    """Alg 2.5 step 2: a random sequence of the hospitals, with the depot fixed first."""
    hospitals = list(range(1, n))
    rng.shuffle(hospitals)
    return [config.DEPOT] + hospitals


def swap_two_cities(tour: list[int], rng: random.Random) -> tuple[list[int], tuple[int, int]]:
    """Alg 2.5 step 4: swap the positions of two cities (position 0 = depot never moves)."""
    i, j = rng.sample(range(1, len(tour)), 2)
    new_tour = tour.copy()
    new_tour[i], new_tour[j] = new_tour[j], new_tour[i]
    return new_tour, (i, j)


def reverse_segment(tour: list[int], rng: random.Random) -> tuple[list[int], tuple[int, int]]:
    """OUR EXTENSION ("2-opt" move): reverse the order of the cities between positions i..j.
    On an asymmetric matrix the reversed arcs change direction, so the caller recomputes
    the whole tour cost (no symmetric shortcut)."""
    i, j = sorted(rng.sample(range(1, len(tour)), 2))
    new_tour = tour[:i] + tour[i:j + 1][::-1] + tour[j + 1:]
    return new_tour, (i, j)


NEIGHBORS = {"swap": swap_two_cities, "2opt": reverse_segment}


def metropolis(delta: float, T: float, rng: random.Random) -> tuple[bool, float, float | None]:
    """Alg 2.5 steps 6-10 (acceptance criteria). Returns (accepted, P, r).

    Same rule as Appendix 4.5: ``new < current or random() < exp((current - new) / T)``,
    so r is drawn only for moves that are not improvements, and delta = 0 gives P = 1.
    """
    if delta < 0:                     # Alg 2.5 steps 6-7: shorter tour -> accept
        return True, 1.0, None
    p = math.exp(-delta / T)          # Alg 2.5 step 9: P = e^(-delta/T)
    r = rng.random()                  # uniform random number in [0, 1)
    return r < p, p, r                # accept the worse tour with probability P


def calibrate_initial_temperature(D: list[list[float]], neighbor: str = "swap",
                                  target_p: float = config.SA_DEFAULTS.target_initial_acceptance,
                                  samples: int = config.CALIBRATION_SAMPLES,
                                  seed: int = config.CALIBRATION_SEED) -> tuple[float, float]:
    """Choose T0 so that an AVERAGE worse move is accepted with probability ``target_p``.

    Solve  target_p = e^(-mean_uphill_delta / T0)  ->  T0 = -mean_uphill_delta / ln(target_p).
    Returns (T0, mean_uphill_delta), both in km. Uses its own fixed seed, so every run
    of the experiment starts from the same T0.
    """
    rng, n, make_move = random.Random(seed), len(D), NEIGHBORS[neighbor]
    uphill = []
    for _ in range(samples):
        tour = random_tour(n, rng)
        new_tour, _ = make_move(tour, rng)
        delta = tour_cost(new_tour, D) - tour_cost(tour, D)
        if delta > 0:
            uphill.append(delta)
    mean_uphill = statistics.fmean(uphill)
    return round(-mean_uphill / math.log(target_p), 2), mean_uphill


def resolve_params(D: list[list[float]], params: SAParams, neighbor: str) -> SAParams:
    """Fill in T0 when it is set to 'auto' (None)."""
    if params.t0 is not None:
        return params
    t0, _ = calibrate_initial_temperature(D, neighbor, params.target_initial_acceptance)
    return params.with_(t0=t0)


# ---------------------------------------------------------------------------
# The algorithm
# ---------------------------------------------------------------------------
def simulated_annealing(D: list[list[float]], params: SAParams, seed: int,
                        neighbor: str = "swap", record_history: bool = True,
                        trace_steps: int = 0,
                        snapshot_every: int = config.SNAPSHOT_EVERY) -> SAResult:
    """Run SA once on distance matrix ``D`` (row = from, column = to). Reproducible via ``seed``."""
    params = resolve_params(D, params, neighbor)
    rng, make_move, n = random.Random(seed), NEIGHBORS[neighbor], len(D)
    history = SAHistory() if record_history else None
    trace: list[TraceStep] = []
    started = time.perf_counter()

    # Alg 2.5 step 1: input = cities (vertices) and the pairwise distance matrix D
    # Alg 2.5 step 2: random initial tour and its total distance
    current = random_tour(n, rng)
    current_cost = tour_cost(current, D)
    initial_tour, initial_cost = current.copy(), current_cost
    best, best_cost, best_found_at = current.copy(), current_cost, 0  # best-so-far

    # Alg 2.5 step 3: set a high initial temperature
    T = params.t0
    iteration, level, stale_levels, stop_reason = 0, 0, 0, ""
    patience = params.patience_levels

    while True:
        # Alg 2.5 step 12 (a): stop when the temperature is sufficiently low
        if T <= params.t_stop:
            stop_reason = f"temperature reached T_stop = {params.t_stop:g}"
            break
        best_before_level = best_cost

        for _ in range(params.iterations_per_temperature):  # inner loop (Appendix 4.5)
            # Alg 2.5 step 4: generate a new tour by a small change (swap two cities)
            new_tour, positions = make_move(current, rng)
            # Alg 2.5 step 5: total distance of the new tour
            new_cost = tour_cost(new_tour, D)
            delta = new_cost - current_cost
            # Alg 2.5 steps 6-10: accept if shorter, else accept with P = e^(-delta/T)
            accepted, p, r = metropolis(delta, T, rng)
            if len(trace) < trace_steps:
                trace.append(TraceStep(iteration + 1, level, T, current.copy(), current_cost,
                                       positions, new_tour, new_cost, delta, p, r, accepted))
            if accepted:
                current, current_cost = new_tour, new_cost
                if current_cost < best_cost:  # keep the best tour ever seen (for step 13)
                    best, best_cost, best_found_at = current.copy(), current_cost, iteration + 1
            iteration += 1
            if history is not None:
                history.record(iteration, level, T, current_cost, best_cost, delta, p, accepted)
                if iteration % snapshot_every == 0:
                    history.snapshots.append((iteration, T, current.copy(), current_cost,
                                              best.copy(), best_cost))
            if iteration >= params.max_total_iterations:
                break

        # Alg 2.5 step 12 (c): stop when the maximum number of iterations is reached
        if iteration >= params.max_total_iterations:
            stop_reason = f"maximum of {params.max_total_iterations:,} iterations reached"
            break
        # Alg 2.5 step 11: reduce the temperature (geometric cooling T <- alpha * T)
        T *= params.alpha
        level += 1
        # Alg 2.5 step 12 (b): stop when there is no significant improvement
        improved = best_before_level - best_cost > params.min_improvement
        stale_levels = 0 if improved else stale_levels + 1
        if patience is not None and stale_levels >= patience:
            stop_reason = (f"no improvement for {patience} temperature levels "
                           f"(T fell {params.patience_drop_factor:g}x)")
            break

    if history is not None and (not history.snapshots or history.snapshots[-1][0] != iteration):
        history.snapshots.append((iteration, T, current.copy(), current_cost, best.copy(), best_cost))

    # Alg 2.5 step 13: output the shortest tour found
    return SAResult(best_tour=best, best_cost=best_cost, initial_tour=initial_tour,
                    initial_cost=initial_cost, iterations=iteration, levels=level,
                    final_temperature=T, best_found_at=best_found_at, stop_reason=stop_reason,
                    runtime_s=time.perf_counter() - started, seed=seed, neighbor=neighbor,
                    params=params, history=history, trace=trace)
