"""Map helpers that can be tested offline (tile stitching uses a fake tile server)."""
from PIL import Image

from src import config
from src.data_loader import load_dataset
from src.maps import basemap, make_dataset_map, route_directions_url, to_pixels


def test_route_url_lists_every_stop_in_order():
    ds = load_dataset(config.DATA_DIR)
    route = [0, 3, 1, 2, 4, 5, 6, 7, 8, 0]
    url = route_directions_url(ds, route)
    assert url.count("%7C") == 7  # 8 waypoints -> 7 separators
    assert "travelmode=driving" in url


def test_web_mercator_known_point():
    x, y = to_pixels(0.0, 0.0, 1)  # (0, 0) is the centre of the 512 x 512 world at zoom 1
    assert round(x) == 256 and round(y) == 256


def test_basemap_stitches_and_crops(tmp_path):
    calls = []

    def fake_fetch(z, x, y, cache):
        calls.append((z, x, y))
        return Image.new("RGB", (256, 256), (x % 255, y % 255, 0))

    img = basemap((300.0, 100.0, 900.0, 400.0), 3, tmp_path, fetch=fake_fetch)
    assert img.size == (600, 300)
    assert len(calls) == 3 * 2  # tiles x 1..3, y 0..1


def test_dataset_map_shows_every_location_and_pair(tmp_path):
    ds = load_dataset(config.DATA_DIR)
    D = [[float(v) for v in row] for row in ds.matrix]
    page = make_dataset_map(ds, D, tmp_path / "m.html").read_text(encoding="utf-8")
    assert all(loc.label in page for loc in ds.locations)
    assert page.count("L.polyline(") == ds.n * (ds.n - 1) // 2
    assert f"V0 → V1 = {D[0][1]:g} km" in page and f"V1 → V0 = {D[1][0]:g} km" in page
