"""
visualize.py - every chart in outputs/ (the maps live in maps.py).

Design rules used throughout (so the figures read well in a screen recording):
  * large fonts, thin marks, hairline grids, one y-axis per chart
  * fixed colours: blue = SA / best, orange = current tour or depot, aqua = third series
  * every figure is stamped with the data source (bottom right)
"""
from __future__ import annotations

import math
import sys
from io import BytesIO
from pathlib import Path

import matplotlib

if "ipykernel" not in sys.modules:  # keep Jupyter's inline plots working
    matplotlib.use("Agg")  # render to files; works without a display
import matplotlib.pyplot as plt  # noqa: E402
import networkx as nx  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402
from PIL import Image  # noqa: E402

from src import config  # noqa: E402
from src.data_loader import Dataset  # noqa: E402
from src.report import fmt_km  # noqa: E402

# Palette (validated for colour-vision deficiency; see docs/README).
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#898781"
GRID, AXIS, SURFACE = "#e1e0d9", "#c3c2b7", "#ffffff"
SEQ_BLUES = LinearSegmentedColormap.from_list(
    "seq_blue", ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"])


# ---------------------------------------------------------------------------
# Shared style, stamping and saving
# ---------------------------------------------------------------------------
def apply_style() -> None:
    fs = config.BASE_FONT_SIZE
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": fs, "axes.titlesize": fs + 3,
        "axes.titleweight": "bold", "axes.labelsize": fs, "xtick.labelsize": fs - 2,
        "ytick.labelsize": fs - 2, "legend.fontsize": fs - 2, "legend.frameon": False,
        "axes.edgecolor": AXIS, "axes.linewidth": 1, "axes.labelcolor": INK,
        "xtick.color": INK2, "ytick.color": INK2, "text.color": INK,
        "axes.grid": True, "grid.color": GRID, "grid.linewidth": 1, "grid.linestyle": "-",
        "axes.spines.top": False, "axes.spines.right": False, "axes.axisbelow": True,
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
        "lines.linewidth": 2, "lines.solid_capstyle": "round",
    })


def stamp(fig: plt.Figure, ds: Dataset, y: float = -0.01, va: str = "top") -> None:
    """Data-source footer on every figure. The footer sits just below the figure (kept by bbox_inches='tight') so it never
    covers an axis label."""
    fig.text(0.995, y, ds.source_label, ha="right", va=va, fontsize=10, color=MUTED)


def save(fig: plt.Figure, path: Path, ds: Dataset) -> Path:
    stamp(fig, ds)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=config.FIG_DPI, bbox_inches="tight")
    plt.close(fig)
    return path


def node_label(ds: Dataset, i: int) -> str:
    return f"{ds.labels[i]}\n{ds.display_name(i)}"


def circular_positions(n: int) -> dict[int, tuple[float, float]]:
    """Vertices on a circle, depot at the top, numbering clockwise."""
    return {k: (math.cos(math.pi / 2 - 2 * math.pi * k / n),
                math.sin(math.pi / 2 - 2 * math.pi * k / n)) for k in range(n)}


def geo_positions(ds: Dataset) -> dict[int, tuple[float, float]]:
    """Longitude/latitude scaled so 1 unit east = 1 unit north on the ground."""
    lat0 = math.radians(sum(l.latitude for l in ds.locations) / ds.n)
    return {l.id: (l.longitude * math.cos(lat0), l.latitude) for l in ds.locations}


def _draw_nodes(ax, G: nx.DiGraph, pos: dict, ds: Dataset, size: int = 1500) -> None:
    hospitals = [v for v in G.nodes if v != config.DEPOT]
    nx.draw_networkx_nodes(G, pos, nodelist=hospitals, node_color=BLUE, node_size=size,
                           edgecolors=SURFACE, linewidths=2, ax=ax)
    nx.draw_networkx_nodes(G, pos, nodelist=[config.DEPOT], node_color=ORANGE,
                           node_shape="s", node_size=size, edgecolors=SURFACE, linewidths=2,
                           ax=ax)
    nx.draw_networkx_labels(G, pos, labels={v: ds.labels[v] for v in G.nodes},
                            font_color="white", font_weight="bold",
                            font_size=config.BASE_FONT_SIZE - 1, ax=ax)


def _draw_names(ax, pos: dict, ds: Dataset, push: float = 1.22) -> None:
    """Short names just outside the circle so they never sit on top of an arc."""
    for v, (x, y) in pos.items():
        ha = "left" if x > 0.15 else "right" if x < -0.15 else "center"
        va = "bottom" if y > 0.15 else "top" if y < -0.15 else "center"
        ax.text(x * push, y * push, ds.display_name(v), ha=ha, va=va, color=INK,
                fontsize=config.BASE_FONT_SIZE - 1,
                bbox=dict(boxstyle="round,pad=0.2", fc=SURFACE, ec="none", alpha=0.9))


def _graph_legend(ax, route: bool = False) -> None:
    handles = [Line2D([], [], marker="s", ls="", ms=13, mfc=ORANGE, mec=ORANGE,
                      label="V0 depot (start/end)"),
               Line2D([], [], marker="o", ls="", ms=13, mfc=BLUE, mec=BLUE, label="hospital"),
               Line2D([], [], color=MUTED, lw=1, label="directed arc i → j")]
    if route:
        handles.append(Line2D([], [], color=BLUE, lw=3, label="route arc (km)"))
    ax.legend(handles=handles, loc="upper left", bbox_to_anchor=(-0.02, 1.0))


# ---------------------------------------------------------------------------
# Figure 1 - the labelled directed graph
# ---------------------------------------------------------------------------
def plot_graph(G: nx.DiGraph, ds: Dataset, path: Path) -> Path:
    """Complete digraph: every ordered pair is an arc. Weights are in Figure 2."""
    fig, ax = plt.subplots(figsize=(11, 10))
    pos = circular_positions(ds.n)
    nx.draw_networkx_edges(G, pos, ax=ax, edge_color=MUTED, alpha=0.55, width=1,
                           arrowstyle="-|>", arrowsize=11, node_size=1500,
                           connectionstyle="arc3,rad=0.10")
    _draw_nodes(ax, G, pos, ds)
    _draw_names(ax, pos, ds)
    _graph_legend(ax)
    ax.set_title(f"G = (V, A): {ds.n} vertices, {G.number_of_edges()} directed arcs\n"
                 f"(complete digraph; arc weights = driving km, see the matrix figure)",
                 fontsize=config.BASE_FONT_SIZE + 2)
    ax.set_axis_off()
    ax.set_xlim(-1.75, 1.75)
    ax.set_ylim(-1.38, 1.45)
    return save(fig, path, ds)


def plot_route_graph(G: nx.DiGraph, ds: Dataset, route: list[int], total: float,
                     path: Path) -> Path:
    """Same graph, with the chosen route's arcs highlighted and their weights printed."""
    fig, ax = plt.subplots(figsize=(11, 10))
    pos = circular_positions(ds.n)
    route_arcs = list(zip(route[:-1], route[1:]))
    others = [e for e in G.edges if e not in route_arcs]
    nx.draw_networkx_edges(G, pos, edgelist=others, ax=ax, edge_color=GRID, width=1,
                           arrowstyle="-|>", arrowsize=9, node_size=1500,
                           connectionstyle="arc3,rad=0.10")
    nx.draw_networkx_edges(G, pos, edgelist=route_arcs, ax=ax, edge_color=BLUE, width=3,
                           arrowstyle="-|>", arrowsize=24, node_size=1500,
                           connectionstyle="arc3,rad=0.10")
    labels = {(a, b): f"{k}: {fmt_km(G[a][b]['weight'])}" for k, (a, b) in
              enumerate(route_arcs, start=1)}
    nx.draw_networkx_edge_labels(G, pos, edge_labels=labels, ax=ax, font_color=INK,
                                 font_size=config.BASE_FONT_SIZE - 1,
                                 connectionstyle="arc3,rad=0.10",
                                 bbox=dict(boxstyle="round,pad=0.2", fc=SURFACE, ec=BLUE, lw=1))
    _draw_nodes(ax, G, pos, ds)
    _draw_names(ax, pos, ds)
    _graph_legend(ax, route=True)
    ax.set_title(f"Route found by Simulated Annealing: {fmt_km(total)} km\n"
                 f"labels = leg number: km", fontsize=config.BASE_FONT_SIZE + 2)
    ax.set_axis_off()
    ax.set_xlim(-1.75, 1.75)
    ax.set_ylim(-1.38, 1.45)
    return save(fig, path, ds)


# ---------------------------------------------------------------------------
# Figure 2 - the weight matrix
# ---------------------------------------------------------------------------
def plot_matrix(D: list[list[float]], ds: Dataset, path: Path) -> Path:
    """Heatmap of D with every value printed. Hatched cells = ASSUMED (not measured)."""
    n = ds.n
    values = np.array(D, dtype=float)
    masked = np.ma.masked_where(np.eye(n, dtype=bool), values)
    fig, ax = plt.subplots(figsize=(1.25 * n + 3.5, 1.05 * n + 2.5))
    im = ax.imshow(masked, cmap=SEQ_BLUES, vmin=0, vmax=values.max())
    ax.grid(False)
    vmax = values.max()
    for i in range(n):
        for j in range(n):
            if i == j:
                ax.add_patch(Rectangle((j - .5, i - .5), 1, 1, fc="#f0efec", ec=SURFACE, lw=2))
                ax.text(j, i, "–", ha="center", va="center", color=MUTED)
                continue
            assumed = ds.edge_status(i, j) == "ASSUMED"
            ax.add_patch(Rectangle((j - .5, i - .5), 1, 1, fill=False, ec=SURFACE, lw=2,
                                   hatch="///" if assumed else None))
            colour = "white" if values[i, j] > 0.55 * vmax else INK
            ax.text(j, i, fmt_km(D[i][j]) + ("*" if assumed else ""), ha="center", va="center",
                    color=colour, fontsize=config.BASE_FONT_SIZE - 2, weight="bold")
    ticks = [node_label(ds, k) for k in range(n)]
    ax.set_xticks(range(n), ticks, fontsize=config.BASE_FONT_SIZE - 4)
    ax.set_yticks(range(n), ticks, fontsize=config.BASE_FONT_SIZE - 4)
    ax.xaxis.tick_top()
    ax.set_xlabel("TO (column)")
    ax.xaxis.set_label_position("top")
    ax.set_ylabel("FROM (row)")
    cbar = fig.colorbar(im, ax=ax, fraction=0.04, pad=0.02)
    cbar.set_label("driving distance (km)")
    note = f"* hatched = ASSUMED (not measured); all other cells ACTUAL ({ds.source_label})"
    ax.set_title(f"Weight matrix D (km): D[i][j] = distance FROM row i TO column j\n{note}",
                 fontsize=config.BASE_FONT_SIZE, pad=14, loc="left", y=-0.12)
    return save(fig, path, ds)


# ---------------------------------------------------------------------------
# Figure 4 - convergence (two panels instead of a dual axis)
# ---------------------------------------------------------------------------
def plot_convergence(hist, optimum: float | None, ds: Dataset, path: Path) -> Path:
    fig, (top, bottom) = plt.subplots(2, 1, figsize=(13, 9), sharex=True,
                                      gridspec_kw={"height_ratios": [2.2, 1]})
    it = np.array(hist.iteration)
    top.plot(it, hist.current_cost, color=ORANGE, lw=1, alpha=0.75, label="current tour")
    top.plot(it, hist.best_cost, color=BLUE, lw=2.5, label="best tour so far")
    if optimum is not None:
        top.axhline(optimum, color=INK, lw=1)
        top.text(it[-1], optimum, f"proven optimum {fmt_km(optimum)} km", va="top",
                 ha="right", color=INK, fontsize=config.BASE_FONT_SIZE - 2,
                 bbox=dict(boxstyle="round,pad=0.2", fc=SURFACE, ec="none", alpha=0.9))
        best = np.array(hist.best_cost)
        reached = np.flatnonzero(np.abs(best - optimum) <= config.FLOAT_TOL)
        if reached.size:
            first = it[reached[0]]
            top.scatter([first], [optimum], s=90, color=BLUE, edgecolor=SURFACE, lw=2, zorder=5)
            top.annotate(f"optimum first reached\nat move {first:,}", (first, optimum),
                         xytext=(25, 60), textcoords="offset points", color=INK,
                         fontsize=config.BASE_FONT_SIZE - 2,
                         arrowprops=dict(arrowstyle="-", color=INK2, lw=1),
                         bbox=dict(boxstyle="round,pad=0.25", fc=SURFACE, ec=AXIS, lw=1))
    top.set_ylabel("tour length (km)")
    top.set_title("Simulated Annealing convergence")
    top.legend(loc="upper right")
    bottom.plot(it, hist.temperature, color=INK2, lw=2)
    bottom.set_yscale("log")
    bottom.set_ylabel("temperature T\n(km, log scale)")
    bottom.set_xlabel("move (iteration)")
    bottom.set_title("Cooling schedule T ← αT (one step per temperature level)",
                     fontsize=config.BASE_FONT_SIZE)
    return save(fig, path, ds)


# ---------------------------------------------------------------------------
# Figure 5 - acceptance of worse moves
# ---------------------------------------------------------------------------
def plot_acceptance(hist, ds: Dataset, path: Path) -> Path:
    it, delta = np.array(hist.iteration), np.array(hist.delta)
    prob, acc, level = np.array(hist.probability), np.array(hist.accepted), np.array(hist.level)
    temp = np.array(hist.temperature)
    worse = delta > 0
    fig, (left, right) = plt.subplots(1, 2, figsize=(16, 6.5))
    left.scatter(it[worse & acc], prob[worse & acc], s=10, color=BLUE, alpha=0.35,
                 label="worse move ACCEPTED", rasterized=True)
    left.scatter(it[worse & ~acc], prob[worse & ~acc], s=10, color=ORANGE, alpha=0.35,
                 label="worse move REJECTED", rasterized=True)
    left.set_xlabel("move (iteration)")
    left.set_ylabel("P = e^(−Δ/T)")
    left.set_title("Acceptance probability of each worse move")
    left.legend(loc="upper right", markerscale=2.5)
    levels = np.unique(level[worse])
    t_level = np.array([temp[level == k][0] for k in levels])
    observed = np.array([acc[worse & (level == k)].mean() for k in levels])
    expected = np.array([prob[worse & (level == k)].mean() for k in levels])
    right.plot(t_level, expected, color=BLUE, lw=2, label="mean P (theory)")
    right.plot(t_level, observed, color=AQUA, lw=0, marker="o", ms=4,
               label="observed acceptance rate")
    right.set_xscale("log")
    right.invert_xaxis()
    right.set_xlabel("temperature T (km, log scale; cooling →)")
    right.set_ylabel("share of worse moves accepted")
    right.set_ylim(-0.03, 1.03)
    right.set_title("Worse moves are accepted less as T drops")
    right.legend(loc="upper right")
    return save(fig, path, ds)


# ---------------------------------------------------------------------------
# Figure 7 - 30 runs vs optimum vs greedy;  search-space histogram
# ---------------------------------------------------------------------------
def plot_runs(records, optimum: float, greedy_cost: float, ds: Dataset, path: Path) -> Path:
    costs = np.array([r.cost for r in records])
    hits = sum(r.hit_optimum for r in records)
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.boxplot([costs], positions=[0], widths=0.35, showfliers=False,
               medianprops=dict(color=BLUE, lw=2), boxprops=dict(color=AXIS),
               whiskerprops=dict(color=AXIS), capprops=dict(color=AXIS))
    jitter = np.random.default_rng(0).uniform(-0.12, 0.12, len(costs))
    ax.scatter(jitter, costs, s=70, color=BLUE, edgecolor=SURFACE, lw=1.5, zorder=3,
               label=f"SA runs (seeds {records[0].seed}..{records[-1].seed})")
    ax.scatter([1], [greedy_cost], s=110, color=ORANGE, edgecolor=SURFACE, lw=1.5, zorder=3,
               label="greedy nearest neighbour")
    ax.scatter([2], [optimum], s=110, color=INK, edgecolor=SURFACE, lw=1.5, zorder=3,
               label="brute force (proven optimum)")
    ax.axhline(optimum, color=INK, lw=1)
    ax.text(1, greedy_cost, f"   {fmt_km(greedy_cost)} km", va="center", color=INK)
    ax.text(2, optimum, f"   {fmt_km(optimum)} km", va="bottom", color=INK)
    ax.annotate(f"{hits}/{len(costs)} runs reached the optimum", (0.2, costs.max()),
                xytext=(0, 18), textcoords="offset points", va="bottom", color=INK)
    ax.set_xticks([0, 1, 2], [f"Simulated Annealing\n({len(costs)} runs)", "Greedy\n(1 run)",
                              "Brute force\n(exact)"])
    ax.set_xlim(-0.6, 2.8)
    span = max(costs.max(), greedy_cost) - optimum
    ax.set_ylim(optimum - 0.15 * span - 0.5, max(costs.max(), greedy_cost) + 0.25 * span + 0.5)
    ax.set_ylabel("total tour length (km)")
    ax.set_title("Solution quality over independent runs (same distance matrix)")
    ax.legend(loc="upper right")
    return save(fig, path, ds)


def plot_search_space(all_costs: list[float], optimum: float, sa_cost: float, greedy_cost: float,
                      mean_cost: float, ds: Dataset, path: Path) -> Path:
    fig, ax = plt.subplots(figsize=(13, 6.5))
    ax.hist(all_costs, bins=60, color=BLUE, alpha=0.85, edgecolor=SURFACE, linewidth=0.5)
    ymax = ax.get_ylim()[1]
    marks = [(optimum, INK, f"optimum = SA result\n{fmt_km(optimum)} km"
              if abs(sa_cost - optimum) <= config.FLOAT_TOL else f"optimum {fmt_km(optimum)} km"),
             (greedy_cost, ORANGE, f"greedy {fmt_km(greedy_cost)} km"),
             (mean_cost, INK2, f"average random tour\n{fmt_km(mean_cost)} km")]
    if abs(sa_cost - optimum) > config.FLOAT_TOL:
        marks.append((sa_cost, AQUA, f"SA {fmt_km(sa_cost)} km"))
    for k, (x, colour, text) in enumerate(marks):
        ax.axvline(x, color=colour, lw=2)
        ax.text(x, ymax * (0.95 - 0.17 * k), " " + text, color=INK, va="top",
                fontsize=config.BASE_FONT_SIZE - 2, zorder=5,
                bbox=dict(boxstyle="round,pad=0.25", fc=SURFACE, ec=AXIS, lw=1))
    ax.set_xlabel("total tour length (km)")
    ax.set_ylabel("number of tours")
    ax.set_title(f"The whole search space: all {len(all_costs):,} possible tours "
                 f"((n−1)! with the depot fixed)")
    return save(fig, path, ds)


# ---------------------------------------------------------------------------
# Figure 8 - parameter study (alpha, neighbour)
# ---------------------------------------------------------------------------
def plot_parameter_study(rows: list[dict], key: str, xlabel: str, title: str, ds: Dataset,
                         path: Path) -> Path:
    """Two panels side by side: solution quality and runtime for each setting."""
    labels = [str(r[key]) for r in rows]
    x = np.arange(len(rows))
    fig, (left, right) = plt.subplots(1, 2, figsize=(15, 6.2))
    hit = [r["hit_rate_pct"] for r in rows]
    left.bar(x, hit, width=0.45, color=BLUE)
    for xi, r in zip(x, rows):
        left.text(xi, r["hit_rate_pct"] + 2, f"{r['hit_rate_pct']:.0f}%\ngap "
                  f"{r['mean_gap_pct']:.2f}%", ha="center", va="bottom",
                  fontsize=config.BASE_FONT_SIZE - 3)
    left.set_ylim(0, 128)
    left.set_yticks([0, 25, 50, 75, 100])
    left.set_xticks(x, labels)
    left.set_xlabel(xlabel)
    left.set_ylabel("runs reaching the optimum (%)")
    left.text(0.0, -0.2, "gap = mean % above the proven optimum", transform=left.transAxes,
              fontsize=config.BASE_FONT_SIZE - 4, color=INK2)
    left.set_title("Solution quality")
    rt = [1000 * r["mean_runtime_s"] for r in rows]
    right.bar(x, rt, width=0.45, color=BLUE)
    for xi, r, v in zip(x, rows, rt):
        right.text(xi, v * 1.03, f"{v:.0f} ms\n{r['mean_iterations'] / 1000:,.0f}k moves",
                   ha="center", va="bottom", fontsize=config.BASE_FONT_SIZE - 3)
    right.set_ylim(0, max(rt) * 1.3)
    right.set_xticks(x, labels)
    right.set_xlabel(xlabel)
    right.set_ylabel("mean runtime per run (ms)")
    right.set_title("Cost in time")
    fig.suptitle(title, fontsize=config.BASE_FONT_SIZE + 3, weight="bold")
    return save(fig, path, ds)


# ---------------------------------------------------------------------------
# Figure 6 - animated GIF of the search
# ---------------------------------------------------------------------------
def _frame(ds: Dataset, pos: dict, snap: tuple, total_moves: int,
           figsize: tuple[float, float]) -> Image.Image:
    it, T, cur, cur_cost, best, best_cost = snap
    fig, ax = plt.subplots(figsize=figsize)
    for tour, colour, lw, alpha, z in ((cur, ORANGE, 1.5, 0.7, 2), (best, BLUE, 3.5, 1.0, 3)):
        closed = tour + [tour[0]]
        for a, b in zip(closed[:-1], closed[1:]):
            ax.annotate("", xy=pos[b], xytext=pos[a], zorder=z,
                        arrowprops=dict(arrowstyle="-|>", color=colour, lw=lw, alpha=alpha,
                                        shrinkA=14, shrinkB=14, mutation_scale=18))
    for v, (x, y) in pos.items():
        ax.scatter([x], [y], s=520, marker="s" if v == config.DEPOT else "o",
                   color=ORANGE if v == config.DEPOT else INK2, edgecolor=SURFACE, lw=2,
                   zorder=4)
        ax.text(x, y, ds.labels[v], color="white", ha="center", va="center",
                fontsize=11, weight="bold", zorder=5)
    ax.set_aspect("equal")
    ax.margins(0.08)
    ax.set_axis_off()
    ax.set_title(f"move {it:,}/{total_moves:,}   T = {T:.3f} km\n"
                 f"current {fmt_km(cur_cost)} km (orange)   best {fmt_km(best_cost)} km (blue)",
                 fontsize=15)
    stamp(fig, ds, y=0.01, va="bottom")
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=90)
    plt.close(fig)
    buf.seek(0)
    return Image.open(buf).convert("P", palette=Image.Palette.ADAPTIVE)


def make_gif(hist, ds: Dataset, path: Path) -> Path:
    """Animated GIF: the current tour wandering (orange) and the best tour improving (blue)."""
    snaps = hist.snapshots
    step = max(1, math.ceil(len(snaps) / config.GIF_MAX_FRAMES))
    chosen = snaps[::step]
    if chosen[-1] is not snaps[-1]:
        chosen.append(snaps[-1])
    pos = geo_positions(ds)
    xs, ys = [p[0] for p in pos.values()], [p[1] for p in pos.values()]
    aspect = (max(ys) - min(ys)) / max(max(xs) - min(xs), 1e-9)
    figsize = (9.0, min(9.0, max(4.0, 9.0 * aspect)) + 1.4)  # + room for the title
    frames = [_frame(ds, pos, s, snaps[-1][0], figsize) for s in chosen]
    frames += [frames[-1]] * 8  # hold the final answer on screen
    path.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=config.GIF_FRAME_MS,
                   loop=0)
    return path
