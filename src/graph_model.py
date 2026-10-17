"""
graph_model.py - the weighted DIRECTED graph G = (V, A) and the tour-cost function.

    V = {V0 (depot), V1..V(n-1) (hospitals)}
    A = every ordered pair (i, j) with i != j  -> complete digraph, n(n-1) arcs
    w(i, j) = driving distance from i to j in km (may differ from w(j, i))

A tour is stored the way the paper's Appendix 4.5 stores it: a list of the n
vertices in visiting order with the return to the start implied. Here the
depot is always at position 0. ``closed_route`` adds the return explicitly
(n + 1 entries) for printing and verification.
"""
from __future__ import annotations

import networkx as nx

from src.data_loader import Dataset


def build_digraph(ds: Dataset, D: list[list[float]]) -> nx.DiGraph:
    """Complete weighted digraph with node and arc attributes taken from the CSVs."""
    G = nx.DiGraph(name="Red Cross CDO blood-delivery network", unit="km")
    for loc in ds.locations:
        G.add_node(loc.id, label=loc.label, name=loc.name, short_name=loc.short_name,
                   role=loc.role, lat=loc.latitude, lon=loc.longitude)
    for i in range(ds.n):
        for j in range(ds.n):
            if i != j:
                G.add_edge(i, j, weight=D[i][j], status=ds.edge_status(i, j))
    return G


def tour_cost(tour: list[int], D: list[list[float]]) -> float:
    """Total distance of a CLOSED tour: sum of D[a][b] over consecutive vertices,
    plus the return arc from the last vertex back to tour[0].

    O(n) - this is the "calculate the total distance" step of Alg 2.5 (steps 2 and 5).
    The direction matters: D[a][b] is FROM a TO b.
    """
    total = 0.0
    for k in range(len(tour) - 1):
        total += D[tour[k]][tour[k + 1]]
    total += D[tour[-1]][tour[0]]  # return to the start (the depot)
    return total


def closed_route(tour: list[int]) -> list[int]:
    """[0, 3, 1, 2] -> [0, 3, 1, 2, 0]: write the return to the depot explicitly."""
    return list(tour) + [tour[0]]


def route_labels(route: list[int], ds: Dataset) -> str:
    """[0, 3, 1, 0] -> 'V0 -> V3 -> V1 -> V0'."""
    return " -> ".join(ds.labels[v] for v in route)


def route_names(route: list[int], ds: Dataset) -> str:
    """[0, 3, 1, 0] -> 'PRC -> NMMC -> ... -> PRC' (short names)."""
    return " -> ".join(ds.display_name(v) for v in route)
