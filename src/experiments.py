"""
experiments.py - repeated runs and parameter studies (all on the same distance matrix).

* run_many / summarize    30 independent SA runs -> paper Table 2 statistics
* alpha_sensitivity       solution quality vs runtime for several cooling rates
* neighbor_comparison     swap (paper) vs segment reversal (our extension)
* paper_defaults_run      one run with the Appendix 4.5 defaults, for comparison
"""
from __future__ import annotations

import math
import statistics
from dataclasses import dataclass

from src import config
from src.baselines import gap_percent, is_optimal
from src.config import SAParams
from src.simulated_annealing import resolve_params, simulated_annealing


@dataclass
class RunRecord:
    seed: int
    cost: float
    runtime_s: float
    iterations: int
    levels: int
    best_found_at: int
    stop_reason: str
    tour: list[int]
    hit_optimum: bool
    gap_pct: float


def run_many(D: list[list[float]], params: SAParams, seeds: list[int], neighbor: str,
             optimum: float) -> list[RunRecord]:
    """Independent SA runs (no history recorded, so the timing is the algorithm only)."""
    params = resolve_params(D, params, neighbor)
    records = []
    for seed in seeds:
        res = simulated_annealing(D, params, seed, neighbor, record_history=False)
        records.append(RunRecord(seed, res.best_cost, res.runtime_s, res.iterations, res.levels,
                                 res.best_found_at, res.stop_reason, res.best_tour,
                                 is_optimal(res.best_cost, optimum),
                                 gap_percent(res.best_cost, optimum)))
    return records


def summarize(records: list[RunRecord]) -> dict:
    """Best / worst / average / variance / std (sample, n-1) / time - as in paper Table 2."""
    costs = [r.cost for r in records]
    many = len(costs) > 1
    return {
        "runs": len(records),
        "best": min(costs),
        "worst": max(costs),
        "mean": statistics.fmean(costs),
        "variance": statistics.variance(costs) if many else 0.0,
        "std": statistics.stdev(costs) if many else 0.0,
        "mean_runtime_s": statistics.fmean(r.runtime_s for r in records),
        "mean_iterations": statistics.fmean(r.iterations for r in records),
        "hit_rate_pct": 100.0 * sum(r.hit_optimum for r in records) / len(records),
        "mean_gap_pct": statistics.fmean(r.gap_pct for r in records),
        "max_gap_pct": max(r.gap_pct for r in records),
    }


def planned_levels(params: SAParams) -> int:
    """Temperature levels until T <= T_stop if no other stopping rule fires."""
    return math.ceil(math.log(params.t_stop / params.t0) / math.log(params.alpha))


def alpha_sensitivity(D: list[list[float]], base: SAParams, alphas: tuple[float, ...],
                      seeds: list[int], neighbor: str, optimum: float) -> list[dict]:
    """Vary only alpha; everything else (T0, moves per level, T_stop, patience, seeds) is
    fixed. The patience rule is defined as a temperature drop, so it means the same for
    every alpha, and the row for our default alpha equals the main 30-run statistics."""
    base = resolve_params(D, base, neighbor)
    rows = []
    for alpha in alphas:
        params = base.with_(alpha=alpha)
        summary = summarize(run_many(D, params, seeds, neighbor, optimum))
        rows.append({"alpha": alpha, "t0": params.t0, "planned_levels": planned_levels(params),
                     "patience_levels": params.patience_levels, **summary})
    return rows


def neighbor_comparison(D: list[list[float]], base: SAParams, seeds: list[int],
                        optimum: float) -> list[dict]:
    """Swap (paper) vs segment reversal (our extension). T0 is calibrated per neighbour,
    because the two moves produce different typical uphill deltas."""
    rows = []
    for neighbor in ("swap", "2opt"):
        params = resolve_params(D, base, neighbor)
        summary = summarize(run_many(D, params, seeds, neighbor, optimum))
        rows.append({"neighbor": neighbor, "t0": params.t0, **summary})
    return rows


def paper_defaults_run(D: list[list[float]], seed: int, optimum: float) -> dict:
    """One run with the paper's Appendix 4.5 defaults (T0=1000, alpha=0.995, ...)."""
    rec = run_many(D, config.PAPER_DEFAULTS, [seed], "swap", optimum)[0]
    return {"seed": seed, "t0": config.PAPER_DEFAULTS.t0, "alpha": config.PAPER_DEFAULTS.alpha,
            "iterations_per_temperature": config.PAPER_DEFAULTS.iterations_per_temperature,
            "t_stop": config.PAPER_DEFAULTS.t_stop, "cost": rec.cost,
            "hit_optimum": rec.hit_optimum, "iterations": rec.iterations, "levels": rec.levels,
            "runtime_s": rec.runtime_s}
