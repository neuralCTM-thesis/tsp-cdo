"""Brute force (exact) and greedy nearest neighbour on the hand-checkable instance."""
import math

from src.baselines import brute_force, gap_percent, greedy_nearest_neighbor, is_optimal
from tests.conftest import TINY_TOURS


def test_brute_force_finds_hand_computed_optimum(tiny):
    bf = brute_force(tiny)
    assert bf.optimal_cost == 8
    assert bf.optimal_tours == [[0, 1, 2, 3]]
    assert bf.route == [0, 1, 2, 3, 0]


def test_brute_force_evaluates_every_tour(tiny):
    bf = brute_force(tiny)
    assert bf.tours_evaluated == math.factorial(4 - 1) == 6
    assert sorted(bf.all_costs) == sorted(TINY_TOURS.values())
    assert bf.worst_cost == 22


def test_brute_force_reports_ties():
    D = [[0, 1, 1], [1, 0, 1], [1, 1, 0]]  # both tours cost 3
    bf = brute_force(D)
    assert len(bf.optimal_tours) == 2


def test_greedy_always_takes_nearest_outgoing_arc(tiny):
    g = greedy_nearest_neighbor(tiny)
    # from 0 nearest is 1 (1 km); from 1: 2 (3) beats 3 (6); from 2: 3; back to 0
    assert g.tour == [0, 1, 2, 3]
    assert g.cost == 8


def test_greedy_can_be_suboptimal():
    # Greedy: 0->1 (1) ->2 (1) ->3 (1) and is then forced to pay 3->0 = 20: total 23.
    # Better: 0->3 (2) ->1 (1) ->2 (1) ->0 (1) = 5.
    D = [[0, 1, 2, 2], [1, 0, 1, 10], [1, 10, 0, 1], [20, 1, 1, 0]]
    g, bf = greedy_nearest_neighbor(D), brute_force(D)
    assert g.tour == [0, 1, 2, 3] and g.cost == 23
    assert bf.optimal_cost == 5 and [0, 3, 1, 2] in bf.optimal_tours  # 0-2-3-1-0 ties


def test_gap_and_optimal_helpers():
    assert gap_percent(11, 10) == 10.0
    assert is_optimal(8.0, 8.0 + 1e-12)
    assert not is_optimal(8.1, 8.0)
