"""
data_loader.py - read the three CSV files in data/ and validate them.

Files (row = FROM, column = TO; distances in km):
    locations.csv        one row per vertex V0..V(n-1); V0 is the depot
    distance_matrix.csv  full n x n DIRECTED matrix (A->B may differ from B->A)
    data_sources.csv     one row per directed edge: ACTUAL (read from a map / routing
                         service, with date/time) or ASSUMED (e.g. copied from the
                         reverse direction)

The validator never "fixes" data silently. It returns a list of errors (the
program refuses to run) and warnings (the program runs but prints them).
"""
from __future__ import annotations

import csv
import math
from dataclasses import dataclass, field
from pathlib import Path

from src import config

LOCATION_COLUMNS = ["id", "label", "name", "short_name", "role", "address",
                    "latitude", "longitude", "google_maps_url", "notes"]
SOURCE_COLUMNS = ["from_label", "to_label", "from_short_name", "to_short_name",
                  "distance_km", "status", "source", "measured_date",
                  "measured_time", "route_summary", "assumed_basis", "notes"]
VALID_STATUSES = ("ACTUAL", "ASSUMED")
VALID_ROLES = ("depot", "stop")
MATRIX_CORNER = "from\\to"

# Rough bounding box of Cagayan de Oro City (used only for a warning).
CDO_LAT_RANGE = (8.20, 8.60)
CDO_LON_RANGE = (124.45, 124.85)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------
@dataclass
class Location:
    """One vertex of the graph (a row of locations.csv)."""
    id: int
    label: str
    name: str
    short_name: str
    role: str
    address: str
    latitude: float | None
    longitude: float | None
    google_maps_url: str
    notes: str


@dataclass
class EdgeSource:
    """Provenance of one directed edge (a row of data_sources.csv)."""
    from_label: str
    to_label: str
    distance_km: float | None
    status: str
    source: str
    measured_date: str
    measured_time: str
    route_summary: str
    assumed_basis: str
    notes: str


@dataclass
class Dataset:
    """Everything the algorithms need, loaded from one data folder."""
    data_dir: Path
    locations: list[Location]
    matrix: list[list[float | None]]
    matrix_labels: list[str]
    sources: dict[tuple[int, int], EdgeSource]
    load_errors: list[str] = field(default_factory=list)

    @property
    def n(self) -> int:
        return len(self.locations)

    @property
    def labels(self) -> list[str]:
        return [loc.label for loc in self.locations]

    def edge_status(self, i: int, j: int) -> str:
        """ACTUAL / ASSUMED (or MISSING) for the edge i -> j."""
        src = self.sources.get((i, j))
        return src.status if src else "MISSING"

    @property
    def source_label(self) -> str:
        """Short name of where the distances come from (figure footers, console)."""
        text = " ".join(s.source for s in self.sources.values()).lower()
        if "osrm" in text or "openstreetmap" in text:
            return "OpenStreetMap/OSRM road distances"
        if "google" in text:
            return "Google Maps driving distances"
        return "measured road distances"

    def display_name(self, i: int) -> str:
        loc = self.locations[i]
        return loc.short_name or loc.name or loc.label


@dataclass
class ValidationReport:
    """Result of validate_dataset()."""
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    asymmetric_pairs: list[tuple[int, int, float, float]] = field(default_factory=list)
    assumed_edges: list[tuple[int, int]] = field(default_factory=list)
    status_counts: dict[str, int] = field(default_factory=dict)
    triangle_violations: list[tuple[int, int, int, float, float]] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


# ---------------------------------------------------------------------------
# Small parsing helpers
# ---------------------------------------------------------------------------
def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    """Read a CSV into a list of dicts. Accepts UTF-8 (with/without BOM) or cp1252."""
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            with path.open(newline="", encoding=encoding) as fh:
                return [{(k or "").strip(): (v or "").strip() for k, v in row.items()}
                        for row in csv.DictReader(fh)]
        except UnicodeDecodeError:
            continue
    raise ValueError(f"{path.name}: cannot decode file (save it as 'CSV UTF-8').")


def _to_float(text: str) -> float | None:
    """'2.5' -> 2.5 ; '' -> None ; 'abc' -> nan (reported by the validator)."""
    text = text.strip().replace(",", "")
    if text == "":
        return None
    try:
        return float(text)
    except ValueError:
        return math.nan


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------
def load_locations(path: Path) -> list[Location]:
    rows = _read_csv_rows(path)
    locations = []
    for row in rows:
        id_text = row.get("id", "")
        locations.append(Location(
            id=int(id_text) if id_text.lstrip("-").isdigit() else -1,
            label=row.get("label", ""),
            name=row.get("name", ""),
            short_name=row.get("short_name", ""),
            role=row.get("role", "").lower(),
            address=row.get("address", ""),
            latitude=_to_float(row.get("latitude", "")),
            longitude=_to_float(row.get("longitude", "")),
            google_maps_url=row.get("google_maps_url", ""),
            notes=row.get("notes", ""),
        ))
    return locations


def load_matrix(path: Path) -> tuple[list[str], list[str], list[list[float | None]]]:
    """Return (column labels, row labels, matrix). Blank cells become None."""
    with path.open(newline="", encoding="utf-8-sig") as fh:
        table = [[cell.strip() for cell in row] for row in csv.reader(fh) if row]
    col_labels = table[0][1:]
    row_labels = [row[0] for row in table[1:]]
    matrix = [[_to_float(cell) for cell in row[1:]] for row in table[1:]]
    return col_labels, row_labels, matrix


def load_sources(path: Path, label_to_id: dict[str, int]) -> tuple[dict, list[str]]:
    """Return ({(i, j): EdgeSource}, problems found while reading)."""
    sources: dict[tuple[int, int], EdgeSource] = {}
    problems: list[str] = []
    for line_no, row in enumerate(_read_csv_rows(path), start=2):
        f_lab, t_lab = row.get("from_label", ""), row.get("to_label", "")
        if f_lab not in label_to_id or t_lab not in label_to_id:
            problems.append(f"{path.name} line {line_no}: unknown label '{f_lab}' or '{t_lab}'.")
            continue
        key = (label_to_id[f_lab], label_to_id[t_lab])
        if key in sources:
            problems.append(f"{path.name} line {line_no}: duplicate row for {f_lab}->{t_lab}.")
        sources[key] = EdgeSource(
            from_label=f_lab, to_label=t_lab,
            distance_km=_to_float(row.get("distance_km", "")),
            status=row.get("status", "").upper(),
            source=row.get("source", ""),
            measured_date=row.get("measured_date", ""),
            measured_time=row.get("measured_time", ""),
            route_summary=row.get("route_summary", ""),
            assumed_basis=row.get("assumed_basis", ""),
            notes=row.get("notes", ""),
        )
    return sources, problems


def load_dataset(data_dir: Path) -> Dataset:
    """Load the three CSVs from ``data_dir`` (no validation yet)."""
    locations = load_locations(data_dir / config.LOCATIONS_FILE)
    col_labels, row_labels, matrix = load_matrix(data_dir / config.MATRIX_FILE)
    load_errors = []
    if row_labels != col_labels:
        load_errors.append(f"{config.MATRIX_FILE}: row labels {row_labels} differ from "
                           f"column labels {col_labels}.")
    label_to_id = {loc.label: loc.id for loc in locations}
    sources, problems = load_sources(data_dir / config.SOURCES_FILE, label_to_id)
    load_errors.extend(problems)
    return Dataset(data_dir=data_dir, locations=locations, matrix=matrix,
                   matrix_labels=col_labels, sources=sources, load_errors=load_errors)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
def _check_locations(ds: Dataset, rep: ValidationReport) -> None:
    n = ds.n
    if not 3 <= n <= config.BRUTE_FORCE_MAX_N:
        rep.errors.append(f"locations.csv has {n} vertices; expected 3..{config.BRUTE_FORCE_MAX_N}.")
    for idx, loc in enumerate(ds.locations):
        where = f"locations.csv row {idx + 2}"
        if loc.id != idx:
            rep.errors.append(f"{where}: id must be {idx} (ids are 0..n-1 in file order), got {loc.id}.")
        if loc.label != f"V{idx}":
            rep.errors.append(f"{where}: label must be 'V{idx}', got '{loc.label}'.")
        if not loc.name:
            rep.errors.append(f"{where}: name is empty.")
        if loc.role not in VALID_ROLES:
            rep.errors.append(f"{where}: role must be 'depot' or 'stop', got '{loc.role}'.")
        if loc.latitude is None or loc.longitude is None or math.isnan(loc.latitude) \
                or math.isnan(loc.longitude):
            rep.errors.append(f"{where}: latitude/longitude missing or not a number.")
        elif not (CDO_LAT_RANGE[0] <= loc.latitude <= CDO_LAT_RANGE[1]
                  and CDO_LON_RANGE[0] <= loc.longitude <= CDO_LON_RANGE[1]):
            rep.warnings.append(f"{where}: ({loc.latitude}, {loc.longitude}) is outside the "
                                f"Cagayan de Oro area - latitude/longitude swapped?")
        if not loc.google_maps_url:
            rep.warnings.append(f"{where}: google_maps_url is empty.")
    depots = [loc.id for loc in ds.locations if loc.role == "depot"]
    if depots != [config.DEPOT]:
        rep.errors.append(f"Exactly one depot is required and it must be V{config.DEPOT}; "
                          f"found depot rows {depots}.")


def _check_matrix(ds: Dataset, rep: ValidationReport) -> None:
    n, D = ds.n, ds.matrix
    if ds.matrix_labels != ds.labels:
        rep.errors.append(f"distance_matrix.csv labels {ds.matrix_labels} do not match "
                          f"locations.csv labels {ds.labels}.")
    if len(D) != n or any(len(row) != n for row in D):
        rep.errors.append(f"distance_matrix.csv must be {n} x {n} (square, one row and one "
                          f"column per location); got {len(D)} rows with lengths "
                          f"{[len(r) for r in D]}.")
        return
    for i in range(n):
        for j in range(n):
            v, cell = D[i][j], f"distance_matrix[{ds.labels[i]}->{ds.labels[j]}]"
            if v is None:
                rep.errors.append(f"{cell} is blank.")
            elif math.isnan(v):
                rep.errors.append(f"{cell} is not a number.")
            elif i == j and v != 0:
                rep.errors.append(f"{cell} is on the diagonal and must be 0, got {v}.")
            elif i != j and v <= 0:
                rep.errors.append(f"{cell} must be a positive distance, got {v}.")
            elif i != j and v > 100:
                rep.warnings.append(f"{cell} = {v} km looks too large (metres typed as km?).")


def _matrix_is_numeric(ds: Dataset) -> bool:
    return (len(ds.matrix) == ds.n
            and all(len(r) == ds.n and all(v is not None and not math.isnan(v) for v in r)
                    for r in ds.matrix))


def _check_sources(ds: Dataset, rep: ValidationReport) -> None:
    n = ds.n
    for i in range(n):
        for j in range(n):
            if i == j:
                if (i, j) in ds.sources:
                    rep.errors.append(f"data_sources.csv: remove the diagonal row "
                                      f"{ds.labels[i]}->{ds.labels[j]}.")
                continue
            src = ds.sources.get((i, j))
            edge = f"{ds.labels[i]}->{ds.labels[j]}"
            if src is None:
                rep.errors.append(f"data_sources.csv: no row for edge {edge}.")
                continue
            if src.status not in VALID_STATUSES:
                rep.errors.append(f"data_sources.csv {edge}: status must be ACTUAL or ASSUMED, "
                                  f"got '{src.status}'.")
            rep.status_counts[src.status] = rep.status_counts.get(src.status, 0) + 1
            if src.status == "ASSUMED":
                rep.assumed_edges.append((i, j))
                if not src.assumed_basis:
                    rep.warnings.append(f"data_sources.csv {edge}: ASSUMED but assumed_basis "
                                        f"is empty (e.g. 'copied from {ds.labels[j]}->"
                                        f"{ds.labels[i]}').")
            if src.status == "ACTUAL" and not (src.measured_date and src.measured_time):
                rep.errors.append(f"data_sources.csv {edge}: ACTUAL rows need measured_date "
                                  f"and measured_time.")
            matrix_value = ds.matrix[i][j] if _matrix_is_numeric(ds) else None
            if src.distance_km is None or math.isnan(src.distance_km):
                rep.errors.append(f"data_sources.csv {edge}: distance_km is blank/invalid.")
            elif matrix_value is not None and abs(src.distance_km - matrix_value) > config.FLOAT_TOL:
                rep.errors.append(f"{edge}: data_sources.csv says {src.distance_km} km but "
                                  f"distance_matrix.csv says {matrix_value} km.")


def _find_asymmetry_and_triangles(ds: Dataset, rep: ValidationReport) -> None:
    """Report asymmetric pairs, and triangle-inequality breaks (possible typos)."""
    D, n = ds.matrix, ds.n
    for i in range(n):
        for j in range(i + 1, n):
            if abs(D[i][j] - D[j][i]) > config.FLOAT_TOL:
                rep.asymmetric_pairs.append((i, j, D[i][j], D[j][i]))
    slack = 0.1  # allow one Google-Maps rounding step (0.1 km)
    for i in range(n):
        for k in range(n):
            if i == k:
                continue
            for j in range(n):
                if j in (i, k):
                    continue
                if D[i][k] > D[i][j] + D[j][k] + slack:
                    rep.triangle_violations.append((i, j, k, D[i][k], D[i][j] + D[j][k]))


def validate_dataset(ds: Dataset) -> ValidationReport:
    """Run every check. ``report.ok`` is False if anything would break the algorithms."""
    rep = ValidationReport(errors=list(ds.load_errors))
    _check_locations(ds, rep)
    _check_matrix(ds, rep)
    _check_sources(ds, rep)
    if rep.ok:
        _find_asymmetry_and_triangles(ds, rep)
        if rep.triangle_violations:
            rep.warnings.append(
                f"{len(rep.triangle_violations)} triangle-inequality breaks "
                f"(d(i,k) > d(i,j) + d(j,k) + 0.1 km). Possible on real roads, but "
                f"double-check these entries for typos (see outputs/data_quality.csv).")
    return rep


def distance_matrix(ds: Dataset) -> list[list[float]]:
    """The validated matrix as plain floats (call only after validate_dataset passes)."""
    return [[float(v) for v in row] for row in ds.matrix]


# ---------------------------------------------------------------------------
# Helpers for writing the CSVs (used by main.py --fetch-osm)
# ---------------------------------------------------------------------------
def directed_pairs_in_entry_order(n: int) -> list[tuple[int, int]]:
    """V0->V1, V1->V0, V0->V2, V2->V0, ... : each pair and its reverse next to each other,
    matching how you measure them by hand (look up A->B, then press 'reverse')."""
    return [edge for i in range(n) for j in range(i + 1, n) for edge in ((i, j), (j, i))]


def build_matrix_from_sources(data_dir: Path) -> Path:
    """Write distance_matrix.csv from the distance_km column of data_sources.csv."""
    locations = load_locations(data_dir / config.LOCATIONS_FILE)
    label_to_id = {loc.label: loc.id for loc in locations}
    sources, problems = load_sources(data_dir / config.SOURCES_FILE, label_to_id)
    if problems:
        raise ValueError("\n".join(problems))
    path = data_dir / config.MATRIX_FILE
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow([MATRIX_CORNER] + [loc.label for loc in locations])
        for a in locations:
            cells = []
            for b in locations:
                src = sources.get((a.id, b.id))
                if a.id == b.id:
                    cells.append("0")
                elif src is None or src.distance_km is None:
                    cells.append("")
                else:
                    cells.append(f"{src.distance_km:g}")
            writer.writerow([a.label] + cells)
    return path
