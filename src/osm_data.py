"""
osm_data.py - fill the data/ CSVs from OpenStreetMap instead of reading Google Maps by hand.

    python main.py --fetch-osm

1. Coordinates: every location whose latitude/longitude is blank is looked up with
   Nominatim (OpenStreetMap's geocoder). A match is accepted only when it lies inside
   Cagayan de Oro; otherwise the row is left blank for you to fill in by hand.
2. Distances: for every ordered pair (i, j) the OSRM car router (OpenStreetMap road
   network) returns the driving distance of its route from i to j. Both directions
   are requested separately, so one-way streets give an asymmetric matrix.
3. data_sources.csv gets one ACTUAL row per directed edge (distance, source, date and
   time of the request in Philippine time, main roads used), then the matrix is built.

Usage policies respected: one request per second, an identifying User-Agent, and
results are cached in the CSVs so the servers are queried only once.
"""
from __future__ import annotations

import csv
import json
import re
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

from src import config
from src.data_loader import (CDO_LAT_RANGE, CDO_LON_RANGE, LOCATION_COLUMNS, SOURCE_COLUMNS,
                             build_matrix_from_sources, directed_pairs_in_entry_order,
                             load_locations)

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OSRM_URL = "https://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}"
USER_AGENT = "tsp_sa_cdo/1.0 (university course project; educational use)"
PH_TIME = timezone(timedelta(hours=8))
OSRM_SOURCE = "OpenStreetMap road network via OSRM car router (router.project-osrm.org)"
DECIMALS = 2  # OSRM returns metres; keep 10 m resolution (0.01 km)


def get_json(url: str, params: dict | None = None) -> object:
    """GET a JSON document (the one network call; tests replace it with a fake)."""
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def in_cdo(lat: float, lon: float) -> bool:
    return (CDO_LAT_RANGE[0] <= lat <= CDO_LAT_RANGE[1]
            and CDO_LON_RANGE[0] <= lon <= CDO_LON_RANGE[1])


# ---------------------------------------------------------------------------
# 1. Coordinates
# ---------------------------------------------------------------------------
GENERIC_WORDS = {"hospital", "medical", "center", "centre", "general", "inc", "the", "of",
                 "and", "de", "oro", "cagayan", "city", "misamis", "oriental"}


def key_words(text: str) -> set[str]:
    """Distinctive words of a place name: 'Polymedic Medical Plaza' -> {'polymedic', 'plaza'}."""
    words = re.findall(r"[a-z]+", text.lower())
    return {w for w in words if w not in GENERIC_WORDS and len(w) > 1}


def search_queries(name: str, map_url: str = "") -> list[str]:
    """Full name, name without '(...)', and the query of the Google Maps search link."""
    queries = [name, re.sub(r"\(.*?\)", " ", name).strip()]
    query = urllib.parse.parse_qs(urllib.parse.urlparse(map_url).query).get("query")
    if query:
        queries.append(query[0])
    return list(dict.fromkeys(q for q in queries if q))


def local_part(display_name: str) -> str:
    """'Sabal Hospital, Velez Street, Barangay 2, Cagayan de Oro, ..., Northern Mindanao, ...'
    -> 'Sabal Hospital, Velez Street, Barangay 2' (name, street, barangay; no region)."""
    parts = display_name.split(", ")
    for k, part in enumerate(parts):
        if "Cagayan de Oro" in part:
            return ", ".join(parts[:k])
    return ", ".join(parts[:3])


def geocode(name: str, fetch=get_json, map_url: str = "", pause: float = 0.0,
            other_names: tuple[str, ...] = ()) -> dict | None:
    """Nominatim match inside Cagayan de Oro whose name/street contains every distinctive
    word of one of the search queries and no distinctive word that belongs only to another
    location (so 'Polymedic Medical Plaza' never matches 'Polymedic General Hospital').
    Returns None when nothing safe is found."""
    forbidden = set().union(*(key_words(o) for o in other_names)) - key_words(name)
    for query in search_queries(name, map_url):
        params = {"q": f"{query}, Cagayan de Oro", "format": "jsonv2", "limit": 5,
                  "countrycodes": "ph", "viewbox": "124.45,8.60,124.85,8.20", "bounded": 1}
        hits = fetch(NOMINATIM_URL, params)
        time.sleep(pause)
        for hit in hits:
            lat, lon = float(hit["lat"]), float(hit["lon"])
            found = key_words(local_part(hit.get("display_name", "")))
            if in_cdo(lat, lon) and key_words(query) <= found and not found & forbidden:
                return {"lat": lat, "lon": lon, "osm": f"{hit.get('osm_type')}/{hit.get('osm_id')}",
                        "display_name": hit.get("display_name", ""), "query": query}
    return None


def fill_missing_coordinates(data_dir: Path, fetch=get_json, pause: float = 1.0) -> list[str]:
    """Geocode rows with blank latitude/longitude. Returns the names that were not found."""
    path = data_dir / config.LOCATIONS_FILE
    with path.open(newline="", encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))
    not_found = []
    for row in rows:
        if row["latitude"].strip() and row["longitude"].strip():
            continue
        others = tuple(r["name"] for r in rows if r is not row)
        hit = geocode(row["name"], fetch, row.get("google_maps_url", ""), pause, others)
        if hit is None:
            not_found.append(row["name"])
            print(f"  NOT FOUND in OpenStreetMap: {row['label']} {row['name']} -> fill in by hand")
            continue
        row["latitude"], row["longitude"] = f"{hit['lat']:.6f}", f"{hit['lon']:.6f}"
        row["notes"] = (f"coordinates: OpenStreetMap Nominatim {hit['osm']} "
                        f"({hit['display_name'][:80]}); " + row.get("notes", ""))
        print(f"  {row['label']} {row['short_name']:<10} {row['latitude']}, {row['longitude']}"
              f"  <- {hit['display_name'][:70]}")
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=LOCATION_COLUMNS)
        writer.writeheader()
        writer.writerows({c: r.get(c, "") for c in LOCATION_COLUMNS} for r in rows)
    return not_found


# ---------------------------------------------------------------------------
# 2. Directed driving distances
# ---------------------------------------------------------------------------
def osrm_route(a, b, fetch=get_json) -> tuple[float, str]:
    """Driving distance in km from location a to location b, and the main roads used."""
    url = OSRM_URL.format(lon1=a.longitude, lat1=a.latitude, lon2=b.longitude, lat2=b.latitude)
    data = fetch(url, {"overview": "false", "steps": "false"})
    if data.get("code") != "Ok" or not data.get("routes"):
        raise RuntimeError(f"OSRM found no route {a.label}->{b.label}: {data.get('code')}")
    route = data["routes"][0]
    summary = route["legs"][0].get("summary", "") if route.get("legs") else ""
    return round(route["distance"] / 1000.0, DECIMALS), summary


def fetch_distances(data_dir: Path, fetch=get_json, pause: float = 1.0) -> Path:
    """Query every directed pair and write data_sources.csv + distance_matrix.csv."""
    locations = load_locations(data_dir / config.LOCATIONS_FILE)
    missing = [l.label for l in locations if l.latitude is None or l.longitude is None]
    if missing:
        raise ValueError(f"coordinates missing for {missing}; fill them in first")
    rows = []
    for i, j in directed_pairs_in_entry_order(len(locations)):
        a, b = locations[i], locations[j]
        km, summary = osrm_route(a, b, fetch)
        now = datetime.now(PH_TIME)
        rows.append({"from_label": a.label, "to_label": b.label,
                     "from_short_name": a.short_name, "to_short_name": b.short_name,
                     "distance_km": f"{km:.{DECIMALS}f}", "status": "ACTUAL",
                     "source": OSRM_SOURCE, "measured_date": now.strftime("%Y-%m-%d"),
                     "measured_time": now.strftime("%H:%M"),
                     "route_summary": f"via {summary}" if summary else "",
                     "assumed_basis": "", "notes": "OSRM car profile; distance of its route"})
        print(f"  {a.label}->{b.label}  {km:6.2f} km  {rows[-1]['route_summary']}")
        time.sleep(pause)
    path = data_dir / config.SOURCES_FILE
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=SOURCE_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    build_matrix_from_sources(data_dir)
    return path


def fetch_all(data_dir: Path = config.DATA_DIR) -> None:
    print("Step 1/2 - coordinates from OpenStreetMap (only for blank rows)")
    not_found = fill_missing_coordinates(data_dir)
    if not_found:
        print(f"\nStopping: add coordinates for {not_found} in data/locations.csv "
              f"(Google Maps: right-click the pin), then run --fetch-osm again.")
        return
    print("\nStep 2/2 - directed driving distances from OSRM (about 1-2 minutes)")
    fetch_distances(data_dir)
    print("\nDone. Next: python main.py --validate")
