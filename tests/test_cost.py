"""The tour-cost function: closed tour, directed arcs."""
import pytest

from src.graph_model import closed_route, tour_cost
from tests.conftest import TINY_TOURS


@pytest.mark.parametrize("tour,expected", TINY_TOURS.items())
def test_tour_cost_matches_hand_calculation(tiny, tour, expected):
    assert tour_cost(list(tour), tiny) == expected


def test_cost_includes_return_to_depot(tiny):
    # 0 -> 1 -> 2 -> 3 is 1 + 3 + 1 = 5 without the return; the return 3 -> 0 adds 3.
    assert tour_cost([0, 1, 2, 3], tiny) == 8


def test_direction_matters(tiny):
    assert tour_cost([0, 1, 2, 3], tiny) != tour_cost([0, 3, 2, 1], tiny)


def test_closed_route_appends_start():
    assert closed_route([0, 3, 1, 2]) == [0, 3, 1, 2, 0]
