"""
config.py - every tunable parameter of the project in one place.

Change values HERE (not inside the algorithm files) so that the slides, the
console output and the code always agree on what was used.

Paper reference
---------------
Luna-Garcia, Candano & Caga-anan (2024), "Performance Analysis of Classical
Algorithms for the Traveling Salesman Problem", TMJM 6(2):79-111.
Appendix 4.5 defaults: initial_temperature=1000, cooling_rate=0.995,
stop_temperature=1e-8, max_iterations=1000 (moves per temperature level).
Those defaults need ~5,054 temperature levels x 1,000 moves = ~5 million tour
evaluations, which is far more than a 9-vertex instance needs and too slow for
a live demo, and T0 = 1000 ignores the units of the data (km). Our tuned values
are below and are justified by the alpha sensitivity experiment
(python main.py --experiments).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, replace
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PLACEHOLDER_DIR = DATA_DIR / "placeholder"
OUTPUT_DIR = PROJECT_ROOT / "outputs"
DOCS_DIR = PROJECT_ROOT / "docs"
TEMPLATES_DIR = DOCS_DIR / "templates"

LOCATIONS_FILE = "locations.csv"
MATRIX_FILE = "distance_matrix.csv"
SOURCES_FILE = "data_sources.csv"

# ---------------------------------------------------------------------------
# Problem
# ---------------------------------------------------------------------------
DEPOT = 0                 # vertex id of the depot (always tour position 0)
DISTANCE_UNIT = "km"
FLOAT_TOL = 1e-9          # tolerance when comparing two tour totals


@dataclass(frozen=True)
class SAParams:
    """Parameters of Simulated Annealing (paper Algorithm 2.5 / Appendix 4.5).

    t0 = None means "calibrate automatically from the data" so that an average
    worse move is accepted with probability ``target_initial_acceptance`` at
    the start (see simulated_annealing.calibrate_initial_temperature).
    """
    t0: float | None = None                  # Alg 2.5 step 3: initial temperature (km)
    target_initial_acceptance: float = 0.80  # used only when t0 is None
    alpha: float = 0.98                      # Alg 2.5 step 11: T <- alpha * T
    iterations_per_temperature: int = 200    # inner loop of Appendix 4.5 (~7x the 28 swaps)
    t_stop: float = 0.001                    # Alg 2.5 step 12: stop when T <= t_stop (km)
    patience_drop_factor: float | None = 100.0  # step 12: stop if no new best while T fell 100x
    min_improvement: float = 1e-9            # what counts as "significant" improvement (km)
    max_total_iterations: int = 2_000_000    # step 12: hard cap on the number of moves

    @property
    def patience_levels(self) -> int | None:
        """Temperature levels in which T falls by ``patience_drop_factor`` (None = rule off).
        Defined through the temperature so the rule means the same for every alpha."""
        if self.patience_drop_factor is None:
            return None
        return math.ceil(math.log(self.patience_drop_factor) / -math.log(self.alpha))

    def with_(self, **changes) -> "SAParams":
        """Return a copy with some fields changed (keeps the original frozen)."""
        return replace(self, **changes)


# Our tuned defaults. Why these values: outputs/alpha_sensitivity.csv (python main.py
# --experiments). T_stop = 0.001 km: the distances have a resolution of 0.01 km (10 m), and
# at T = 0.001 even a 10 m worse move is accepted with P = e^-10 = 0.00005 ("frozen").
SA_DEFAULTS = SAParams()

# The paper's Appendix 4.5 defaults, reproduced once in the experiments for
# comparison. No patience rule: the paper's code only stops on temperature.
PAPER_DEFAULTS = SAParams(
    t0=1000.0,
    alpha=0.995,
    iterations_per_temperature=1000,
    t_stop=1e-8,
    patience_drop_factor=None,
    max_total_iterations=10**8,
)

# ---------------------------------------------------------------------------
# Runs and experiments
# ---------------------------------------------------------------------------
DEFAULT_SEED = 1              # seed of the single "presentation" run
DEFAULT_RUNS = 30             # independent SA runs for the Table-2 statistics
FIRST_RUN_SEED = 1            # the 30 runs use seeds 1..30
CALIBRATION_SEED = 2024       # fixed seed for T0 calibration -> same T0 for every run
CALIBRATION_SAMPLES = 2000    # random moves sampled to estimate the typical uphill delta
NEIGHBOR_DEFAULT = "swap"     # "swap" (paper) or "2opt" (our extension)

ALPHA_VALUES = (0.90, 0.95, 0.98, 0.995)   # sensitivity experiment (0.98 = our choice)
SENSITIVITY_RUNS = 100               # runs per setting in --experiments (seeds 1..100)

TRACE_PRINT_STEPS = 5         # moves printed in full by --trace
TRACE_EXPORT_STEPS = 100      # moves written to outputs/trace.csv
SNAPSHOT_EVERY = 50           # store the current tour every N moves (for the GIF)

BRUTE_FORCE_MAX_N = 11        # (n-1)! = 3.6 million tours; refuse anything larger

# ---------------------------------------------------------------------------
# Figures and maps
# ---------------------------------------------------------------------------
FIG_DPI = 160
BASE_FONT_SIZE = 15           # large enough to read in a screen recording
GIF_MAX_FRAMES = 60
GIF_FRAME_MS = 180
USE_BASEMAP_TILES = True      # static PNG map: try OpenStreetMap tiles, fall back to plain plot
TILE_URL = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
TILE_USER_AGENT = "tsp_sa_cdo/1.0 (university course project; educational use)"
TILE_TIMEOUT_S = 6
MAP_ATTRIBUTION = "Basemap (c) OpenStreetMap contributors"
