"""The verifier must accept a correct route and catch every kind of wrong one."""
import pytest

from src.verify import VerificationError, check_route, verify_solution


@pytest.fixture
def G(tiny):
    import networkx as nx
    g = nx.DiGraph()
    for i in range(4):
        for j in range(4):
            if i != j:
                g.add_edge(i, j, weight=tiny[i][j], status="ACTUAL")
    return g


def test_valid_route_passes_and_sums_edges(G):
    rep = verify_solution([0, 1, 2, 3, 0], 8.0, G)
    assert rep.passed
    assert [e.km for e in rep.edges] == [1, 3, 1, 3]
    assert [e.cumulative_km for e in rep.edges] == [1, 4, 5, 8]
    assert rep.recomputed_km == 8


def test_reported_total_must_match(G):
    with pytest.raises(VerificationError):
        verify_solution([0, 1, 2, 3, 0], 7.9, G)


@pytest.mark.parametrize("route,failing", [
    ([1, 0, 2, 3, 1], "starts at depot"),
    ([0, 1, 2, 3], "ends at depot"),
    ([0, 1, 2, 0], "n + 1 entries"),
    ([0, 1, 1, 3, 0], "every stop exactly once"),
    ([0, 1, 2, 0, 0], "every stop exactly once"),
])
def test_invalid_routes_are_caught(route, failing):
    failed = {c.name for c in check_route(route, 4) if not c.passed}
    assert failing in failed


def test_invalid_route_raises_in_strict_mode(G):
    with pytest.raises(VerificationError):
        verify_solution([0, 1, 1, 3, 0], 8.0, G)
