"""
maps.py - the route on a real map.

* make_folium_map   interactive HTML (OpenStreetMap), numbered stops, direction arrows,
                    a Google Maps directions link for every leg and for the whole route
* make_static_map   PNG for the slides. Uses OpenStreetMap tiles when the internet is
                    available; otherwise draws the same picture on a plain background.

The straight lines show the VISITING ORDER, not the road geometry. Each leg's
length in km is the driving distance from the matrix.
"""
from __future__ import annotations

import html
import math
import urllib.request
from io import BytesIO
from pathlib import Path

import folium
import matplotlib.pyplot as plt
from folium.plugins import PolyLineTextPath
from PIL import Image

from src import config
from src.data_loader import Dataset
from src.report import fmt_km
from src.visualize import BLUE, INK, INK2, MUTED, ORANGE, SURFACE, save

TILE = 256


# ---------------------------------------------------------------------------
# Google Maps links
# ---------------------------------------------------------------------------
def _latlon(ds: Dataset, v: int) -> str:
    loc = ds.locations[v]
    return f"{loc.latitude:.6f},{loc.longitude:.6f}"


def leg_directions_url(ds: Dataset, a: int, b: int) -> str:
    return ("https://www.google.com/maps/dir/?api=1&travelmode=driving"
            f"&origin={_latlon(ds, a)}&destination={_latlon(ds, b)}")


def route_directions_url(ds: Dataset, route: list[int]) -> str:
    """One link that opens the whole route in Google Maps (max 9 waypoints)."""
    waypoints = "%7C".join(_latlon(ds, v) for v in route[1:-1])
    return ("https://www.google.com/maps/dir/?api=1&travelmode=driving"
            f"&origin={_latlon(ds, route[0])}&destination={_latlon(ds, route[-1])}"
            f"&waypoints={waypoints}")


# ---------------------------------------------------------------------------
# Interactive HTML map
# ---------------------------------------------------------------------------
def _marker_html(text: str, depot: bool) -> str:
    shape = "border-radius:4px;" if depot else "border-radius:50%;"
    colour = ORANGE if depot else BLUE
    return (f'<div style="background:{colour};color:white;{shape}width:30px;height:30px;'
            f'line-height:30px;text-align:center;font:bold 15px sans-serif;'
            f'border:2px solid white;box-shadow:0 0 3px #0006;">{text}</div>')


def _legend_html(ds: Dataset, route: list[int], total: float, url: str) -> str:
    stops = "".join(f"<li>{html.escape(ds.labels[v])} {html.escape(ds.display_name(v))}</li>"
                    for v in route[1:-1])
    warn = ('<div style="color:#d03b3b;font-weight:bold;font-size:16px">PLACEHOLDER DATA - '
            'not real distances</div>') if ds.is_placeholder else ""
    return (f'<div style="position:fixed;top:12px;right:12px;z-index:9999;background:white;'
            f'padding:10px 14px;border-radius:6px;box-shadow:0 0 6px #0004;'
            f'font:14px sans-serif;max-width:300px">{warn}'
            f'<b style="font-size:16px">Blood-delivery route: {fmt_km(total)} km</b><br>'
            f'Start/end: {html.escape(ds.display_name(route[0]))} (D)<ol>{stops}</ol>'
            f'<a href="{url}" target="_blank">Open the whole route in Google Maps</a><br>'
            f'<span style="color:{MUTED};font-size:11px">Lines show visiting order, not road '
            f'geometry. Data fingerprint {ds.fingerprint}</span></div>')


def make_folium_map(ds: Dataset, route: list[int], D: list[list[float]], total: float,
                    path: Path) -> Path:
    lats = [l.latitude for l in ds.locations]
    lons = [l.longitude for l in ds.locations]
    m = folium.Map(location=[sum(lats) / len(lats), sum(lons) / len(lons)], zoom_start=14,
                   tiles="OpenStreetMap", control_scale=True)
    for k, (a, b) in enumerate(zip(route[:-1], route[1:]), start=1):
        pa, pb = ds.locations[a], ds.locations[b]
        text = f"Leg {k}: {ds.labels[a]} → {ds.labels[b]} = {fmt_km(D[a][b])} km"
        popup = f'{html.escape(text)}<br><a href="{leg_directions_url(ds, a, b)}" ' \
                f'target="_blank">driving directions</a>'
        line = folium.PolyLine([(pa.latitude, pa.longitude), (pb.latitude, pb.longitude)],
                               color=BLUE, weight=4, opacity=0.9, tooltip=text,
                               popup=folium.Popup(popup, max_width=260))
        line.add_to(m)
        PolyLineTextPath(line, "   ►   ", repeat=True, offset=7,
                         attributes={"fill": BLUE, "font-size": "16"}).add_to(m)
    for order, v in enumerate(route[:-1]):
        loc, depot = ds.locations[v], v == config.DEPOT
        info = (f"<b>{html.escape(loc.label)} {html.escape(loc.name)}</b><br>"
                f"{html.escape(loc.address)}<br>visit #{order if not depot else 'start/end'}")
        if loc.google_maps_url:
            info += f'<br><a href="{html.escape(loc.google_maps_url)}" target="_blank">Google Maps</a>'
        folium.Marker([loc.latitude, loc.longitude],
                      icon=folium.DivIcon(html=_marker_html("D" if depot else str(order), depot),
                                          icon_size=(30, 30), icon_anchor=(15, 15)),
                      tooltip=f"{loc.label} {ds.display_name(v)}",
                      popup=folium.Popup(info, max_width=280)).add_to(m)
    m.get_root().html.add_child(folium.Element(
        _legend_html(ds, route, total, route_directions_url(ds, route))))
    m.fit_bounds([[min(lats), min(lons)], [max(lats), max(lons)]], padding=(40, 40))
    path.parent.mkdir(parents=True, exist_ok=True)
    m.save(str(path))
    return path


# ---------------------------------------------------------------------------
# Static PNG map (Web-Mercator pixel coordinates)
# ---------------------------------------------------------------------------
def to_pixels(lat: float, lon: float, zoom: int) -> tuple[float, float]:
    """Latitude/longitude -> global Web-Mercator pixel coordinates at ``zoom``."""
    scale = TILE * 2 ** zoom
    x = (lon + 180.0) / 360.0 * scale
    lat_r = math.radians(lat)
    y = (1 - math.log(math.tan(lat_r) + 1 / math.cos(lat_r)) / math.pi) / 2 * scale
    return x, y


def choose_zoom(ds: Dataset, max_w: int = 1100, max_h: int = 850) -> int:
    for zoom in range(17, 9, -1):
        pts = [to_pixels(l.latitude, l.longitude, zoom) for l in ds.locations]
        w = max(p[0] for p in pts) - min(p[0] for p in pts)
        h = max(p[1] for p in pts) - min(p[1] for p in pts)
        if w <= max_w and h <= max_h:
            return zoom
    return 10


def fetch_tile(z: int, x: int, y: int, cache: Path) -> Image.Image:
    """Download one OpenStreetMap tile (cached on disk so it is fetched only once)."""
    file = cache / f"{z}_{x}_{y}.png"
    if not file.exists():
        req = urllib.request.Request(config.TILE_URL.format(z=z, x=x, y=y),
                                     headers={"User-Agent": config.TILE_USER_AGENT})
        with urllib.request.urlopen(req, timeout=config.TILE_TIMEOUT_S) as resp:
            data = resp.read()
        cache.mkdir(parents=True, exist_ok=True)
        file.write_bytes(data)
    return Image.open(BytesIO(file.read_bytes())).convert("RGB")


def basemap(bounds: tuple[float, float, float, float], zoom: int, cache: Path,
            fetch=fetch_tile) -> Image.Image:
    """Stitch the tiles covering pixel bounds (x0, y0, x1, y1) and crop to them."""
    x0, y0, x1, y1 = bounds
    tx0, ty0, tx1, ty1 = int(x0 // TILE), int(y0 // TILE), int(x1 // TILE), int(y1 // TILE)
    canvas = Image.new("RGB", ((tx1 - tx0 + 1) * TILE, (ty1 - ty0 + 1) * TILE), "white")
    for tx in range(tx0, tx1 + 1):
        for ty in range(ty0, ty1 + 1):
            canvas.paste(fetch(zoom, tx, ty, cache), ((tx - tx0) * TILE, (ty - ty0) * TILE))
    left, top = x0 - tx0 * TILE, y0 - ty0 * TILE
    return canvas.crop((int(left), int(top), int(left + x1 - x0), int(top + y1 - y0)))


def make_static_map(ds: Dataset, route: list[int], D: list[list[float]], total: float,
                    path: Path, use_tiles: bool = config.USE_BASEMAP_TILES,
                    fetch=fetch_tile) -> tuple[Path, bool]:
    """Route map as a PNG. Returns (path, True if OpenStreetMap tiles were used)."""
    fig, ax, px, used_tiles = _map_axes(ds, use_tiles, fetch)
    _draw_route(ax, ds, route, D, px)
    ax.set_title(f"Blood-delivery route, Cagayan de Oro: {fmt_km(total)} km "
                 f"(D = depot, 1..{ds.n - 1} = visiting order)")
    return save(fig, path, ds), used_tiles


def make_locations_map(ds: Dataset, path: Path, use_tiles: bool = config.USE_BASEMAP_TILES,
                       fetch=fetch_tile) -> Path:
    """The vertices only (no route), for introducing the locations before solving."""
    fig, ax, px, _ = _map_axes(ds, use_tiles, fetch)
    obstacles = list(px.values())
    for loc in ds.locations:
        depot = loc.id == config.DEPOT
        x, y = px[loc.id]
        z = 7 if depot else 5  # depot on top: NMMC is next door in the same compound
        ax.scatter([x], [y], s=480, marker="s" if depot else "o", color=ORANGE if depot else BLUE,
                   edgecolor=SURFACE, lw=2.5, zorder=z)
        ax.text(x, y, str(loc.id), color="white", ha="center", va="center",
                fontsize=13, weight="bold", zorder=z + 1)
        obstacles.append(_name_label(ax, f"{ds.labels[loc.id]} {ds.display_name(loc.id)}",
                                     x, y, obstacles))
    ax.set_title(f"The {ds.n} locations in Cagayan de Oro City (square = depot V0)")
    return save(fig, path, ds)


def _map_axes(ds: Dataset, use_tiles: bool, fetch):
    """Figure framed around every location, on OpenStreetMap tiles when available."""
    zoom = choose_zoom(ds)
    px = {l.id: to_pixels(l.latitude, l.longitude, zoom) for l in ds.locations}
    pad = 120
    x0, x1 = min(p[0] for p in px.values()) - pad, max(p[0] for p in px.values()) + pad
    y0, y1 = min(p[1] for p in px.values()) - pad, max(p[1] for p in px.values()) + pad
    fig, ax = plt.subplots(figsize=(13, 13 * (y1 - y0) / (x1 - x0)))
    used_tiles = False
    if use_tiles:
        try:
            img = basemap((x0, y0, x1, y1), zoom, config.OUTPUT_DIR / ".tile_cache", fetch)
            ax.imshow(img, extent=(x0, x1, y1, y0), alpha=0.85)
            used_tiles = True
        except Exception as exc:  # offline, blocked, or rate-limited -> plain background
            print(f"  (basemap tiles unavailable: {type(exc).__name__}; drawing plain map)")
    ax.set_xlim(x0, x1)
    ax.set_ylim(y1, y0)  # pixel y grows downwards
    ax.set_aspect("equal")
    ax.set_axis_off()
    credit = config.MAP_ATTRIBUTION if used_tiles else "Plain background (map tiles unavailable)"
    ax.text(0.005, 0.005, credit, transform=ax.transAxes, fontsize=10, color=INK2,
            bbox=dict(fc=SURFACE, ec="none", alpha=0.8))
    return fig, ax, px, used_tiles


def _draw_route(ax, ds: Dataset, route: list[int], D: list[list[float]], px: dict) -> None:
    obstacles = []  # points that a name label should keep away from
    for a, b in zip(route[:-1], route[1:]):
        ax.annotate("", xy=px[b], xytext=px[a], zorder=3,
                    arrowprops=dict(arrowstyle="-|>", color=BLUE, lw=3, shrinkA=17, shrinkB=17,
                                    mutation_scale=24))
        mx, my = (px[a][0] + px[b][0]) / 2, (px[a][1] + px[b][1]) / 2
        ax.text(mx, my, f"{fmt_km(D[a][b])} km", fontsize=12, color=INK, ha="center",
                va="center", zorder=8,
                bbox=dict(boxstyle="round,pad=0.15", fc=SURFACE, ec=BLUE, lw=1))
        obstacles += [(mx, my)] + [(px[a][0] + t * (px[b][0] - px[a][0]),
                                    px[a][1] + t * (px[b][1] - px[a][1])) for t in (0.25, 0.75)]
    obstacles += list(px.values())
    for order, v in enumerate(route[:-1]):
        depot = v == config.DEPOT
        x, y = px[v]
        z = 9 if depot else 5  # depot on top: NMMC is next door in the same compound
        ax.scatter([x], [y], s=650, marker="s" if depot else "o", color=ORANGE if depot else BLUE,
                   edgecolor=SURFACE, lw=2.5, zorder=z)
        ax.text(x, y, "D" if depot else str(order), color="white", ha="center", va="center",
                fontsize=14, weight="bold", zorder=z + 1)
        spot = _name_label(ax, f"{ds.labels[v]} {ds.display_name(v)}", x, y, obstacles)
        obstacles.append(spot)


def _name_label(ax, text: str, x: float, y: float, obstacles: list) -> tuple[float, float]:
    """Try 8 directions around the stop and put its name where it is farthest from the
    route lines, the km labels, the other stops and the names already placed."""
    best, best_score = None, -1.0
    for k in range(8):
        angle = math.pi / 4 * k
        dx, dy = math.cos(angle), math.sin(angle)
        cx, cy = x + dx * 55 + dx * 6 * len(text) * (abs(dx) > 0.5), y + dy * 38
        score = min(math.hypot(cx - ox, cy - oy) for ox, oy in obstacles)
        if score > best_score:
            best, best_score = (dx, dy, cx, cy), score
    dx, dy, cx, cy = best
    ha = "left" if dx > 0.35 else "right" if dx < -0.35 else "center"
    va = "top" if dy > 0.35 else "bottom" if dy < -0.35 else "center"
    ax.annotate(text, (x, y), xytext=(dx * 18, -dy * 18), textcoords="offset points",
                ha=ha, va=va, fontsize=13, color=INK, zorder=7,
                bbox=dict(boxstyle="round,pad=0.2", fc=SURFACE, ec="none", alpha=0.9))
    return cx, cy
