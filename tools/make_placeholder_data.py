"""
make_placeholder_data.py - create (1) the PLACEHOLDER demo dataset and (2) the empty
templates for the real Google Maps data.

    python tools/make_placeholder_data.py            # writes data/placeholder/ only
    python tools/make_placeholder_data.py --templates  # also (re)writes blank data/ templates

The placeholder numbers are SYNTHETIC: random points near downtown Cagayan de Oro,
with "road" distances = straight-line distance x a random detour factor (1.25-1.6),
plus a few one-way detours so the matrix is asymmetric, rounded to 0.1 km like
Google Maps. They exist only so the pipeline runs end to end. Never present them.
"""
from __future__ import annotations

import argparse
import csv
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src import config  # noqa: E402
from src.data_loader import (LOCATION_COLUMNS, MATRIX_CORNER, SOURCE_COLUMNS,  # noqa: E402
                             directed_pairs_in_entry_order)

N_HOSPITALS = 8
SEED = 20261017
CENTER = (8.4740, 124.6460)  # inland of downtown Cagayan de Oro (coast is to the north)


def haversine_km(a: tuple[float, float], b: tuple[float, float]) -> float:
    lat1, lon1, lat2, lon2 = map(math.radians, (*a, *b))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(h))


def placeholder_points(rng: random.Random, n: int) -> list[tuple[float, float]]:
    pts = [CENTER]
    while len(pts) < n:
        p = (CENTER[0] + rng.uniform(-0.030, 0.010), CENTER[1] + rng.uniform(-0.030, 0.030))
        if all(haversine_km(p, q) > 0.7 for q in pts):
            pts.append(p)
    return pts


def placeholder_matrix(rng: random.Random, pts: list) -> list[list[float]]:
    n = len(pts)
    D = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            base = haversine_km(pts[i], pts[j]) * rng.uniform(1.25, 1.6)
            D[i][j] = D[j][i] = round(base, 1)
            if rng.random() < 0.35:  # one-way street detour in one direction
                k = (i, j) if rng.random() < 0.5 else (j, i)
                D[k[0]][k[1]] = round(base + rng.uniform(0.3, 1.5), 1)
    return D


def write_dataset(folder: Path, names: list[tuple[str, str]], pts: list, D, status: str) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    n = len(names)
    with (folder / config.LOCATIONS_FILE).open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(LOCATION_COLUMNS)
        for i, (name, short) in enumerate(names):
            lat, lon = pts[i] if pts else ("", "")
            w.writerow([i, f"V{i}", name, short, "depot" if i == 0 else "stop",
                        "PLACEHOLDER - synthetic point" if pts else "",
                        f"{lat:.6f}" if pts else "", f"{lon:.6f}" if pts else "", "",
                        "synthetic demo vertex" if pts else ""])
    with (folder / config.MATRIX_FILE).open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow([MATRIX_CORNER] + [f"V{j}" for j in range(n)])
        for i in range(n):
            w.writerow([f"V{i}"] + ["0" if i == j else (f"{D[i][j]:g}" if D else "")
                                    for j in range(n)])
    with (folder / config.SOURCES_FILE).open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=SOURCE_COLUMNS)
        w.writeheader()
        for i, j in directed_pairs_in_entry_order(n):
            row = {c: "" for c in SOURCE_COLUMNS}
            row.update(from_label=f"V{i}", to_label=f"V{j}",
                       from_short_name=names[i][1], to_short_name=names[j][1])
            if D:
                row.update(distance_km=f"{D[i][j]:g}", status=status,
                           source="SYNTHETIC (haversine x detour factor) - not Google Maps",
                           notes="placeholder only")
            w.writerow(row)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("--templates", action="store_true",
                        help="also overwrite the blank real-data templates in data/")
    args = parser.parse_args()
    rng = random.Random(SEED)
    n = N_HOSPITALS + 1
    names = [("PLACEHOLDER Depot (Red Cross chapter office)", "Depot*")] + [
        (f"PLACEHOLDER Hospital {chr(65 + k)}", f"Hosp {chr(65 + k)}*") for k in range(N_HOSPITALS)]
    pts = placeholder_points(rng, n)
    write_dataset(config.PLACEHOLDER_DIR, names, pts, placeholder_matrix(rng, pts), "PLACEHOLDER")
    print(f"wrote placeholder dataset to {config.PLACEHOLDER_DIR}")
    if args.templates:
        blank = [("", "")] * n
        write_dataset(config.DATA_DIR, blank, [], None, "")
        print(f"wrote blank templates to {config.DATA_DIR}")


if __name__ == "__main__":
    main()
