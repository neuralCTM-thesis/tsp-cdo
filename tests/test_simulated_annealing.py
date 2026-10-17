"""Simulated Annealing: valid output, reproducible, finds the optimum on small instances."""
import math
import random

import pytest

from src import config
from src.baselines import brute_force
from src.graph_model import tour_cost
from src.simulated_annealing import (calibrate_initial_temperature, metropolis, reverse_segment,
                                     simulated_annealing, swap_two_cities)
from src.verify import check_route

FAST = config.SA_DEFAULTS.with_(alpha=0.95, iterations_per_temperature=100)


@pytest.mark.parametrize("neighbor", ["swap", "2opt"])
def test_sa_returns_a_valid_closed_tour(random_instance, neighbor):
    res = simulated_annealing(random_instance, FAST, seed=1, neighbor=neighbor)
    assert all(c.passed for c in check_route(res.route, len(random_instance)))
    assert res.route[0] == res.route[-1] == config.DEPOT
    assert math.isclose(res.best_cost, tour_cost(res.best_tour, random_instance))


def test_sa_finds_optimum_on_tiny_instance(tiny):
    res = simulated_annealing(tiny, FAST, seed=3)
    assert res.best_cost == 8 and res.route == [0, 1, 2, 3, 0]


def test_sa_matches_brute_force_on_7_vertices(random_instance):
    optimum = brute_force(random_instance).optimal_cost
    res = simulated_annealing(random_instance, config.SA_DEFAULTS, seed=5)
    assert math.isclose(res.best_cost, optimum)


def test_same_seed_same_result(random_instance):
    a = simulated_annealing(random_instance, FAST, seed=42, record_history=False)
    b = simulated_annealing(random_instance, FAST, seed=42, record_history=False)
    assert (a.best_tour, a.best_cost, a.iterations) == (b.best_tour, b.best_cost, b.iterations)


def test_best_is_never_worse_than_initial(random_instance):
    res = simulated_annealing(random_instance, FAST, seed=9)
    assert res.best_cost <= res.initial_cost
    assert min(res.history.current_cost) >= res.best_cost - 1e-9


def test_temperature_follows_geometric_cooling(random_instance):
    res = simulated_annealing(random_instance, FAST, seed=2)
    t0, alpha = res.params.t0, res.params.alpha
    for level, T in zip(res.history.level, res.history.temperature):
        assert math.isclose(T, t0 * alpha ** level)


def test_depot_never_moves():
    rng = random.Random(0)
    tour = [0, 1, 2, 3, 4, 5]
    for _ in range(500):
        for move in (swap_two_cities, reverse_segment):
            new, _ = move(tour, rng)
            assert new[0] == 0 and sorted(new) == sorted(tour)


def test_metropolis_rule():
    rng = random.Random(0)
    assert metropolis(-1.0, 5.0, rng) == (True, 1.0, None)      # better: always accept
    accepted, p, r = metropolis(0.0, 5.0, rng)                   # equal: P = e^0 = 1
    assert accepted and p == 1.0
    _, p, r = metropolis(2.0, 4.0, rng)                          # worse: P = e^(-2/4)
    assert math.isclose(p, math.exp(-0.5)) and 0 <= r < 1


def test_trace_records_hand_checkable_steps(random_instance):
    res = simulated_annealing(random_instance, FAST, seed=4, trace_steps=5)
    assert len(res.trace) == 5
    for step in res.trace:
        assert math.isclose(step.delta, step.new_cost - step.current_cost)
        assert math.isclose(step.new_cost, tour_cost(step.new_tour, random_instance))
        if step.delta >= 0:
            assert math.isclose(step.probability, math.exp(-step.delta / step.temperature))
            assert step.accepted == (step.r < step.probability)


def test_calibrated_t0_gives_target_acceptance(random_instance):
    t0, mean_uphill = calibrate_initial_temperature(random_instance, target_p=0.8)
    assert math.isclose(math.exp(-mean_uphill / t0), 0.8, abs_tol=0.01)


def test_patience_levels_follow_temperature_drop():
    p = config.SA_DEFAULTS.with_(alpha=0.98, patience_drop_factor=100.0)
    assert 0.98 ** p.patience_levels <= 1 / 100 < 0.98 ** (p.patience_levels - 1)
    assert config.PAPER_DEFAULTS.patience_levels is None
