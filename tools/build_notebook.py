"""
build_notebook.py - (re)create demo.ipynb, the step-by-step notebook for the video.

    python tools/build_notebook.py

The notebook calls the same functions as main.py, so its numbers are identical.
It is saved with outputs cleared (run "Restart & Run All" while recording).
"""
from pathlib import Path

import nbformat as nbf

ROOT = Path(__file__).resolve().parent.parent

CELLS = [
    ("md", """# Simulated Annealing for the TSP: blood deliveries in Cagayan de Oro City
**Algorithm:** Simulated Annealing (Luna-Garcia, Candano & Caga-anan, TMJM 6(2), 2024, Algorithm 2.5).
**Problem:** a Red Cross courier leaves the chapter office (V0), visits 8 hospitals once each and returns, minimising the total **driving distance in km**.

Run with **Kernel → Restart & Run All**. Every cell calls the same code as `python main.py`."""),
    ("code", """# Setup: big fonts for the screen recording
from IPython.display import HTML, Image, display
import inspect
import pandas as pd

display(HTML('''<style>
  .jp-OutputArea-output pre, .output_text pre, .jp-RenderedText pre {font-size: 15px !important;}
  .dataframe, .jp-RenderedHTMLCommon table {font-size: 16px !important;}
</style>'''))

import main
from src import config, report
from src.baselines import brute_force, greedy_nearest_neighbor
from src.docs_builder import build_docs
from src.experiments import run_many, summarize
from src.graph_model import build_digraph
from src.simulated_annealing import simulated_annealing
from src.verify import verify_solution
from src import visualize as viz
viz.apply_style()
SEED, NEIGHBOR, OUT = config.DEFAULT_SEED, config.NEIGHBOR_DEFAULT, config.OUTPUT_DIR"""),
    ("md", "## 1 · Input data (`data/*.csv`) and validation"),
    ("code", """ds, rep, D = main.load_and_validate()   # stops with an error message if the data are invalid"""),
    ("code", """locations = pd.DataFrame([vars(l) for l in ds.locations])[
    ["label", "name", "short_name", "role", "latitude", "longitude"]]
display(locations)"""),
    ("code", """matrix = pd.DataFrame(D, index=ds.labels, columns=ds.labels)
matrix.index.name = "FROM \\\\ TO (km)"
display(matrix.style.format("{:.1f}").background_gradient(cmap="Blues", axis=None))
print("Edge provenance:", rep.status_counts, "| asymmetric pairs:", len(rep.asymmetric_pairs))"""),
    ("md", "## 2 · Graph model: complete directed graph G = (V, A)"),
    ("code", """G = build_digraph(ds, D)
print(f"|V| = {G.number_of_nodes()} vertices, |A| = {G.number_of_edges()} directed arcs (weights in km)")
display(Image(viz.plot_graph(G, ds, OUT / "fig1_graph.png"), width=700))
display(Image(viz.plot_matrix(D, ds, OUT / "fig2_weight_matrix.png"), width=800))"""),
    ("md", "## 3 · Simulated Annealing parameters (`src/config.py`)"),
    ("code", """params, mean_uphill = main.resolve_sa_params(D, NEIGHBOR)
report.print_params(params, NEIGHBOR, SEED, mean_uphill, config.DEFAULT_RUNS)"""),
    ("md", "## 4 · Run SA: trace of the first 5 moves (Alg 2.5 steps 4–10), then the result"),
    ("code", """res = simulated_annealing(D, params, SEED, NEIGHBOR, record_history=True,
                         trace_steps=config.TRACE_EXPORT_STEPS)
report.print_trace(res.trace[:config.TRACE_PRINT_STEPS], ds, NEIGHBOR)
report.print_sa_result(res, ds)"""),
    ("md", "## 5 · Verification: valid closed tour, total recomputed edge by edge"),
    ("code", """vr = verify_solution(res.route, res.best_cost, G)   # raises an error if anything is wrong
report.print_verification(vr, ds)"""),
    ("md", "## 6 · Is it optimal? Brute force over all (n−1)! tours, and greedy, on the same matrix"),
    ("code", """bf, greedy = brute_force(D), greedy_nearest_neighbor(D)
report.print_comparison(res.best_cost, bf, greedy, ds)"""),
    ("md", "## 7 · 30 independent runs (paper Table 2 format)"),
    ("code", """seeds = list(range(config.FIRST_RUN_SEED, config.FIRST_RUN_SEED + config.DEFAULT_RUNS))
records = run_many(D, params, seeds, NEIGHBOR, bf.optimal_cost)
summary = summarize(records)
report.print_run_statistics(summary, bf.optimal_cost, greedy.cost, bf.runtime_s, greedy.runtime_s)"""),
    ("md", "## 8 · Route on the map, convergence, acceptance"),
    ("code", """ctx = dict(params=params, mean_uphill=mean_uphill, res=res, G=G, vr=vr, bf=bf, greedy=greedy,
           records=records, summary=summary)
files = main.make_figures(ds, D, ctx)
import html as _html   # embed the interactive folium map in the notebook
map_src = _html.escape(files["map_html"].read_text(encoding="utf-8"))
display(HTML(f'<iframe srcdoc="{map_src}" width="1000" height="600" style="border:none"></iframe>'))"""),
    ("code", """for key in ("convergence", "acceptance", "runs", "search_space"):
    display(Image(files[key], width=950))
display(Image(files["gif"]))"""),
    ("md", "## 9 · The core code: `simulated_annealing()` (comments = Algorithm 2.5 step numbers)"),
    ("code", """print(inspect.getsource(simulated_annealing))"""),
    ("md", "## 10 · Save the results (feeds `docs/` and the consistency check)"),
    ("code", """args = main.parse_args([])
report.write_json(OUT / "results_summary.json", main.build_summary(ds, rep, D, ctx, args))
report.export_trace(res.trace, ds, OUT); report.export_history(res.history, OUT, ds.fingerprint)
report.export_verification(vr, ds, OUT); report.export_runs(records, OUT, ds)
report.export_table2(summary, bf.optimal_cost, greedy, bf, OUT, ds.fingerprint)
build_docs()"""),
]


def main() -> None:
    nb = nbf.v4.new_notebook()
    nb.cells = [nbf.v4.new_markdown_cell(src) if kind == "md" else nbf.v4.new_code_cell(src)
                for kind, src in CELLS]
    nb.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
    path = ROOT / "demo.ipynb"
    nbf.write(nb, path)
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
