"""
verify.py - independent checks of the route returned by Simulated Annealing.

1. Validity: starts and ends at the depot, n + 1 entries, every hospital exactly once.
2. Total: re-add the route edge by edge, reading each weight from the networkx graph
   (not from the list-of-lists matrix the algorithm used), and require that the
   recomputed sum equals the total SA reported.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import networkx as nx

from src import config


class VerificationError(AssertionError):
    """Raised when the reported total does not match the recomputed total."""


@dataclass
class Check:
    name: str
    passed: bool
    detail: str


@dataclass
class EdgeRow:
    step: int
    from_id: int
    to_id: int
    km: float
    cumulative_km: float
    status: str


@dataclass
class VerificationReport:
    route: list[int]
    checks: list[Check]
    edges: list[EdgeRow] = field(default_factory=list)
    recomputed_km: float = math.nan
    reported_km: float = math.nan

    @property
    def route_valid(self) -> bool:
        return all(c.passed for c in self.checks)

    @property
    def total_matches(self) -> bool:
        return math.isclose(self.recomputed_km, self.reported_km, abs_tol=config.FLOAT_TOL)

    @property
    def passed(self) -> bool:
        return self.route_valid and self.total_matches


def check_route(route: list[int], n: int, depot: int = config.DEPOT) -> list[Check]:
    """The closed-tour rules of the TSP, one named check each."""
    inner = route[1:-1]
    expected = set(range(n)) - {depot}
    missing = sorted(expected - set(inner))
    repeated = sorted({v for v in inner if inner.count(v) > 1})
    return [
        Check("starts at depot", bool(route) and route[0] == depot,
              f"first vertex = {route[0] if route else None}"),
        Check("ends at depot", bool(route) and route[-1] == depot,
              f"last vertex = {route[-1] if route else None}"),
        Check("n + 1 entries", len(route) == n + 1, f"{len(route)} entries, expected {n + 1}"),
        Check("every stop exactly once", not missing and not repeated and depot not in inner,
              f"missing={missing or 'none'}, repeated={repeated or 'none'}"),
    ]


def edge_by_edge(route: list[int], G: nx.DiGraph) -> list[EdgeRow]:
    """Walk the route and read every arc weight from the graph G."""
    rows, running = [], 0.0
    for step, (a, b) in enumerate(zip(route[:-1], route[1:]), start=1):
        km = G[a][b]["weight"]
        running += km
        rows.append(EdgeRow(step, a, b, km, running, G[a][b].get("status", "")))
    return rows


def verify_solution(route: list[int], reported_km: float, G: nx.DiGraph,
                    strict: bool = True) -> VerificationReport:
    """Run all checks. With ``strict`` a failed check raises VerificationError."""
    report = VerificationReport(route=route, checks=check_route(route, G.number_of_nodes()),
                                reported_km=reported_km)
    if report.route_valid:
        report.edges = edge_by_edge(route, G)
        report.recomputed_km = math.fsum(e.km for e in report.edges)
    if strict and not report.route_valid:
        failed = [c.name for c in report.checks if not c.passed]
        raise VerificationError(f"Route is not a valid closed tour: {failed}")
    if strict:
        assert_totals_match(report)
    return report


def assert_totals_match(report: VerificationReport) -> None:
    if not report.total_matches:
        raise VerificationError(f"Recomputed total {report.recomputed_km:.6f} km differs from "
                                f"the reported total {report.reported_km:.6f} km.")
