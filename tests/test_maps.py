"""Map helpers that can be tested offline (tile stitching uses a fake tile server)."""
from PIL import Image

from src import config
from src.data_loader import load_dataset
from src.maps import basemap, route_directions_url, to_pixels


def test_route_url_lists_every_stop_in_order():
    ds = load_dataset(config.PLACEHOLDER_DIR)
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
