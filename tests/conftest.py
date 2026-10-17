"""Shared fixtures: a tiny asymmetric instance small enough to check by hand."""
import pytest

# 4 vertices, V0 = depot. Row = FROM, column = TO.  D[1][0] = 2 but D[0][1] = 1, etc.
TINY = [
    [0, 1, 5, 4],
    [2, 0, 3, 6],
    [7, 2, 0, 1],
    [3, 8, 2, 0],
]

# All (4-1)! = 6 tours that start at the depot, with their totals worked out by hand:
#   0-1-2-3-0 : 1 + 3 + 1 + 3 = 8   <- the unique optimum
#   0-1-3-2-0 : 1 + 6 + 2 + 7 = 16
#   0-2-1-3-0 : 5 + 2 + 6 + 3 = 16
#   0-2-3-1-0 : 5 + 1 + 8 + 2 = 16
#   0-3-1-2-0 : 4 + 8 + 3 + 7 = 22
#   0-3-2-1-0 : 4 + 2 + 2 + 2 = 10   <- the REVERSE of the optimum costs more (asymmetric)
TINY_TOURS = {
    (0, 1, 2, 3): 8, (0, 1, 3, 2): 16, (0, 2, 1, 3): 16,
    (0, 2, 3, 1): 16, (0, 3, 1, 2): 22, (0, 3, 2, 1): 10,
}


@pytest.fixture
def tiny():
    return [[float(v) for v in row] for row in TINY]


@pytest.fixture
def random_instance():
    """A 7-vertex asymmetric instance (fixed seed) for SA-vs-brute-force checks."""
    import random
    rng = random.Random(123)
    n = 7
    return [[0.0 if i == j else round(rng.uniform(1, 10), 1) for j in range(n)] for i in range(n)]
