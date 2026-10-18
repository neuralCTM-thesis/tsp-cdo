"""OpenStreetMap fetcher, tested offline with a fake server."""
import csv
import shutil

from src import config
from src.data_loader import load_dataset, validate_dataset
from src.osm_data import fetch_distances, fill_missing_coordinates, geocode, search_queries


def fake_nominatim(url, params):
    if "Nowhere" in params["q"]:
        return []
    if "Outside" in params["q"]:
        return [{"lat": "14.6", "lon": "121.0", "osm_type": "way", "osm_id": 1}]  # Manila
    return [{"lat": "8.4800", "lon": "124.6500", "osm_type": "way", "osm_id": 42,
             "display_name": "Some Hospital, Cagayan de Oro"}] if "Some" in params["q"] or \
        "Hospital A" in params["q"] else []


REGION = "Cagayan de Oro, Misamis Oriental, Northern Mindanao, 9000, Philippines"


def test_geocode_never_confuses_two_polymedic_hospitals():
    general = {"lat": "8.47", "lon": "124.64", "osm_type": "way", "osm_id": 7,
               "display_name": f"Polymedic General Hospital, Velez Street, {REGION}"}
    plaza = {"lat": "8.48", "lon": "124.62", "osm_type": "way", "osm_id": 8,
             "display_name": f"Polymedic Medical Plaza, Kauswagan Highway, {REGION}"}
    names = ("Polymedic Medical Plaza", "Cagayan de Oro Polymedic General Hospital")
    only_general = lambda url, params: [general]  # noqa: E731
    only_plaza = lambda url, params: [plaza]  # noqa: E731
    assert geocode(names[0], only_general, other_names=names[1:]) is None
    assert geocode(names[1], only_general, other_names=names[:1])["osm"] == "way/7"
    assert geocode(names[1], only_plaza, other_names=names[:1]) is None


def test_region_name_does_not_count_as_a_match():
    any_hospital = lambda url, params: [{"lat": "8.47", "lon": "124.64", "osm_type": "node",  # noqa: E731
                                         "osm_id": 1, "display_name": f"Sabal Hospital, {REGION}"}]
    assert geocode("Northern Mindanao Medical Center", any_hospital) is None


def test_search_queries_include_short_forms():
    url = "https://www.google.com/maps/search/?api=1&query=ACE+Medical+Center+Cagayan+de+Oro"
    qs = search_queries("Allied Care Experts (ACE) Medical Center - Cagayan de Oro", url)
    assert qs[-1] == "ACE Medical Center Cagayan de Oro" and "(ACE)" not in qs[1]


def test_geocode_accepts_only_points_in_cdo():
    assert geocode("Some Hospital", fake_nominatim)["osm"] == "way/42"
    assert geocode("Outside Hospital", fake_nominatim) is None
    assert geocode("Nowhere Hospital", fake_nominatim) is None


def test_fill_missing_coordinates_keeps_existing_and_reports_missing(tmp_path):
    shutil.copytree(config.DATA_DIR, tmp_path / "d")
    path = tmp_path / "d" / config.LOCATIONS_FILE
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    rows[1]["latitude"] = rows[1]["longitude"] = ""
    rows[2]["latitude"] = rows[2]["longitude"] = ""
    rows[2]["name"] = "Nowhere Hospital"
    rows[1]["name"] = "Some Hospital"
    kept = rows[3]["latitude"]
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)
    missing = fill_missing_coordinates(tmp_path / "d", fetch=fake_nominatim, pause=0)
    after = list(csv.DictReader(path.open(encoding="utf-8")))
    assert missing == ["Nowhere Hospital"]
    assert after[1]["latitude"] == "8.480000" and "Nominatim way/42" in after[1]["notes"]
    assert after[3]["latitude"] == kept


def test_fetch_distances_builds_a_valid_asymmetric_dataset(tmp_path):
    shutil.copytree(config.DATA_DIR, tmp_path / "d")

    def fake_osrm(url, params):
        coords = url.rsplit("/", 1)[1].split(";")
        (lon1, lat1), (lon2, lat2) = (map(float, c.split(",")) for c in coords)
        metres = 1000 + abs(lat1 - lat2) * 1e5 + abs(lon1 - lon2) * 1e5 + (300 if lat1 < lat2 else 0)
        return {"code": "Ok", "routes": [{"distance": metres, "legs": [{"summary": "Corrales Ave"}]}]}

    fetch_distances(tmp_path / "d", fetch=fake_osrm, pause=0)
    ds = load_dataset(tmp_path / "d")
    rep = validate_dataset(ds)
    assert rep.ok, rep.errors
    assert rep.status_counts == {"ACTUAL": 72}
    assert rep.asymmetric_pairs  # the +300 m in one direction makes the matrix directed
    assert ds.sources[(0, 1)].route_summary == "via Corrales Ave"
